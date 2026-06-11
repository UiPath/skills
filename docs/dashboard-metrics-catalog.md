# Dashboard Metrics Catalog

Everything the `uipath-coded-apps` dashboard capability can track, by tier — with sample prompts.

> Grounded in `@uipath/uipath-typescript` **1.4.0** and `capability-registry.json`. Time windows: `1d` / `7d` / `30d` / `90d` (Agent Memory defaults to last 24h when unspecified). Governance metrics require an elevated (org-admin) caller.

## How tiers work

| Tier | What it means | You get |
|------|---------------|---------|
| **T1** | Metric is in the catalog — matched by name/alias | Pre-tuned widget, icon, headline aggregate, delta polarity, formatted columns |
| **T2** | Catalog metric + your filter parameter | Same, with your threshold/state/status plugged in |
| **T3** | Custom — any read API + a transform | Any widget type; agent derives the query from SDK references |
| **T0** | Not derivable from any API | Refused inline with an alternative offered |

---

## T1 — Catalog metrics

### Agents (Insights RTM)

| Metric | Widget | Shows | Say things like |
|--------|--------|-------|-----------------|
| `active-agents-kpi` | KPI card | Count of agents active in the window | "active agents", "how many agents" |
| `agent-consumption` | Ranked table | Agents ranked by AGU/PLTU consumed | "AGU consumption", "most expensive agents", "units consumed" |
| `agent-health` | Ranked table | Agents by health score (0–100, worst first), last incident, last run | "agent health", "unhealthy agents", "health score" |

### Agent Memory

| Metric | Widget | Shows | Say things like |
|--------|--------|-------|-----------------|
| `agent-memory-timeline` | Area chart | Memory entries over time (total / in-memory / enabled) | "agent memory", "memory state over time" |
| `memory-calls-trend` | Area chart | Memory access volume per bucket | "memory calls", "memory access trend" |
| `top-memory-spaces` | Ranked table | Memory spaces by entry count | "top memory spaces", "largest memory spaces" |

### Governance *(org-admin)*

| Metric | Widget | Shows | Say things like |
|--------|--------|-------|-----------------|
| `policy-denials` | Data table | Actions blocked by policies — policy, actor, resource, when | "policy denials", "blocked actions", "policy violations" |
| `governance-verdicts` | Donut | Allow / Deny / Simulated enforcement breakdown | "governance summary", "allow deny breakdown" |

### Jobs / RPA

| Metric | Widget | Shows | Say things like |
|--------|--------|-------|-----------------|
| `job-failures` | Data table | Currently faulted jobs | "faulted jobs", "failed jobs" |
| `job-completion-trend` | Data table | Recently completed jobs | "completed jobs", "RPA throughput" |

---

## T2 — Parametric metrics (your filter, plugged in)

| Metric | Param | Sample phrasing |
|--------|-------|-----------------|
| `jobs-duration-threshold` | minutes threshold | "jobs running longer than 30 minutes" |
| `jobs-by-state` | `Running` / `Faulted` / `Stopped` / `Successful` | "all running jobs", "stopped jobs" |
| `tasks-by-status` | `Pending` / `Completed` / `Unassigned` | "pending Action Center tasks" |
| `cases-running-above` | running-count threshold | "Maestro cases with more than 20 running" |

---

## T3 — Custom metrics (composable)

Any **read** method + a JS transform, rendered as any widget type. Available data sources:

| Service | Read surface | Example T3 metrics |
|---------|-------------|--------------------|
| **Jobs** | `getAll` + OData filter (`State`, `ProcessType`, …) | Faulted-jobs trend by day; agent-only run volume (`ProcessType eq 'Agent'`); failure-rate % (rate-chart); jobs grouped by process; duration percentiles computed from `endTime − startTime` |
| **Agents** | `getAll(start, end, { orderBy })` | Agents with health < N; consumption grouped by folder; agents idle since a date (`lastRun`) |
| **AgentMemory** | `getTimeline` / `getCallsTimeline` / `getTopSpaces` | Enabled-vs-disabled memory split; per-agent memory scoped by `agentId`/`folderKeys`; Debug-vs-Runtime via `executionType` |
| **Governance** | `getPolicyTraces` (filters: result, policy, actor, resource) / `getOperationSummary` | Denials by actor / by resource type / by policy; org-wide view via `fullOrganization: true`; deny-rate % (deniedCount ÷ totalEvaluations) |
| **Tasks** | `getAll` + OData filter | Tasks by priority; overdue/unassigned counts; agent-raised tasks (`taskSource`) |
| **Cases / Maestro** | `Cases.getAll`, `MaestroProcesses.getAll` (pre-aggregated counts), `ProcessIncidents.getAll` | Process health table (running/faulted/completed per process); incident summaries |
| **Data Fabric** | `Entities.getAllRecords`, `queryRecordsById` (server-side `aggregates` + `groupBy`) | Records by status donut; counts per category; any entity-backed KPI |
| **Queues / Processes / Assets** | `getAll` | Queue definitions table; deployed package catalog; asset inventory |

