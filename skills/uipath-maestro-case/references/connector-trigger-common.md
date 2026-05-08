# Connector Trigger — Shared Pipeline

Shared planning and implementation logic for connector-based triggers. Used by both:
- [connector-trigger task](plugins/tasks/connector-trigger/planning.md) — in-stage `wait-for-connector`
- [event trigger](plugins/triggers/event/planning.md) — case-level `Intsvc.EventTrigger`

Both use the same TypeCache (`typecache-triggers-index.json`), same read-only IS metadata fetches, same metadata structure, and same enrichment pipeline. Only the target (task vs trigger node), serviceType, and output format differ — see each plugin's own docs for those specifics.

---

## Planning Pipeline

### 1. Find the trigger in TypeCache

Read `~/.uip/case-resources/typecache-triggers-index.json` directly. Match on `displayName`, `connectorKey`, or `eventOperation` from sdd.md. Record `uiPathActivityTypeId`.

### 2. Resolve the connection

```bash
uip case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`.

- **Single connection** → use it.
- **Multiple connections** → **AskUserQuestion** with connection names + "Something else".
- **Empty `Connections`** → mark `<UNRESOLVED>`. Both plugins emit skeletons at execution time (different shapes per plugin) — see [skeleton-tasks.md](skeleton-tasks.md) for connector-task skeletons and [`plugins/triggers/event/impl-json.md` § Skeleton fallback](plugins/triggers/event/impl-json.md) for event-trigger skeletons.

Record `connection-id`, `connector-key`, `object-name`, `eventOperation` from the response.

### 3. Describe the trigger — discover event parameters and filter fields

```bash
uip is triggers describe "<connector-key>" "<eventOperation>" "<object-name>" \
  --connection-id "<connection-id>" --output json
```

Returns:
- **`eventParameters`** — fields that configure *what* the trigger monitors. May be `required: true` and may have `reference` objects.
- **`filterFields`** — fields used to narrow *which* events fire the trigger. Optional filter criteria.
- **`eventMode`** — `"polling"` or `"webhooks"`. Authoritative source for `event-mode`.

**This step is mandatory.** Without it, the agent cannot discover required event parameters or available filter fields.

### 4. Resolve reference fields in event parameters

Check `eventParameters` for fields with a `reference` object. For each, resolve display names from sdd.md to IDs:

```bash
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<connection-id>" --output json
```

Match the sdd.md value to `displayName`. Use the resolved `id` in `input-values`.

> **Paginate when looking up by name.** If `Pagination.HasMore` is `true`, re-run with `--query "nextPage=<NextPageToken>"` until found.

If a reference cannot be resolved, **AskUserQuestion** with the available options. Do not guess.

### 5. Validate required event parameters

For each `eventParameters` entry with `required: true`:
1. Check if sdd.md provides a value
2. If missing, **AskUserQuestion** — list the missing parameter with its `displayName` and description
3. Only after all required event parameters have values, proceed

### 6. Map SDD inputs to event parameters vs filter fields

SDD input fields don't map 1:1 to the connector's schema. Cross-reference each SDD input against `eventParameters` and `filterFields` from Step 3 to decide where it goes:

- **eventParameters** → configure *what* the trigger monitors. Values must be **static** — resolved to IDs at planning time. Go into `input-values`.
- **filterFields** → narrow *which* events fire the trigger. Values can be **static** literals or **dynamic** `=vars.X` references resolved at runtime. Go into `filter`.

If an SDD input matches an `eventParameters` field name, it's an event parameter. If it matches a `filterFields` field name, it's a filter. If it matches neither, **AskUserQuestion** — the SDD may use different naming than the connector.

### 7. Build input-values and filter

**input-values** — resolved event parameter values (static IDs only):
```json
{"parentFolderId": "AAMkADNm..."}
```

**filter** — translate SDD filter criteria using `filterFields` from Step 3. Build a **structured filter tree** (NOT a flat JMESPath string). The CLI converts the tree to a JMESPath expression automatically.

#### Filter tree shape

