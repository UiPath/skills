# OAuth Scopes Reference

Which OAuth scopes a Coded App needs, and where to look them up.

Use this reference to:
1. Determine which scopes to include in the `scope` field of `uipath.json`
2. Determine which scopes to add to the UiPath External Application

**Note:** Broader scopes cover granular ones (e.g., `OR.Assets` covers `OR.Assets.Read`). Use the most specific scope that satisfies the operations the app performs.

> **Update scopes WHEN you add the feature.** Any new service call — a write op, an action-causing method (`Jobs.stop`/`resume`/`restart`, `Tasks.complete`/`assign`, `ProcessInstances.cancel`, `Exchanges.createFeedback`, etc.), or a call to a service the app hasn't used before — may need a scope broader than what the current `scope` field in `uipath.json` carries. Look up the method's scope (below) before shipping the feature. The External Application registration must also allow the scope; if not, the token request is rejected entirely (see [oauth-client-setup.md](oauth-client-setup.md)).

## Per-method scope lookup

The per-method scope table ships **inside the SDK package**. Read the installed copy — it is version-exact and offline:

`node_modules/@uipath/uipath-typescript/docs/oauth-scopes.md`

Required scopes can change between SDK versions, so read the installed copy rather than a CDN `@latest` that may not match the installed version. If the installed SDK predates the file, upgrade the SDK. This skill deliberately does NOT duplicate the per-method table.

What the shipped table does NOT cover (skill knowledge, below): widget scopes and the task-level bundles.

## Common Scope Bundles

Task-level bundles — what to put in the `uipath.json` `scope` field for a given feature set. Start here; consult the per-method table for methods outside these bundles.

| App uses... | Minimum scopes needed |
|---|---|
| Orchestrator Assets (read) | `OR.Assets.Read` (`OR.Assets` to also write asset values) |
| Orchestrator Queues (read) | `OR.Queues.Read` |
| Orchestrator Buckets (read + upload) | `OR.Buckets` (read-only browsing: `OR.Buckets.Read`) |
| Orchestrator Attachments (read) | `OR.Folders.Read` |
| Orchestrator Tasks (read + complete) | `OR.Tasks` |
| Orchestrator Processes (list + start) | `OR.Execution OR.Jobs` |
| Orchestrator Jobs (list + read output) | `OR.Jobs.Read OR.Folders.Read` (add `OR.Folders.Read` so `Jobs.getOutput()` can resolve file-type output arguments via Attachments) |
| Data Fabric (read-only) | `DataFabric.Schema.Read DataFabric.Data.Read` |
| Data Fabric (read + write) | `DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write` |
| Maestro full access | `PIMS OR.Execution.Read` |
| Maestro analytics / insights dashboards (top run/fault/duration counts, status timelines, SLA) | add `Insights.RealTimeData Insights OR.Folders.Read` (SLA summaries also need `PIMS`) |
| Conversational Agent | `OR.Execution OR.Folders OR.Jobs ConversationalAgents Traces.Api` (add `OR.Users` for user-settings read/write) |
| Agent Feedback | `Traces.Api` (every method) |
| Insights RTM (Agents, Agent Traces, Agent Memory, Governance, Maestro Insights) | `Insights Insights.RealTimeData OR.Folders.Read` |
| Maestro SLA (CaseInstances SLA summary) | `Insights Insights.RealTimeData OR.Folders.Read PIMS` |
| Generic trace spans (`Traces.getById` / `getSpansByIds`) | `Traces.Api` (+ `Insights Insights.RealTimeData`) |

## Widgets

Scopes required by `@uipath/ui-widgets-*` React components. The widget's own runtime API calls are listed here — add scopes from the per-method table for any additional SDK calls the host app makes.

### Validation Station (`@uipath/ui-widgets-validation-station`)

| Required Scope | Why |
|----------------|-----|
| `OR.Buckets` | Widget reads the document and extraction artifacts from a storage bucket and uploads the validated payload during save. Read-only `OR.Buckets.Read` is insufficient — the upload step requires write. |
| `OR.Tasks` or `OR.Tasks.Write` | Required when the host app calls `task.complete()` in `onSaveComplete` (action apps, and web apps that complete the task on save). |

See [widgets/validation-station.md](widgets/validation-station.md) for the full integration guide.

### Conversational Agent Chat (`@uipath/ui-widgets-conversational-agent-chat`)

| Required Scope | Why |
|----------------|-----|
| `OR.Execution OR.Folders OR.Jobs ConversationalAgents` | Agent resolution, conversation create/list, WebSocket session, attachment upload — the Conversational Agent bundle above. |
| `Traces.Api` | The widget's feedback flow (`createFeedback` on thumbs up/down). Omitting it breaks feedback silently. |

See [widgets/conversational-agent-chat.md](widgets/conversational-agent-chat.md) for the full integration guide.

### DataTable (`@uipath/ui-widgets-datatable`)

| Required Scope | Why |
|----------------|-----|
| `DataFabric.Schema.Read` | Widget reads the entity schema to build columns. |
| `DataFabric.Data.Read` | Record listing, choice-set/foreign-key resolution, file download. |
| `DataFabric.Data.Write` | Commit/insert/delete flows and file upload/remove — the grid ships with editing enabled. Omit only if every column is set `editable: false`. |

See [widgets/datatable.md](widgets/datatable.md) for the full integration guide.

### Multi-File Upload (`@uipath/ui-widgets-multi-file-upload`)

| Required Scope | Why |
|----------------|-----|
| `OR.Buckets` | Widget uploads files to a storage bucket — a write; read-only `OR.Buckets.Read` is insufficient. |

See [widgets/multi-file-upload.md](widgets/multi-file-upload.md) for the full integration guide.

### PDF Viewer (`@uipath/ui-widgets-pdf-viewer`)

| Required Scope | Why |
|----------------|-----|
| `OR.Buckets.Read` (or `OR.Buckets`) | Bucket sources — the widget resolves a read URI and fetches the document. |
| `DataFabric.Data.Read` | Entity sources — the widget downloads the record's file attachment. |

Only the scope for the source shape(s) the app actually uses; `url`/`data` sources need no scopes. See [widgets/pdf-viewer.md](widgets/pdf-viewer.md) for the full integration guide.

### External Auth (`@uipath/ui-widgets-external-auth`)

No UiPath scopes — the widget makes no UiPath API calls (it starts logins at external IdPs). See [widgets/external-auth.md](widgets/external-auth.md).
