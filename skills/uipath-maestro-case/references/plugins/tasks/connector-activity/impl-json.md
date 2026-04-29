# connector-activity task — Implementation (Direct JSON Write)

> **Phase split.** Runs across both phases. Phase 2a writes `data.type-id` + `data.connection-id` only; **do NOT call `is resources describe` in 2a**. Phase 2b runs `is resources describe`, writes `data.inputs[]` / `data.outputs[]` schema, then binds values. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch connector metadata via CLI, then write the task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md`.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"c7ce0a96-2091-3d94-b16f-706ebb1eb351"` |
| `connection-id` | `"bc095c1f-671f-4669-8634-b7164fa46aa0"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"send-mail-v2"` |
| `input-values` | `{"body":{"message":{"toRecipients":"user@example.com"}}}` (already resolved IDs) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Configuration Workflow

> **Each connector task runs its own `get-connection`.** Even when two tasks share the same `connection-id`, the Entry and Config objects differ between activity and trigger types (`httpMethod`, `activityType`, `inputMetadata`, etc.). Never reuse another task's CLI output.

### Step 1 — Get connection details + Entry

```bash
uip case registry get-connection \
  --type typecache-activities \
  --activity-type-id "<type-id>" --output json
```

**Save:**

| Variable | Source | Example |
|---|---|---|
| `Entry` | `.Data.Entry` (full object) | `{ displayName: "Send Email", svgIconUrl: "icons/...", ... }` |
| `Config` | `.Data.Config` | `{ connectorKey, objectName, httpMethod, activityType, version }` |
| `folderKey` | `.Data.Connections[selected].folder.key` | `"87fd6cec-..."` |
| `folderName` | `.Data.Connections[selected].folder.name` | `"57d6e3b0's workspace"` |
| `connectorName` | `.Data.Connections[selected].connector.name` | `"Microsoft Outlook 365"` |
| `connectionName` | `.Data.Connections[selected].name` | `"song.zhao@uipath.com #1"` |

### Step 2 — Get enriched metadata + outputs

```bash
uip case tasks describe --type connector-activity \
  --id "<type-id>" \
  --connection-id "<connection-id>" --output json
```

**Save:**

| Variable | Source | Example |
|---|---|---|
| `enrichment.operation` | `.Data.enrichment.operation` | `"SendEmailV2"` |
| `enrichment.path` | `.Data.enrichment.path` | `"/hubs/productivity/send-mail-v2"` |
| `enrichment.inputMetadata` | `.Data.enrichment.inputMetadata` | `{"type":"multipart","multipart":{"bodyFieldName":"body"}}` |
| `enrichment.multipartParameters` | `.Data.enrichment.multipartParameters` | `[{"name":"file","dataType":"file"},{"name":"body","dataType":"string"}]` |
| `enrichment.configuration` | `.Data.enrichment.configuration` | `"=jsonString:{\"essentialConfiguration\":{...}}"` |
| `outputs` | `.Data.outputs` | Array with response schema + Error |
| `inputs` | `.Data.inputs` | Array — includes `pathParameters`, `queryParameters`, `file` entries when applicable |

> **All enrichment fields are critical.** Without `inputMetadata`, multipart activities fail. Without `configuration`, the FE strips enrichment data on re-save. Without `multipartParameters`, the runtime cannot parse multipart request bodies (400 "Unable to parse multipart body").

> **Do NOT derive `path` or `operation` from `Config.objectName`.** The resolved values differ (e.g., `SendEmailV2` not `send-mail-v2`, `/hubs/productivity/send-mail-v2` not `/send-mail-v2`).

