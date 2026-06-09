# Tier Resolution — Classifying Metrics

Every metric in `intent.json` requires a `fnBody` that you write based on the SDK documentation. The tier tells the build script where to find display hints — it does not drive code generation.

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
           You still write the fnBody from SDK docs
  ↓
T2 — Parametric check
  → Known metric with user-supplied filter?
    → YES: registry provides hints + you incorporate params into fnBody
  ↓
T3 — Custom
  → Not in catalog: you provide everything (fnBody + displayAs + hints)
```

**Every tier requires `fnBody`.** The registry never generates code — it only describes what template and keys to use.

---

## Writing fnBody

The agent reads SDK documentation (loaded in the parallel blast) to find the right service and method. The `fnBody` must:

- Return `Promise<Array<Record<string, unknown>>>`
- Use dynamic import: `const { ServiceClass } = await import('@uipath/uipath-typescript/...')`
- Use constructor injection: `new ServiceClass(sdk as never)`
- Return a flat array — the build script passes it directly to the chart/table

Time constants (all `Date` objects, injected by build script):
`NOW`, `ONE_DAY_AGO`, `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, `NINETY_DAYS_AGO`

---

## T1 — Catalog metrics with display hints

The registry entry describes the metric and the expected SDK call. Use it as your guide, then write the correct `fnBody` from the SDK documentation.

| Metric name | What it shows | Registry template | SDK hint |
|-------------|--------------|-------------------|----------|
| `agent-errors` | Daily error counts | `line-chart` | `Agents.getErrorsTimeline(start, end)` → `{ data: [{date, value}] }` |
| `invocation-volume` | AGU consumption over time | `area-chart` | `Agents.getConsumptionTimeline(start, end)` → `{ data: [{timeSlice, aguConsumption}] }` |
| `top-failing-agents` | Agents ranked by errors | `ranked-table` | `Agents.getTopErroredAgents(start, end)` → `{ data: [{name, count}] }` |
| `active-agents-kpi` | Count of active agents | `kpi-card` | `Agents.getAll(start, end)` → `{ items: AgentListItem[] }` |
| `agent-latency` | P50/P95 execution time | `multi-line-chart` | `Agents.getLatencyTimeline(start, end)` → `{ data: [{name:'P50'\|'P95', value, date}] }` |
| `job-failures` | Faulted jobs | `data-table` | `new Jobs(sdk).getAll({ filter: "State eq 'Faulted'" })` → `{ items: [{processName, state, createdTime}] }` |
| `job-completion-trend` | Completed jobs | `data-table` | `new Jobs(sdk).getAll({ filter: "State eq 'Successful'" })` → `{ items: [{processName, state, endTime}] }` |

### T1 intent format

```json
{
  "name": "agent-errors",
  "tier": "T1",
  "title": "Agent Error Rate",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nreturn (await svc.getErrorsTimeline(THIRTY_DAYS_AGO, NOW))?.data ?? []"
}
```

The registry fills in: `template: "line-chart"`, `xKey: "date"`, `yKey: "value"`, `title` default, `icon`, `deltaDir`.
You can override any of these in the intent.

### T1 kpi-card example (active agents)

```json
{
  "name": "active-agents-kpi",
  "tier": "T1",
  "title": "Active Agents",
  "displayAs": "kpi-card",
  "valueField": "count",
  "valueLabel": "active agents",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nconst result = await svc.getAll(THIRTY_DAYS_AGO, NOW)\nreturn [{ count: result?.items?.length ?? 0 }]"
}
```

---

## T2 — Parametric metrics (catalog with user filter)

The agent incorporates the user's filter parameters directly into the `fnBody`.

| Metric name | What it does | Params |
|-------------|-------------|--------|
| `jobs-duration-threshold` | Jobs running longer than N minutes | `{ threshold: number, direction: "gt" }` |
| `jobs-by-state` | Jobs in a specific state | `{ value: "Faulted" \| "Running" \| "Stopped" }` |
| `tasks-by-status` | Tasks by status | `{ value: "Pending" \| "Completed" }` |
| `cases-running-above` | Cases exceeding threshold | `{ threshold: number, direction: "gt" }` |

### T2 intent format

```json
{
  "name": "jobs-by-state",
  "tier": "T2",
  "title": "Faulted Jobs",
  "params": { "value": "Faulted" },
  "displayAs": "data-table",
  "columns": "[{key:\"processName\",label:\"Process\"},{key:\"state\",label:\"State\"},{key:\"createdTime\",label:\"Started\"}]",
  "fnBody": "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nconst svc = new Jobs(sdk as never)\nreturn (await svc.getAll({ filter: \"State eq 'Faulted'\" }))?.items ?? []"
}
```

