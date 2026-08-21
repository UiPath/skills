# BPMN Run Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Status:** Parked (never faulted, never completed)

---

## Diagnostic Summary

The instance ran successfully through its first two elements and then stalled at
an exclusive gateway. It has been blocked since `2026-05-01T12:03:00Z`.

### Element Execution Trail

| Element ID | Type | State |
|---|---|---|
| `Start_Manual` | startEvent | Completed |
| `ServiceTask_Score` | serviceTask | Completed |
| `Gw_ApprovalRoute` | exclusiveGateway | **Waiting / Blocked** |

### Cursor State

The active cursor is parked on `Gw_ApprovalRoute`. No downstream element has
ever been entered.

### Gateway Outgoing-Flow Evaluation

The gateway has two outgoing sequence flows. Neither condition evaluated true
at the time the token arrived:

| Flow ID | Condition | Evaluated True? |
|---|---|---|
| `Flow_HighRisk` | `=vars.riskScore > 80` | false |
| `Flow_LowRisk` | `=vars.riskScore < 20` | false |

The runtime value of `vars.riskScore` lies in the range **[20, 80]** (neither
condition's branch was taken). No default flow (`bpmn:exclusiveGateway
default="…"`) is defined on `Gw_ApprovalRoute`, so the runtime has no path to
follow and the token is permanently blocked.

---

## Root Cause

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched and the gateway has no default flow.

---

## Fix (Author action required)

The BPMN source needs one of the following corrections:

1. **Add a default flow** — set `default="Flow_MediumRisk"` (or a new flow) on
   `Gw_ApprovalRoute` and remove its `conditionExpression` so any score not
   caught by the two explicit branches is safely routed.
2. **Cover the gap with a third condition** — add
   `=vars.riskScore >= 20 and vars.riskScore <= 80` on a third outgoing flow.

Retry or cursor movement should only be attempted after the BPMN source defect
is fixed, re-packaged, and a new version is published. This is an Operate action
that requires explicit user consent.
