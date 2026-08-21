# Run Diagnosis — inst-triage-001

## Summary

The process instance `inst-triage-001` is parked and has not faulted.
Control flow reached an exclusive gateway after the service task completed, but
the gateway cannot route the token to any outgoing path, so the instance
remains indefinitely blocked.

## Diagnostic trace (Step 5 — element executions and cursors)

| Step | Element ID | Type | State |
|------|-----------|------|-------|
| 1 | `Start_Manual` | startEvent | Completed |
| 2 | `ServiceTask_Score` | serviceTask | Completed |
| 3 | `Gw_ApprovalRoute` | exclusiveGateway | **Waiting / Blocked** |

### Outgoing flow evaluations at `Gw_ApprovalRoute`

| Flow ID | Condition | Result |
|---------|-----------|--------|
| `Flow_HighRisk` | `=vars.riskScore > 80` | `false` (not evaluated true) |
| `Flow_LowRisk` | `=vars.riskScore < 20` | `false` (not evaluated true) |

`hasDefaultFlow: false` — no fallback route is modelled.

The cursor confirms the token has been blocked at this gateway since
`2026-05-01T12:03:00Z`.

## Root cause

The runtime value of `vars.riskScore` falls between 20 and 80 (inclusive),
so neither outgoing condition expression evaluates to `true`.
Because the exclusive gateway declares **no default flow**, the BPMN runtime
has no route to take and the token stalls permanently.
No fault is raised; the instance simply never advances.

## Labels

STUCK_ELEMENT: Gw_ApprovalRoute
STUCK_REASON: No outgoing condition matched (riskScore is between 20 and 80) and the gateway has no default flow.

## Recommended fix (authoring — no cloud change required)

In the BPMN source, add a default sequence flow on `Gw_ApprovalRoute` that
routes mid-range scores to an appropriate path, **or** add a third outgoing
condition expression `=vars.riskScore >= 20 && vars.riskScore <= 80` covering
the missing band.  After the source change, repackage and redeploy; then, with
explicit user consent, migrate or cancel and restart the stuck instance.

> **No mutations were performed during this diagnosis.**
> Retry, cancel, migrate, and cursor movement require explicit user consent.
