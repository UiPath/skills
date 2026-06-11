# Agents & Agent Memory (Insights RTM) Reference

> Requires `@uipath/uipath-typescript` **≥ 1.4.0**. Scopes: `Insights Insights.RealTimeData`.

Two services, **two different calling conventions** — do not mix them up:

| Service | Subpath | Convention |
|---------|---------|------------|
| `Agents` | `@uipath/uipath-typescript/agents` | **Positional `Date` args**: `getAll(startTime, endTime, options?)` |
| `AgentMemory` | `@uipath/uipath-typescript/agent-memory` | **Options object**: `getTimeline({ startTime?, endTime?, ... })` — dates inside the object |

## Agents Service

```typescript
import { Agents, AgentListSortColumn } from '@uipath/uipath-typescript/agents';
const svc = new Agents(sdk as never)
```

### getAll(startTime: Date, endTime: Date, options?: AgentListOptions)

The agent list with consumption + health metadata aggregated over the window. Returns `NonPaginatedResponse<AgentListItem>` (or `PaginatedResponse` with pagination options). **Rows are on `.items`.**

`AgentListOptions`: `folderKeys?: string[]`, `agentNames?: string[]`, `projectKeys?: string[]`, `agentId?: string`, `processVersion?: string`, `orderBy?: { column: AgentListSortColumn, desc?: boolean }` + pagination (`pageSize`, `cursor`, `jumpToPage`).

`AgentListSortColumn`: `AgentName`, `ParentProcess`, `LastRun`, `HealthScore`, `LastIncident`, `FolderName`, `QuantityAGU`, `QuantityPLTU`, `FolderPath`.

`AgentListItem` fields: `agentId`, `agentName`, `parentProcess`, `folderKey`, `folderName`, `folderPath`, `lastRun`, `processKey`, `processVersion`, `healthScore` (0–100), `lastIncidentType`, `unitsQuantity`, `unitsName`, `quantityAGU`, `quantityPLTU`. Nullable: `parentProcess`, `folderKey/Name/Path`, `processKey`, `processVersion`, `lastIncidentType`, `unitsName` (may be `null` or `""`).

**Example response** (`.items` — field names exact, values illustrative):

```json
{
  "items": [
    {
      "agentId": "ag-0001", "agentName": "InvoiceTriageAgent",
      "parentProcess": "InvoiceFlow", "folderKey": "f-1001", "folderName": "Finance",
      "folderPath": "Finance", "lastRun": "2026-06-10T18:22:00Z",
      "processKey": "p-0088", "processVersion": "1.2.0",
      "healthScore": 92, "lastIncidentType": null,
      "unitsQuantity": 340, "unitsName": "AGU", "quantityAGU": 340, "quantityPLTU": 0
    },
    {
      "agentId": "ag-0002", "agentName": "ContractReviewAgent",
      "parentProcess": null, "folderKey": "f-1001", "folderName": "Finance",
      "folderPath": "Finance", "lastRun": "2026-06-10T16:05:00Z",
      "processKey": null, "processVersion": null,
      "healthScore": 58, "lastIncidentType": "Error",
      "unitsQuantity": 1210, "unitsName": "AGU", "quantityAGU": 1210, "quantityPLTU": 12
    }
  ],
  "count": 2
}
```

> **Semantics:** this is the ONLY Agents method in SDK 1.4.0. There is **no error timeline, latency timeline, consumption timeline, or top-errored endpoint** — do not invent `getErrorsTimeline` / `getConsumptionTimeline` / `getLatencyTimeline` / `getTopErroredAgents`. Per-agent totals (`quantityAGU`, `healthScore`) support KPIs and ranked tables, not time-series charts. For agent run/error *trends*, use the Jobs SDK with `ProcessType eq 'Agent'` (see `sdk/orchestrator.md § Job classification`).

### fnBody patterns

```typescript
// Count of active agents (kpi-card)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk as never).getAll(THIRTY_DAYS_AGO, NOW)
return [{ count: result?.items?.length ?? 0 }]
```

```typescript
// Agents ranked by AGU consumption (ranked-table)
const { Agents, AgentListSortColumn } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk as never).getAll(THIRTY_DAYS_AGO, NOW, {
  orderBy: { column: AgentListSortColumn.QuantityAGU, desc: true },
})
return result?.items ?? []
```

## AgentMemory Service

```typescript
import { AgentMemory, AgentMemoryExecutionType } from '@uipath/uipath-typescript/agent-memory';
const svc = new AgentMemory(sdk as never)
```

All three methods take ONE optional options object — `{ startTime?: Date, endTime?: Date, agentId?, agentVersion?, folderKeys?, executionType? }` (`AgentMemoryExecutionType.Debug | Runtime`; omit for both). Window defaults to the **last 24 hours**. All three return a **bare array** — no `.items` / `.data` unwrapping needed.

| Method | Returns (bare array of) | Use for |
|--------|------------------------|---------|
| `getTimeline(options?)` | `{ timeSlice, inMemoryCount, notInMemoryCount, totalCount, enabledMemoryCount, disabledMemoryCount }` | Memory state over time (line/area chart) |
| `getCallsTimeline(options?)` | `{ timeSlice, memoryCallsCount }` | Memory access volume over time |
| `getTopSpaces(options?)` | `{ memorySpaceId, memorySpaceName, memoryCount, enabledMemoryCount, disabledMemoryCount }` | Top memory spaces (ranked; `limit?` option, default 5) |

**Example response** — `getTimeline()` (values from SDK test fixtures):

```json
[
  { "timeSlice": "2026-06-10T00:00:00Z", "inMemoryCount": 3, "notInMemoryCount": 1, "totalCount": 4, "enabledMemoryCount": 2, "disabledMemoryCount": 2 },
  { "timeSlice": "2026-06-10T01:00:00Z", "inMemoryCount": 5, "notInMemoryCount": 0, "totalCount": 5, "enabledMemoryCount": 5, "disabledMemoryCount": 0 }
]
```

### fnBody pattern

```typescript
// Memory calls over the last 7 days (area-chart: xKey timeSlice, yKey memoryCallsCount)
const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')
return await new AgentMemory(sdk as never).getCallsTimeline({ startTime: SEVEN_DAYS_AGO, endTime: NOW })
```
