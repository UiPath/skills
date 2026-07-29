# Agents & Agent Memory (Insights RTM) Reference

Signatures/params/examples: `dist/agents/index.d.ts`, `dist/agent-memory/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Cross-service contrast warning:** calling conventions and field semantics differ between `Agents`, `AgentMemory`, and `AgentTraces` (`sdk/traces.md`) — positional Dates vs options objects, `name` = agent vs error, ms vs seconds. Read each signature/JSDoc; do NOT pattern-match from one service to another.

## Agents — which method for which widget

`getAll` returns per-agent totals over the window — good for KPIs and ranked tables. For *time-series* (error / latency / consumption trends) use the dedicated timeline methods. There is still **no invocation-count timeline** and **no per-percentile method other than `getLatencyTimeline`**.

### Insights aggregates

Purpose-built aggregate endpoints — prefer these over hand-rolling aggregates from `getAll`. Registry widget mapping:

| Method | Widget |
|---|---|
| `getTopErrorCount` | `agents-by-errors` |
| `getTopConsumption` | `agent-consumption` |
| `getIncidentDistribution` | `agent-incident-distribution` |
| `getSummary` | `agent-success-rate` |
| `getUnitConsumptionSummary` | `agent-unit-consumption-summary` |

> **Delta from one call.** `getSummary` / `getUnitConsumptionSummary` with `{ lookbackPeriodAnalysis: true }` — feed `lookbackPeriodSummary` straight into a kpi-card's `previous`. No second call, no `priorWindow()`.

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
// Agents ranked by error count (ranked-table)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const result = await new Agents(sdk).getTopErrorCount(THIRTY_DAYS_AGO, NOW, { limit: 10 })
return result.data.map(agent => ({ name: agent.name, value: agent.count }))
```

```typescript
// Agents ranked by consumption (ranked-table)
const { Agents } = await import('@uipath/uipath-typescript/agents')
return (await new Agents(sdk).getTopConsumption(THIRTY_DAYS_AGO, NOW, { limit: 10 })).agents.map(agent => ({ ...agent }))
```

```typescript
// Incident distribution (donut): flat response → chart rows
const { Agents } = await import('@uipath/uipath-typescript/agents')
const distribution = await new Agents(sdk).getIncidentDistribution(THIRTY_DAYS_AGO, NOW)
return [
  { name: 'Errors', value: distribution.errorCount },
  { name: 'Escalations', value: distribution.escalationCount },
  { name: 'Policy', value: distribution.policyCount },
]
```

```typescript
// Success-rate KPI with vs-previous delta (kpi-card)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const summary = await new Agents(sdk).getSummary(THIRTY_DAYS_AGO, NOW, { lookbackPeriodAnalysis: true })
return [{ value: summary.currentPeriodSummary.successRate, previous: summary.lookbackPeriodSummary?.successRate }]
```

```typescript
// Total Agent Units consumed, with delta (kpi-card)
const { Agents } = await import('@uipath/uipath-typescript/agents')
const summary = await new Agents(sdk).getUnitConsumptionSummary(THIRTY_DAYS_AGO, NOW, { lookbackPeriodAnalysis: true })
const current = summary.currentPeriodSummary.totalAgentUnitConsumption
const prior = summary.lookbackPeriodSummary?.totalAgentUnitConsumption
return [{ value: current.completeJobs + current.incompleteJobs, previous: prior ? prior.completeJobs + prior.incompleteJobs : undefined }]
```

## AgentMemory Service

Widget mapping: `getTimeline` → memory state over time (line/area chart), `getCallsTimeline` → memory access volume over time, `getTopSpaces` → ranked memory spaces.

### fnBody pattern

```typescript
// Memory calls over the last 7 days (area-chart: xKey timeSlice, yKey memoryCallsCount)
const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')
const series = await new AgentMemory(sdk).getCallsTimeline({ startTime: SEVEN_DAYS_AGO, endTime: NOW })
return series.map(point => ({ ...point }))
```
