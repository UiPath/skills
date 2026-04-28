# User intent → SDK read call (for dashboards)

Translate a "show me / chart / dashboard" request into the right SDK read method + filter. Only read-path intents appear here — anything that mutates tenant state is out of scope for this skill.

## Step 0 — Load SDK context

Before writing any `@uipath/uipath-typescript` call:
- Fetch https://uipath.github.io/uipath-typescript/llms-full-content.txt (complete SDK doc for LLM context), OR
- Drag `node_modules/@uipath/uipath-typescript/` into the AI IDE context.

This file is the dashboard-specific **opinion** layer — "which method do I reach for when the user asks for X". Method signatures and filter-field catalogs live in the SDK docs above; don't re-document them here.

## "Show me..." / "List..." / "What's running?"

| User says | UiPath concept | SDK call | Default viz |
|---|---|---|---|
| "my bots" / "my processes" / "automations I've published" | Process definitions | `processes.getAll()` | table |
| "my agents" (as definitions) | Process definitions filtered to agents | `processes.getAll({ filter: "PackageType eq 'Agent'" })` | table / count KPI |
| "agent runs" / "agent invocations" | Jobs filtered to agents | `jobs.getAll({ filter: "ProcessType eq 'Agent' and CreationTime gt <iso>" })` | hourly bar / daily bar |
| "what's running right now" | Jobs in active states | `jobs.getAll({ filter: "State eq 'Running' or State eq 'Pending'" })` | KPI + live list |
| "recent job runs" / "job history" | Jobs, recent | `jobs.getAll({ filter: "CreationTime gt <iso>" })` | time series bar |
| "what failed" / "errors today" | Faulted jobs | `jobs.getAll({ filter: "State eq 'Faulted' and CreationTime gt <iso>" })` | KPI / daily trend |
| "my queues" | Queue definitions | `queues.getAll()` | table |
| "my assets" | Orchestrator assets | `assets.getAll()` | table |
| "buckets" | Bucket definitions | `buckets.getAll()` | table |
| "files in a bucket" | File metadata | `buckets.getFileMetaData(bucketId, folderId)` | table + size histogram |
| "tasks waiting for action" / "approvals pending" | Action Center tasks | `tasks.getAll({ filter: "Status eq 'Unassigned' or Status eq 'Pending'" })` | KPI + sorted table |
| "my Maestro processes" | Maestro definitions | `maestroProcesses.getAll()` | table |
| "running Maestro instances" | Maestro instances | `processInstances.getAll()` | stacked bar by status |
| "Maestro incidents" | Process incidents | `processIncidents.getAll()` | horizontal bar by type/severity |
| "open cases" / "case pipeline" | Case instances | `caseInstances.getAll()` | funnel (Open→Paused→Closed) |
| "case types" | Case definitions | `cases.getAll()` | table |
| "my data tables" / "entities" | Data Service entities | `entities.getAll()` | table |
| "records in entity X" | Entity records | `entities.getAllRecords(entityId)` or `entities.queryRecordsById(...)` | depends on aggregation |
| "agent conversations" | Exchanges | `exchanges.getAll()` | line/bar of volume |
| "messages in a conversation" | Messages | `messages.getAll({ conversationId })` | table or histogram of message counts |

## "How many..." / "Count of..."

Use the same `getAll` call with a narrow `filter` and use pagination to get the count. When the tenant has totals, read `resp.totalCount` from the first page — saves fetching all rows.

| User says | SDK call | Viz |
|---|---|---|
| "how many jobs today" | `jobs.getAll({ filter: "CreationTime gt <local midnight>" })` → read `totalCount` | KPI |
| "how many faulted jobs last week" | `jobs.getAll({ filter: "State eq 'Faulted' and CreationTime gt <7d ago>" })` → `totalCount` | KPI |
| "how many active agents" | distinct `processName` on agent-filtered jobs in window | KPI |
| "open tasks" | `tasks.getAll({ filter: "Status ne 'Completed'" })` → `totalCount` | KPI |
| "open incidents" | `processIncidents.getAll()` client-filter `status === 'Open'` | KPI |
| "open cases" | `caseInstances.getAll({ filter: "Status eq 'Open'" })` → `totalCount` | KPI |

## "Trend..." / "Over time..."

Bucket by `createdTime` client-side after paginating. Always zero-fill missing buckets (use `zeroFill()` from `src/lib/utils.ts`).

| User says | Data source | Bucket | Viz |
|---|---|---|---|
| "invocations per hour last 24h" | Jobs last 24h | hour (24 slots) | vertical bar |
| "invocations per day last 7d/30d" | Jobs in window | day | vertical bar or line |
| "error rate trend" | faulted / total, per day, last 7d | day | bar (red) |
| "task backlog over time" | snapshots of open-task count | day | line |
| "case close rate" | `closedTime` per day | day | bar |
| "conversation volume" | `exchanges.getAll({ filter: "CreatedTime gt ..." })` | day or hour | line / bar |

## "Top N..." / "Ranked list"

| User says | SDK call + client aggregation | Viz |
|---|---|---|
| "top agents by invocation" | Jobs in window, group by `processName`, sort by count desc | table (or horizontal bar) |
| "top assignees" | Tasks in window, group by `assignedToUser.name` | horizontal bar |
| "most frequent case types" | Case instances, group by `caseAppKey` | horizontal bar |
| "top tools used by agents" | Exchanges → tool calls, group by tool name | horizontal bar |
| "top incidents by element" | ProcessIncidents, group by `elementId` | horizontal bar colored by severity |

## "Breakdown by..." / "Distribution..."

| User says | SDK call | Viz |
|---|---|---|
| "jobs by state" | `jobs.getAll({ filter: window })`, group by `state` | bar (≤6) or horizontal bar |
| "tasks by status" | `tasks.getAll()`, group by `status` | bar or donut if ≤5 |
| "tasks by priority" | same, group by `priority` | bar |
| "cases by status" | `caseInstances.getAll()`, group by `status` | bar / funnel |
| "Maestro instances by state" | `processInstances.getAll()`, group by `status` | stacked bar over time |
| "agents by package type" | `processes.getAll()`, group by `packageType` | bar |

## "Relate X to Y..." / "Flow..."

| User says | Data | Viz |
|---|---|---|
| "case stage flow" | `caseInstance.getExecutionHistory()` or `getStages()` | sankey |
| "Maestro BPMN with runtime overlay" | `processInstance.getBpmn()` + `getExecutionHistory()` | BPMN viewer (bpmn-js) |
| "variable value over time for an instance" | `processInstance.getVariables()` history | line |
| "conversation tool-call tree" | Exchange `contentParts` + `toolCalls` | tree / indented list |

## "Show me this single record"

Every service exposes a `getById` — use it for detail views (drill-downs from lists).

## Pattern: data the user wants isn't in the SDK

If the user asks for something the SDK doesn't expose as a read method (e.g., queue-item transactions), check `node_modules/@uipath/uipath-typescript/dist/<service>/index.d.ts`. If no read method exists, the only dashboard path is a raw HTTP call against the Orchestrator OData endpoint with the same token — outside the SDK's coverage but still a valid data source for your chart.
