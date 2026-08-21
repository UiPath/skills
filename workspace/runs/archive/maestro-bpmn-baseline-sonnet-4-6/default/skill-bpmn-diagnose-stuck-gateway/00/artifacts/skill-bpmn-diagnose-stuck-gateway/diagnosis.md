# BPMN Run Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Status:** Parked (never faulted, never completed)

---

## Diagnostic steps performed

The following `uip maestro bpmn` reads were executed in priority-ladder order:

| Step | Command | Result |
|------|---------|--------|
| 2 | `instance incidents inst-triage-001 -f folder-public --output json` | No incidents — run never faulted |
| 3 | `instance variables inst-triage-001 -f folder-public --output json` | Command unmocked; variables not available |
| 4 | `instance asset inst-triage-001 -f folder-public --output json` | Command unmocked; deployed asset not available |
| 5 | `instance element-executions inst-triage-001 -f folder-public --output json` | **Root cause identified** (see below) |
| 5 | `instance cursors inst-triage-001 -f folder-public --output json` | **Confirmed** (see below) |

---

## Element executions

| Element ID | Type | State |
|------------|------|-------|
| `Start_Manual` | startEvent | Completed |
| `ServiceTask_Score` | serviceTask | Completed |
| `Gw_ApprovalRoute` | exclusiveGateway | **Waiting** |

The gateway evaluated two outgoing sequence flows and neither resolved to `true`:

| Flow ID | Condition expression | Evaluated |
|---------|---------------------|-----------|
| `Flow_HighRisk` | `=vars.riskScore > 80` | `false` |
| `Flow_LowRisk` | `=vars.riskScore < 20` | `false` |

`hasDefaultFlow: false` — no default (unconditional) outgoing flow is configured.

---

## Cursor state

The runtime cursor is **Blocked** at `Gw_ApprovalRoute`:

> "No outgoing sequence-flow condition evaluated true and no default flow is defined;
> the token cannot advance."

The cursor has been in this state since `2026-05-01T12:03:00Z`.

---

## Root cause

The exclusive gateway `Gw_ApprovalRoute` covers only the extreme tails of the
`riskScore` distribution (`> 80` or `< 20`). A mid-range value (20 ≤ riskScore ≤ 80)
satisfies neither condition. Because no default sequence flow is defined on the
gateway, the BPMN runtime has no path to route the token and the instance stalls
indefinitely without raising a fault.

---

## Conclusion

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched (riskScore was in the uncovered range 20–80) and the gateway has no default flow.

---

## Recommended fix (Author action — requires explicit user consent before any cloud change)

Add a **default sequence flow** to `Gw_ApprovalRoute` in the BPMN source so that
any `riskScore` value not caught by the explicit conditions is routed to a
well-defined downstream path (e.g. a "medium-risk" task or a reject/review lane).
In BPMN XML, set the `default` attribute on the gateway element to the ID of the
fallback sequence flow and remove the `conditionExpression` child from that flow.
After the source fix, repackage, re-upload, and re-publish; then retry or migrate
the stuck instance per the Operate guide.
