# System Center — Full API Reference

Complete API reference for the System Center service. For general info see [system-center.md](system-center.md).

---

## System Center Service (`ISystemCenterService`)

Accessed via the `systemCenter` service accessor.

### RunbookService

Creates an `IRunbookService` instance connected to a System Center Orchestrator.

```csharp
IRunbookService RunbookService(ISystemCenterClientProvider clientProvider);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `clientProvider` | `ISystemCenterClientProvider` | Yes | System Center authentication provider |

**Returns:** `IRunbookService` — Service for performing runbook operations.

---

## Runbook Service (`IRunbookService`)

Provides runbook management operations. Obtained from `systemCenter.RunbookService(...)`.

### GetRunbookServers

Gets a list of all runbook servers.

```csharp
Task<RunbookServer[]> GetRunbookServers();
```

**Returns:** `Task<RunbookServer[]>` — Array of available runbook servers.

---

### GetRunbookById

Gets a runbook by its ID.

```csharp
Task<Runbook> GetRunbookById(string id);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | Runbook ID (GUID) |

**Returns:** `Task<Runbook>`

---

### GetRunbookByPath

Gets a runbook by its path.

```csharp
Task<Runbook> GetRunbookByPath(string path);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | `string` | Yes | Runbook path in the Orchestrator folder hierarchy |

**Returns:** `Task<Runbook>`

---

### GetRunbookInstances

Gets running instances of a runbook, optionally filtered by job ID.

```csharp
Task<RunbookInstance[]> GetRunbookInstances(string runbookId, string jobId);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `runbookId` | `string` | Yes | Runbook ID |
| `jobId` | `string` | Yes | Job ID to filter by (or `null` for all instances) |

**Returns:** `Task<RunbookInstance[]>`

---

### StartRunbook

Starts a runbook execution with the specified parameters.

```csharp
Task<RunbookJob> StartRunbook(string runbookId, string runbookServerId, DataTable parameterDataTable);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `runbookId` | `string` | Yes | ID of the runbook to start |
| `runbookServerId` | `string` | Yes | ID of the runbook server to execute on |
| `parameterDataTable` | `DataTable` | Yes | Input parameters as a DataTable (key-value pairs) |

**Returns:** `Task<RunbookJob>` — The created job.

---

### StopRunbook

Stops a running runbook.

```csharp
Task StopRunbook(string runbookId);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `runbookId` | `string` | Yes | ID of the runbook to stop |

---

### GetJob

Gets a runbook job by its ID.

```csharp
Task<RunbookJob> GetJob(string id);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | Job ID |

**Returns:** `Task<RunbookJob>`

---

### StopJob

Stops a running runbook job.

```csharp
Task StopJob(string id);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | ID of the job to stop |
