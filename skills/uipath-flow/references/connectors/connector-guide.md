# Connector Activity Nodes

Connector activity nodes call external services (Jira, Slack, Salesforce, Outlook, etc.) via UiPath Integration Service. They are dynamically loaded -- not built-in -- and appear in the registry after `uip login` + `uip flow registry pull`. Every connector node requires an authenticated IS connection bound in `bindings_v2.json`.

---

## Node Type Pattern

`uipath.connector.<connector-key>.<activity>`

Examples:
- `uipath.connector.uipath-salesforce-slack.send-message`
- `uipath.connector.uipath-atlassian-jira.create-issue`
- `uipath.connector.uipath-microsoft-outlook365.get-newest-email`

---

## Decision Ladder

Prefer higher tiers when connecting to external services:

| Tier | Approach | When to Use |
|---|---|---|
| 1 | **IS connector activity** (this node type) | A connector exists and its activities cover the use case |
| 2 | **HTTP Request within a connector** | A connector exists but lacks the specific endpoint -- connector still handles auth |
| 3 | **Standalone HTTP Request** (`core.action.http`) | No connector exists, or quick prototyping -- you handle auth manually |
| 4 | **RPA workflow** | Target system has no API at all (legacy desktop apps, terminals) |

### When NOT to Use

- **No connector exists for the service** -- use `core.action.http` instead
- **Simple GET request with no auth** -- `core.action.http` is simpler and faster to configure
- **The operation needs desktop/browser interaction** -- use an RPA resource node
- **The task requires reasoning or judgment** -- use an agent node

---

## Ports

| Input Port | Output Port(s) |
|---|---|
| `input` | `success` |

> Connector nodes use `success` as their output port, not `output`. This differs from resource nodes.

---

## Output Variables

- `$vars.<NODE_ID>.output` -- the connector response (structure depends on the operation)
- `$vars.<NODE_ID>.error` -- error details if the call fails

---

## Discovery

### Registry Search

```bash
uip flow registry pull --force
uip flow registry search "<SERVICE_NAME>" --output json
```

Confirm `category: "connector"` in the results. If the connector key fails, list all connectors:

```bash
uip is connectors list --output json
```

Keys are often prefixed -- e.g., `uipath-salesforce-slack` not `slack`, `uipath-atlassian-jira` not `jira`.

### Connection Health Check

For each connector found in registry search, verify a healthy connection exists. Extract the connector key from the node type name (e.g., `uipath.connector.uipath-microsoft-outlook365.get-newest-email` -> key is `uipath-microsoft-outlook365`).

```bash
# List available connections for the connector
uip is connections list "<CONNECTOR_KEY>" --folder-key "<FOLDER_KEY>" --output json

# Verify the connection is healthy
uip is connections ping "<CONNECTION_ID>" --output json
```

- If a default enabled connection exists (`IsDefault: Yes`, `State: Enabled`), record the connection ID for configuration.
- If no connection exists, the user must create one before proceeding: `uip is connections create "<CONNECTOR_KEY>"`.

---

## Configuration Workflow

Follow these 6 steps for every connector node.

### Step 1 -- Fetch and bind a connection

Extract the connector key from the node type (`uipath.connector.<connector-key>.<activity-name>`) and fetch a connection.

```bash
# 1. List available connections
uip is connections list "<CONNECTOR_KEY>" --folder-key "<FOLDER_KEY>" --output json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)

# 3. Verify the connection is healthy
uip is connections ping "<CONNECTION_ID>" --output json
```

If a connector key fails, list all available connectors to find the correct key: `uip is connectors list --output json`.

If no connection exists, tell the user before proceeding -- they must create one in the IS portal or via `uip is connections create "<CONNECTOR_KEY>"`.

> The `--folder-key` parameter specifies which Orchestrator folder to list/create connections in. If omitted, the CLI defaults to the Personal Workspace folder.

### Step 2 -- Get enriched node definitions with connection

Call `registry get` with `--connection-id` to fetch connection-aware metadata including custom fields:

```bash
uip flow registry get "<NODE_TYPE>" --connection-id "<CONNECTION_ID>" --output json
```

This returns enriched `inputDefinition.fields` and `outputDefinition.fields` with accurate type, required, description, enum, and `reference` info. Without `--connection-id`, only standard/base fields are returned.

The response also includes `connectorMethodInfo` with the real HTTP `method` (e.g., `GET`, `POST`) and `path` template (e.g., `/ConversationsInfo/{conversationsInfoId}`). Save these two values -- you must pass them to `node configure` later.

### Step 3 -- Describe the resource and read full metadata

Run `is resources describe` to fetch and cache the full operation metadata, then read the cached metadata file for complete field details including descriptions, types, references, and query/path parameters. The describe summary omits some of this.

