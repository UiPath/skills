# Agent Traces (Insights RTM) Reference

Signatures/params/examples: `dist/traces/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> Requires `@uipath/uipath-typescript` **≥ 1.4.1**. The two governance methods (`getGovernanceDecisions` / `getGovernanceSummary`) are **≥ 1.5.1, org-admin, GATED** — full contract, gate, and module patterns in [`sdk/governance-traces.md`](governance-traces.md).

Trace-level (span-level) view of agent execution — errors, latency, unit consumption, and raw spans. Distinct from the `Agents` service (`sdk/agents.md`), which aggregates per agent. Use traces when the request is about *spans*, *trace-level* timelines, or per-(agent, version, folder) unit breakdowns.

> **Cross-service contrast warning:** conventions and field semantics differ from `Agents` (options-object vs positional dates, `name` = error vs agent, seconds vs ms) — read each signature/JSDoc; do NOT pattern-match from `Agents` to `AgentTraces`.

## Traps

- `executionType`: omit to include BOTH `Debug` and `Runtime` (the option's JSDoc does not state this).
- `getLatencyTimeline`: `name` is a series/grouping label with NO guaranteed values (unlike `Agents`, where observed values are `P50`/`P95`). For a robust default, average `value` per `date` into a single series; inspect live `name` values before plotting distinct series with a `multi-line-chart`.

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
