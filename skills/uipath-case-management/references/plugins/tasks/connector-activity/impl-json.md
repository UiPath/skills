# connector-activity task — Implementation (Direct JSON Write)

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
| `connectorName` | `.Data.Connections[selected].connector.name` | `"Microsoft Outlook 365"` |

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
| `outputs` | `.Data.outputs` | Array with response schema + Error |

> **All three enrichment fields are critical.** Without `inputMetadata`, multipart activities fail. Without `path`, wrong endpoint. Without `operation`, incomplete essentialConfiguration.

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

### 3b. `data.context[]`

No `operation` context entry for activities — the FE only adds `operation` to context for triggers. Activity tasks use `enrichment.operation` inside `essentialConfiguration` and `designTimeMetadata` only.

| `name` | `value` source | Notes |
|---|---|---|
| `connectorKey` | `connector-key` (tasks.md) | |
| `connection` | `=bindings.<connBindingId>` | Reference — not raw UUID |
| `resourceKey` | `connection-id` (tasks.md) | |
| `folderKey` | `=bindings.<folderBindingId>` | Reference — not raw UUID |
| `objectName` | `object-name` (tasks.md) | |
| `method` | `Config.httpMethod` (Step 1) | |
| `path` | `enrichment.path` (Step 2) | From Swagger — includes hub prefix |
| `_label` | `Entry.displayName` (Step 1) | |
| `metadata` | *(see §3c)* | `type: "json"` with `body` |

### 3c. `metadata` context entry body

```json
{
  "activityMetadata": {
    "activity": "<Entry from Step 1 — copy full object>"
  },
  "designTimeMetadata": {
    "activityDisplayName": "<Entry.displayName>",
    "connectorLogoUrl": "<Entry.svgIconUrl>",
    "activityConfig": {
      "isCurated": true,
      "operation": "<enrichment.operation>"
    }
  },
  "telemetryData": {
    "connectorKey": "<connector-key>",
    "connectorName": "<connectorName from Step 1>",
    "operationType": "<see table below>",
    "objectName": "<object-name>",
    "objectDisplayName": "<Entry.displayName>",
    "primaryKeyName": ""
  },
  "inputMetadata": "<enrichment.inputMetadata from Step 2 — copy as-is, or {} if absent>",
  "errorState": { "hasError": false },
  "activityPropertyConfiguration": {
    "configuration": "=jsonString:<see §3d>",
    "uiPathActivityTypeId": "<type-id>",
    "errorState": { "issues": [] }
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

A `=jsonString:` prefixed JSON string. Use `Config` from Step 1 + enrichment from Step 2:

```
=jsonString:{"essentialConfiguration":{"instanceParameters":{"activityType":"<Config.activityType>","objectName":"<object-name>","operation":"<enrichment.operation>","connectorKey":"<connector-key>","version":"<Config.version>"},"objectName":"<object-name>","operation":"<lowercase enrichment.operation>","httpMethod":"<Config.httpMethod>","path":"<enrichment.path>","packageVersion":"<Config.version>","connectorVersion":null,"executionType":null,"customFieldsRequestDetails":null,"unifiedTypesCompatible":true}}
```

> `connectorVersion` is `null` for activities (triggers use `enrichment.connectorVersion`).

### 3e. `data.inputs[]`

Copy `input-values` from the `tasks.md` entry directly. Planning already resolved all field values, IDs, and built the nested JSON structure — implementation just writes it.

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

If `input-values` includes `queryParameters`, add a separate entry:

```json
{
  "name": "queryParameters",
  "type": "json",
  "target": "queryParameters",
  "body": "<input-values.queryParameters from tasks.md>",
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
| get-connection | Context from tasks.md values only. No bindings — folderKey unknown | `[SKIPPED] get-connection failed — bindings/folderKey omitted` |
| tasks describe | Context + bindings. No outputs/enrichment. Use Config fallbacks | `[SKIPPED] tasks describe failed — outputs/enrichment omitted` |
| All succeed | Full population per §3a-3h | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"execute-connector-activity"`
2. `data.serviceType` is `"Intsvc.ActivityExecution"`
3. `data.context[]` has: `connectorKey`, `connection`, `resourceKey`, `folderKey`, `objectName`, `method`, `path`, `_label`, `metadata` — but NOT `operation`
4. `metadata.body.activityPropertyConfiguration.configuration` starts with `=jsonString:` and contains `enrichment.operation` + `enrichment.path`
5. `metadata.body.inputMetadata` matches `enrichment.inputMetadata` (not empty `{}` if multipart)
6. Root bindings exist for ConnectionId + folderKey
7. `data.bindings[]` is empty `[]`
8. `data.outputs[]` copied verbatim with `elementId` set

## What NOT to Do

- **Do NOT add `operation` to `data.context[]`.** The FE only adds `operation` for triggers — activity context must not have it.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE crashes if activity tasks have task-level binding copies.
- **Do NOT derive `path` from `objectName`** (e.g., `/<objectName>`). The real path includes hub prefixes — use `enrichment.path`.
- **Do NOT derive `operation` from `objectName`.** They differ (e.g., `SendEmailV2` vs `send-mail-v2`) — use `enrichment.operation`.
- **Do NOT set `inputMetadata: {}`** when `enrichment.inputMetadata` has content. Multipart activities fail without it.
- **Do NOT add `data.name`.** The FE does not use it for connector tasks.
- **Do NOT auto-inject `entryConditions`.** Step 10 handles them — injecting here creates duplicates.

## Known Limitation

The `activityPropertyConfiguration.configuration` uses `essentialConfiguration` only (from the shared SDK). Tasks work at **runtime** (debug/publish) but the FE editor may not render them until the user re-configures the task in the UI.
