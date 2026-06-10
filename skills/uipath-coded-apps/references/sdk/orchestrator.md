# Orchestrator Reference

## Imports

```typescript
import { Assets } from '@uipath/uipath-typescript/assets';
import { Queues } from '@uipath/uipath-typescript/queues';
import { Buckets } from '@uipath/uipath-typescript/buckets';
import { Processes } from '@uipath/uipath-typescript/processes';
import { Jobs } from '@uipath/uipath-typescript/jobs';
import { Attachments } from '@uipath/uipath-typescript/attachments';
```

## Note: Folder-Scoped Services

Assets, Queues, Buckets, and Processes are folder-scoped. Many methods require a `folderId` parameter.

**Bound methods**: `Jobs.getById()` and `Jobs.getAll()` items return response objects with attached methods (`getOutput()`, `stop()`, `resume()`, `restart()`). Assets, Queues, Buckets, Processes, and Attachments responses do **not** have attached methods — use the service directly.

## `getByName` folder identifiers

`Assets.getByName` and `Processes.getByName` accept `FolderScopedOptions` — supply one of `folderId`, `folderKey`, or `folderPath` (e.g., `'Shared/Finance'`). If multiple are supplied, server precedence is `folderPath` > `folderKey` > `folderId`.

## Types to Import

```typescript
// Assets
import type {
  AssetGetResponse,
  AssetGetAllOptions,
  AssetGetByIdOptions,
  AssetGetByNameOptions,
  CustomKeyValuePair,
} from '@uipath/uipath-typescript/assets';

// Queues
import type {
  QueueGetResponse,
  QueueGetAllOptions,
  QueueGetByIdOptions,
} from '@uipath/uipath-typescript/queues';

// Buckets
import type {
  BucketGetResponse,
  BucketGetAllOptions,
  BucketGetByIdOptions,
  BucketGetFileMetaDataWithPaginationOptions,
  BucketGetFileMetaDataOptions,
  BucketGetReadUriOptions,
  BucketGetUriResponse,
  BucketUploadFileOptions,
  BucketUploadResponse,
  BlobItem,
} from '@uipath/uipath-typescript/buckets';

// Processes
import type {
  ProcessGetResponse,
  ProcessGetAllOptions,
  ProcessGetByIdOptions,
  ProcessGetByNameOptions,
  ProcessStartRequest,
  ProcessStartResponse,
} from '@uipath/uipath-typescript/processes';

// Jobs
import type {
  JobGetResponse,
  JobGetAllOptions,
  JobGetByIdOptions,
  JobStopOptions,
  JobResumeOptions,
  JobMethods,
} from '@uipath/uipath-typescript/jobs';

// Attachments
import type {
  AttachmentResponse,
  AttachmentGetByIdOptions,
} from '@uipath/uipath-typescript/attachments';
```

## Enums

```typescript
// Assets
import {
  AssetValueScope,   // Global, PerRobot
  AssetValueType,    // DBConnectionString, HttpConnectionString, Text, Bool, Integer, Credential, WindowsCredential, KeyValueList, Secret
} from '@uipath/uipath-typescript/assets';

// Buckets
import {
  BucketOptions,     // None, ReadOnly, AuditReadAccess, AccessDataThroughOrchestrator
} from '@uipath/uipath-typescript/buckets';

// Processes
import {
  PackageType,       // Undefined, Process, ProcessOrchestration, WebApp, Agent, TestAutomationProcess, Api, MCPServer, BusinessRules
  JobPriority,       // Low, Normal, High
  StartStrategy,     // All, Specific, RobotCount, JobsCount, ModernJobsCount
  TargetFramework,   // Legacy, Windows, Portable
  RobotSize,         // Small, Standard, Medium, Large
  PackageSourceType, // Manual, Schedule, Queue, StudioWeb, ...
  StopStrategy,      // SoftStop, Kill
} from '@uipath/uipath-typescript/processes';
```

## Assets Service (Scopes: `OR.Assets` or `OR.Assets.Read`)

