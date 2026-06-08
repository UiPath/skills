# Tier Resolution — Classifying Metrics

Every metric in `intent.json` has a `tier` field you must set during Phase 3.

## Tier Decision Tree

```
User asks for metric
  → Check hard-refuse list below
    → If match: refuse metric (not whole dashboard), offer alternative
  → Search T1 catalog: exact metric name or alias match?
    → YES: tier = "T1"
  → Search T2 catalog: maps to known SDK service + custom filter?
    → YES: tier = "T2", provide compact params object
  → Else: tier = "T3", write fnBody
```

## Tier 1 — Known catalog metrics

| Metric name | What it shows |
|-------------|--------------|
| `agent-errors` | Daily error counts as trend line |
| `invocation-volume` | AGU consumption over time as area chart (uses getConsumptionTimeline — xKey: timeSlice, yKey: aguConsumption) |
| `top-failing-agents` | Agents ranked by error count |
| `active-agents-kpi` | Count of agents with at least one run |
| `agent-latency` | P50/P95 latency over time |
| `job-failures` | Processes ranked by failure count |
| `job-completion-trend` | Completed jobs per day |

## Tier 2 — Parametric metrics

| Metric name | What it does | Required params |
|-------------|-------------|----------------|
| `queue-failure-threshold` | Queues filtered by failureCount | `{ threshold: number, direction: "gt" }` |
| `jobs-duration-threshold` | Jobs filtered by duration | `{ threshold: number, direction: "gt" }` |

T2 params format:
```json
{ "name": "queue-failure-threshold", "tier": "T2", "params": { "threshold": 20, "direction": "gt" } }
```

## Tier 3 — Custom metrics

Use when the metric doesn't match T1 or T2. Two sub-paths:

### T3-Insights: custom Insights RTM endpoint

Any `useInsights` endpoint not in the T1 catalog. Provide the namespace, method, and template:

```json
{
  "name": "incident-distribution",
  "tier": "T3",
  "title": "Incident Distribution",
  "namespace": "agents",
  "method": "getIncidentDistribution",
  "template": "donut-chart",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "name",
  "yKey": "value",
  "description": "Incident types as a breakdown"
}
```

### T3-SDK: custom SDK query

For data not available via Insights RTM. Provide an async function body using `sdk.*`:

```json
{
  "name": "faulted-queues",
  "tier": "T3",
  "title": "Faulted Queue Items",
  "displayAs": "ranked-table",
  "columns": "[{key:\"name\",label:\"Queue\"},{key:\"count\",label:\"Faulted\",align:\"right\" as const}]",
  "fnBody": "const svc = new Queues(sdk as never)\nconst r = await svc.getAll({ state: 'Faulted' })\nreturn (r?.items ?? []).map((q: any) => ({ name: q.name ?? '', count: q.transactionsCount ?? 0 }))"
}
```

T3-SDK rules for fnBody:
- Must return `Promise<Array<Record<string, unknown>>>`
- Use constructor injection: `new ServiceClass(sdk as never)` — never `sdk.serviceName.method()`
- ServiceClass names: Queues, Jobs, Assets, Tasks, Processes, Entities (import from @uipath/uipath-typescript/* as needed — shell provides the sdk object, not imports)
- Use `await` for all async operations
- No `import` statements (shell provides all imports)
- No JSX

## Hard Refuse List

Refuse ONLY the specific metric. Offer the dashboard with remaining metrics.

| User asks for | Reason | Suggest instead |
|--------------|--------|----------------|
| Agent cost in dollars | Platform tracks AGU, not currency | `invocation-volume` for AGU consumption |
| CPU/memory per agent | Not exposed by any API | `agent-latency` for fleet-level latency |
| Who triggered a job | Job records carry no end-user identity | `job-completion-trend` by process |
| Cross-tenant data | Single-tenant scope only | Multi-widget view within one tenant |
| SLA breach % | No SLA metadata in platform | Success rate from `job-completion-trend` |
| Error message text | No aggregation endpoint | `agent-errors` for counts |
| Governance policy summary | Requires a policy UUID the build script cannot infer | Ask user for the UUID, then use T3-Insights: `{ namespace: "governance", method: "getPolicySummary", ... }` with the UUID in the request |
