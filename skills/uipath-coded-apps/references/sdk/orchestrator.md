# Orchestrator — Traps & Server Behavior

Signatures/params/examples: `dist/assets/index.d.ts`, `dist/queues/index.d.ts`, `dist/buckets/index.d.ts`, `dist/processes/index.d.ts`, `dist/jobs/index.d.ts`, `dist/attachments/index.d.ts`. Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Scope pairing warning:** `Jobs.getOutput()` resolves file-type output arguments through the Attachments service internally — the app needs `OR.Folders` (or `OR.Folders.Read`) **in addition to** its Jobs scope, or the call 403s. Do not assume one scope per service; check the shipped table per method.

## Job classification — agent vs process vs app

An agent job is identified by **`packageType === 'Agent'`** — both when reading response objects and in OData `filter` strings (the SDK rewrites SDK field names to API names in `filter`/`orderby`/`select`/`expand` automatically).

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

Job latency ← `endTime − startTime` (both timestamps; `endTime` is null while `Running` — a server behavior the types show only as `string | null`).

Server-side filters (SDK field names — the SDK rewrites them to API names):
- Agent jobs: `getAll({ filter: "packageType eq 'Agent'", orderby: 'createdTime desc' })`
- Faulted agent jobs: `getAll({ filter: "State eq 'Faulted' and packageType eq 'Agent'" })`
- Reading results: `result.items.filter(j => j.packageType === 'Agent')`

### OData filter field names

The SDK rewrites SDK field names inside `filter` / `orderby` / `select` / `expand` to raw API names before sending (`processName → releaseName`, `createdTime → creationTime`, `packageType → processType`); raw API names pass through unchanged, so either spelling works. `folderId` is never a `$filter` field — folder scoping travels via header.

### Recipe — jobs for a named agent → its most-recent trace's spans

The bridge from a clicked agent to its spans (e.g. a `rowLink` table's `fetchDetailByKey`):

```ts
import type { MetricDetailByKeyFn } from '@/lib/metric-contract'

export const fetchDetailByKey: MetricDetailByKeyFn = async (sdk, agentName) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const jobs = (await new Jobs(sdk).getAll({ filter: "packageType eq 'Agent'", orderby: 'createdTime desc' }))?.items ?? []
  const job = jobs.find(j => j.processName === agentName)   // name match is client-side (no server-side name filter)
  if (!job?.traceId) return []
  return await new AgentTraces(sdk).getSpansByTraceId(job.traceId)   // Job carries traceId (see traces.md)
}
```

## Bucket file listing — which method

`getFiles` (folder-aware `BucketFile` items, regex filtering) vs `getFileMetaData` (flat `BlobItem` list by `prefix`): prefer **`getFiles`** for directory-style browsing. Neither method's JSDoc mentions the other. Note `JobGetResponse.process` is populated only via `expand` (its JSDoc, unlike `machine`/`robot`, does not say so).

## Attachments Service

Cross-artifact role the types don't show: Coded Action Apps resolve a `type: "file"` input — the file reference handed in by the automation (Maestro / Agent / RPA) — into bytes via `Attachments.getById()` → `blobFileAccess` (signed URL + headers). `Jobs.getOutput()` uses the same service internally for file-type outputs (see scope pairing warning above). When `blobFileAccess.requiresAuth` is `true`, pass `blobFileAccess.headers` on the download request.

```typescript
import { Attachments } from '@uipath/uipath-typescript/attachments';

const attachment = await new Attachments(sdk).getById('<attachmentId>');
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
