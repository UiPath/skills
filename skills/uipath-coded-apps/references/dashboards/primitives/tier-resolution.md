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

## SDK validation — do this before writing the plan

For every requested metric, before writing it into the plan:

1. Check T0 Hard Refuse list — if it matches, refuse that metric inline
2. Check T1/T2 catalog — if name or alias matches, use the registry hint
3. For T3 (custom) metrics: **find a method in the SDK service reference below** that can return the needed data. If no method maps to it, T0 refuse it — do not invent methods

> If a metric is feasible but requires a method that may not be in the installed SDK version (e.g. a newly released Insights endpoint), include it in the plan with a note: "relies on `Agents.methodName` — will verify after install." `tsc` catches a missing method before build.

After the plan is confirmed, **Phase 3.5 cross-checks each `fnBody` against the example response + semantics notes in `references/sdk/*.md`** — the example shows real field *values*, not just that a field exists. (E.g. an agent job is `packageType === 'Agent'` / OData `ProcessType eq 'Agent'` — `sourceType` is the trigger origin, not the agent discriminator.)

---

## Writing fnBody

The agent reads the SDK service reference (this file, loaded in the parallel blast) to find the right service and method. The `fnBody` must:

- Return `Promise<Array<Record<string, unknown>>>`
- Use dynamic import: `const { ServiceClass } = await import('@uipath/uipath-typescript/...')`
- Use constructor injection: `new ServiceClass(sdk as never)`
- Return a flat array — the build script passes it directly to the chart/table
- **Read methods ONLY.** Dashboards display data; they never mutate. Allowed: `getAll`, `getById`, `getAllRecords`, `queryRecordsById`, `getIncidents`. Never call `create`, `complete`, `assign`, `start`, `stop`, `resume`, `restart`, `insert*`, `update*`, `delete*`, `upload*` — even though the shared `sdk/*.md` references document them for the app-building modes.

**Presentation matters as much as the query.** A chart with the wrong headline or an empty subtitle reads as broken. For every chart metric set `headlineMode` + `deltaPolarity` + `subtitle`, and give it a record-grain `detailFnBody` + `detailColumns` so the drill-down shows real records, not the chart's buckets. For ratios (error rate, success rate) use `displayAs: "rate-chart"` with `rateNum`/`rateDen`. See `plugins/build/impl.md § Presentation fields` for the full schema and an example.

**Don't add your own request caching.** The scaffold wraps `fetch` (`src/lib/fetch-cache.ts`) so identical GET requests across all widgets share one network call and are cached ~15s — this prevents 429s when many widgets mount at once. Just call the SDK normally; results may be up to 15s stale, which is fine for a dashboard.

Time constants (all `Date` objects, injected by build script):
`NOW`, `ONE_DAY_AGO`, `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, `NINETY_DAYS_AGO`

---

## T1 — Catalog metrics with display hints

The registry entry describes the metric and the expected SDK call. Use it as your guide, then write the correct `fnBody` from the SDK documentation.

| Metric name | What it shows | Registry template | SDK hint |
|-------------|--------------|-------------------|----------|
| ~~`agent-errors`~~ | ~~Daily error counts~~ | — | ~~`Agents.getErrorsTimeline`~~ — unavailable (PR #438) |
| ~~`invocation-volume`~~ | ~~AGU consumption~~ | — | ~~`Agents.getConsumptionTimeline`~~ — unavailable (PR #438) |
| ~~`top-failing-agents`~~ | ~~Agents ranked by errors~~ | — | ~~`Agents.getTopErroredAgents`~~ — unavailable (PR #438) |
| ~~`active-agents-kpi`~~ | ~~Count of active agents~~ | — | ~~`Agents.getAll`~~ — unavailable (PR #438) |
| ~~`agent-latency`~~ | ~~P50/P95 execution time~~ | — | ~~`Agents.getLatencyTimeline`~~ — unavailable (PR #438) |
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

Full method signatures, response types, and field names live in `references/sdk/` (loaded in the parallel blast). Use those files as the source of truth — do not rely on memory.

| Domain | Reference file | Key service classes |
|--------|---------------|---------------------|
| ~~Agents / Insights RTM~~ | ~~`sdk/agents.md`~~ | ~~`Agents`~~ — not yet available (PR #438 pending) |
| Jobs, Queues, Processes, Assets | `sdk/orchestrator.md` *(from skill root)* | `Jobs`, `Queues`, `Processes`, `Assets` |
| Tasks | `sdk/action-center.md` *(from skill root)* | `Tasks` |
| Cases, Process Instances | `sdk/maestro.md` *(from skill root)* | `Cases`, `CaseInstances` |
| Data entities | `sdk/data-fabric.md` *(from skill root)* | `Entities` |

`sdk/orchestrator.md` is **always loaded** in the parallel blast. Load `sdk/action-center.md` or `sdk/maestro.md` only when the user's request involves tasks or cases. When PR #438 ships, uncomment `sdk/agents.md` in `CAPABILITY.md` and remove the strikethrough above.

**Non-Insights services:** access items via `result?.items ?? result?.value ?? []`