### getAll(options?: AssetGetAllOptions)

Returns `NonPaginatedResponse<AssetGetResponse>` or `PaginatedResponse<AssetGetResponse>`. Options extend `RequestOptions & PaginationOptions & { folderId?: number }`. Supports `filter`, `orderby`, `expand`, `select`.

### getById(id: number, folderId: number, options?: AssetGetByIdOptions)

Returns `Promise<AssetGetResponse>`. The `folderId` is required.

### getByName(name: string, options: AssetGetByNameOptions)

Returns `Promise<AssetGetResponse>`. Resolves an asset by display name within a folder. Supply one of `folderId` (number), `folderKey` (GUID string), or `folderPath` (e.g., `'Shared/Finance'`). Throws `NotFoundError` if no asset matches.

```typescript
await assets.getByName('ApiKey', { folderId: 123 });
await assets.getByName('ApiKey', { folderKey: '5f6dadf1-3677-49dc-8aca-c2999dd4b3ba' });
await assets.getByName('ApiKey', { folderPath: 'Shared/Finance', expand: 'keyValueList' });
```

`AssetGetResponse` fields: `key`, `name`, `id`, `canBeDeleted`, `valueScope`, `valueType`, `value`, `credentialStoreId`, `keyValueList`, `hasDefaultValue`, `description`, `foldersCount`, `lastModifiedTime`, `createdTime`, `creatorUserId`. **Note:** Additional fields may be available. Check the TypeScript types for the complete list.

## Queues Service (Scopes: `OR.Queues` or `OR.Queues.Read`)

### getAll(options?: QueueGetAllOptions)

Returns `NonPaginatedResponse<QueueGetResponse>` or `PaginatedResponse<QueueGetResponse>`. Options extend `RequestOptions & PaginationOptions & { folderId?: number }`.

### getById(id: number, folderId: number, options?: QueueGetByIdOptions)

Returns `Promise<QueueGetResponse>`. The `folderId` is required.

`QueueGetResponse` fields: `key`, `name`, `id`, `description`, `maxNumberOfRetries`, `acceptAutomaticallyRetry`, `retryAbandonedItems`, `enforceUniqueReference`, `encrypted`, `createdTime`, `slaInMinutes`, `riskSlaInMinutes`, `folderId`, `folderName`.

## Buckets Service (Scopes: `OR.Administration` or `OR.Administration.Read`)

### getAll(options?: BucketGetAllOptions)

Returns `NonPaginatedResponse<BucketGetResponse>` or `PaginatedResponse<BucketGetResponse>`. Options extend `RequestOptions & PaginationOptions & { folderId?: number }`.

### getById(bucketId: number, folderId: number, options?: BucketGetByIdOptions)

Returns `Promise<BucketGetResponse>`.

`BucketGetResponse` fields: `id`, `name`, `description`, `identifier`, `storageProvider`, `storageContainer`, `options`, `foldersCount`.

### getFileMetaData(bucketId: number, folderId: number, options?: BucketGetFileMetaDataWithPaginationOptions)

Returns `NonPaginatedResponse<BlobItem>` or `PaginatedResponse<BlobItem>`. Options: `{ prefix?: string }` plus pagination. Each `BlobItem` has: `path`, `contentType`, `size`, `lastModified`.

### uploadFile(options: BucketUploadFileOptions)

Returns `Promise<BucketUploadResponse>` with `{ success, statusCode }`. Options: `{ bucketId, folderId, path, content: Blob | Uint8Array<ArrayBuffer> | File }`.

### getReadUri(options: BucketGetReadUriOptions)

Returns `Promise<BucketGetUriResponse>` with `{ uri, httpMethod, requiresAuth, headers }`. Options: `{ bucketId, folderId, path, expiryInMinutes? }`.

## Processes Service (Scopes: `OR.Execution` / `OR.Execution.Read`, `OR.Jobs` / `OR.Jobs.Write` for start)

### getAll(options?: ProcessGetAllOptions)

