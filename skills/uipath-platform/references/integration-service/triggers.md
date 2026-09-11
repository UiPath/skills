# Triggers

Triggers are event-based activities fired by external-system events. Use trigger metadata to discover objects, inputs, filters, and outputs.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown below.

## Trigger Discovery Flow

```text
[ ] 1. List trigger activities → select one → note its Operation
[ ] 2. For CREATED/UPDATED/DELETED, list objects → resolve the object name (ask if unclear)
[ ] 3. Describe the resolved object and operation → obtain field metadata
```

For `CREATED`, `UPDATED`, and `DELETED`, run the intermediate `objects` step. For other operations, skip it and use the activity’s `ObjectName`.

**Source of truth:** event-parameter inputs are the union of `triggers objects → parameters[]` and `triggers describe → EventParameters`. Configure every field either source marks `required`; never use only one response. `triggers describe` also supplies `FilterFields` and `OutputFields`. Run both calls, do not invent fields, and do not substitute metadata from another command.

## Discover Activities and Objects

Run:

```bash
uip is activities list "<connector-key>" --triggers --output json
```

Use `Operation` to identify the event type.

For `CREATED`, `UPDATED`, or `DELETED`, run:

```bash
uip is triggers objects "<connector-key>" "<OPERATION>" --output json

# With connection (includes custom objects):
uip is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --output json
```

Use uppercase `CREATED`, `UPDATED`, or `DELETED`. Pass `--connection-id` for custom or connection-specific objects and `--refresh` to bypass cache.

Resolve the exact object name from `triggers objects` response `Data[].Name`:

1. Match the user’s intent against `Name` or `DisplayName`, case-insensitively.
2. If exactly one matches, use its `Name` verbatim.
3. If none or multiple match, ask the user and present candidates by `displayName`. Do not guess or fabricate a name; a wrong name can return empty or incorrect metadata.

For non-CRUD operations, use the activity’s `ObjectName` directly. Generic CRUD triggers may have no `objectName` in the flow-node manifest; pass the resolved `Name` as `objectName` when configuring the node: `node configure --detail.objectName` (Maestro Flow).

## Describe Trigger Metadata

Run:

```bash
uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
  --connection-id "<id>" --output json
```

Always pass `--connection-id`; without it, custom or connection-specific fields may be omitted. For CRUD operations, use the name from object resolution. The response, requested with `allFields=true` by the API, is the source of truth; use field names verbatim and do not guess.

| Operation | Objects step | Object name |
|---|---|---|
| **CREATED / UPDATED / DELETED** | Required | Matching `Name` from objects response |
| **Other** | Skip | Activity `ObjectName` |

### Response Fields

**Trigger activities**

| Field | Meaning |
|---|---|
| `Name` | Activity identifier |
| `DisplayName` | Human-readable name |
| `ObjectName` | Object for non-CRUD triggers |
| `Operation` | `CREATED`, `UPDATED`, `DELETED`, or custom event |
| `IsCurated` | Whether the activity is curated |

**Trigger objects** provide `name` for describe, `displayName`, `byoaConnection`, `isWebhookUrlVisible`, `eventMode` (`"webhooks"` or `"polling"`), and `parameters[]`.

`parameters[]` is incomplete: merge it with `triggers describe → EventParameters`. Each entry contains:

| Field | Meaning |
|---|---|
| `name` | Configure under the bucket selected by `type` |
| `displayName` | Prompt label |
| `dataType` | Value type such as `string`, `number`, or `boolean` |
| `required` | Whether the value must be supplied |
| `description` | User-facing field hint |
| `reference` | Lookup ID; resolve it with `uip is resources run list "<connector-key>" "<reference.objectName>" --connection-id "<id>"` |
| `design.position` | `"primary"` is the top-level card input; other values are layout hints only |
| `type` | `"query"` → `queryParameters`; `"path"` → `pathParameters`; otherwise → `eventParameters` |

