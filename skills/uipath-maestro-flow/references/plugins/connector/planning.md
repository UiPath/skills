# Connector Activity Nodes — Planning

Connector activity nodes call external services (Jira, Slack, Salesforce, Outlook, etc.) via UiPath Integration Service. They are dynamically loaded — not built-in — and appear in the registry after `uip login` + `uip flow registry pull`.

## When to Use

Use a connector activity node when the flow needs to **call an external service that has a pre-built UiPath connector**. Connectors handle auth (OAuth, API keys), token refresh, pagination, and error formatting automatically.

### Decision Order

Prefer higher tiers when connecting to external services:

| Tier | Approach | When to Use |
| --- | --- | --- |
| 1 | **IS connector activity** (this node type) | A connector exists and its activities cover the use case |
| 2 | **Managed HTTP Request** (`core.action.http.v2`) | A connector exists but lacks the specific curated activity — uses the connector's IS connection for auth |
| 3 | **Managed HTTP Request — manual mode** (`core.action.http.v2`) | No connector exists — you provide the full URL manually |
| 4 | **RPA workflow** | Target system has no API at all (legacy desktop apps, terminals) |

### Prerequisites

- `uip login` required — connector nodes only appear in the registry after authentication
- A healthy IS connection must exist for the connector — if none exists, the user must create one before proceeding
- `uip flow registry pull` must be run to cache connector node types locally

### When NOT to Use

- **No connector exists for the service** — use `core.action.http.v2` manual mode instead
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

## HTTP Fallback (Managed HTTP Request)

When a connector exists but lacks the specific curated activity, use `core.action.http.v2` (Managed HTTP Request). This node proxies through the `uipath-uipath-http` connector and uses the **target connector's** IS connection for authentication — you supply the API URL and payload.

> **Do NOT use individual connector HTTP request nodes** (e.g., `uipath.connector.<key>.http-request`). Always use the unified `core.action.http.v2` Managed HTTP Request node for non-curated API calls.

> **Do NOT use `core.action.http` (v1) with `authenticationType: "connection"` for this.** The v1 node does not pass IS credentials at runtime. Always use `core.action.http.v2`.

See [http/planning.md](../http/planning.md) for full selection heuristics and [http/impl.md](../http/impl.md) for configuration via `uip flow node configure`.

Note as `managed-http: <service> — <operation>` during planning.

## Planning Annotation

In the architectural plan, annotate connector nodes as:
- `connector: <service-name>` with the intended operation (e.g., "connector: Jira — create issue")
- If discovery found no connector, fall back to `core.action.http` or flag the gap in Open Questions
