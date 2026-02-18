# OAuth Scopes Reference for UiPath TypeScript SDK

This document provides the complete mapping between SDK services/methods and their required OAuth scopes. Use this to determine which scopes an application needs based on the SDK services it uses.

Source: https://uipath.github.io/uipath-typescript/oauth-scopes/

## Scope Format

Scopes follow a hierarchy:
- **Broad scope** (e.g., `OR.Assets`) grants full access (read + write)
- **Granular scope** (e.g., `OR.Assets.Read`) grants restricted access

When in doubt, use the broad scope. Use granular scopes for least-privilege access.

## Complete Service-to-Scope Mapping

### Assets Service

```typescript
import { Assets } from '@uipath/uipath-typescript/assets';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Assets` or `OR.Assets.Read` |
| `getById()` | `OR.Assets` or `OR.Assets.Read` |

### Buckets Service

```typescript
import { Buckets } from '@uipath/uipath-typescript/buckets';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Administration` or `OR.Administration.Read` |
| `getById()` | `OR.Administration` or `OR.Administration.Read` |
| `getFileMetaData()` | `OR.Administration` or `OR.Administration.Read` |
| `getReadUri()` | `OR.Administration` or `OR.Administration.Read` |
| `uploadFile()` | `OR.Administration` or `OR.Administration.Read` |

### Entities Service (Data Fabric)

```typescript
import { Entities } from '@uipath/uipath-typescript/entities';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `DataFabric.Schema.Read` |
| `getById()` | `DataFabric.Schema.Read` |
| `getAllRecords()` | `DataFabric.Data.Read` |
| `getRecordById()` / `getRecord()` | `DataFabric.Data.Read` |
| `insertRecordById()` / `insertRecord()` | `DataFabric.Data.Write` |
| `insertRecordsById()` / `insertRecords()` | `DataFabric.Data.Write` |
| `updateRecordsById()` / `updateRecords()` | `DataFabric.Data.Write` |
| `deleteRecordsById()` / `deleteRecords()` | `DataFabric.Data.Write` |
| `downloadAttachment()` | `DataFabric.Data.Read` |

**Note:** Data Fabric operations typically need both `DataFabric.Schema.Read` (to discover entities) AND `DataFabric.Data.Read`/`DataFabric.Data.Write` (to access data).

### ChoiceSets Service (Data Fabric)

```typescript
import { ChoiceSets } from '@uipath/uipath-typescript/entities';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `DataFabric.Schema.Read` |
| `getById()` | `DataFabric.Data.Read` |

### Processes Service

```typescript
import { Processes } from '@uipath/uipath-typescript/processes';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Execution` or `OR.Execution.Read` |
| `getById()` | `OR.Execution` or `OR.Execution.Read` |
| `start()` | `OR.Jobs` or `OR.Jobs.Write` |

**Note:** Starting processes requires a different scope than listing them.

### ProcessInstances Service (Maestro)

```typescript
import { ProcessInstances } from '@uipath/uipath-typescript/maestro';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `PIMS` |
| `getById()` | `PIMS` |
| `getExecutionHistory()` | `PIMS` |
| `getBpmn()` | `OR.Execution.Read` |
| `getVariables()` | `PIMS` |
| `getIncidents()` | `PIMS` |
| `cancel()` | `PIMS` |
| `pause()` | `PIMS` |
| `resume()` | `PIMS` |

### MaestroProcesses Service

```typescript
import { MaestroProcesses } from '@uipath/uipath-typescript/maestro';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `PIMS` |
| `getIncidents()` | `PIMS` |

### Cases Service

```typescript
import { Cases } from '@uipath/uipath-typescript/cases';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `PIMS` |

### CaseInstances Service

```typescript
import { CaseInstances } from '@uipath/uipath-typescript/cases';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `PIMS` `OR.Execution.Read` |
| `getById()` | `PIMS` `OR.Execution.Read` |
| `close()` | `PIMS` |
| `pause()` | `PIMS` |
| `resume()` | `PIMS` |
| `reopen()` | `PIMS` |
| `getExecutionHistory()` | `PIMS` |
| `getStages()` | `PIMS` `OR.Execution.Read` |
| `getActionTasks()` | `OR.Tasks` or `OR.Tasks.Read` |

### Queues Service

```typescript
import { Queues } from '@uipath/uipath-typescript/queues';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Queues` or `OR.Queues.Read` |
| `getById()` | `OR.Queues` or `OR.Queues.Read` |

### Tasks Service (Action Center)

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';
```

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Tasks` or `OR.Tasks.Read` |
| `getById()` | `OR.Tasks` or `OR.Tasks.Read` |
| `getUsers()` | `OR.Tasks` or `OR.Tasks.Read` |
| `getFormTaskById()` | `OR.Tasks` or `OR.Tasks.Read` |
| `create()` | `OR.Tasks` or `OR.Tasks.Write` |
| `assign()` | `OR.Tasks` or `OR.Tasks.Write` |
| `reassign()` | `OR.Tasks` or `OR.Tasks.Write` |
| `unassign()` | `OR.Tasks` or `OR.Tasks.Write` |
| `complete()` | `OR.Tasks` or `OR.Tasks.Write` |