Returns `NonPaginatedResponse<ProcessGetResponse>` or `PaginatedResponse<ProcessGetResponse>`. Options extend `RequestOptions & PaginationOptions & { folderId?: number }`.

### getById(id: number, folderId: number, options?: ProcessGetByIdOptions)

Returns `Promise<ProcessGetResponse>`.

### getByName(name: string, options: ProcessGetByNameOptions)

Returns `Promise<ProcessGetResponse>`. Resolves a process release by name within a folder. Supply one of `folderId`, `folderKey`, or `folderPath`. Throws `NotFoundError` if no process matches.

```typescript
await processes.getByName('MyProcess', { folderPath: 'Shared/Finance', expand: 'entryPoints' });
```

`ProcessGetResponse` fields: `key`, `packageKey`, `packageVersion`, `isLatestVersion`, `description`, `name`, `packageType`, `targetFramework`, `robotSize`, `autoUpdate`, `id`, `folderId`, `folderName`, `folderKey`, `createdTime`, `lastModifiedTime`.

### start(request: ProcessStartRequest, folderId: number, options?: RequestOptions)

Returns `Promise<ProcessStartResponse[]>`. The `request` must include either `processKey` or `processName`. Optional fields: `strategy`, `robotIds`, `jobsCount`, `inputArguments`, `jobPriority`.

`ProcessStartResponse` fields: `key`, `startTime`, `endTime`, `state`, `source`, `processName`, `type`, `id`, `folderId`.

## Jobs Service (Scopes: `OR.Jobs` or `OR.Jobs.Read`)

### getAll(options?: JobGetAllOptions)

Returns `NonPaginatedResponse<JobGetResponse>` or `PaginatedResponse<JobGetResponse>`. Options extend `RequestOptions & PaginationOptions & { folderId?: number }`. Supports `filter`, `orderby`, `expand`, `select`. Rows are on `.items`.

**Example response** (`.items`) — an agent job next to a standard RPA job. The agent job is `packageType: "Agent"` (the SDK maps raw `ProcessType` → `packageType`). Note `sourceType` is the *trigger origin* (here both happen to differ) and does NOT identify an agent — see § Job classification:

```json
{
  "items": [
    {
      "id": 4012, "key": "a1b2c3d4-0000-0000-0000-000000000001",
      "state": "Successful", "packageType": "Agent", "sourceType": "Manual",
      "processName": "InvoiceTriageAgent",
      "startTime": "2026-06-09T10:01:22Z", "endTime": "2026-06-09T10:01:48Z",
      "createdTime": "2026-06-09T10:01:20Z", "hostMachineName": "AGENT-RUNTIME-3"
    },
    {
      "id": 4011, "key": "a1b2c3d4-0000-0000-0000-000000000002",
      "state": "Faulted", "packageType": "Process", "sourceType": "Schedule",
      "processName": "DailyReconcile",
      "startTime": "2026-06-09T09:40:00Z", "endTime": "2026-06-09T09:41:12Z",
      "createdTime": "2026-06-09T09:39:58Z", "hostMachineName": "BOT-07"
    }
  ],
  "count": 2
}
```

### getById(id: string, folderId: number, options?: JobGetByIdOptions)

Returns `Promise<JobGetResponse>`. The `folderId` is required. **Note:** `id` is a `string` here (not a `number` like Assets/Queues/Processes).

### getOutput(jobKey: string, folderId: number)

Returns `Promise<Record<string, unknown> | null>` — the job's parsed output arguments, or `null` if unavailable. Use after a job has finished; output is not populated while the job is still running.

### stop(jobKeys: string[], folderId: number, options?: JobStopOptions)

Returns `Promise<void>`. Stops one or more jobs (pass an array even for a single job). Throws if any keys cannot be resolved. `JobStopOptions`: `{ strategy?: StopStrategy }` — `StopStrategy.SoftStop` (default, graceful) or `StopStrategy.Kill` (immediate).

### resume(jobKey: string, folderId: number, options?: JobResumeOptions)

