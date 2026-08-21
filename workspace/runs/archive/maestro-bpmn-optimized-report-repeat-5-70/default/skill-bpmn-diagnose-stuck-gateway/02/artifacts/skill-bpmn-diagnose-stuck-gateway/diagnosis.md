# BPMN Run Diagnosis — inst-triage-001

## Summary

Instance `inst-triage-001` (folder: `folder-public`) is parked mid-flow. The
run never raised an incident and never reached an end event. Diagnostic reads
via `uip maestro bpmn instance element-executions` and
`uip maestro bpmn instance cursors` locate the blocked token.

## Element execution trace

| Element ID | Type | State |
|---|---|---|
| `Start_Manual` | startEvent | Completed |
| `ServiceTask_Score` | serviceTask | Completed |
| `Gw_ApprovalRoute` | exclusiveGateway | **Waiting / Blocked** |

## Cursor state

The runtime cursor is parked at `Gw_ApprovalRoute` (blocked since
`2026-05-01T12:03:00Z`). No downstream element has been entered.

## Gateway evaluation details

The exclusive gateway `Gw_ApprovalRoute` has two outgoing sequence flows:

| Flow ID | Condition | Evaluated true? |
|---|---|---|
| `Flow_HighRisk` | `=vars.riskScore > 80` | false |
| `Flow_LowRisk` | `=vars.riskScore < 20` | false |

`hasDefaultFlow: false` — the gateway defines no default (unconditional) exit
path.

Because `vars.riskScore` fell in the range 20–80, neither condition matched, and
there is no default flow to fall back to. The BPMN runtime cannot advance the
token and has no fault to raise, so the instance stalls indefinitely.

## Conclusion

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched (riskScore was between 20 and 80) and the gateway has no default flow, so the token cannot advance.

## Fix (authoring, requires separate consent)

In the BPMN source, add a `default` attribute on `Gw_ApprovalRoute` pointing to
a catch-all sequence flow (e.g. `Flow_MediumRisk`), or add a third condition
branch that covers the unhandled range. Re-package and re-deploy after the fix.
No runtime mutation (retry, cursor move, cancel) is recommended until the BPMN
source defect is corrected.
