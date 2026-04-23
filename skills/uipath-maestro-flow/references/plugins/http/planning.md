# HTTP Request Node — Planning

## Node Type

**Default: `core.action.http.v2`** (Managed HTTP Request). Use v1 (`core.action.http`) only in one narrow case — see below.

- **`core.action.http.v2`** (Managed HTTP Request) — default for all HTTP calls. Works for both IS connector-managed auth (OAuth via a connection) and manual auth. Requires `uip maestro flow node configure` to populate `inputs.detail` + generate `bindings_v2.json`. `supportsErrorHandling: true` enables the implicit `error` port.
- **`core.action.http`** (v1, standalone) — use ONLY for **public APIs with no authentication** (e.g., open-meteo, public data endpoints where you send zero auth headers). Smaller flow files and no connection resource needed.

> **Check for a connector first.** Before using either HTTP node, run `uip maestro flow registry search "<service>"` to see if an IS connector exists for the target service (Slack, Salesforce, Jira, GitHub, etc.). If one does, **use the connector** — not raw HTTP with a bearer token. IS connectors handle auth, retries, pagination, and schema shape.

> **Never use v1 with `authenticationType: "connection"`** — the v1 node does not pass IS credentials at runtime. If you need IS-managed auth, use v2.

## When to Use

Default to v2 managed HTTP. Fall back to v1 only when all of: (a) the target service has no IS connector, (b) no authentication is required, (c) the flow needs a trivial REST call with no retry/error-port plumbing.

### Selection Heuristics

| Situation | Node |
| --- | --- |
| Target service has an IS connector (Slack, Salesforce, Jira, GitHub, etc.) | Neither — use [Connector Activity](../connector/planning.md) |
| IS connector exists but lacks the specific curated activity, and you need its auth | **v2** — connector mode |
| Public REST API, **no auth at all** (e.g., open-meteo, public weather/data) | **v1** — simplest; no connection resource needed |
| Public REST API, simple manual auth (static API key / bearer token) AND no IS connector | **v2** manual mode (keeps error-port + retry pattern) |
| Any call that needs the implicit `error` output port or `inputs.branches` | **v2** — v1 has no `supportsErrorHandling` |
| Target system has no API (desktop app) | Neither — use [RPA Workflow](../rpa/planning.md) |

### Two Authentication Modes

| Mode | When to use | Key `--detail` fields |
| --- | --- | --- |
| **Connector** | A connector exists for the service — uses IS connection for OAuth/API key auth | `authentication: "connector"`, `targetConnector`, `connectionId`, `folderKey`, `url` |
| **Manual** | No connector, or public API with no auth needed | `authentication: "manual"`, `url` |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `default`, `error`, `branch-{id}` (dynamic, one per `inputs.branches` entry) |

- `default` — primary success output, or fallback when configured branches don't match.
- `error` — implicit error port; fires when the call fails (network error, timeout, non-2xx not caught by a branch). Shared with all action nodes — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).
- `branch-{id}` — HTTP-specific, configured via `inputs.branches` (response-content routing). See [Conditional Branches](#conditional-branches) below.

## Output Variables

- `$vars.{nodeId}.output` — `{ body, code, method, rawStringBody, request }` on success
- `$vars.{nodeId}.error` — `{ code, message, detail, category, status }` when the error port fires

## Conditional Branches

Use `inputs.branches` when you need to route downstream paths based on response content (e.g., empty vs non-empty results). For generic call-failure handling, prefer the shared `error` port instead — don't enumerate every bad status code as a branch.

Each branch's `conditionExpression` is a JS expression with `$self` bound to the current HTTP node's output:

```json
{
  "inputs": {
    "branches": [
      { "id": "hasItems",  "name": "Has Items",  "conditionExpression": "$self.output.body.items.length > 0" },
      { "id": "empty",     "name": "Empty",      "conditionExpression": "$self.output.body.items.length == 0" }
    ]
  }
}
```

Wire `branch-hasItems` / `branch-empty` as source ports on outgoing edges. `default` fires when no branch condition matches.

> **Do not use `=js:` on `conditionExpression`** — HTTP branch conditions are evaluated as JS automatically (same rule as decision/switch expressions). See [variables-and-expressions.md](../../variables-and-expressions.md#http-branch-condition-inputsbranchesconditionexpression).

## Dynamic values

IS activity input fields (`url`, `headers`, `body`, `query` under `bodyParameters`) do **not** resolve `{$vars.x}` brace-templates — the template runner only applies to native flow fields. Use `=js:` expressions for any dynamic value; template literals with `${...}` interpolation or string concatenation both work. See [Step 3b — Dynamic values](impl.md#step-3b--dynamic-values-in-url--headers--body--query) for the full rationale and examples.

## Key Inputs (`--detail` for `node configure`)

Run `uip maestro flow node configure` with a `--detail` JSON. The CLI builds the full `inputs.detail` payload, `bindings_v2.json`, and connection resource files automatically. **Do not hand-write `inputs.detail`.**

**Connector mode** (IS connection auth):

| `--detail` Key | Required | Description |
| --- | --- | --- |
| `authentication` | Yes | `"connector"` |
| `method` | Yes | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `targetConnector` | Yes | Target connector key (e.g., `"uipath-salesforce-slack"`) |
| `connectionId` | Yes | Target connector's IS connection ID (from `uip is connections list`) |
| `folderKey` | Yes | Orchestrator folder key (from `uip is connections list`) |
| `url` | No | API endpoint URL/path (e.g., `"/conversations.replies"`). Auto-fills both `bodyParameters.path` and `bodyParameters.url`. |
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

## Prerequisites

- `uip login` required (for both modes — node type comes from registry)
- For connector mode: a healthy IS connection for the **target connector**
- `uip maestro flow registry pull` to cache the `core.action.http.v2` definition

## Planning Annotation

In the architectural plan, annotate managed HTTP nodes as:
- Connector mode: `managed-http: <service> — <operation>` (e.g., "managed-http: Slack — GET /conversations.replies")
- Manual mode: `managed-http: manual — <method> <url>` (e.g., "managed-http: manual — GET https://api.example.com/data")