Returns `Promise<void>`. Resumes a job currently in `Suspended` state. `JobResumeOptions`: `{ inputArguments?: Record<string, unknown> }`.

### restart(jobKey: string, folderId: number)

Returns `Promise<JobGetResponse>` — a **new** job with a new `key`, in `Pending` state. The original job must be in a final state (`Successful`, `Faulted`, or `Stopped`). Inputs are inherited from the original.

`JobGetResponse` fields: `key`, `id`, `state`, `createdTime`, `startTime`, `endTime`, `lastModifiedTime`, `resumeTime`, `processName`, `entryPointPath`, `processVersionId`, `hostMachineName`, `inputArguments`, `outputArguments`, `environmentVariables`, `type`, `sourceType`, `packageType`, `runtimeType`, `serverlessJobType`, `jobPriority`, `specificPriorityValue`, `stopStrategy`, `remoteControlAccess`, `batchExecutionKey`, `parentJobKey`, `traceId`, `parentSpanId`, `errorCode`, `jobError`, `subState`, `machine`, `robot`, `process`. The `machine`, `robot`, and `process` fields are populated only when requested via `expand`.

### Job classification — agent vs process vs app

An agent job is identified by **`packageType === 'Agent'`** on the SDK response object. The SDK's `JobMap` renames the raw API field `ProcessType → packageType`, so a raw job with `ProcessType: "Agent"` arrives as `packageType: "Agent"`.

| Where | Field | Agent job value |
|-------|-------|-----------------|
| SDK response object (`fnBody` reads this) | `packageType` | `"Agent"` |
| OData server-side `filter` string (raw API name) | `ProcessType` | `"Agent"` |

> **Do NOT use `sourceType` to find agent jobs.** `sourceType` (raw `Source` / `JobSourceType`) is the **trigger origin** — `Manual`, `Schedule`, `Queue`, `Agent`, `Apps`, `HttpTrigger`, … An agent job can be triggered manually (`sourceType: "Manual"`), and `sourceType: "Agent"` only means "started by an agent source," which is a different thing. Filtering on `sourceType === 'Agent'` is wrong in both directions.

Field mappings (raw → SDK, from `JobMap`): `releaseName → processName`, `creationTime → createdTime`, `organizationUnitId → folderId`. Job latency ← `endTime − startTime` (both timestamps; `endTime` is null while `Running`).

Server-side filters (use the raw field name `ProcessType` in the OData string):
- Agent jobs: `getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' })`
- Faulted agent jobs: `getAll({ filter: "State eq 'Faulted' and ProcessType eq 'Agent'" })`
- Reading results: `result.items.filter(j => j.packageType === 'Agent')` (client-side, mapped field name)

Cross-check any filter against the example response above before committing it: the field you filter on must appear there with the value you expect.

## Job-Attached Methods (JobMethods)

Returned by `getById()` and `getAll()` items on each `JobGetResponse`. These are bound to the job's `key` and `folderId`, so you don't need to pass them again:

- `job.getOutput()` -> `Promise<Record<string, unknown> | null>`
- `job.stop(options?)` -> `Promise<void>`
- `job.resume(options?)` -> `Promise<void>`
- `job.restart()` -> `Promise<JobGetResponse>` (new job)

```typescript
const all = await jobs.getAll({ folderId, pageSize: 20 });
const running = all.items.find(j => j.state === 'Running');
if (running) await running.stop();             // bound — no folderId needed
const completed = all.items.find(j => j.state === 'Successful');
if (completed) {
  const output = await completed.getOutput();   // bound
  const newJob = await completed.restart();     // bound
}
```

## Attachments Service (Scopes: `OR.Folders` or `OR.Folders.Read`)

Standalone service for retrieving Orchestrator attachment metadata and a signed URL for downloading the blob. `Jobs.getOutput()` uses this internally to resolve file-type output arguments — most app code will not need to call it directly, but if you call `Jobs.getOutput()` you must add `OR.Folders` (or `OR.Folders.Read`) to the app's scopes in addition to `OR.Jobs`.

