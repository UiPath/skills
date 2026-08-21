# BPMN Run Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Symptom:** Run is parked mid-flow — never faulted, never completed.

---

## Diagnostic steps

### Step 2 — Incidents
`uip maestro bpmn instance incidents inst-triage-001 -f folder-public` returned no
incidents. The instance has not faulted, confirming the run is silently stuck rather
than errored.

### Step 5 — Element executions and cursors

**Element executions** (`uip maestro bpmn instance element-executions`):

| Element ID | Type | State |
|---|---|---|
| `Start_Manual` | startEvent | Completed |
| `ServiceTask_Score` | serviceTask | Completed |
| `Gw_ApprovalRoute` | exclusiveGateway | **Waiting** |

The gateway evaluation log shows both outgoing flows were tested and neither
returned `true`:

| Flow ID | Condition | Result |
|---|---|---|
| `Flow_HighRisk` | `=vars.riskScore > 80` | `false` |
| `Flow_LowRisk` | `=vars.riskScore < 20` | `false` |

`hasDefaultFlow: false` — no fallback path exists.

**Cursor** (`uip maestro bpmn instance cursors`):

```
elementId:     Gw_ApprovalRoute
elementType:   exclusiveGateway
state:         Blocked
blockedReason: No outgoing sequence-flow condition evaluated true and no default
               flow is defined; the token cannot advance.
since:         2026-05-01T12:03:00Z
```

The token has been parked at this gateway since 2026-05-01T12:03:00Z.

---

## Conclusion

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched (riskScore fell in the gap between the two guards) and the gateway has no default flow, so the token cannot advance.

---

## Root cause

The exclusive gateway `Gw_ApprovalRoute` has exactly two outgoing sequence flows:

- `Flow_HighRisk` — condition `=vars.riskScore > 80`
- `Flow_LowRisk`  — condition `=vars.riskScore < 20`

At runtime the score landed in the range **[20, 80]**, which satisfies neither
condition. Because no `default` attribute is set on the gateway element, the BPMN
specification requires the runtime to throw a fault or stall — here it stalls.

## Fix (Author action — no cloud mutation required)

The BPMN source needs one of the following corrections before repackaging:

1. **Add a default flow.** Set `default="Flow_LowRisk"` (or a new `Flow_Medium`)
   on `<bpmn:exclusiveGateway id="Gw_ApprovalRoute">` and remove the condition from
   that flow's `<bpmn:conditionExpression>`.
2. **Close the gap.** Change one guard to cover the middle band, e.g.
   `=vars.riskScore >= 20` for `Flow_LowRisk`, ensuring every possible score
   routes somewhere.

No retry, cancel, cursor move, or cloud change should be made until the source
defect is corrected and redeployed.
