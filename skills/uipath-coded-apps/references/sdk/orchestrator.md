# Orchestrator Reference — Scopes, Conventions, Traps

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/assets/index.d.ts`, `dist/queues/index.d.ts`, `dist/buckets/index.d.ts`, `dist/processes/index.d.ts`, `dist/jobs/index.d.ts`, `dist/attachments/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

## Imports

```typescript
import { Assets } from '@uipath/uipath-typescript/assets';
import { Queues } from '@uipath/uipath-typescript/queues';
import { Buckets } from '@uipath/uipath-typescript/buckets';
import { Processes } from '@uipath/uipath-typescript/processes';
import { Jobs } from '@uipath/uipath-typescript/jobs';
import { Attachments } from '@uipath/uipath-typescript/attachments';
```

Types, options, and enums export from the same subpath as their service class.

## Scopes

- Assets: `OR.Assets` or `OR.Assets.Read`
- Queues: `OR.Queues` or `OR.Queues.Read`
- Buckets: `OR.Buckets` or `OR.Buckets.Read`; `OR.Buckets.Write` for `deleteFile`
- Processes: `OR.Execution` / `OR.Execution.Read`; `OR.Jobs` / `OR.Jobs.Write` for `start`
- Jobs: `OR.Jobs` or `OR.Jobs.Read`
- Attachments: `OR.Folders` or `OR.Folders.Read`
- `Jobs.getOutput()` uses Attachments internally to resolve file-type output arguments — if you call `Jobs.getOutput()` you must add `OR.Folders` (or `OR.Folders.Read`) to the app's scopes in addition to `OR.Jobs`

## Traps

### Folder-scoped services

Assets, Queues, Buckets, and Processes are folder-scoped. Many methods require a `folderId` parameter.

### Attached methods

`Jobs.getById()` and `Jobs.getAll()` items return response objects with attached methods (`getOutput()`, `stop()`, `resume()`, `restart()`) bound to the job's `key` and `folderId`, so you don't need to pass them again — prefer them over re-calling the service with ids. The full list is the `JobMethods` type in the `.d.ts`. Assets, Queues, Buckets, Processes, and Attachments responses do **not** have attached methods — use the service directly.

### `getByName` folder identifiers

`Assets.getByName`, `Processes.getByName`, and `Buckets.getByName` accept `FolderScopedOptions` — supply one of `folderId`, `folderKey`, or `folderPath` (e.g., `'Shared/Finance'`). If multiple are supplied, server precedence is `folderPath` > `folderKey` > `folderId`. Throws `NotFoundError` if nothing matches.

### `getFiles` vs `getFileMetaData` (Buckets)

`getFiles` returns `BucketFile` items (folder-aware — each includes `isDirectory` — supports regex filtering) and is folder-scoped via `FolderScopedOptions`. `getFileMetaData` returns flat `BlobItem` items by `prefix` and takes a positional `folderId`. Prefer `getFiles` for directory-style browsing.

### Jobs service behavior

- `Jobs.getById()`: **Note:** `id` is a `string` here (not a `number` like Assets/Queues/Processes).
- `getOutput()` returns the job's parsed output arguments, or `null` if unavailable. Use after a job has finished; output is not populated while the job is still running.
- `stop()` takes an array of job keys (pass an array even for a single job). Throws if any keys cannot be resolved. `StopStrategy.SoftStop` (default, graceful) or `StopStrategy.Kill` (immediate).
- `resume()` resumes a job currently in `Suspended` state.
- `restart()` returns a **new** job with a new `key`, in `Pending` state. The original job must be in a final state (`Successful`, `Faulted`, or `Stopped`). Inputs are inherited from the original.
- `Processes.start()`: the `request` must include either `processKey` or `processName`.
- `JobGetResponse`: the `machine`, `robot`, and `process` fields are populated only when requested via `expand`.

## Job classification — agent vs process vs app

An agent job is identified by **`packageType === 'Agent'`** on the SDK response object. The SDK's `JobMap` renames the raw API field `ProcessType → packageType`, so a raw job with `ProcessType: "Agent"` arrives as `packageType: "Agent"`.

