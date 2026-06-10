# Connector Activity Nodes — Implementation

How to configure connector activity nodes: connection binding, enriched metadata, reference field resolution, and debugging. Connection bindings are emitted by `uip maestro flow node configure` into the flow's top-level `bindings[]`; `bindings_v2.json` is regenerated from them at debug/pack time and should never be hand-edited.

For generic node/edge add, remove, and wiring procedures, see [editing-operations.md](../../editing-operations.md). This guide covers the connector-specific configuration workflow that must follow the generic node add.

## How Connector Nodes Differ from OOTB

1. **Connection binding required** — every connector node needs an IS connection (OAuth, API key, etc.) authored in the flow's top-level `bindings[]` (which the CLI regenerates into `bindings_v2.json` at debug/pack time). Without it, the node cannot authenticate.
2. **Enriched metadata via `--connection-id`** — call `registry get` with `--connection-id` to get connection-aware field metadata. Without it, only base fields are returned — custom fields, dynamic enums, and reference resolution are missing.
3. **`inputs.detail` object** — connector nodes store operation-specific configuration in `inputs.detail`, populated by `uip maestro flow node configure`:
   - `connectionId` — the bound IS connection UUID
   - `connectionFolderKey` — the Orchestrator folder key in the authored `.flow` file. `node configure --detail` accepts `folderKey` as input and writes it back as `connectionFolderKey`.
   - `method` — HTTP method from `registry get` → `connectorMethodInfo.method` (e.g., `POST`)
   - `endpoint` — API path. Read `connectorMethodInfo.path` (from `registry get`) or `availableOperations[].path` (from `is resources describe`).
   - `objectName` — required for generic activities (see below). The API object name (e.g. `"Opportunity"`); ignored for concrete nodes.
   - `bodyParameters` — field-value pairs for the request body. Read field names from `inputDefinition.fields[].name` (`registry get`) or `requestFields[].name` (`is resources describe`).
   - `queryParameters` — field-value pairs for query string parameters. Read from `connectorMethodInfo.parameters[]` where `type: query` (`registry get`) or `parameters[]` (`is resources describe`).
   - `pathParameters` — field-value pairs for path placeholders in `endpoint` (e.g. `{conversationsInfoId}`). Read from `connectorMethodInfo.parameters[]` where `type: path` (`registry get`) or `parameters[]` (`is resources describe`).
   - `filter` — structured FilterBuilder tree for list/query operations. See Step 6a.
   - `customFieldsRequestDetails` — design-time cache for connectors with an api-type ObjectAction at top-level `objectActions[]` OR `connectorMethodInfo.design.actions[]` (e.g. Jira `GenerateSchema`, Dataservice V3 `FetchObjectMetadataTenant`). camelCase keys; `parameterValues` as `[key, value]` tuples. See Step 6c.
   - `multipartParameters` — derived from IS metadata params where `type === "multipart"`. Array of `{name, dataType, value?}`. Pass file values via `--detail.bodyParameters.<name>`; `node configure` moves file-typed values into the matching `multipartParameters[i].value` slot (matched by `name`). String-typed entries — including the body aggregator field whose name is given by `inputMetadata.multipart.bodyFieldName` — stay in `bodyParameters`.
   - `inputMetadata` — auto-derived. `{type: "multipart", multipart: {bodyFieldName}}` when multipart params exist; `{operation: "list", pagination: {maxPageSize}}` for list operations. Driven by `methodInfo.parameters` + `methodInfo.operation`.

---

## Generic vs Concrete Activities

Connector nodes come in two flavors:

- **Concrete** — the node type encodes a specific object + operation (e.g. `uipath.connector.uipath-atlassian-jira.curated_create_issue`). `inputDefinition.fields[]` is populated; `method` and `endpoint` are fixed.
- **Generic** — the node type encodes only the operation (e.g. `uipath.connector.uipath-salesforce-sfdc.list-records`, `…insert-record`, `…update-record`). `inputDefinition` is `{}`; the node needs an extra `objectName` in `--detail`, and `method` / `endpoint` come from `is resources describe`.

To classify a node, read `Node.form.sections[0].fields[0].componentProps.connectorDetail.configuration` from the `registry get` response, parse it as JSON, and check `activityType`. `"Generic"` → run Step 2a to discover `objectName` (and capture `operation` from the same marker for the `--operation` flag in Step 3). Anything else → skip Step 2a.

## Critical: Connector Definition Must Include `form`

> Connector definitions in `definitions[]` are CLI-owned (see [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node)) — `uip maestro flow node add` copies them verbatim from the registry, and you should never hand-write or hand-edit them. If `node configure` fails with `No instanceParameters found in definition`, the definition in `definitions[]` is missing the `form` field — typically because the local registry cache is stale (the definition was copied in before the CLI started emitting `form`). Recovery: `uip maestro flow registry pull --force`, delete the stale `definitions[]` entry, re-run `uip maestro flow node add <file> <node-type>` so the CLI re-copies the definition with `form`. Do not paste `form` in by hand — re-running `node add` is the supported path.

## No-Live-Tenant / Planned Configuration

If you cannot run `node configure` (no live connection, sandbox forbids it, the user asked for planning only):

