# BPMN Run Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Run status:** Running (never faulted, never completed — token is parked mid-flow)

---

## Diagnostic summary

### Element executions

| Element ID | Type | State |
|---|---|---|
| `Start_Manual` | startEvent | Completed |
| `ServiceTask_Score` | serviceTask | Completed |
| `Gw_ApprovalRoute` | exclusiveGateway | **Waiting** |

The exclusive gateway `Gw_ApprovalRoute` entered `Waiting` state and has not exited.  
Its two outgoing sequence-flow conditions were evaluated at runtime:

| Flow ID | Condition | Result |
|---|---|---|
| `Flow_HighRisk` | `=vars.riskScore > 80` | false (not evaluated to true) |
| `Flow_LowRisk` | `=vars.riskScore < 20` | false (not evaluated to true) |

Neither condition matched the actual value of `vars.riskScore` (which falls in the range 20–80,
i.e. between the two thresholds and therefore true for neither branch).

### Cursor

The live cursor for the instance is parked at `Gw_ApprovalRoute` (state: **Blocked**) since
`2026-05-01T12:03:00Z`:

> "No outgoing sequence-flow condition evaluated true and no default flow is defined;
> the token cannot advance."

The gateway has `hasDefaultFlow: false`, so the BPMN runtime has no fallback path to take.

---

## Root cause

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched (riskScore is between the two thresholds) and the gateway has no default flow.

---

## Fix (author action required — no cloud mutation)

In the BPMN source, add a default sequence flow on `Gw_ApprovalRoute` (set the `default`
attribute on the gateway to point to a new or existing flow that handles the mid-range case),
or add a third outgoing condition that covers `vars.riskScore >= 20 && vars.riskScore <= 80`.
After editing the source, repackage and redeploy; then migrate or cancel the stuck instance
with explicit user consent.
