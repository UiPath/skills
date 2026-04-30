# Connector Activity Nodes — Implementation

How to configure connector activity nodes: connection binding, enriched metadata, reference field resolution, and debugging. Connection bindings are authored in the flow's top-level `bindings[]` — `bindings_v2.json` is regenerated from them at debug/pack time and should never be hand-edited.

For generic node/edge add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). This guide covers the connector-specific configuration workflow that must follow the generic node add.

## How Connector Nodes Differ from OOTB

1. **Connection binding required** — every connector node needs an IS connection (OAuth, API key, etc.) authored in the flow's top-level `bindings[]` (which the CLI regenerates into `bindings_v2.json` at debug/pack time). Without it, the node cannot authenticate.
2. **Enriched metadata via `--connection-id`** — call `registry get` with `--connection-id` to get connection-aware field metadata. Without it, only base fields are returned — custom fields, dynamic enums, and reference resolution are missing.
3. **`inputs.detail` object** — connector nodes store operation-specific configuration in `inputs.detail`, populated by `uip maestro flow node configure`:
   - `connectionId` — the bound IS connection UUID
   - `folderKey` — the Orchestrator folder key
   - `method` — HTTP method from `connectorMethodInfo` (e.g., `POST`)
   - `endpoint` — API path from `connectorMethodInfo` (e.g., `/issues`)
   - `bodyParameters` — field-value pairs for the request body
   - `queryParameters` — field-value pairs for query string parameters

---

## Critical: Connector Definition Must Include `form`

> When writing a connector definition in the `definitions` array, you **must** include the `form` field from the `registry get` output. The `form` contains a `connectorDetail.configuration` JSON string that `uip maestro flow node configure` reads to build the runtime configuration. Without it, `node configure` fails with `No instanceParameters found in definition`. Copy the full `form` object from `uip maestro flow registry get <nodeType> --output json` → `Data.Node.form` into your definition.

## Configuration Workflow

Follow these steps for every connector node.

### Step 1 — Fetch and bind a connection

For each connector, extract the connector key from the node type (`uipath.connector.<connector-key>.<activity-name>`) and fetch a connection.

```bash
# 1. List available connections
uip is connections list "<connector-key>" --folder-key "<folder-key>" --output json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)

# 3. Verify the connection is healthy
uip is connections ping "<connection-id>" --output json
```

**If a connector key fails**, list all available connectors to find the correct key: `uip is connectors list --output json`. Connector keys are often prefixed (e.g., `uipath-<service>`).

**Read [/uipath:uipath-platform — Integration Service — connections.md](../../../../uipath-platform/references/integration-service/connections.md) for connection selection rules** (default preference, `--refresh` retry on empty results, HTTP fallback, multi-connection disambiguation, no-connection recovery, ping verification).

### Step 2 — Get enriched node definitions with connection

Call `registry get` with `--connection-id` to fetch connection-aware metadata including custom fields:

```bash
uip maestro flow registry get <nodeType> --connection-id <connection-id> --output json
```

This returns enriched `inputDefinition.fields` and `outputDefinition.fields` with accurate type, required, description, enum, and `reference` info. Without `--connection-id`, only standard/base fields are returned.

The response also includes `connectorMethodInfo` with the real HTTP `method` (e.g. `GET`, `POST`) and `path` template (e.g. `/ConversationsInfo/{conversationsInfoId}`). **Save these two values** — you must pass them to `node configure` later.

### Step 3 — Describe the resource and read full metadata

Run `is resources describe` to fetch and cache the full operation metadata, then **read the cached metadata file** for complete field details including descriptions, types, references, and query/path parameters. The describe summary omits some of this.

```bash
# 1. Describe to trigger fetch + cache (extract the objectName from the connector node type)
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json
# -> response includes metadataFile path

# 2. Read the full cached metadata
cat <metadataFile path from response>
```

The full metadata contains:
- **`parameters`** — query and path parameters (may include required params not in `requestFields`, e.g. `send_as` for Slack)
- **`requestFields`** — body fields with `type`, `required`, `description`, and `reference` objects for ID resolution
- **`path`** — the API endpoint path (also available in `connectorMethodInfo` from `registry get`)
- **`responseFields`** — response schema

### Step 4 — Resolve reference fields

Check `requestFields` from the metadata for fields with a `reference` object — these require ID lookup from the connector's live data. Use `uip is resources execute list` to resolve them:

> **Resolve every reference field freshly, against the current `--connection-id`, immediately before `node configure` (Step 6)** — even if you think you already know the ID from a previous flow. Reference IDs are connection-scoped and reused values fault silently at runtime. See [Reference IDs Are Connection-Scoped (CRITICAL)](../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical) for the full mechanism and failure mode, and the top-level Anti-Patterns in [SKILL.md](../../../SKILL.md).