Configure each bucket as a JSON object keyed by `name`. Resolve reference IDs before configuring because IDs are connection-scoped.

**Trigger metadata** typically contains:

| Field | Meaning |
|---|---|
| `EventParameters` | First-class event inputs; merge with `parameters[]` and configure every required entry |
| `FilterFields` | Fields allowed in the optional `filter` tree |
| `OutputFields` | Payload schema for downstream `$vars.{triggerId}.output.*` |
| `eventMode` | `"webhooks"` or `"polling"` |
| `byoaConnection` | Whether a BYOA connection is required |
| `isWebhookUrlVisible` | Whether the webhook URL is exposed |

`EventParameters` are not output-only metadata. `flow registry get`’s `eventParameters.fields` mirrors them and is the offline fallback.

## Build Filter Trees from `filterFields`

Filters are structured trees, not JMESPath strings. The CLI compiles the tree into runtime `filterExpression` and stores both forms for Studio Web round-tripping. Do not pass `filterExpression` directly; validation rejects it.

After loading `filterFields.fields` (for example, through `flow registry get`):

1. Match each user condition to a `name`; unknown names are rejected at configure time.
2. Select an operator by intent and field type; see [uipath-maestro-flow > connector-trigger](../../../uipath-maestro-flow/references/author/plugins/connector-trigger/impl.md#supported-operators).
3. Create one leaf per condition and place same-level conditions under `groupOperator` `0` (AND) or `1` (OR).
4. Use nested `groups` for mixed AND/OR logic.
5. Wrap string operands in a `value` object containing `value`, `rawString` (verbatim user text, including string quotes), and `isLiteral`. A leaf operand may be dynamic (`isLiteral: false`, compiled to a `{var_…}` placeholder plus `filterVariables`), but `eventParameters` must be literals because triggers run before a flow run exists.
6. If `filterFields` is empty or absent, omit `filter`; do not invent an empty expression.

Mandatory connector subscription filters are not freeform leaves. Set them through `eventParameters`; the CLI runs them and AND-joins the result into the runtime `filterExpression` at the top level of the node’s `inputs.detail`.

For array-shaped names containing `[*]` (such as `tags[*]` or `ParentFolders[*].ID`), use the full schema name in the leaf `id`. The CLI generates projection syntax such as `(tags[?@=='urgent'])` or `(ParentFolders[?ID=='INBOX'])`.

## Retrieve Webhook URLs

A webhook trigger will not fire until its URL is registered with the external service.

Retrieve the URL only when `eventMode: "webhooks"` and the matching object has `isWebhookUrlVisible: true`. If visibility is `false`, skip retrieval; the connector manages registration. This is independent of `byoaConnection`.

1. Run:

   ```bash
   uip is connections list "<connector-key>" --connection-id "<id>" --output json
   ```

   Obtain `ElementInstanceId`. If it is empty, the connection is the wrong type for webhooks. Check `byoaConnection`; if `true`, switch to a BYOA connection.

2. Run:

   ```bash
   uip is webhooks config "<connector-key>" \
     --connection-id "<connection-guid>" \
     --element-instance-id <number> \
     --output json
   ```

3. Present `WebhookUrl` with registration instructions. Prefer `design.textBlocks` from `triggers objects` when present, substituting `{webhookUrl}`. Otherwise instruct the user to register the URL in the external service’s app settings and verify it.

## Generic Happy Path

Run:

```bash
# 1. List trigger activities
uip is activities list "<connector-key>" --triggers --output json

# 2. For a CRUD operation, list objects
uip is triggers objects "<connector-key>" CREATED \
  --connection-id "<id>" --output json

# 3. Describe the uniquely resolved object
uip is triggers describe "<connector-key>" CREATED "<object-name>" \
  --connection-id "<id>" --output json
```

For a non-CRUD operation, skip step 2 and run describe with the activity’s `ObjectName`:

```bash
uip is triggers describe "<connector-key>" "<OPERATION>" "<ObjectName>" \
  --connection-id "<id>" --output json
```