| Where | Field | Agent job value |
|-------|-------|-----------------|
| SDK response object (`fnBody` reads this) | `packageType` | `"Agent"` |
| OData server-side `filter` string (raw API name) | `ProcessType` | `"Agent"` |

> **Do NOT use `sourceType` to find agent jobs.** `sourceType` (raw `Source` / `JobSourceType`) is the **trigger origin** — `Manual`, `Schedule`, `Queue`, `Agent`, `Apps`, `HttpTrigger`, … An agent job can be triggered manually (`sourceType: "Manual"`), and `sourceType: "Agent"` only means "started by an agent source," which is a different thing. Filtering on `sourceType === 'Agent'` is wrong in both directions.

**Example response** (`Jobs.getAll()` `.items`) — an agent job next to a standard RPA job. The agent job is `packageType: "Agent"`. Note `sourceType` is the *trigger origin* (here both happen to differ) and does NOT identify an agent:

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

Field mappings (raw → SDK, from `JobMap`): `releaseName → processName`, `creationTime → createdTime`, `organizationUnitId → folderId`. Job latency ← `endTime − startTime` (both timestamps; `endTime` is null while `Running`).

Server-side filters (use the raw field name `ProcessType` in the OData string):
- Agent jobs: `getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' })`
- Faulted agent jobs: `getAll({ filter: "State eq 'Faulted' and ProcessType eq 'Agent'" })`
- Reading results: `result.items.filter(j => j.packageType === 'Agent')` (client-side, mapped field name)

### Filterable vs read-only Job fields

A field appearing in the response does **NOT** make it valid in an OData `$filter`. The SDK's mapped (renamed) response fields are **read-only** — filtering on them throws `Invalid OData query options … Could not find a property named '<field>'` at request time (invisible to `tsc`).

| Read-only (response only — NEVER in `$filter`) | Filter on the raw field instead |
|---|---|
| `processName` (← `releaseName`) | match **client-side**: `items.filter(j => j.processName === name)` |
| `createdTime` (← `creationTime`) | `CreationTime` (e.g. `orderby: 'CreationTime desc'`) |
| `folderId` (← `organizationUnitId`) | folder is scoped via header, not `$filter` |
| `packageType` (← `ProcessType`) | `ProcessType` |

Safe `$filter` fields: **`ProcessType`**, **`State`**, **`CreationTime`**, **`StartTime`**. To find a specific agent's jobs, filter `ProcessType eq 'Agent'` and match the name **client-side** on `processName` — there is no server-side name filter.

### Recipe — jobs for a named agent → its most-recent trace's spans

The bridge from a clicked agent to its spans (e.g. a `rowLink` table's `fetchDetailByKey`):

```ts
import type { MetricDetailByKeyFn } from '@/lib/metric-contract'

export const fetchDetailByKey: MetricDetailByKeyFn = async (sdk, agentName) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const jobs = (await new Jobs(sdk).getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' }))?.items ?? []
  const job = jobs.find(j => j.processName === agentName)   // client-side match — processName is read-only
  if (!job?.traceId) return []
  return await new AgentTraces(sdk).getSpansByTraceId(job.traceId)   // Job carries traceId (see traces.md)
}
```

## Attachments Service

Standalone service for retrieving an Orchestrator attachment's metadata and a signed URL for downloading the blob. Coded Action Apps use this to resolve a `type: "file"` input — the file reference handed in by the automation (Maestro / Agent / RPA) — into downloadable bytes. `Jobs.getOutput()` also uses it internally to resolve file-type output arguments (see Scopes above).

This service exposes **only** `getById` — there is no `getAll`, no create, and no delete. `id` is the attachment **UUID** (string) — not a number. Throws `ValidationError` if `id` is empty.

Resolve a `file`-typed input to its bytes via `blobFileAccess` (the signed URL + headers). Respect `requiresAuth` — when `true`, pass `headers` on the download request:

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
