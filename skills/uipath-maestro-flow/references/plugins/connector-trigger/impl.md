# Connector Trigger Nodes — Implementation

How to configure connector trigger nodes: connection binding, enriched metadata, event parameter resolution, and trigger-specific `node configure` fields. This replaces the IS activity workflow (Steps 1-6 in [connector/impl.md](../connector/impl.md)) — trigger nodes have different metadata and configuration.

## Configuration Workflow

Follow these steps for every IS trigger node.

### Step 1 — Fetch and bind a connection

Same as IS activity nodes. Extract the connector key from the node type (`uipath.connector.trigger.<connector-key>.<trigger-name>`) and fetch a connection.

```bash
# 1. List available connections
uip is connections list "<connector-key>" --output json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)

# 3. Verify the connection is healthy
uip is connections ping "<connection-id>" --output json
```

**If no connection exists**, tell the user before proceeding — they must create one in the IS portal or via `uip is connections create "<connector-key>"`.

### Step 2 — Get enriched trigger metadata

`--connection-id` is **required** for trigger nodes. Without it, the command fails.

```bash
uip flow registry get <triggerNodeType> --connection-id <connection-id> --output json
```

The response contains three trigger-specific sections:

**`eventParameters`** — fields that configure *what* the trigger watches (e.g., which email folder, which Jira project). These are the trigger's required setup fields.

```json
{
  "eventParameters": {
    "fields": [
      {
        "name": "parentFolderId",
        "displayName": "Email folder",
        "type": "string",
        "required": true,
        "reference": {
          "objectName": "MailFolder",
          "lookupValue": "id",
          "lookupNames": ["displayName"],
          "path": "/MailFolders"
        }
      }
    ]
  }
}
```

**`filterFields`** — fields used to narrow *which* events fire the trigger (e.g., only emails from a specific sender). These are optional filter criteria.

```json
{
  "filterFields": {
    "fields": [
      {
        "name": "fromAddress",
        "displayName": "From address",
        "type": "string",
        "required": false
      }
    ]
  }
}
```

**`outputResponseDefinition`** — the event payload schema (all fields the trigger outputs when it fires). **Save this** — you need it in Step 4b to know the exact field paths for downstream `$vars` expressions (e.g., `$vars.{nodeId}.output.text`, `$vars.{nodeId}.output.channel`). Do not guess output field names.

**`eventMode`** — `"webhooks"` or `"polling"`.

The response also includes `model.context` with:
- `connectorKey` — the connector identifier
- `operation` — the event operation name (e.g., `"EMAIL_RECEIVED"`, `"ISSUE_CREATED"`)
- `objectName` — the IS object (e.g., `"Message"`, `"Issue"`)

### Step 3 — Resolve reference fields in event parameters

Check `eventParameters.fields` for fields with a `reference` object — these require ID lookup, same as IS activity nodes.

```bash
# Example: resolve Outlook mail folder "Inbox" to its ID
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<id>" --output json
```

Use the resolved IDs in the trigger's event parameter configuration.

### Step 4 — Validate required event parameters

Check every field in `eventParameters.fields` where `required: true`. All required event parameters must have values before building the flow.

1. Collect all required event parameter fields
2. For each, check if the user's prompt provides a value
3. If any required field is missing, **ask the user** — list the missing fields with their `displayName`
4. Only proceed after all required event parameters are resolved

### Step 4b — Map trigger output fields for downstream nodes

Before wiring downstream nodes, check `outputResponseDefinition` from Step 2 to know the exact field names available in `$vars.{triggerId}.output`. Do NOT guess field names — different triggers output different schemas.

Each trigger type has a different output schema — field names like `.text`, `.subject`, or `.body.content` vary by connector. Use the actual field names from `outputResponseDefinition` when writing expressions in downstream nodes.

### Step 5 — Replace the manual trigger with the connector trigger node

The trigger node replaces the default `core.trigger.manual` start node. **Use CLI commands — do NOT manually edit the JSON to remove the start node.** The CLI handles edge cleanup, orphaned definition removal, and `variables.nodes` regeneration automatically.

```bash
# 1. Delete the manual trigger (also removes its edges and orphaned definition)
uip flow node delete <PROJECT>.flow start --output json

# 2. Add the connector trigger node
uip flow node add <PROJECT>.flow <triggerNodeType> \
  --label "Email Received" --position 200,144 --output json
# → Note the generated node ID from the response (e.g., "emailReceived1")

# 3. Re-wire the edge from the new trigger to the next node
uip flow edge add <PROJECT>.flow <newTriggerId> <nextNodeId> \
  --source-port output --target-port input --output json
```

### Step 6 — Configure the trigger node

**Read the `--detail` field table below before calling `node configure`.** The fields and types are strict — unknown keys or wrong types cause validation errors. Do not guess field names from other node types (e.g., activity nodes use `method`/`endpoint`/`bodyParameters`; triggers use `eventMode`/`eventParameters`/`filterExpression`).

Use `node configure` with trigger-specific `--detail` fields:

```bash
uip flow node configure <PROJECT>.flow <triggerId> --detail '{
  "connectionId": "<CONNECTION_ID>",
  "folderKey": "<FOLDER_KEY>",
  "eventMode": "<EVENT_MODE>",
  "eventParameters": { "<paramName>": "<RESOLVED_VALUE>" },
  "filterExpression": "((fields.<fieldName><`value`>))"
}'
```

**`--detail` fields for triggers:**

