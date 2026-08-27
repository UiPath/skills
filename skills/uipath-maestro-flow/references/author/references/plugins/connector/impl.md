# Connector Activity Nodes — Implementation

Configure connector activity nodes after the generic node-add operation in [editing-operations.md](../../editing-operations.md). Configuration covers connection binding, metadata, object and operation discovery, references, custom fields, filters, input wiring, and debugging.

`uip maestro flow node configure` authors top-level `bindings[]` and `inputs.detail`. `bindings_v2.json` is regenerated from `bindings[]` at debug/pack time; never hand-edit it.

## Requirements and data model

Every connector node requires an Integration Service connection in top-level `bindings[]`. Run `registry get` with `--connection-id`; otherwise custom fields, dynamic enums, and reference metadata are absent.

Connector configuration is stored in `inputs.detail`:

- `connectionId`: bound IS connection UUID.
- `connectionFolderKey`: Orchestrator folder key in the authored `.flow`; `--detail folderKey` serializes as `connectionFolderKey`.
- `method`: IS method label from metadata.
- `endpoint`: API path from `connectorMethodInfo.path` or `availableOperations[].path`.
- `objectName`: required for generic activities.
- `bodyParameters`: values keyed by `inputDefinition.fields[].name` or `requestFields[].name`.
- `queryParameters`: parameters whose `type` is `query`.
- `pathParameters`: parameters whose `type` is `path`.
- `filter`: structured FilterBuilder tree.
- `customFieldsRequestDetails`: design-time cache for supported api-type ObjectActions; keys are camelCase and `parameterValues` is an array of `[key, value]` tuples.
- `multipartParameters`: derived from IS parameters where `type === "multipart"`; entries are `{name, dataType, value?}`.
- `inputMetadata`: derived multipart or list metadata.

For multipart parameters, pass file values through `--detail.bodyParameters.<name>`; `node configure` moves file-typed values into matching `multipartParameters[i].value`. Keep string entries, including the body aggregator named by `inputMetadata.multipart.bodyFieldName`, in `bodyParameters`. When multipart parameters exist, `inputMetadata` is `{type: "multipart", multipart: {bodyFieldName}}`; for list operations it is `{operation: "list", pagination: {maxPageSize}}`.

Concrete activities encode object and operation in the node type; their `inputDefinition.fields[]`, method, and endpoint are normally populated. Generic activities encode only the operation; `inputDefinition` is `{}` and require `objectName`, method, and endpoint from resource metadata.

Classify the activity from `Node.form.sections[0].fields[0].componentProps.connectorDetail.configuration` returned by `registry get`, parsing it as JSON and checking `activityType`. For `"Generic"`, run Step 2a and capture its `operation` for Step 3's `--operation`; otherwise skip Step 2a.

Definitions in `definitions[]` are CLI-owned. `uip maestro flow node add` copies them from the registry; never hand-write or hand-edit them. If configuration reports `No instanceParameters found in definition`, run `uip maestro flow registry pull --force`, delete the stale `definitions[]` entry, and run `uip maestro flow node add <file> <node-type>` again. Do not paste `form` by hand.

## No-live-tenant or planning-only configuration

If `node configure` cannot run:

1. Run `uip maestro flow registry search <keyword>` and `registry get <node-type>` to confirm the operation; see [cli-commands.md — registry](../../../../shared/cli-commands.md#uip-maestro-flow-registry).
2. Run `uip maestro flow node add <file> <node-type> --output json`; inside a loop body, add `--parent <LOOP_NODE_ID>` as described in [loop/impl.md](../loop/impl.md).
3. Write the planned `--detail` payload, including placeholder connection and folder UUIDs, to a separate file such as `<nodeId>.detail.json`. Do not put partial `inputs.detail` on the node.
4. Report under **Missing connections** or **Open questions** that the node will not pass `flow validate` until real `node configure` runs.

Do not replace a registered connector node with `core.logic.mock`. Use mocks only for genuinely unknown, unpublished, or not-yet-built non-connector resources. Preserve the registered connector key.

When parsing `--output json`, do not merge stderr into stdout. Use `2>/dev/null` for parse-only probes or capture stderr separately.

## Configuration workflow

### Step 1 — Fetch and bind a connection

Extract `<connector-key>` from `uipath.connector.<connector-key>.<activity-name>`. Before any `uip is connections ...` call, read [/uipath:uipath-platform — connections.md](../../../../../../uipath-platform/references/integration-service/connections.md), which is authoritative for auto-selection, personal workspace, BYOA filtering, empty-result recovery, and ping verification.

Run:

```bash
uip is connections list "<connector-key>" --all-folders --output json
```

`Data` is a flat array. Read `Data[i].Id` and `Data[i].FolderKey`; do not parse `Data.Connections` or `Data.Items`. Use `Data[i].Id` for `--connection-id` and `Data[i].FolderKey` for `folderKey`. End with a healthy connection ID and folder key for Steps 2 and 6.

### Step 2 — Fetch enriched metadata

Run:

```bash
uip maestro flow registry get <node-type> --connection-id <connection-id> --output json
```

Read enriched `inputDefinition.fields` and `outputDefinition.fields`, including type, required, description, enum, and `reference`. For concrete activities, save `connectorMethodInfo.method` and `connectorMethodInfo.path`. For generic activities, `connectorMethodInfo` is empty; use Step 3.

### Step 2a — Discover the object for generic activities

Run this only for `activityType: "Generic"`:

```bash
uip is resources list "<connector-key>" --connection-id "<connection-id>" --output json \
  --output-filter "[?contains(DisplayName,'<search>')].{Name:Name,Path:Path,Custom:Custom}"
```

Use case-sensitive `Name` as `objectName`, never `DisplayName`. `Path` is the endpoint suffix and `Custom` indicates tenant-defined objects.

### Step 3 — Describe the resource and read the cache

Read `<objectName>` from the node definition copied into `definitions[]`, never from the node-type suffix or by case conversion. Read `model.context[]` `{name:"objectName", value:"…"}` or `objectName` inside the `configuration` `=jsonString:` blob.

Sequence dependent calls; do not parallelize `node add`, `registry get`, and `describe`. If describe returns 404, reread `objectName` and retry; do not skip describe.

Run:

```bash
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json
```

Then run `cat <metadataFile path from response>` and read the full cached metadata. Pass `--operation` as the node definition's `model.context[].method` verbatim. Do not use `connectorMethodInfo.operation` or `connectorMethodInfo.method` as the describe lookup key.

Read `availableOperations[].method` and `availableOperations[].path` for method and endpoint; `parameters[]` for query/path parameters and `reference` objects; `requestFields[]` for body names, types, required status, descriptions, and `reference` objects; and `responseFields[]` for the response schema.

### Step 3a — Resolve parent-field-driven custom fields

Run this whenever metadata contains an api-type ObjectAction in top-level `objectActions[]` or `connectorMethodInfo.design.actions[]`. This applies to every operation whose schema depends on parent fields, including Create/Edit/Update inputs and Get/Retrieve/Query response fields.

Run the matching action with `-f, --field` before Step 5 and reuse the same values in Step 6c. Follow [/uipath:uipath-platform — resources.md > Parent-Field-Driven Custom Fields (api-type ObjectActions)](../../../../../../uipath-platform/references/integration-service/resources.md#parent-field-driven-custom-fields-api-type-objectactions) for procedure, flags, merge semantics, and recovery.

Do not skip this for Get/Retrieve: runtime may succeed while Studio Web lacks the design-time schema and downstream `$vars.<thisNode>.output.<custom-field>` resolves to undefined. `flow validate` does not catch this.

### Step 4 — Resolve every reference field

Inspect both `requestFields` and `parameters` for `reference`. Preserve `reference` when projecting `connectorMethodInfo.parameters[]` from `registry get`.

Resolve every reference immediately before Step 6, freshly against the current flow connection. IDs are connection-scoped; never reuse IDs from another connection. Read [/uipath:uipath-platform — Integration Service — resources.md](../../../../../../uipath-platform/references/integration-service/resources.md) for the full workflow.

Run `uip is resources run list` with the current `--connection-id` and use resolved IDs, not display names. If multiple matches exist, ask the user with one option per match and **"Something else"** last, following the dropdown question rule in [SKILL.md](../../../../../SKILL.md).

If a user-supplied value has zero matches after `Data.Pagination.HasMore` is `"false"`, ask with closest candidates and **"Something else"** last; use the unverified value only after confirmation.

If `reference.filterPattern` exists, substitute `{filter}` and pass the result as `--query`. `filterPattern` exists only in describe metadata, not the flow registry reference. Do not invent `searchTerm=`, `where=`, or `filter=` parameters.

Without `filterPattern`, paginate with `Data.Pagination.HasMore` and `NextPageToken`, using `--query "nextPage=<token>"`; stop on match and do not report not-found until `HasMore` is `"false"`. See [reference-resolution.md — Search References (filterPattern)](../../../../../../uipath-platform/references/integration-service/reference-resolution.md#search-references-filterpattern) and [reference-resolution.md](../../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

### Step 5 — Validate required fields

Check every `required: true` field in both `requestFields` and `parameters`. Use `defaultValue` for required query/path parameters when the user supplied no value:

1. Collect required fields from both metadata sections.
2. Match each against user-provided values.
3. Ask before building for every missing field without a default, showing `displayName` and expected value type. Use free-form input for open-ended values and dropdown options for finite choices, following [SKILL.md](../../../../../SKILL.md).
4. Do not guess or skip a required field.

Run Step 3a first for api-type ObjectActions because base describe may omit custom required fields.

### Step 5b — Wire upstream outputs

Use this form inside `bodyParameters`, `queryParameters`, and `pathParameters`:

```text
"=js:$vars.<sourceNodeId>.output.<field>"
```

The `=js:` prefix is mandatory for every `$vars`, `$metadata`, and `$self` reference. There is no `nodes.X.output.Y` syntax. See [node-output-wiring.md](../../../../shared/node-output-wiring.md).

### Step 6 — Configure the node

Run `is resources describe` first. `node configure` rebuilds `inputs.detail` and the essential-configuration blob from supplied `--detail`; it does not merge prior values. On every reconfiguration, pass the complete intended shape: connection plumbing, all parameter buckets, filter, and `customFieldsRequestDetails`.

Omitting `bodyParameters`, `queryParameters`, or `pathParameters` removes prior values. Omitting `filter` removes `savedFilterTrees` and filter derivation. Omitting `customFieldsRequestDetails` resets it to `null`.

#### Step 6a — FilterBuilder parameters

Scan every operation's `parameters[]` for `design.component === "FilterBuilder"`; this is not limited to list operations. Use the actual parameter `name` (`where`, `q`, or another connector-specific name).

Pass a structured tree under `--detail.filter`. The CLI writes runtime `queryParameters.<name>` and design-time `configuration.essentialConfiguration.savedFilterTrees.<name>`. Never pass a raw CEQL string under `queryParameters.<name>`; the CLI rejects it or leaves Studio Web's tree undefined.

Dynamic operands may use `{ "value": {"value": "=js:$vars...", "isLiteral": false} }`.

For dynamic-entity connectors, set the entity in the same configure call, such as `pathParameters.entityName`. Read exact, case-sensitive field names from `uip df entities list --output json` and `uip df entities get <entity-id> --output json`; unmatched leaves are silently dropped.

If no FilterBuilder parameter exists, pass no `filter` and filter downstream.

##### Hand-authored CEQL strings

Prefer, in order:

1. `node configure --detail.filter` with a structured tree.
2. A hand-authored `=js:` string only when a runtime value requires it, using bare field names, single-quoted values, and no OData aliases. Map `eq`→`=`, `ne`→`!=`, `gt`→`>`, `ge`→`>=`, `lt`→`<`, and `le`→`<=`. See [uipath-platform — Filter Trees (CEQL)](../../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

#### Step 6b — Run configure

Run:

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '<complete-detail-json>' \
  --output json
```

For generic nodes include `objectName`; concrete nodes ignore it if supplied. Use `method` and `endpoint` from `registry get` for concrete activities, or `availableOperations[].method` and `availableOperations[].path` from describe for both kinds. For generic activities, describe is the only source. Copy IS labels such as `GETBYID` verbatim; the CLI normalizes them. Validate that method agrees with the node operation.

Supply endpoint placeholders through `pathParameters` and resolve their IDs with `uip is resources run list` using the current connection. Body names come from `inputDefinition.fields[].name` or `requestFields[].name`.

For array fields, strip trailing `[*]` from the authored key and use a `=js:` expression returning the array; literal JSON arrays do not bind. Names containing `[*].` are not authorable. This applies to body, query, and path buckets; `customFieldsRequestDetails.parameterValues` uses `_array` encoding. The expression may return the whole array or wrap one element.

Derive connector output shape from `connectorMethodInfo.operation`, not vendor intuition or `outputDefinition.output.type`: `list` returns a bare array; other operations return one object. Use `=js:$vars.<node>.output` for list collections and `=js:$vars.<node>.output.<field>` otherwise.

`node configure` populates `inputs.detail` and top-level `bindings[]`. The serialized folder field is `connectionFolderKey`; never hand-edit it. Do not use `filterExpression`, which belongs to trigger/JMESPath filtering; see [connector-trigger/impl.md](../connector-trigger/impl.md#filter-trees).

For complex JSON, write a temporary file and run:

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json
```

#### Step 6c — Populate api-type custom fields

Inspect both `objectActions[]` and `connectorMethodInfo.design.actions[]`. Supported actions use top-level `ActionType: "Api"` or nested `actionType: "api"`. If no applicable api action exists, omit `customFieldsRequestDetails`; the CLI emits `null`.

Run Step 3a and use the matched action's `name` and `apiConfiguration.{url,body}` tokens. Match `source: field` or `source: method` according to metadata; for operation-scoped lookup use the node definition's `model.context[].method`.

Encode tokens longest-first: `:::` → `_sub_`; `[*]` → `_array`; `::` → `_sub_`; `.` → `_sub_`. Use camelCase keys and include every token from `apiConfiguration.url` and `body`:

```json
"customFieldsRequestDetails": {
  "objectActionName": "<ObjectActionName>",
  "parameterValues": [
    ["<encoded-token>", "<value>"],
    ["<unset-token>", null]
  ]
}
```

`customFieldsRequestDetails` complements runtime parameters: put raw parent values in `bodyParameters`, `queryParameters`, or `pathParameters`, and encoded values in the design-time cache. Values are strings or `null`; `parameterValues` is never an object map. The cache is embedded in `essentialConfiguration.customFieldsRequestDetails`, not set as a top-level `inputs.detail` field. Pass runtime values and the cache in the same configure call. The CLI does not validate action existence or token coverage, so Step 3a is mandatory.

## IS CLI commands

```bash
uip is connections list "<connector-key>" --all-folders --output json
uip is connections ping "<connection-id>" --output json
uip is connections create "<connector-key>"
uip maestro flow registry get <node-type> --connection-id <connection-id> --output json
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json
uip is resources run list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json
uip is connectors list --output json
```

Run `uip is connections --help` or `uip is resources --help` for all options.

## Bindings

Bindings belong in flow top-level `bindings[]`, alongside `nodes`, `edges`, and `definitions`. At debug/pack time the CLI regenerates `content/bindings_v2.json`; never edit that generated file.

Leave the registry definition's `model.context[]` unchanged. Connector definitions typically contain `<bindings.<connector-key> connection>` and `<bindings.FolderKey>` placeholders. Do not author `model.context[]` on the node instance. Connector binding matching is name-only within `resource: "Connection"` because `model.bindings.resourceKey` is typically unset. Resource nodes instead match `(name, resourceKey)`.

`node configure` claims the empty connection stub created by `node add` and adds the folder row. For each unique connection it emits two entries:

```json
{
  "id": "<unique-id>",
  "name": "<connector-key> connection",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<connection-uuid>",
  "default": "<connection-uuid>",
  "propertyAttribute": "ConnectionId"
}
```

and:

```json
{
  "id": "<unique-id>",
  "name": "FolderKey",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<connection-uuid>",
  "default": "<folder-key>",
  "propertyAttribute": "FolderKey"
}
```

The connection binding `name` is fetched from IS by `node configure` and must match the definition placeholder. Both entries use the same UUID. `resource` is capitalized `"Connection"`; `propertyAttribute` is exactly `"ConnectionId"` or `"FolderKey"`. Reuse the same pair for nodes sharing a connection; do not add duplicates.

An empty `resourceKey` on a configured `ConnectionId` row is a defect and causes `Value cannot be null. (Parameter 'Connection')`. Do not remove or repair bindings by hand. The only legitimate empty stub is a deliberately planned, unconfigured node. An empty stub after successful configure or node removal is a CLI bug to report.

Never hardcode connection IDs; fetch them from IS at authoring time. Connector-trigger flows may additionally emit `EventTrigger` and `Property` resources; see [connector-trigger/impl.md](../connector-trigger/impl.md). Queue and time-trigger resources follow their relevant plugins.

## Debug and common errors

- **No connection found:** top-level `bindings[]` is missing or mismatched. Run Step 1 and verify `ConnectionId` and `FolderKey` entries.
- **Connection ping failed:** re-authenticate the connection in IS.
- **Missing `inputs.detail`:** run `node configure`.
- **Display name instead of reference ID:** resolve with `uip is resources run list`.
- **Resource not found after clean validate/debug:** resolve the reference again with the current connection; IDs are connection-scoped. Reconfigure and re-debug.
- **Required field missing:** inspect every `required: true` entry in cached `requestFields` and `parameters`.
- **`No api-type ObjectAction matched for fields [...]`:** pass the node definition's `model.context[].method` verbatim as `--operation`; do not use `connectorMethodInfo.operation` or `connectorMethodInfo.method`.
- **Unresolvable `$vars`:** verify graph edges and upstream output paths.
- **Missing method/path:** rerun `registry get` with `--connection-id` or use describe for generic activities.
- **Malformed or stale `bindings_v2.json`:** never edit it; rerun `node configure` and debug/pack.
- **Connector key not found:** run `uip is connectors list --output json`; keys are often prefixed with `uipath-`.
- **FilterBuilder UI is `undefined`:** configure a structured `--detail.filter`, not a raw `queryParameters` string.
- **FilterBuilder configure rejection:** move the value into `--detail.filter` as a structured tree.
- **Data Service filter returns every record or malformed CEQL ending in `AND`:** compare tree field IDs case-sensitively with `uip df entities get <entity-id> --output json`; unmatched leaves are dropped.
- **CEQL `[102003]` field-name error:** leave field names bare and quote only values, or use a filter tree.
- **CEQL `[102003]` `Unsupported value expression 'Column'`:** single-quote values inside the `=js:` concatenation; do not double-quote them.
- **CEQL `[102003]` with `eq`, `ne`, `gt`, `ge`, `lt`, or `le`:** replace aliases with `=`, `!=`, `>`, `>=`, `<`, or `<=`.
- **`parameterValues` object-map error:** use `[key, value]` tuples.
- **Custom-field token unresolved:** reread `apiConfiguration.url` and `body` and add every encoded token.
- **Unknown `ObjectActionName` or `ParameterValues`:** use camelCase `objectActionName` and `parameterValues`.
- **Array field rejected as unknown:** strip trailing `[*]`, use a `=js:` array expression, and reconfigure. Names containing `[*].` are not authorable.
- **Array field round-trips empty:** replace the literal JSON array with a `=js:` expression returning the array.

## Final checks

1. Inspect top-level `bindings[]`; do not treat `bindings_v2.json` as ground truth.
2. Compare every input with the cached metadata file.
3. Remember that `flow validate` checks JSON schema and graph structure, not missing connector inputs, wrong reference IDs, or expired connections; run `flow debug`.
4. Check both `requestFields` and `parameters`.
5. Confirm `node configure` was run with the complete intended detail on every reconfiguration.
6. If planning-only, record the planned sidecar `<nodeId>.detail.json`, do not author `bindings[]` directly, and report that validation requires real configuration.