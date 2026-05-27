# Connector Activity Nodes — Planning

Connector activity nodes call external services (Jira, Slack, Salesforce, Outlook, etc.) via UiPath Integration Service. They are dynamically loaded — not built-in — and appear in the registry after `uip login` + `uip maestro flow registry pull`.

## When to Use

Use a connector activity node when the flow needs to **call an external service that has a pre-built UiPath connector**. Connectors handle auth (OAuth, API keys), token refresh, and error formatting automatically at runtime. Note: design-time reference resolution (looking up records by name during authoring) still requires the agent to paginate — see [impl.md](impl.md).

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
- `uip maestro flow registry pull` must be run to cache connector node types locally

### When NOT to Use

- **No connector exists for the service** — use `core.action.http.v2` manual mode instead
- **Simple GET request with no auth** — `core.action.http.v2` (manual mode) is simpler and faster to configure
- **The operation needs desktop/browser interaction** — use an RPA resource node
- **The task requires reasoning or judgment** — use an agent node

## Node Type Pattern

`uipath.connector.<connector-key>.<activity>`

Examples:
- `uipath.connector.uipath-salesforce-slack.send-message`
- `uipath.connector.uipath-atlassian-jira.create-issue`

## Discovery

```bash
uip maestro flow registry search <service> --output json
```

Confirm `category: "connector"` in the results. If the connector key fails, list all connectors:

```bash
uip is connectors list --output json
```

Keys are often prefixed — e.g., `uipath-salesforce-slack` not `slack`.

### Sanity-check before deciding "no connector activity exists"

A `registry search <service>` that returns **only `uipath.connector.trigger.*`** entries — zero activity entries — is **suspicious, not authoritative**. Connector activities and triggers are independent fetches against different typecache endpoints; the registry cache can transiently miss the activity branch when one of those endpoints flakes (TTL: 30 min). Falling through to managed HTTP at this point produces a flow that *validates* but skips the real connector node — a silent topology mistake.

When `registry search` returns triggers but **no activities** for a service whose connector you've already confirmed exists (`uip is connectors list`), or returns nothing at all for a well-known connector, **force a fresh pull before falling back**:

```bash
uip maestro flow registry pull --force
uip maestro flow registry search <service> --output json
```

If the second search still returns no activities for that connector, the fallback to managed HTTP (Tier 2 below) is legitimate. If the second search now lists activities, the cache was stale — proceed with the connector activity node as Tier 1.

> **Why this matters**: a partial registry pull is an indirect failure — `registry pull` reports `Success` even when one node-source branch silently dropped its contribution. The shape (`triggers > 0 && activities == 0`) is the only local signal you have. Treat it like a stale-cache symptom, not a topology fact.

### Disambiguation — when search returns multiple connectors for the same intent

`uip maestro flow registry search <keyword>` routinely returns multiple connectors for the same user intent (e.g. searching `databricks` returns both the native AI-serving connector and the JDBC gateway). **Never silently pick the first match.**

Apply the canonical disambiguation ladder owned by Integration Service:

- [/uipath:uipath-platform — Integration Service — connectors.md — Connector Disambiguation](../../../../../../uipath-platform/references/integration-service/connectors.md#connector-disambiguation) — classify catalog/custom/mock, intent-match by `Description`, count remaining candidates (1 → silent, >1 → AskUser, 0 catalog → STOP).
- [/uipath:uipath-platform — Integration Service — connectors.md — JDBC Gateway — Database SQL Intent](../../../../../../uipath-platform/references/integration-service/connectors.md#jdbc-gateway--database-sql-intent) — special handling when the user's intent is a database SQL operation (native connector vs JDBC gateway, connection-name keyword matching, decision matrix, lifecycle disclosure).

Lock the chosen connector key in the planning notes — never re-derive per node within the same flow.

### Check Connector Connections

For each connector found in registry search, verify a healthy connection exists. Extract the connector key from the node type name (e.g., `uipath.connector.uipath-microsoft-outlook365.get-newest-email` -> key is `uipath-microsoft-outlook365`).

**Never type a connector key from memory.** Use the key from the `registry search` node type only. `uipath-gmail` / `uipath-microsoft-office365` are wrong; the real keys (`uipath-google-gmail`, `uipath-microsoft-outlook365`) appear only in `registry search` output.

```bash
uip is connections list "<connector-key>" --all-folders --output json
```

> `--all-folders` is mandatory. Without it the CLI returns the active folder only and hides connections in other folders the user can see. Plain `uip is connections list "<connector-key>"` is forbidden for discovery.

- If a default enabled connection exists (`IsDefault: Yes`, `State: Enabled`), record the connection ID for implementation planning.
- **If the result is empty, do not conclude "no connection exists."** An empty `connections list` is suspicious, not authoritative. Three things must hold before you treat it as real: (a) the key came from `registry search`, not memory; (b) the call used `--all-folders`; (c) a `--refresh` retry was still empty. Only then surface it in **Open Questions** so the user can create one while reviewing. Never ask the user a connection-creation question on an unverified empty result. See [impl.md](impl.md) for the platform-skill empty-result recovery path shared with implementation.

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `success`, `error` |

The `error` port is the implicit error port shared with all action nodes — see [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.output` — the connector response (structure depends on the operation)
- `$vars.{nodeId}.error` — error details if the call fails

## HTTP Fallback (Managed HTTP Request)

When a connector exists but lacks the specific curated activity, use `core.action.http.v2` (Managed HTTP Request). This node proxies through the `uipath-uipath-http` connector and uses the **target connector's** IS connection for authentication — you supply the API URL and payload.

> **Do NOT use individual connector HTTP request nodes** (e.g., `uipath.connector.<key>.http-request`). Always use the unified `core.action.http.v2` Managed HTTP Request node for non-curated API calls.

> **Do NOT use `core.action.http` (v1) with `authenticationType: "connection"` for this.** The v1 node does not pass IS credentials at runtime. Always use `core.action.http.v2`.

See [http/planning.md](../http/planning.md) for full selection heuristics and [http/impl.md](../http/impl.md) for configuration via `uip maestro flow node configure`.

Note as `managed-http: <service> — <operation>` during planning.

## Planning Annotation

In the architectural plan, annotate connector nodes as:
- `connector: <service-name>` with the intended operation (e.g., "connector: Jira — create issue")
- If discovery found no connector, fall back to `core.action.http.v2` (manual mode) or flag the gap in Open Questions
