# OAuth Scopes Reference

Required OAuth scopes for each `@uipath/uipath-typescript` SDK service and method.

Use this reference to:
1. Determine which scopes to include in `VITE_UIPATH_SCOPE` (`.env`)
2. Determine which scopes to add to the UiPath External Application

**Note:** Broader scopes cover granular ones (e.g., `OR.Assets` covers `OR.Assets.Read`). Use the most specific scope that satisfies the operations the app performs.

---

## Assets

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Assets` or `OR.Assets.Read` |
| `getById()` | `OR.Assets` or `OR.Assets.Read` |

---

## Jobs

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Jobs` or `OR.Jobs.Read` |

---

## Buckets

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `OR.Administration` or `OR.Administration.Read` |
| `getById()` | `OR.Administration` or `OR.Administration.Read` |
| `getFileMetaData()` | `OR.Administration` or `OR.Administration.Read` |
| `getReadUri()` | `OR.Administration` or `OR.Administration.Read` |
| `uploadFile()` | `OR.Administration` or `OR.Administration.Read` |

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
| `updateRecordById()` / `updateRecord()` | `DataFabric.Data.Write` |
| `updateRecordsById()` / `updateRecords()` | `DataFabric.Data.Write` |
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
| `getFormTaskById()` | `OR.Tasks` or `OR.Tasks.Read` |
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

---

## Cases

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `PIMS` |

## Case Instances

| Method | Required Scope |
|--------|----------------|
| `getAll()` | `PIMS` and `OR.Execution.Read` |
| `getById()` | `PIMS` and `OR.Execution.Read` |
| `getStages()` | `PIMS` and `OR.Execution.Read` |
| `close()` / `pause()` / `resume()` / `reopen()` | `PIMS` |
| `getExecutionHistory()` | `PIMS` |
| `getActionTasks()` | `OR.Tasks` or `OR.Tasks.Read` |

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
| `uploadAttachment()` | `OR.Execution`, `OR.Jobs` |

### Exchanges

| Method | Required Scope |
|--------|----------------|
| `getAll()` / `getById()` | `OR.Execution.Read`, `OR.Jobs.Read` |
| `createFeedback()` | `OR.Execution`, `OR.Jobs`, `Traces.Api` |

### Messages

| Method | Required Scope |
|--------|----------------|
| `getById()` / `getContentPartById()` | `OR.Execution.Read`, `OR.Jobs.Read` |

---

## Common Scope Bundles

| App uses... | Minimum scopes needed |
|---|---|
| Data Fabric (read-only) | `DataFabric.Schema.Read DataFabric.Data.Read` |
| Data Fabric (read + write) | `DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write` |
| Orchestrator Tasks (read + complete) | `OR.Tasks` |
| Orchestrator Processes (list + start) | `OR.Execution OR.Jobs` |
| Maestro full access | `PIMS OR.Execution.Read` |
| Conversational Agent | `OR.Execution OR.Folders OR.Jobs ConversationalAgents Traces.Api` |
