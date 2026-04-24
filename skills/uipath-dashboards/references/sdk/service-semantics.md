# Service semantics — the SDK's mental model

When deriving metrics, the agent must know how each SDK service *thinks*. This file captures the semantic model — what the service's canonical row looks like, what dimensions are filterable, what time axis (if any) it has, what the detail-view columns should be when drilling into a widget backed by this service.

This is the knowledge an expert human dashboards engineer would have. We encode it here so the generator reasons at that level.

## Per-service mental model

### Jobs (`@uipath/uipath-typescript/jobs`)

**Canonical row:** a `Job` — one invocation of a process (robot or agent) at a point in time.

**Primary identity:** `id` (globally unique).

**Semantic columns for detail views:**
- `id` → job GUID
- `processName` → what ran
- `packageType` → `Process` vs `Agent` (how to tell robot from agent)
- `state` → `Running`, `Pending`, `Faulted`, `Successful`, `Stopped`, etc.
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
- `dueDate` → SLA target

**Time axis:** yes — creation, assignment, completion, dueDate.

**Derived: SLA risk** = `dueDate - now()`. Negative = breached.

**What this service is GOOD for:** backlog, SLA health, completion rate, per-assignee load.

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
- `instanceId`, `status`, `stage`, `folderKey` (GUID)
- `startTime`, `endTime`, duration for completed

**Semantic columns (ProcessIncident):**
- `elementId` (which BPMN element flagged)
- `incidentType`, `severity`, `status`
- `createdTime`

**What this service is GOOD for:** long-running orchestration monitoring, incident boards, BPMN overlays.

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
