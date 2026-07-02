# OAuth Scopes Reference

Required OAuth scopes for each `@uipath/uipath-typescript` SDK service and method.

Use this reference to:
1. Determine which scopes to include in `VITE_UIPATH_SCOPE` (`.env`)
2. Determine which scopes to add to the UiPath External Application

**Note:** Broader scopes cover granular ones (e.g., `OR.Assets` covers `OR.Assets.Read`). Use the most specific scope that satisfies the operations the app performs.

> **Update scopes WHEN you add the feature.** Any new service call — a write op (`insertRecordById`, `updateRecordById`, `deleteRecordById`), an action-causing method (`Jobs.stop`/`resume`/`restart`, `Tasks.complete`/`assign`, `ProcessInstances.cancel`, `Exchanges.createFeedback`, etc.), or a call to a service the app hasn't used before — may need a scope broader than what the current `VITE_UIPATH_SCOPE` in `.env` carries. Check the tables below before shipping the feature. The External Application registration must also allow the scope; if not, the token request is rejected entirely (see [oauth-client-setup.md](oauth-client-setup.md)).

---

## Assets

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Assets` or `OR.Assets.Read` |
| `getById()` | `OR.Assets` or `OR.Assets.Read` |
| `getByName()` | `OR.Assets` or `OR.Assets.Read` |

---

## Jobs

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Jobs` or `OR.Jobs.Read` |
| `getById()` | `OR.Jobs` or `OR.Jobs.Read` |
| `getOutput()` | `OR.Jobs` or `OR.Jobs.Read` **plus** `OR.Folders` or `OR.Folders.Read` (required because `getOutput` internally calls the Attachments API to resolve file-type output arguments) |
| `stop()` | `OR.Jobs` |
| `resume()` | `OR.Jobs` or `OR.Jobs.Write` |
| `restart()` | `OR.Jobs` |

---

## Attachments

| Method | Required Scope |
|--------|----------------|
| `getById()` | `OR.Folders` or `OR.Folders.Read` |

---

## Buckets

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Buckets` or `OR.Buckets.Read` |
| `getById()` | `OR.Buckets` or `OR.Buckets.Read` |
| `getByName()` | `OR.Buckets` or `OR.Buckets.Read` |
| `getFiles()` | `OR.Buckets` or `OR.Buckets.Read` |
| `getFileMetaData()` | `OR.Buckets` or `OR.Buckets.Read` |
| `getReadUri()` | `OR.Buckets` or `OR.Buckets.Read` |
| `uploadFile()` | `OR.Buckets` |
| `deleteFile()` | `OR.Buckets` or `OR.Buckets.Write` |

---

## Entities (Data Fabric)

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `DataFabric.Schema.Read` |
| `getById()` | `DataFabric.Schema.Read` |
| `getAllRecords()` | `DataFabric.Data.Read` |
| `getRecordById()` / `getRecord()` | `DataFabric.Data.Read` |
| `insertRecordById()` / `insertRecord()` | `DataFabric.Data.Write` |
| `insertRecordsById()` / `insertRecords()` | `DataFabric.Data.Write` |
| `deleteRecordsById()` / `deleteRecords()` | `DataFabric.Data.Write` |
| `deleteRecordById()` / `deleteRecord()` | `DataFabric.Data.Write` |
| `updateRecordById()` / `updateRecord()` | `DataFabric.Data.Write` |
| `updateRecordsById()` / `updateRecords()` | `DataFabric.Data.Write` |
| `queryRecordsById()` / `queryRecords()` | `DataFabric.Data.Read` |
| `downloadAttachment()` | `DataFabric.Data.Read` |
| `uploadAttachment()` | `DataFabric.Data.Write` |
| `deleteAttachment()` | `DataFabric.Data.Write` |

---

## ChoiceSets (Data Fabric)

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `DataFabric.Schema.Read` |
| `getById()` | `DataFabric.Data.Read` |

---

## Processes

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Execution` or `OR.Execution.Read` |
| `getById()` | `OR.Execution` or `OR.Execution.Read` |
| `getByName()` | `OR.Execution` or `OR.Execution.Read` |
| `start()` | `OR.Jobs` or `OR.Jobs.Write` |

---

