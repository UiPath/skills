# Service semantics — gotchas + opinion (NOT the SDK's full surface)

> **READ FIRST:** This file is **opinion + gotchas layered on top of the SDK** — it does NOT enumerate everything. The canonical list of services / classes / methods is in `<project>/.dashboard/sdk-manifest.json` produced by [../primitives/sdk-introspection.md](../primitives/sdk-introspection.md). Always introspect first; this file's per-service sections are illustrative and may lag the SDK by entire services (e.g., the SDK can grow Spans/Traces/Agents subpaths that aren't documented here yet).

## Semantic column renderers (state/status/priority/severity coloring)

State, status, priority, and severity columns must NOT render as plain text — UiPath products color-code them everywhere, and dashboards must match. The generator auto-applies `<StateBadge service={...} field={...} value={row.X} />` to detail-view columns whose `(service, fieldName)` matches the registry below.

| Service | Field | Renderer | Notes |
|---|---|---|---|
| `Jobs` / `JobInstances` | `state` | `<StateBadge service="Jobs" field="state" />` | Successful/Completed → success; Faulted/Stopped/Killed → destructive; Pending/Resumed/Suspended → warning; Running → info |
| `Tasks` | `priority` | `<StateBadge service="Tasks" field="priority" />` | High/Critical → destructive; Medium → warning; Low → neutral |
| `Tasks` | `status` / `state` | `<StateBadge service="Tasks" field="status" />` | Completed → success; Pending/Unassigned → warning; Rejected/Cancelled → destructive; InProgress → info |
| `CaseInstances` / `ProcessInstances` | `state` / `status` | `<StateBadge service="CaseInstances" field="state" />` | Completed/Closed/Resolved → success; Failed/Cancelled/Aborted → destructive; Paused/Suspended/Waiting → warning; Running/Open/InProgress → info |
| `ProcessIncidents` | `severity` | `<StateBadge service="ProcessIncidents" field="severity" />` | High/Critical → destructive; Medium → warning; Low → neutral; Info → info. Derive from `errorCode` if no `severity` field. |

The runtime mapping lives in `src/dashboard/chrome/StateBadge.tsx`. To add a new (service, field) pair, extend `toneFor()` in that file AND add a row above. For unmapped values, the badge falls back to the generic value-based heuristic (success/fail/warning/running keywords) and renders neutral if no match.

**Generator rule (detail views and ranked-table widgets):** when a column's `key` matches a registered field for the column's source service, emit:
```tsx
{ key: 'state', label: 'State', render: r => <StateBadge service="Jobs" field="state" value={r.state} /> }
```
NOT:
```tsx
{ key: 'state', label: 'State' }   // ← renders raw text, banned
```
Plain-text state cells are a generation bug — the validation pass catches them by grepping detail-view templates for `key:.*['"]state['"]` without an accompanying `<StateBadge>`.
>
> What lives HERE that the SDK's own types don't expose:
> - Pagination caps that produce 4xx (`pims: 500`, `autopilot: 100`)
> - Folder-id (`number`) vs folder-key (`string GUID`) inconsistency between services
> - "Filterable ≠ projected" gotchas (e.g., Releases `packageType` not OData-filterable)
> - Service base URL paths for raw HTTP debugging
> - Paginated vs non-paginated services (some return `T[]` directly)
> - Across-folders auto-routing behavior
> - Scope requirements that aren't in the type system (e.g., `ConversationalAgents Traces.Api`)
> - Object-shaped fields that crash React if rendered raw (`jobError`)
> - Empirical enum values when the SDK types use `string`
>
> What does NOT live here (read the .d.ts via the manifest instead):
> - Full method signatures
> - Complete projected-row field lists
> - Type aliases and interface bodies
>
> Treat the per-service sections below as **starting points** for services we've explored. Anything else — read the manifest, open the .d.ts, reason from first principles per [metric-derivation.md](metric-derivation.md).

## Service base URLs (for debugging and raw HTTP fallback)

| Service | Base path | Canonical `getAll` endpoint |
|---|---|---|
| Orchestrator (Jobs / Tasks / Assets / Queues / Buckets / Processes-Releases) | `orchestrator_/odata/` | `<Entity>` or `<Entity>/UiPath.Server.Configuration.OData.Get<Entity>AcrossFolders` |
| pims — CaseInstances | `pims_/api/v1/` | `instances?processType=CaseManagement` |
| pims — ProcessInstances | `pims_/api/v1/` | `instances?processType=ProcessManagement` |
| pims — ProcessIncidents | `pims_/api/v1/` | `incidents/summary` *(not `/incidents`; that returns 405)* |
| autopilot — Conversations | `autopilotforeveryone_/api/v1/` | `conversation` |
| Data Service — Entities | `dataservice_/api/data/v1/` | `entities` |
| Conversational Agent traces | `agents_/api/v1/` | `conversations` *(distinct from autopilot)* |

