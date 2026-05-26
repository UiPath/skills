# SDK Capability Registry

Single source of truth for what data the dashboard skill can access. Consulted during Phase 3a
feasibility gate. Route each metric here before planning any widget.

**Data layers:**
- **Insights RTM** — POST-based analytics API via custom HTTP client (temporary; will migrate to SDK)
- **Orchestrator SDK** — live operational state via `@uipath/uipath-typescript` services

---

## Hard Refuse Table

Check this table FIRST in Phase 3a. If the user's request matches, refuse before planning.
Never approximate these silently. State the reason and offer the best alternative if one exists.

| Requested metric | Why unavailable | Suggest instead |
|---|---|---|
| Agent cost in dollars / currency | Platform tracks AGU/PLTU units, not currency | `agents.getConsumption` (AGU/PLTU) |
| Real-time CPU / memory per agent | Not exposed via any UiPath API | — |
| Per-user job attribution | Job records don't carry end-user identity | — |
| Cross-tenant comparison | Dashboard scoped to one tenant at build time | — |
| Agent version history | No version tracking endpoint | — |
| Who triggered a job (username) | Not in any UiPath API | — |
| Historical queue throughput trend | No Insights endpoint for queue history | SDK `QueueItems.getAll()` for current state |
| SLA breach count as % | No % endpoint; raw count only | `CaseInstances.getSlaSummary()` for counts |
| Per-agent memory usage | Traceview is fleet-level only | `traceview.getMemoryTimeline` (fleet) |
| Error message text / stack traces | `jobs.getFailureDetails` has rows but no aggregation | `jobs.getFailuresByReason` for type breakdown |

**Refuse wording pattern:**
```
⚠ "[Requested metric]" isn't available — [specific reason].
[If alternative: I can show [alternative] instead — want that?]
[If no alternative: I've excluded it from the plan.]
```

---

## Metric Classification

When Phase 3a classifies each requested metric:

- **GREEN** — capability entry exists AND matching template listed → use `widgets[]` array in plan.json
- **AMBER** — capability entry exists, no template → write custom SDK hook in `files{}` map; use the
  exact method signature and response shape from the capability entry below. TypeScript must compile.
- **RED** — no capability entry → hard refuse using the wording pattern above

---

## Insights RTM Capabilities

Base URL: `${VITE_UIPATH_CLOUD_URL}/${ORG}/${TENANT}/insightsrtm_`
Jobs base: `${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}`
All calls: POST JSON. All require `tenantId` (UUID), `startTime` (ISO 8601), `endTime` (ISO 8601).
**Omitting `endTime` causes 500 errors.** Always pass `endTime: NOW`.

> **Migration note:** These endpoints will be replaced by `sdk.insights.*` methods when the
> Insights service joins the TypeScript SDK. When that happens, update each entry's **Source** line
> and the `InsightsClient` method references. Templates and plan.json format do not change.

---

### agents.getSummaryV2 — Agent Fleet Summary

**Source:** Insights RTM HTTP client · `POST Agents/summaryV2`
**Response shape:**
```typescript
{
  data: {
    currentPeriodSummary: {
      totalJobs: number
      successfulJobs: number
      successRate: number          // 0–100
      averageDurationSeconds: number
    }
    agents: Array<{
      processKey: string
      successRate: number
      averageDurationSeconds: number
      lastJobStatus: string
    }>
  }
}
```
**Computable metrics:** Fleet success rate, avg duration, total job count, per-agent success rate
**Cannot compute:** Time-series trend (aggregate only — never use for line/area charts), cost
**Templates:** `kpi-card`, `ranked-table`
**Aliases:** "success rate", "pass rate", "how well are agents doing", "avg duration", "average execution time", "fleet summary", "overview", "key metrics", "important metrics", "agent health overview"

---

### agents.getErrors — Agent Error Counts Over Time

**Source:** Insights RTM HTTP client · `POST Agents/errors`
**Response shape:**
```typescript
{ data: Array<{ name: string; value: number; date: string }> }
// name = agentName, value = errorCount, date = ISO string
// One row per agent per time bucket
```
**Computable metrics:** Error count over time, total errors, error trend, per-agent error count
**Cannot compute:** Error rate % (need total runs — combine with agents.getSummaryV2), error text
**Templates:** `line-chart`, `area-chart`, `kpi-card`, `kpi-with-sparkline`
**Aliases:** "agent errors", "error count", "errors over time", "error trend", "agent failures", "which agents are failing", "error spikes"

