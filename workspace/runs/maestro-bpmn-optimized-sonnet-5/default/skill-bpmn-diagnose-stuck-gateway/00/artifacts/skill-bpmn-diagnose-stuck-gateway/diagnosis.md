# Diagnosis: Stuck Maestro BPMN Run

- Instance ID: inst-triage-001
- Folder key: folder-public

## Method

Followed the diagnose priority ladder using read-only `uip maestro bpmn instance ...`
commands scoped to the folder:

1. `uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json`
   → no incident data available, consistent with a run that never faulted.
2. `uip maestro bpmn instance variables inst-triage-001 -f folder-public --output json`
   → not available in this environment; not required to establish root cause.
3. `uip maestro bpmn instance element-executions inst-triage-001 -f folder-public --output json`
   → shows the token progressed through `Start_Manual` (Completed) and
     `ServiceTask_Score` (Completed), then reached `Gw_ApprovalRoute`
     (exclusiveGateway), which is in state `Waiting`. Its two outgoing
     evaluations (`Flow_HighRisk`: `=vars.riskScore > 80`, `Flow_LowRisk`:
     `=vars.riskScore < 20`) both report `evaluated: false`, and
     `hasDefaultFlow` is `false`. The execution record's own note states:
     "No outgoing condition evaluated true and the gateway has no default flow."
4. `uip maestro bpmn instance cursors inst-triage-001 -f folder-public --output json`
   → confirms a single active cursor parked at `Gw_ApprovalRoute`, state
     `Blocked`, with `blockedReason`: "No outgoing sequence-flow condition
     evaluated true and no default flow is defined; the token cannot advance."

Both element-executions and cursors independently agree on the same element
and the same root cause, so no deployed-asset comparison was needed to
resolve ambiguity.

## Conclusion

The run never faults because there is no error — the exclusive gateway
`Gw_ApprovalRoute` simply cannot select an outgoing sequence flow given the
current `riskScore` value (apparently between 20 and 80 inclusive, satisfying
neither `Flow_HighRisk` nor `Flow_LowRisk`), and the gateway has no default
flow to fall back on. The token is permanently parked at the gateway with
nowhere to go, so the instance is stuck mid-flow instead of completing or
faulting.

**Fix belongs in BPMN source (Author):** add a default flow on
`Gw_ApprovalRoute` (or widen/adjust the existing conditions so they are
exhaustive) so every possible `riskScore` value routes somewhere.

**Safe next action:** none taken here (diagnosis only). Once the source fix
is authored and republished, an explicit-consent Operate action (e.g. cursor
move/retry on the existing instance, or letting new instances run the fixed
process) would be required — not performed as part of this diagnosis.

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched at exclusive gateway Gw_ApprovalRoute and the gateway has no default flow, so the token cannot advance.
