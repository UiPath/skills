# Insights Capability Catalog

Source: "Insights APIs to use for dashboard as code" (internal Confluence)
Base URL pattern: `${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}/insightsrtm_/<namespace>/<endpoint>`
Environment values for VITE_UIPATH_BASE_URL:
  alpha:   https://alpha.api.uipath.com
  staging: https://staging.api.uipath.com
  prod:    https://api.uipath.com
All calls: POST JSON body. All require `tenantId` (UUID), `startTime` (ISO 8601), AND `endTime` (ISO 8601).
**Omitting `endTime` causes 500 errors.** Always pass `endTime: NOW` alongside any `startTime`.

---

## Agents namespace — POST /Agents/...

| Method                         | Route suffix                       | Key metrics                                    | Shape       | Key response fields |
|--------------------------------|------------------------------------|------------------------------------------------|-------------|---------------------|
| `agents.getSummaryV2`          | Agents/summaryV2                   | Success rate, failure rate, avg duration, Δ    | kpi, table  | `data.currentPeriodSummary.{ totalJobs, successfulJobs, successRate, averageDurationSeconds }` · per-agent: `agents[].{ processKey, successRate, averageDurationSeconds, lastJobStatus }` |
| `agents.getErrors`             | Agents/errors                      | Error count over time per agent                | area, line  | `data[].{ name (agentName), value (errorCount), date (ISO) }` · x_key=`date` y_key=`value` series=`name` |
| `agents.getTopErroredAgents`   | Agents/topErroredAgents            | Top-N erroring agents leaderboard              | bar, table  | `{ totalErrors, data[].{ agentId, name (agentName), count } }` · x_key=`name` y_key=`count` |
| `agents.getIncidents`          | Agents/incidents                   | Paged incident table                           | table       | `{ totalErrorCount, pagination, data[].{ type, description, agentId, agentName, firstSeen, count, folderPath } }` · columns: `agentName`, `type`, `description`, `count`, `firstSeen` |
| `agents.getIncidentDistribution` | Agents/incidentDistribution      | Error / Escalation / Policy split              | donut, kpi  | `{ data.{ errorCount, escalationCount, policyCount } }` · convert to array: `[{name:'Errors',value:errorCount},…]` |
| `agents.getConsumption`        | Agents/consumption                 | Top agents by AGU/PLTU                         | bar, table  | `{ data.{ totalConsumed, totalAGUConsumed, totalPLTUConsumed, agents[].{ agentId, agentName, consumedQuantity, consumedAGUQuantity } } }` |
| `agents.getConsumptionTimeline`| Agents/consumptionTimeline         | AGU burn-rate / invocation proxy over time     | area, line  | `data[].{ timeSlice (ISO), aguConsumption (number) }` · x_key=`timeSlice` y_key=`aguConsumption` |
| `agents.getLatencyTimeline`    | Agents/latencyTimeline             | P50 / P95 latency per agent                    | line        | `data[].{ name ('P50'|'P95'), value (seconds), date (ISO) }` · filter by `name` for each series |
| `agents.getAgents`             | Agents/agents                      | Fleet list with healthScore                    | table       | `{ data.{ agents[].{ agentId, agentName, folderPath, lastRun, healthScore, lastIncidentType, unitsQuantity, quantityAGU } } }` · columns: `agentName`, `healthScore`, `unitsQuantity`, `lastRun` |
| `agents.getUnitConsumption`    | Agents/summary/unit-consumption    | AGU/PLTU by complete vs incomplete jobs        | kpi, bar    | `{ data.currentPeriodSummary.{ totalAgentUnitConsumption.{ completeJobs, incompleteJobs }, totalPlatformUnitConsumption.{ completeJobs, incompleteJobs } } }` |
| `agents.getNames`              | Agents/names                       | Agent name list (filter dropdowns)             | filter only | `{ agents: string[] }` |

Not for MVP: `agents.getProcessEscalations`

---

## Traceview namespace — POST /Traceview/...