---

### agents.getTopErroredAgents — Top-N Erroring Agents

**Source:** Insights RTM HTTP client · `POST Agents/topErroredAgents`
**Response shape:**
```typescript
{ totalErrors: number; data: Array<{ agentId: string; name: string; count: number }> }
```
**Computable metrics:** Error leaderboard, top N by error count
**Cannot compute:** Error rate %, error text
**Templates:** `bar-chart`, `ranked-table`
**Aliases:** "top erroring agents", "most failures", "error leaderboard", "which agents fail most", "worst agents"

---

### agents.getIncidents — Agent Incidents (Paged)

**Source:** Insights RTM HTTP client · `POST Agents/incidents`
**Response shape:**
```typescript
{
  totalErrorCount: number
  pagination: { total: number; pageNumber: number; pageSize: number }
  data: Array<{
    type: string
    description: string
    agentId: string
    agentName: string
    firstSeen: string     // ISO
    count: number
    folderPath: string
  }>
}
```
**Computable metrics:** Incident list, incident type breakdown, recurring error detection
**Cannot compute:** Root cause, fix recommendations
**Templates:** `data-table`
**Aliases:** "agent incidents", "recurring errors", "incident list", "what went wrong", "failure details"

---

### agents.getIncidentDistribution — Incident Type Split

**Source:** Insights RTM HTTP client · `POST Agents/incidentDistribution`
**Response shape:**
```typescript
{ data: { errorCount: number; escalationCount: number; policyCount: number } }
```
**Computable metrics:** Error / Escalation / Policy proportion
**Cannot compute:** Time-series (single aggregate period)
**Templates:** `donut-chart`, `progress-bar-list`, `kpi-card`
**Aliases:** "incident types", "error vs escalation", "incident breakdown", "what kind of failures", "incident distribution"

---

### agents.getConsumption — Agent AGU/PLTU Consumption

**Source:** Insights RTM HTTP client · `POST Agents/consumption`
**Response shape:**
```typescript
{
  data: {
    totalConsumed: number
    totalAGUConsumed: number
    totalPLTUConsumed: number
    agents: Array<{
      agentId: string
      agentName: string
      consumedQuantity: number
      consumedAGUQuantity: number
    }>
  }
}
```
**Computable metrics:** AGU/PLTU by agent, total consumption, top consumers
**Cannot compute:** Cost in currency, future consumption forecast
**Templates:** `bar-chart`, `ranked-table`, `kpi-card`
**Aliases:** "AGU consumption", "PLTU consumption", "token consumption", "top consumers", "most expensive agents", "highest usage", "who uses the most AGU"

---

### agents.getConsumptionTimeline — AGU Burn-Rate Over Time

**Source:** Insights RTM HTTP client · `POST Agents/consumptionTimeline`
**Response shape:**
```typescript
{ data: Array<{ timeSlice: string; aguConsumption: number }> }
// timeSlice = ISO string (hourly or daily bucket)
```
**Computable metrics:** AGU burn rate over time, invocation activity proxy
**Cannot compute:** Per-agent breakdown (fleet total only), cost
**Templates:** `area-chart`, `line-chart`
**Aliases:** "invocation volume", "how busy", "activity over time", "run count", "agent calls", "AGU burn rate", "usage over time"

---

### agents.getLatencyTimeline — P50/P95 Latency Per Agent

**Source:** Insights RTM HTTP client · `POST Agents/latencyTimeline`
**Response shape:**
```typescript
{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }
// value in seconds; one row per percentile per time bucket
```
**Computable metrics:** P50/P95 latency trend, slowest agents
**Cannot compute:** P99, individual run timing
**Templates:** `line-chart`, `multi-line-chart`
**Aliases:** "latency", "response time", "P95", "P50", "how fast are agents", "slowest agents", "execution time trend"

---

### agents.getAgents — Agent Fleet List

