# HTTP Request Node — Planning

## Node Type

`core.action.http.v2` (Managed HTTP Request)

> **Always use `core.action.http.v2`** for all HTTP requests — both connector-authenticated and manual. The older `core.action.http` (v1) is deprecated and does not pass IS credentials at runtime.

## When to Use

Use a managed HTTP node to call a REST API — either with IS connector-managed authentication or with manual auth (raw URL).

### Selection Heuristics

| Situation | Use Managed HTTP? |
| --- | --- |
| Connector exists but lacks the specific curated activity | Yes — connector mode with target connector's connection |
| No connector exists, but service has a REST API | Yes — manual mode with full URL |
| Quick prototyping against any REST API | Yes — manual mode |
| Connector exists and covers the use case | No — use [Connector Activity](../connector/planning.md) |
| Target system has no API (desktop app) | No — use [RPA Workflow](../rpa/planning.md) |

### Two Authentication Modes

| Mode | When to use | Key `--detail` fields |
| --- | --- | --- |
| **Connector** | A connector exists for the service — uses IS connection for OAuth/API key auth | `authentication: "connector"`, `targetConnector`, `connectionId`, `folderKey`, `url` |
| **Manual** | No connector, or public API with no auth needed | `authentication: "manual"`, `url` |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `branch-{id}` (dynamic, one per `inputs.branches` entry), `default` |

The HTTP node has **no dedicated `error` source port**. To branch on specific response conditions (non-2xx status, missing fields, etc.), configure `inputs.branches` — each entry creates a `branch-{id}` port; `default` is the fallback. See [Conditional Branches](#conditional-branches) below.

## Output Variables

- `$vars.{nodeId}.output` — `{ body, code, method, rawStringBody, request }` on success
- `$vars.{nodeId}.error` — `{ code, message, detail, category, status }` on failure

## Conditional Branches

Use `inputs.branches` to route to different downstream paths based on the response. Each branch's `conditionExpression` is a JS expression with `$self` bound to the current HTTP node's output:

```json
{
  "inputs": {
    "branches": [
      { "id": "ok",       "name": "OK",       "conditionExpression": "$self.output.statusCode >= 200 && $self.output.statusCode < 300" },
      { "id": "notFound", "name": "Not Found", "conditionExpression": "$self.output.statusCode == 404" }
    ]
  }
}
```

Wire `branch-ok` and `branch-notFound` as source ports on outgoing edges. `default` fires when no branch condition matches.

> **Do not use `=js:` on `conditionExpression`** — HTTP branch conditions are evaluated as JS automatically (same rule as decision/switch expressions). See [variables-and-expressions.md](../../variables-and-expressions.md#http-branch-condition-inputsbranchesconditionexpression).

Configuring branches also changes fault behavior: when a branch matches a non-2xx response, the node routes through that branch instead of faulting. Without any branches, non-2xx responses fault the whole flow.

## Key Inputs (`--detail` for `node configure`)

Run `uip flow node configure` with a `--detail` JSON. The CLI builds the full `inputs.detail` payload, `bindings_v2.json`, and connection resource files automatically. **Do not hand-write `inputs.detail`.**

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
- `uip flow registry pull` to cache the `core.action.http.v2` definition

## Planning Annotation

In the architectural plan, annotate managed HTTP nodes as:
- Connector mode: `managed-http: <service> — <operation>` (e.g., "managed-http: Slack — GET /conversations.replies")
- Manual mode: `managed-http: manual — <method> <url>` (e.g., "managed-http: manual — GET https://api.example.com/data")
