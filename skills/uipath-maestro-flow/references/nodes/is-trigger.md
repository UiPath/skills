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
| Configuration | `node configure --detail` (method, endpoint, bodyParameters) | Direct `.flow` JSON edit (event params + filter expression) |
| Bindings | `Connection` resource | `Connection` + `EventTrigger` + `Property` resources |

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

### Step 5 — Discover trigger metadata for bindings

Fetch the trigger object metadata to build the `EventTrigger` binding:

```bash
uip is triggers describe "<connector-key>" "<operation>" "<objectName>" \
  --connection-id "<id>" --output json
```

This returns the trigger metadata needed for the `EventTrigger` resource in `bindings_v2.json`.

### Step 6 — Build the trigger node in the .flow file

Replace the `core.trigger.manual` start node with the connector trigger node. The trigger node is always the first node in the flow (position x=200).

```json
{
  "id": "start",
  "type": "uipath.connector.trigger.<connector-key>.<trigger-name>",
  "typeVersion": "1.0.0",
  "ui": { "position": { "x": 200, "y": 144 } },
  "display": { "label": "Email Received" },
  "inputs": {
    "eventParameters": {
      "parentFolderId": "<RESOLVED_FOLDER_ID>"
    },
    "filterExpression": "((fields.fromAddress<`someone@example.com`>))"
  },
  "model": {
    "type": "bpmn:StartEvent",
    "eventDefinition": "bpmn:SignalEventDefinition",
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-microsoft-outlook365" },
      { "name": "operation", "type": "string", "value": "EMAIL_RECEIVED" },
      { "name": "objectName", "type": "string", "value": "Message" },
      { "name": "connection", "type": "string", "value": "<bindings.uipath-microsoft-outlook365 connection>" }
    ]
  }
}
```

**Key points:**
- `model.type` is `bpmn:StartEvent` — this is a start node
- `model.context.connection` uses a `<bindings.*>` placeholder, resolved at runtime via `bindings_v2.json`
- `inputs.eventParameters` holds the resolved event parameter values from Step 3
- `inputs.filterExpression` holds the filter using the syntax `((fields.<fieldName><`value`>))` — omit if no filters are needed
- The `id` should be `"start"` (replacing the manual trigger) so existing edge wiring from `start` is preserved

### Step 7 — Populate definitions

Same as any node — fetch the definition from the registry and add it to `definitions`:

```bash
uip flow registry get <triggerNodeType> --connection-id <connection-id> --output json
```

Copy `Data.Node` into the `definitions` array. Remove the old `core.trigger.manual` definition if no other node uses it.

---

## Bindings — `bindings_v2.json`

Trigger nodes require more binding resources than activity nodes. A connector activity needs only a `Connection` resource; a connector trigger needs `Connection` + `EventTrigger` + `Property` resources.

### Connection resource

