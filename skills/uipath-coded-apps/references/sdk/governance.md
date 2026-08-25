# Governance (Insights RTM) Reference

Signatures/params/examples: `dist/governance/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

This service answers the **platform governance** question — policy enforcement verdicts (allow/deny) on user and agent actions across the platform. For **agentic runtime governance** (per-hook policy checks inside agent runs — standards packs, rule violations) → [`sdk/governance-traces.md`](governance-traces.md), a different domain.

On a 403 (org-admin gating — see the `fullOrganization` JSDoc): tell the user their account lacks governance access; do not retry.

`getOperationSummary` returns a **single object — not an array**. For a kpi-card or donut, the `fnBody` must wrap/transform it into a row array (see patterns).

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