```bash
# Example: resolve Slack channel "#test-slack" to its ID
uip is resources execute list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<id>" --output json
# -> { "id": "C1234567890", "name": "test-slack" }
```

The `<id>` in `--connection-id "<id>"` MUST be the connection bound to **this** flow (the one picked in Step 1), not any other connection you've used in another flow. Use the resolved IDs (not display names) — from this very `execute list` call — in the flow's node `inputs`. Present options to the user when multiple matches exist.

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items) and surfaces `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. If the target isn't on the first page, re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit as soon as the target name matches — don't pull every page.

**Read [/uipath:uipath-platform — Integration Service — resources.md](../../../../uipath-platform/references/integration-service/resources.md) for the full reference resolution workflow**, including: identifying reference fields, dependency chains (resolve parent fields before children), pagination, describe failures, and fallback strategies.

### Step 5 — Validate required fields

**Check every required field** — both `requestFields` and `parameters` where `required: true` — against what the user provided. This is a hard gate — do NOT proceed to building until all required fields have values. For query/path parameters with a `defaultValue`, use the default if the user didn't specify one.

1. Collect all required fields from the metadata (`requestFields` + `parameters`)
2. For each required field, check if the user's prompt contains a value
3. If any required field is missing and has no `defaultValue`, **ask the user** before proceeding — list the missing fields with their `displayName` and what kind of value is expected
4. Only after all required fields are accounted for, proceed to building

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

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

> **The `=js:` prefix is REQUIRED on every `$vars`/`$metadata`/`$self` reference inside `bodyParameters`, `queryParameters`, and `pathParameters`.** Without it the BPMN runtime sees a literal string (`"vars.createEntityRecord1.output.Id"`) and binds it as-is to the activity input — `flow validate` passes; the failure surfaces only at `flow debug`. There is no `nodes.X.output.Y` syntax — that is an invention that silently ships as a literal string. See [node-output-wiring.md](../../shared/node-output-wiring.md) for the per-field-type rule and the full failure-mode table (MST-9107).

### Step 6 — Configure the node

**Run `is resources describe` (Step 3) before this step.** The full metadata tells you which fields are required, what types they expect, and which need reference resolution. Do not guess field names or skip the metadata check — required fields missing from `--detail` cause runtime errors that `flow validate` does not catch.

#### Step 6a — Detect FilterBuilder parameters

Before writing `--detail`, scan the operation's `parameters[]` (from Step 3 / `registry get`) for any entry with `design.component === "FilterBuilder"`. This applies to **any** operation, not only List operations — connectors render the FilterBuilder UI for any param flagged this way.

For every match:

- That parameter's `name` is the connector-specific filter input — most commonly `where`, sometimes `q` (Salesforce), sometimes another name. Do not assume `where`.
- **Pass a structured filter tree under `--detail.filter`** — the CLI compiles it into both halves of the contract: the runtime CEQL string at `inputs.detail.queryParameters.<name>` *and* the design-time tree at `inputs.detail.configuration.essentialConfiguration.savedFilterTrees.<name>`. Studio Web reads the latter to render the FilterBuilder UI; only `--detail.filter` populates that side.
- **Do not pass a raw CEQL string under `--detail.queryParameters.<name>`.** It populates only the runtime half — debug runs succeed but the FilterBuilder UI shows `undefined` when the activity is reopened in SW. The CLI rejects this at configure time.
- Tree shape, operator table, examples → [uipath-platform — Filter Trees (CEQL)](../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

If the operation has no FilterBuilder parameter, server-side filtering is not supported — pass no `filter` and filter downstream (e.g. with a Script node).

#### Step 6b — Run configure

After adding the node with `uip maestro flow node add`, configure it with the resolved connection and field values:

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "method": "POST", "endpoint": "/issues", "bodyParameters": {"fields.project.key": "ENGCE", "fields.issuetype.id": "10004"}}' \
  --output json
```

The `method` and `endpoint` values come from `connectorMethodInfo` in the `registry get` response (Step 2). The command populates `inputs.detail` and creates workflow-level `bindings` entries. Use **resolved IDs** from Step 4, not display names. For FilterBuilder params, see Step 6a.

