# Tier Resolution — Classifying Metrics

Every metric in `intent.json` has a `tier` field you must set during Phase 2.

## Tier Decision Tree

```
User asks for metric
  ↓
T0 — Check the Hard Refuse list first
  → Does the metric match? → YES: refuse only that metric, offer alternative
  ↓
T1 — Catalog check
  → Exact name or alias match in capability-registry.json?
    → YES: tier = "T1"
  ↓
T2 — Parametric check
  → Known SDK service + user-controlled filter value?
    → YES: tier = "T2", include params object
  ↓
T3 — Custom
  → tier = "T3", write fnBody
```

---

## T0 — Hard Refuse

**Refuse ONLY the specific metric — never the whole dashboard.** Always offer the closest alternative and build the remaining widgets normally.

| User asks for | Why it's impossible | Offer instead |
|--------------|---------------------|---------------|
| Agent cost in dollars | Platform tracks AGU units, not currency | `invocation-volume` for AGU consumption |
| CPU or memory per agent | Not exposed by any API | `agent-latency` for fleet-level latency trends |
| Who triggered a job | Job records carry no end-user identity | T3-SDK: `new Jobs(sdk as never).getAll({})` grouped by `processName` |
| Data from multiple tenants | Dashboards are scoped to one tenant only | Multi-widget view within the same tenant |
| SLA breach percentage | Platform has no SLA metadata | T3-SDK: `new Jobs(sdk as never).getAll({ filter: "State eq 'Faulted'" })` to compute failure rate |
| Error message text or stack traces | No aggregation endpoint exists | `agent-errors` for error counts |
| Governance policy summary | Requires a specific policy UUID — the build cannot infer it | Ask the user for the UUID, then use T3-SDK with the `Governance` service |

---

## T1 — Known catalog metrics

These are pre-built. The build script generates the entire widget from the metric name — no additional configuration needed.

| Metric name | What it shows |
|-------------|--------------|
| `agent-errors` | Daily error counts as a trend line |
| `invocation-volume` | AGU consumption over time |
| `top-failing-agents` | Agents ranked by error count |
| `active-agents-kpi` | Count of agents with at least one run |
| `agent-latency` | P50 and P95 execution time side by side |

---

## T2 — Parametric metrics

The build script generates a filtered SDK query from the metric name and the filter values the user provides.

| Metric name | What it does | Params |
|-------------|-------------|--------|
| `jobs-duration-threshold` | Jobs running longer than N minutes | `{ threshold: number, direction: "gt" }` |
| `jobs-by-state` | Jobs in a specific execution state | `{ value: "Faulted" \| "Running" \| "Stopped" \| "Successful" }` |
| `tasks-by-status` | Action Center tasks filtered by status | `{ value: "Pending" \| "Completed" \| "Unassigned" }` |
| `cases-running-above` | Maestro processes with high active case counts | `{ threshold: number, direction: "gt" }` |

```json
// Numeric filter example
{ "name": "jobs-duration-threshold", "tier": "T2", "params": { "threshold": 30, "direction": "gt" } }

// String filter example
{ "name": "jobs-by-state", "tier": "T2", "params": { "value": "Faulted" } }
```

---

## T3 — Custom metrics

Use when the metric doesn't match T1 or T2. The agent writes an async function body (`fnBody`) that fetches and shapes the data.

`displayAs` must be one of: `kpi-card`, `ranked-table`, `data-table`.

### Example — ranked table from Insights

```json
{
  "name": "incident-distribution",
  "tier": "T3",
  "title": "Incident Distribution",
  "description": "Types of agent incidents",
  "displayAs": "ranked-table",
  "columns": "[{key:\"name\",label:\"Type\"},{key:\"count\",label:\"Count\",align:\"right\" as const}]",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nconst result = await svc.getIncidentDistribution(THIRTY_DAYS_AGO, NOW)\nreturn result?.data ?? []"
}
```

### Example — KPI card

```json
{
  "name": "total-active-agents",
  "tier": "T3",
  "title": "Total Active Agents",
  "displayAs": "kpi-card",
  "valueField": "count",
  "valueLabel": "active agents",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nconst result = await svc.getAll(THIRTY_DAYS_AGO, NOW)\nreturn [{ count: result?.items?.length ?? 0 }]"
}
```

### fnBody rules

- Must return `Promise<Array<Record<string, unknown>>>`
- Use dynamic import: `const { ServiceClass } = await import('@uipath/uipath-typescript/...')`
- Use constructor injection: `new ServiceClass(sdk as never)`
- `sdk` and `getToken` are available as parameters — do not import `useAuth`
- No JSX, no static top-level imports
- Time constants (`Date` objects) are injected at the top of the generated file: `NOW`, `ONE_DAY_AGO`, `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, `NINETY_DAYS_AGO`. Use them directly in fnBody.

---

## SDK service reference

| Service | Import | Key response fields |
|---------|--------|---------------------|
| `Agents` | `@uipath/uipath-typescript/agents` | 14 Insights methods — errors, latency, consumption, incidents |
| `Governance` | `@uipath/uipath-typescript/governance` | `getPolicyTraces()`, `getOperationSummary()` |
| `Memory` | `@uipath/uipath-typescript/memory` | `getTimeline()`, `getCallsTimeline()`, `getTopSpaces()` |
| `Jobs` | `@uipath/uipath-typescript/jobs` | `key`, `state`, `processName`, `startTime`, `endTime` |
| `Queues` | `@uipath/uipath-typescript/queues` | `id`, `name`, `maxRetries`, `acceptsRejectedItems` |
| `Assets` | `@uipath/uipath-typescript/assets` | `id`, `name`, `hasValue`, `value` |
| `Tasks` | `@uipath/uipath-typescript/tasks` | `id`, `title`, `priority`, `status`, `assignedTo` |
| `Processes` | `@uipath/uipath-typescript/processes` | `id`, `name`, `key`, `processType` |
| `Entities` | `@uipath/uipath-typescript/entities` | `id`, `name`, `displayName`, `entityType` |
| `Cases` | `@uipath/uipath-typescript/cases` | `processKey`, `runningCount`, `completedCount` |

**Insights methods take two positional `Date` arguments**, not an options object:
```typescript
// Correct
new Agents(sdk as never).getErrorsTimeline(THIRTY_DAYS_AGO, NOW)

// Wrong — options syntax does not match the SDK signature
new Agents(sdk as never).getErrors({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
```

**Paginated responses** — normalise with:
```typescript
const items = result?.items ?? result?.value ?? []
```

**Duration** is not a response field on `Jobs`. Compute it:
```typescript
const durationMs = new Date(j.endTime).getTime() - new Date(j.startTime).getTime()
```

**Constructor injection** requires the `as never` cast:
```typescript
// ✓ Correct
const svc = new Jobs(sdk as never)

// ✗ Wrong — TypeScript error without the cast
const svc = new Jobs(sdk)

// ✗ Wrong — sdk.jobs doesn't exist at runtime
sdk.jobs.getAll()
```