Widget types for any tier: `kpi-card`, `data-table`, `ranked-table`, `area-chart`, `line-chart`, `bar-chart`, `donut-chart`, `multi-line-chart`, `rate-chart` (numerator ÷ denominator → % axis, pp delta).

Every chart additionally gets: headline aggregate (`sum`/`avg`/`latest`/`count`/`max`/`min`), computed delta badge, subtitle, and a record-grain drill-down detail view with formatted/colored columns (`number`, `percent`, `duration`, `timeAgo`; `goodHigh`/`goodLow` coloring).

---

## T0 — Refused (with the alternative offered)

| Asked for | Why refused | Offered instead |
|-----------|-------------|-----------------|
| Agent error / latency / consumption **timelines**, "P95 latency", "top failing agents" | SDK 1.4.0 Agents service has only `getAll` — no time-series endpoints | `agent-health`, `agent-consumption`, or a Jobs-based agent trend |
| Cost in dollars | Platform tracks AGU/PLTU units, not currency | `agent-consumption` |
| CPU/RAM per agent | Not exposed by any API | `agent-health`; `agent-memory-timeline` if the Memory feature was meant |
| Who triggered a job | Job records carry no end-user identity | `policy-denials` includes `actorIdentityId` for governance events |
| Cross-tenant data | Single-tenant scope | Exception: Governance supports `fullOrganization: true` (org admin) |
| SLA breach % | No SLA metadata | Success rate from job completions |
| Error text / stack traces | No aggregation endpoint | Faulted-jobs table — rows carry `errorCode` / `jobError` |
| Queue failure counts | `QueueGetResponse` has no failure field | Faulted jobs grouped by process |

---

## Sample prompts

Each builds in one shot; tier breakdown shown for reference.

1. **Agent memory deep-dive**
   > "Build a dashboard for agent memory: memory entries over time, memory access volume for the last 7 days, and the top 10 memory spaces"

   → `agent-memory-timeline` (T1) + `memory-calls-trend` (T1) + `top-memory-spaces` (T1)

2. **Cross-domain ops overview**
   > "Create an operations overview: active agents, faulted jobs, pending Action Center tasks, and completed jobs"

   → `active-agents-kpi` (T1) + `job-failures` (T1) + `tasks-by-status` (T2: Pending) + `job-completion-trend` (T1)

3. **CoE admin dashboard**
   > "CoE dashboard: agents ranked by AGU consumption, agent health worst-first, governance verdicts donut, and policy denials this week"

   → `agent-consumption` (T1) + `agent-health` (T1) + `governance-verdicts` (T1) + `policy-denials` (T1)

4. **Agent reliability via Jobs**
   > "Agent reliability: agent job failure rate as a percentage trend over 30 days, agent run volume by day, and a table of faulted agent jobs"

   → T3 rate-chart (faulted ÷ total, `ProcessType eq 'Agent'`) + T3 area chart + T3 data table

5. **Maestro process health**
   > "Maestro health: cases with more than 15 running instances, a process health table with running/faulted/completed counts, and incident summaries"

   → `cases-running-above` (T2: 15) + T3 (MaestroProcesses pre-aggregated counts) + T3 (ProcessIncidents)

6. **Data Fabric entity tracking**
   > "Track my SupportTickets entity: tickets by status as a donut, total open tickets as a KPI, and a table of the newest tickets"

   → T3 (queryRecordsById `groupBy` status) + T3 KPI (server-side count) + T3 data table

7. **Compliance / governance audit**
   > "Org-wide compliance view: governance denials across all tenants this month, denials grouped by resource type, and the overall deny rate"

   → T3 (`getPolicyTraces` with `fullOrganization: true`) + T3 ranked table + T3 KPI (deniedCount ÷ totalEvaluations)

8. **Long-running work monitor**
   > "Show jobs running longer than 45 minutes, all currently running jobs, and completed throughput for the week"

   → `jobs-duration-threshold` (T2: 45) + `jobs-by-state` (T2: Running) + `job-completion-trend` (T1)

> A prompt that includes an unbuildable metric (e.g. "agent latency trend") doesn't fail the dashboard — that one widget is refused inline in the plan with the closest buildable alternative offered.
