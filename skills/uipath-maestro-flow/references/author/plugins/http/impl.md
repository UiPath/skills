# HTTP Request Node — Implementation

Implement managed HTTP requests with `core.action.http.v2`: choose a mode, add the node with the CLI, configure it with `node configure`, wire its ports, and validate it.

## Node type and mode

Use `core.action.http.v2` for every HTTP request. `core.action.http` (v1) is deprecated.

| Mode | Use when | Walkthrough |
| --- | --- | --- |
| **Connector** | The target system has an IS connector and authentication uses an existing IS connection (OAuth/API key). | [impl-connector.md](impl-connector.md) |
| **Manual** | No connector exists, the API is public/no-auth, or quick prototyping is required. | [impl-manual.md](impl-manual.md) |

Prefer a curated connector activity. If none exists, try connector mode. If it cannot be configured because the connector lacks HTTP request support (`HasHttpRequest` false) or no usable IS connection exists, fall through to manual mode automatically. Confirm the switch with the user before finalizing because manual mode changes authentication. See [impl-connector.md — Step 2](impl-connector.md#step-2--identify-target-connection).

The `--detail` payload differs by mode only in `authentication` (`"connector"` or `"manual"`) and connector-only fields `targetConnector`, `connectionId`, and `folderKey`. Connector-mode `url` is relative to the connector base; manual-mode `url` is absolute. Node creation, dynamic values, branches, edges, and debugging are shared.

<a id="critical-use-node-configure"></a>
## Configure through the CLI

Do not hand-write `inputs.detail`, `bindings_v2.json`, or connection resource files. Run `uip maestro flow node configure`; it builds the required configuration from `--detail`, including `essentialConfiguration`. `core.action.http.v2` is CLI-owned per [Author capability — Node ownership](../../CAPABILITY.md#node-ownership--who-authors-the-node), with the same envelope rules as connector activities.

## Validate the registry

Run:

```bash
uip maestro flow registry get core.action.http.v2 --output json
```

Confirm `Data.Node.handleConfiguration` has target port `input` and source ports `branch-{item.id}` (dynamic, `repeat: inputs.branches`) and `default`; `Data.Node.supportsErrorHandling: true`; and model `serviceType` is `Intsvc.UnifiedHttpRequest`. HTTP v2 uses the implicit `error` port pattern shared by action nodes (see [Action Node Structure](../../../shared/action-nodes.md)).

<a id="add-the-node"></a>
## Add and configure

Run:

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```

Save the returned node ID. The CLI copies the manifest into `definitions[]`, adds the node to `nodes[]`, registers `variables.nodes`, inserts a `layout.nodes` placeholder byte-for-byte from the registry, and obtains `typeVersion` from the manifest's `version`; do not hardcode it.

The CLI initializes:

```json
"inputs": {
  "branches": [],
  "timeout": "PT15M",
  "retryCount": 0,
  "swaggerDefinition": null,
  "detail": {}
}
```

Set `branches`, `timeout`, and `retryCount` during `node add` with `--input`; populate `inputs.detail` only with `node configure --detail`:

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

`timeout` is an ISO 8601 duration such as `PT15M`, `PT1H`, or `P1D` and defaults to `PT15M`. `retryCount` is an integer and defaults to `0`. `branches` is optional and belongs at `inputs.branches`, not `inputs.detail.branches`. Do not edit `inputs.*` afterward or hand-author the definition; run `uip maestro flow node add` and `uip maestro flow node configure`.

<a id="dynamic-values-in-url--headers--body--query"></a>
## Dynamic values

Do not use `{$vars.x}` brace templates in IS activity inputs. Runtime `{...}` interpolation applies to native flow fields, not `inputs.detail.bodyParameters` on HTTP v2 or `uipath.connector.*` activities; such templates can be sent literally and cause a 400 response.

Use `=js:` expressions for dynamic URL, header, body, and query values. `$vars` is available in the JavaScript context:

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

Pass the expression string verbatim to `node configure`:

```bash
uip maestro flow node configure <Project>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "=js:`https://api.example.com/users/${$vars.userId}`"
  }' --output json
```

## Conditional branches

Use branches only to route based on response content, not to handle call failures; failures use the `error` port. Each `inputs.branches` entry creates `branch-{id}`; `$self` refers to the HTTP node output. Set branches with `node add --input`; `node configure --detail` does not accept them. Do not prefix `conditionExpression` with `=js:`; branch conditions are automatically evaluated as JS.

## Wire edges

The target port is `input`. Source ports are `default` (primary success output or fallback when no configured branch matches), `error` (network, timeout, or non-2xx failure not caught by a branch), and `branch-{id}` (one per `inputs.branches` entry).

Use `Edit` to add edge objects to `edges[]`; do not use `uip maestro flow edge add` for structural wiring. Use exact port names and this shape:

```json
{
  "id": "e-<upstreamNodeId>-<nodeId>",
  "sourceNodeId": "<upstreamNodeId>",
  "sourcePort": "<port>",
  "targetNodeId": "<nodeId>",
  "targetPort": "input"
}
```

For success and error handling:

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

Add an `error` edge only when requirements specify failure behavior. Without one, a failed call faults the flow. When an HTTP node has an outgoing `error` edge, set `inputs.errorHandlingEnabled: true`. `uip maestro flow edge add --source-port error` and `uip maestro flow format` set it automatically; direct JSON edits must set it explicitly. Never set it without an error edge: that suppresses the fault and can report a failed call as successful. See [file-format.md — Default: off](../../../shared/file-format.md#default-off--enable-only-for-a-failure-the-flow-actually-handles).

For a branch edge, use:

```json
{
  "id": "e-<nodeId>-<hasItemsDownstream>",
  "sourceNodeId": "<nodeId>",
  "sourcePort": "branch-hasItems",
  "targetNodeId": "<hasItemsDownstream>",
  "targetPort": "input"
}
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `not_authed` or 401/403 | v1 node, missing bindings, or expired connection | Verify `core.action.http.v2`, check `bindings_v2.json`, and ping the connection. |
| `configuration` field missing | Node was not configured through the CLI | Run `uip maestro flow node configure`; do not hand-write `inputs.detail`. |
| `flow validate` reports missing `uiPathActivityTypeId` on `core.action.http.v2` | Definition was hand-authored | Remove the node, run `uip maestro flow node add <file> core.action.http.v2 ...`, then run `node configure`. |
| Connection not found | Wrong connection ID or connector key | Re-run `uip is connections list` for the target connector. |
| Wrong API response | Incorrect `url` or `query` | Check the target service API documentation. |
| `ImplicitConnection` errors | Manual mode is misconfigured | Verify `authentication: "manual"` and a full URL. |
| Flow faults on 4xx/5xx | No `error` edge | This is expected when no fallback is required. Otherwise add `sourcePort: "error"` to an error-handler node. See [Implicit error port on action nodes](../../../shared/file-format.md#implicit-error-port-on-action-nodes). |
| Flow reports `Completed` although the API call failed | `inputs.errorHandlingEnabled: true` without a handler, or an error edge enters the happy path/success End node | Remove the flag without an error edge; otherwise route the error to a distinct End node with an error/status output or `core.logic.terminate`. See [Do not swallow the failure](../../../shared/file-format.md#do-not-swallow-the-failure). |
| Edge `source-port output` rejected | Variable namespace used as a port | Use `default`, `error`, or `branch-{id}`. `output` is only the variable namespace `$vars.{nodeId}.output`. |