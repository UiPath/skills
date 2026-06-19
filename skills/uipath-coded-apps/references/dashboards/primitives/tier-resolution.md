# Tier Resolution — Classifying Metrics

Every metric in `intent.json` requires a `metrics/<name>.ts` module that you write based on the SDK documentation. The tier tells the build script where to find display hints — it does not drive code generation.

`intent.json` has `"schemaVersion": 2`. Metric entries are **pure metadata** — no `fnBody`, no `detailFnBody`.

---

## How it works

```
User asks for a metric
  ↓
T0 — Check Hard Refuse list (first)
  → Match? Refuse only that metric, offer alternative
  ↓
T1 — Catalog check
  → Name/alias in capability-registry.json?
    → YES: registry provides display hints (template, xKey, yKey, icon)
           You still write the metrics/<name>.ts module from SDK docs
  ↓
T2 — Parametric check
  → Known metric with user-supplied filter?
    → YES: registry provides hints + you incorporate params into the module
  ↓
T3 — Custom
  → Not in catalog: you provide all display config and write the module entirely from SDK docs
```

**Every tier requires a `metrics/<name>.ts` module.** The registry never generates code — it only describes what template and keys to use.

---

## SDK validation — do this before writing the plan

For every requested metric, before writing it into the plan:

1. Check T0 Hard Refuse list — if it matches, refuse that metric inline
2. Check T1/T2 catalog — if name or alias matches, use the registry hint
3. For T3 (custom) metrics: **find a method in the SDK service reference below** that can return the needed data. If no method maps to it, T0 refuse it — do not invent methods

> If a metric is feasible but requires a method that may not be in the installed SDK version (e.g. a newly released Insights endpoint), include it in the plan with a note: "relies on `Agents.methodName` — will verify after install." `tsc` catches a missing method before build.

After the plan is confirmed, **Phase 3.5 cross-checks each metric module against the example response + semantics notes in `references/sdk/*.md`** — the example shows real field *values*, not just that a field exists. (E.g. an agent job is `packageType === 'Agent'` / OData `ProcessType eq 'Agent'` — `sourceType` is the trigger origin, not the agent discriminator.)

---

## Writing a metric module

Write each metric's data-fetch code as a real TypeScript module at `metrics/<metric-name>.ts` (a `metrics/` folder sibling to `intent.json`). The build copies these files into `src/metrics/` and type-checks them.

### Module contract

```ts
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')
  return await new AgentMemory(sdk as never).getTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
}
```

`MetricFn` is `(sdk: any, getToken: () => Promise<string>) => Promise<any[]>`.

**Rules:**
- Export `fetchData` (required). Export `fetchDetail` (optional, same `MetricFn` signature) for record-grain drill-downs.
- Return a **flat array of row objects** — SDK-typed arrays accepted directly. Never add `as unknown as Record<string,unknown>[]` casts.
- Use dynamic import: `const { ServiceClass } = await import('@uipath/uipath-typescript/...')`
- Use constructor injection: `new ServiceClass(sdk as never)`
- **Read methods ONLY.** Allowed: `getAll`, `getById`, `getAllRecords`, `queryRecordsById`, `getIncidents`, `getErrors`, `getErrorsTimeline`, `getConsumptionTimeline`, `getLatencyTimeline`, `getUnitConsumption`, `getTimeline`, `getCallsTimeline`, `getTopSpaces`, `getSpansByTraceId`, `getSpansByReference`, `getPolicyTraces`, `getOperationSummary`, `getSlaSummary`, `getStagesSlaSummary`, `getTopRunCount`, `getTopFaultedCount`, `getTopExecutionDuration`, `getTopElementFailedCount`, `getInstanceStatusTimeline`, `getElementStats`. Never call `create`, `complete`, `assign`, `start`, `stop`, `resume`, `restart`, `insert*`, `update*`, `delete*`, `upload*`.
- **Full listings: use `fetchAll` — never hand-write the cursor loop.**
  ```ts
  import { fetchAll } from '@/lib/paginate'
  return await fetchAll(cursor => svc.getAll({ pageSize: 200, cursor }))
  ```
- **Don't add your own request caching.** The scaffold wraps `fetch` (`src/lib/fetch-cache.ts`) so identical GET requests share one network call, cached ~15s. Call the SDK normally.

### Time constants