| Method                           | Route suffix                   | Key metrics                              | Shape      | Key response fields |
|----------------------------------|--------------------------------|------------------------------------------|------------|---------------------|
| `traceview.getLatencyTimeline`   | Traceview/latencyTimeline      | P50/P95 trace latency over time          | line       | `data[].{ name ('P50'|'P95'), value (seconds), date (ISO) }` · same shape as agents.getLatencyTimeline |
| `traceview.getErrorsTimeline`    | Traceview/errorsTimeline       | Trace errors per agent per bucket        | area, line | `data[].{ name (agentName), value (count), date (ISO) }` |
| `traceview.getMemoryTimeline`    | Traceview/memoryTimeline       | In/out/enabled/disabled memory counts    | area       | `data[].{ timeSlice (ISO), inMemoryCount, notInMemoryCount, totalCount, enabledMemoryCount, disabledMemoryCount }` |
| `traceview.getMemoryCallsTimeline` | Traceview/memoryCallsTimeline | Memory API calls over time               | bar        | `data[].{ timeSlice (ISO), memoryCallsCount }` |
| `traceview.getTopMemorySpaces`   | Traceview/topMemorySpaces      | Most-active memory spaces                | bar, table | (response structure TBD — see Insights team) |
| `traceview.getUnitConsumption`   | Traceview/unitConsumption      | Per-agent AIU + PLTU from traces         | table, bar | `data[].{ agentId, folderKey, agentVersion, agentUnitsConsumed, platformUnitsConsumed }` |

Not for MVP: `traceview.getSpansByTraceId`, `traceview.getSpansByReferenceId`

---

## Governance namespace — POST /Governance/...

| Method                          | Route suffix                      | Key metrics                       | Shape       |
|---------------------------------|-----------------------------------|-----------------------------------|-------------|
| `governance.getPolicySummary`   | Governance/policy/summary         | Allow/Deny/NoOp for one policy    | donut, kpi  |
| `governance.getPolicyTraces`    | Governance/policy/traces          | Per-evaluation trace table        | table       |
| `governance.getOperationSummary`| Governance/operation/summary      | Governed operation volume         | bar, kpi    |

Note: `getPolicySummary` requires additional `policy` (UUID) field in body.

---

## Jobs namespace — POST /api/v1.0/InsightsJobs/... (base: jobsBase)

| Method                          | Route suffix                                  | Key metrics                          | Shape      |
|---------------------------------|-----------------------------------------------|--------------------------------------|------------|
| `jobs.getSummary`               | api/v1.0/InsightsJobs/summary                 | KPI: total/success count, avg time   | kpi        |
| `jobs.getCompletedTimeline`     | api/v1.0/InsightsJobs/completed-timeline      | Completed jobs over time by state    | area, line |
| `jobs.getUncompletedTimeline`   | api/v1.0/InsightsJobs/uncompleted-timeline    | Pending/running jobs over time       | area, line |
| `jobs.getTopFailures`           | api/v1.0/InsightsJobs/top-failures            | Processes by failed-job count        | bar        |
| `jobs.getFailuresByReason`      | api/v1.0/InsightsJobs/failures-by-reason      | Failures by exception type           | bar, donut |
| `jobs.getProcessDetails`        | api/v1.0/InsightsJobs/process-details         | Per-process success/duration table   | table      |
| `jobs.getFailureDetails`        | api/v1.0/InsightsJobs/failure-details         | Detailed failure rows (drill-down)   | table      |

---

## Not in Insights — use SDK instead

Current operational state: live job/queue/task counts, process inventory, case SLA summaries,
DataFabric entity records, Maestro instance lists, Action Center task counts.

---

## Widget Recipes

Pre-written patterns for the most common widgets. When building plan.json `widgets` array entries, use these as the source for `dataHook`, `dataSelector`, `xKey`, `yKey`, `columns`, etc.

### ColumnDef format — memorise this, never invent variations