**Source:** Insights RTM HTTP client · `POST Agents/agents`
**Response shape:**
```typescript
{
  data: {
    agents: Array<{
      agentId: string
      agentName: string
      folderPath: string
      lastRun: string     // ISO
      healthScore: number // 0–100
      lastIncidentType: string
      unitsQuantity: number
      quantityAGU: number
    }>
  }
}
```
**Computable metrics:** Fleet list with health, active agent count, stale agents, unit usage per agent
**Cannot compute:** Real-time status, current run state
**Templates:** `data-table`, `kpi-card` (for count)
**Aliases:** "agent list", "fleet overview", "all agents", "agent status table", "health scores", "active agents", "fleet size", "how many agents", "agent count"

---

### agents.getUnitConsumption — AGU/PLTU by Job Completion

**Source:** Insights RTM HTTP client · `POST Agents/summary/unit-consumption`
**Response shape:**
```typescript
{
  data: {
    currentPeriodSummary: {
      totalAgentUnitConsumption: { completeJobs: number; incompleteJobs: number }
      totalPlatformUnitConsumption: { completeJobs: number; incompleteJobs: number }
    }
  }
}
```
**Computable metrics:** AGU/PLTU split by complete vs incomplete jobs
**Cannot compute:** Per-agent breakdown, trend over time
**Templates:** `kpi-card`, `bar-chart`
**Aliases:** "AGU by job type", "consumption split", "complete vs incomplete consumption", "unit consumption breakdown"

---

### traceview.getLatencyTimeline — Trace-Level P50/P95 Latency

**Source:** Insights RTM HTTP client · `POST Traceview/latencyTimeline`
**Response shape:** same shape as `agents.getLatencyTimeline`
```typescript
{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }
```
**Computable metrics:** Trace-level latency percentiles (NOT agent-level)
**Cannot compute:** Per-agent breakdown — use `agents.getLatencyTimeline` for that
**Templates:** `line-chart`, `multi-line-chart`
**Aliases:** "trace latency", "trace P50/P95", "trace response time"

---

### traceview.getErrorsTimeline — Trace Errors Per Agent

**Source:** Insights RTM HTTP client · `POST Traceview/errorsTimeline`
**Response shape:**
```typescript
{ data: Array<{ name: string; value: number; date: string }> }
// name = agentName
```
**Computable metrics:** Trace error count per agent over time
**Cannot compute:** Per-agent breakdown across fleet — use `agents.getErrors` for that
**Templates:** `area-chart`, `line-chart`
**Aliases:** "trace errors", "trace error trend"

---

### traceview.getMemoryTimeline — Agent Memory Usage (Fleet)

**Source:** Insights RTM HTTP client · `POST Traceview/memoryTimeline`
**Response shape:**
```typescript
{
  data: Array<{
    timeSlice: string        // ISO
    inMemoryCount: number
    notInMemoryCount: number
    totalCount: number
    enabledMemoryCount: number
    disabledMemoryCount: number
  }>
}
```
**Computable metrics:** In-memory vs not-in-memory agent count over time
**Cannot compute:** Per-agent memory usage (fleet total only)
**Templates:** `area-chart`
**Aliases:** "memory usage", "agent memory", "in-memory traces", "context retention", "memory timeline"

---

### governance.getPolicySummary — Policy Allow/Deny/NoOp Ratio

**Source:** Insights RTM HTTP client · `POST Governance/policy/summary`
**Extra required field:** `policy` (UUID of the policy to report on)
**Response shape:**
```typescript
{ data: { allowCount: number; denyCount: number; noOpCount: number } }
```
**Computable metrics:** Policy decision ratio
**Cannot compute:** Cross-policy comparison in one widget (one policy per call)
**Templates:** `donut-chart`, `kpi-card`
**Aliases:** "policy summary", "allow vs deny", "governance violations", "policy decisions"

---

### governance.getPolicyTraces — Policy Decision Trace Table

**Source:** Insights RTM HTTP client · `POST Governance/policy/traces`
**Response shape:**
```typescript
{
  data: Array<{
    traceId: string
    agentId: string
    agentName: string
    decision: 'Allow' | 'Deny' | 'NoOp'
    timestamp: string
    policyName: string
  }>
}
```
**Computable metrics:** Recent policy evaluations, denial feed
**Templates:** `data-table`
**Aliases:** "policy traces", "recent policy decisions", "denial feed", "governance trace"

---

### governance.getOperationSummary — Governed Operation Volume

**Source:** Insights RTM HTTP client · `POST Governance/operation/summary`
**Response shape:**
```typescript
{ data: Array<{ operationName: string; count: number; date: string }> }
```
**Computable metrics:** Which operations are governed, volume over time
**Templates:** `bar-chart`
**Aliases:** "governed operations", "operation volume", "governance activity"