When a widget breaks with 404/405, first move is to verify the base path. Grep `node_modules/@uipath/uipath-typescript/dist/<service>/index.mjs` for template strings like `` `${PIMS_BASE}/api/v1/incidents/summary` `` — the real paths are always visible there.

## Paginated vs non-paginated services

Default to `fetchAllPaginated()` for Orchestrator OData (cursor-based with dedup-by-id). Exceptions:

| Service | Shape | Helper |
|---|---|---|
| `MaestroProcesses.getAll()` | returns `T[]` directly (no cursor) | `fetchPlainArray()` |
| `ProcessIncidents.getAll()` | returns `T[]` directly | `fetchPlainArray()` |
| `Cases.getAll()` (case *definitions*) | returns `T[]` directly | `fetchPlainArray()` |
| `CaseInstances.getAll()` (case *instances*) | paginated, 500-row cap | `fetchAllPims()` |
| `ProcessInstances.getAll()` | paginated, 500-row cap | `fetchAllPims()` |

Using the cursor-based paginator against `MaestroProcesses` / `ProcessIncidents` / `Cases` causes coercion bugs — it tries to iterate a plain array as if it were a `{items, nextCursor}` envelope.

**Shared backing storage:** `CaseInstances` and `ProcessInstances` hit the same `/pims_/api/v1/instances` endpoint with different `processType` query params. A dashboard querying both hits the same endpoint twice (different filters). The 500-row cap is shared — a dashboard with both services querying in parallel can still each get 500 rows, but they compete for the same backend.

## Folder-scoped services and the across-folders fallback

Orchestrator services that are traditionally folder-scoped (Buckets, Assets, Tasks, Queues, Jobs) raise `"A folder is required for this action."` when hit raw without a folder header. The SDK's `<service>.getAll()` without a `folderId` auto-routes to the `Get<Entity>AcrossFolders` OData action instead — which returns data the caller's token can see across all folders.

If you're debugging a widget and looking at the network tab, the URL you see may be `/orchestrator_/odata/Buckets/UiPath.Server.Configuration.OData.GetBucketsAcrossFolders` rather than `/odata/Buckets`. Both are the SDK's behavior; don't assume a 200 at one means the other works.

## Per-service mental model

### Jobs (`@uipath/uipath-typescript/jobs`)

**Canonical row:** a `Job` — one invocation of a process (robot or agent) at a point in time.

**Primary identity:** `id` (globally unique).

**Semantic columns for detail views:**
- `id` → job GUID
- `processName` → what ran
- `packageType` → `Process` vs `Agent` (how to tell robot from agent)
- `state` → canonical enum set:
  - `Running` — currently executing
  - `Pending` — queued, not yet started
  - `Successful` — completed without error (this is the "all-good" terminal state)
  - `Faulted` — runtime error (the strict fault signal)
  - `Stopped` — human-aborted before completion
  - `Suspended` — paused mid-run; expected to resume
  - Less common: `Killed`, `Cancelled`, `Terminated`, `Abandoned` — tenant-specific; grep `node_modules/@uipath/uipath-typescript/dist/jobs/` for the full set
- `startTime` / `endTime` → duration = `endTime - startTime`
- `createdTime` → when it was queued
- `folderName` → which folder scope
- `jobError` → fault details, **structured object** (not a string):
  ```ts
  { code?: string; title?: string; detail?: string; category?: string;
    status?: number|string; timestamp?: string }
  ```
  **CRITICAL — never render raw `jobError` as a React child.** React crashes with "Objects are not valid as a React child" on objects. Always flatten via `formatJobError(job.jobError)` from `_shared.ts` (produces a human string like `"Timeout — retries exhausted after 3 attempts"`).

**"What counts as faulted":**
`state === 'Faulted'` is the narrow definition. For error-rate dashboards, callers usually want a broader predicate that also includes `Stopped` and `Cancelled` (both are non-success outcomes from the user's perspective). Use `FAULT_STATES` and `isFaulted()` from `_shared.ts` rather than hand-writing the state check — this keeps the definition consistent across a dashboard. `Abandoned` / `Suspended` are typically EXCLUDED from error counts.

**Time axis:** yes — `CreationTime`, `StartTime`, `EndTime`. Filter on server-side PascalCase (see `invariants.md §2`).

**Agent filter:** `ProcessType eq 'Agent'` (server field; NOT `packageType` which is the client-side rename).

**Pagination:** cursor-based via `{ value: string }` object (see `invariants.md §1`). Dedup by `id` on busy tenants.

**What this service is GOOD for:** invocation volume, error rates, latency distributions, per-process breakdowns, agent activity. Anything about *what ran when with what outcome*.

**What it's NOT for:** queue-item-level events (not in SDK), conversation content (use `ConversationalAgent`), policy violations (not in SDK).

---

### Processes (`@uipath/uipath-typescript/processes`)

**Canonical row:** a `Process` — a published package at some version, deployable to folders.

**Primary identity:** `key` (process key GUID).

**Semantic columns:**
- `key` / `name` / `version`
- `packageType` → `Process` | `Agent` | `TestAutomation` | etc.
- `folderName` / `folderId` → where it's visible
- `createdTime` / `lastModificationTime`

**Time axis:** weak — packages have created/modified timestamps but "processes over time" isn't typically the question. Treat as a **snapshot** service.

**What this service is GOOD for:** inventory. "What's published?" "How many agents exist?" "Breakdown by package type."

**What it's NOT for:** execution data (that's Jobs). A published Process with zero Jobs is a valid state.

