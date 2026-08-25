---
confidence: high
---

# Connection Service — Trigger Management Failed (CNS1020, CNS1014, CNS1025, CNS1039, CNS2004)

> **Fault bucket: 👤 A for `CNS1020`/`CNS1014`/`CNS1039` and most `CNS1025` (bad ID, blocked delete, bad interval, malformed request) · 🛠 B1 for `CNS2004` (persisted trigger configuration cannot be deserialized — a data/platform defect).** These codes fire on trigger CRUD — create, rename, enable/disable, convert, delete — via the Connection Service API. For a trigger that manages fine but silently doesn't *fire*, use [trigger-not-firing.md](./trigger-not-firing.md) instead; for enable failing because the underlying connection is dead, it's `CNS1061` in [cs-connection-not-authenticated.md](./cs-connection-not-authenticated.md).

## Context

What this looks like:
- HTTP `400`/`404` from trigger endpoints, error body `{ "code": "CNS1020", "message": "Trigger [<guid>] is invalid or you do not have access…", "traceId": "…" }`

| Code | Name | Exact meaning | HTTP | Bucket |
|------|------|---------------|:---:|:---:|
| `CNS1020` | TriggerIdInvalid | Trigger ID doesn't exist / caller has no access — or the trigger isn't of the type the operation requires (e.g. convert/migrate on a non-automation trigger) | 404 | 👤 A |
| `CNS1014` | DeleteTriggerWithActiveProcessNotAllowed | Delete blocked: the trigger still has active/assigned processes | 400 | 👤 A |
| `CNS1025` | TriggerRequestInvalid | Malformed trigger request — **heavily overloaded**: missing body fields, *"In S2S context, the folder key is required"* (also thrown by some connection endpoints), and one service-side notification-failure branch | 400 (one 500 branch) | 👤 A (mostly) |
| `CNS1039` | InvalidPollingInterval | Polling interval outside the allowed min/max range | 400 | 👤 A |
| `CNS2004` | TriggerConfigDeserializationFailed | The trigger's persisted configuration blob can't be deserialized / has an unknown trigger type — data corruption or version drift | 500 | 🛠 B1 |

What can cause it:
- Automations/scripts referencing trigger IDs that were deleted or belong to another folder/tenant
- Attempting to delete a trigger still wired to processes (`CNS1014` is a guard, not a fault)
- S2S/machine callers omitting the folder key after an integration change (`CNS1025`)
- Setting polling intervals below the tenant minimum (`CNS1039`)
- `CNS2004`: a trigger created by an older service version whose config schema the current version can't read, or a corrupted row — never customer-caused

What to look for:
- The trigger GUID and which operation failed (create/update/state-change/delete/convert)
- `CNS1025`: read the message — "folder key is required" vs a field-validation message vs anything else; the code alone does not identify the failure
- `CNS2004`: which trigger ID — the same trigger will fail deterministically on every read/fire until repaired

## Investigation

1. **Resolve the trigger** in the tenant (Integration Service → Triggers, or via API list) — confirm existence, folder, and type. `CNS1020` on convert/migrate operations can mean "exists but wrong trigger type", which the message indicates.
2. **`CNS1014`:** list the processes attached to the trigger; that list is the blocker. This is working-as-designed protection.
3. **`CNS1025`:** classify by message. Folder-key-required → fix the S2S caller (see [cs-permission-denied.md](./cs-permission-denied.md) for the same pattern under `CNS1043`). Field validation → fix the request payload. Anything mentioning notification/SAP with a 500 → treat as service-side, capture `traceId`, escalate.
4. **`CNS2004`:** deterministic 500 on a specific trigger = data-level defect. Do not loop retries. Capture the trigger ID and `traceId` and check whether the trigger predates a known migration; the owner team repairs or migrates the config.
5. If trigger *creation* fails with an Orchestrator-related error rather than these codes, the failing leg is Connection Service → Orchestrator (`CNS2005`) — route to [cs-dependency-unavailable.md](./cs-dependency-unavailable.md).

## Resolution

- **`CNS1020`:** correct the trigger reference (recreate the trigger or point the caller at the right ID/folder); for type-mismatch variants, run the operation against a trigger of the required type.
- **`CNS1014`:** unassign/stop the attached processes first, then delete the trigger — or keep the trigger if the processes are still needed.
- **`CNS1025` (customer variants):** fix the request — supply the folder key on S2S calls, complete required fields.
- **`CNS1039`:** set the polling interval within the documented range for the tenant/connector.
- **`CNS2004`:** escalate to the Integration Service owner team with trigger ID + `traceId`. Deleting and recreating the trigger is a customer-side workaround *only if* losing the trigger's history/config is acceptable — offer it, don't default to it.