```json
{
  "groupOperator": 0,
  "index": 0,
  "filters": [
    {
      "id": "<fieldName from filterFields>",
      "operator": "<PascalCase operator>",
      "value": { "value": "<literal>", "rawString": "\"<literal>\"", "isLiteral": true }
    }
  ],
  "groups": []
}
```

- `groupOperator`: `0` (And) or `1` (Or) — combines sibling filters and groups
- `filters[]`: leaf conditions. `id` must be a field name from `filterFields` (Step 3)
- `groups[]`: nested sub-trees for mixed AND/OR logic (empty for simple cases)

#### Operators

| Pattern | Operator |
|---|---|
| Exact match | `"Equals"` |
| Not equal | `"NotEquals"` |
| Substring match | `"Contains"` |
| Does not contain | `"NotContains"` |
| Starts with | `"StartsWith"` |
| Greater than | `"GreaterThan"` |
| Less than | `"LessThan"` |
| Is empty | `"IsEmpty"` |
| Is not empty | `"IsNotEmpty"` |
| One of (multi-value) | `"In"` |
| Not one of | `"NotIn"` |
| Is null | `"IsNull"` |
| Is not null | `"IsNotNull"` |

> See the IS SDK `FilterOperator` enum for the complete list (includes `Like`, `NotLike`, datetime operators, etc.).

#### Examples

Single filter (AND with one leaf):
```json
{ "groupOperator": 0, "index": 0, "filters": [
    { "id": "subject", "operator": "Contains", "value": { "value": "urgent", "rawString": "\"urgent\"", "isLiteral": true } }
], "groups": [] }
```

Multiple conditions (AND):
```json
{ "groupOperator": 0, "index": 0, "filters": [
    { "id": "project", "operator": "Equals", "value": { "value": "PROJ", "rawString": "\"PROJ\"", "isLiteral": true } },
    { "id": "issuetype", "operator": "Equals", "value": { "value": "Bug", "rawString": "\"Bug\"", "isLiteral": true } }
], "groups": [] }
```

Nested AND/OR (e.g., "status is Open AND (priority > 3 OR assignee is null)"):
```json
{ "groupOperator": 0, "index": 0, "filters": [
    { "id": "status", "operator": "Equals", "value": { "value": "Open", "rawString": "\"Open\"", "isLiteral": true } }
], "groups": [
    { "groupOperator": 1, "index": 1, "filters": [
        { "id": "priority", "operator": "GreaterThan", "value": { "value": 3, "rawString": "\"3\"", "isLiteral": true } },
        { "id": "assignee", "operator": "IsNull", "value": null }
    ], "groups": [] }
] }
```

No filter (trigger fires on all events): omit `filter` from the tasks.md entry entirely.

#### Dynamic variable limitation

The filter tree only supports `isLiteral: true` values. When a filter requires runtime case variable references (`=vars.X`), write the `body.filters.expression` JMESPath string directly and leave `essentialConfiguration.filter` as `null`. This is a known SDK limitation shared with flow-tool.

Only use field names that appear in `filterFields`. If a filter cannot be translated unambiguously, **AskUserQuestion**.

---

## Implementation — Shared Metadata Fetches (read-only CLI)

> **Each connector task runs its own `get-connection`.** Even when two tasks share the same `connection-id`, the Entry and Config objects differ between activity and trigger types. Never reuse another task's CLI output.

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
| `folderName` | `.Data.Connections[selected].folder.name` | `"57d6e3b0's workspace"` |
| `connectorName` | `.Data.Connections[selected].connector.name` | `"Microsoft Outlook 365"` |
| `connectionName` | `.Data.Connections[selected].name` | `"my-outlook-connection"` |

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
| `enrichment.configuration` | `.Data.enrichment.configuration` | `"=jsonString:{\"essentialConfiguration\":{...}}"` |
| `outputs` | `.Data.outputs` | Array with response schema + Error |

---

## Implementation — Shared Metadata Construction

### Context array

Every context entry MUST include `"type": "string"` (or `"type": "json"` for metadata). Omitting `type` causes Studio Web to fail to render the case.