### getById(id: string, options?: AttachmentGetByIdOptions)

Returns `Promise<AttachmentResponse>`. Options support OData `expand` / `select`.

`AttachmentResponse` fields: `id`, `name`, `jobKey?`, `attachmentCategory?`, `lastModifiedTime?`, `lastModifierUserId?`, `createdTime?`, `creatorUserId?`, `blobFileAccess: BucketGetUriResponse` (the signed URL + headers — `{ uri, httpMethod, requiresAuth, headers }`).

```typescript
import { Attachments } from '@uipath/uipath-typescript/attachments';

const attachments = new Attachments(sdk);
const attachment = await attachments.getById('<attachmentId>');
// Download the blob using the signed URI
const blob = await fetch(attachment.blobFileAccess.uri).then(r => r.blob());
```

## Bridging folderKey ↔ folderId

Maestro services return `folderKey` (GUID string), but Orchestrator services like `Processes.start()` require `folderId` (number). These are **completely different identifiers** — `parseInt(folderKey)` gives `NaN`.

**NEVER do this:**
```typescript
// WRONG — folderKey is a GUID like "a1b2c3d4-e5f6-...", parseInt returns NaN
const folderId = parseInt(process.folderKey, 10);
await processes.start(request, folderId);
```

**Correct pattern — resolve folderId from Orchestrator:**

```typescript
import { Processes } from '@uipath/uipath-typescript/processes';
import { MaestroProcesses } from '@uipath/uipath-typescript/maestro-processes';

// 1. Get the Maestro process (has folderKey and processKey, but no folderId)
const maestro = new MaestroProcesses(sdk);
const maestroProcesses = await maestro.getAll();
const target = maestroProcesses.find(p => p.name === 'My Process');
// target.folderKey = "a1b2c3d4-e5f6-..." (GUID)
// target.processKey = the Orchestrator release key (use for Processes.start())
// target.packageId = the NuGet package identifier (NOT the processKey!)

// 2. Get Orchestrator processes to find the matching folderId
const processes = new Processes(sdk);
const orchResult = await processes.getAll();
// ProcessGetResponse has BOTH folderKey and folderId
const orchProcess = orchResult.items.find(p => p.folderKey === target.folderKey);
const folderId = orchProcess?.folderId;

// 3. Now start the process with the correct fields:
//    - processKey comes from MaestroProcess.processKey (NOT packageId!)
//    - folderId comes from the Orchestrator bridge above
if (folderId) {
  await processes.start({ processKey: target.processKey }, folderId);
}
```

**Cache the mapping:** If your app frequently bridges between Maestro and Orchestrator, resolve the `folderKey → folderId` mapping once on load and cache it in a `Map<string, number>` or React state. Don't re-query on every operation.

```typescript
// Build a folderKey → folderId lookup map (do once)
const orchProcesses = await processes.getAll();
const folderMap = new Map<string, number>();
for (const p of orchProcesses.items) {
  if (p.folderKey && p.folderId) {
    folderMap.set(p.folderKey, p.folderId);
  }
}
// Use: folderMap.get(maestroProcess.folderKey) → folderId
```

## Usage Example

```typescript
import { useMemo } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Assets } from '@uipath/uipath-typescript/assets';
import { Processes } from '@uipath/uipath-typescript/processes';
import type { ProcessStartRequest } from '@uipath/uipath-typescript/processes';

function OrchestratorActions({ folderId }: { folderId: number }) {
  const { sdk } = useAuth();
  const assets = useMemo(() => new Assets(sdk), [sdk]);
  const processes = useMemo(() => new Processes(sdk), [sdk]);

  const listAssets = async () => {
    const result = await assets.getAll({ folderId, pageSize: 10 });
    return result.items;
  };

  const startProcess = async (processKey: string) => {
    const request: ProcessStartRequest = { processKey };
    const jobs = await processes.start(request, folderId);
    return jobs;
  };
}
```
