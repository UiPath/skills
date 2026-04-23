# Connector Trigger Nodes — Planning

Connector trigger nodes start a flow when an external event fires (e.g., "email received in Outlook", "issue created in Jira"). They use UiPath Integration Service connectors — the same ecosystem as IS activity nodes — but replace the manual/scheduled start node with an event-driven one.

## When to Use

Use a connector trigger node when the flow should **start automatically in response to an external event** from a service with a pre-built UiPath connector.

### Decision Order

| Tier | Trigger Type | When to Use |
|---|---|---|
| 1 | **IS connector trigger** (this node type) | A connector exists and supports the event you need (e.g., "new email", "issue created") |
| 2 | **Scheduled trigger** (`core.trigger.scheduled`) | No event trigger exists, but you can poll on a schedule + filter for changes |
| 3 | **Manual trigger** (`core.trigger.manual`) | Flow is started on demand by a user or API call |

### Prerequisites

- `uip login` required — trigger nodes only appear in the registry after authentication
- A healthy IS connection must exist for the connector — if none exists, the user must create one before proceeding
- `uip maestro flow registry pull` must be run to cache trigger node types locally

### When NOT to Use

- **No connector exists for the service** — use a scheduled trigger with `core.action.http` polling instead
- **The event is time-based, not data-driven** — use `core.trigger.scheduled`
- **The flow should be started manually** — use `core.trigger.manual`
- **You need to react to UiPath Orchestrator queue items** — use a queue trigger (separate mechanism)

## Node Type Pattern

`uipath.connector.trigger.<connector-key>.<trigger-name>`

Examples:
- `uipath.connector.trigger.uipath-microsoft-outlook365.email-received`
- `uipath.connector.trigger.uipath-atlassian-jira.issue-created`
- `uipath.connector.trigger.uipath-salesforce-slack.new-message`

## Key Differences from IS Activity Nodes

| Aspect | IS Activity | IS Trigger |
|---|---|---|
| Type pattern | `uipath.connector.<key>.<activity>` | `uipath.connector.trigger.<key>.<trigger>` |
| Position in flow | Anywhere (action node) | Start node only (replaces manual trigger) |
| `--connection-id` on `registry get` | Optional (enriches metadata) | **Required** (fails without it) |
| Metadata returned | `inputDefinition`, `outputResponseDefinition`, `connectorMethodInfo` | `eventParameters`, `filterFields`, `outputResponseDefinition`, `eventMode` |
| Configuration | `node configure --detail` (method, endpoint, bodyParameters) | `node configure --detail` (eventMode, eventParameters, filter tree) |
| Bindings | `Connection` resource | `Connection` + `EventTrigger` + `Property` resources (auto-generated) |

## Discovery

```bash
# Search for trigger nodes in the registry
uip maestro flow registry search trigger --output json

# Or search by service name
uip maestro flow registry search outlook trigger --output json
```

Confirm `tags` includes both `"connector"` and `"trigger"` in the results.

If the trigger doesn't appear, re-pull the registry (triggers require authentication):

```bash
uip login status --output json
uip maestro flow registry pull --force
```

## Ports

| Input Port | Output Port(s) |
|---|---|
| — (start node) | `output` |

## Output Variables

- `$vars.{nodeId}.output` — the event payload (structure depends on the trigger — see `outputResponseDefinition` from enrichment)
- `$vars.{nodeId}.error` — error details if the trigger encounters an issue

## Event Mode

Triggers operate in one of two modes (returned in `eventMode` from `registry get`):

| Mode | Behavior |
|---|---|
| `webhooks` | The connector registers a webhook — events fire in near-real-time |
| `polling` | The runtime polls the service on an interval — slight delay between event and trigger |

The agent does not need to configure the mode — it is determined by the connector. Note it in the plan for the user's awareness.

> **Debug impact:** Only `polling` triggers can be debugged in Studio Web. `webhooks` triggers cannot be tested via `uip maestro flow debug` — they require deployment to Orchestrator. Flag this in the plan if the trigger uses webhook mode.

## Planning Annotation

In the architectural plan, annotate connector trigger nodes as:
- `trigger: <service-name>` with the intended event (e.g., "trigger: Outlook — email received")
- Record the event mode (`webhooks` or `polling`) if known from discovery
- If discovery found no trigger for the event, fall back to `core.trigger.scheduled` + polling or flag the gap in Open Questions
