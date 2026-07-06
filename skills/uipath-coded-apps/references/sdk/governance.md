# Governance (Insights RTM) Reference

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/governance/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

> Requires `@uipath/uipath-typescript` **≥ 1.4.1**. Scopes: `Insights Insights.RealTimeData`. Governance endpoints expect an **elevated (org-admin) caller** — `fullOrganization: true` returns 403 without org-admin rights; if a tenant-scoped call 403s, tell the user their account lacks governance access.

This service answers the **platform governance** question — policy enforcement verdicts (allow/deny) on user and agent actions across the platform. For **agentic runtime governance** (per-hook policy checks inside agent runs — standards packs, rule violations) → [`sdk/governance-traces.md`](governance-traces.md), a different domain.

```typescript
import { Governance, PolicyEvaluationResult } from '@uipath/uipath-typescript/governance';
const svc = new Governance(sdk)
```

Both methods take a **required positional `startTime: Date`** first; everything else lives in the options object.

Return shapes and server-side behavior the types don't show:

| Method | Returns | Notes |
|--------|---------|-------|
| `getPolicyTraces(startTime, options?)` | **rows on `.items`** (`NonPaginatedResponse<GovernancePolicyTrace>`, or paginated) | One row per policy verdict per event (one user action can yield multiple rows). Ordered by event start time desc. Filters AND across fields, OR within an array |
| `getOperationSummary(startTime, options?)` | **single object — not an array**: `{ totalEvaluations, allowedCount, deniedCount, noOpCount }` | Summarizes ALL policies — no policy UUID required |

> **Semantics:** the SDK maps raw `allow`/`deny`/`noOp` → `allowedCount`/`deniedCount`/`noOpCount`. For a kpi-card or donut, the `fnBody` must wrap/transform the object into a row array (see patterns).

## fnBody patterns

```typescript
// Denied actions (data-table)
const { Governance, PolicyEvaluationResult } = await import('@uipath/uipath-typescript/governance')
const result = await new Governance(sdk).getPolicyTraces(SEVEN_DAYS_AGO, {
  endTime: NOW,
  evaluationResult: [PolicyEvaluationResult.Deny, PolicyEvaluationResult.SimulatedDeny],
})
return (result?.items ?? []).map(x => ({ ...x }))
```

```typescript
// Allow / Deny / NoOp breakdown (donut-chart: xKey name, yKey value)
const { Governance } = await import('@uipath/uipath-typescript/governance')
const s = await new Governance(sdk).getOperationSummary(SEVEN_DAYS_AGO, { endTime: NOW })
return [
  { name: 'Allowed', value: s.allowedCount },
  { name: 'Denied', value: s.deniedCount },
  { name: 'Simulated', value: s.noOpCount },
]
```