## Step 3 — Build `data` and write to caseplan.json

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`). Create the task skeleton:

```json
{
  "id": "<taskId>",
  "type": "execute-connector-activity",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.ActivityExecution"
  }
}
```

Then populate each section:

### 3a. Root-level bindings

Create 2 entries in `root.data.uipath.bindings[]` per [bindings/impl-json.md](../../variables/bindings/impl-json.md). Connector tasks use `resource: "Connection"`:

| Binding | `propertyAttribute` | `default` |
|---|---|---|
| ConnectionId | `"ConnectionId"` | `connection-id` (from tasks.md) |
| folderKey | `"folderKey"` | `folderKey` (from Step 1) |

Both share `resourceKey` = `connection-id`. ID generation: `b` + 8 alphanumeric chars.

### 3a-post. IS connection cache

After writing root bindings in § 3a, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `get-connection` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 (after all connector tasks), not per-task. See [bindings-v2-sync.md § When to Run](../../../bindings-v2-sync.md).

### 3b. `data.context[]`

No `operation`, `_label`, or `designTimeMetadata` for activities — the FE only adds `operation` to context for triggers. Activity tasks use `enrichment.operation` inside `essentialConfiguration` only.

Every context entry MUST include `"type": "string"` (or `"type": "json"` for metadata). Omitting `type` causes Studio Web to fail to render the case.

| `name` | `type` | `value` source | Notes |
|---|---|---|---|
| `connectorKey` | `"string"` | `connector-key` (tasks.md) | |
| `connection` | `"string"` | `=bindings.<connBindingId>` | Reference — not raw UUID |
| `resourceKey` | `"string"` | `connection-id` (tasks.md) | |
| `folderKey` | `"string"` | `=bindings.<folderBindingId>` | Reference — not raw UUID |
| `objectName` | `"string"` | `object-name` (tasks.md) | |
| `method` | `"string"` | `Config.httpMethod` (Step 1) | |
| `path` | `"string"` | `enrichment.path` (Step 2) | From Swagger — includes hub prefix |
| `metadata` | `"json"` | *(see §3c)* | Uses `body` not `value` |

### 3c. `metadata` context entry body

Key order must match FE: `activityPropertyConfiguration` → `activityMetadata` → `inputMetadata` → `telemetryData`. No `designTimeMetadata` or top-level `errorState`.

```json
{
  "activityPropertyConfiguration": {
    "multipartParameters": "<enrichment.multipartParameters from Step 2 — omit key entirely if absent>",
    "configuration": "<enrichment.configuration from Step 2 — copy as-is>",
    "uiPathActivityTypeId": "<type-id>",
    "errorState": { "issues": [] }
  },
  "activityMetadata": {
    "activity": "<Entry from Step 1 — copy full object>"
  },
  "inputMetadata": "<enrichment.inputMetadata from Step 2 — copy as-is, or {} if absent>",
  "telemetryData": {
    "connectorKey": "<connector-key>",
    "connectorName": "<connectorName from Step 1>",
    "operationType": "<see table below>",
    "objectName": "<object-name>",
    "objectDisplayName": "<Entry.displayName>",
    "primaryKeyName": ""
  }
}
```

**`telemetryData.operationType`** — derived from `Config.httpMethod`:

| httpMethod | operationType |
|---|---|
| `GET` | `"read"` |
| `POST` | `"create"` |
| `PUT` | `"replace"` |
| `PATCH` | `"update"` |
| `DELETE` | `"delete"` |

### 3d. `activityPropertyConfiguration.configuration`

Copy `enrichment.configuration` from Step 2 as-is. The CLI pre-builds this `=jsonString:` string using the full `Entry.configuration` as `instanceParameters` and httpMethod→verb mapping for `operation` — matching what Studio Web's DAP produces.

> **Do NOT hand-construct this string.** Previous versions of this doc had a manual template that produced incorrect `instanceParameters` (missing `httpMethod`, `supportsStreaming`, `subType`) and wrong `operation` values. The CLI now returns the correct pre-built string.

> If `enrichment.configuration` is absent (older CLI version), defer to skeleton task per Rule 7 — do not hand-construct.

### 3e. `data.inputs[]`

Build inputs from `tasks describe` Step 2 output (`.Data.inputs`) and `input-values` from `tasks.md`. The `tasks describe` response already includes all required input entries (`pathParameters`, `queryParameters`, `file`, `body`) — use them as the skeleton and populate `body` values from `tasks.md`.

Always include `pathParameters` (even when empty):

```json
{
  "name": "pathParameters",
  "type": "json",
  "target": "pathParameters",
  "var": "<v + 8 chars>",
  "id": "<same as var>",
  "elementId": "<elementId>"
}
```

If `tasks describe` returns a `queryParameters` input, include it (populate `body` from `input-values.queryParameters` if present):

```json
{
  "name": "queryParameters",
  "type": "json",
  "target": "queryParameters",
  "body": "<input-values.queryParameters from tasks.md, or {} if absent>",
  "var": "<v + 8 chars>",
  "id": "<same as var>",
  "elementId": "<elementId>"
}
```

If `tasks describe` returns a `file` input (multipart activities), include it (even when empty):

```json
{
  "name": "file",
  "type": "file",
  "target": "file",
  "var": "<v + 8 chars>",
  "id": "<same as var>",
  "elementId": "<elementId>"
}
```

The `body` input carries the actual task data from `input-values`:

```json
{
  "name": "body",
  "type": "json",
  "target": "body",
  "body": "<input-values.body from tasks.md — already nested>",
  "var": "<v + 8 chars>",
  "id": "<same as var>",
  "elementId": "<elementId>"
}
```

### 3f. `data.outputs[]`

Copy verbatim from `tasks describe` (Step 2). Set `elementId` to the task's elementId on each output. Copy `_jsonSchema` from Error output if present.

### 3g. `data.bindings[]`

Leave as empty array `[]`. The FE does not expect task-level binding copies for activities.

### 3h. `entryConditions`

Do NOT auto-inject. Step 10 handles all task entry conditions.

### Write to caseplan.json

Append the task to the target stage's `tasks[]` array in its own task set (one task per lane).

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.ActivityExecution" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| get-connection | Context from tasks.md values only. No bindings, no bindings_v2 sync — folderKey unknown | `[SKIPPED] get-connection failed — bindings/folderKey omitted` |
| tasks describe | Context + bindings + bindings_v2. No outputs, no `enrichment.configuration`, no `inputMetadata`, no `multipartParameters` — write skeleton per Rule 7 | `[SKIPPED] tasks describe failed — outputs/enrichment omitted` |
| All succeed | Full population per §3a-3h including bindings_v2 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"execute-connector-activity"`
2. `data.serviceType` is `"Intsvc.ActivityExecution"`
3. `data.context[]` has: `connectorKey`, `connection`, `resourceKey`, `folderKey`, `objectName`, `method`, `path`, `metadata` — but NOT `operation` or `_label`
4. `metadata.body.activityPropertyConfiguration.configuration` matches `enrichment.configuration` from Step 2 (starts with `=jsonString:`, contains full `instanceParameters` from `Entry.configuration`)
5. `metadata.body.activityPropertyConfiguration.multipartParameters` matches `enrichment.multipartParameters` (present when multipart)
6. `metadata.body.inputMetadata` matches `enrichment.inputMetadata` (not empty `{}` if multipart)
7. Root bindings exist for ConnectionId + folderKey
8. `data.bindings[]` is empty `[]`
9. `data.outputs[]` copied verbatim with `elementId` set
10. `data.inputs[]` includes `pathParameters` (always), `queryParameters` (when applicable), `file` (when multipart has file), `body`
11. `bindings_v2.json` `resources` array matches `root.data.uipath.bindings` (unless get-connection failed)

