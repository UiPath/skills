# Agents & Agent Memory (Insights RTM) Reference

> Requires `@uipath/uipath-typescript` **≥ 1.4.1**. Scopes: `Insights Insights.RealTimeData`.

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

> **Semantics:** `getAll` returns per-agent totals (`quantityAGU`, `healthScore`, `lastIncidentType`) — good for KPIs and ranked tables. For *time-series* (error / latency / consumption trends) use the dedicated timeline methods below — all added in SDK 1.4.1. There is still **no invocation-count timeline** and **no per-percentile method other than `getLatencyTimeline`**.

### getErrors(startTime: Date, endTime: Date, options?: AgentGetErrorsOptions)

Agent error classes (incidents) observed in the window, ranked. Returns `NonPaginatedResponse<AgentError>` (or `PaginatedResponse` with pagination options). **Rows are on `.items`.**

`AgentGetErrorsOptions`: filters (`folderKeys`, `agentNames`, `projectKeys`, `agentId`, `processVersion`) + `orderBy?: { column: AgentErrorSortColumn, desc?: boolean }` + pagination. `AgentErrorSortColumn`: `ExecutionCount`, `ErrorTitle`, `Type`, … (import from `@uipath/uipath-typescript/agents`).

`AgentError` fields: `type`, `description`, `agentId`, `agentName`, `jobKey`, `parentProcess`, `firstSeen`, `folderKey`, `folderName`, `folderPath`, `count`, `firstSeenJob`, `lastSeenJob`.

```json
{ "items": [
  { "type": "ToolError", "description": "Tool 'search' timed out", "agentId": "ag-0002", "agentName": "ContractReviewAgent", "count": 14, "firstSeen": "2026-06-02T09:11:00Z", "folderName": "Finance" }
], "count": 1 }
```

### getErrorsTimeline(startTime: Date, endTime: Date, options?)

Time-series of error counts grouped by agent. Returns a **bare array** `[{ name, value, date }]` — `name` is the agent name, `value` the error count, `date` the bucket. Options: filters + `limit?` (top-N agents, default 10).

```json
[ { "name": "ContractReviewAgent", "value": 6, "date": "2026-06-02" },
  { "name": "InvoiceTriageAgent", "value": 1, "date": "2026-06-02" } ]
```

### getConsumptionTimeline(startTime: Date, endTime: Date, options?)

Time-series of AGU consumption. Returns a **bare array** `[{ timeSlice, aguConsumption }]` — native chart shape. Options: filters.

```json
[ { "timeSlice": "2026-06-01T00:00:00Z", "aguConsumption": 120 },
  { "timeSlice": "2026-06-02T00:00:00Z", "aguConsumption": 340 } ]
```

### getLatencyTimeline(startTime: Date, endTime: Date, options?)

Time-series of agent latency per percentile. Returns a **bare array** `[{ name, value, date }]` — `name` is the percentile (`"P50"` / `"P95"`), `value` is **milliseconds**, `date` the bucket. Options: filters.

```json
[ { "name": "P50", "value": 820, "date": "2026-06-02" },
  { "name": "P95", "value": 2400, "date": "2026-06-02" } ]
```

> **Convention:** all four timeline methods take **positional `Date` args** (`start, end`) like `getAll` — NOT an options object. Filters go in the optional third arg. Contrast with `AgentMemory` (options object) and `AgentTraces` (options object). For trace-level error/latency/consumption, see `sdk/traces.md`.

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

```typescript
// Agent errors over time — total across agents (area-chart: xKey date, yKey value)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const points = await new Agents(sdk as never).getErrorsTimeline(THIRTY_DAYS_AGO, NOW)
const byDate: Record<string, number> = {}
for (const p of points) byDate[p.date] = (byDate[p.date] ?? 0) + p.value
return Object.entries(byDate).sort().map(([date, value]) => ({ date, value }))
```

```typescript
// Agent latency P50/P95 over time — pivot long→wide (multi-line-chart: xKey date, series P50/P95)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const points = await new Agents(sdk as never).getLatencyTimeline(THIRTY_DAYS_AGO, NOW)
const byDate: Record<string, Record<string, unknown>> = {}
for (const p of points) {
  byDate[p.date] = byDate[p.date] ?? { date: p.date }
  byDate[p.date][p.name] = p.value
}
return Object.values(byDate).sort((a, b) => String(a.date).localeCompare(String(b.date)))
```

```typescript
// AGU consumption over time — native shape, return as-is (area-chart: xKey timeSlice, yKey aguConsumption)
const { Agents } = await import('@uipath/uipath-typescript/agents')
return await new Agents(sdk as never).getConsumptionTimeline(THIRTY_DAYS_AGO, NOW)
```

```typescript
// Top agent errors ranked by occurrence (ranked-table)
const { Agents, AgentErrorSortColumn } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk as never).getErrors(THIRTY_DAYS_AGO, NOW, {
  orderBy: { column: AgentErrorSortColumn.ExecutionCount, desc: true },
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
