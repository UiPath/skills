# HTTP Request Nodes — Planning

Two HTTP node types exist. Pick based on whether you need connector-managed authentication.

## Node Types

| Node Type | Version | When to Use |
| --- | --- | --- |
| `core.action.http.v2` | 2.0.0 | **Preferred.** Call a REST API with IS connector-managed auth (OAuth, API keys). Use this when a connector exists but lacks the specific curated activity. |
| `core.action.http` | 1.0.0 | Call a REST API with **manual** auth (bearer token in headers) or no auth. Use for services with no IS connector, or quick prototyping. |

> **Never use `core.action.http` (v1) for connector-authenticated requests.** The v1 node's `authenticationType: "connection"` input does not pass credentials at runtime — use `core.action.http.v2` instead.

---

## `core.action.http.v2` — Managed HTTP Request

Use when a connector exists for the service but lacks the specific endpoint (curated activity). The managed HTTP node proxies through the `uipath-uipath-http` connector and uses the target connector's connection for auth.

### Selection Heuristics

| Situation | Use Managed HTTP? |
| --- | --- |
| Connector exists but lacks the specific curated activity | Yes — use target connector's connection for auth |
| Connector exists and covers the use case | No — use [Connector Activity](../connector/planning.md) |
| No connector exists for the service | No — use `core.action.http` (v1) with manual auth |
| Simple GET with no auth | No — use `core.action.http` (v1) |

### Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

### Output Variables

- `$vars.{nodeId}.output` — `{ body, code, method, rawStringBody, request }`

### Key Inputs (`--detail` for `node configure`)

Run `uip flow node configure` with a `--detail` JSON. The CLI builds the full `inputs.detail` payload, `bindings_v2.json`, and connection resource files automatically. **Do not hand-write `inputs.detail`.**

**Connector mode** (IS connection auth):

| `--detail` Key | Required | Description |
| --- | --- | --- |
| `authentication` | Yes | `"connector"` |
| `method` | Yes | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `targetConnector` | Yes | Target connector key (e.g., `"uipath-salesforce-slack"`) |
| `connectionId` | Yes | Target connector's IS connection ID (from `uip is connections list`) |
| `folderKey` | Yes | Orchestrator folder key (from `uip is connections list`) |
| `path` | No | API endpoint path (e.g., `"/conversations.replies"`) |
| `query` | No | Query parameters as key-value object |
| `headers` | No | Additional headers as key-value object |
| `body` | No | Request body (for POST/PUT/PATCH) |

**Manual mode** (no connector auth):

| `--detail` Key | Required | Description |
| --- | --- | --- |
| `authentication` | Yes | `"manual"` |
| `method` | Yes | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `url` | Yes | Full target URL |
| `query` | No | Query parameters as key-value object |
| `headers` | No | Additional headers as key-value object |
| `body` | No | Request body (for POST/PUT/PATCH) |

### Prerequisites

- `uip login` required
- A healthy IS connection for the **target connector** (e.g., Slack, Jira)
- `uip flow registry pull` to cache the `core.action.http.v2` definition

### Planning Annotation

In the architectural plan, annotate managed HTTP nodes as:
- `managed-http: <service> — <operation>` (e.g., "managed-http: Slack — GET /conversations.replies")
- Note the target connector key and intended API path. Phase 2 resolves the connection and configures the node.

---

## `core.action.http` — Standalone HTTP Request

Use for one-off API calls to services **without** a connector, or when no auth is needed.

### Selection Heuristics

| Situation | Use Standalone HTTP? |
| --- | --- |
| No connector exists for the service | Yes |
| Quick prototyping against any REST API | Yes |
| Connector exists but lacks the specific endpoint | No — use `core.action.http.v2` (managed HTTP) |
| Connector exists and covers the use case | No — use [Connector Activity](../connector/planning.md) |
| Target system has no API (desktop app) | No — use [RPA Workflow](../rpa/planning.md) |

### Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `default`, `branch-{id}` (dynamic per branch) |

**Dynamic ports:** Each entry in `branches` creates a `branch-{item.id}` output port. If no branch condition matches, flow goes to `default`.

### Output Variables

- `$vars.{nodeId}.output` — `{ body, statusCode, headers }`
- `$vars.{nodeId}.error` — error details if the call fails

### Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `method` | Yes | GET, POST, PUT, PATCH, DELETE |
| `url` | Yes | Target URL or `=js:` expression |
| `headers` | No | Key-value pairs (include `Authorization` header for manual auth) |
| `body` | No | Request body string |
| `contentType` | No | Default `application/json` |
| `timeout` | No | ISO 8601 duration (default `PT15M`) |
| `retryCount` | No | Retries on failure (default 0) |
| `branches` | No | Response routing conditions |

### Planning Annotation

In the architectural plan, note the HTTP method and URL pattern. Use `<PLACEHOLDER>` for values that Phase 2 must resolve.
