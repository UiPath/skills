# connector-trigger task — Implementation (Direct JSON Write)

Fetch connector metadata via CLI, then write the task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md`.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"7dc57f24-894c-5ae2-a902-66056fa40609"` |
| `connection-id` | `"bc095c1f-671f-4669-8634-b7164fa46aa0"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"Message"` |
| `event-operation` | `"EMAIL_RECEIVED"` |
| `event-mode` | `"polling"` |
| `input-values` | `{"parentFolderId": "AAMkADNm..."}` (already resolved IDs) |
| `filter` | `"(contains(subject, 'urgent'))"` (already JMESPath) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Configuration Workflow

### Step 1 — Get connection details + Entry

```bash
uip case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<type-id>" --output json
```

**Save:**

| Variable | Source | Example |
|---|---|---|
| `Entry` | `.Data.Entry` (full object) | `{ displayName: "Email Received", ... }` |
| `Config` | `.Data.Config` | `{ connectorKey, objectName, eventOperation, eventMode, version, supportsStreaming }` |
| `folderKey` | `.Data.Connections[selected].folder.key` | `"87fd6cec-..."` |
| `connectorName` | `.Data.Connections[selected].connector.name` | `"Microsoft Outlook 365"` |

### Step 2 — Get enriched metadata + outputs

```bash
uip case tasks describe --type connector-trigger \
  --id "<type-id>" \
  --connection-id "<connection-id>" --output json
```

**Save:**

| Variable | Source | Example |
|---|---|---|
| `enrichment.operation` | `.Data.enrichment.operation` | `"EMAIL_RECEIVED"` |
| `enrichment.connectorVersion` | `.Data.enrichment.connectorVersion` | `"1.35.48"` |
| `outputs` | `.Data.outputs` | Array with response schema + Error |

