---
confidence: medium
---

# Activity Configuration Corrupt (DAP-RT-1000 / 1001 / 1004 / 1008 / 1100 / DAP-GE-3001)

> **Fault bucket: 🛠 B1 — IS platform / connector defect (escalate to owner team).** The activity pack or connector metadata is malformed, unversioned, or failed to migrate — the customer cannot fix the underlying defect in their workflow. Lead with: "This is a service-side issue (connector/activity-pack defect), not something you can fix in your workflow — contact the owner team (Integration Service)." Where a package downgrade or re-migration is available, offer it as an interim workaround, not the fix. See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like — the activity's stored configuration is incomplete, null, unversioned, or failed to migrate, so IS cannot build the request:

| Code | Name | Specific cause |
|---|---|---|
| `DAP-RT-1000` | ActivityConfigurationNull | Activity configuration is null/empty — corrupt or failed-to-deserialize config blob |
| `DAP-RT-1001` | ServiceProviderNull | Runtime DI/service provider not available — internal runtime error |
| `DAP-RT-1004` | InvalidConfigurationVersion | Config schema version not understood by the runtime |
| `DAP-RT-1008` | InvalidActivityConfiguration | Activity configuration is malformed |
| `DAP-RT-1100` | HttpMethodMissing | Activity built without an HTTP method — incomplete connector metadata |
| `DAP-GE-3001` | InvalidMigration | Activity failed to migrate to a newer connector schema version |

What can cause it:
- Activity package upgraded and the old configuration didn't migrate cleanly (`3001`, `1000`, `1004`)
- Connector metadata generated incomplete — no HTTP method, malformed schema (`1100`, `1008`)
- Project/package corruption during publish or merge — the config blob is empty or malformed (`1000`)
- Internal runtime fault — service provider not constructed (`1001`)

What to look for:
- No `ProviderErrorCode` / provider status — the failure is IS-side, before any provider call (the signal that this is **Bucket B1**; "service error" is your classification, not a field)
- `ProviderErrorCode` and `ConnectionId` are typically absent — nothing reached the connection layer
- Whether the failure started immediately after an activity package upgrade (points to a migration code — `3001`/`1004`)

## Investigation

1. **Confirm it is config-layer, not connection or provider** — no `ProviderErrorCode` / provider status. The connection ping is healthy; the problem is the activity definition / connector metadata.
2. **Read the workflow source** — open the failing activity in the project. Verify the configuration blob is present and complete:
   - **`DAP-RT-1100`:** check the HTTP method is set on the activity.
   - **`DAP-RT-1000` / `1008`:** check the activity's configuration is not empty/null/malformed.
3. **Check for a recent package upgrade** — compare the activity package version against the project history. A migration code (`3001`/`1004`) indicates a migration the package could not complete.
4. `uip is activities list <connector-key>` — confirm the activity still exists and is supported in the installed package version.

## Resolution

**Primary: escalate.** These are connector/activity-pack defects on the IS side. Report the `DAP` code, `RequestId`, connector key, and package version to the Integration Service owner team. The customer cannot resolve the underlying defect from their workflow.

Interim workarounds (try while the escalation is open, where applicable):

- **`DAP-RT-1100` / `1008`:** open the activity and set the HTTP method / reconfigure the operation, then republish. If the connector metadata itself is incomplete, this only works if the field is settable in Studio — otherwise escalate.
- **`DAP-RT-1000`:** re-create the activity from a clean state — delete and re-add it, reconfigure inputs, republish. If project corruption is suspected, restore from source control.
- **Migration codes (`DAP-GE-3001`, `DAP-RT-1004`):** re-open the project in Studio to run the activity migration, or downgrade to the previous connector package version if migration cannot complete; then re-validate and republish.
- **`DAP-RT-1001` (ServiceProviderNull):** no customer workaround — internal runtime error. Escalate with the `RequestId`.
- After any workaround, re-run to confirm the config-layer error clears before checking for downstream provider errors.