| Field | Required | Description |
|---|---|---|
| `connectionId` | Yes | Connection UUID from Step 1 |
| `folderKey` | Yes | Orchestrator folder key for the connection |
| `eventMode` | Yes | `"webhooks"` or `"polling"` — from `registry get` response |
| `eventParameters` | No | JSON object of resolved event parameter values from Steps 3-4 |
| `filterExpression` | No | Filter using `((fields.<fieldName><`value`>))` syntax — omit to trigger on all events |

The command populates `inputs.detail` (including the internal `configuration` blob) and creates workflow-level connection bindings.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)"`

---

## Bindings

Trigger nodes require more binding resources than activity nodes: `Connection` + `EventTrigger` + `Property` resources. **`node configure` and the packaging pipeline handle all of these automatically:**

- **Connection bindings** — created in the `.flow` file by `node configure` (Step 6)
- **EventTrigger + Property bindings** — generated into `bindings_v2.json` during `flow debug` or packaging from the trigger node's `inputs.detail`

You do **not** need to manually create or edit `bindings_v2.json` for trigger nodes.

---

## CLI Commands

```bash
# Discovery
uip flow registry search trigger --output json               # find trigger node types
uip flow registry pull --force                                # refresh registry (requires login)

# Enriched trigger metadata (--connection-id REQUIRED)
uip flow registry get <triggerNodeType> --connection-id <connection-id> --output json

# Node lifecycle
uip flow node delete <PROJECT>.flow start --output json       # remove manual trigger
uip flow node add <PROJECT>.flow <triggerNodeType> --label "<LABEL>" --position 200,144 --output json
uip flow node configure <PROJECT>.flow <nodeId> --detail '<TRIGGER_DETAIL_JSON>' --output json

# Trigger object metadata
uip is triggers objects "<connector-key>" "<operation>" --connection-id "<id>" --output json
uip is triggers describe "<connector-key>" "<operation>" "<objectName>" --connection-id "<id>" --output json

# Connections (same as IS activity)
uip is connections list "<connector-key>" --output json
uip is connections ping "<connection-id>" --output json

# Reference resolution (same as IS activity)
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json
```

---

## Testing Trigger Flows

`uip flow debug` works with trigger-based flows, but unlike manual triggers the flow does **not** execute immediately. The debug session registers a live webhook/poll with the external service and waits for a real event.

### Testing workflow

1. **Warn the user** — explain that debug will start a live listener and they must produce the event themselves (e.g., send a Slack message, create a Jira issue)
2. Run `uip flow debug .` — uploads to Studio Web, starts the debug session, and begins polling (~10 min timeout)
3. **User triggers the event** in the external service (e.g., sends a message in the configured Slack channel)
4. The flow fires, executes all nodes, and debug reports the result
5. If no event arrives before the timeout, the session ends with no execution

```bash
uip flow debug . --output json
# → Session starts, listening for trigger event...
# → User must now produce the event in the external service
# → Flow executes when event arrives
```

### Key differences from manual-trigger debug

| Aspect | Manual trigger | Connector trigger |
|---|---|---|
| Execution start | Immediate | Waits for external event |
| User action needed | None | Must produce the event manually |
| Timeout risk | Low (runs immediately) | High (~10 min window) |
| What gets registered | Nothing | Live webhook or polling subscription |

> **Do NOT run `flow debug` for trigger flows without telling the user first.** They need to know they must produce the event within the timeout window.

---

## Debug

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Trigger nodes require --connection-id` | Ran `registry get` without `--connection-id` | Re-run with `--connection-id <id>` — required for all trigger nodes |
| No trigger nodes in registry | Not authenticated or registry not pulled | Run `uip login` then `uip flow registry pull --force` |
| Connection not found in bindings | `node configure` not run or connection expired | Re-run `node configure` with valid `connectionId` and `folderKey` |
| Event parameter missing at runtime | Required event parameter not configured | Check `eventParameters.fields` for `required: true` fields and include them in `--detail` `eventParameters` |
| Filter expression syntax error | Wrong filter format | Use `((fields.<fieldName><`value`>))` syntax |
| Trigger not firing | Event parameters point to wrong resource (e.g., wrong folder ID) | Re-resolve reference fields with `uip is resources execute list` |
| `model.context` missing operation | Node added without context entries | Delete and re-add the node — `node add` populates `model.context` from the registry definition |

### Debug Tips

1. **Always verify the connection is healthy** before debugging trigger issues — run `uip is connections ping "<id>"`
2. **`flow validate` does NOT catch trigger-specific issues** — missing event parameters, wrong reference IDs, and expired connections are caught only at runtime
3. **Event parameters with `reference` objects** need resolved IDs, not display names — same as IS activity fields
4. **Filter expressions are optional** — omit `filterExpression` from `--detail` if the user wants all events to trigger the flow
5. **Bindings are auto-managed** — `node configure` creates flow-level bindings; `flow debug`/packaging generates `bindings_v2.json` from them
6. **Use `uip flow node delete` to remove the manual trigger** — do NOT manually edit the JSON to delete the start node. The CLI automatically removes associated edges, orphaned definitions, and regenerates `variables.nodes`. Direct JSON editing skips these cleanup steps and can leave orphaned references.
7. **Check `outputResponseDefinition` before writing downstream expressions** — trigger output field names vary by connector. Do not assume field names like `.text` or `.subject` — verify from the enriched `registry get` response (Step 2)