---

### Tasks (`@uipath/uipath-typescript/tasks`)

**Canonical row:** a `Task` — an Action Center action item awaiting human decision.

**Primary identity:** `id`.

**Semantic columns:**
- `id` / `title`
- `status` → `Unassigned`, `Pending`, `Completed`, etc.
- `priority` → `Low` | `Medium` | `High` | `Critical`
- `assignedToUser.name` → who owns it
- `creationTime` / `lastAssignedTime` / `completionTime`
- `taskDefinitionName` → type of task
- `taskSlaDetail` → **SLA status lives here, NOT on a `dueDate` field** (the raw response has no `dueDate`):
  ```ts
  taskSlaDetail?: {
    status?: 'Overdue' | 'OverdueSoon' | 'OverdueLater' | 'CompletedInTime';
    dueTime?: string;  // ISO timestamp
  }
  ```

**Time axis:** yes — creation, assignment, completion, and `taskSlaDetail.dueTime`.

**Derived: SLA status** — use `taskSlaStatusOf(task)` from `_shared.ts`. Returns one of `Overdue | OverdueSoon | OverdueLater | CompletedInTime | Unknown`. Never compute `dueDate - now()` directly — the `dueDate` field doesn't exist on the raw response; the SLA status is already bucketed server-side.

**What this service is GOOD for:** backlog, SLA health via `taskSlaStatusOf`, completion rate, per-assignee load.

---

### Queues (`@uipath/uipath-typescript/queues`)

**Canonical row:** a `QueueDefinition` — NOT queue items.

**Primary identity:** `id` / `name`.

**Semantic columns:** `id`, `name`, `description`, `folderName`, `creationTime`.

**Time axis:** snapshot (the queue's definition is stable; queue *items* have activity but they're not in the SDK).

**What this service is GOOD for:** queue inventory.

**What it's NOT for:** queue-item throughput, SLA, completion rates — those require raw Orchestrator OData calls outside the SDK. See `intent-map.md § "Pattern: data the user wants isn't in the SDK"`.

---

### Assets (`@uipath/uipath-typescript/assets`)

**Canonical row:** an `Asset` — a named configuration value.

**Primary identity:** `id` / `name`.

**Semantic columns:** `name`, `valueType`, `valueScope`, `folderName`, `creationTime`.

**Time axis:** snapshot.

**What this service is GOOD for:** asset inventory, valueType distribution.

---

### Buckets (`@uipath/uipath-typescript/buckets`)

**Canonical row:** a `Bucket` (definition) — and via `getFileMetaData()`, file-level rows.

**Two-level access:** bucket list is snapshot; file-level reads require `(bucketId, folderId)`.

**Semantic columns (bucket):** `id`, `name`, `description`, `folderName`.
**Semantic columns (file):** `fullPath`, `size`, `lastModified`, `isDirectory`.

**What this service is GOOD for:** bucket inventory; storage growth if you iterate files.

---

### Cases (`@uipath/uipath-typescript/cases`) and CaseInstances

**Two rows:** case definition (template) and case instance (running).

**Semantic columns (CaseInstance):**
- `caseAppKey` → which case type
- `status` → `Open` | `Paused` | `Closed`
- `stage` → current stage name
- `openTime` / `closedTime`
- `createdBy`

**Folder identity:** uses `folderKey` (GUID string), NOT `folderId` (int). See `invariants.md §6`.

**Time axis:** yes — open/close timestamps; stages are flow-ordered.

**What this service is GOOD for:** pipeline funnel (Open → Paused → Closed), close rate, per-type volume, stage flow (Sankey).

---

### MaestroProcesses (`@uipath/uipath-typescript/maestro-processes`)

**Three rows:** `MaestroProcess` (definition), `ProcessInstance` (running long-lived), `ProcessIncident` (issue).