```bash
# 1. Describe to trigger fetch + cache (extract the objectName from the connector node type)
uip is resources describe "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" --operation Create --output json
# -> response includes metadataFile path

# 2. Read the full cached metadata
cat <METADATA_FILE_PATH>
```

The full metadata contains:
- **`parameters`** -- query and path parameters (may include required params not in `requestFields`, e.g., `send_as` for Slack)
- **`requestFields`** -- body fields with `type`, `required`, `description`, and `reference` objects for ID resolution
- **`path`** -- the API endpoint path (also available in `connectorMethodInfo` from `registry get`)
- **`responseFields`** -- response schema

### Step 4 -- Resolve reference fields

Check `requestFields` from the metadata for fields with a `reference` object -- these require ID lookup from the connector's live data. Use `uip is resources execute list` to resolve them:

```bash
# Example: resolve Slack channel "#test-slack" to its ID
uip is resources execute list "uipath-salesforce-slack" "curated_channels?types=public_channel,private_channel" \
  --connection-id "<CONNECTION_ID>" --output json
# -> { "id": "C1234567890", "name": "test-slack" }
```

Use the resolved IDs (not display names) in the flow's node `inputs`. Present options to the user when multiple matches exist.

### Step 5 -- Validate required fields

Check every required field -- both `requestFields` and `parameters` where `required: true` -- against what the user provided. This is a hard gate -- do NOT proceed to building until all required fields have values.

1. Collect all required fields from the metadata (`requestFields` + `parameters`).
2. For each required field, check if the user's prompt contains a value.
3. For query/path parameters with a `defaultValue`, use the default if the user did not specify one.
4. If any required field is missing and has no `defaultValue`, ask the user before proceeding -- list the missing fields with their `displayName` and what kind of value is expected.
5. Only after all required fields are accounted for, proceed to building.

> Do NOT guess or skip missing required fields. A missing required field will cause a runtime error. It is always better to ask than to assume.

### Step 6 -- Configure the node

#### CLI Mode

After adding the node with `uip flow node add`, configure it with the resolved connection and field values:

```bash
uip flow node configure <FILE> <NODE_ID> \
  --detail '{"connectionId": "<CONNECTION_ID>", "folderKey": "<FOLDER_KEY>", "method": "POST", "endpoint": "/issues", "bodyParameters": {"fields.project.key": "ENGCE", "fields.issuetype.id": "10004"}}'
```

The `method` and `endpoint` values come from `connectorMethodInfo` in the `registry get` response (Step 2). The command populates `inputs.detail` and creates workflow-level bindings entries. Use resolved IDs from Step 4, not display names.

> Shell quoting tip: For complex `--detail` JSON, write it to a temp file: `uip flow node configure <FILE> <NODE_ID> --detail "$(cat /tmp/detail.json)"`

#### JSON Mode

Edit `inputs.detail` directly on the node instance:

```json
"inputs": {
  "detail": {
    "connectionId": "<CONNECTION_ID>",
    "folderKey": "<FOLDER_KEY>",
    "method": "POST",
    "endpoint": "/issues",
    "bodyParameters": {
      "fields.project.key": "ENGCE",
      "fields.issuetype.id": "10004"
    },
    "queryParameters": {}
  }
}
```

The `inputs.detail` object contains:

| Field | Description |
|---|---|
| `connectionId` | The bound IS connection UUID |
| `folderKey` | The Orchestrator folder key |
| `method` | HTTP method from `connectorMethodInfo` (e.g., `POST`) |
| `endpoint` | API path from `connectorMethodInfo` (e.g., `/issues`) |
| `bodyParameters` | Field-value pairs for the request body |
| `queryParameters` | Field-value pairs for query string parameters |

When editing JSON directly, you must also manually add the `Connection` resource to `bindings_v2.json` (see below).

---

## `bindings_v2.json` -- Connection Resource

When a flow uses connector nodes, the runtime needs to know which authenticated connection to use for each connector. This is configured in `content/bindings_v2.json`.

### How Connector Nodes Reference Bindings

Each connector node's `model.context` contains a `connection` entry with a placeholder:

```json
{ "name": "connection", "type": "string", "value": "<bindings.uipath-atlassian-jira connection>" }
```

At runtime, the engine resolves this placeholder by looking up `bindings_v2.json` for a `Connection` resource whose `metadata.Connector` matches `uipath-atlassian-jira`.

### Connection Resource Schema

