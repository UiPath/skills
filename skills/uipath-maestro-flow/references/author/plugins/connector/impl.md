# Connector Activity Nodes — Implementation

Configure connector activity nodes after the generic node-add operation in [editing-operations.md](../../editing-operations.md). Configuration covers connection binding, metadata, object and operation discovery, references, custom fields, filters, input wiring, and debugging.

`uip maestro flow node configure` authors top-level `bindings[]` and `inputs.detail`. `bindings_v2.json` is regenerated from `bindings[]` at debug/pack time; never hand-edit it.

## Requirements and data model

Every connector node requires an Integration Service connection in top-level `bindings[]`. Run `registry get` with `--connection-id`; otherwise custom fields, dynamic enums, and reference metadata are absent. `registry get` accepts only `--connection-id` and `--local` — no `--activity-version` (it reads the node's own `configuration.version` and self-routes `4.0.0` activities; anything else fails `error: unknown option`). For `4.0.0` nodes `--connection-id` adds nothing (metadata not connection-scoped — see [§ 4.0.0 Activities](#400-activities)).

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

## 4.0.0 Activities

An activity is `4.0.0` when its `configuration` JSON reports `"version":"4.0.0"`. Author it through the Configuration workflow below like any other connector activity; `describe`/version mechanics are in [/uipath:uipath-platform — resources.md § `--activity-version`](../../../../../uipath-platform/references/integration-service/resources.md#--activity-version). Four deltas:

1. **No `objectName` in `--detail`** — resolved from the configuration's `activityName` (`model.context.objectName` is empty).
2. **`method` / `endpoint`** — from `connectorMethodInfo` (`registry get`) or `availableOperations[]` (`is resources describe <connector-key> <activity-name> --activity-version 4.0.0`).
3. **Operation label ≠ HTTP verb** — a semantic operation (e.g. `Update`) pairs with any verb (e.g. `POST /usergroups.users.update`). `flow validate` accepts it; do not "fix" the method to match the label.
4. **Not connection-scoped** — `--connection-id` on `registry get` adds no custom fields.

## No-Live-Tenant / Planned Configuration

If `node configure` cannot run:

1. Run `uip maestro flow registry search <keyword>` and `registry get <node-type>` to confirm the operation; see [cli-commands.md — registry](../../../shared/cli-commands.md#uip-maestro-flow-registry).
2. Run `uip maestro flow node add <file> <node-type> --output json`; inside a loop body, add `--parent <LOOP_NODE_ID>` as described in [loop/impl.md](../loop/impl.md).
3. Write the planned `--detail` payload, including placeholder connection and folder UUIDs, to a separate file such as `<nodeId>.detail.json`. Do not put partial `inputs.detail` on the node.
4. Report under **Missing connections** or **Open questions** that the node will not pass `flow validate` until real `node configure` runs.

Do not replace a registered connector node with `core.logic.mock`. Use mocks only for genuinely unknown, unpublished, or not-yet-built non-connector resources. Preserve the registered connector key.

When parsing `--output json`, do not merge stderr into stdout. Use `2>/dev/null` for parse-only probes or capture stderr separately.

## Configuration workflow

### Step 1 — Fetch and bind a connection

Extract `<connector-key>` from `uipath.connector.<connector-key>.<activity-name>`. Before any `uip is connections ...` call, read [/uipath:uipath-platform — connections.md](../../../../../uipath-platform/references/integration-service/connections.md), which is authoritative for auto-selection, personal workspace, BYOA filtering, empty-result recovery, and ping verification.

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

Read `<objectName>` from the node definition copied into `definitions[]`, never from the node-type suffix or by case conversion. Read `model.context[]` `{name:"objectName", value:"…"}` or `objectName` inside the `configuration` `=jsonString:` blob. Example: node type `…google-gmail.send-email` has objectName `SendEmail` (not `send_email`); `…teams.send-bot-direct-message` has objectName `bot_direct_messages` (not `send-bot-direct-message`). kebab→snake and kebab→Pascal are both guesses that 404.

Sequence dependent calls; do not parallelize `node add`, `registry get`, and `describe`. If describe returns 404, reread `objectName` and retry; do not skip describe.

Run:

```bash
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json
```

Then run `cat <metadataFile path from response>` and read the full cached metadata. Pass `--operation` as the node definition's `model.context[].method` verbatim. E.g. Jira `curated_get_issue` → `GETBYID`; Data Service `QueryEntityRecordsCurated` → `POST`. Do not use `connectorMethodInfo.operation` or `connectorMethodInfo.method` as the describe lookup key.

> **`4.0.0` activities** — positional is the `activityName`, `--activity-version 4.0.0` is mandatory, `--operation` takes the verb from `model.context[].method` (never a guessed semantic label), and `--connection-id` is ignored: `uip is resources describe "<connector-key>" "<activityName>" --activity-version 4.0.0 --operation <method> --output json`. See [§ 4.0.0 Activities](#400-activities).

Read `availableOperations[].method` and `availableOperations[].path` for method and endpoint; `parameters[]` for query/path parameters and `reference` objects; `requestFields[]` for body names, types, required status, descriptions, and `reference` objects; and `responseFields[]` for the response schema.

### Step 3a — Resolve parent-field-driven custom fields

Run this whenever metadata contains an api-type ObjectAction in top-level `objectActions[]` or `connectorMethodInfo.design.actions[]`. This applies to every operation whose schema depends on parent fields, including Create/Edit/Update inputs and Get/Retrieve/Query response fields.

Run the matching action with `-f, --field` before Step 5 and reuse the same values in Step 6c. Follow [/uipath:uipath-platform — resources.md > Parent-Field-Driven Custom Fields (api-type ObjectActions)](../../../../../uipath-platform/references/integration-service/resources.md#parent-field-driven-custom-fields-api-type-objectactions) for procedure, flags, merge semantics, and recovery.

Do not skip this for Get/Retrieve: runtime may succeed while Studio Web lacks the design-time schema and downstream `$vars.<thisNode>.output.<custom-field>` resolves to undefined. `flow validate` does not catch this.

### Step 4 — Resolve reference fields

Check **BOTH `requestFields` AND `parameters`** from the metadata for entries with a `reference` object — these require ID lookup from the connector's live data. Use `uip is resources run list` to resolve them:

> **References are NOT body-field-only.** Query and path parameters carry `reference` objects too, and on some connectors the activity's PRIMARY input is a required **path parameter** whose `reference` is the design-time lookup behind a Studio Web dropdown. Scanning only `requestFields` misses it — the node then configures and passes `flow validate` with an unverified value and 404s at runtime. The same `reference` blocks appear on `connectorMethodInfo.parameters[]` in `registry get` output (with or without `--connection-id`) — when projecting parameter metadata for inspection, always include the `reference` key, not just `name`/`required`/`design.component`.

> **Resolve every reference field freshly, against the current `--connection-id`, immediately before `node configure` (Step 6)** — even if you think you already know the ID from a previous flow. Reference IDs are connection-scoped and reused values fault silently at runtime. See [Reference IDs Are Connection-Scoped (CRITICAL)](../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical) for the full mechanism and failure mode, and the top-level Anti-Patterns in [SKILL.md](../../../../SKILL.md).

```bash
# Example: resolve Slack channel "#test-slack" to its ID
uip is resources run list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<id>" --output json
# -> { "id": "C1234567890", "name": "test-slack" }
```

The `<id>` in `--connection-id "<id>"` MUST be the connection bound to **this** flow (the one picked in Step 1), not any other connection you've used in another flow. Use the resolved IDs (not display names) — from this very `run list` call — in the flow's node `inputs`. When multiple matches exist, ask the user, with one option per match plus **"Something else"** as the last option (see the dropdown question rule in [SKILL.md](../../../../SKILL.md)).

> **Zero matches on a user-supplied value** — if the completed lookup (`Data.Pagination.HasMore` is `"false"`) finds no entry matching a value the user provided, do NOT configure the node with it silently. Ask the user, presenting the closest candidates as options plus **"Something else"** as the last option (see the dropdown question rule in [SKILL.md](../../../../SKILL.md)). Proceed with the unverified value only if the user confirms it.

> **The lookup call itself failed** — a 403/401 on an expired or revoked grant, or a 5xx, means you have no ID and no candidate list to offer. Do NOT configure the node with the display name, a vendor well-known alias, or an ID from memory; each passes `flow validate` and faults at runtime. Stop and report the failed resolve, naming the connection and the vendor error. See [reference-resolution.md — When the Lookup Call Fails](../../../../../uipath-platform/references/integration-service/reference-resolution.md#when-the-lookup-call-fails-critical).

> **Filter server-side before paginating.** If the field's `reference` carries a `filterPattern` (e.g. Teams `userId`: `"$filter=startswith(userPrincipalName,'{filter}')"`), substitute the search term for `{filter}` and pass the result as `--query` — one targeted call instead of walking a large directory. `filterPattern` appears only in `is resources describe` output; the flow `registry get` reference object strips it (keeps only `objectName`/`lookupValue`/`lookupNames`/`path`/`childPath`), so read it from the Step 3 describe metadata. Guessed params (`searchTerm=`/`where=`/`filter=`) are silently ignored. See [reference-resolution.md — Search References (filterPattern)](../../../../../uipath-platform/references/integration-service/reference-resolution.md#search-references-filterpattern).

> **Paginate only when there is no `filterPattern`.** Use `Data.Pagination.HasMore` / `NextPageToken` with `--query "nextPage=<token>"`. Short-circuit on match. Do NOT conclude "not found" until `HasMore` is `"false"`. See [resources.md#pagination](../../../../../uipath-platform/references/integration-service/resources.md#pagination).

**Read [/uipath:uipath-platform — Integration Service — resources.md](../../../../../uipath-platform/references/integration-service/resources.md) for the full reference-resolution workflow** (pagination, describe failures, fallbacks).

### Step 5 — Validate required fields

Check every `required: true` field in both `requestFields` and `parameters`. Use `defaultValue` for required query/path parameters when the user supplied no value:

1. Collect required fields from both metadata sections.
2. Match each against user-provided values.
3. Ask before building for every missing field without a default, showing `displayName` and expected value type. Use free-form input for open-ended values and dropdown options for finite choices, following [SKILL.md](../../../../SKILL.md).
4. Do not guess or skip a required field.

Run Step 3a first for api-type ObjectActions because base describe may omit custom required fields.

### Step 5b — Wire upstream outputs

Use this form inside `bodyParameters`, `queryParameters`, and `pathParameters`:

```text
"=js:$vars.<sourceNodeId>.output.<field>"
```

The `=js:` prefix is mandatory for every `$vars`, `$metadata`, and `$self` reference. There is no `nodes.X.output.Y` syntax. See [node-output-wiring.md](../../../shared/node-output-wiring.md).

### Step 6 — Configure the node

Run `is resources describe` first. `node configure` rebuilds `inputs.detail` and the essential-configuration blob from supplied `--detail`; it does not merge prior values. On every reconfiguration, pass the complete intended shape: connection plumbing, all parameter buckets, filter, and `customFieldsRequestDetails`.

Omitting `bodyParameters`, `queryParameters`, or `pathParameters` removes prior values. Omitting `filter` removes `savedFilterTrees` and filter derivation. Omitting `customFieldsRequestDetails` resets it to `null`.

#### Step 6a — FilterBuilder parameters

A filter is authored as a tree under the `filter` key of `--detail`. The CLI compiles the tree; you never write the query text. Five steps:

1. **Find the filter parameter and the path slots** — read them from the registry, never guess:

   ```bash
   uip maestro flow registry get <node-type> --output json \
     --output-filter "Node.{filterParams:connectorMethodInfo.parameters[?design.component=='FilterBuilder'].name,path:connectorMethodInfo.path,pathParams:connectorMethodInfo.parameters[?type=='path'].name}"
   ```

   Data Service `query-entity-records` returns `filterParams: ["queryExpression"]`, `path: "/v2/{entityName}/qer"`, `pathParams: ["entityName"]`. FilterBuilder parameters are not limited to list operations. If `filterParams` is empty, pass no `filter` and filter downstream.

2. **Read exact field names** — `uip df entities list --output json`, then `uip df entities get <ENTITY_ID> --output json`. Names are case-sensitive; a leaf whose `id` matches no field is dropped without an error.

3. **Write the `--detail` JSON to a file** with a quoted heredoc. The value of `filter` IS the tree — `groupOperator`, `filters[]`, `groups[]` at its top level. Do not nest it under the parameter name; the CLI applies the tree to the FilterBuilder parameter it found in step 1 (the first one, if there are several). A runtime value is a leaf operand with `"isLiteral": false`:

   ```json
   {
     "connectionId": "<CONNECTION_ID>", "folderKey": "<FOLDER_KEY>",
     "pathParameters": { "entityName": "<ENTITY_NAME>" },
     "filter": {
       "groupOperator": 0,
       "filters": [
         { "id": "accountNumber", "operator": "Equals",
           "value": { "value": "=js:$vars.<node>.output.<field>", "isLiteral": false } }
       ],
       "groups": []
     }
   }
   ```

   Tree shape and operator tokens: [uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

4. **Configure** — `uip maestro flow node configure <ProjectName>.flow <NODE_ID> --detail "$(cat /tmp/detail.json)" --output json` (Step 6b).

5. **Verify the compile** — read the node back. `queryParameters.<name>` must hold the compiled query with a placeholder, `accountNumber = '{var_<hash>}'`, and `filterVariables` must have that `var_<hash>` key. The CLI also writes `configuration.essentialConfiguration.savedFilterTrees.<name>`. An **empty** `queryParameters.<name>` means the tree was mis-shaped (step 3): the CLI found no `filters` at the top level and compiled an empty query with no error, so the flow would fetch the whole entity.

Never:

- pass a CEQL string under `queryParameters.<name>` — the CLI rejects it or leaves Studio Web's tree undefined;
- write the query as a whole-value `=js:` string — `flow validate` cannot read it (it reads only a plain concatenation) and the CLI warns on it; replace any you find with a tree;
- hand-type `endpoint` or `pathParameters` names — take them from step 1.

#### Step 6b — Run configure

Run:

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '<complete-detail-json>' \
  --output json
```

For generic nodes include `objectName`; concrete nodes ignore it if supplied. Use `method` and `endpoint` from `registry get` for concrete activities, or `availableOperations[].method` and `availableOperations[].path` from describe for both kinds. For generic activities, describe is the only source. Copy IS labels such as `GETBYID` verbatim; the CLI normalizes them. Validate that method agrees with the node operation.

Supply endpoint placeholders through `pathParameters` and resolve their IDs with `uip is resources run list` using the current connection. Body names come from `inputDefinition.fields[].name` or `requestFields[].name`.

For array fields, strip trailing `[*]` from the authored key and use a `=js:` expression returning the array; literal JSON arrays do not bind. Names containing `[*].` are not authorable. This applies to body, query, and path buckets; `customFieldsRequestDetails.parameterValues` uses `_array` encoding. The expression may return the whole array or wrap one element — wrap a literal array in parentheses, `"fields.labels": "=js:(['shield', 'p0'])"`; pass a whole array from a variable as `"=js:$vars.allTags"`; wrap a single element as `"=js:([$vars.priorityTag])"`.

Derive connector output shape from `connectorMethodInfo.operation`, not vendor intuition or `outputDefinition.output.type`: `list` returns a bare array; other operations return one object. Use `=js:$vars.<node>.output` for list collections and `=js:$vars.<node>.output.<field>` otherwise.

`node configure` populates `inputs.detail` and top-level `bindings[]`. The serialized folder field is `connectionFolderKey`; never hand-edit it. Do not use `filterExpression`, which belongs to trigger/JMESPath filtering; see [connector-trigger/impl.md](../connector-trigger/impl.md#filter-trees).

For complex JSON, write a temporary file and run:

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json
```

#### Step 6c — Populate api-type custom fields

Inspect both `objectActions[]` and `connectorMethodInfo.design.actions[]`. Supported actions use top-level `ActionType: "Api"` or nested `actionType: "api"`. If no applicable api action exists, omit `customFieldsRequestDetails`; the CLI emits `null`.

Illustrative supported activities (confirm against `registry get` for the specific connector/object/activity — the set evolves):

| Connector key | Object | Activity / Action | HTTP | Source |
|---|---|---|---|---|
| `uipath-microsoft-azureapplicationinsights` | `executeQuery` | `generateSchema` | — | field |
| `uipath-salesforce-sfdc` | `curated_soqlQuery` | `generateSchema` | — | field |
| `uipath-workday-workdayrest` | `wql` | `generateSchema` | — | field |
| `uipath-oracle-netsuite` | `executeSuiteQL` | `generateSchema` | — | field |
| `uipath-snowflake-snowflake` | `executeQuery` | `generateSchema` | — | field |
| `uipath-atlassian-jira` | `curated_create_issue` | Create Issue | POST | method |
| `uipath-atlassian-jira` | `curated_edit_issue` | Update Issue | PUT | method |
| `uipath-atlassian-jira` | `curated_get_issue` | Get Issue | GETBYID | method |
| `uipath-uipath-dataservice` | `CreateEntityRecordCurated` | Create Entity Record | POST | method |
| `uipath-uipath-dataservice` | `QueryEntityRecordsCurated` | Query Entity Records | POST | method |
| `uipath-mailchimp-mailchimp` | `list_members_curated_dynamic::members` | Add Subscriber | POST | method |
| `uipath-microsoft-onedrive` | `AddListItem` | Add List Item | POST | method |
| `uipath-sap-s4hanacloud` | `Entity` | Create Entity | POST | method |
| `uipath-google-bigquery` | `projects::table` | List All Records | GET | method |

> **Data Fabric also has native nodes — check whether they exist before choosing.** `core.datafabric.read` / `create` / `update` / `delete` ([data-fabric/planning.md](../data-fabric/planning.md)) need no Integration Service connection and are authored with `Edit`/`Write` instead of `node configure`, so they are the lighter path **when the tenant has them**. Their flags default to off, so confirm with `uip maestro flow registry get core.datafabric.read` first. If that answers "Node not found" — or search reports `AvailableOnTenant: false` — these `uipath-uipath-dataservice` activities are the correct path; stay here. Stay here too when the entity is federated, since the native writes require a native entity.

Run Step 3a and use the matched action's `name` and `apiConfiguration.{url,body}` tokens. Match `source: field` or `source: method` according to metadata; for operation-scoped lookup use the node definition's `model.context[].method`.

Encode tokens longest-first: `:::` → `_sub_`; `[*]` → `_array`; `::` → `_sub_`; `.` → `_sub_`. Examples: `fields.project.key` → `fields_sub_project_sub_key`; `items[*]` → `items_array`; `tenantEntityName` → `tenantEntityName` (unchanged). Use camelCase keys and include every token from `apiConfiguration.url` and `body`:

```json
"customFieldsRequestDetails": {
  "objectActionName": "<ObjectActionName>",
  "parameterValues": [
    ["<encoded-token>", "<value>"],
    ["<unset-token>", null]
  ]
}
```

`customFieldsRequestDetails` complements runtime parameters: put raw parent values in `bodyParameters`, `queryParameters`, or `pathParameters`, and encoded values in the design-time cache. Values are strings or `null`; `parameterValues` is never an object map. The cache is embedded in `essentialConfiguration.customFieldsRequestDetails`, not set as a top-level `inputs.detail` field. Pass runtime values and the cache in the same configure call — omitting the runtime bucket is the most common mistake; the design-time cache alone does not feed the connector at runtime. Concrete (Jira Create Issue): `bodyParameters.fields.project.key = "<PROJECT_KEY>"` AND `parameterValues = [["fields_sub_project_sub_key", "<PROJECT_KEY>"]]`. Dropping the runtime-input copy manifests as `DAP-DT-_2003 refField with name <X> not found` at activity load. The CLI does not validate action existence or token coverage, so Step 3a is mandatory.

**Worked `--detail` payloads** — each passes BOTH the runtime bucket and the design-time cache in one call.

Jira Create Issue — `source: method` (raw `fields.project.key` in body + encoded `fields_sub_project_sub_key` in cache):

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat <<'JSON'
{
  "connectionId": "<id>",
  "folderKey": "<key>",
  "method": "POST",
  "endpoint": "/curated_create_issue",
  "bodyParameters": {
    "fields.project.key": "<PROJECT_KEY>",
    "fields.issuetype.id": "3",
    "fields.summary": "Created from Maestro"
  },
  "customFieldsRequestDetails": {
    "objectActionName": "GenerateSchema",
    "parameterValues": [
      ["fields_sub_project_sub_key", "<PROJECT_KEY>"],
      ["fields_sub_issuetype_sub_id", "3"]
    ]
  }
}
JSON
)" --output json
```

Snowflake Execute Query — `source: field` (SQL string is the parent field; `query` unchanged, no dots):

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat <<'JSON'
{
  "connectionId": "<id>",
  "folderKey": "<key>",
  "method": "POST",
  "endpoint": "/executeQuery",
  "bodyParameters": {
    "query": "SELECT id, name FROM customers WHERE active = TRUE"
  },
  "customFieldsRequestDetails": {
    "objectActionName": "generateSchema",
    "parameterValues": [
      ["query", "SELECT id, name FROM customers WHERE active = TRUE"]
    ]
  }
}
JSON
)" --output json
```

Dataservice V3 Query Entity Records — `source: method` (`tenantEntityName` unchanged, no dots):

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat <<'JSON'
{
  "connectionId": "<id>",
  "folderKey": "<key>",
  "method": "POST",
  "endpoint": "/v3/QueryEntityRecords/query",
  "queryParameters": {
    "entityScope": "tenant",
    "tenantEntityName": "\"my-entity\""
  },
  "customFieldsRequestDetails": {
    "objectActionName": "FetchObjectMetadataTenant",
    "parameterValues": [
      ["tenantEntityName", "\"my-entity\""]
    ]
  }
}
JSON
)" --output json
```

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
- **FilterBuilder UI is `undefined`:** configure a structured tree under the `filter` key of `--detail`, not a raw `queryParameters` string.
- **FilterBuilder configure rejection:** move the value into the `filter` key of `--detail` as a structured tree.
- **Data Service filter returns every record or malformed CEQL ending in `AND`:** compare tree field IDs case-sensitively with `uip df entities get <entity-id> --output json`; unmatched leaves are dropped.
- **CEQL `[102003]` field-name error, or `[102001]`:** the query was hand-written as a string. Delete it and configure a filter tree under the `filter` key of `--detail` (Step 6a); put runtime values in a leaf operand with `"isLiteral": false`.
- **`parameterValues` object-map error:** use `[key, value]` tuples.
- **`[400300] Error evaluating expression … Invalid or unexpected token`, or the command itself dies with a shell parse error (`zsh: parse error`, `bash: syntax error near unexpected token`):** the `=js:` expression was hand-escaped through nested shell quotes inside `--detail '<json>'`. Write the detail JSON to a file with a quoted heredoc and pass `--detail "$(cat /tmp/detail.json)"`. See [editing-operations-cli.md — Configure a connector node](../../editing-operations-cli.md#configure-a-connector-node).
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