---

### jobs.getSummary — Job KPI Summary

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/summary`
**Response shape:**
```typescript
{
  data: {
    totalJobs: number
    successfulJobs: number
    failedJobs: number
    averageDurationSeconds: number
  }
}
```
**Computable metrics:** Total jobs, success count, failure count, avg duration (aggregate, not time-series)
**Cannot compute:** Time-series trend (use `jobs.getCompletedTimeline` for that)
**Templates:** `kpi-card`
**Aliases:** "job KPI", "job summary", "total jobs", "job success count", "job aggregate"

---

### jobs.getCompletedTimeline — Completed Jobs Over Time

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/completed-timeline`
**Response shape:**
```typescript
{ data: Array<{ date: string; count: number; state: string }> }
// state = 'Successful' | 'Faulted' | 'Stopped'
```
**Computable metrics:** Completed job volume over time, success vs failure trend
**Templates:** `area-chart`, `line-chart`
**Aliases:** "job trend", "completed jobs over time", "automation volume", "job history", "jobs over time"

---

### jobs.getTopFailures — Top Failing Processes

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/top-failures`
**Response shape:**
```typescript
{ data: Array<{ processName: string; failureCount: number }> }
```
**Computable metrics:** Ranked list of processes by failure count
**Templates:** `bar-chart`, `ranked-table`
**Aliases:** "top failures", "failing processes", "most failed automations", "worst processes"

---

### jobs.getFailuresByReason — Job Failures by Exception Type

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/failures-by-reason`
**Response shape:**
```typescript
{ data: Array<{ reason: string; count: number }> }
```
**Computable metrics:** Breakdown of failure causes by exception type
**Templates:** `donut-chart`, `bar-chart`
**Aliases:** "failure reasons", "exception types", "why are jobs failing", "failure breakdown"

---

