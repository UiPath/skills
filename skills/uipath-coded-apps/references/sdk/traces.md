# Agent Traces (Insights RTM) Reference

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/traces/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

> Requires `@uipath/uipath-typescript` **≥ 1.4.1**. Scope: `Insights Insights.RealTimeData` (same as Agents/Agent Memory). Subpath: `@uipath/uipath-typescript/traces`.

Trace-level (span-level) view of agent execution — errors, latency, unit consumption, and raw spans. Distinct from the `Agents` service (`sdk/agents.md`), which aggregates per agent. Use traces when the request is about *spans*, *trace-level* timelines, or per-(agent, version, folder) unit breakdowns.

```typescript
import { AgentTraces, AgentTraceExecutionType } from '@uipath/uipath-typescript/traces';
const svc = new AgentTraces(sdk)
```

**Convention:** every method takes ONE optional options object — dates (`startTime` / `endTime`) go INSIDE the object (unlike `Agents`, which uses positional Dates). Window defaults to the **last 1 year** server-side. `executionType`: omit for both `Debug` and `Runtime`. Exception: the two governance methods take a **required positional `startTime: Date`** first (options second) and are GATED — full contract, gate, and module patterns in [`sdk/governance-traces.md`](governance-traces.md).

The three timeline/consumption methods return a **bare array** — no `.items` / `.data` unwrapping. The span methods are listed for completeness but are record-grain (not dashboard metrics).

| Method | Returns (bare array of) | Use for |
|--------|------------------------|---------|
| `getErrorsTimeline(options?)` | `{ name, value, date }` (`name` = error name) | Trace error volume over time |
| `getLatencyTimeline(options?)` | `{ name, value, date }` (`value` = **seconds**) | Trace latency over time |
| `getUnitConsumption(options?)` | `{ agentId, folderKey, agentVersion, agentUnitsConsumed, platformUnitsConsumed }` | Per-agent AGU/PLTU totals (ranked table) |
| `getSpansByTraceId(traceId)` | `AgentSpanGetResponse[]` | All spans of one trace (drill-down, not a metric) |
| `getSpansByReference(referenceId, options?)` | paginated `AgentSpanGetResponse` | Spans under a reference id (drill-down, not a metric) |
| `getGovernanceDecisions(startTime, options?)` **(≥ 1.5.1, org-admin)** | paginated `.items` decision rows | Runtime-governance policy checks — see `sdk/governance-traces.md` |
| `getGovernanceSummary(startTime, options?)` **(≥ 1.5.1, org-admin)** | single summary object | Governance posture breakdowns — see `sdk/governance-traces.md` |

## Traps

- `getErrorsTimeline`: `name` is the **error name/category** (not an agent name — contrast with `Agents.getErrorsTimeline`).
- `getLatencyTimeline`: `value` is **decimal seconds** (`Agents.getLatencyTimeline` is milliseconds). `name` is a series/grouping label — the exact values are not guaranteed to be `P50`/`P95`. For a robust default, average `value` per `date` into a single series; inspect live `name` values before plotting distinct series with a `multi-line-chart`.

## Module patterns

```typescript
// Trace errors over time — total across error names (area-chart: xKey date, yKey value)
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const points = await new AgentTraces(sdk).getErrorsTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
  const byDate: Record<string, number> = {}
  for (const p of points) byDate[p.date] = (byDate[p.date] ?? 0) + p.value
  return Object.entries(byDate).sort().map(([date, value]) => ({ date, value }))
}
```

```typescript
// Trace latency over time — average per date (area-chart: xKey date, yKey value, seconds)
const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
const points = await new AgentTraces(sdk).getLatencyTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
const acc: Record<string, { sum: number; n: number }> = {}
for (const p of points) {
  acc[p.date] = acc[p.date] ?? { sum: 0, n: 0 }
  acc[p.date].sum += p.value
  acc[p.date].n += 1
}
return Object.entries(acc).sort().map(([date, { sum, n }]) => ({ date, value: n ? sum / n : 0 }))
```

```typescript
// Per-agent unit consumption (ranked-table)
const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
const consumption = await new AgentTraces(sdk).getUnitConsumption({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
return consumption.map(x => ({ ...x }))
```

## Spans (drill-down only)

`getSpansByTraceId(traceId)` and `getSpansByReference(referenceId, options?)` return raw span records — record-grain trace inspection, not aggregate dashboard metrics. Use them for a `fetchDetail` drill-down, not a top-level widget. `getSpansByReference` is paginated (use `fetchAll`).