## Queues

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Queues` or `OR.Queues.Read` |
| `getById()` | `OR.Queues` or `OR.Queues.Read` |

---

## Tasks (Orchestrator)

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Tasks` or `OR.Tasks.Read` |
| `getById()` | `OR.Tasks` or `OR.Tasks.Read` |
| `getUsers()` | `OR.Tasks` or `OR.Tasks.Read` |
| `create()` | `OR.Tasks` or `OR.Tasks.Write` |
| `assign()` / `reassign()` / `unassign()` | `OR.Tasks` or `OR.Tasks.Write` |
| `complete()` | `OR.Tasks` or `OR.Tasks.Write` |

---

## Maestro Process Instances

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `PIMS` |
| `getById()` | `PIMS` |
| `getExecutionHistory()` | `PIMS` |
| `getBpmn()` | `OR.Execution.Read` |
| `getVariables()` | `PIMS` |
| `getIncidents()` | `PIMS` |
| `cancel()` / `pause()` / `resume()` | `PIMS` |

## Maestro Processes

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `PIMS` |
| `getIncidents()` | `PIMS` |
| `getInstanceStatusTimeline()` | `Insights.RealTimeData Insights OR.Folders.Read` |
| `getTopRunCount()` / `getTopFaultedCount()` / `getTopExecutionDuration()` | `Insights.RealTimeData Insights OR.Folders.Read` |

## Maestro Process Incidents (standalone)

| Method | Required Scope |
|--------|----------------|
| `ProcessIncidents.getAll()` | `PIMS` |

---

## Cases

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `PIMS` |
| `getInstanceStatusTimeline()` | `Insights.RealTimeData Insights OR.Folders.Read` |
| `getTopRunCount()` / `getTopFaultedCount()` / `getTopExecutionDuration()` | `Insights.RealTimeData Insights OR.Folders.Read` |

## Case Instances

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `PIMS` and `OR.Execution.Read` |
| `getById()` | `PIMS` and `OR.Execution.Read` |
| `getStages()` | `PIMS` and `OR.Execution.Read` |
| `close()` / `pause()` / `resume()` / `reopen()` | `PIMS` |
| `getExecutionHistory()` | `PIMS` |
| `getActionTasks()` | `OR.Tasks` or `OR.Tasks.Read` |
| `getSlaSummary()` / `getStagesSlaSummary()` | `Insights.RealTimeData Insights OR.Folders.Read PIMS` |

---

## Conversational Agent

Combined scopes required: `OR.Execution` · `OR.Folders` · `OR.Jobs` · `ConversationalAgents` · `Traces.Api`