| `name` | `type` | `value` source | Notes |
|---|---|---|---|
| `connectorKey` | `"string"` | `connector-key` (tasks.md) | |
| `connection` | `"string"` | `=bindings.<connBindingId>` | Reference — not raw UUID |
| `resourceKey` | `"string"` | `connection-id` (tasks.md) | |
| `folderKey` | `"string"` | `=bindings.<folderBindingId>` | Reference — not raw UUID |
| `method` | `"string"` | *(no value)* | Empty placeholder. Do not omit entry. |
| `path` | `"string"` | *(no value)* | Empty placeholder. Do not omit entry. |
| `objectName` | `"string"` | `object-name` (tasks.md) | |
| `operation` | `"string"` | `enrichment.operation` (Step 2) | |
| `metadata` | `"json"` | *(see below)* | Uses `body` not `value` |

### Metadata body

```json
{
  "activityPropertyConfiguration": {
    "objectName": "<object-name>",
    "eventType": "<enrichment.operation>",
    "eventMode": "<event-mode from tasks.md>",
    "configuration": "<enrichment.configuration from Step 2 — copy as-is>",
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

### essentialConfiguration

Copy `enrichment.configuration` from Step 2 as-is. The CLI pre-builds this `=jsonString:` string using the full `Entry.configuration` as `instanceParameters` (with `activityType` overridden to `"CuratedWaitFor"`) and includes `connectorVersion` and `filter` when available.

> **Do NOT hand-construct this string.** The CLI returns the correct pre-built configuration. Hand-constructing produces incomplete `instanceParameters` and risks using the wrong `activityType`.

> If `enrichment.configuration` is absent (older CLI version), defer to skeleton task per Rule 8 — do not hand-construct.

> **Critical:** The CLI already overrides `activityType` to `"CuratedWaitFor"` (NOT `Config.activityType` which is `"CuratedTrigger"`). Case `wait-for-connector` tasks use different runtime semantics than Flow triggers.

> When a structured filter tree is provided (from §7), store it in `essentialConfiguration.filter` so Studio Web can round-trip the filter UI. The derived JMESPath expression goes in `inputs[].body.filters.expression`. When no filter is needed, `filter` stays `null`.

### Input body (from tasks.md values)

If `input-values` has event parameters, the CLI auto-generates the JMESPath expression from the structured filter tree. The body contains:

```json
{
  "filters": { "expression": "(parentFolderId == 'AAMkADNm...') && (contains(subject, 'urgent'))" },
  "queryParams": { "parentFolderId": "AAMkADNm..." }
}
```

If no `input-values` and no `filter`: empty body `{}`.

### Root-level bindings

Create 2 entries in the bindings array — destination path per [bindings/impl-json.md § Schema-dependent destination](plugins/variables/bindings/impl-json.md) (v19: `root.data.uipath.bindings[]`; v20: top-level `bindings[]`):

| Binding | `propertyAttribute` | `default` |
|---|---|---|
| ConnectionId | `"ConnectionId"` | `connection-id` |
| folderKey | `"folderKey"` | `folderKey` (from Step 1) |

Both share `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

### Root-level bindings post-sync

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Skip if `get-connection` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 (after all connector tasks), not per-task. See [bindings-v2-sync.md § When to Run](bindings-v2-sync.md).

---

## What NOT to Do (shared)

- **Do NOT use `CuratedTrigger`** in essentialConfiguration. It MUST be `CuratedWaitFor`.
- **Do NOT hand-write JMESPath filter expressions.** Build a structured filter tree (§7); the CLI derives the expression automatically.
- **Do NOT use `filterExpression` as a CLI input.** The CLI rejects raw `filterExpression` strings (MST-8802).
- **Never reuse a reference ID from a prior case or session.** Reference IDs (mailbox folders, Slack channels, Jira projects) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources execute list` against the current `--connection-id`.
- **Do NOT add `body.parameters`.** Only `body.filters.expression` + `body.queryParams`.
- **Do NOT auto-inject `entryConditions`** (for tasks). Step 10 handles them.

## Known Limitation (shared)

The `activityPropertyConfiguration.configuration` uses `essentialConfiguration` only (from the shared SDK). Works at **runtime** but the FE editor may not render until the user re-configures in the UI.