**Semantic columns (ProcessInstance):**
- `instanceId`, `folderKey` (GUID)
- `latestRunStatus` → status enum. Observed values: `'Running'`, `'Completed'`, `'Faulted'`, `'Paused'`, `'Cancelled'`. Use `.toLowerCase()` if comparing — SDK's casing is inconsistent across tenants.
- `startTime`, `endTime`, duration for completed
- NO `stage` field on the raw response. Stage information has to be derived from `getStages()` / `getExecutionHistory()` for a specific instance.

**Semantic columns (CaseInstance):**
- `instanceId`, `caseAppKey`, `folderKey`
- `latestRunStatus` → same enum as ProcessInstance. For case pipeline KPIs, map `.toLowerCase().includes('…')` → `Open` | `Paused` | `Closed`:
  - `running` / `inprogress` / `pending` → Open
  - `paused` / `suspended` → Paused
  - `completed` / `closed` / `cancelled` / `faulted` → Closed
- `openTime` / `closedTime`

**Semantic columns (ProcessIncident):**
Actual raw response shape (`ProcessIncidentGetAllResponse`):
```ts
{
  count: number;
  errorMessage: string;
  errorCode: string;
  firstOccuranceTime: string;  // ISO
  processKey: string;
}
```
Previous drafts of this doc claimed a `severity` field — it does NOT exist. Group-by for severity-like breakdowns uses `errorCode` (or derive a severity classifier from the `errorCode` prefix at widget-generation time; document the classification in the widget's description).

**What this service is GOOD for:** long-running orchestration monitoring, incident boards, BPMN overlays. NOT for severity-first dashboards unless you map `errorCode → severity` yourself.

---

### Entities (`@uipath/uipath-typescript/entities`) + ChoiceSets

**Canonical rows:** entity schemas + entity records (via `getAllRecords(entityId)` or `queryRecordsById(...)`).

**Schema-first:** users define the shape; you drill-in by entity-id.

**What this service is GOOD for:** reporting over custom Data Service datasets — any user-defined schema becomes a queryable table.

---

### ConversationalAgent / Exchanges / Messages (`@uipath/uipath-typescript/conversational-agent`)

**Three rows:** Agent, Exchange (conversation session), Message (utterance).

**Scope:** `ConversationalAgents Traces.Api` scope; different from Orchestrator scopes.

**Semantic columns (Exchange):** `id`, `createdTime`, `agentId`, `userId`, `feedback`, `toolCalls`, `error`.

**What this service is GOOD for:** conversation volume, feedback distribution, tool usage, per-agent activity.

**Gotcha:** UI-initiated agent runs may not appear via this SDK — they appear in Jobs. For "agent runs" prefer Jobs filtered by `ProcessType eq 'Agent'`.

**Silent-failure trap (scope):** if the user's PAT doesn't include `ConversationalAgents Traces.Api` scope, the endpoint may return `{data: []}` or a 302 redirect instead of a 403. Widgets then show "No conversations on record." indistinguishable from a legitimately empty tenant. When generating Conversation widgets:
1. Log the expected scope to console at hook init so developers can diagnose from DevTools.
2. Mirror the scope requirement into the generated `SECURITY.md`: *"Conversation widgets need the `ConversationalAgents Traces.Api` scope. Standard Orchestrator PATs do NOT include it — generate a scoped PAT from the conversational-agent portal."*
3. If possible, add a lightweight scope-probe at mount that hits a trivial endpoint and logs "scope missing" on 4xx/redirect.

---

## Cross-cutting semantics

### Folder identity (critical — `invariants.md §6`)

Services disagree on folder identity format:

| Uses `folderId: number` | Uses `folderKey: string` (GUID) |
|---|---|
| Jobs, Processes, Assets, Queues, Tasks, Buckets | Cases, MaestroProcesses |

Don't interchange. The detail view's filter must match the service's expected type.

### Time-bucketing defaults

| Window | Default bucket |
|---|---|
| ≤ 24h | hourly (24 slots) |
| 1d – 14d | daily |
| 2w – 8w | daily or weekly |
| > 8w | weekly or monthly |

Zero-fill ALL buckets per `invariants.md §7`.

### Empty-state phrasing per service

Detail views use service-aware empty messages. Agent derives them from the filter, not a fixed string.

| Service | Empty phrasing template |
|---|---|
| Jobs | "No agent invocations matching [filter] in [window]." |
| Tasks | "No tasks matching [filter] currently." |
| Cases | "No cases matching [filter] in [window]." |
| Processes | "No processes matching [filter]." |
| Incidents | "No process incidents matching [filter] in [window]." |

## Using this file

`data-router.md` references this file when synthesizing SDK calls. `detail-views.md` references it for column derivation. `metric-derivation.md` uses it as the "what service owns this?" leg of the four-axis decomposition.

When the generator writes a detail view, it does NOT hardcode columns. It reads this file's "Semantic columns" section for the metric's service and produces a column list that covers identity + time + domain-specific dimensions.
