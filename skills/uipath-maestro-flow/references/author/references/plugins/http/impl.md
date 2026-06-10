# HTTP Request Node — Implementation

This page is the entry point for implementing a managed HTTP node. Pick your auth mode below, then follow the matching walkthrough end-to-end. The "Shared Reference" section is an appendix — the mode walkthroughs already inline what you need to act, and link here only for full rationale and extended examples.

## Node Type

`core.action.http.v2` (Managed HTTP Request)

> **Always use `core.action.http.v2`** for all HTTP requests. The older `core.action.http` (v1) is deprecated.

## Pick a Mode

| Mode | Use when | Walkthrough |
| --- | --- | --- |
| **Connector** | Target system has an IS connector — auth via an existing IS connection (OAuth/API key) | [impl-connector.md](impl-connector.md) |
| **Manual** | No connector exists, public/no-auth API, or quick prototyping | [impl-manual.md](impl-manual.md) |

> **Mode fallback — auto-try, then confirm.** Prefer a curated connector activity first; if none, use connector mode; if connector mode cannot be configured (no usable IS connection), fall through to manual mode automatically. Manual changes the auth model (you supply auth yourself), so confirm the switched mode with the user via `AskUserQuestion` before finalizing. See [impl-connector.md — Step 2](impl-connector.md#step-2--identify-target-connection).

The `--detail` payload differs in two places between modes: `authentication` (`"connector"` vs `"manual"`), and the connector-binding fields `targetConnector` / `connectionId` / `folderKey` (connector mode only; `url` is then relative to the connector base, vs. an absolute URL in manual mode). Everything else (node add, dynamic values, branches, edges, debug) is shared.

## Critical: Use `node configure`

> **Do not hand-write `inputs.detail`, `bindings_v2.json`, or connection resource files.** Run `uip maestro flow node configure` — it builds everything from a simple `--detail` JSON. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime. `core.action.http.v2` is CLI-owned per [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node) (same envelope rules as connector activities).

## Registry validation

```bash
uip maestro flow registry get core.action.http.v2 --output json
```

Confirm in `Data.Node.handleConfiguration`: target port `input`, source ports `branch-{item.id}` (dynamic, `repeat: inputs.branches`) and `default`. Also confirm `Data.Node.supportsErrorHandling: true` — HTTP v2 participates in the implicit `error` port pattern shared by every action node (see [Action Node Structure](../../../../shared/action-nodes.md)). Model `serviceType` is `Intsvc.UnifiedHttpRequest`.

---

## Shared Reference (appendix)

The mode walkthroughs link into the sections below for full rationale and extended examples. You do not need to read this section in order — jump directly from the walkthrough link that brought you here.

### Add the node

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```

The CLI copies the manifest into `definitions[]`, adds the node instance to `nodes[]`, registers the `variables.nodes` entries, and inserts a placeholder in `layout.nodes` — all in code, byte-for-byte from the registry (including `typeVersion`, which the CLI pulls from the manifest's `version` field; do not hardcode it). Save the returned node ID — both walkthroughs reuse it.

The CLI initializes `inputs` from the manifest's `inputDefaults`:

```json
"inputs": {
  "branches": [],
  "timeout": "PT15M",
  "retryCount": 0,
  "swaggerDefinition": null,
  "detail": {}
}
```

`inputs.detail` is populated by the configure step (next). The inputs-level siblings — `branches`, `timeout`, `retryCount` — are set at `node add` time via `--input`:

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" \
  --input '{
    "timeout": "PT30M",
    "retryCount": 3,
    "branches": [
      { "id": "hasItems", "name": "Has Items", "conditionExpression": "$self.output.body.items.length > 0" },
      { "id": "empty",    "name": "Empty",    "conditionExpression": "$self.output.body.items.length == 0" }
    ]
  }' --output json
```

- `timeout` — ISO 8601 duration (e.g. `PT15M`, `PT1H`, `P1D`). Default `PT15M`.
- `retryCount` — integer. Default `0`.
- `branches` — see [Conditional branches](#conditional-branches) below.

> **Do not hand-author the `core.action.http.v2` definition, and do not `Edit` `inputs.*` after the fact.** Use `uip maestro flow node add` (with `--input` for branches/timeout/retryCount) and `uip maestro flow node configure` (for `inputs.detail`). These are the only supported authoring paths.

### Dynamic values in URL / headers / body / query

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

When calling `uip maestro flow node configure --detail`, pass the `=js:` string verbatim — the CLI stores it in `inputs.detail.bodyParameters` unchanged:

```bash
uip maestro flow node configure <Project>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "=js:`https://api.example.com/users/${$vars.userId}`"
  }' --output json
```

### Conditional branches

Skip this section unless you need to route downstream paths based on the *response content* (e.g., `items.length > 0` vs empty). Do **not** use `branches` just to handle call failures — for that, use the `error` port (see [Wire edges](#wire-edges)).

Each branch entry creates a `branch-{id}` source port. `$self` refers to the current HTTP node's output inside the condition.

Set `branches` at `node add` time via `--input` (see [Add the node](#add-the-node)) — `branches` lives at `inputs.branches`, not `inputs.detail.branches`, and `node configure --detail` does not accept it.

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" \
  --input '{
    "branches": [
      { "id": "hasItems", "name": "Has Items", "conditionExpression": "$self.output.body.items.length > 0" },
      { "id": "empty",    "name": "Empty",    "conditionExpression": "$self.output.body.items.length == 0" }
    ]
  }' --output json
```

> **Do not prefix `conditionExpression` with `=js:`** — HTTP branch conditions are auto-evaluated as JS (same rule as decision/switch expressions).

### Wire edges

The managed HTTP node's target port is `input`. Its source ports are:

- `default` — primary success output (or fallback when configured branches don't match)
- `error` — fires when the HTTP call fails (network error, timeout, non-2xx not caught by a branch); wire this to an error handler to keep the flow from faulting
- `branch-{id}` — one per entry in `inputs.branches` ([Conditional branches](#conditional-branches)); use the exact `id` you set

Use `Edit` to add edge objects to `edges[]`; do not use `uip maestro flow edge add` for this structural wiring. Examples:

```json
{
  "id": "e-<upstreamNodeId>-<nodeId>",
  "sourceNodeId": "<upstreamNodeId>",
  "sourcePort": "<port>",
  "targetNodeId": "<nodeId>",
  "targetPort": "input"
}
```

```json
{
  "id": "e-<nodeId>-<downstreamNodeId>",
  "sourceNodeId": "<nodeId>",
  "sourcePort": "default",
  "targetNodeId": "<downstreamNodeId>",
  "targetPort": "input"
}
```

```json
{
  "id": "e-<nodeId>-<errorHandlerId>",
  "sourceNodeId": "<nodeId>",
  "sourcePort": "error",
  "targetNodeId": "<errorHandlerId>",
  "targetPort": "input"
}
```

When an HTTP node has an outgoing `error` edge, the HTTP node instance must also include `inputs.errorHandlingEnabled: true`. `uip maestro flow edge add --source-port error` and `uip maestro flow format` set this automatically; direct JSON edits must set it explicitly.

```json
{
  "id": "e-<nodeId>-<hasItemsDownstream>",
  "sourceNodeId": "<nodeId>",
  "sourcePort": "branch-hasItems",
  "targetNodeId": "<hasItemsDownstream>",
  "targetPort": "input"
}
```

### Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `not_authed` or 401/403 | Wrong node type (v1 instead of v2), missing bindings, or expired connection | Verify node type is `core.action.http.v2`, check `bindings_v2.json` exists, ping the connection |
| `configuration` field missing | Node not configured via CLI | Run `uip maestro flow node configure` — do not hand-write `inputs.detail` |
| `flow validate` errors with `uiPathActivityTypeId` missing on `core.action.http.v2` | Node was hand-authored in `definitions[]` instead of via `uip maestro flow node add` | Remove the node, re-add it via `uip maestro flow node add <file> core.action.http.v2 ...`, then re-run `node configure`. |
| Connection not found | Wrong connection ID or connector key | Re-run `uip is connections list` for the target connector |
| Wrong API response | Incorrect `url` or `query` | Check the target service's API documentation |
| `ImplicitConnection` errors | Manual mode misconfigured | Verify `authentication: "manual"` and `url` is a full URL |
| Flow faults on 4xx/5xx response | No `error` edge wired from the HTTP node | Add an edge with `sourcePort: "error"` to an error-handler node. See [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes) — same mechanism applies to all action nodes |
| Edge `source-port output` rejected | Referencing the variable namespace as a port name | HTTP source ports are `default`, `error`, and `branch-{id}` — not `output`. The `output` name is only a variable namespace (`$vars.{nodeId}.output`) |
