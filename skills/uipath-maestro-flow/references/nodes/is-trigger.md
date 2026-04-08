# IS Trigger Nodes

Connector trigger nodes start a flow when an external event fires (e.g., "email received in Outlook", "issue created in Jira"). They use UiPath Integration Service connectors — the same ecosystem as IS activity nodes — but replace the manual/scheduled start node with an event-driven one.

## When to Use

Use an IS trigger node when the flow should **start automatically in response to an external event** from a service with a pre-built UiPath connector.

### Decision Order

| Tier | Trigger Type | When to Use |
|---|---|---|
| 1 | **IS connector trigger** (this node type) | A connector exists and supports the event you need (e.g., "new email", "issue created") |
| 2 | **Scheduled trigger** (`core.trigger.scheduled`) | No event trigger exists, but you can poll on a schedule + filter for changes |
| 3 | **Manual trigger** (`core.trigger.manual`) | Flow is started on demand by a user or API call |

### Prerequisites

- `uip login` required — trigger nodes only appear in the registry after authentication
- A healthy IS connection must exist for the connector — if none exists, the user must create one before proceeding
- `uip flow registry pull` must be run to cache trigger node types locally

### When NOT to Use

- **No connector exists for the service** — use a scheduled trigger with `core.action.http` polling instead
- **The event is time-based, not data-driven** — use `core.trigger.scheduled`
- **The flow should be started manually** — use `core.trigger.manual`
- **You need to react to UiPath Orchestrator queue items** — use a queue trigger (separate mechanism)

## Implementation

### Node Type Pattern

`uipath.connector.trigger.<connector-key>.<trigger-name>`

Examples:
- `uipath.connector.trigger.uipath-microsoft-outlook365.email-received`
- `uipath.connector.trigger.uipath-atlassian-jira.issue-created`
- `uipath.connector.trigger.uipath-salesforce-slack.new-message`

### Key Differences from IS Activity Nodes

| Aspect | IS Activity | IS Trigger |
|---|---|---|
| Type pattern | `uipath.connector.<key>.<activity>` | `uipath.connector.trigger.<key>.<trigger>` |
| Position in flow | Anywhere (action node) | Start node only (replaces manual trigger) |
| `--connection-id` on `registry get` | Optional (enriches metadata) | **Required** (fails without it) |
| Metadata returned | `inputDefinition`, `outputResponseDefinition`, `connectorMethodInfo` | `eventParameters`, `filterFields`, `outputResponseDefinition`, `eventMode` |
| Configuration | `node configure --detail` (method, endpoint, bodyParameters) | `node configure --detail` (eventMode, eventParameters, filterExpression) |
| Bindings | `Connection` resource | `Connection` + `EventTrigger` + `Property` resources (auto-generated) |

### Discovery

```bash
# Search for trigger nodes in the registry
uip flow registry search trigger --output json

# Or search by service name
uip flow registry search outlook trigger --output json
```

Confirm `tags` includes both `"connector"` and `"trigger"` in the results.

If the trigger doesn't appear, re-pull the registry (triggers require authentication):

```bash
uip login status --output json
uip flow registry pull --force
```

### Ports

| Input Port | Output Port(s) |
|---|---|
| — (start node) | `output` |

### Output Variables

- `$vars.{nodeId}.output` — the event payload (structure depends on the trigger — see `outputResponseDefinition` from enrichment)
- `$vars.{nodeId}.error` — error details if the trigger encounters an issue

### Event Mode

Triggers operate in one of two modes (returned in `eventMode` from `registry get`):

| Mode | Behavior |
|---|---|
| `webhooks` | The connector registers a webhook — events fire in near-real-time |
| `polling` | The runtime polls the service on an interval — slight delay between event and trigger |

The agent does not need to configure the mode — it is determined by the connector. Note it in the plan for the user's awareness.

---

## Configuration Workflow

Follow these steps for every IS trigger node. This replaces the IS activity workflow (Steps 1-6 in `is-activity.md`) — trigger nodes have different metadata and configuration.

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

**`outputResponseDefinition`** — the event payload schema (all fields the trigger outputs when it fires).

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

### Step 5 — Replace the manual trigger with the connector trigger node

The trigger node replaces the default `core.trigger.manual` start node. Use CLI commands:

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

## IS Trigger CLI Commands

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
