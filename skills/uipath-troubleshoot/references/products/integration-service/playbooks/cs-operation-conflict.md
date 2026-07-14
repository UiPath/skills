---
confidence: high
---

# Connection Service — Conflict / Duplicate (CNS3002, CNS1007, CNS1038)

> **Fault bucket: 👤 A for `CNS1038` (pick another name) · 🛠 mixed for `CNS1007` (usually a create race — retry once) · 🔧 ops-tooling for `CNS3002` (an internal migration/backfill is already running — wait or deliberately override; never a customer action).** Everything here is a *state collision*, not a fault: something already exists or is already running.

## Context

What this looks like:

| Code | Name | Exact meaning | HTTP | Who acts |
|------|------|---------------|:---:|---|
| `CNS3002` | Conflict | A single-flight lock is held: an in-progress **tenant migration**, **Orchestrator-trigger migration** (`migrate-disconnected`), or **personal-workspace backfill** job is already running for the tenant, and a second trigger attempt arrived without the override flag | 409 | Ops / owner team |
| `CNS1007` | ConnectionKeyOrIndexViolation | Duplicate-key violation inserting a connection — two concurrent creates of the same connection, or a retry racing its original | 400 | Customer (retry) / service if persistent |
| `CNS1038` | ConnectionNameDuplicated | Rename rejected — *"The name is already in use."* | 400 | Customer |

Related 409: `CNS1075` (connector not deployed) also surfaces as 409 but is a connector-deployment fault — see [cs-connector-unavailable.md](./cs-connector-unavailable.md).

What can cause it:
- `CNS3002`: a previous migration/backfill run is still in progress — or crashed while holding its lock (stuck lock). The message names the job type (e.g. an `OrchTrigger` migration record).
- `CNS1007`: double-submit on connection creation (UI double-click, client retry without idempotency), or parallel automation creating the same connection
- `CNS1038`: straightforward — the target name exists in scope

What to look for:
- `CNS3002`: **is the named job actually running?** A genuinely running job → wait. No live job but the lock persists → stuck lock from a crashed run.
- `CNS1007`: whether the connection actually got created despite the error (the race's winner) — often the retry fails but the resource exists

## Investigation

1. **`CNS3002`:** identify the job family from the message (GWS tenant migration / OrchTrigger migration / PWs backfill). Owner team: check the job's progress records and task-runner logs for a live run. If the last run terminated abnormally and the lock is stale, the trigger API accepts an explicit override flag (`OverrideMigrationInProcess` / `OverrideJobInProcess` / `OverrideBackfillInProcess`) — an **ops decision**: only override when certain no run is in flight, since overriding overwrites the live migration record.
2. **`CNS1007`:** list connections for the connector/folder — if the intended connection exists, the create actually succeeded on the other racer; use it. If nothing exists and the error repeats on clean single-flight creates, capture the `traceId` and escalate (persistent key collision is a service defect).
3. **`CNS1038`:** nothing to investigate — enumerate existing names.

## Resolution

- **`CNS3002` with a live job:** wait for completion; the lock releases itself. Do not spam the trigger endpoint.
- **`CNS3002` with a stuck lock:** ops re-fires the trigger with the override flag — on the **first** batch/attempt only; never override while a run is legitimately in flight.
- **`CNS1007`:** retry the create once; if the connection appeared, deduplicate client-side (avoid double-submit). Persistent → escalate with `traceId`.
- **`CNS1038`:** choose a unique connection name. Name-length/empty variants of the same rename validation surface as `CNS1032`/`CNS1033`.
