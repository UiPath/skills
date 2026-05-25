# Data Router — SDK vs Insights

Rule: SDK for operational state (current counts, list views, snapshots).
      Insights for analytics (historical trends, aggregations, percentiles, derived metrics).

## Routing Table

All Insights API calls are POST JSON with body `{ "tenantId": "<UUID>", "startTime": "...", ... }`.

| Intent signals                                           | Route    | Call                                                       |
|----------------------------------------------------------|----------|------------------------------------------------------------|
| job count, job status, running jobs, failed jobs         | SDK      | orchestrator/jobs → `Jobs.getAll()`                        |
| queue items, queue depth, transaction throughput         | SDK      | orchestrator/queues → `QueueItems.getAll()`                |
| process list, automation inventory                       | SDK      | orchestrator/processes → `Processes.getAll()`              |
| maestro instances, flow runs, active flows               | SDK      | maestro/processes → `ProcessInstances.getAll()`            |
| case status, case backlog                                | SDK      | maestro/cases → `CaseInstances.getAll()`                   |
| case SLA, SLA compliance                                 | SDK      | maestro/cases → `CaseInstances.getSlaSummary()`            |
| action center tasks, pending approvals                   | SDK      | action-center/tasks → `Tasks.getAll()`                     |
| DataFabric entity records                                | SDK      | data-fabric/entities → `Entities.getAll()`                 |
| agent success rate, failure rate, avg duration           | Insights | `agents.getSummaryV2` → POST `/Agents/summaryV2`           |
| agent error spikes, errors over time                     | Insights | `agents.getErrors` → POST `/Agents/errors`                 |
| top erroring agents, error leaderboard                   | Insights | `agents.getTopErroredAgents` → POST `/Agents/topErroredAgents` |
| agent incidents, recurring errors                        | Insights | `agents.getIncidents` → POST `/Agents/incidents`           |
| incident type mix (error/escalation/policy split)        | Insights | `agents.getIncidentDistribution` → POST `/Agents/incidentDistribution` |
| token consumption, AGU, PLTU, cost per agent             | Insights | `agents.getConsumption` → POST `/Agents/consumption`       |
| AGU burn-rate over time                                  | Insights | `agents.getConsumptionTimeline` → POST `/Agents/consumptionTimeline` |
| P50 / P95 latency per agent over time                    | Insights | `agents.getLatencyTimeline` → POST `/Agents/latencyTimeline` |
| agent fleet list, health score, stale agents             | Insights | `agents.getAgents` → POST `/Agents/agents`                 |
| AGU/PLTU split by complete vs incomplete jobs            | Insights | `agents.getUnitConsumption` → POST `/Agents/summary/unit-consumption` |
| trace latency P50/P95 over time (trace-level)            | Insights | `traceview.getLatencyTimeline` → POST `/Traceview/latencyTimeline` |
| trace errors by agent over time                          | Insights | `traceview.getErrorsTimeline` → POST `/Traceview/errorsTimeline` |
| memory usage (in/out/enabled/disabled)                   | Insights | `traceview.getMemoryTimeline` → POST `/Traceview/memoryTimeline` |
| top memory spaces, memory adoption                       | Insights | `traceview.getTopMemorySpaces` → POST `/Traceview/topMemorySpaces` |
| policy Allow/Deny/NoOp ratio                             | Insights | `governance.getPolicySummary` → POST `/Governance/policy/summary` |
| recent policy decisions, denial feed                     | Insights | `governance.getPolicyTraces` → POST `/Governance/policy/traces` |
| governed operation volume                                | Insights | `governance.getOperationSummary` → POST `/Governance/operation/summary` |
| completed job trend (historical)                         | Insights | `jobs.getCompletedTimeline` → POST `/api/v1.0/InsightsJobs/completed-timeline` |
| job aggregate KPI (total/success/avg duration)           | Insights | `jobs.getSummary` → POST `/api/v1.0/InsightsJobs/summary` |
| top failing processes (historical)                       | Insights | `jobs.getTopFailures` → POST `/api/v1.0/InsightsJobs/top-failures` |

## Tie-breaking Rules
- "job count today" → SDK (current state); "job count over 7 days" → Insights `jobs.getCompletedTimeline`
- "queue depth" → SDK; "queue throughput trend" → no Insights endpoint, stay SDK
- P50/P95/P99 latency → Insights `agents.getLatencyTimeline` (fleet) or `traceview.getLatencyTimeline` (trace)
- "agent health" snapshot → Insights `agents.getAgents` (has `healthScore`); "success rate over time" → `agents.getSummaryV2`
- `governance.getPolicySummary` requires `policy` (UUID) in body in addition to `tenantId`

## SDK Import Pattern
```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
import { Jobs } from '@uipath/uipath-typescript/jobs';
// Never root imports — always subpath exports
```

## Insights Hook Pattern
```typescript
import { useInsights } from '../hooks/useInsights';
// Key is namespace.method
const { data, loading, error } = useInsights(
  'agents.getSummaryV2',
  { startTime: '2025-01-01T00:00:00Z' }
);
```