The `params` field is documentation — the actual filter logic is in `fnBody`.

---

## T3 — Custom metrics

For any metric not in the catalog. You provide all display config and write the `fnBody` entirely from SDK documentation.

### T3 area chart from SDK data

```json
{
  "name": "faulted-jobs-trend",
  "tier": "T3",
  "title": "Faulted Jobs Over Time",
  "displayAs": "area-chart",
  "xKey": "date",
  "yKey": "count",
  "fnBody": "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nconst svc = new Jobs(sdk as never)\nconst result = await svc.getAll({ filter: \"State eq 'Faulted'\" })\nconst byDate: Record<string, number> = {}\nfor (const j of result?.items ?? []) {\n  const date = String(j.createdTime).slice(0, 10)\n  byDate[date] = (byDate[date] ?? 0) + 1\n}\nreturn Object.entries(byDate).sort().map(([date, count]) => ({ date, count }))"
}
```

### T3 ranked table from Insights

```json
{
  "name": "incident-distribution",
  "tier": "T3",
  "title": "Incident Distribution",
  "displayAs": "ranked-table",
  "columns": "[{key:\"name\",label:\"Type\"},{key:\"count\",label:\"Count\",align:\"right\" as const}]",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nconst result = await svc.getIncidentDistribution(THIRTY_DAYS_AGO, NOW)\nreturn result?.data ?? []"
}
```

### T3 kpi-card

```json
{
  "name": "running-jobs-count",
  "tier": "T3",
  "title": "Running Jobs",
  "displayAs": "kpi-card",
  "valueField": "count",
  "valueLabel": "running jobs",
  "fnBody": "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nconst svc = new Jobs(sdk as never)\nconst result = await svc.getAll({ filter: \"State eq 'Running'\" })\nreturn [{ count: result?.items?.length ?? 0 }]"
}
```

---

## T0 — Hard Refuse

**Refuse ONLY the specific metric — not the whole dashboard.** Always offer an alternative.

| User asks for | Why impossible | Suggest instead |
|--------------|----------------|-----------------|
| Agent cost in dollars | Platform tracks AGU, not currency | `invocation-volume` for AGU consumption |
| CPU/memory per agent | Not exposed by any API | `agent-latency` for fleet-level latency |
| Who triggered a job | Job records have no end-user identity | `job-completion-trend` grouped by process |
| Cross-tenant data | Single-tenant scope only | Multi-widget single-tenant view |
| SLA breach % | No SLA metadata in platform | Success rate from job completions |
| Error text / stack traces | No aggregation endpoint | `agent-errors` for error counts |
| Governance policy summary | Requires a policy UUID | Ask user for UUID, use T3 with `Governance` service |

---

## SDK service reference

**Insights methods take positional Date params:**
```typescript
new Agents(sdk as never).getErrorsTimeline(THIRTY_DAYS_AGO, NOW)  // ✓
new Agents(sdk as never).getErrors({ startTime: ..., endTime: ... })  // ✗ wrong signature
```

| Service | Import | Key response fields |
|---------|--------|---------------------|
| `Agents` | `@uipath/uipath-typescript/agents` | Insights: getErrorsTimeline, getConsumptionTimeline, getLatencyTimeline, getTopErroredAgents, getAll, getIncidentDistribution |
| `Jobs` | `@uipath/uipath-typescript/jobs` | `key`, `state`, `processName`, `startTime`, `endTime`, `createdTime` |
| `Queues` | `@uipath/uipath-typescript/queues` | `id`, `name`, `maxRetries`, `acceptsRejectedItems` |
| `Tasks` | `@uipath/uipath-typescript/tasks` | `id`, `title`, `priority`, `status`, `assignedTo`, `createdTime` |
| `Processes` | `@uipath/uipath-typescript/processes` | `id`, `name`, `key`, `processType` |
| `Cases` | `@uipath/uipath-typescript/cases` | `processKey`, `runningCount`, `completedCount` |
| `Entities` | `@uipath/uipath-typescript/entities` | `id`, `name`, `displayName`, `entityType` |
| `Governance` | `@uipath/uipath-typescript/governance` | `getPolicyTraces()`, `getOperationSummary()` |

**Non-Insights services:** access items via `result?.items ?? result?.value ?? []`

**Duration** is not a direct field on Jobs. Compute it:
```typescript
const ms = new Date(j.endTime).getTime() - new Date(j.startTime).getTime()
```