### Agents

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Execution` or `OR.Execution.Read` |
| `getById()` | `OR.Execution` or `OR.Execution.Read` |

### Conversations

| Method | Required Scope |
|--------|----------------|
| `create()` | `OR.Execution`, `OR.Folders`, `OR.Jobs` |
| `getAll()` / `getById()` | `OR.Execution.Read`, `OR.Jobs.Read` |
| `updateById()` / `deleteById()` | `OR.Execution`, `OR.Jobs` |
| `startSession()` | `OR.Execution`, `OR.Jobs`, `ConversationalAgents` |
| `uploadAttachment()` / `getAttachmentUploadUri()` | `OR.Execution`, `OR.Jobs` |

### Exchanges

| Method | Required Scope |
|--------|----------------|
| `getAll()` / `getById()` | `OR.Execution.Read`, `OR.Jobs.Read` |
| `createFeedback()` | `OR.Execution`, `OR.Jobs`, `Traces.Api` |

### Messages

| Method | Required Scope |
|--------|----------------|
| `getById()` / `getContentPartById()` | `OR.Execution.Read`, `OR.Jobs.Read` |

### User Settings (`conversationalAgent.user`)

| Method | Required Scope |
|--------|----------------|
| `getSettings()` | `OR.Users` or `OR.Users.Read` |
| `updateSettings()` | `OR.Users` |

---

## Agent Feedback

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `Traces.Api` |
| `getById()` | `Traces.Api` |
| `getCategories()` | `Traces.Api` |
| `submit()` | `Traces.Api` |
| `updateById()` | `Traces.Api` |
| `deleteById()` | `Traces.Api` |
| `createCategory()` | `Traces.Api` |
| `deleteCategory()` | `Traces.Api` |

---

## Widgets

Scopes required by `@uipath/ui-widgets-*` React components. The widget's own runtime API calls are listed here — add scopes from the sections above for any additional SDK calls the host app makes.

### Validation Station (`@uipath/ui-widgets-validation-station`)

| Required Scope | Why |
|----------------|-----|
| `OR.Buckets` | Widget reads the document and extraction artifacts from a storage bucket and uploads the validated payload during save. Read-only `OR.Buckets.Read` is insufficient — the upload step requires write. |
| `OR.Tasks` or `OR.Tasks.Write` | Required when the host app calls `task.complete()` in `onSaveComplete` (action apps, and web apps that complete the task on save). |

See [widgets/validation-station.md](widgets/validation-station.md) for the full integration guide.

> **TODO:** Document scopes for the remaining widgets when their integration guides land in `references/widgets/`:
> - `@uipath/ui-widgets-conversational-agent-chat`
> - `@uipath/ui-widgets-datatable`
> - `@uipath/ui-widgets-multi-file-upload`

---

## Agents — Insights RTM (SDK ≥ 1.4.1)

| Method | Required Scope |
|--------|----------------|
| `Agents.getAll()` / `getErrors()` | `Insights` and `Insights.RealTimeData` |
| `Agents.getErrorsTimeline()` / `getConsumptionTimeline()` / `getLatencyTimeline()` | `Insights` and `Insights.RealTimeData` |

## Agent Traces (SDK ≥ 1.4.1)

| Method | Required Scope |
|--------|----------------|
| `AgentTraces.getErrorsTimeline()` / `getLatencyTimeline()` / `getUnitConsumption()` | `Insights` and `Insights.RealTimeData` |
| `AgentTraces.getSpansByTraceId()` / `getSpansByReference()` | `Insights` and `Insights.RealTimeData` |
| `Traces.getById()` / `getSpansByIds()` (generic spans — governance traces) | `Traces.Api` (+ `Insights` and `Insights.RealTimeData`) |

## Agent Memory (SDK ≥ 1.4.1)

| Method | Required Scope |
|--------|----------------|
| `AgentMemory.getTimeline()` / `getCallsTimeline()` / `getTopSpaces()` | `Insights` and `Insights.RealTimeData` |

## Governance (SDK ≥ 1.4.1)

| Method | Required Scope |
|--------|----------------|
| `Governance.getPolicyTraces()` / `getOperationSummary()` | `Insights` and `Insights.RealTimeData` — caller needs elevated (org-admin) access; `fullOrganization: true` returns 403 without org-admin |

## Maestro Insights — RTM (SDK ≥ 1.4.x)

These use the Insights RTM host (`INSIGHTS_RTM_BASE`). The SLA methods also touch PIMS-backed case data and require `PIMS` on top of the Insights scopes.

| Method | Required Scope |
|--------|----------------|
| `Cases` / `MaestroProcesses` `.getTopRunCount()` / `getTopFaultedCount()` / `getTopExecutionDuration()` / `getTopElementFailedCount()` / `getInstanceStatusTimeline()` / `getElementStats()` | `Insights` · `Insights.RealTimeData` · `OR.Folders.Read` |
| `CaseInstances.getSlaSummary()` / `getStagesSlaSummary()` | `Insights` · `Insights.RealTimeData` · `OR.Folders.Read` · **`PIMS`** |

> All Insights RTM methods (Agents, Agent Traces, Agent Memory, Governance, Maestro Insights above) also require `OR.Folders.Read` — covered by the granted `OR.Folders`. `Cases.getAll` / `CaseInstances.getAll` (PIMS host, not Insights) require `PIMS` — see the Maestro sections above.

---

## Common Scope Bundles

| App uses... | Minimum scopes needed |
|---|---|
| Data Fabric (read-only) | `DataFabric.Schema.Read DataFabric.Data.Read` |
| Data Fabric (read + write) | `DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write` |
| Orchestrator Tasks (read + complete) | `OR.Tasks` |
| Orchestrator Processes (list + start) | `OR.Execution OR.Jobs` |
| Orchestrator Jobs (list + read output) | `OR.Jobs.Read OR.Folders.Read` (add `OR.Folders.Read` so `Jobs.getOutput()` can resolve file-type output arguments via Attachments) |
| Maestro full access | `PIMS OR.Execution.Read` |
| Maestro analytics / insights dashboards (top run/fault/duration counts, status timelines, SLA) | add `Insights.RealTimeData Insights OR.Folders.Read` (SLA summaries also need `PIMS`) |
| Conversational Agent | `OR.Execution OR.Folders OR.Jobs ConversationalAgents Traces.Api` (add `OR.Users` for user-settings read/write) |
| Insights RTM (Agents, Agent Traces, Agent Memory, Governance, Maestro Insights) | `Insights Insights.RealTimeData OR.Folders.Read` |
| Maestro SLA (CaseInstances SLA summary) | `Insights Insights.RealTimeData OR.Folders.Read PIMS` |
