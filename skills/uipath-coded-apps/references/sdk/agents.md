# Agents & Agent Memory (Insights RTM) Reference

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/agents/index.d.ts` and `dist/agent-memory/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

> Requires `@uipath/uipath-typescript` **≥ 1.4.1**; Insights aggregates **≥ 1.5.0**. Scopes: `Insights Insights.RealTimeData`.

## Calling conventions

Two services, **two different calling conventions** — do not mix them up:

| Service | Subpath | Convention |
|---------|---------|------------|
| `Agents` | `@uipath/uipath-typescript/agents` | **Positional `Date` args**: `getAll(startTime, endTime, options?)` |
| `AgentMemory` | `@uipath/uipath-typescript/agent-memory` | **Options object**: `getTimeline({ startTime?, endTime?, ... })` — dates inside the object |

ALL `Agents` methods — list, errors, the four timelines, and the ≥ 1.5.0 aggregates — take **positional `Date` args** (`start, end`) — NOT an options object. Filters go in the optional third arg. Contrast with `AgentMemory` (options object) and `AgentTraces` (options object — `sdk/traces.md`).

## Agents Service

```typescript
import { Agents, AgentListSortColumn } from '@uipath/uipath-typescript/agents';
const agents = new Agents(sdk)
```

Return shapes and server-side behavior the types don't show:

| Method | Returns | Notes |
|--------|---------|-------|
| `getAll(start, end, options?)` | **rows on `.items`** (`NonPaginatedResponse<AgentListItem>`, or `PaginatedResponse` with pagination options) | Per-agent totals aggregated over the window (`quantityAGU`, `healthScore` 0–100, `lastIncidentType`) — good for KPIs and ranked tables. `unitsName` may be `null` or `""` |
| `getErrors(start, end, options?)` | **rows on `.items`** | Agent error classes (incidents) observed in the window, ranked |
| `getErrorsTimeline(start, end, options?)` | **bare array** of `{ name, value, date }` | `name` is the **agent name** (contrast: `AgentTraces.getErrorsTimeline`, where `name` is the error name), `value` the error count, `date` the bucket. `limit?` option = top-N agents, default 10 |
| `getConsumptionTimeline(start, end, options?)` | **bare array** of `{ timeSlice, aguConsumption }` | Native chart shape |
| `getLatencyTimeline(start, end, options?)` | **bare array** of `{ name, value, date }` | `name` is the percentile (`"P50"` / `"P95"`), `value` is **milliseconds** (the `AgentTraces` counterpart is seconds) |

> **Semantics:** `getAll` returns per-agent totals — good for KPIs and ranked tables. For *time-series* (error / latency / consumption trends) use the dedicated timeline methods — all added in SDK 1.4.1. There is still **no invocation-count timeline** and **no per-percentile method other than `getLatencyTimeline`**.

### Insights aggregates (SDK ≥ 1.5.0)

Purpose-built aggregate endpoints — all **positional `Date` args** `(startTime, endTime, options?)`, same as `getAll`. Prefer these over hand-rolling aggregates from `getAll`.

| Method | Returns | Use for |
|---|---|---|
| `getTopErrorCount(start, end, { limit?, folderKeys? })` | `{ totalErrors, data: [{ name, count, agentId, … }] }` | Agents ranked by error count (`agents-by-errors`) |
| `getTopConsumption(start, end, { limit?, healthy?, agentTypes? })` | `{ totalConsumed, totalAGUConsumed, …, agents: [{ agentName, consumedQuantity, consumedAGUQuantity, consumedPLTUQuantity }] }` | Agents ranked by consumption (`agent-consumption`) |
| `getIncidentDistribution(start, end, { folderKeys? })` | `{ errorCount, escalationCount, policyCount }` | Incident breakdown donut (`agent-incident-distribution`) |
| `getSummary(start, end, { lookbackPeriodAnalysis?, executionType?, … })` | `{ currentPeriodSummary: { totalJobs, successfulJobs, successRate, averageDurationSeconds, agents:[…] }, lookbackPeriodSummary? }` | Success-rate / job-volume KPIs with vs-previous delta (`agent-success-rate`) |
| `getUnitConsumptionSummary(start, end, { lookbackPeriodAnalysis?, … })` | `{ currentPeriodSummary: { totalAgentUnitConsumption: { completeJobs, incompleteJobs }, totalPlatformUnitConsumption: {…} }, lookbackPeriodSummary? }` | Aggregate AGU/PLTU KPI with delta (`agent-unit-consumption-summary`) |

> **Delta from one call.** `getSummary` / `getUnitConsumptionSummary` with `{ lookbackPeriodAnalysis: true }` return the prior equal-length window as `lookbackPeriodSummary` — feed it straight into a kpi-card's `previous`. No second call, no `priorWindow()`.

### fnBody patterns

```typescript
// Count of active agents (kpi-card)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk).getAll(THIRTY_DAYS_AGO, NOW)
return [{ count: result?.items?.length ?? 0 }]
```

```typescript
// Agents ranked by AGU consumption (ranked-table)
const { Agents, AgentListSortColumn } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk).getAll(THIRTY_DAYS_AGO, NOW, {
  orderBy: { column: AgentListSortColumn.QuantityAGU, desc: true },
})
return (result?.items ?? []).map(agent => ({ ...agent }))
```

