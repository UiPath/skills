# Insights Capability Catalog

Source: "Insights APIs to use for dashboard as code" (internal Confluence)
Base URL pattern: `${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}/insightsrtm_/<namespace>/<endpoint>`
Environment values for VITE_UIPATH_BASE_URL:
  alpha:   https://alpha.api.uipath.com
  staging: https://staging.api.uipath.com
  prod:    https://api.uipath.com
All calls: POST JSON body. All require `tenantId` (UUID). Add `startTime`/`endTime` (ISO 8601) per endpoint.

---

## Agents namespace — POST /Agents/...

| Method                         | Route suffix                       | Key metrics                                    | Shape       |
|--------------------------------|------------------------------------|------------------------------------------------|-------------|
| `agents.getSummaryV2`          | Agents/summaryV2                   | Success rate, failure rate, avg duration, Δ    | kpi, table  |
| `agents.getErrors`             | Agents/errors                      | Error count over time per agent                | area, line  |
| `agents.getTopErroredAgents`   | Agents/topErroredAgents            | Top-N erroring agents leaderboard              | bar, table  |
| `agents.getIncidents`          | Agents/incidents                   | Paged incident table                           | table       |
| `agents.getIncidentDistribution` | Agents/incidentDistribution      | Error / Escalation / Policy split              | donut, kpi  |
| `agents.getConsumption`        | Agents/consumption                 | Top agents by AGU/PLTU                         | bar, table  |
| `agents.getConsumptionTimeline`| Agents/consumptionTimeline         | AGU burn-rate over time                        | area, line  |
| `agents.getLatencyTimeline`    | Agents/latencyTimeline             | P50 / P95 latency per agent                    | line        |
| `agents.getAgents`             | Agents/agents                      | Fleet list with healthScore                    | table       |
| `agents.getUnitConsumption`    | Agents/summary/unit-consumption    | AGU/PLTU by complete vs incomplete jobs        | kpi, bar    |
| `agents.getNames`              | Agents/names                       | Agent name list (filter dropdowns)             | filter only |

Not for MVP: `agents.getProcessEscalations`

---

## Traceview namespace — POST /Traceview/...

| Method                           | Route suffix                   | Key metrics                              | Shape      |
|----------------------------------|--------------------------------|------------------------------------------|------------|
| `traceview.getLatencyTimeline`   | Traceview/latencyTimeline      | P50/P95 trace latency over time          | line       |
| `traceview.getErrorsTimeline`    | Traceview/errorsTimeline       | Trace errors per agent per bucket        | area, line |
| `traceview.getMemoryTimeline`    | Traceview/memoryTimeline       | In/out/enabled/disabled memory counts    | area       |
| `traceview.getMemoryCallsTimeline` | Traceview/memoryCallsTimeline | Memory API calls over time               | bar        |
| `traceview.getTopMemorySpaces`   | Traceview/topMemorySpaces      | Most-active memory spaces                | bar, table |
| `traceview.getUnitConsumption`   | Traceview/unitConsumption      | Per-agent AIU + PLTU from traces         | table, bar |

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

## Suggested Dashboard Packages

| Dashboard                | Primary endpoints                                                                  |
|--------------------------|------------------------------------------------------------------------------------|
| Executive Fleet Health   | getSummaryV2, jobs.getSummary, getIncidentDistribution, getConsumptionTimeline      |
| Jobs Operations          | jobs.getCompletedTimeline, jobs.getTopFailures, jobs.getProcessDetails             |
| Agent Reliability        | getErrors, getTopErroredAgents, getIncidents, getLatencyTimeline                   |
| Agent Cost / FinOps      | getConsumption, getConsumptionTimeline, getUnitConsumption, getAgents              |
| Traces & Memory          | traceview.getLatencyTimeline, traceview.getErrorsTimeline, traceview.getMemoryTimeline |
| Governance Posture       | governance.getPolicySummary, governance.getPolicyTraces, governance.getOperationSummary |
