# Orchestrator Reference

## Imports

```typescript
import { Assets } from '@uipath/uipath-typescript/assets';
import { Queues } from '@uipath/uipath-typescript/queues';
import { Buckets } from '@uipath/uipath-typescript/buckets';
import { Processes } from '@uipath/uipath-typescript/processes';
```

## Note: Folder-Scoped Services

Assets, Queues, Buckets, and Processes are folder-scoped. Many methods require a `folderId` parameter.

**No bound methods**: These are read-only response objects. Unlike Entities, Tasks, or Maestro instances, the responses from Orchestrator services do not have attached methods. Use the service directly for all operations.

## Types to Import

```typescript
// Assets
import type {
  AssetGetResponse,
  AssetGetAllOptions,
  AssetGetByIdOptions,
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
  ProcessStartRequest,
  ProcessStartResponse,
} from '@uipath/uipath-typescript/processes';
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

`ProcessGetResponse` fields: `key`, `packageKey`, `packageVersion`, `isLatestVersion`, `description`, `name`, `packageType`, `targetFramework`, `robotSize`, `autoUpdate`, `id`, `folderId`, `folderName`, `folderKey`, `createdTime`, `lastModifiedTime`.

### start(request: ProcessStartRequest, folderId: number, options?: RequestOptions)

Returns `Promise<ProcessStartResponse[]>`. The `request` must include either `processKey` or `processName`. Optional fields: `strategy`, `robotIds`, `jobsCount`, `inputArguments`, `jobPriority`.

`ProcessStartResponse` fields: `key`, `startTime`, `endTime`, `state`, `source`, `processName`, `type`, `id`, `folderId`.

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