Import from `@/lib/time` — do NOT redeclare them:
`NOW`, `ONE_DAY_AGO`, `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, `NINETY_DAYS_AGO` (all `Date` objects).

### Drill-down detail

For record-grain drill-downs: export `fetchDetail: MetricFn` in the same module AND set `"detail": true` on the metric in `intent.json`. If `detail` is absent, the detail view reuses `fetchData` (shows the chart's buckets — avoid for chart metrics).

### Build type-check loop

The build type-checks all `metrics/*.ts` modules in isolation (Stage A) before generating widgets.
- `METRICS_PASS` — silent; build continues.
- `METRICS_RETRY:{ files: [...], errors: [...] }` — fix the named `src/metrics/<name>.ts` file(s) and re-run. Max 2 attempts; if still failing, drop the metric. (This replaces any older retry mechanism — there is no `T3_RETRY`.)

---

## T1 — Catalog metrics with display hints

The registry entry describes the metric and expected SDK call. Use it as your guide, then write the correct `metrics/<name>.ts` module from the SDK documentation.

| Metric name | What it shows | Registry template | SDK hint (≥ 1.4.1) |
|-------------|--------------|-------------------|--------------------|
| `active-agents-kpi` | Count of active agents | `kpi-card` | `Agents.getAll(start, end)` → `{ items }`; return `[{ count: items.length }]` |
| `agent-consumption` | Agents ranked by AGU/PLTU | `ranked-table` | `Agents.getAll(start, end, { orderBy: { column: AgentListSortColumn.QuantityAGU, desc: true } })` → `{ items }` |
| `agent-health` | Agents ranked by health score | `ranked-table` | `Agents.getAll(start, end, { orderBy: { column: AgentListSortColumn.HealthScore } })` → `{ items }` (healthScore 0–100, lastIncidentType) |
| `agent-error-timeline` | Agent errors over time | `area-chart` | `Agents.getErrorsTimeline(start, end)` → BARE `[{ name, value, date }]`; module sums `value` per `date` |
| `agent-latency-timeline` | P50/P95 latency over time | `multi-line-chart` | `Agents.getLatencyTimeline(start, end)` → BARE `[{ name:'P50'\|'P95', value (ms), date }]`; module pivots to `[{ date, P50, P95 }]` |
| `agent-consumption-timeline` | AGU consumed over time | `area-chart` | `Agents.getConsumptionTimeline(start, end)` → BARE `[{ timeSlice, aguConsumption }]` (native shape) |
| `agent-errors` | Error classes ranked | `ranked-table` | `Agents.getErrors(start, end, { orderBy: { column: AgentErrorSortColumn.ExecutionCount, desc: true } })` → `{ items }` |
| `trace-error-timeline` | Trace errors over time | `area-chart` | `AgentTraces.getErrorsTimeline({ startTime, endTime })` → BARE `[{ name, value, date }]` (see `sdk/traces.md`) |
| `trace-latency-timeline` | Trace latency over time | `area-chart` | `AgentTraces.getLatencyTimeline({ startTime, endTime })` → BARE `[{ name, value (s), date }]`; module averages per date |
| `agent-unit-consumption` | AGU/PLTU per agent | `ranked-table` | `AgentTraces.getUnitConsumption({ startTime, endTime })` → BARE `[{ agentId, agentUnitsConsumed, platformUnitsConsumed }]` |
| `agent-memory-timeline` | Memory entries over time | `area-chart` | `AgentMemory.getTimeline({ startTime, endTime })` → BARE array `[{ timeSlice, totalCount, … }]` |
| `memory-calls-trend` | Memory access volume | `area-chart` | `AgentMemory.getCallsTimeline({ startTime, endTime })` → BARE array `[{ timeSlice, memoryCallsCount }]` |
| `top-memory-spaces` | Top memory spaces | `ranked-table` | `AgentMemory.getTopSpaces({ limit: 10 })` → BARE ranked array |
| `policy-denials` | Governance-blocked actions | `data-table` | `Governance.getPolicyTraces(start, { evaluationResult: [Deny, SimulatedDeny] })` → `{ items }` (needs org-admin) |
| `governance-verdicts` | Allow/Deny/NoOp breakdown | `donut-chart` | `Governance.getOperationSummary(start)` → single object; transform to `[{ name, value }]` rows |
| `job-failures` | Faulted jobs | `data-table` | `new Jobs(sdk).getAll({ filter: "State eq 'Faulted'" })` → `{ items: [{processName, state, createdTime}] }` |
| `job-completion-trend` | Completed jobs | `data-table` | `new Jobs(sdk).getAll({ filter: "State eq 'Successful'" })` → `{ items: [{processName, state, endTime}] }` |
| `case-sla-status` | Case SLA status split | `donut-chart` | `CaseInstances.getSlaSummary()` → `.items` `{slaStatus}`; group by status → `[{name,value}]` (scope adds PIMS) |
| `case-sla-breaches` | Cases at SLA risk/overdue | `data-table` | `CaseInstances.getSlaSummary()` → filter `slaStatus` At Risk/Overdue (scope adds PIMS) |
| `case-stage-sla` | Stage-level SLA | `data-table` | `CaseInstances.getStagesSlaSummary()` → BARE; flatten `stages` (scope adds PIMS) |
| `top-maestro-processes-by-runs` | Busiest processes | `ranked-table` | `MaestroProcesses.getTopRunCount(start,end)` → BARE `[{name,runCount,...}]` |
| `top-maestro-processes-by-faults` | Top failing processes | `ranked-table` | `MaestroProcesses.getTopFaultedCount(start,end)` → BARE `[{name,faultedCount,...}]` |
| `top-maestro-processes-by-duration` | Slowest processes | `ranked-table` | `MaestroProcesses.getTopExecutionDuration(start,end)` → BARE `[{name,duration,...}]` |
| `maestro-process-status-timeline` | Process status over time | `multi-line-chart` | `MaestroProcesses.getInstanceStatusTimeline(start,end)` → pivot to `[{date,Completed,Faulted,Cancelled}]` |
| `top-failing-process-elements` | Top failing BPMN elements | `ranked-table` | `MaestroProcesses.getTopElementFailedCount(start,end)` → BARE `[{elementName,failedCount,...}]` |
| `top-cases-by-runs` | Busiest cases | `ranked-table` | `Cases.getTopRunCount(start,end)` → BARE `[{name,runCount,...}]` |
| `top-cases-by-faults` | Top failing cases | `ranked-table` | `Cases.getTopFaultedCount(start,end)` → BARE `[{name,faultedCount,...}]` |
| `top-cases-by-duration` | Slowest cases | `ranked-table` | `Cases.getTopExecutionDuration(start,end)` → BARE `[{name,duration,...}]` |
| `case-status-timeline` | Case status over time | `multi-line-chart` | `Cases.getInstanceStatusTimeline(start,end)` → pivot to `[{date,Completed,Faulted,Cancelled}]` |
| `top-failing-case-elements` | Top failing case elements | `ranked-table` | `Cases.getTopElementFailedCount(start,end)` → BARE `[{elementName,failedCount,...}]` |

> Maestro Insights metrics (the rows above the Jobs entries that use `Top*`/`InstanceStatusTimeline`) need `Insights Insights.RealTimeData OR.Folders.Read`; the `case-sla-*` metrics additionally need `PIMS`. See `sdk/maestro.md` and `oauth-scopes.md`.

### T1 intent entry (pure metadata)

```json
{
  "name": "agent-memory-timeline",
  "tier": "T1",
  "title": "Agent Memory"
}
```

The registry fills in: `template: "area-chart"`, `xKey: "timeSlice"`, `yKey: "totalCount"`, `title` default, `icon`, `headlineMode`, `deltaPolarity`.
Override any of these in the intent entry.

Corresponding module at `metrics/agent-memory-timeline.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')
  return await new AgentMemory(sdk as never).getTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
}
```

### T1 kpi-card example (active agents)

Intent entry:

```json
{
  "name": "active-agents-kpi",
  "tier": "T1",
  "title": "Active Agents",
  "displayAs": "kpi-card",
  "valueField": "count",
  "valueLabel": "active agents"
}
```

Module at `metrics/active-agents-kpi.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { Agents } = await import('@uipath/uipath-typescript/agents')
  const svc = new Agents(sdk as never)
  const result = await svc.getAll(THIRTY_DAYS_AGO, NOW)
  return [{ count: result?.items?.length ?? 0 }]
}
```

---

## T2 — Parametric metrics (catalog with user filter)

Incorporate user's filter parameters directly into the module.

| Metric name | What it does | Params |
|-------------|-------------|--------|
| `jobs-duration-threshold` | Jobs running longer than N minutes | `{ threshold: number, direction: "gt" }` |
| `jobs-by-state` | Jobs in a specific state | `{ value: "Faulted" \| "Running" \| "Stopped" }` |
| `tasks-by-status` | Tasks by status | `{ value: "Pending" \| "Completed" }` |
| `cases-running-above` | Cases exceeding threshold | `{ threshold: number, direction: "gt" }` |
| `element-latency-stats` | Per-element duration percentiles | `{ processKey, packageId, version }` |

### T2 intent entry (pure metadata)

```json
{
  "name": "jobs-by-state",
  "tier": "T2",
  "title": "Faulted Jobs",
  "params": { "value": "Faulted" },
  "displayAs": "data-table",
  "columns": "[{key:\"processName\",label:\"Process\"},{key:\"state\",label:\"State\"},{key:\"createdTime\",label:\"Started\"}]"
}
```

`params` is documentation — the actual filter logic lives in the module.

Module at `metrics/jobs-by-state.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const svc = new Jobs(sdk as never)
  return (await svc.getAll({ filter: "State eq 'Faulted'" }))?.items ?? []
}
```

---

## T3 — Custom metrics

For any metric not in the catalog. Provide all display config in the intent entry and write the module entirely from SDK documentation.

### T3 area chart from SDK data

Intent entry:

```json
{
  "name": "faulted-jobs-trend",
  "tier": "T3",
  "title": "Faulted Jobs Over Time",
  "displayAs": "area-chart",
  "xKey": "date",
  "yKey": "count"
}
```

Module at `metrics/faulted-jobs-trend.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const svc = new Jobs(sdk as never)
  const result = await svc.getAll({ filter: "State eq 'Faulted'" })
  const byDate: Record<string, number> = {}
  for (const j of result?.items ?? []) {
    const date = String(j.createdTime).slice(0, 10)
    byDate[date] = (byDate[date] ?? 0) + 1
  }
  return Object.entries(byDate).sort().map(([date, count]) => ({ date, count }))
}
```

### Table display columns — which field to use

A `data-table`/`ranked-table` widget renders from **`columns`** (a literal string) or **`columnDefs`** (a structured `{key,label,align?,format?,color?}[]` array, all tiers). Every key must be a field the module returns per row. **`detailColumns` is NOT for table display** — it only styles a *chart's* drill-down view; a table given only `detailColumns` renders empty `—` cells. A T3 table with neither `columns` nor `columnDefs` is rejected by the build (fail-loud, not a silent fallback).

To make table rows clickable, add `rowLink: { key: "<rowField>" }` and export `fetchDetailByKey` (see `detail-views.md § Row-click drill-down`); optionally `defaultSortAsc: true` to sort ascending.

### T3 ranked table from Insights (governance denials grouped by actor)

Intent entry:

```json
{
  "name": "denials-by-actor",
  "tier": "T3",
  "title": "Denials by Actor",
  "displayAs": "ranked-table",
  "columns": "[{key:\"name\",label:\"Actor\"},{key:\"count\",label:\"Denials\",align:\"right\" as const}]"
}
```

Module at `metrics/denials-by-actor.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { Governance, PolicyEvaluationResult } = await import('@uipath/uipath-typescript/governance')
  const result = await new Governance(sdk as never).getPolicyTraces(THIRTY_DAYS_AGO, { evaluationResult: [PolicyEvaluationResult.Deny] })
  const byActor: Record<string, number> = {}
  for (const t of result?.items ?? []) {
    const actor = t.actorProcessId ?? 'unknown'
    byActor[actor] = (byActor[actor] ?? 0) + 1
  }
  return Object.entries(byActor).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count)
}
```

### T3 kpi-card

Intent entry:

```json
{
  "name": "running-jobs-count",
  "tier": "T3",
  "title": "Running Jobs",
  "displayAs": "kpi-card",
  "valueField": "count",
  "valueLabel": "running jobs"
}
```

Module at `metrics/running-jobs-count.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const svc = new Jobs(sdk as never)
  const result = await svc.getAll({ filter: "State eq 'Running'" })
  return [{ count: result?.items?.length ?? 0 }]
}
```

### T3 chart with drill-down detail

Intent entry (note `"detail": true`):

```json
{
  "name": "faulted-jobs-trend",
  "tier": "T3",
  "title": "Faulted Jobs",
  "displayAs": "area-chart",
  "xKey": "date",
  "yKey": "count",
  "headlineMode": "sum",
  "deltaPolarity": "up-bad",
  "subtitle": "Faulted jobs — last 7 days",
  "detail": true,
  "detailColumns": [
    { "key": "processName", "label": "Process" },
    { "key": "state", "label": "State" },
    { "key": "createdTime", "label": "Started", "format": "timeAgo" }
  ],
  "detailSortKey": "createdTime"
}
```

Module at `metrics/faulted-jobs-trend.ts` (exports both `fetchData` and `fetchDetail`):

```ts
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const rows = (await new Jobs(sdk as never).getAll({ filter: "State eq 'Faulted'" }))?.items ?? []
  const byDate: Record<string, number> = {}
  for (const j of rows) { const d = String(j.createdTime).slice(0, 10); byDate[d] = (byDate[d] ?? 0) + 1 }
  return Object.entries(byDate).sort().map(([date, count]) => ({ date, count }))
}

export const fetchDetail: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  return (await new Jobs(sdk as never).getAll({ filter: "State eq 'Faulted'", orderby: 'CreationTime desc' }))?.items ?? []
}
```

---

## Governance violations — GATED, interim (trace-derived)

A dedicated capability for **agent governance/compliance violations against standards** (catalog keys
`agent-governance-violations`, `violations-by-standard`, `violations-by-rule`, `violations-by-hook`,
`agents-by-violations`, `recent-violations`, `agent-compliance-report`). It is **trace-derived and interim**
(no OOB aggregate; bounded by-agent scan, cap 10) — full recipe + the typed `@/lib/governance` parser in
[`sdk/governance-traces.md`](../../sdk/governance-traces.md).

> Violation widgets show only matched rules — a passing fleet looks empty. For runtime-compliance requests,
> ALSO offer the all-evaluations metrics: `rule-evaluations-by-outcome` (Pass vs Matched),
> `rule-evaluations-by-hook`, and `rule-compliance` (rule · standard · hook · evaluated · matched) — backed by
> `parseRuleEvaluations` / `scanEvaluations` (PASS + MATCHED), not `parseGovernanceSpans().violations`.

> **Gate — propose these ONLY on an EXPLICIT runtime-compliance / standards / rules-violation signal:**
> a standard/pack reference ("standard(s)", "pack", `ISO` + clause e.g. `ISO 42001` / `A.8.4`, or a named
> `pack_name`), an explicit **rule violation** ("rule(s) violated/fired", "rule violations"), or
> **runtime-governance** terms ("runtime compliance/governance", hook names, `enforce`/`audit` mode). The
> request must name one of these — generic intent does not qualify.
> `agent-compliance-report`'s row-click opens a RICH detail view by default (violations-by-hook donut + top-rules ranked table + full evaluations table) via `detailView`.
>
> **Do NOT regress the Insights-API governance metrics.** Plain "governance", "policy", "denials", "blocked
> actions", "allow/deny", "enforcement summary", "policy violations" → route to `policy-denials` /
> `governance-verdicts` (the existing `Governance` SDK metrics, `sdk/governance.md`), NOT to these
> trace-derived widgets. When unsure which the user means, ASK — don't default to the trace scan.
> **Never add governance widgets to a plain agent-health/ops dashboard.**
>
> When the gate IS met, load `sdk/governance-traces.md` and write each module with `@/lib/governance`
> (`parseGovernanceSpans`/`countBy`) — never hand-roll span parsing. Every widget shows an EmptyState when
> there's no governance data (un-instrumented agents must not crash the dashboard).

## T0 — Hard Refuse

**Refuse ONLY the specific metric — not the whole dashboard.** Always offer an alternative.

| User asks for | Why impossible | Suggest instead |
|--------------|----------------|-----------------|
| Agent **invocation-count** timeline (runs/calls per period) | SDK 1.4.1 has error/latency/consumption timelines but no invocation-count endpoint | `agent-consumption-timeline` (AGU over time), `agent-error-timeline`, or T3 Jobs trend with `ProcessType eq 'Agent'` |
| Agent cost in dollars | Platform tracks AGU/PLTU units, not currency | `agent-consumption` for per-agent unit totals |
| CPU/RAM per agent | Not exposed by any API ("Agent Memory" = memory entries, not RAM) | `agent-health`; or `agent-memory-timeline` if they meant the Memory feature |
| Who triggered a job | Job records have no end-user identity | `job-completion-trend` grouped by process; `policy-denials` includes `actorIdentityId` for governance events |
| Cross-tenant data | Single-tenant scope — except Governance, which supports `fullOrganization: true` (org admin) | Multi-widget single-tenant view; or T3 `getPolicyTraces(start, { fullOrganization: true })` |
| Raw RPA stack traces / exception text | No endpoint aggregates raw RPA-job error text | `agent-errors` (T1) for agent error classes; T3 `ProcessIncidents.getAll` for Maestro process error messages; faulted-jobs data-table (`errorCode`/`jobError`) for RPA |

---

## SDK service reference

Full method signatures, response types, and field names live in `references/sdk/` (loaded in the parallel blast). Use those files as the source of truth — do not rely on memory.

| Domain | Reference file | Key service classes |
|--------|---------------|---------------------|
| Agents + Agent Memory (Insights RTM, ≥ 1.4.1) | `sdk/agents.md` *(from skill root)* | `Agents`, `AgentMemory` |
| Agent Traces (Insights RTM, ≥ 1.4.1) | `sdk/traces.md` *(from skill root)* | `AgentTraces` |
| Governance (Insights RTM, ≥ 1.4.1) | `sdk/governance.md` *(from skill root)* | `Governance` |
| Agent governance violations (GATED, interim, trace-derived) | `sdk/governance-traces.md` *(from skill root)* | `Jobs` → `Traces.getById(traceId)` spans + `@/lib/governance` |
| Jobs, Queues, Processes, Assets | `sdk/orchestrator.md` *(from skill root)* | `Jobs`, `Queues`, `Processes`, `Assets` |
| Tasks | `sdk/action-center.md` *(from skill root)* | `Tasks` |
| Cases, Process Instances, Maestro Insights/SLA | `sdk/maestro.md` *(from skill root)* | `Cases`, `CaseInstances`, `MaestroProcesses` |
| Data entities | `sdk/data-fabric.md` *(from skill root)* | `Entities` |

`sdk/agents.md` and `sdk/orchestrator.md` are **always loaded** in the parallel blast. Load `sdk/traces.md` (trace/span-level metrics), `sdk/action-center.md` (tasks), `sdk/maestro.md` (cases), or `sdk/governance.md` (governance/policy) only when the request mentions them. Load `sdk/governance-traces.md` ONLY when the prompt signals governance/compliance/standard/ISO intent (see the gated section above).

**Calling conventions — don't mix them up:**
- `Agents.getAll / getErrors / getErrorsTimeline / getConsumptionTimeline / getLatencyTimeline(startTime, endTime, options?)` — positional `Date` args. `getAll`/`getErrors` return rows on `.items`; the three timeline methods return a **bare array**
- `AgentTraces.getErrorsTimeline / getLatencyTimeline / getUnitConsumption({ startTime?, endTime?, … })` — ONE options object, dates inside, returns a **bare array** (see `sdk/traces.md`)
- `AgentMemory.getTimeline({ startTime?, endTime?, … })` — ONE options object, dates inside, returns a **bare array**
- `Governance.getPolicyTraces(startTime, options?)` — required positional `startTime`, rest in options, rows on `.items`; `getOperationSummary` returns a **single object** (wrap into rows in the module)
- `Cases` / `MaestroProcesses.getTopRunCount / getTopFaultedCount / getTopExecutionDuration / getTopElementFailedCount / getInstanceStatusTimeline(start, end, options?)` — positional `Date`s, **bare array**; `getElementStats(processKey, packageId, start, end, version)` all positional, bare array (see `sdk/maestro.md`)
- `CaseInstances.getSlaSummary({ startTimeUtc?, endTimeUtc?, … })` — options object, rows on `.items`; `getStagesSlaSummary(options?)` — **bare array**. SLA methods need `PIMS` on top of the Insights scopes

**Non-Insights services:** access items via `result?.items ?? result?.value ?? []`
