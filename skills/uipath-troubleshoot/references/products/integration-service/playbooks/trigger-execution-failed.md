---
confidence: medium
---

# Trigger Execution Failed (DAP-RT-1050 / DAP-RT-1051 / DAP-RT-1052 / DAP-RT-1053)

> **Fault bucket: mixed — classify per code.** `1051`/`1050` → **🛠 B2** (connector trigger endpoint / malformed provider payload — provider-side, wait/escalate). `1053` → **👤 A** (trigger misconfigured — customer fixes the filter/parameters). `1052` → **not an error** (zero matches, usually expected). Lead with the bucket that matches the emitted code. See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like — trigger (polling/webhook) runtime codes:

| Code | Name | Specific cause | Bucket |
|---|---|---|:---:|
| `DAP-RT-1051` | TriggerExecutionFailed | Trigger evaluation call failed or returned empty — connector trigger endpoint issue | 🛠 B2 |
| `DAP-RT-1050` | TriggerDataMissing | Event payload missing the expected event ID — malformed webhook/poll payload | 🛠 B2 |
| `DAP-RT-1053` | TriggerInvalidConfiguration | Trigger misconfigured — bad filters/parameters | 👤 A |
| `DAP-RT-1052` | TriggerNoMatches | Filter matched zero events — **often expected, not always an error** | — |

What can cause it:
- Connection used by the trigger is inactive or expired (`1051`)
- Connector trigger endpoint changed, errored, or returned an unexpected shape (`1051`)
- Webhook/poll payload from the provider is malformed or missing the event ID (`1050`)
- Trigger filters/parameters set incorrectly by the user (`1053`)
- Trigger filter genuinely matched no events in the polling window (`1052` — usually benign)

What to look for:
- `ConnectionId` and `RequestId` in the customEvent
- For `1052`: whether zero matches is expected for the schedule/filter before treating it as a fault
- Whether the trigger subscription still exists in the external service

> The Maestro/Orchestrator-surfaced view (subscription missing, robot lacks Triggers permission, debug-vs-deploy bindings) is [trigger-not-firing.md](./trigger-not-firing.md). Use it for "events occur but no job/instance starts"; use this playbook when a `DAP-RT-105x` code is emitted during trigger evaluation.

## Investigation

1. **Classify the code first.** `1052` (NoMatches) is frequently expected — confirm the trigger is *supposed* to find events before investigating it as a failure.
2. **Read the connection resource file** — identify the connector and connection (see "Connection Resource File" in [overview.md](../overview.md)).
3. `uip is connections ping <connection-id>` — verify the trigger's connection is active (primary cause of `1051`).
4. `uip is triggers objects <connector-key> <operation>` / `uip is triggers describe ...` — verify the trigger object type and expected payload schema.
5. For `1050`: inspect the provider payload (from logs/`RequestId`) for the missing event ID — a provider-side or subscription-config problem.

## Resolution

- **`DAP-RT-1051` — connection inactive:** re-authenticate via `uip is connections edit <connection-id>` (see [token-refresh-failed.md](./token-refresh-failed.md) for auth-expiry).
- **`DAP-RT-1051` — endpoint issue:** verify the trigger object/operation is still supported by the connector; reconfigure if the connector changed.
- **`DAP-RT-1050`:** verify the subscription in the external service emits the expected event shape; recreate the trigger subscription if the payload contract drifted.
- **`DAP-RT-1053` (customer-resolvable):** fix the trigger's filter/parameter configuration — correct invalid filter expressions or required parameters, then re-save the trigger.
- **`DAP-RT-1052`:** if zero matches is expected, no action — do not flag as a fault. If events *should* match, check the trigger filter and the polling window.
