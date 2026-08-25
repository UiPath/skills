# Maestro — Traps & Server Behavior

Signatures/params/examples: `dist/maestro-processes/index.d.ts`, `dist/cases/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Scope fork warning:** this service family splits across TWO scope bundles — instance/process operations use `PIMS`, while the analytics/SLA methods use the Insights bundle (`Insights Insights.RealTimeData OR.Folders.Read`; SLA also needs `PIMS`). Do not assume service-uniform scopes; check the shipped table per method. A 403 on analytics means the External App lacks the Insights bundle — surface it as a permissions message.

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

### `reopen()` — where the required `stageId` comes from

Get it from `getStages()` on the case instance.

### Rendering `getVariables()` output — MANDATORY

See [../patterns.md](../patterns.md) section "Rendering Process Instance Data". **NEVER dump raw JSON** — parse `globalVariables` / `elements` and render structured UI.

## Which incident accessor when

| Scope | Use |
|---|---|
| All incidents across all folders (summary rollup) | `new ProcessIncidents(sdk).getAll()` — returns `ProcessIncidentGetAllResponse[]` |
| All incidents for one process | `MaestroProcesses.getIncidents(processKey, folderKey)` or `process.getIncidents()` |
| Incidents on a single instance | `ProcessInstances.getIncidents(instanceId, folderKey)` or `instance.getIncidents()` |

`ProcessIncidentGetAllResponse` (summary) and `ProcessIncidentGetResponse` (per-incident detail) are different shapes.

## Analytics / Insights RTM — server behavior the types don't show

`Cases` and `MaestroProcesses` expose the same six analytics methods; `CaseInstances` adds the two SLA methods.

| Method | Server behavior |
|--------|----------------|
| `getTopRunCount` | ≤5 rows, ranked |
| `getTopFaultedCount` | ≤10 rows, ranked |
| `getTopExecutionDuration` | ≤5 rows, `duration` in **ms** |
| `getTopElementFailedCount` | ≤10 rows, BPMN elements |
| `getInstanceStatusTimeline` | `startTime` is a **LOCALE string**, not ISO |

- For Cases, `name` is derived from `packageId` (CaseManagement prefix stripped); for MaestroProcesses, `name === packageId`.
- `slaStatus`: **compare as strings** (`'At Risk'`, `'Overdue'`, …) — do not import the enum (avoids TS narrowing errors; values are stable).

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