| Field | Description |
|---|---|
| `resource` | Always `"Connection"` |
| `key` | The connection ID (UUID from `uip is connections list`) |
| `id` | `"Connection"` + `<connection-id>` (concatenated, no separator) |
| `value.ConnectionId.defaultValue` | The actual connection ID |
| `value.ConnectionId.isExpression` | Always `false` |
| `value.ConnectionId.displayName` | Human-readable label (e.g., `"uipath-atlassian-jira connection"`) |
| `metadata.UseConnectionService` | Always `"true"` |
| `metadata.Connector` | Connector key (e.g., `"uipath-atlassian-jira"`) -- must match the node's `model.context` connector key |
| `metadata.ActivityName` | Display name of the activity using this connection |
| `metadata.BindingsVersion` | Always `"2.2"` |
| `metadata.DisplayLabel` | Same as `value.ConnectionId.displayName` |

### Example

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

> `uip flow node configure` (CLI mode) populates `bindings_v2.json` automatically. Only edit bindings manually when using JSON mode or when the CLI does not support your use case.

See [bindings-guide.md](../bindings-guide.md) for the full binding system overview, including multi-connector examples, other resource types (`EventTrigger`, `Property`, `Queue`, `TimeTrigger`), and deduplication rules.

---

## `model.context` Connection Placeholder

Each connector node instance includes a connection placeholder in `model.context`:

```json
"context": [
  { "name": "connection", "type": "string", "value": "<bindings.<CONNECTOR_KEY> connection>" }
]
```

The `<CONNECTOR_KEY>` matches the `metadata.Connector` field in `bindings_v2.json`. At runtime, the engine resolves this to the bound connection ID.

---

## HTTP Fallback Pattern (Tier 2)

When a connector exists but lacks the specific endpoint, use the connector's HTTP Request activity. The connector still manages authentication; you supply the path and payload.

1. Search for the connector's HTTP activity: `uip flow registry search "<CONNECTOR_KEY>" --output json` and look for an HTTP Request activity.
2. Add it as a connector node, following the same 6-step configuration workflow.
3. Set the `method`, `endpoint`, and `bodyParameters`/`queryParameters` in `inputs.detail` to match the target API endpoint.

This approach inherits the connector's OAuth/API key management while giving you full control over the request.

---

## IS CLI Commands

```bash
# Connections
uip is connections list "<CONNECTOR_KEY>" --folder-key "<FOLDER_KEY>" --output json
uip is connections ping "<CONNECTION_ID>" --output json
uip is connections create "<CONNECTOR_KEY>"

# Enriched node metadata (pass connection for custom fields)
uip flow registry get "<NODE_TYPE>" --connection-id "<CONNECTION_ID>" --output json

# Resource description and metadata
uip is resources describe "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" --operation Create --output json

# Reference resolution
uip is resources execute list "<CONNECTOR_KEY>" "<RESOURCE>" \
  --connection-id "<CONNECTION_ID>" --output json

# List all available connectors
uip is connectors list --output json
```

---

## Debug / Common Errors

| Error | Cause | Fix |
|---|---|---|
| No connection found | Connection not bound in `bindings_v2.json` | Run Step 1 to bind a connection |
| Connection ping failed | Connection expired or misconfigured | Re-authenticate the connection in the IS portal |
| Missing `inputs.detail` | Node added but not configured | Run `uip flow node configure` with the detail JSON (Step 6) |
| Reference field has display name instead of ID | `uip is resources execute list` was skipped | Resolve the reference field to get the actual ID (Step 4) |
| Required field missing at runtime | Required input field not provided | Check metadataFile for all `required: true` fields in both `requestFields` and `parameters` |
| `$vars` expression unresolvable | Node outputs block missing or node not connected | Verify the node has edges and upstream outputs are correctly referenced |
| `connectorMethodInfo` missing method/path | Used `registry get` without `--connection-id` | Re-run with `--connection-id` for enriched metadata (Step 2) |
| `bindings_v2.json` malformed | Hand-edited with wrong field structure | Compare against the Connection resource schema above |
| Connector key not found | Wrong key name | Run `uip is connectors list --output json` -- keys are often prefixed with `uipath-` |

### Debug Tips

1. **Always check `bindings_v2.json`** -- connector nodes silently fail if the binding is missing or malformed. Compare against the Connection resource schema above.
2. **Compare inputs against metadataFile** -- the full metadata (from `is resources describe`) has every field with types, descriptions, and whether it is required.
3. **`flow validate` does NOT catch connector-specific issues** -- validation only checks JSON schema and graph structure. Missing `inputs.detail` fields, wrong reference IDs, and expired connections are caught only at runtime (`flow debug`).
4. **If a connector key does not work** -- list all connectors: `uip is connectors list --output json`. Keys are often prefixed with `uipath-`.
5. **Query/path parameters** -- some required parameters appear only in the metadataFile `parameters` section, not in `requestFields`. Check both.
6. **`node configure` populates bindings automatically** -- if you use the CLI to configure connector nodes, it writes `bindings_v2.json` for you. Only edit bindings manually when the CLI does not support your use case.