### Conversational Agent

Combined scopes needed: `OR.Execution` · `OR.Folders` · `OR.Jobs` · `ConversationalAgents` · `Traces.API`

#### Agents

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Execution` or `OR.Execution.Read` |
| `getById()` | `OR.Execution` or `OR.Execution.Read` |

#### Conversations

| Method | Required Scope |
|--------|---------------|
| `create()` | `OR.Execution`, `OR.Folders`, `OR.Jobs` |
| `getAll()` | `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read` |
| `getById()` | `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read` |
| `updateById()` | `OR.Execution`, `OR.Jobs` |
| `deleteById()` | `OR.Execution`, `OR.Jobs` |
| `startSession()` | `OR.Execution`, `OR.Jobs`, `ConversationalAgents` |
| `uploadAttachment()` | `OR.Execution`, `OR.Jobs` |

#### Exchanges

| Method | Required Scope |
|--------|---------------|
| `getAll()` | `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read` |
| `getById()` | `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read` |
| `createFeedback()` | `OR.Execution`, `OR.Jobs`, `Traces.API` |

#### Messages

| Method | Required Scope |
|--------|---------------|
| `getById()` | `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read` |
| `getContentPartById()` | `OR.Execution` or `OR.Execution.Read`, `OR.Jobs` or `OR.Jobs.Read` |

## Quick Scope Builder

To determine the minimum scopes for an app, find all SDK service imports and combine the required scopes:

**Example 1:** App uses Processes (list + start) and Tasks (read + complete)
```
OR.Execution.Read OR.Jobs.Write OR.Tasks
```

**Example 2:** App uses Entities (CRUD) and ChoiceSets (read)
```
DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write
```

**Example 3:** App uses Maestro Processes and Case management
```
PIMS OR.Execution.Read OR.Tasks.Read
```

**Example 4:** App uses Conversational Agent
```
OR.Execution OR.Folders OR.Jobs ConversationalAgents Traces.API
```

**Example 5:** Full-featured app with everything
```
OR.Assets OR.Administration DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write PIMS OR.Execution OR.Folders OR.Jobs OR.Jobs.Write OR.Queues OR.Tasks ConversationalAgents Traces.API
```

## UiPath External Application Resource Mapping

When adding scopes in the UiPath Admin UI (External Applications → Edit → "Add scopes"), scopes are grouped into **resource categories** selected from a dropdown. Here's how SDK scopes map to UI resources:

| Resource in UI Dropdown | SDK Scopes Under This Resource |
|---|---|
| **UiPath.Orchestrator** | `OR.Assets`, `OR.Assets.Read`, `OR.Administration`, `OR.Administration.Read`, `OR.Execution`, `OR.Execution.Read`, `OR.Folders`, `OR.Jobs`, `OR.Jobs.Read`, `OR.Jobs.Write`, `OR.Queues`, `OR.Queues.Read`, `OR.Tasks`, `OR.Tasks.Read`, `OR.Tasks.Write` |
| **Data Fabric API** | `DataFabric.Schema.Read`, `DataFabric.Data.Read`, `DataFabric.Data.Write` |
| **PIMS** | `PIMS` |
| **ConversationalAgents** | `ConversationalAgents` |
| **Traces.API** | `Traces.API` |

**Direct edit URL pattern:** `{baseUrl}/{orgName}/portal_/admin/external-apps/oauth/edit/{clientId}`

## All Available Scopes (Alphabetical)

| Scope | Services |
|-------|----------|
| `ConversationalAgents` | Conversations (startSession) |
| `DataFabric.Data.Read` | Entities (read records, download attachments), ChoiceSets (getById) |
| `DataFabric.Data.Write` | Entities (insert, update, delete records) |
| `DataFabric.Schema.Read` | Entities (list/get entities), ChoiceSets (getAll) |
| `OR.Administration` | Buckets (full access) |
| `OR.Administration.Read` | Buckets (read-only) |
| `OR.Assets` | Assets (full access) |
| `OR.Assets.Read` | Assets (read-only) |
| `OR.Execution` | Processes (full access), Agents, Conversations, Exchanges, Messages |
| `OR.Execution.Read` | Processes (read-only), ProcessInstances (getBpmn), CaseInstances (getAll, getById, getStages), Agents (read) |
| `OR.Folders` | Conversations (create) |
| `OR.Jobs` | Processes (start jobs), Conversations, Exchanges |
| `OR.Jobs.Read` | Conversations (read), Exchanges (read), Messages (read) |
| `OR.Jobs.Write` | Processes (start jobs) |
| `OR.Queues` | Queues (full access) |
| `OR.Queues.Read` | Queues (read-only) |
| `OR.Tasks` | Tasks (full access), CaseInstances (getActionTasks) |
| `OR.Tasks.Read` | Tasks (read-only), CaseInstances (getActionTasks) |
| `OR.Tasks.Write` | Tasks (write operations) |
| `PIMS` | MaestroProcesses, ProcessInstances, Cases, CaseInstances |
| `Traces.API` | Exchanges (createFeedback) |