`RecordsTable` uses **`{ key, label, align? }`** — NOT TanStack Table's `{ accessorKey, header }`:

```typescript
// ✅ CORRECT — RecordsTable ColumnDef
{ key: 'agentName', label: 'Agent' }
{ key: 'healthScore', label: 'Health Score', align: 'right' as const }

// ❌ WRONG — these do not exist in RecordsTable:
{ accessorKey: 'agentName', header: 'Agent' }   // TanStack style — wrong
{ key: 'count', label: 'Errors', numeric: true } // numeric prop — wrong
```

**`align`** must be exactly `'right' as const` or `'left' as const` (or omit for default left). Never use `numeric: true`.

---

### Recipe 1 — Agent Error Trend
**Triggers:** "error rate", "errors over time", "error trend", "agent failures", "which agents are failing"
**Template:** `line-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: Array<{ name: string; value: number; date: string }> }>(
  'agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW }
)
const chartData = (data as any)?.data ?? []
// X_KEY: "date"   Y_KEY: "value"
// Note: data has one row per agent per day — this plots total across all agents
```

---

### Recipe 2 — Invocation / Activity Timeline
**Triggers:** "invocation volume", "how busy", "activity over time", "run count", "agent calls"
**Template:** `area-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: Array<{ timeSlice: string; aguConsumption: number }> }>(
  'agents.getConsumptionTimeline', { startTime: ONE_DAY_AGO, endTime: NOW }
)
const chartData = (data as any)?.data ?? []
// X_KEY: "timeSlice"   Y_KEY: "aguConsumption"
// timeSlice is ISO string — format with toLocaleTimeString() for readability
```

---

### Recipe 3 — Active Agents Count (KPI)
**Triggers:** "active agents", "fleet size", "how many agents", "agent count"
**Template:** `kpi-card.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: { agents: Array<{ agentId: string }> } }>(
  'agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW }
)
const value = String((data as any)?.data?.agents?.length ?? '—')
// TITLE: "Active Agents"
```

---

### Recipe 4 — Success Rate KPI
**Triggers:** "success rate", "pass rate", "health score", "how well are agents doing"
**Template:** `kpi-card.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: { currentPeriodSummary: { successRate: number; totalJobs: number; averageDurationSeconds: number } }
}>('agents.getSummaryV2', { startTime: THIRTY_DAYS_AGO, endTime: NOW })
const value = (() => {
  const s = (data as any)?.data?.currentPeriodSummary
  return s ? `${s.successRate.toFixed(1)}%` : '—'
})()
// TITLE: "Success Rate (30 days)"
```

---

### Recipe 5 — Avg Duration KPI
**Triggers:** "average duration", "how long do agents take", "avg execution time"
**Template:** `kpi-card.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: { currentPeriodSummary: { averageDurationSeconds: number } }
}>('agents.getSummaryV2', { startTime: THIRTY_DAYS_AGO, endTime: NOW })
const value = (() => {
  const secs = (data as any)?.data?.currentPeriodSummary?.averageDurationSeconds
  return secs != null ? `${(secs / 60).toFixed(1)}m` : '—'
})()
// TITLE: "Avg Duration (30 days)"
```

---

### Recipe 6 — Top Erroring Agents (Bar)
**Triggers:** "top erroring agents", "most failures", "error leaderboard", "which agents fail most"
**Template:** `bar-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{
  totalErrors: number; data: Array<{ name: string; count: number }>
}>('agents.getTopErroredAgents', { startTime: SEVEN_DAYS_AGO, endTime: NOW })
const chartData = (data as any)?.data ?? []
// X_KEY: "name"   Y_KEY: "count"
```

---

### Recipe 7 — P95 Latency Trend (Line)
**Triggers:** "latency", "response time", "P95", "P50", "how fast are agents", "slowest agents"
**Template:** `line-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: Array<{ name: 'P50' | 'P95'; value: number; date: string }>
}>('agents.getLatencyTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })
const chartData = (data as any)?.data?.filter((d: { name: string }) => d.name === 'P95') ?? []
// X_KEY: "date"   Y_KEY: "value"
// To show both P50 and P95: remove the filter and add a second <Line dataKey="value" />
// grouped by name — or split into two separate chart components
```

