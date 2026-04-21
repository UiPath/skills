# HTTP Request Node — Implementation

## Node Type

`core.action.http.v2` (Managed HTTP Request)

> **Always use `core.action.http.v2`** for all HTTP requests. The older `core.action.http` (v1) is deprecated.

## Registry Validation

```bash
uip flow registry get core.action.http.v2 --output json
```

Confirm in `Data.Node.handleConfiguration`: target port `input`, source ports `branch-{item.id}` (dynamic, `repeat: inputs.branches`) and `default`. Also confirm `Data.Node.supportsErrorHandling: true` — HTTP v2 participates in the shared implicit `error` port pattern used by all action nodes. See [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes). Model serviceType is `Intsvc.UnifiedHttpRequest`.

## Critical: Use `node configure`

> **Do not hand-write `inputs.detail`, `bindings_v2.json`, or connection resource files.** Run `uip flow node configure` — it builds everything from a simple `--detail` JSON. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime.

## Configuration Workflow

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
