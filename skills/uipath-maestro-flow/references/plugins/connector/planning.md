# Connector Activity Nodes — Planning

Connector activity nodes call external services (Jira, Slack, Salesforce, Outlook, etc.) via UiPath Integration Service. They are dynamically loaded — not built-in — and appear in the registry after `uip login` + `uip flow registry pull`.

## When to Use

Use a connector activity node when the flow needs to **call an external service that has a pre-built UiPath connector**. Connectors handle auth (OAuth, API keys), token refresh, pagination, and error formatting automatically.

### Decision Order

Prefer higher tiers when connecting to external services:

| Tier | Approach | When to Use |
| --- | --- | --- |
| 1 | **IS connector activity** (this node type) | A connector exists and its activities cover the use case |
| 2 | **HTTP Request within a connector** | A connector exists but lacks the specific endpoint — connector still handles auth |
| 3 | **Standalone HTTP Request** (`core.action.http`) | No connector exists, or quick prototyping — you handle auth manually |
| 4 | **RPA workflow** | Target system has no API at all (legacy desktop apps, terminals) |

### Prerequisites

- `uip login` required — connector nodes only appear in the registry after authentication
- A healthy IS connection must exist for the connector — if none exists, the user must create one before proceeding
- `uip flow registry pull` must be run to cache connector node types locally

### When NOT to Use

- **No connector exists for the service** — use `core.action.http` instead
- **Simple GET request with no auth** — `core.action.http` is simpler and faster to configure
- **The operation needs desktop/browser interaction** — use an RPA resource node
- **The task requires reasoning or judgment** — use an agent node

## Node Type Pattern

`uipath.connector.<connector-key>.<activity>`

Examples:
- `uipath.connector.uipath-salesforce-slack.send-message`
- `uipath.connector.uipath-atlassian-jira.create-issue`

## Discovery

```bash
uip flow registry search <service> --output json
```

Confirm `category: "connector"` in the results. If the connector key fails, list all connectors:

```bash
uip is connectors list --output json
```

Keys are often prefixed — e.g., `uipath-salesforce-slack` not `slack`.

### Check Connector Connections

For each connector found in registry search, verify a healthy connection exists. Extract the connector key from the node type name (e.g., `uipath.connector.uipath-microsoft-outlook365.get-newest-email` -> key is `uipath-microsoft-outlook365`).

```bash
uip is connections list "<connector-key>" --output json
```

- If a default enabled connection exists (`IsDefault: Yes`, `State: Enabled`), record the connection ID for implementation planning.
- **If no connection exists**, surface it in the **Open Questions** section of the architectural plan so the user can create it while reviewing.

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `success` |

## Output Variables

- `$vars.{nodeId}.output` — the connector response (structure depends on the operation)
- `$vars.{nodeId}.error` — error details if the call fails

## HTTP Fallback

When a connector exists but lacks the specific endpoint, use the connector's HTTP Request activity. The connector still manages authentication; you supply the path and payload. Note as `connector: <service> (HTTP fallback)` during planning.

## Planning Annotation

In the architectural plan, annotate connector nodes as:
- `connector: <service-name>` with the intended operation (e.g., "connector: Jira — create issue")
- If discovery found no connector, fall back to `core.action.http` or flag the gap in Open Questions