---

### Recipe 8 — Incident Type Distribution (Donut)
**Triggers:** "incident types", "error vs escalation", "incident breakdown", "what kind of failures"
**Template:** `donut-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: { errorCount: number; escalationCount: number; policyCount: number }
}>('agents.getIncidentDistribution', { startTime: THIRTY_DAYS_AGO, endTime: NOW })
const chartData = [
  { name: 'Errors',      value: (data as any)?.data?.errorCount      ?? 0 },
  { name: 'Escalations', value: (data as any)?.data?.escalationCount  ?? 0 },
  { name: 'Policy',      value: (data as any)?.data?.policyCount      ?? 0 },
].filter(d => d.value > 0)
// DATA_KEY: "value"   NAME_KEY: "name"
```

---

### Recipe 9 — Agent Fleet Table
**Triggers:** "agent list", "fleet overview", "all agents", "agent status table", "health scores"
**Template:** `data-table.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: { agents: Array<{ agentName: string; healthScore: number; unitsQuantity: number; lastRun: string }> }
}>('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })
const rows = [...((data as any)?.data?.agents ?? [])].sort((a, b) => b.unitsQuantity - a.unitsQuantity)
// COLUMNS: [
//   { key: 'agentName',    label: 'Agent' },
//   { key: 'healthScore',  label: 'Health' },
//   { key: 'unitsQuantity', label: 'Units Used' },
//   { key: 'lastRun',      label: 'Last Run' },
// ]
```

---

### Recipe 10 — Top Agents by Consumption (Bar)
**Triggers:** "top consumers", "most expensive agents", "highest usage", "who uses the most AGU"
**Template:** `bar-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: { agents: Array<{ agentName: string; consumedQuantity: number }> }
}>('agents.getConsumption', { startTime: THIRTY_DAYS_AGO, endTime: NOW })
const chartData = (data as any)?.data?.agents ?? []
// X_KEY: "agentName"   Y_KEY: "consumedQuantity"
```

---

### Recipe 11 — Job Completion Timeline
**Triggers:** "job trend", "completed jobs over time", "automation volume", "job history"
**Template:** `area-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: Array<{ date: string; count: number }> }>(
  'jobs.getCompletedTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW }
)
const chartData = (data as any)?.data ?? []
// X_KEY: "date"   Y_KEY: "count"
// Note: confirm field names with Insights team — jobs API response shape not yet fully documented
```

---

### Recipe 12 — Memory Usage Timeline (Traceview)
**Triggers:** "memory usage", "agent memory", "in-memory traces", "context retention"
**Template:** `area-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: Array<{ timeSlice: string; inMemoryCount: number; totalCount: number }>
}>('traceview.getMemoryTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })
const chartData = (data as any)?.data ?? []
// X_KEY: "timeSlice"   Y_KEY: "inMemoryCount"
```

---

### Recipe 13 — P50 + P95 Latency (multi-line)
**Triggers:** "latency with P50 and P95", "compare P50 vs P95", "latency percentiles"
**Template:** `multi-line-chart.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }>(
  'agents.getLatencyTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW }
)
const rawData = (data as any)?.data ?? []
const chartData = rawData.reduce((acc: Record<string, unknown>[], row: { name: string; value: number; date: string }) => {
  const existing = acc.find(r => r.date === row.date) as Record<string, unknown> | undefined
  if (existing) { existing[row.name] = row.value }
  else acc.push({ date: row.date, [row.name]: row.value })
  return acc
}, [])
// X_KEY: "date"
// SERIES: [{ key: 'P50', color: 'hsl(var(--chart-1))' }, { key: 'P95', color: 'hsl(var(--chart-2))' }]
```

---