### jobs.getProcessDetails — Per-Process Job Stats

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/process-details`
**Response shape:**
```typescript
{
  data: Array<{
    processName: string
    totalJobs: number
    successfulJobs: number
    successRate: number
    averageDurationSeconds: number
  }>
}
```
**Computable metrics:** Per-process success rate, duration, volume
**Templates:** `data-table`, `ranked-table`
**Aliases:** "process breakdown", "per-process stats", "automation details", "which process succeeds most"

---

## Orchestrator SDK Capabilities

Import pattern — always use subpath exports:
```typescript
import { Jobs } from '@uipath/uipath-typescript/jobs'
import { QueueItems } from '@uipath/uipath-typescript/queues'
import { Processes } from '@uipath/uipath-typescript/processes'
import { Tasks } from '@uipath/uipath-typescript/tasks'
```

SDK calls do NOT need `tenantId`, `startTime`, or `endTime` — those are Insights-only.
SDK calls use `const { sdk, isAuthenticated } = useAuth()` then `new ServiceClass(sdk as never)`.

---

### Jobs.getAll — Current Job State

**Source:** SDK · `@uipath/uipath-typescript/jobs`
**Call pattern:** `new Jobs(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{
  state?: string           // comma-separated: 'Running,Pending,Successful,Faulted,Stopped'
  startTime?: string       // ISO — filter jobs started after this time
  processName?: string     // filter by process
  top?: number             // page size (default 20, max 100)
  skip?: number            // offset for pagination
}
```
**Response shape:**
```typescript
{
  items: Array<{
    id: string
    key: string
    state: 'Running' | 'Successful' | 'Faulted' | 'Stopped' | 'Pending'
    startTime: string    // ISO
    endTime: string      // ISO (null if still running)
    processName: string
    organizationUnitId: number
  }>
  count: number          // total matching records (not just this page)
}
```
**Computable metrics:** Running job count, pending count, today's success count, today's failure count
**Cannot compute:** Historical trend (use `jobs.getCompletedTimeline`), per-agent breakdown
**Templates:** `sdk-kpi-card`
**Aliases:** "running jobs", "active jobs", "jobs in progress", "how many jobs are running", "pending jobs", "job queue", "job count today", "failed jobs today"

---

### QueueItems.getAll — Queue Depth (Current State)

**Source:** SDK · `@uipath/uipath-typescript/queues`
**Call pattern:** `new QueueItems(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{
  status?: string          // comma-separated: 'New,InProgress,Successful,Failed,Abandoned,Retried'
  queueDefinitionId?: number
  top?: number
  skip?: number
}
```
**Response shape:**
```typescript
{
  items: Array<{
    id: number
    status: 'New' | 'InProgress' | 'Successful' | 'Failed' | 'Abandoned' | 'Retried'
    queueDefinitionId: number
    queueDefinitionName: string
    priority: 'Low' | 'Normal' | 'High'
    dueDate: string | null    // ISO
    creationTime: string      // ISO
  }>
  count: number
}
```
**Computable metrics:** Queue depth (New + InProgress count), failed item count, queue name breakdown
**Cannot compute:** Historical throughput trend, SLA compliance %
**Templates:** `sdk-kpi-card`, `sdk-data-table`
**Aliases:** "queue depth", "active queue items", "queued transactions", "how full is my queue", "queue status", "queue items"

---

### Processes.getAll — Deployed Automation Inventory

**Source:** SDK · `@uipath/uipath-typescript/processes`
**Call pattern:** `new Processes(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{ top?: number; skip?: number }
```
**Response shape:**
```typescript
{
  items: Array<{
    id: string
    name: string
    description: string
    version: string
    environmentId: number
    environmentName: string
  }>
  count: number
}
```
**Computable metrics:** Total deployed automations, process inventory
**Cannot compute:** Run history, success rate (use Insights for historical)
**Templates:** `sdk-data-table`
**Aliases:** "what processes are deployed", "automation inventory", "list my processes", "what automations do I have", "deployed processes", "process list"

---

### Tasks.getAll — Action Center Pending Tasks

**Source:** SDK · `@uipath/uipath-typescript/tasks`
**Call pattern:** `new Tasks(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{
  status?: string          // comma-separated: 'Unassigned,Pending,Completed'
  type?: string
  top?: number
  skip?: number
}
```
**Response shape:**
```typescript
{
  items: Array<{
    id: number
    title: string
    status: 'Unassigned' | 'Pending' | 'Completed'
    type: string
    creationTime: string    // ISO
    lastModificationTime: string
  }>
  count: number
}
```
**Computable metrics:** Pending task count, unassigned task count, Action Center backlog
**Cannot compute:** SLA compliance, average resolution time
**Templates:** `sdk-kpi-card`
**Aliases:** "pending tasks", "action center backlog", "tasks waiting for review", "human tasks", "approval queue", "unassigned tasks"

---

## Standard Time Constants

Canonical definition — reference these, do not redefine them in other files.

```typescript
const NOW             = new Date().toISOString()
const ONE_DAY_AGO     = new Date(Date.now() -    86_400_000).toISOString()
const SEVEN_DAYS_AGO  = new Date(Date.now() -   604_800_000).toISOString()
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000).toISOString()
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000).toISOString()
```

`build-dashboard.mjs` injects these after the last import line in every generated widget file.
Use the plain names (`SEVEN_DAYS_AGO`, `NOW`, etc.) in `dataHook` expressions — the script adds the declarations.

**Both `startTime` AND `endTime` are required for Insights calls.** Omitting `endTime` causes 500 errors.

---

## Widget Recipes

Pre-written `plan.json` widget configurations. Use these as-is for the most common requests.
For Insights RTM recipes, `dataHook` uses `useInsights<ResponseType>(key, params)`.
For SDK recipes, use AMBER path — write custom hook in `files{}` map using the capability entry above.

### ColumnDef format — never invent variations

`RecordsTable` uses `{ key, label, align? }` — NOT TanStack Table's `{ accessorKey, header }`:

```typescript
{ key: 'agentName', label: 'Agent' }
{ key: 'healthScore', label: 'Health Score', align: 'right' as const }
// align must be 'right' as const or 'left' as const — never numeric: true
```

### Insights RTM Recipes

**Recipe 1 — Agent Error Trend**
Triggers: "error rate", "errors over time", "error trend", "agent failures", "which agents are failing"
```json
{
  "template": "line-chart",
  "dataHook": "useInsights<{ data: Array<{ name: string; value: number; date: string }> }>('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "date",
  "yKey": "value",
  "deltaDir": "down-good"
}
```

**Recipe 2 — Invocation / Activity Timeline**
Triggers: "invocation volume", "how busy", "activity over time", "run count"
```json
{
  "template": "area-chart",
  "dataHook": "useInsights<{ data: Array<{ timeSlice: string; aguConsumption: number }> }>('agents.getConsumptionTimeline', { startTime: ONE_DAY_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "timeSlice",
  "yKey": "aguConsumption"
}
```

**Recipe 3 — Active Agents Count (KPI)**
Triggers: "active agents", "fleet size", "how many agents", "agent count"
```json
{
  "template": "kpi-card",
  "dataHook": "useInsights<{ data: { agents: Array<{ agentId: string }> } }>('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "valueExpression": "String((data as any)?.data?.agents?.length ?? '—')",
  "deltaDir": "neutral"
}
```

**Recipe 4 — Success Rate KPI**
Triggers: "success rate", "pass rate", "how well are agents doing"
```json
{
  "template": "kpi-card",
  "dataHook": "useInsights<{ data: { currentPeriodSummary: { successRate: number } } }>('agents.getSummaryV2', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "valueExpression": "(() => { const s = (data as any)?.data?.currentPeriodSummary; return s ? `${s.successRate.toFixed(1)}%` : '—' })()",
  "deltaDir": "up-good"
}
```

**Recipe 5 — Avg Duration KPI**
Triggers: "average duration", "how long do agents take", "avg execution time"
```json
{
  "template": "kpi-card",
  "dataHook": "useInsights<{ data: { currentPeriodSummary: { averageDurationSeconds: number } } }>('agents.getSummaryV2', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "valueExpression": "(() => { const secs = (data as any)?.data?.currentPeriodSummary?.averageDurationSeconds; return secs != null ? `${(secs / 60).toFixed(1)}m` : '—' })()",
  "deltaDir": "neutral"
}
```

**Recipe 6 — Top Erroring Agents (Bar)**
Triggers: "top erroring agents", "most failures", "error leaderboard"
```json
{
  "template": "bar-chart",
  "dataHook": "useInsights<{ totalErrors: number; data: Array<{ name: string; count: number }> }>('agents.getTopErroredAgents', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "name",
  "yKey": "count"
}
```

**Recipe 7 — P95 Latency Trend**
Triggers: "latency", "response time", "P95", "how fast are agents"
```json
{
  "template": "line-chart",
  "dataHook": "useInsights<{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }>('agents.getLatencyTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data?.filter((d: { name: string }) => d.name === 'P95') ?? []",
  "xKey": "date",
  "yKey": "value"
}
```

**Recipe 8 — Incident Type Distribution (Donut)**
Triggers: "incident types", "error vs escalation", "incident breakdown"
```json
{
  "template": "donut-chart",
  "dataHook": "useInsights<{ data: { errorCount: number; escalationCount: number; policyCount: number } }>('agents.getIncidentDistribution', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[{ name: 'Errors', value: (data as any)?.data?.errorCount ?? 0 }, { name: 'Escalations', value: (data as any)?.data?.escalationCount ?? 0 }, { name: 'Policy', value: (data as any)?.data?.policyCount ?? 0 }].filter(d => d.value > 0)",
  "dataKey": "value",
  "nameKey": "name"
}
```

**Recipe 9 — Agent Fleet Table**
Triggers: "agent list", "fleet overview", "all agents", "health scores"
```json
{
  "template": "data-table",
  "dataHook": "useInsights<{ data: { agents: Array<{ agentName: string; healthScore: number; unitsQuantity: number; lastRun: string }> } }>('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[...((data as any)?.data?.agents ?? [])].sort((a, b) => b.unitsQuantity - a.unitsQuantity)",
  "columns": "[{ key: 'agentName', label: 'Agent' }, { key: 'healthScore', label: 'Health' }, { key: 'unitsQuantity', label: 'Units Used', align: 'right' as const }, { key: 'lastRun', label: 'Last Run' }]"
}
```

**Recipe 10 — Top Agents by Consumption (Bar)**
Triggers: "top consumers", "highest usage", "who uses the most AGU"
```json
{
  "template": "bar-chart",
  "dataHook": "useInsights<{ data: { agents: Array<{ agentName: string; consumedQuantity: number }> } }>('agents.getConsumption', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data?.agents ?? []",
  "xKey": "agentName",
  "yKey": "consumedQuantity"
}
```

**Recipe 11 — Job Completion Timeline**
Triggers: "job trend", "completed jobs over time", "automation volume", "job history"
```json
{
  "template": "area-chart",
  "dataHook": "useInsights<{ data: Array<{ date: string; count: number; state: string }> }>('jobs.getCompletedTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data?.filter((d: { state: string }) => d.state === 'Successful') ?? []",
  "xKey": "date",
  "yKey": "count"
}
```

**Recipe 12 — Memory Usage Timeline (Traceview)**
Triggers: "memory usage", "agent memory", "in-memory traces", "context retention"
```json
{
  "template": "area-chart",
  "dataHook": "useInsights<{ data: Array<{ timeSlice: string; inMemoryCount: number; totalCount: number }> }>('traceview.getMemoryTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "timeSlice",
  "yKey": "inMemoryCount"
}
```

**Recipe 13 — P50 + P95 Latency (Multi-Line)**
Triggers: "latency with P50 and P95", "compare P50 vs P95", "latency percentiles"
```json
{
  "template": "multi-line-chart",
  "dataHook": "useInsights<{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }>('agents.getLatencyTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "date",
  "pivotExpression": "rawData.reduce((acc: Record<string, unknown>[], row: { name: string; value: number; date: string }) => { const existing = acc.find(r => r.date === row.date) as Record<string, unknown> | undefined; if (existing) { existing[row.name] = row.value } else acc.push({ date: row.date, [row.name]: row.value }); return acc }, [])",
  "series": "[{ key: 'P50', color: 'hsl(var(--chart-1))' }, { key: 'P95', color: 'hsl(var(--chart-2))' }]"
}
```

**Recipe 14 — Agent Error Rate KPI with Sparkline**
Triggers: "agent error rate trend", "errors with trend", "error KPI with sparkline"
```json
{
  "template": "kpi-with-sparkline",
  "dataHook": "useInsights<{ data: Array<{ name: string; value: number; date: string }> }>('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(() => { const byDate = ((data as any)?.data ?? []).reduce((acc: Record<string, number>, r: { date: string; value: number }) => { const day = r.date.slice(0, 10); acc[day] = (acc[day] ?? 0) + r.value; return acc }, {}); return Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b)).map(([date, errors]) => ({ date, errors })) })()",
  "valueExpression": "(() => { const allRows = (data as any)?.data ?? []; const byDate = allRows.reduce((acc: Record<string, number>, r: { date: string; value: number }) => { const day = r.date.slice(0, 10); acc[day] = (acc[day] ?? 0) + r.value; return acc }, {}); const sorted = Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b)); return sorted.length > 0 ? String(sorted[sorted.length - 1][1]) : '—' })()",
  "yKey": "errors",
  "deltaDir": "down-good"
}
```

**Recipe 15 — Top Agents Ranked Table**
Triggers: "top agents", "leaderboard", "agents ranked by errors"
```json
{
  "template": "ranked-table",
  "dataHook": "useInsights<{ data: Array<{ name: string; count: number }> }>('agents.getTopErroredAgents', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[...((data as any)?.data ?? [])].sort((a, b) => b.count - a.count)",
  "columns": "[{ key: 'name', label: 'Agent' }, { key: 'count', label: 'Errors', align: 'right' as const }]"
}
```

**Recipe 16 — Incident Type Progress Bars**
Triggers: "incident breakdown", "error vs escalation as bars", "incident proportions"
```json
{
  "template": "progress-bar-list",
  "dataHook": "useInsights<{ data: { errorCount: number; escalationCount: number; policyCount: number } }>('agents.getIncidentDistribution', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[{ label: 'Errors', value: (data as any)?.data?.errorCount ?? 0 }, { label: 'Escalations', value: (data as any)?.data?.escalationCount ?? 0 }, { label: 'Policy', value: (data as any)?.data?.policyCount ?? 0 }].filter(d => d.value > 0)"
}
```

### SDK Recipes

SDK capabilities use one of two paths based on whether a template exists:

**GREEN path (has template):** When a capability entry lists an `sdk-*` template in its **Templates**
field, use the `widgets[]` array in plan.json with the named template and the SDK-specific fields:
`sdkImport`, `sdkService`, `sdkCall`, `sdkResultType`. The build script handles code generation.

**AMBER path (no template):** When a capability entry has no matching `sdk-*` template, write a
custom TypeScript hook directly in the `files{}` map using the exact method signature and response
shape from the capability entry. Do NOT use `useInsights`. Use `const { sdk, isAuthenticated } = useAuth()`
and `new ServiceClass(sdk as never).method(params)`.

**SDK Recipe A — Running Jobs Count (AMBER path — no template exists for this computation)**
Triggers: "running jobs", "active jobs", "jobs in progress", "how many jobs are running"
```tsx
// Write to files['src/dashboard/widgets/RunningJobs.tsx']:
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity } from 'lucide-react'
import { Jobs } from '@uipath/uipath-typescript/jobs'
import { useAuth } from '@/hooks/useAuth'
import { DeltaBadge, ViewAllLink, LoadingState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function RunningJobs() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [count, setCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    const svc = new Jobs(sdk as never)
    svc.getAll({ state: 'Running,Pending' })
      .then((r: { items?: Array<{ state: string }> }) => { if (!cancelled) setCount(r.items?.length ?? 0) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])
  if (loading) return <LoadingState height="h-32" />
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/running-jobs')}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2"><Activity className="w-4 h-4 text-muted-foreground" /></div>
          <div><CardTitle className="text-base">Running Jobs</CardTitle><CardDescription>Active and pending jobs right now</CardDescription></div>
        </div>
        <ViewAllLink to="/running-jobs" />
      </CardHeader>
      <div className="px-6 pb-4 flex items-baseline gap-3">
        <span className="text-3xl font-semibold tabular-nums">{error ? '—' : String(count ?? '—')}</span>
        <DeltaBadge direction="neutral" text="" />
      </div>
    </Card>
  )
}
```

**SDK Recipe B — Queue Depth**
Triggers: "queue depth", "active queue items", "queued transactions"
Use `sdk-kpi-card` template (GREEN) with:
- `sdkImport: "@uipath/uipath-typescript/queues"`
- `sdkService: "QueueItems"`
- `sdkCall: "getAll({ status: 'New,InProgress' })"`
- `sdkResultType: "{ items?: Array<{ status: string; queueDefinitionName: string }> }"`
- `valueExpression: "String((r as any)?.items?.length ?? '—')"`
- `deltaDir: "neutral"`

**SDK Recipe C — Pending Action Center Tasks**
Triggers: "pending tasks", "action center backlog", "human tasks"
Use `sdk-kpi-card` template (GREEN) with:
- `sdkImport: "@uipath/uipath-typescript/tasks"`
- `sdkService: "Tasks"`
- `sdkCall: "getAll({ status: 'Pending,Unassigned' })"`
- `sdkResultType: "{ items?: Array<{ status: string; title: string }> }"`
- `valueExpression: "String((r as any)?.items?.length ?? '—')"`
- `deltaDir: "neutral"`

**SDK Recipe D — Process Inventory Table (GREEN path — use `sdk-data-table` template)**
Triggers: "what processes are deployed", "automation inventory", "process list"
Use `sdk-data-table` template (add to `widgets[]` array) with:
- `sdkImport: "@uipath/uipath-typescript/processes"`
- `sdkService: "Processes"`
- `sdkCall: "getAll()"`
- `sdkResultType: "{ items?: Array<{ name: string; description: string; version: string }> }"`
- `dataSelector: "(r as any)?.items ?? []"`
- `columns: "[{ key: 'name', label: 'Process' }, { key: 'description', label: 'Description' }, { key: 'version', label: 'Version' }]"`

---

## Tie-Breaking Rules

- "job count today" → SDK `Jobs.getAll`; "job count over 7 days" → `jobs.getCompletedTimeline`
- "queue depth" → SDK `QueueItems.getAll`; "queue throughput trend" → no endpoint, stay SDK with disclaimer
- P50/P95 latency → `agents.getLatencyTimeline` (fleet) or `traceview.getLatencyTimeline` (trace-level)
- `governance.getPolicySummary` requires a `policy` UUID body field. If user asks for policy data
  without specifying a policy, ask: "Which policy would you like to report on? Please provide the
  policy name or UUID." If user cannot provide one, suggest `governance.getOperationSummary` instead
  (broader operation volume — no policy filter required).
- "invocation volume" → `agents.getConsumptionTimeline` (activity proxy — say so in plan)
- `getSummaryV2` is AGGREGATE ONLY — never use for line/area/bar time-series charts
- "real-time" → SDK operational state; "over time" / "trend" → Insights RTM analytics