1. Confirm the connector operation exists: `uip maestro flow registry search <keyword>` and `registry get <node-type>` (see [cli-commands.md — registry](../../../../shared/cli-commands.md#uip-maestro-flow-registry) for the `search` output shape).
2. Add the connector node with `uip maestro flow node add <file> <node-type> --output json`. This is still required — it inserts the node and copies the definition into `definitions[]`.
3. Write the planned `--detail` payload to a separate file (e.g. `<nodeId>.detail.json`) with placeholder values for missing connection/folder UUIDs. Do **not** put a partial `inputs.detail` on the node.
4. **The node will not pass `flow validate` until `node configure` is run.** Surface this explicitly in your completion report under "Missing connections" or "Open questions" — do not let the user discover it via a validation failure later.

Do not replace a registered connector operation with `core.logic.mock` because configuration cannot run. Mocks are only for genuinely unknown, unpublished, or not-yet-built non-connector resources. A real connector node added via `node add` but unconfigured preserves the registered connector key that Studio Web, reviewers, and downstream tooling need.

When piping `--output json` into `python`, `jq`, or another parser, do not merge stderr into stdout. The CLI may emit diagnostic lines such as "Tool factory already registered..." before the JSON on stderr; use `2>/dev/null` for parse-only probes or capture stderr separately.

## Configuration Workflow

Follow these steps for every connector node.

### Step 1 — Fetch and bind a connection

Extract the connector key from the node type (`uipath.connector.<connector-key>.<activity-name>`).

Discovery call is **always**:

```bash
uip is connections list "<connector-key>" --all-folders --output json
```

`connections list` returns `Data` as a flat array. Do **not** parse `Data.Connections` or `Data.Items`; those wrapper objects are not part of the CLI JSON contract. Read each candidate from `Data[]` and use PascalCase fields:

```json
{
  "Data": [
    {
      "Id": "<connection-id>",
      "Name": "<display-name>",
      "State": "Enabled",
      "IsDefault": "Yes",
      "Folder": "<folder-name>",
      "FolderKey": "<folder-key>"
    }
  ]
}
```

Use `Data[i].Id` as the `--connection-id` value and `Data[i].FolderKey` as the `folderKey` value in `node configure --detail`.

> **MUST READ before any `uip is connections ...` call:** [/uipath:uipath-platform — connections.md](../../../../../../uipath-platform/references/integration-service/connections.md). Single source of truth for selection rules (auto-select, personal workspace), BYOA filtering, empty-result recovery, ping verification.

End state: a healthy connection `Id` + `FolderKey` for Step 2 (`registry get --connection-id`) and Step 6 (`node configure --detail`).

### Step 2 — Get enriched node definitions with connection

Call `registry get` with `--connection-id` to fetch connection-aware metadata including custom fields:

```bash
uip maestro flow registry get <node-type> --connection-id <connection-id> --output json
```

This returns enriched `inputDefinition.fields` and `outputDefinition.fields` with accurate type, required, description, enum, and `reference` info. Without `--connection-id`, only standard/base fields are returned.

The response also includes `connectorMethodInfo` with the real HTTP `method` (e.g. `GET`, `POST`) and `path` template (e.g. `/ConversationsInfo/{conversationsInfoId}`). **Save `connectorMethodInfo.method` and `connectorMethodInfo.path`** — you must pass them to `node configure` later as `method` and `endpoint`.

> **For generic activities, `connectorMethodInfo` is empty.** Method and endpoint are object-specific and only resolve once Step 2a picks an `objectName`; Step 3 then surfaces them via `availableOperations[]`. Don't try to derive them from the manifest alone.

### Step 2a — Discover the object name (generic activities only)

Skip this step for concrete activities — they encode the object in the node type. For generic activities (`activityType: "Generic"`), list the connection's catalog and pick the object the user wants to act on.

```bash
uip is resources list "<connector-key>" --connection-id "<connection-id>" --output json \
  --output-filter "[?contains(DisplayName,'<search>')].{Name:Name,Path:Path,Custom:Custom}"
```

- `Name` — what `--detail.objectName` accepts. Case-sensitive (e.g. `"Opportunity"`, not `"opportunity"`). Don't substitute `DisplayName`.
- `Path` — API endpoint suffix (e.g. `/Opportunity`). Pair with the operation's HTTP method (Step 3) for `endpoint`.
- `Custom` — `true` for tenant-defined objects.

### Step 3 — Describe the resource and read full metadata

Run `is resources describe` to fetch and cache the full operation metadata, then **read the cached metadata file** for complete field details including descriptions, types, references, and query/path parameters. The describe summary omits some of this.

**Read `<objectName>` from the node definition in `definitions[]` (written by `node add`) — do not guess it from the node-type suffix.**

```bash
# 1. Describe to trigger fetch + cache (objectName = the activity's API object, NOT the node-type suffix)
#    Read <objectName> from the node definition FIRST (see note below) — do not batch this
#    call with `node add` / `registry get`; those calls PRODUCE the objectName this one consumes.
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json
# -> response includes metadataFile path

# 2. Read the full cached metadata
cat <metadataFile path from response>
```

> **`<objectName>` is the activity's API object name, not the node-type's trailing segment — and NOT a case-conversion of it.** Read it from the node definition copied into `definitions[]` by `node add`: `model.context[]` entry `{name:"objectName", value:"…"}` (or the `objectName` field inside the `configuration` `=jsonString:` blob). Never derive it by transforming the node-type suffix — kebab→snake (`send-email` → `send_email`) and kebab→Pascal are both guesses and both 404. Example: node type `…google-gmail.send-email` has objectName `SendEmail` (not `send_email`); `…teams.send-bot-direct-message` has objectName `bot_direct_messages` (not `send-bot-direct-message`). A 404 means wrong objectName — re-read it from the definition and retry; do NOT treat the 404 as "describe unavailable" and skip the step. Skipping describe loses `requestFields[].reference.filterPattern` and other IS-level metadata that `registry get` does not carry (see Step 4).
>
> **Sequence, don't parallelize, the objectName-dependent calls.** `<objectName>` is an OUTPUT of `node add` (it lands in `definitions[]`). Read that value before calling `is resources describe` — do not place `describe` in the same parallel Bash batch as `node add` or `registry get`, or you'll have nothing to pass but a guess. This is the failure mode behind the snake-case 404 above.

The full metadata contains:
- **`availableOperations[].method`** and **`availableOperations[].path`** — HTTP method and API endpoint path. Same value as `connectorMethodInfo.method` / `.path` from `registry get`.
- **`parameters`** — query and path parameters (may include required params not in `requestFields`, e.g. `send_as` for Slack)
- **`requestFields`** — body fields with `name`, `type`, `required`, `description`, and `reference` objects for ID resolution. Pair these field names with the `path` above (e.g. `messageToSend` for Slack `/send_message_to_channel_v2`).
- **`responseFields`** — response schema

### Step 3a — Resolve parent-field-driven custom fields (api-type ObjectActions)

**Run whenever the activity has a parent-field-driven schema** — an api-type ObjectAction in `objectActions[]` or `connectorMethodInfo.design.actions[]` (see Step 6c's support table). Applies to **every** operation with such an action — Create/Edit/Update for parent-driven required body fields AND Get/Retrieve/Query for the response-schema fields downstream nodes will reference. The base `describe` returns only static metadata; this step runs the matching ObjectAction against the live connection so the cache you author in Step 6c is a replay of a real call, not a fabrication.

Pass parent values via `-f, --field` — see [/uipath:uipath-platform — resources.md > Parent-Field-Driven Custom Fields (api-type ObjectActions)](../../../../../../uipath-platform/references/integration-service/resources.md#parent-field-driven-custom-fields-api-type-objectactions) for the full procedure, flag table, merge semantics, and error recovery.

> **Skipping is not free even when the runtime call works.** For Get/Retrieve the upstream API returns data regardless — runtime stays green. The fetch is what makes Step 6c's `customFieldsRequestDetails` honest: without it, Studio Web has no schema to render the activity's custom fields, and any downstream `$vars.<thisNode>.output.<custom-field>` resolves to undefined. `flow validate` does not catch this — it surfaces as silent design-time corruption (MST-9107-class).

Run this before Step 5 (validate required fields) and reuse the same parent-field values in Step 6c's `customFieldsRequestDetails.parameterValues` (with the encoded keys).

### Step 4 — Resolve reference fields

Check `requestFields` from the metadata for fields with a `reference` object — these require ID lookup from the connector's live data. Use `uip is resources run list` to resolve them:

> **Resolve every reference field freshly, against the current `--connection-id`, immediately before `node configure` (Step 6)** — even if you think you already know the ID from a previous flow. Reference IDs are connection-scoped and reused values fault silently at runtime. See [Reference IDs Are Connection-Scoped (CRITICAL)](../../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical) for the full mechanism and failure mode, and the top-level Anti-Patterns in [SKILL.md](../../../../../SKILL.md).

```bash
# Example: resolve Slack channel "#test-slack" to its ID
uip is resources run list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<id>" --output json
# -> { "id": "C1234567890", "name": "test-slack" }
```

The `<id>` in `--connection-id "<id>"` MUST be the connection bound to **this** flow (the one picked in Step 1), not any other connection you've used in another flow. Use the resolved IDs (not display names) — from this very `run list` call — in the flow's node `inputs`. When multiple matches exist, present them via `AskUserQuestion` with one option per match plus **"Something else"** as the last option (see the AskUserQuestion dropdown rule in [SKILL.md](../../../../../SKILL.md)).

> **Filter server-side before paginating.** If the field's `reference` carries a `filterPattern` (e.g. Teams `userId`: `"$filter=startswith(userPrincipalName,'{filter}')"`), substitute the search term for `{filter}` and pass the result as `--query` — one targeted call instead of walking a large directory. `filterPattern` appears only in `is resources describe` output; the flow `registry get` reference object strips it (keeps only `objectName`/`lookupValue`/`lookupNames`/`path`/`childPath`), so read it from the Step 3 describe metadata. Guessed params (`searchTerm=`/`where=`/`filter=`) are silently ignored. See [reference-resolution.md — Search References (filterPattern)](../../../../../../uipath-platform/references/integration-service/reference-resolution.md#search-references-filterpattern).

> **Paginate only when there is no `filterPattern`.** Use `Data.Pagination.HasMore` / `NextPageToken` with `--query "nextPage=<token>"`. Short-circuit on match. Do NOT conclude "not found" until `HasMore` is `"false"`. See [resources.md#pagination](../../../../../../uipath-platform/references/integration-service/resources.md#pagination).

**Read [/uipath:uipath-platform — Integration Service — resources.md](../../../../../../uipath-platform/references/integration-service/resources.md) for the full reference-resolution workflow** (pagination, describe failures, fallbacks).

### Step 5 — Validate required fields

**Check every required field** — both `requestFields` and `parameters` where `required: true` — against what the user provided. This is a hard gate — do NOT proceed to building until all required fields have values. For query/path parameters with a `defaultValue`, use the default if the user didn't specify one.

1. Collect all required fields from the metadata (`requestFields` + `parameters`)
2. For each required field, check if the user's prompt contains a value
3. If any required field is missing and has no `defaultValue`, **ask the user** before proceeding — list the missing fields with their `displayName` and what kind of value is expected. Free-form input is appropriate when the value space is open-ended (channel names, message bodies, IDs); when a finite set of sensible values exists, present them via `AskUserQuestion` per the dropdown rule in [SKILL.md](../../../../../SKILL.md).
4. Only after all required fields are accounted for, proceed to building

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

> **For connectors with api-type ObjectActions, run Step 3a first.** Base `describe` does not surface custom required fields driven by project / issue type / query / tenant entity. Use `-f, --field name=value` to fetch the connection-and-parent-field-specific schema before validating.

### Step 5b — Wire outputs from previous nodes

When a connector node's input field needs a value produced by an upstream node (e.g. the `Id` returned by a Create activity becomes the `recordId` for a Get-by-Id activity), the value MUST use the canonical expression form:

```
"=js:$vars.<sourceNodeId>.output.<field>"
```

Examples in `inputs.detail`:

```jsonc
"queryParameters": {
  "recordId": "=js:$vars.createEntityRecord1.output.Id"
},
"bodyParameters": {
  "ParentId":  "=js:$vars.queryAccounts1.output[0].Id",
  "BankName":  "HDFC Bank",
  "Note":      "=js:`Linked from run ${$metadata.instanceId}`"
}
```

> **The `=js:` prefix is REQUIRED on every `$vars`/`$metadata`/`$self` reference inside `bodyParameters`, `queryParameters`, and `pathParameters`.** Without it the BPMN runtime sees a literal string (`"vars.createEntityRecord1.output.Id"`) and binds it as-is to the activity input — `flow validate` passes; the failure surfaces only at `flow debug`. There is no `nodes.X.output.Y` syntax — that is an invention that silently ships as a literal string. See [node-output-wiring.md](../../../../shared/node-output-wiring.md) for the per-field-type rule and the full failure-mode table (MST-9107).

### Step 6 — Configure the node

**Run `is resources describe` (Step 3) before this step.** The full metadata tells you which fields are required, what types they expect, and which need reference resolution. Do not guess field names or skip the metadata check — required fields missing from `--detail` cause runtime errors that `flow validate` does not catch.

> **Re-configure is full rebuild, not partial merge — every `--detail` field omitted gets dropped.** Each `node configure` call constructs a fresh `inputs.detail` object (`connector-service.ts:792-803`) and a fresh `essentialConfiguration` blob from `--detail` only. Anything not in this call's `--detail` is dropped from the rewritten flow:
>
> | If you omit on re-configure | What happens |
> |---|---|
> | `bodyParameters` / `queryParameters` / `pathParameters` | Field is removed from `inputs.detail` (the prior values are NOT preserved) |
> | `filter` | `savedFilterTrees` is omitted from the `=jsonString:` blob; `queryParameters.<filterParamName>` is not re-derived |
> | `customFieldsRequestDetails` | Resets to `null` inside the `=jsonString:` blob |
>
> **Rule:** always re-pass the full intended `--detail` shape — connection plumbing + every parameter bucket + filter tree + customFieldsRequestDetails — even when changing one field. The CLI does not read the prior `inputs.detail` to fill gaps.

#### Step 6a — Detect FilterBuilder parameters

Before writing `--detail`, scan the operation's `parameters[]` (from Step 3 / `registry get`) for any entry with `design.component === "FilterBuilder"`. This applies to **any** operation, not only List operations — connectors render the FilterBuilder UI for any param flagged this way.

For every match:

- That parameter's `name` is the connector-specific filter input — most commonly `where`, sometimes `q` (Salesforce), sometimes another name. Do not assume `where`.
- **Pass a structured filter tree under `--detail.filter`** — the CLI compiles it into both halves of the contract: the runtime CEQL string at `inputs.detail.queryParameters.<name>` *and* the design-time tree at `inputs.detail.configuration.essentialConfiguration.savedFilterTrees.<name>`. Studio Web reads the latter to render the FilterBuilder UI; only `--detail.filter` populates that side.
- **Do not pass a raw CEQL string under `--detail.queryParameters.<name>`.** It populates only the runtime half — debug runs succeed but the FilterBuilder UI shows `undefined` when the activity is reopened in SW. The CLI rejects this at configure time.
- Tree shape, operator table, examples → [uipath-platform — Filter Trees (CEQL)](../../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

If the operation has no FilterBuilder parameter, server-side filtering is not supported — pass no `filter` and filter downstream (e.g. with a Script node).

**Dynamic-entity connectors (e.g. Dataservice V3) — documented CLI-limitation exception.** When filterable fields are resolved at design time via an `actionType: "api"` action keyed off a parent field (V3's `FetchObjectMetadataTenant` keyed off `tenantEntityName`), the CLI's `--detail.filter` validator rejects leaf field IDs not in static metadata. Symptom: `Failed to build filter for activity "...": Filter references field 'X' which is not present in trigger metadata`. The CLI also rejects raw `--detail.queryParameters.<filterParamName>` for FilterBuilder params on these connectors.

> **This is the only sanctioned case where `Edit` touches `inputs.detail` on a CLI-owned node** (see [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node)). The CLI cannot accept the input it itself requires for these connectors. Do not generalize this pattern to any other connector — for everything else, `node configure` is the only path. File a CLI issue if you hit a similar dynamic-entity rejection on a new connector before applying this workaround.

Workaround (Dataservice V3 / dynamic-entity FilterBuilder only):

1. `node configure` with `bodyParameters` / `queryParameters` and `customFieldsRequestDetails` — omit `filter`. This populates the rest of `inputs.detail` and the bindings the CLI normally writes.
2. `Edit` the `.flow` file to inject the two filter halves the CLI refused:
   - Runtime: `inputs.detail.queryParameters.<filterParamName>` = compiled CEQL string (e.g. `"test = 'Active'"`)
   - Design-time: `essentialConfiguration.savedFilterTrees.<filterParamName>` = structured tree (inside the `=jsonString:` blob)
3. Validate. Both halves must be present or Studio Web round-trip shows an empty FilterBuilder.
4. Note in your completion report that this node was finished via the documented CLI-limitation Edit; this is a re-configure hazard (re-running `node configure` later will drop both halves per the full-rebuild rule below).

#### Step 6b — Run configure

After adding the node with `uip maestro flow node add`, configure it with the resolved connection and field values.

**Concrete activity** (Jira `curated_create_issue` — object encoded in node type):

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "method": "POST", "endpoint": "/issues", "bodyParameters": {"fields.project.key": "ENGCE", "fields.issuetype.id": "10004"}}' \
  --output json
```

**Generic activity, list** (Salesforce `list-records` against Opportunity — object selected at configure time, no per-record input):

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "method": "GET", "endpoint": "/Opportunity", "objectName": "Opportunity"}' \
  --output json
```

**Generic activity, retrieve-by-id** (Salesforce `get-record` against Account — object plus a path parameter for the record ID):

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "method": "GETBYID", "endpoint": "/Account/{accountId}", "objectName": "Account", "pathParameters": {"accountId": "001KY000007uI02YAE"}}' \
  --output json
```

Path-parameterized GETs are a distinct shape from list/query: `endpoint` carries `{<placeholder>}` tokens and `pathParameters` supplies the values. Resolve the ID via `is resources run list <connector-key> <objectName>` (Step 4) — never paste IDs across connections (see [reference-resolution.md](../../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical)).

The `objectName` field is required for generic nodes (see "Generic vs Concrete Activities" above). The CLI fails fast with a runnable hint when it's missing on a generic node. For concrete nodes the field is ignored if supplied.

**Source of truth for `method` and `endpoint`** — pick either (both read the same upstream IS metadata):

- `registry get` (Step 2) → `connectorMethodInfo.method` and `connectorMethodInfo.path` — populated for **concrete** activities only.
- `is resources describe <connector-key> <objectName> --operation <Op>` (Step 3) → `availableOperations[].method` and `availableOperations[].path` — works for both, and is the only source for **generic** activities.

> **Method label — pass the IS describe value verbatim.** `is resources describe` sometimes returns synthesized IS-side labels (notably `"GETBYID"` for path-parameterized retrieve operations). The CLI accepts both standard HTTP verbs (`GET`, `POST`, …) and IS-side labels (`GETBYID`) — copy `operation.method` from `is resources describe` as-is and the CLI normalizes to the underlying HTTP verb internally. Don't translate by hand.

> **`flow validate` cross-checks `method` against the activity's `operation`.** If the value you pass disagrees with the operation baked into the node by `node add` (e.g. `method: "POST"` on a Retrieve activity), validate fails with `HTTP method "<X>" does not match operation "<Y>". Expected "<Z>"`. This catches stale copy-paste — fix by re-reading `operation.method` from `is resources describe` against the right `--operation`.

Body field names in `bodyParameters` come from `inputDefinition.fields[].name` (`registry get`, concrete only) or `requestFields[].name` (`is resources describe`, both).

> **Array fields — `[*]` indicates an array.** `[*]` in `requestFields[].name` (or `inputDefinition.fields[].name`) marks the field as an array; `dataType` identifies the element type. **Supported only when `[*]` is the name suffix.** Any name containing `[*].` (path segments after the `[*]`, e.g. `addresses[*].zipCode`, `contacts[*].emails[*]`) is not authorable — the canvas UI does not emit these shapes. The rule below covers `bodyParameters`, `queryParameters`, and `pathParameters`.
>
> | `requestFields[].name` | `dataType` | Authoring shape in `inputs.detail` |
> |---|---|---|
> | `fields.labels[*]` | `string` | `"fields.labels": ["shield", "p0"]` |
> | `fields.components_arrayRemap_name[*]` | `string` | `"fields.components_arrayRemap_name": ["IS Runtime"]` |
>
> **Strip `[*]` from the key; pass an array value in `--detail`.** The canvas UI is the source of truth — it omits `[*]` from the wire key on write, and the CLI follows the same convention when it builds `inputs.detail`. The runtime rejects any key containing the literal `[*]` substring as unknown (regardless of value shape), so pass the stripped form in your `node configure --detail` payload. **Distinct from `customFieldsRequestDetails.parameterValues`**, where `[*]` is encoded as `_array` — see Step 6c.
>
> **Expression values.** The serializer is purely structural (dot-expansion only; no expression evaluation, no type coercion). Choose the authoring shape based on what the expression returns at runtime:
>
> | Expression resolves to | Authoring shape | Example |
> |---|---|---|
> | The whole array | `"<field>": "=<expr>"` | `"fields.labels": "=js:$vars.allTags"` |
> | A single element to wrap | `"<field>": ["=<expr>"]` | `"fields.labels": ["=js:$vars.priorityTag"]` |

The command populates `inputs.detail` and creates workflow-level `bindings` entries. Use **resolved IDs** from Step 4, not display names. For FilterBuilder params, see Step 6a.

When inspecting the resulting `.flow`, note that the folder field is named `connectionFolderKey` in `inputs.detail`. The CLI `--detail` input accepts `folderKey` for convenience, then serializes the `.flow` field expected by validation. Do not hand-edit this field — `inputs.detail` is CLI-owned (see [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node)); re-run `node configure` to change it.

> **Do not use `filterExpression`** — that field is the trigger / JMESPath path. See [connector-trigger/impl.md](../connector-trigger/impl.md#filter-trees).

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json`

#### Step 6c — Populate custom fields (api-type ObjectActions)

A connector activity has a **parent-field-driven schema** when its valid input fields are not fixed in static metadata but are computed at design time by running an api-type ObjectAction against the IS Element Service. Examples: Jira's `Create Issue` schema depends on the project + issue type; Snowflake's `executeQuery` response columns depend on the SQL string; Dataservice V3's entity field set depends on `tenantEntityName`. The activity persists the parent-field values in `essentialConfiguration.customFieldsRequestDetails` so the runtime can replay the schema-fetch ObjectAction on each invocation. The CLI passes this through verbatim.

**How DAP determines support — check both metadata locations.** An api-type action may live at either:

- Top-level `objectActions[]` with PascalCase `ActionType: "Api"` (older shape, e.g. Jira `GenerateSchema`)
- `connectorMethodInfo.design.actions[]` with lowercase `actionType: "api"` (newer shape, e.g. Dataservice V3 `FetchObjectMetadataTenant`)

The dispatcher matches `ObjectActionType.Api === 'api'` (case-sensitive lowercase string) — both shapes go through the same `_processCustomFieldsRequestAction` code path with no per-connector branching. Always inspect both locations from `registry get` output before deciding the connector has none.

The matching action is then selected by one of two rule sources:

- **`source: field`** — the action's `rules[].refFieldName` are satisfied by user-supplied `-f, --field` values (typically SQL-style query connectors where the query string is the parent field).
- **`source: method`** — the action is declared at the operation level and matched against the operation's HTTP method (typically CRUD activities).

**Examples of supported activities.** The list below is illustrative, not exhaustive — DAP's actual support set evolves with connector metadata. Always confirm by inspecting `objectActions[]` / `connectorMethodInfo.design.actions[]` from `registry get` for the specific (connector, object, activity) you're configuring.

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

If neither metadata location contains an `actionType: "api"` / `ActionType: "Api"` entry for the activity you're configuring, it has no parent-field-driven schema — omit `customFieldsRequestDetails` (CLI emits `null`).

Each api-type entry has `name` (the `ObjectActionName`) and `apiConfiguration.{url,body}` with `{token}` placeholders — those tokens name the parent fields whose values must be in `parameterValues`.

**Token encoding rule.** Tokens are encoded via `NamingHelper.getValidIdentifier` (the IS-side identifier sanitizer) before being used as `parameterValues` keys, so they match design-property names at lookup time. Substitutions (applied longest-first):

| Match in token | Encoded as |
|---|---|
| `:::` | `_sub_` |
| `[*]` | `_array` |
| `::` | `_sub_` |
| `.` | `_sub_` |

Examples: `fields.project.key` → `fields_sub_project_sub_key`; `items[*]` → `items_array`; `tenantEntityName` → `tenantEntityName` (unchanged). When in doubt, inspect a working `.flow` for the encoded form.

> **`customFieldsRequestDetails` is COMPLEMENTARY to `bodyParameters` / `queryParameters`, not a substitute.** Same parent-field values must appear in BOTH places, with different keys:
>
> | Location | Purpose | Key shape |
> |---|---|---|
> | `bodyParameters` / `queryParameters` / `pathParameters` | Runtime input — what the connector actually sends to its API | **Raw** field names (e.g. `fields.project.key`, `tenantEntityName`) |
> | `essentialConfiguration.customFieldsRequestDetails.parameterValues` | Design-time replay cache — drives the parent-field-driven schema fetch when the activity is re-opened or re-validated | **Encoded** keys (e.g. `fields_sub_project_sub_key`, `tenantEntityName`) |
>
> Concrete (Jira Create Issue): `bodyParameters.fields.project.key = "ENGCE"` AND `parameterValues = [["fields_sub_project_sub_key", "ENGCE"]]`. Concrete (Dataservice V3): `queryParameters.tenantEntityName = ""my-entity""` AND `parameterValues = [["tenantEntityName", ""my-entity""]]`. Dropping the runtime-input copy on the assumption that the cache covers it leaves the runtime with no field value to bind — manifests as `DAP-DT-_2003 refField with name <X> not found` at activity load.

**Shape (verified against Solution 386 — Jira Create Issue):**

```json
"customFieldsRequestDetails": {
  "objectActionName": "GenerateSchema",
  "parameterValues": [
    ["fields_sub_project_sub_key", "ENGCE"],
    ["fields_sub_issuetype_sub_id", "3"]
  ]
}
```

Rules:

- camelCase keys (`objectActionName`, `parameterValues`). PascalCase rejected at validate time.
- `parameterValues` is an **array of `[key, value]` tuples** — never an object map. The IS-side serializer emits a `Map<string,string|null>` via `Array.from(entries())`; the CLI rejects object-map form.
- Tuple value is `string` or `null`. Use `null` for tokens the user has not yet set.
- The CLI does NOT validate ObjectAction existence or token coverage at configure time. **Always run Step 3a first** with the planned parent-field combination — if it errors with `No api-type ObjectAction matched for fields [...]`, the cache you're about to write is wrong (adjust tokens or action name); if it succeeds, the response confirms the action and tokens are real, and you author `customFieldsRequestDetails` from that result, not from memory or doc examples. Read `apiConfiguration.url` / `body` from the matched action (top-level `objectActions[]` OR `connectorMethodInfo.design.actions[]`) to enumerate required tokens.

**CLI invocation — pass BOTH halves.** The runtime input bucket (`bodyParameters` / `queryParameters` / `pathParameters`) AND the design-time cache (`customFieldsRequestDetails`) must both appear in the same `--detail`. Omitting the runtime bucket is the most common mistake — the cache alone does not feed the connector at runtime.

Jira Create Issue — `source: method` (raw `fields.project.key` in body + encoded `fields_sub_project_sub_key` in cache):

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat <<'JSON'
{
  "connectionId": "<id>",
  "folderKey": "<key>",
  "method": "POST",
  "endpoint": "/curated_create_issue",
  "bodyParameters": {
    "fields.project.key": "ENGCE",
    "fields.issuetype.id": "3",
    "fields.summary": "Created from Maestro"
  },
  "customFieldsRequestDetails": {
    "objectActionName": "GenerateSchema",
    "parameterValues": [
      ["fields_sub_project_sub_key", "ENGCE"],
      ["fields_sub_issuetype_sub_id", "3"]
    ]
  }
}
JSON
)" --output json
```

Snowflake Execute Query — `source: field` (the SQL string is the parent field; raw `query` in body + same key encoded — unchanged here, no dots — in cache):

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

Dataservice V3 Query Entity Records — `source: method` (raw `tenantEntityName` in queryParameters + same key encoded — unchanged here, no dots — in cache):

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat <<'JSON'
{
  "connectionId": "<id>",
  "folderKey": "<key>",
  "method": "POST",
  "endpoint": "/v3/QueryEntityRecords/query",
  "queryParameters": {
    "entityScope": "tenant",
    "tenantEntityName": ""my-entity""
  },
  "customFieldsRequestDetails": {
    "objectActionName": "FetchObjectMetadataTenant",
    "parameterValues": [
      ["tenantEntityName", ""my-entity""]
    ]
  }
}
JSON
)" --output json
```

The CLI embeds the payload verbatim in `essentialConfiguration.customFieldsRequestDetails` inside the `=jsonString:` blob. Top-level `inputs.detail.customFieldsRequestDetails` is NOT set — the field lives only inside `essentialConfiguration`.

---

## IS CLI Commands

```bash
# Connections
uip is connections list "<connector-key>" --all-folders --output json      # discover connections (--all-folders is mandatory)
uip is connections ping "<connection-id>" --output json      # verify connection health
uip is connections create "<connector-key>"                  # create new connection (interactive)

# Enriched node metadata (pass connection for custom fields)
uip maestro flow registry get <node-type> --connection-id <connection-id> --output json

# Resource description and metadata
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json

# Reference resolution
uip is resources run list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json

# List all available connectors
uip is connectors list --output json
```

Run `uip is connections --help` or `uip is resources --help` for all options.

---

## Bindings — top-level `.flow` `bindings[]`

When a flow uses connector nodes, the runtime needs to know **which authenticated connection** to use for each connector. Bindings are authored in the flow's **top-level `bindings[]` array** (a sibling of `nodes`, `edges`, `definitions`). At `flow debug` / `flow pack` time the CLI regenerates `content/bindings_v2.json` from these entries.

> **Never edit `bindings_v2.json` directly.** Any manual edits are overwritten on the next debug/pack. All authoring flows through the `.flow` file's top-level `bindings[]`.

### How connector nodes reference bindings

The connector node's **definition** (the manifest copied from `uip maestro flow registry get` into `definitions[]`) carries a `model.context[]` template like this. **Leave the definition exactly as the registry returns it** — do NOT rewrite `<bindings.*>` placeholders inside the definition, and do NOT author `model.context[]` on the instance:

```json
"context": [
  { "name": "connectorKey", "type": "string", "value": "uipath-atlassian-jira" },
  { "name": "connection", "type": "string", "value": "<bindings.uipath-atlassian-jira connection>" },
  { "name": "folderKey", "type": "string", "value": "<bindings.FolderKey>" }
]
```

At BPMN emit time, the runtime rewrites each `<bindings.{name}>` placeholder to `=bindings.{id}` by finding a top-level `bindings[]` entry whose `name` matches the placeholder. For connectors the definition's `model.bindings.resourceKey` is typically unset, so matching is **name-only** within the `resource: "Connection"` candidate set.

> **Matching differs from resource nodes.** For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the definition's `model.bindings.resourceKey` is set to `<FolderPath>.<ResourceName>`, so placeholder matching is scoped by `(name, resourceKey)`. For connector nodes, `resourceKey` on the definition is typically unset, so matching is name-only — the `<CONNECTOR_KEY> connection` placeholder must be unique per connector in the flow. Don't confuse the two patterns.

### Top-level `bindings[]` shape (CLI-emitted; reference only)

`uip maestro flow node configure` populates these entries — you do not author them by hand. The schema below is the shape the CLI emits, for **inspection** when debugging a flow's binding state and as the planned shape for the **No-Live-Tenant** flow's sidecar `<nodeId>.detail.json` (see § No-Live-Tenant / Planned Configuration above). Per the [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node) rules, `bindings[]` is part of the CLI-owned envelope for connector / connector-trigger / managed HTTP nodes.

For every unique connection used in the flow, `node configure` appends **two entries** to top-level `bindings[]`:

```json
"bindings": [
  {
    "id": "<CONN_BINDING_ID>",
    "name": "<CONNECTOR_KEY> connection",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "<CONNECTION_UUID>",
    "default": "<CONNECTION_UUID>",
    "propertyAttribute": "ConnectionId"
  },
  {
    "id": "<FOLDER_BINDING_ID>",
    "name": "FolderKey",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "<CONNECTION_UUID>",
    "default": "<FOLDER_KEY>",
    "propertyAttribute": "FolderKey"
  }
]
```

| Field | Value |
|-------|-------|
| `id` | Unique string within the file. Descriptive (e.g. `bJiraConn`) or short random (e.g. `bKEFLMRB2`). |
| `name` (connection binding) | The IS connection name (e.g. `"chandu.lella@uipath.com #3"`). `uip maestro flow node configure` fetches this from IS automatically — this is the supported path. The placeholder form `"<CONNECTOR_KEY> connection"` appears in the table for reference only (e.g. when inspecting a flow whose bindings have not yet been configured); it must match the definition's `model.context[].connection` placeholder (without the `<bindings.` prefix and `>` suffix). |
| `name` (folder binding) | Literal `"FolderKey"` — matches `<bindings.FolderKey>`. |
| `type` | Always `"string"`. |
| `resource` | Always `"Connection"` — capital C, case-sensitive. |
| `resourceKey` | The connection UUID from `uip is connections list`. **Same UUID on both bindings.** |
| `default` | Connection binding → connection UUID. Folder binding → folder key. |
| `propertyAttribute` | `"ConnectionId"` or `"FolderKey"` — case matters. |

The connector node instance carries no `model` block and no binding/context data. `uip maestro flow node configure` populates only `inputs.detail` on the instance and appends the two top-level `bindings[]` entries. The connection UUID is held on the binding entry (`resourceKey`), not on the node.

> **CLI side-effect — duplicate empty bindings.** `node configure` currently appends placeholder entries with `resourceKey: ""` and no `default` alongside the resolved pair (4 entries per configure call instead of 2). Validate passes; they're harmless but verbose. Remove the empty pair via `Edit` after configure if you care about clean diffs.

**Share bindings across nodes using the same connection.** If two connector nodes share the same `<CONNECTION_UUID>`, reuse the same two binding entries — do not add duplicates. Matching is by `name` only (the `<CONNECTOR_KEY> connection` placeholder is unique per connector), so any node whose definition resolves against `<bindings.<CONNECTOR_KEY> connection>` picks up the shared binding pair.

### Single-connector example (Jira)

```json
"bindings": [
  {
    "id": "bJiraConn",
    "name": "uipath-atlassian-jira connection",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "7622a703-5d85-4b55-849b-6c02315b9e6e",
    "default": "7622a703-5d85-4b55-849b-6c02315b9e6e",
    "propertyAttribute": "ConnectionId"
  },
  {
    "id": "bJiraFolder",
    "name": "FolderKey",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "7622a703-5d85-4b55-849b-6c02315b9e6e",
    "default": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "propertyAttribute": "FolderKey"
  }
]
```

### Multi-connector example (Jira + Slack)

Two unique connections → four entries in `bindings[]` (two per connection):

```json
"bindings": [
  { "id": "bJiraConn",   "name": "uipath-atlassian-jira connection",   "type": "string", "resource": "Connection", "resourceKey": "7622a703-5d85-4b55-849b-6c02315b9e6e", "default": "7622a703-5d85-4b55-849b-6c02315b9e6e", "propertyAttribute": "ConnectionId" },
  { "id": "bJiraFolder", "name": "FolderKey",                          "type": "string", "resource": "Connection", "resourceKey": "7622a703-5d85-4b55-849b-6c02315b9e6e", "default": "folder-uuid-for-jira",                "propertyAttribute": "FolderKey" },
  { "id": "bSlackConn",  "name": "uipath-salesforce-slack connection", "type": "string", "resource": "Connection", "resourceKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "default": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "propertyAttribute": "ConnectionId" },
  { "id": "bSlackFolder","name": "FolderKey",                          "type": "string", "resource": "Connection", "resourceKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "default": "folder-uuid-for-slack",               "propertyAttribute": "FolderKey" }
]
```

Both `FolderKey` entries share the same `name` but have distinct `resourceKey`s — that's how the runtime keeps them separate.

### Generated `bindings_v2.json` (reference only — do not edit)

At debug/pack time, the CLI derives `content/bindings_v2.json` from the top-level `bindings[]` above. One `Connection` resource per unique `resourceKey`; the `FolderKey` bindings are absorbed as metadata (they do not produce standalone resource entries). The generated output looks like:

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "7622a703-5d85-4b55-849b-6c02315b9e6e",
      "id": "Connection7622a703-5d85-4b55-849b-6c02315b9e6e",
      "value": {
        "ConnectionId": {
          "defaultValue": "7622a703-5d85-4b55-849b-6c02315b9e6e",
          "isExpression": false,
          "displayName": "my-jira-connection"
        }
      },
      "metadata": {
        "ActivityName": "Create Issue",
        "BindingsVersion": "2.2",
        "DisplayLabel": "my-jira-connection",
        "UseConnectionService": "true",
        "Connector": "uipath-atlassian-jira"
      }
    }
  ]
}
```

- `id` is always `"Connection" + <resourceKey>` (concatenated, no separator) — generated, not authored.
- `metadata.Connector` is derived from the definition's `model.context[].connectorKey`.
- `metadata.ActivityName` comes from the matched node's `display.label`.

### Other binding resource types (triggers, queues, scheduled)

For connector-trigger flows, the same pattern applies — top-level `bindings[]` entries with additional metadata; the CLI derives `EventTrigger` and `Property` resources for `bindings_v2.json`. See [connector-trigger/impl.md](../connector-trigger/impl.md) for the trigger-specific shape.

| Generated `bindings_v2.json` resource | Authored via | Key source fields |
|---------------------------------------|--------------|-------------------|
| `Connection` | Top-level `bindings[]` with `resource: "Connection"`, `propertyAttribute: "ConnectionId"` | Covered above |
| `EventTrigger` | Top-level `bindings[]` + the trigger node itself | See connector-trigger plugin |
| `Property` | Trigger node's `model.inputs.filterFields` | See connector-trigger plugin |
| `Queue` / `TimeTrigger` | Specific trigger types | See relevant trigger plugin |

> **Never hardcode connection IDs.** Always fetch them from IS at authoring time. Connection IDs are tenant-specific and change across environments.

---

## Debug

### Common Errors

| Error | Cause | Fix |
| --- | --- | --- |
| No connection found | Connection not bound — top-level `bindings[]` missing or `resourceKey` doesn't match the node | Run Step 1 above to bind a connection; verify both entries (`ConnectionId` + `FolderKey`) are in the top-level `bindings[]` |
| Connection ping failed | Connection expired or misconfigured | Re-authenticate the connection in the IS portal |
| Missing `inputs.detail` | Node added but not configured | Run `uip maestro flow node configure` with the detail JSON (Step 6) |
| Reference field has display name instead of ID | `uip is resources run list` was skipped | Resolve the reference field to get the actual ID (Step 4) |
| Node faults at runtime with "resource not found" or similar after a clean build and validate | Reference field uses an ID scoped to a **different** connection (common when copying from a prior flow in the same session — e.g., a Slack channel ID from workspace A pasted into a node bound to workspace B's connection) | Re-run `uip is resources run list "<connector-key>" "<objectName>" --connection-id <CURRENT_CONNECTION_ID>`, extract the fresh ID, update `bodyParameters` / `queryParameters` in `--detail`, re-run `node configure`, re-debug. See Step 4 and the top-level Anti-Pattern on reference-ID reuse in [SKILL.md](../../../../../SKILL.md). |
| Required field missing at runtime | Required input field not provided | Check metadataFile for all `required: true` fields in both `requestFields` and `parameters` |
| `$vars` expression unresolvable | Node outputs block missing or node not connected | Verify the node has edges and upstream outputs are correctly referenced |
| `connectorMethodInfo` missing method/path | Used `registry get` without `--connection-id` | Re-run with `--connection-id` for enriched metadata (Step 2) |
| `bindings_v2.json` malformed or stale | It was hand-edited (the CLI overwrites edits on next debug/pack), or top-level `bindings[]` was mutated by hand | Never edit `bindings_v2.json` directly. Re-run `uip maestro flow node configure` on the affected connector node(s) so the CLI re-emits top-level `bindings[]`; `bindings_v2.json` is regenerated from those at the next debug/pack. Compare the emitted shape against the CLI-emitted reference in § Top-level `bindings[]` shape. |
| Connector key not found | Wrong key name | Run `uip is connectors list --output json` — keys are often prefixed with `uipath-` |
| FilterBuilder UI shows `undefined` when activity is reopened in Studio Web; flow runs at debug | A raw `queryParameters.<filterParamName>` string was passed instead of a structured filter tree, so `essentialConfiguration.savedFilterTrees.<filterParamName>` is empty. The runtime side works but Studio Web has no tree to render. | Re-run `uip maestro flow node configure` with `--detail '{"filter": {...tree...}}'` — the CLI populates both halves. See Step 6a above and [uipath-platform — Filter Trees (CEQL)](../../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). |
| `node configure` fails with `'<name>' is a FilterBuilder parameter — pass a structured filter tree under --detail.filter` | Same root cause — raw string under `queryParameters` for a FilterBuilder param | Move the value into `--detail.filter` as a structured tree. The CLI catches this at configure time so it never reaches Studio Web. |
| `node configure` fails with `customFieldsRequestDetails.parameterValues must be an array of [key, value] tuples, not an object map` | Wrote `parameterValues: {key: value}` (object map). Studio Web emits its `Map<string,string\|null>` as `Array.from(entries())` — tuples, not object | Convert to tuples: `[["key", "value"], ...]`. See Step 6c. |
| Custom fields fault at runtime with token unresolved | A `{token}` in `objectActions[].apiConfiguration.url` or `body` has no entry in `parameterValues` | Re-read the ObjectAction's `apiConfiguration` placeholders, add the missing tuple to `parameterValues`. CLI does not validate token coverage. |
| `node configure` fails with `customFieldsRequestDetails has unknown keys: ObjectActionName, ParameterValues` | PascalCase inner keys instead of camelCase | Use `objectActionName` / `parameterValues`. Studio Web emits camelCase; PascalCase is rejected. |
| Field rejected at runtime as unknown (e.g. `"unknown field 'fields.labels[*]'"`) after a clean `flow validate` | `[*]` was left in the `bodyParameters` / `queryParameters` / `pathParameters` key. `[*]` is an array marker from `requestFields[].name`, not part of the wire key. | Strip `[*]` from the key in your `--detail` payload, pass an array value matching the field's `dataType`, and re-run `node configure`. Fields with `[*].` (segments after the `[*]`) are not authorable. See the array-fields table in Step 6b. |

### Debug Tips

1. **Always check top-level `bindings[]` in the `.flow` file** — connector nodes silently fail if a binding is missing or malformed. Compare against the CLI-emitted `bindings[]` shape documented above (§ Top-level `bindings[]` shape). Do not inspect `bindings_v2.json` as ground truth; it is regenerated from the `.flow` on every debug/pack.
2. **Compare inputs against metadataFile** — the full metadata (from `is resources describe`) has every field with types, descriptions, and whether it's required
3. **`flow validate` does NOT catch connector-specific issues** — validation only checks JSON schema and graph structure. Missing `inputs.detail` fields, wrong reference IDs, and expired connections are caught only at runtime (`flow debug`)
4. **If a connector key doesn't work** — list all connectors: `uip is connectors list --output json`. Keys are often prefixed with `uipath-`
5. **Query/path parameters** — some required parameters appear only in the metadataFile `parameters` section, not in `requestFields`. Check both.
6. **`node configure` populates bindings automatically** — it appends the two top-level `bindings[]` entries and populates `inputs.detail`. The generated `bindings_v2.json` follows from these at debug/pack time. If you cannot run `node configure` (no live tenant, sandbox forbids it, planning-only request), record the planned binding entries in the sidecar `<nodeId>.detail.json` per the No-Live-Tenant flow above — do not author `bindings[]` directly on the `.flow` as a substitute, and note that the flow will not pass `flow validate` until a real `node configure` runs.