### Recipe 14 — Agent Error Rate KPI with Sparkline
**Triggers:** "agent error rate trend", "errors with trend", "error KPI with sparkline"
**Template:** `kpi-with-sparkline.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: Array<{ name: string; value: number; date: string }> }>(
  'agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW }
)
const allRows = (data as any)?.data ?? []
// Aggregate total errors per day across all agents
const byDate = allRows.reduce((acc: Record<string, number>, r: { date: string; value: number }) => {
  const day = r.date.slice(0, 10)
  acc[day] = (acc[day] ?? 0) + r.value
  return acc
}, {})
const sparklineData = Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b)).map(([date, errors]) => ({ date, errors }))
const latestValue = sparklineData.length > 0 ? String(sparklineData[sparklineData.length - 1].errors) : '—'
// VALUE_EXPRESSION: latestValue
// Y_KEY: "errors"
// DELTA_DIR: "down-good"  (fewer errors is better)
```

---

### Recipe 15 — Top Agents Ranked Table
**Triggers:** "top agents", "leaderboard", "agents ranked by", "most errors/usage/consumption"
**Template:** `ranked-table.tsx`
```tsx
const { data, loading, error } = useInsights<{ data: Array<{ agentName: string; count: number }> }>(
  'agents.getTopErroredAgents', { startTime: SEVEN_DAYS_AGO, endTime: NOW }
)
const rows = [...((data as any)?.data ?? [])].sort((a, b) => b.count - a.count)
// COLUMNS: [{ key: 'agentName', label: 'Agent' }, { key: 'count', label: 'Errors', align: 'right' as const }]
// X_KEY for sort: "count"
```

---

### Recipe 16 — Incident Type Progress Bars
**Triggers:** "incident breakdown", "error vs escalation", "incident types as bars", "proportion breakdown"
**Template:** `progress-bar-list.tsx`
```tsx
const { data, loading, error } = useInsights<{
  data: { errorCount: number; escalationCount: number; policyCount: number }
}>('agents.getIncidentDistribution', { startTime: THIRTY_DAYS_AGO, endTime: NOW })
const items = [
  { label: 'Errors',      value: (data as any)?.data?.errorCount ?? 0 },
  { label: 'Escalations', value: (data as any)?.data?.escalationCount ?? 0 },
  { label: 'Policy',      value: (data as any)?.data?.policyCount ?? 0 },
].filter(d => d.value > 0)
// LABEL_KEY: "label"   VALUE_KEY: "value"
```

---

---

### Recipe 17 — Queue Depth (SDK)
**Triggers:** "queue depth", "active queue items", "queued transactions", "how full is my queue"
**Template:** `kpi-card.tsx`
**Source:** SDK `QueueItems.getAll()` — operational state, not Insights analytics
```tsx
import { useAuth } from '@/hooks/useAuth'
import { QueueItems } from '@uipath/uipath-typescript/queues'
import { useState, useEffect } from 'react'

export function QueueDepthKpi() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [count, setCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    const svc = new QueueItems(sdk as never)
    svc.getAll({ status: 'New,InProgress' })
      .then(r => setCount(r.items?.length ?? 0))
      .catch(e => setError(e instanceof Error ? e : new Error(String(e))))
      .finally(() => setLoading(false))
  }, [sdk, isAuthenticated])

  // ... card anatomy: title "Active Queue Items", delta neutral
}
// VALUE: String(count ?? '—')
// DELTA_DIR: "neutral"   DETAIL_ROUTE: "/queue-depth"
```

---

### Recipe 18 — Running Jobs Count (SDK)
**Triggers:** "running jobs", "active jobs", "jobs in progress", "how many jobs are running"
**Template:** `kpi-card.tsx`
**Source:** SDK `Jobs.getAll()` — live operational state
```tsx
import { Jobs } from '@uipath/uipath-typescript/jobs'

// Inside useEffect:
const svc = new Jobs(sdk as never)
svc.getAll({ state: 'Running,Pending' })
  .then(r => setCount(r.items?.length ?? 0))
  ...

// VALUE: String(count ?? '—')
// DELTA_DIR: "neutral"   DETAIL_ROUTE: "/running-jobs"
```