```typescript
// Agent errors over time — total across agents (area-chart: xKey date, yKey value)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const points = await new Agents(sdk).getErrorsTimeline(THIRTY_DAYS_AGO, NOW)
const byDate: Record<string, number> = {}
for (const point of points) byDate[point.date] = (byDate[point.date] ?? 0) + point.value
return Object.entries(byDate).sort().map(([date, value]) => ({ date, value }))
```

```typescript
// Agent latency P50/P95 over time — pivot long→wide (multi-line-chart: xKey date, series P50/P95)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const points = await new Agents(sdk).getLatencyTimeline(THIRTY_DAYS_AGO, NOW)
const byDate: Record<string, Record<string, unknown>> = {}
for (const point of points) {
  byDate[point.date] = byDate[point.date] ?? { date: point.date }
  byDate[point.date][point.name] = point.value
}
return Object.values(byDate).sort((a, b) => String(a.date).localeCompare(String(b.date)))
```

```typescript
// AGU consumption over time (area-chart: xKey timeSlice, yKey aguConsumption)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const series = await new Agents(sdk).getConsumptionTimeline(THIRTY_DAYS_AGO, NOW)
return series.map(point => ({ ...point }))
```

```typescript
// Top agent errors ranked by occurrence (ranked-table)
const { Agents, AgentErrorSortColumn } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk).getErrors(THIRTY_DAYS_AGO, NOW, {
  orderBy: { column: AgentErrorSortColumn.ExecutionCount, desc: true },
})
return (result?.items ?? []).map(agent => ({ ...agent }))
```

```typescript
// Agents ranked by error count (ranked-table) — ≥ 1.5.0
const { Agents } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk).getTopErrorCount(THIRTY_DAYS_AGO, NOW, { limit: 10 })
return result.data.map(agent => ({ name: agent.name, value: agent.count }))
```

```typescript
// Agents ranked by consumption (ranked-table) — ≥ 1.5.0
const { Agents } = await import('@uipath/uipath-typescript/agents')
return (await new Agents(sdk).getTopConsumption(THIRTY_DAYS_AGO, NOW, { limit: 10 })).agents.map(agent => ({ ...agent }))
```

```typescript
// Incident distribution (donut) — ≥ 1.5.0: flat response → chart rows
const { Agents } = await import('@uipath/uipath-typescript/agents')
const distribution = await new Agents(sdk).getIncidentDistribution(THIRTY_DAYS_AGO, NOW)
return [
  { name: 'Errors', value: distribution.errorCount },
  { name: 'Escalations', value: distribution.escalationCount },
  { name: 'Policy', value: distribution.policyCount },
]
```

```typescript
// Success-rate KPI with vs-previous delta (kpi-card) — ≥ 1.5.0
const { Agents } = await import('@uipath/uipath-typescript/agents')
const summary = await new Agents(sdk).getSummary(THIRTY_DAYS_AGO, NOW, { lookbackPeriodAnalysis: true })
return [{ value: summary.currentPeriodSummary.successRate, previous: summary.lookbackPeriodSummary?.successRate }]
```

```typescript
// Total Agent Units consumed, with delta (kpi-card) — ≥ 1.5.0
const { Agents } = await import('@uipath/uipath-typescript/agents')
const summary = await new Agents(sdk).getUnitConsumptionSummary(THIRTY_DAYS_AGO, NOW, { lookbackPeriodAnalysis: true })
const current = summary.currentPeriodSummary.totalAgentUnitConsumption
const prior = summary.lookbackPeriodSummary?.totalAgentUnitConsumption
return [{ value: current.completeJobs + current.incompleteJobs, previous: prior ? prior.completeJobs + prior.incompleteJobs : undefined }]
```

## AgentMemory Service

```typescript
import { AgentMemory, AgentMemoryExecutionType } from '@uipath/uipath-typescript/agent-memory';
const memory = new AgentMemory(sdk)
```

All three methods take ONE optional options object — dates (`startTime` / `endTime`) go INSIDE it. `executionType`: omit for both `Debug` and `Runtime`. Window defaults to the **last 24 hours**. All three return a **bare array** — no `.items` / `.data` unwrapping needed.

| Method | Returns (bare array of) | Use for |
|--------|------------------------|---------|
| `getTimeline(options?)` | `{ timeSlice, inMemoryCount, notInMemoryCount, totalCount, enabledMemoryCount, disabledMemoryCount }` | Memory state over time (line/area chart) |
| `getCallsTimeline(options?)` | `{ timeSlice, memoryCallsCount }` | Memory access volume over time |
| `getTopSpaces(options?)` | `{ memorySpaceId, memorySpaceName, memoryCount, enabledMemoryCount, disabledMemoryCount }` | Top memory spaces (ranked; `limit?` option, default 5) |

### fnBody pattern

```typescript
// Memory calls over the last 7 days (area-chart: xKey timeSlice, yKey memoryCallsCount)
const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')
const series = await new AgentMemory(sdk).getCallsTimeline({ startTime: SEVEN_DAYS_AGO, endTime: NOW })
return series.map(point => ({ ...point }))
```
