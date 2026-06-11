# Governance (Insights RTM) Reference

> Requires `@uipath/uipath-typescript` **≥ 1.4.0**. Scopes: `Insights Insights.RealTimeData`. Governance endpoints expect an **elevated (org-admin) caller** — `fullOrganization: true` returns 403 without org-admin rights; if a tenant-scoped call 403s, tell the user their account lacks governance access.

```typescript
import { Governance, PolicyEvaluationResult } from '@uipath/uipath-typescript/governance';
const svc = new Governance(sdk as never)
```

Both methods take a **required positional `startTime: Date`** first; everything else lives in the options object.

## getPolicyTraces(startTime: Date, options?)

Per-policy enforcement decisions, one row per policy verdict per event (one user action can yield multiple rows). Ordered by event start time desc. Returns `NonPaginatedResponse<GovernancePolicyTrace>` (or paginated). **Rows are on `.items`.**

Options (`GovernancePolicyTraceGetAllOptions`): `endTime?: Date`, `fullOrganization?: boolean`, `evaluationResult?: PolicyEvaluationResult[]`, `policyId?: string[]`, `actorProcessId?: string[]`, `actorProcessType?: string[]`, `actorIdentityId?: string[]`, `resourceId?: string[]`, `resourceType?: string[]`, `traceId?: string[]` + pagination. Filters AND across fields, OR within an array.

`PolicyEvaluationResult` enum: `Allow`, `Deny`, `SimulatedAllow`, `SimulatedDeny`.

`GovernancePolicyTrace` fields: `tenantId`, `startTime`, `finalEnforcement`, `policyId`, `policyEnforcement`, `policyEvaluationResult`, `policyName`, `policyStatus`, `policyEvaluationDetails`, `actorProcessId`, `actorProcessType`, `actorIdentityId`, `resourceId`, `resourceType`, `folderKey`, `traceId`, `processKey`, `jobKey`. All optional except `startTime`.

**Example response** (`.items` — shape from SDK test fixtures):

```json
{
  "items": [
    {
      "tenantId": "t-2298", "startTime": "2026-06-10T14:03:22Z",
      "finalEnforcement": "Deny", "policyId": "pol-7f3a", "policyEnforcement": "Deny",
      "policyEvaluationResult": "Deny", "policyName": "Block external LLM calls",
      "policyStatus": "Active", "actorProcessId": "InvoiceTriageAgent",
      "actorProcessType": "CodedAgent", "actorIdentityId": "user-91",
      "resourceId": "openai.com", "resourceType": "ExternalService",
      "folderKey": "f-1001", "traceId": "tr-...", "processKey": "p-0088", "jobKey": "j-..."
    }
  ],
  "count": 1
}
```

## getOperationSummary(startTime: Date, options?)

Aggregate enforcement counts for the window. Options: `{ endTime?: Date, fullOrganization?: boolean }`. Returns a **single object — not an array**:

```json
{ "totalEvaluations": 1240, "allowedCount": 1180, "deniedCount": 42, "noOpCount": 18 }
```

> **Semantics:** the SDK maps raw `allow`/`deny`/`noOp` → `allowedCount`/`deniedCount`/`noOpCount`. For a kpi-card or donut, the `fnBody` must wrap/transform the object into a row array (see patterns). No policy UUID is required — this summarizes all policies.

## fnBody patterns

```typescript
// Denied actions (data-table)
const { Governance, PolicyEvaluationResult } = await import('@uipath/uipath-typescript/governance')
const result = await new Governance(sdk as never).getPolicyTraces(SEVEN_DAYS_AGO, {
  endTime: NOW,
  evaluationResult: [PolicyEvaluationResult.Deny, PolicyEvaluationResult.SimulatedDeny],
})
return result?.items ?? []
```

```typescript
// Allow / Deny / NoOp breakdown (donut-chart: xKey name, yKey value)
const { Governance } = await import('@uipath/uipath-typescript/governance')
const s = await new Governance(sdk as never).getOperationSummary(SEVEN_DAYS_AGO, { endTime: NOW })
return [
  { name: 'Allowed', value: s.allowedCount },
  { name: 'Denied', value: s.deniedCount },
  { name: 'Simulated', value: s.noOpCount },
]
```
