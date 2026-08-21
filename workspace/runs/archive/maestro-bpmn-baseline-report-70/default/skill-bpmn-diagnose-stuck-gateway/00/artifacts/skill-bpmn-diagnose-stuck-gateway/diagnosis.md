# BPMN Run Diagnosis — inst-triage-001

## Summary

The instance never faulted and never completed. It is parked mid-flow at an
exclusive gateway whose outgoing sequence-flow conditions both evaluated false
and which has no default (fallback) flow, so the runtime token cannot advance.

## Diagnostic trace

**Folder context:** `folder-public`  
**Instance ID:** `inst-triage-001`

### Step 1 — Incidents

The manifest exposes no incident endpoint for this instance (the run was not
faulted; it is in a stalled/blocked state). No incidents were raised.

### Step 2 — Element executions

```
uip maestro bpmn instance element-executions inst-triage-001 -f folder-public --output json
```

| Element ID | Type | State |
|---|---|---|
| `Start_Manual` | startEvent | **Completed** |
| `ServiceTask_Score` | serviceTask | **Completed** |
| `Gw_ApprovalRoute` | exclusiveGateway | **Waiting** |

Outgoing flow evaluations on `Gw_ApprovalRoute`:

| Flow | Condition | Evaluated |
|---|---|---|
| `Flow_HighRisk` | `=vars.riskScore > 80` | `false` |
| `Flow_LowRisk` | `=vars.riskScore < 20` | `false` |

`hasDefaultFlow: false`

### Step 3 — Cursors

```
uip maestro bpmn instance cursors inst-triage-001 -f folder-public --output json
```

The single active cursor is parked on `Gw_ApprovalRoute` with state `Blocked`:

> "No outgoing sequence-flow condition evaluated true and no default flow is
> defined; the token cannot advance."

The cursor has been blocked since `2026-05-01T12:03:00Z`.

## Conclusion

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched (riskScore was between 20 and 80, satisfying neither Flow_HighRisk nor Flow_LowRisk) and the gateway has no default flow.

## Fix ownership

The defect lives in **BPMN source** (Author):

1. Add a default flow to `Gw_ApprovalRoute` (set the `default` attribute on
   the gateway to a catch-all sequence flow) to handle values that fall
   between the two explicit conditions, **or**
2. Widen / close the gap in the conditions so they are mutually exhaustive
   (e.g. `riskScore >= 20 && riskScore <= 80` as the third branch), **or**
3. Combine both: a third named branch plus a default as a final safety net.

## Safe next action

No mutating action should be taken until root cause is confirmed with the
process owner. After source is fixed, the corrected package must be uploaded
and published before any retry or cursor-move operation is performed.