## What NOT to Do

- **Do NOT add `operation` to `data.context[]`.** The FE only adds `operation` for triggers — activity context must not have it.
- **Do NOT add `_label` to `data.context[]`.** The FE does not include it.
- **Do NOT add `designTimeMetadata` to the metadata body.** The FE does not include it for case management tasks.
- **Do NOT add top-level `errorState` to the metadata body.** Error state belongs inside `activityPropertyConfiguration.errorState` only.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE crashes if activity tasks have task-level binding copies.
- **Do NOT derive `path` from `objectName`** (e.g., `/<objectName>`). The real path includes hub prefixes — use `enrichment.path`.
- **Do NOT derive `operation` from `objectName`.** They differ (e.g., `SendEmailV2` vs `send-mail-v2`) — use `enrichment.operation`.
- **Do NOT hand-construct `activityPropertyConfiguration.configuration`.** Copy `enrichment.configuration` from Step 2 as-is. Hand-constructing produces wrong `instanceParameters` (missing fields like `httpMethod`, `supportsStreaming`, `subType`) and wrong `operation` values, causing the FE to strip enrichment data on re-save.
- **Do NOT set `inputMetadata: {}`** when `enrichment.inputMetadata` has content. Multipart activities fail without it.
- **Do NOT omit `multipartParameters`** from `activityPropertyConfiguration` when `enrichment.multipartParameters` exists. Without it, the runtime cannot parse multipart request bodies (400 "Unable to parse multipart body").
- **Do NOT omit `pathParameters` input.** Always include it, even when empty — the FE always sends it.
- **Do NOT omit `file` input** when `enrichment.multipartParameters` has a file entry. Include it even when empty.
- **Do NOT add `data.name`.** The FE does not use it for connector tasks.
- **Do NOT auto-inject `entryConditions`.** Step 10 handles them — injecting here creates duplicates.
- **Never reuse a reference ID from a prior case or session.** Reference IDs (e.g., Jira project keys, Slack channel IDs) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources execute list` against the current `--connection-id`.

## Known Limitation

The CLI-produced `configuration` uses `essentialConfiguration` only. Tasks work at **runtime** (debug/publish) but the FE editor may not render them until the user re-configures the task in the UI.
