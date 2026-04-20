# Connector Activity Nodes — Implementation

How to configure connector activity nodes: connection binding, enriched metadata, reference field resolution, `bindings_v2.json` schema, and debugging.

For generic node/edge add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). This guide covers the connector-specific configuration workflow that must follow the generic node add.

## How Connector Nodes Differ from OOTB

1. **Connection binding required** — every connector node needs an IS connection (OAuth, API key, etc.) bound in `bindings_v2.json`. Without it, the node cannot authenticate.
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

**If `connections list` returns empty**, the CLI scoped to Personal Workspace by default — check other folders with `uip or folders list` + `--folder-key <key>` (Shared is the common case). If still not found, the connection doesn't exist — tell the user, and have them create one via the IS portal or `uip is connections create "<connector-key>"`.

**Read [/uipath:uipath-platform — Integration Service — connections.md](/uipath:uipath-platform) for connection selection rules** (default preference, HTTP fallback, multi-connection disambiguation, no-connection recovery, ping verification).

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

```bash
# Example: resolve Slack channel "#test-slack" to its ID
uip is resources execute list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<id>" --output json
# -> { "id": "C1234567890", "name": "test-slack" }
```

Use the resolved IDs (not display names) in the flow's node `inputs`. Present options to the user when multiple matches exist.

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items) and surfaces `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. If the target isn't on the first page, re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit as soon as the target name matches — don't pull every page.

**Read [/uipath:uipath-platform — Integration Service — resources.md](/uipath:uipath-platform) for the full reference resolution workflow**, including: identifying reference fields, dependency chains (resolve parent fields before children), pagination, describe failures, and fallback strategies.

### Step 5 — Validate required fields

**Check every required field** — both `requestFields` and `parameters` where `required: true` — against what the user provided. This is a hard gate — do NOT proceed to building until all required fields have values. For query/path parameters with a `defaultValue`, use the default if the user didn't specify one.

1. Collect all required fields from the metadata (`requestFields` + `parameters`)
2. For each required field, check if the user's prompt contains a value
3. If any required field is missing and has no `defaultValue`, **ask the user** before proceeding — list the missing fields with their `displayName` and what kind of value is expected
4. Only after all required fields are accounted for, proceed to building

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

### Step 6 — Configure the node

**Run `is resources describe` (Step 3) before this step.** The full metadata tells you which fields are required, what types they expect, and which need reference resolution. Do not guess field names or skip the metadata check — required fields missing from `--detail` cause runtime errors that `flow validate` does not catch.

After adding the node with `uip maestro flow node add`, configure it with the resolved connection and field values:

```bash
uip maestro flow node configure <file> <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "method": "POST", "endpoint": "/issues", "bodyParameters": {"fields.project.key": "ENGCE", "fields.issuetype.id": "10004"}}'
```

The `method` and `endpoint` values come from `connectorMethodInfo` in the `registry get` response (Step 2). The command populates `inputs.detail` and creates workflow-level `bindings` entries. Use **resolved IDs** from Step 4, not display names.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)"`

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

## Bindings — `bindings_v2.json`

When a flow uses connector nodes, the runtime needs to know **which authenticated connection** to use for each connector. This is configured in `content/bindings_v2.json`.

### How connector nodes reference bindings

Each connector node's `model.context` contains a `connection` entry with a placeholder:

```json
{ "name": "connection", "type": "string", "value": "<bindings.uipath-atlassian-jira connection>" }
```

At runtime, the engine resolves this placeholder by looking up `bindings_v2.json` for a `Connection` resource whose `metadata.Connector` matches `uipath-atlassian-jira`.

### bindings_v2.json schema

```json
{
  "version": "2.0",
  "resources": []
}
```

Each element in `resources` is a binding resource. For connector activities, the key resource type is **`Connection`**.

### Connection resource

| Field | Description |
|-------|-------------|
| `resource` | Always `"Connection"` |
| `key` | The connection ID (UUID from `uip is connections list`) |
| `id` | `"Connection" + <connection-id>` (concatenated, no separator) |
| `value.ConnectionId.defaultValue` | The actual connection ID |
| `value.ConnectionId.isExpression` | Always `false` |
| `value.ConnectionId.displayName` | Human-readable label (e.g., `"uipath-atlassian-jira connection"`) |
| `metadata.UseConnectionService` | Always `"true"` |
| `metadata.Connector` | Connector key (e.g., `"uipath-atlassian-jira"`) — must match the node's `model.context.connectorKey` |
| `metadata.ActivityName` | Display name of the activity using this connection |
| `metadata.BindingsVersion` | Always `"2.2"` |
| `metadata.DisplayLabel` | Same as `value.ConnectionId.displayName` |

