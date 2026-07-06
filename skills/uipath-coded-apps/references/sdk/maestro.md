# Maestro Reference — Scopes, Conventions, Traps

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/maestro-processes/index.d.ts` and `dist/cases/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

## Imports

```typescript
import { MaestroProcesses, ProcessInstances, ProcessIncidents } from '@uipath/uipath-typescript/maestro-processes';
import { Cases, CaseInstances } from '@uipath/uipath-typescript/cases';
```

Types, options, and enums export from the same subpath as their service class.

## Scopes

- All Maestro operations: `PIMS`
- ProcessInstances.getBpmn: also requires `OR.Execution.Read`
- CaseInstances.getActionTasks: also requires `OR.Tasks` or `OR.Tasks.Read`
- Analytics / Insights methods (timelines, top-N, SLA): `Insights.RealTimeData Insights OR.Folders.Read` — a **separate bundle from `PIMS`**; SLA summaries additionally need `PIMS`. A 403 here means the External App lacks these scopes — surface it as a permissions message.

## Traps

### `folderKey` is a GUID, not a `folderId`

Maestro responses include `folderKey` (GUID string) but NOT `folderId` (number). If you need an Orchestrator method that requires `folderId` (e.g., `Processes.start()`), bridge via `Processes.getAll()` — see "Bridging folderKey ↔ folderId" in [orchestrator.md](orchestrator.md). **NEVER use `parseInt(folderKey)`** — it returns `NaN`.

### `name` is NOT `processKey`

The human-readable process name (e.g., `"Loan.Origination.and.Review"`) is the `name` field. The `processKey` is a separate internal identifier. When the user provides a process name, first call `MaestroProcesses.getAll()`, find the process where `name` matches, then use its `processKey` and `folderKey`:

```typescript
const allProcesses = await new MaestroProcesses(sdk).getAll();
const target = allProcesses.find(p => p.name === 'Loan.Origination.and.Review');
if (!target) throw new Error('Process not found');
const instances = await processInstances.getAll({ processKey: target.processKey, pageSize: 20 });
```

**NEVER use the process name as the processKey.**

### Attached methods

Objects returned by `getAll()`/`getById()` carry attached operation methods (`instance.cancel()`, `instance.getVariables()`, `process.getIncidents()`, `caseInstance.reopen()` …) — prefer them over re-calling the service with ids. The full list per type is in the `.d.ts` (`ProcessInstanceMethods`, `CaseInstanceMethods`, `ProcessMethods`).

### Rendering `getVariables()` output — MANDATORY

See [../patterns.md](../patterns.md) section "Rendering Process Instance Data". **NEVER dump raw JSON** — parse `globalVariables` / `elements` and render structured UI.

### `CaseInstances.reopen()` needs a `stageId`

`reopen(instanceId, folderKey, { stageId, comment? })` — the `stageId` is required; get it from `getStages()`.

## Which incident accessor when

| Scope | Use |
|---|---|
| All incidents across all folders (summary rollup) | `new ProcessIncidents(sdk).getAll()` — returns `ProcessIncidentGetAllResponse[]` |
| All incidents for one process | `MaestroProcesses.getIncidents(processKey, folderKey)` or `process.getIncidents()` |
| Incidents on a single instance | `ProcessInstances.getIncidents(instanceId, folderKey)` or `instance.getIncidents()` |

`ProcessIncidentGetAllResponse` (summary) and `ProcessIncidentGetResponse` (per-incident detail) are different shapes.

## Maestro Insights — RTM (SDK ≥ 1.4.x)

> Scopes: Top/timeline/element methods need `Insights Insights.RealTimeData OR.Folders.Read`; the SLA methods additionally need **`PIMS`**. These use the Insights RTM host (NOT PIMS) — contrast with `Cases.getAll`/`CaseInstances.getAll`.

`Cases` and `MaestroProcesses` expose the **same six analytics methods** with identical signatures. `CaseInstances` adds the two SLA methods.

**Calling conventions:** positional `Date` args (`start, end`) for the six analytics methods; `getSlaSummary` takes an **options object**. All return a **bare array** except `getSlaSummary` (rows on `.items`).

Server-side behavior the types don't show:

| Method | Returns (bare array of) | Notes |
|--------|------------------------|-------|
| `getTopRunCount(start, end, options?)` | `{ packageId, processKey, runCount, name }` | ≤5, ranked. `options`: `{ packageId?, processKey?, version? }` |
| `getTopFaultedCount(start, end, options?)` | `{ packageId, processKey, faultedCount, name }` | ≤10, ranked |
| `getTopExecutionDuration(start, end, options?)` | `{ packageId, processKey, duration, name }` | ≤5, `duration` in ms |
| `getTopElementFailedCount(start, end, options?)` | `{ elementName, elementType, processKey, failedCount }` | ≤10, BPMN elements |
| `getInstanceStatusTimeline(start, end, options?)` | `{ startTime, status, count }` | `status` ∈ `Completed`/`Faulted`/`Cancelled`; `startTime` is a **LOCALE string**, not ISO; `options`: `{ groupBy?: TimeInterval }` (HOUR/DAY/WEEK, default DAY) |
| `getElementStats(processKey, packageId, start, end, packageVersion)` | element duration/count stats incl. p50/p95/p99 | all positional args |

For Cases, `name` is derived from `packageId` (CaseManagement prefix stripped); for MaestroProcesses, `name === packageId`. Both present on every row.

`CaseInstances` SLA methods:

| Method | Returns | Notes |
|--------|---------|-------|
| `getSlaSummary(options?)` | `{ items: SlaSummaryResponse[] }` (default top 50) or paginated | `options`: `{ caseInstanceId?, startTimeUtc?: Date, endTimeUtc?: Date }` + pagination; `slaDueTime` is ISO UTC |
| `getStagesSlaSummary(options?)` | **bare** `{ caseInstanceId, stages: Stage[] }[]` | `options`: `{ caseInstanceId? }` |

`slaStatus` string values: `'On Track'`, `'At Risk'`, `'Overdue'`, `'Completed'`, `'Unknown'`. **Compare as strings — do not import the enum** (avoids TS narrowing errors; values are stable).

### Module patterns

```ts
// Top processes by run count (ranked-table) — native shape, return as-is
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { MaestroProcesses } = await import('@uipath/uipath-typescript/maestro-processes')
  const processes = await new MaestroProcesses(sdk).getTopRunCount(THIRTY_DAYS_AGO, NOW)
  return processes.map(x => ({ ...x }))
}
```

```ts
// Process instance status over time (multi-line-chart) — pivot long→wide, seed all series
export const fetchData: MetricFn = async (sdk) => {
  const { MaestroProcesses } = await import('@uipath/uipath-typescript/maestro-processes')
  const points = await new MaestroProcesses(sdk).getInstanceStatusTimeline(THIRTY_DAYS_AGO, NOW)
  const byDate: Record<string, Record<string, unknown>> = {}
  for (const p of points) {
    const d = String(p.startTime)
    byDate[d] = byDate[d] ?? { date: d, Completed: 0, Faulted: 0, Cancelled: 0 }
    byDate[d][String(p.status)] = p.count
  }
  return Object.values(byDate)
}
```

```ts
// SLA status breakdown (donut-chart) — group by status string
export const fetchData: MetricFn = async (sdk) => {
  const { CaseInstances } = await import('@uipath/uipath-typescript/cases')
  const { fetchAll } = await import('@/lib/paginate')
  const rows = await fetchAll(cursor => new CaseInstances(sdk).getSlaSummary({ pageSize: 200, cursor }))
  const by: Record<string, number> = {}
  for (const r of rows) { const k = String(r.slaStatus); by[k] = (by[k] ?? 0) + 1 }
  return Object.entries(by).map(([name, value]) => ({ name, value }))
}
```

```ts
// Cases at SLA risk (data-table) — filter At Risk / Overdue
export const fetchData: MetricFn = async (sdk) => {
  const { CaseInstances } = await import('@uipath/uipath-typescript/cases')
  const { fetchAll } = await import('@/lib/paginate')
  const rows = await fetchAll(cursor => new CaseInstances(sdk).getSlaSummary({ pageSize: 200, cursor }))
  return rows.filter(r => { const s = String(r.slaStatus); return s === 'At Risk' || s === 'Overdue' })
}
```

```ts
// Stage-level SLA (data-table) — flatten stages
export const fetchData: MetricFn = async (sdk) => {
  const { CaseInstances } = await import('@uipath/uipath-typescript/cases')
  const data = await new CaseInstances(sdk).getStagesSlaSummary()
  return data.flatMap(d => d.stages.map(s => ({
    caseInstanceId: d.caseInstanceId, stage: s.name, slaStatus: s.slaStatus, slaDueTime: s.slaDueTime, latestStatus: s.latestStatus,
  })))
}
```

```ts
// Element latency stats (T2 — identifiers baked in at authoring time)
export const fetchData: MetricFn = async (sdk) => {
  const { MaestroProcesses } = await import('@uipath/uipath-typescript/maestro-processes')
  const stats = await new MaestroProcesses(sdk).getElementStats('<processKey>', '<packageId>', THIRTY_DAYS_AGO, NOW, '<version>')
  return stats.map(x => ({ ...x }))
}
```
