# HTTP Request Node

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
| Connector exists and covers the use case | No — use [Connector Activity](../connector/flow-plan.md) |
| Target system has no API (desktop app) | No — use [RPA Workflow](../rpa/flow-plan.md) |

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

IS activity input fields (`url`, `headers`, `body`, `query` under `bodyParameters`) do **not** resolve `{$vars.x}` brace-templates — the template runner only applies to native flow fields. Use `=js:` expressions for any dynamic value; template literals with `${...}` interpolation or string concatenation both work. See [Step 3b — Dynamic values](#step-3b--dynamic-values-in-url--headers--body--query) for the full rationale and examples.

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

## Discovery

The node type `core.action.http.v2` is available from the registry after `uip flow registry pull`.

## Registry Validation

```bash
uip flow registry get core.action.http.v2 --output json
```

Confirm in `Data.Node.handleConfiguration`: target port `input`, source ports `branch-{item.id}` (dynamic, `repeat: inputs.branches`) and `default`. Also confirm `Data.Node.supportsErrorHandling: true` — HTTP v2 participates in the shared implicit `error` port pattern used by all action nodes. See [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes). Model serviceType is `Intsvc.UnifiedHttpRequest`.

## Adding / Editing — Configuration Workflow

### Critical: Use `node configure`

> **Do not hand-write `inputs.detail`, `bindings_v2.json`, or connection resource files.** Run `uip flow node configure` — it builds everything from a simple `--detail` JSON. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime.

### Step 1 — Add the node

```bash
uip flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<Label>" --output json
```

### Step 2 — Identify target connector and connection (connector mode only)

Skip this step for manual mode.

```bash
# List connections for the target connector (e.g., Slack)
uip is connections list "<target-connector-key>" --output json

# Verify the connection is healthy
uip is connections ping "<connection-id>" --output json
```

Record the `Id` and `FolderKey` from the connection.

### Step 3 — Configure the node

**Connector mode** (IS connection auth):

```bash
uip flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "connector",
    "targetConnector": "<target-connector-key>",
    "connectionId": "<target-connection-id>",
    "folderKey": "<folder-key>",
    "method": "GET",
    "url": "/api/endpoint",
    "query": {"param1": "value1"}
  }'
```

**Manual mode** (no connector auth):

```bash
uip flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/endpoint",
    "query": {"param1": "value1"}
  }'
```

**What the CLI handles automatically:**
- Builds the full `inputs.detail` structure (connector, connectionId, bodyParameters, essentialConfiguration)
- For connector mode: generates `bindings_v2.json` and creates a connection resource file under `resources/solution_folder/connection/`
- For manual mode: uses `ImplicitConnection` (no bindings needed)

### Step 3b — Dynamic values in URL / headers / body / query

**IS activity input fields do not resolve `{$vars.x}` brace-templates.** The flow runtime's `{...}` template interpolation only applies to native flow fields (end-node output `source`, variable updates, decision `expression`, script body, etc.) — **not** to fields under `inputs.detail.bodyParameters` on HTTP v2 or on any `uipath.connector.*` activity. Evidence: `"url": "https://.../user/{$vars.article}/..."` ships to the service as literal `{vars.article}` (the `$` is stripped, braces remain), producing a 400 Bad Request.

**Use `=js:` expressions for any dynamic value in IS activity inputs.** The runtime evaluates `=js:` before handing the value to the connector:

```json
"bodyParameters": {
  "url": "=js:`https://api.example.com/users/${$vars.userId}/orders`",
  "headers": {
    "Authorization": "=js:'Bearer ' + $vars.apiToken",
    "X-Request-ID": "=js:$metadata.instanceId"
  },
  "query": {
    "since": "=js:$vars.startDate"
  }
}
```

Template literals with `${...}` interpolation work because the whole expression is evaluated as JavaScript — `$vars` is a global in the `=js:` context. Plain string concatenation (`'Bearer ' + $vars.token`) works the same way.

When calling `uip flow node configure --detail`, pass the `=js:` string verbatim — the CLI stores it in `inputs.detail.bodyParameters` unchanged:

```bash
uip flow node configure <Project>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "=js:`https://api.example.com/users/${$vars.userId}`"
  }'
```

### Step 4 — (Optional) Configure response branches for content-based routing

Skip this step unless you need to route downstream paths based on the *response content* (e.g., `items.length > 0` vs empty). Do **not** use `branches` just to handle call failures — for that, use the `error` port (Step 5).

Each branch entry creates a `branch-{id}` source port. `$self` refers to the current HTTP node's output inside the condition.

```bash
uip flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "branches": [
      { "id": "hasItems",  "name": "Has Items",  "conditionExpression": "$self.output.body.items.length > 0" },
      { "id": "empty",     "name": "Empty",      "conditionExpression": "$self.output.body.items.length == 0" }
    ]
  }'
```

> **Do not prefix `conditionExpression` with `=js:`** — HTTP branch conditions are auto-evaluated as JS (same rule as decision/switch expressions).

### Step 5 — Wire edges

The managed HTTP node's target port is `input`. Its source ports are:

- `default` — primary success output (or fallback when configured branches don't match)
- `error` — fires when the HTTP call fails (network error, timeout, non-2xx not caught by a branch); wire this to an error handler to keep the flow from faulting
- `branch-{id}` — one per entry in `inputs.branches` (Step 4); use the exact `id` you set

```bash
# Edge into the HTTP node
uip flow edge add <ProjectName>.flow <upstreamNodeId> <nodeId> \
  --source-port <port> --target-port input --output json

# Simple: single outgoing edge on "default"
uip flow edge add <ProjectName>.flow <nodeId> <downstreamNodeId> \
  --source-port default --target-port input --output json

# With error handler: wire the implicit "error" port
uip flow edge add <ProjectName>.flow <nodeId> <errorHandlerId> \
  --source-port error --target-port input --output json

# With conditional branches: one edge per configured branch (default/error still apply)
uip flow edge add <ProjectName>.flow <nodeId> <hasItemsDownstream> \
  --source-port branch-hasItems --target-port input --output json
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `not_authed` or 401/403 | Wrong node type (v1 instead of v2), missing bindings, or expired connection | Verify node type is `core.action.http.v2`, check `bindings_v2.json` exists, ping the connection |
| `configuration` field missing | Node not configured via CLI | Run `uip flow node configure` — do not hand-write `inputs.detail` |
| Connection not found | Wrong connection ID or connector key | Re-run `uip is connections list` for the target connector |
| Wrong API response | Incorrect `url` or `query` | Check the target service's API documentation |
| `ImplicitConnection` errors | Manual mode misconfigured | Verify `authentication: "manual"` and `url` is a full URL |
| Flow faults on 4xx/5xx response | No `error` edge wired from the HTTP node | Add an edge with `sourcePort: "error"` to an error-handler node. See [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes) — same mechanism applies to all action nodes |
| Edge `source-port output` rejected | Referencing the variable namespace as a port name | HTTP source ports are `default`, `error`, and `branch-{id}` — not `output`. The `output` name is only a variable namespace (`$vars.{nodeId}.output`) |