> **Do not use `filterExpression`** — that field is the trigger / JMESPath path. See [connector-trigger/impl.md](../connector-trigger/impl.md#filter-trees).

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json`

---

## IS CLI Commands

```bash
# Connections
uip is connections list "<connector-key>" --folder-key "<folder-key>" --output json      # list connections for a connector
uip is connections ping "<connection-id>" --output json      # verify connection health
uip is connections create "<connector-key>"                  # create new connection (interactive)

# Enriched node metadata (pass connection for custom fields)
uip maestro flow registry get <nodeType> --connection-id <connection-id> --output json

# Resource description and metadata
uip is resources describe "<connector-key>" "<objectName>" \
  --connection-id "<id>" --operation Create --output json

# Reference resolution
uip is resources execute list "<connector-key>" "<resource>" \
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

### Authoring top-level `bindings[]`

For every unique connection used in the flow, add **two entries** to top-level `bindings[]`:

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
| `name` (connection binding) | The IS connection name (e.g. `"chandu.lella@uipath.com #3"`). `uip maestro flow node configure` fetches this from IS automatically. When adding bindings by hand, use `"<CONNECTOR_KEY> connection"` as a placeholder — it must match the definition's `model.context[].connection` placeholder (without the `<bindings.` prefix and `>` suffix). |
| `name` (folder binding) | Literal `"FolderKey"` — matches `<bindings.FolderKey>`. |
| `type` | Always `"string"`. |
| `resource` | Always `"Connection"` — capital C, case-sensitive. |
| `resourceKey` | The connection UUID from `uip is connections list`. **Same UUID on both bindings.** |
| `default` | Connection binding → connection UUID. Folder binding → folder key. |
| `propertyAttribute` | `"ConnectionId"` or `"FolderKey"` — case matters. |

The connector node instance carries no `model` block and no binding/context data. `uip maestro flow node configure` populates only `inputs.detail` on the instance and appends the two top-level `bindings[]` entries. The connection UUID is held on the binding entry (`resourceKey`), not on the node.

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
| Reference field has display name instead of ID | `uip is resources execute list` was skipped | Resolve the reference field to get the actual ID (Step 4) |
| Node faults at runtime with "resource not found" or similar after a clean build and validate | Reference field uses an ID scoped to a **different** connection (common when copying from a prior flow in the same session — e.g., a Slack channel ID from workspace A pasted into a node bound to workspace B's connection) | Re-run `uip is resources execute list "<connector-key>" "<objectName>" --connection-id <CURRENT_CONNECTION_ID>`, extract the fresh ID, update `bodyParameters` / `queryParameters` in `--detail`, re-run `node configure`, re-debug. See Step 4 and the top-level Anti-Pattern on reference-ID reuse in [SKILL.md](../../../SKILL.md). |
| Required field missing at runtime | Required input field not provided | Check metadataFile for all `required: true` fields in both `requestFields` and `parameters` |
| `$vars` expression unresolvable | Node outputs block missing or node not connected | Verify the node has edges and upstream outputs are correctly referenced |
| `connectorMethodInfo` missing method/path | Used `registry get` without `--connection-id` | Re-run with `--connection-id` for enriched metadata (Step 2) |
| `bindings_v2.json` malformed or stale | It was hand-edited (the CLI overwrites edits on next debug/pack) | Never edit `bindings_v2.json` directly — author bindings in the top-level `.flow` `bindings[]` instead. Compare your top-level `bindings[]` against the schema and examples in the Bindings section above |
| Connector key not found | Wrong key name | Run `uip is connectors list --output json` — keys are often prefixed with `uipath-` |
| FilterBuilder UI shows `undefined` when activity is reopened in Studio Web; flow runs at debug | A raw `queryParameters.<filterParamName>` string was passed instead of a structured filter tree, so `essentialConfiguration.savedFilterTrees.<filterParamName>` is empty. The runtime side works but Studio Web has no tree to render. | Re-run `uip maestro flow node configure` with `--detail '{"filter": {...tree...}}'` — the CLI populates both halves. See Step 6a above and [uipath-platform — Filter Trees (CEQL)](../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). |
| `node configure` fails with `'<name>' is a FilterBuilder parameter — pass a structured filter tree under --detail.filter` | Same root cause — raw string under `queryParameters` for a FilterBuilder param | Move the value into `--detail.filter` as a structured tree. The CLI catches this at configure time so it never reaches Studio Web. |

### Debug Tips

1. **Always check top-level `bindings[]` in the `.flow` file** — connector nodes silently fail if a binding is missing or malformed. Compare against the Authoring top-level `bindings[]` schema above. Do not inspect `bindings_v2.json` as ground truth; it is regenerated from the `.flow` on every debug/pack.
2. **Compare inputs against metadataFile** — the full metadata (from `is resources describe`) has every field with types, descriptions, and whether it's required
3. **`flow validate` does NOT catch connector-specific issues** — validation only checks JSON schema and graph structure. Missing `inputs.detail` fields, wrong reference IDs, and expired connections are caught only at runtime (`flow debug`)
4. **If a connector key doesn't work** — list all connectors: `uip is connectors list --output json`. Keys are often prefixed with `uipath-`
5. **Query/path parameters** — some required parameters appear only in the metadataFile `parameters` section, not in `requestFields`. Check both.
6. **`node configure` populates bindings automatically** — it appends the two top-level `bindings[]` entries and populates `inputs.detail`. The generated `bindings_v2.json` follows from these at debug/pack time. In Direct JSON mode, author the top-level `bindings[]` yourself (see Authoring section above).