### Single connector example (Jira)

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
          "displayName": "uipath-atlassian-jira connection"
        }
      },
      "metadata": {
        "ActivityName": "Create Issue",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-atlassian-jira connection",
        "UseConnectionService": "true",
        "Connector": "uipath-atlassian-jira"
      }
    }
  ]
}
```

### Multi-connector example (Jira + Slack)

When a flow uses multiple connectors, add one `Connection` resource per unique connector:

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
          "displayName": "uipath-atlassian-jira connection"
        }
      },
      "metadata": {
        "ActivityName": "Create Issue",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-atlassian-jira connection",
        "UseConnectionService": "true",
        "Connector": "uipath-atlassian-jira"
      }
    },
    {
      "resource": "Connection",
      "key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "id": "Connectiona1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "value": {
        "ConnectionId": {
          "defaultValue": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "isExpression": false,
          "displayName": "uipath-salesforce-slack connection"
        }
      },
      "metadata": {
        "ActivityName": "Send Message to Channel",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-salesforce-slack connection",
        "UseConnectionService": "true",
        "Connector": "uipath-salesforce-slack"
      }
    }
  ]
}
```

### Other resource types

Beyond `Connection`, `bindings_v2.json` can contain other resource types for trigger-based flows:

| Resource type | When used | Key fields |
|---------------|-----------|------------|
| `EventTrigger` | Connector trigger nodes (e.g., "Issue Created") | `metadata.Operation`, `metadata.ObjectName` |
| `Property` | Trigger filter parameters | `value.<param>.defaultValue`, `metadata.ParentResourceKey` |
| `Queue` | Queue trigger bindings | Queue name and folder |
| `TimeTrigger` | Scheduled triggers | Cron expression |

For manual-trigger flows with connector activities, you only need `Connection` resources.

> **Never hardcode connection IDs.** Always fetch them from IS at authoring time. Connection IDs are tenant-specific and change across environments.

---

## Debug

### Common Errors

| Error | Cause | Fix |
| --- | --- | --- |
| No connection found | Connection not bound in `bindings_v2.json` | Run Step 1 above to bind a connection |
| Connection ping failed | Connection expired or misconfigured | Re-authenticate the connection in the IS portal |
| Missing `inputs.detail` | Node added but not configured | Run `uip maestro flow node configure` with the detail JSON (Step 6) |
| Reference field has display name instead of ID | `uip is resources execute list` was skipped | Resolve the reference field to get the actual ID (Step 4) |
| Required field missing at runtime | Required input field not provided | Check metadataFile for all `required: true` fields in both `requestFields` and `parameters` |
| `$vars` expression unresolvable | Node outputs block missing or node not connected | Verify the node has edges and upstream outputs are correctly referenced |
| `connectorMethodInfo` missing method/path | Used `registry get` without `--connection-id` | Re-run with `--connection-id` for enriched metadata (Step 2) |
| `bindings_v2.json` malformed | Hand-edited with wrong field structure | Compare against the schema and examples in the Bindings section above |
| Connector key not found | Wrong key name | Run `uip is connectors list --output json` — keys are often prefixed with `uipath-` |

### Debug Tips

1. **Always check `bindings_v2.json`** — connector nodes silently fail if the binding is missing or malformed. Compare against the Connection resource schema above.
2. **Compare inputs against metadataFile** — the full metadata (from `is resources describe`) has every field with types, descriptions, and whether it's required
3. **`flow validate` does NOT catch connector-specific issues** — validation only checks JSON schema and graph structure. Missing `inputs.detail` fields, wrong reference IDs, and expired connections are caught only at runtime (`flow debug`)
4. **If a connector key doesn't work** — list all connectors: `uip is connectors list --output json`. Keys are often prefixed with `uipath-`
5. **Query/path parameters** — some required parameters appear only in the metadataFile `parameters` section, not in `requestFields`. Check both.
6. **`node configure` populates bindings automatically** — if you use the CLI to configure connector nodes, it writes `bindings_v2.json` for you. Only edit bindings manually when the CLI doesn't support your use case.
