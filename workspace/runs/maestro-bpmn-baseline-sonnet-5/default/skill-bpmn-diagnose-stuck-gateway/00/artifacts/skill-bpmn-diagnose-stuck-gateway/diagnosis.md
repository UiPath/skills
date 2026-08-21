# Diagnosis: Stuck Maestro BPMN Run

- **Instance ID:** inst-triage-001
- **Folder key:** folder-public

## Investigation

Read-only diagnostic commands used (with folder context):

```bash
uip maestro bpmn instance get inst-triage-001 -f folder-public --output json
uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json
uip maestro bpmn instance element-executions inst-triage-001 -f folder-public --output json
uip maestro bpmn instance cursors inst-triage-001 -f folder-public --output json
uip maestro bpmn instance variables inst-triage-001 -f folder-public --output json
```

`instance get` and `instance incidents` returned no data for this run (consistent
with the run never faulting — there is no incident to inspect). `instance
variables` was also not available for this instance.

### Element executions

```json
[
  { "elementId": "Start_Manual", "elementType": "startEvent", "state": "Completed" },
  { "elementId": "ServiceTask_Score", "elementType": "serviceTask", "state": "Completed" },
  {
    "elementId": "Gw_ApprovalRoute",
    "elementType": "exclusiveGateway",
    "state": "Waiting",
    "outgoingEvaluations": [
      { "flowId": "Flow_HighRisk", "conditionExpression": "=vars.riskScore > 80", "evaluated": false },
      { "flowId": "Flow_LowRisk", "conditionExpression": "=vars.riskScore < 20", "evaluated": false }
    ],
    "hasDefaultFlow": false,
    "note": "No outgoing condition evaluated true and the gateway has no default flow."
  }
]
```

The token progressed through `Start_Manual` and `ServiceTask_Score` (both
Completed), then arrived at the exclusive gateway `Gw_ApprovalRoute`, which is
still in the `Waiting` state. Both outgoing sequence-flow conditions
(`Flow_HighRisk`: `vars.riskScore > 80`, `Flow_LowRisk`: `vars.riskScore < 20`)
did not evaluate true, and the gateway has no default flow (`hasDefaultFlow:
false`).

### Cursors

```json
[
  {
    "elementId": "Gw_ApprovalRoute",
    "elementType": "exclusiveGateway",
    "state": "Blocked",
    "blockedReason": "No outgoing sequence-flow condition evaluated true and no default flow is defined; the token cannot advance.",
    "since": "2026-05-01T12:03:00Z"
  }
]
```

The cursor confirms the single active token is parked at `Gw_ApprovalRoute` in
a `Blocked` state, with the runtime's own blocked reason matching the
element-execution note.

## Root cause

The exclusive gateway `Gw_ApprovalRoute` evaluates a risk score (`vars.riskScore`)
that apparently falls in the gap between the two modeled branches (not `> 80`
and not `< 20`, e.g. a mid-range score). Because neither outgoing condition
matched and no default flow was configured on the gateway, the runtime has no
sequence flow to take. The instance is therefore parked indefinitely at this
gateway — it never faults (no incident is raised for an unresolved gateway
wait) and never completes (the token has nowhere to go).

Fix ownership: BPMN source (Author) — add a default flow on
`Gw_ApprovalRoute`, or widen/adjust the outgoing conditions on
`Flow_HighRisk` / `Flow_LowRisk` so every possible `riskScore` value is
covered.

## Safe next action

No mutating action was taken. Resolving this requires either fixing the BPMN
source (adding a default flow / adjusting conditions) and redeploying, or an
explicit, user-consented Operate action (e.g. cursor movement) — neither was
performed as part of this diagnosis.

---

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched and the gateway has no default flow, so the token cannot advance.
