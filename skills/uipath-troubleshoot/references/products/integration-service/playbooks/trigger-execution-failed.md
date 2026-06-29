---
confidence: medium
---

# Trigger Execution Failed (DAP-RT-1050 / DAP-RT-1051 / DAP-RT-1052 / DAP-RT-1053)

> **Fault bucket: mixed — classify per code.** `1051`/`1050` → **🛠 B2** (connector trigger endpoint / malformed provider payload — provider-side, wait/escalate). `1053` → **🛠 B1** (object name / operation null or empty — handled by connector configuration, the customer cannot fix it → escalate). `1052` is **debug-only and never appears in runtime telemetry** — out of scope for runtime triage. Lead with the bucket that matches the emitted code. See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like — trigger (polling/webhook) runtime codes:

| Code | Name | Specific cause | Bucket |
|---|---|---|:---:|
| `DAP-RT-1051` | TriggerExecutionFailed | Trigger evaluation call failed or returned empty — connector trigger endpoint issue | 🛠 B2 |
| `DAP-RT-1050` | TriggerDataMissing | Event payload missing the expected event ID — malformed webhook/poll payload | 🛠 B2 |
| `DAP-RT-1053` | TriggerInvalidConfiguration | Trigger object name or operation is null/empty — set by connector configuration, not customer-settable | 🛠 B1 |
| `DAP-RT-1052` | TriggerNoMatches | Zero events matched — **debug-mode-only signal; never emitted in runtime telemetry** | — |

What can cause it:
- Connection used by the trigger is inactive or expired (`1051`)
- Connector trigger endpoint changed, errored, or returned an unexpected shape (`1051`)
- Webhook/poll payload from the provider is malformed or missing the event ID (`1050`)
- Connector configuration produced a null/empty trigger object name or operation — a connector-metadata defect, not a user-settable field (`1053`)

What to look for:
- `ConnectionId` and `RequestId` in the customEvent
- For `1053`: `IsServiceError: false` — the null/empty object/operation originates in connector configuration, before the provider call
- Whether the trigger subscription still exists in the external service

> The Maestro/Orchestrator-surfaced view (subscription missing, robot lacks Triggers permission, debug-vs-deploy bindings) is [trigger-not-firing.md](./trigger-not-firing.md). Use it for "events occur but no job/instance starts"; use this playbook when a `DAP-RT-105x` code is emitted during trigger evaluation.

## Investigation

1. **Classify the code first.** `1052` (NoMatches) is a debug-mode-only signal — it will not appear in runtime execution telemetry, so it is not a runtime fault to investigate. For `1053`, the fault is in connector configuration (null/empty object name or operation), not a user-settable field — route to escalation, not workflow edits.
2. **Read the connection resource file** — identify the connector and connection (see "Connection Resource File" in [overview.md](../overview.md)).
3. `uip is connections ping <connection-id>` — verify the trigger's connection is active (primary cause of `1051`).
4. `uip is triggers objects <connector-key> <operation>` / `uip is triggers describe ...` — verify the trigger object type and expected payload schema.
5. For `1050`: inspect the provider payload (from logs/`RequestId`) for the missing event ID — a provider-side or subscription-config problem.

## Resolution

- **`DAP-RT-1051` — connection inactive:** re-authenticate via `uip is connections edit <connection-id>` (see [connection-auth-expired.md](./connection-auth-expired.md) for auth-expiry).
- **`DAP-RT-1051` — endpoint issue:** verify the trigger object/operation is still supported by the connector; reconfigure if the connector changed.
- **`DAP-RT-1050`:** verify the subscription in the external service emits the expected event shape; recreate the trigger subscription if the payload contract drifted.
- **`DAP-RT-1053` (escalate — not customer-fixable):** the trigger object name or operation is null/empty, set by connector configuration. The customer cannot fix this from their workflow. Escalate to the Integration Service owner team with the `DAP-RT-1053` code, `RequestId`, and connector key.
- **`DAP-RT-1052`:** debug-mode-only signal — never emitted in runtime telemetry. If seen during a debug run, it just means the trigger filter matched zero events; it is not a runtime fault and needs no action.
