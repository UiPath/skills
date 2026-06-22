# Agent Traces (Insights RTM) Reference

> Requires `@uipath/uipath-typescript` **≥ 1.4.1**. Scope: `Insights Insights.RealTimeData` (same as Agents/Agent Memory). Subpath: `@uipath/uipath-typescript/traces`.

Trace-level (span-level) view of agent execution — errors, latency, unit consumption, and raw spans. Distinct from the `Agents` service (`sdk/agents.md`), which aggregates per agent. Use traces when the request is about *spans*, *trace-level* timelines, or per-(agent, version, folder) unit breakdowns.

```typescript
import { AgentTraces, AgentTraceExecutionType } from '@uipath/uipath-typescript/traces';
const svc = new AgentTraces(sdk as never)
```

**Convention:** every method takes ONE optional options object — `{ startTime?: Date, endTime?: Date, folderKeys?, agentId?, agentVersion?, executionType? }`. Dates go INSIDE the object (unlike `Agents`, which uses positional Dates). Window defaults to the **last 1 year** server-side. `executionType`: `AgentTraceExecutionType.Debug | Runtime` (omit for both).

The three timeline/consumption methods return a **bare array** — no `.items` / `.data` unwrapping. The span methods are listed for completeness but are record-grain (not dashboard metrics).

| Method | Returns (bare array of) | Use for |
|--------|------------------------|---------|
| `getErrorsTimeline(options?)` | `{ name, value, date }` (`name` = error name) | Trace error volume over time |
| `getLatencyTimeline(options?)` | `{ name, value, date }` (`value` = **seconds**) | Trace latency over time |
| `getUnitConsumption(options?)` | `{ agentId, folderKey, agentVersion, agentUnitsConsumed, platformUnitsConsumed }` | Per-agent AGU/PLTU totals (ranked table) |
| `getSpansByTraceId(traceId)` | `AgentSpanGetResponse[]` | All spans of one trace (drill-down, not a metric) |
| `getSpansByReference(referenceId, options?)` | paginated `AgentSpanGetResponse` | Spans under a reference id (drill-down, not a metric) |

## getErrorsTimeline

```json
[ { "name": "ToolTimeout", "value": 4, "date": "2026-06-02" },
  { "name": "ValidationError", "value": 1, "date": "2026-06-02" } ]
```

`name` is the **error name/category** (not an agent name — contrast with `Agents.getErrorsTimeline`).

## getLatencyTimeline

```json
[ { "name": "P50", "value": 0.82, "date": "2026-06-02" },
  { "name": "P95", "value": 2.40, "date": "2026-06-02" } ]
```

`value` is **decimal seconds**. `name` is a series/grouping label — the exact values are not guaranteed to be `P50`/`P95`. For a robust default, average `value` per `date` into a single series; inspect live `name` values before plotting distinct series with a `multi-line-chart`.

## getUnitConsumption

```json
[ { "agentId": "ag-0001", "folderKey": "f-1001", "agentVersion": "1.2.0", "agentUnitsConsumed": 340, "platformUnitsConsumed": 0 },
  { "agentId": "ag-0002", "folderKey": "f-1001", "agentVersion": "1.0.0", "agentUnitsConsumed": 1210, "platformUnitsConsumed": 12 } ]
```

## Module patterns

```typescript
// Trace errors over time — total across error names (area-chart: xKey date, yKey value)
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const points = await new AgentTraces(sdk as never).getErrorsTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
  const byDate: Record<string, number> = {}
  for (const p of points) byDate[p.date] = (byDate[p.date] ?? 0) + p.value
  return Object.entries(byDate).sort().map(([date, value]) => ({ date, value }))
}
```

```typescript
// Trace latency over time — average per date (area-chart: xKey date, yKey value, seconds)
const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
const points = await new AgentTraces(sdk as never).getLatencyTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
const acc: Record<string, { sum: number; n: number }> = {}
for (const p of points) {
  acc[p.date] = acc[p.date] ?? { sum: 0, n: 0 }
  acc[p.date].sum += p.value
  acc[p.date].n += 1
}
return Object.entries(acc).sort().map(([date, { sum, n }]) => ({ date, value: n ? sum / n : 0 }))
```

```typescript
// Per-agent unit consumption (ranked-table) — native shape, return as-is
const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
return await new AgentTraces(sdk as never).getUnitConsumption({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
```

## Spans (drill-down only)

`getSpansByTraceId(traceId)` and `getSpansByReference(referenceId, options?)` return raw span records (`AgentSpanGetResponse`: `id`, `traceId`, `parentId`, `name`, `startTime`, `endTime`, `attributes`, `status`, `spanType`, `jobKey`, `referenceId`, …). These are record-grain trace inspection, not aggregate dashboard metrics — use them for a `fetchDetail` drill-down, not a top-level widget. `getSpansByReference` is paginated (use `fetchAll`).