## Step 3 — Build `data` and write to caseplan.json

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`). Create the task skeleton:

```json
{
  "id": "<taskId>",
  "type": "wait-for-connector",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.WaitForEvent"
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

| `name` | `value` source | Notes |
|---|---|---|
| `connectorKey` | `connector-key` (tasks.md) | |
| `connection` | `=bindings.<connBindingId>` | Reference — not raw UUID |
| `resourceKey` | `connection-id` (tasks.md) | |
| `folderKey` | `=bindings.<folderBindingId>` | Reference — not raw UUID |
| `method` | *(no value)* | Empty placeholder. Do not omit. |
| `path` | *(no value)* | Empty placeholder. Do not omit. |
| `objectName` | `object-name` (tasks.md) | |
| `operation` | `enrichment.operation` (Step 2) | |
| `metadata` | *(see §3c)* | `type: "json"` with `body` |

### 3c. `metadata` context entry body

```json
{
  "activityPropertyConfiguration": {
    "objectName": "<object-name>",
    "eventType": "<enrichment.operation>",
    "eventMode": "<event-mode from tasks.md>",
    "configuration": "=jsonString:<see §3d>",
    "uiPathActivityTypeId": "<type-id>",
    "errorState": { "issues": [] }
  },
  "activityMetadata": {
    "activity": "<Entry from Step 1 — copy full object>"
  },
  "inputMetadata": {},
  "telemetryData": {
    "connectorKey": "<connector-key>",
    "connectorName": "<connectorName from Step 1>",
    "objectName": "<object-name>",
    "objectDisplayName": "<object-name>",
    "primaryKeyName": ""
  }
}
```

**Differences from connector-activity metadata:**

| Field | Activity | Trigger |
|---|---|---|
| `activityPropertyConfiguration` top-level fields | only `configuration`, `uiPathActivityTypeId`, `errorState` | adds `objectName`, `eventType`, `eventMode` |
| `designTimeMetadata` | present | absent |
| `telemetryData.operationType` | present (derived from httpMethod) | absent |
| `errorState` (metadata level) | `{ hasError: false }` | absent |

### 3d. `activityPropertyConfiguration.configuration`

A `=jsonString:` prefixed JSON string. Use `Config` from Step 1:

```
=jsonString:{"essentialConfiguration":{"instanceParameters":{"connectorKey":"<connector-key>","objectName":"<object-name>","activityType":"CuratedWaitFor","version":"<Config.version>","eventOperation":"<enrichment.operation>","eventMode":"<event-mode>","supportsStreaming":<Config.supportsStreaming>},"objectName":"<object-name>","packageVersion":"<Config.version>","connectorVersion":"<enrichment.connectorVersion>","executionType":null,"httpMethod":null,"path":null,"filter":null}}
```

> **Critical:** `activityType` MUST be `"CuratedWaitFor"` — NOT `Config.activityType` (which is `"CuratedTrigger"`).

> `Config.version`, `Config.supportsStreaming` — from `Config` returned by Step 1.

> `filter` is always `null` in essentialConfiguration. The user's filter expression goes in `body.filters.expression` only (§3e).

### 3e. `data.inputs[]`

Build the input body from `input-values` and `filter` in the `tasks.md` entry. Planning already resolved all IDs and translated filters to JMESPath — implementation just assembles the body.

**If `input-values` has event parameters:**

Convert each key-value pair to JMESPath equality (`key == 'value'`), join with `&&`. If `filter` is also present, combine with `&&`:

```json
{
  "name": "body",
  "type": "json",
  "target": "body",
  "body": {
    "filters": {
      "expression": "(parentFolderId == 'AAMkADNm...')"
    },
    "queryParams": {
      "parentFolderId": "AAMkADNm..."
    }
  },
  "var": "<v + 8 chars>",
  "id": "<same as var>",
  "elementId": "<elementId>"
}
```

`queryParams` preserves raw event parameter values for FE round-trip.

**If no `input-values` and no `filter`:** write empty body `{}`.

### 3f. `data.outputs[]`

Copy verbatim from `tasks describe` (Step 2). Set `elementId` to the task's elementId on each output. Copy `_jsonSchema` from Error output if present.

### 3g. `data.bindings[]`

Leave as empty array `[]`. The FE does not expect task-level binding copies for triggers.

### 3h. `entryConditions`

Do NOT auto-inject. Step 10 handles all task entry conditions.

### Write to caseplan.json

Append the task to the target stage's `tasks[]` array in its own task set (one task per lane).

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.WaitForEvent" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| get-connection | Context from tasks.md values only. No bindings — folderKey unknown | `[SKIPPED] get-connection failed — bindings/folderKey omitted` |
| tasks describe | Context + bindings. No outputs/enrichment | `[SKIPPED] tasks describe failed — outputs/enrichment omitted` |
| All succeed | Full population per §3a-3h | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"wait-for-connector"`
2. `data.serviceType` is `"Intsvc.WaitForEvent"`
3. `data.context[]` has: `connectorKey`, `connection`, `resourceKey`, `folderKey`, `method`, `path`, `objectName`, `operation`, `metadata`
4. `metadata.body.activityPropertyConfiguration.configuration` starts with `=jsonString:` and contains `"activityType":"CuratedWaitFor"`
5. `metadata.body.activityPropertyConfiguration.configuration` contains `enrichment.connectorVersion`
6. Root bindings exist for ConnectionId + folderKey
7. `data.bindings[]` is empty `[]`
8. `data.outputs[]` copied verbatim with `elementId` set
9. If `input-values` present: `body.filters.expression` has JMESPath + `body.queryParams` has raw values (no `body.parameters`)

## What NOT to Do

- **Do NOT use `CuratedTrigger`** in `essentialConfiguration.instanceParameters.activityType`. It MUST be `CuratedWaitFor` for in-stage wait-for-connector tasks.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE does not expect task-level copies for triggers.
- **Do NOT add `body.parameters`.** The FE only uses `body.filters.expression` + `body.queryParams`. No `body.parameters`.
- **Do NOT put the filter expression in `essentialConfiguration.filter`.** It stays `null`. The filter goes in `body.filters.expression` only.
- **Do NOT add `data.name`.** The FE does not use it for connector tasks.
- **Do NOT auto-inject `entryConditions`.** Step 10 handles them — injecting here creates duplicates.
- **Do NOT omit `method` and `path` context entries.** They must be present as empty placeholders (no `value` field) — the runtime expects the keys to exist.

## Known Limitation

The `activityPropertyConfiguration.configuration` uses `essentialConfiguration` only (from the shared SDK). Tasks work at **runtime** (debug/publish) but the FE editor may not render them until the user re-configures the task in the UI.