---

### Recipe 19 — Pending Action Center Tasks (SDK)
**Triggers:** "pending tasks", "action center backlog", "tasks waiting for review", "human tasks"
**Template:** `kpi-card.tsx`
**Source:** SDK `Tasks.getAll()` — Action Center tasks awaiting human completion
```tsx
import { Tasks } from '@uipath/uipath-typescript/tasks'

// Inside useEffect:
const svc = new Tasks(sdk as never)
svc.getAll({ status: 'Pending,Unassigned' })
  .then(r => setCount(r.items?.length ?? 0))
  ...

// VALUE: String(count ?? '—')
// DELTA_DIR: "neutral"   DETAIL_ROUTE: "/pending-tasks"
```

---

### Recipe 20 — Job Success Rate — Today (SDK)
**Triggers:** "job success rate today", "how are jobs doing", "success vs failure today"
**Template:** `kpi-card.tsx`
**Source:** SDK `Jobs.getAll()` — computes success % from state counts
```tsx
import { Jobs } from '@uipath/uipath-typescript/jobs'

// Inside useEffect — fetch today's completed jobs and compute rate:
const svc = new Jobs(sdk as never)
const since = new Date(Date.now() - 86_400_000).toISOString()
svc.getAll({ startTime: since, states: 'Successful,Faulted,Stopped' })
  .then(r => {
    const items = r.items ?? []
    const total = items.length
    const ok = items.filter(j => j.state === 'Successful').length
    setValue(total > 0 ? `${((ok / total) * 100).toFixed(1)}%` : '—')
  })
  ...

// VALUE_EXPRESSION: computed above as `value` state
// DELTA_DIR: "up-good"   DETAIL_ROUTE: "/job-success-rate"
```

---

### Recipe 21 — Process / Automation Inventory (SDK)
**Triggers:** "what processes are deployed", "automation inventory", "list my processes", "what automations do I have"
**Template:** `data-table.tsx`
**Source:** SDK `Processes.getAll()` — shows deployed automations
```tsx
import { Processes } from '@uipath/uipath-typescript/processes'

// Inside useEffect:
const svc = new Processes(sdk as never)
svc.getAll()
  .then(r => setRows(r.items ?? []))
  ...

// DATA_SELECTOR: rows (already an array from above)
// COLUMNS: [{ key: 'name', label: 'Process' }, { key: 'description', label: 'Description' }, { key: 'version', label: 'Version' }]
// DETAIL_ROUTE: "/process-inventory"
```

> **SDK widget note:** All 5 SDK recipes use `useAuth().sdk` instead of `useInsights()`.
> They do NOT need `startTime`/`endTime` or `tenantId` — those are Insights-only requirements.
> SDK calls use OAuth scopes from the existing `useAuth()` hook.

---

**No matching recipe?** Derive from scratch using the Routing Table in `data-router.md` and the Key response fields in the tables above. If no endpoint matches at all, see the **Fallback** section in `data-router.md`.

## Suggested Dashboard Packages

| Dashboard                | Primary endpoints                                                                  |
|--------------------------|------------------------------------------------------------------------------------|
| Executive Fleet Health   | getSummaryV2, jobs.getSummary, getIncidentDistribution, getConsumptionTimeline      |
| Jobs Operations          | jobs.getCompletedTimeline, jobs.getTopFailures, jobs.getProcessDetails             |
| Agent Reliability        | getErrors, getTopErroredAgents, getIncidents, getLatencyTimeline                   |
| Agent Cost / FinOps      | getConsumption, getConsumptionTimeline, getUnitConsumption, getAgents              |
| Traces & Memory          | traceview.getLatencyTimeline, traceview.getErrorsTimeline, traceview.getMemoryTimeline |
| Governance Posture       | governance.getPolicySummary, governance.getPolicyTraces, governance.getOperationSummary |