Same structure as IS activity nodes — see [is-activity.md — Bindings](is-activity.md#bindings--bindings_v2json).

### EventTrigger resource

| Field | Description |
|---|---|
| `resource` | Always `"EventTrigger"` |
| `key` | A generated UUID |
| `id` | `"EventTrigger" + <key>` (concatenated, no separator) |
| `value.EventTriggerId.defaultValue` | The trigger type ID (from `is triggers describe`) |
| `value.EventTriggerId.isExpression` | Always `false` |
| `value.EventTriggerId.displayName` | Human-readable label (e.g., `"Email Received trigger"`) |
| `metadata.Connector` | Connector key (must match the node's `model.context.connectorKey`) |
| `metadata.Operation` | Event operation name (e.g., `"EMAIL_RECEIVED"`) |
| `metadata.ObjectName` | IS object name (e.g., `"Message"`) |
| `metadata.BindingsVersion` | Always `"2.2"` |

### Property resource (one per event parameter)

Each required event parameter gets its own `Property` resource:

| Field | Description |
|---|---|
| `resource` | Always `"Property"` |
| `key` | A generated UUID |
| `id` | `"Property" + <key>` (concatenated, no separator) |
| `value.<paramName>.defaultValue` | The resolved parameter value (e.g., folder ID) |
| `value.<paramName>.isExpression` | Always `false` |
| `value.<paramName>.displayName` | The parameter's display name from `eventParameters` |
| `metadata.ParentResourceKey` | The `key` of the `EventTrigger` resource this parameter belongs to |
| `metadata.BindingsVersion` | Always `"2.2"` |

### Example — Outlook email trigger

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "a1b2c3d4-0000-0000-0000-000000000001",
      "id": "Connectiona1b2c3d4-0000-0000-0000-000000000001",
      "value": {
        "ConnectionId": {
          "defaultValue": "a1b2c3d4-0000-0000-0000-000000000001",
          "isExpression": false,
          "displayName": "uipath-microsoft-outlook365 connection"
        }
      },
      "metadata": {
        "ActivityName": "Email Received",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-microsoft-outlook365 connection",
        "UseConnectionService": "true",
        "Connector": "uipath-microsoft-outlook365"
      }
    },
    {
      "resource": "EventTrigger",
      "key": "b2c3d4e5-0000-0000-0000-000000000002",
      "id": "EventTriggerb2c3d4e5-0000-0000-0000-000000000002",
      "value": {
        "EventTriggerId": {
          "defaultValue": "b2c3d4e5-0000-0000-0000-000000000002",
          "isExpression": false,
          "displayName": "Email Received trigger"
        }
      },
      "metadata": {
        "Connector": "uipath-microsoft-outlook365",
        "Operation": "EMAIL_RECEIVED",
        "ObjectName": "Message",
        "BindingsVersion": "2.2"
      }
    },
    {
      "resource": "Property",
      "key": "c3d4e5f6-0000-0000-0000-000000000003",
      "id": "Propertyc3d4e5f6-0000-0000-0000-000000000003",
      "value": {
        "parentFolderId": {
          "defaultValue": "AAMkAGI2THVSAAA=",
          "isExpression": false,
          "displayName": "Email folder"
        }
      },
      "metadata": {
        "ParentResourceKey": "b2c3d4e5-0000-0000-0000-000000000002",
        "BindingsVersion": "2.2"
      }
    }
  ]
}
```

---

## IS Trigger CLI Commands

```bash
# Discovery
uip flow registry search trigger --output json               # find trigger node types
uip flow registry pull --force                                # refresh registry (requires login)

# Enriched trigger metadata (--connection-id REQUIRED)
uip flow registry get <triggerNodeType> --connection-id <connection-id> --output json

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
| Connection not found in bindings | `bindings_v2.json` missing `Connection` resource | Add the `Connection` resource (see Bindings section) |
| EventTrigger binding missing | `bindings_v2.json` missing `EventTrigger` resource | Add `EventTrigger` with correct `Operation` and `ObjectName` metadata |
| Event parameter missing at runtime | Required event parameter not configured | Check `eventParameters.fields` for `required: true` fields and add matching `Property` bindings |
| Filter expression syntax error | Wrong filter format | Use `((fields.<fieldName><`value`>))` syntax |
| Trigger not firing | Event parameters point to wrong resource (e.g., wrong folder ID) | Re-resolve reference fields with `uip is resources execute list` |
| `model.context` missing operation | Node added without context entries | Ensure `model.context` includes `connectorKey`, `operation`, `objectName`, and `connection` |

### Debug Tips

1. **Always verify the connection is healthy** before debugging trigger issues — run `uip is connections ping "<id>"`
2. **Check all three binding resource types** — trigger nodes need `Connection` + `EventTrigger` + `Property` (not just `Connection`)
3. **`flow validate` does NOT catch trigger-specific issues** — missing event parameters, wrong reference IDs, and expired connections are caught only at runtime
4. **Event parameters with `reference` objects** need resolved IDs, not display names — same as IS activity fields
5. **Filter expressions are optional** — omit `filterExpression` from inputs if the user wants all events to trigger the flow
6. **`node configure` does NOT work for trigger nodes** — it sets `inputs.detail` which is an activity-only concept. Edit the `.flow` file directly for trigger node inputs
