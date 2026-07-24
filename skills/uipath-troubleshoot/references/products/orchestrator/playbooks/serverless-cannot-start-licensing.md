---
confidence: medium
---

# Automation Cannot Be Started — Serverless Licensing / Robot Units

## Context

A serverless (cloud) job (`RuntimeType = Serverless`, runtimetype `9`) never runs because Orchestrator rejects the start on a licensing or capacity check — before any Robot session is created. The error text names the exhausted resource. Distinct from unattended executor failures (no `Could not start executor` here) — the block is in Orchestrator's licensing layer, not on a host.

What this looks like — one of these `Info` signatures:
- `Automation cannot be started. Your user's monthly Personal Automation quota has been exceeded.`
- `Automation cannot be started. Your user's assigned Robot Units have been exceeded.`
- `Automation cannot be started. Your tenant's assigned Robot Units have been exceeded. Allocate more Robot Units to your tenant to continue.`
- `The automation was cancelled because it reached the time limit. Consider optimizing your workflow or splitting into multiple workflows.`
- `Could not obtain the user token from Orchestrator.`
- `You are already running <N> designer jobs.`

Common markers:
- Job faults at or before start with a licensing/quota message, zero execution logs from the workflow itself
- `RuntimeType: Serverless` on `uip or jobs get`
- Scope hint is in the wording: **user's** (per-user) vs **tenant's** (tenant-wide pool)

What can cause it (branches):
1. **Personal Automation monthly quota exhausted** — the user's per-user monthly serverless quota is spent for the current billing period. Scoped to one user; resets next period.
2. **User Robot Units exceeded** — the Robot Units allocated to this user (or the folder for this user) are fully consumed by concurrent/recent runs.
3. **Tenant Robot Units exhausted** — the tenant-wide Robot Unit pool has no capacity left. Tenant-wide: multiple users' serverless jobs fail simultaneously, not just one user's.
4. **Time-limit cancellation** — the run exceeded the serverless maximum execution time and was cancelled mid-flight (not a start-time block — the job ran, then was killed on the ceiling).
5. **Could not obtain user token** — known issue where the serverless runtime fails to mint the execution token from Orchestrator (tracked under HDENS-6105); typically transient / robot-version-sensitive, not a licensing shortage.
6. **Designer job cap** — the interactive "Run" (designer) serverless jobs are capped per user (e.g. 4 concurrent); further starts are refused until running ones finish.

## Investigation

1. Get the failing job — the `Info` text names the resource and scope:
   `uip or jobs get <job-key> --output json`
   Confirm `RuntimeType: Serverless`. Note `Source` (Manual/designer vs trigger), `StartTime`/`EndTime` (a non-trivial gap ⇒ time-limit cancel, branch 4).
2. Read licensing/allocation state:
   `uip or licenses info --output json` — read tenant Robot Unit allocation vs. usage. Zero remaining tenant RU ⇒ branch 3; tenant RU available but user is blocked ⇒ branch 1/2 (per-user).
3. Establish scope — is it one user or tenant-wide?
   `uip or jobs list --folder-key <key> --state Faulted --output json` — if only this user's serverless jobs fail while others succeed ⇒ per-user (branch 1/2); if serverless jobs across multiple users fault with the tenant-RU message ⇒ branch 3.
4. For branch 4 (time-limit): compare `StartTime`/`EndTime` on `jobs get` and the log — the run reached the serverless ceiling. For branch 6 (designer cap): count the user's currently Running designer jobs via `jobs list --state Running`.
5. For branch 5 (`Could not obtain the user token`): check whether the failure is isolated/intermittent and whether the robot/runtime version is current; treat as the known issue, not a quota problem.

## Resolution

- **Branch 1 — Personal Automation quota exhausted:** the per-user monthly quota resets at the next billing period. For immediate need, an admin allocates the user a licensed Robot Unit / Unattended entitlement instead of relying on the free Personal Automation quota (Orchestrator → Admin → Tenant → Licenses, or portal folder licensing). Navigate: Automation Cloud → Admin → Licenses / folder licensing.
- **Branch 2 — user Robot Units exceeded:** increase the user's Robot Unit allocation, or wait for in-flight runs to release units. Where allocation is folder-scoped, raise the folder's allotment (Orchestrator → folder → Settings → licensing).
- **Branch 3 — tenant Robot Units exhausted:** allocate more Robot Units to the tenant (Automation Cloud → Admin → Licenses → allocate RU to the tenant), or free units by stopping non-essential serverless runs. This is a tenant-wide shortage — raising one user's allocation will not help until the tenant pool has capacity.
- **Branch 4 — time-limit cancellation:** optimize the workflow to finish within the serverless execution ceiling, or split it into multiple shorter workflows chained via a trigger/queue. Long-running work should run unattended, not serverless.
- **Branch 5 — could not obtain user token (HDENS-6105):** rerun the job; if it recurs, update the robot/runtime to the latest version. This is a known runtime defect, not a licensing shortage — do not reallocate units for it.
- **Branch 6 — designer job cap:** close/stop the user's already-running designer ("Run") jobs so a slot frees, then rerun. Designer jobs are capped per user by design.

Prevention:
- Monitor tenant Robot Unit utilization and alert before the pool is exhausted (branch 3 is the highest-impact, tenant-wide outage).
- Size serverless workloads to the execution-time ceiling; move long jobs to unattended.
- For heavy per-user automation, license the user with Robot Units rather than depending on the Personal Automation free quota.
