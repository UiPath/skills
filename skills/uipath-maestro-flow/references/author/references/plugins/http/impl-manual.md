# HTTP Request Node — Manual Mode

Use this walkthrough when no IS connector exists, the API needs no auth (or auth passed in headers), or you are prototyping against an arbitrary REST endpoint. For connector-managed auth, use [impl-connector.md](impl-connector.md).

**No connection lookup is required.** Manual mode uses `ImplicitConnection`; there are no IS bindings.

Before starting, read [impl.md](impl.md) for the node type, registry validation, and the **always use `node configure`** rule. Follow Steps 1–4 in order.

## Step 1 — Add the node

Run:

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```

> **Inside a loop body?** Add `--parent <LOOP_NODE_ID>` to set `parentId`. Without it, the node runs outside the loop context and outputs are null. See [loop/impl.md](../loop/impl.md).

Save `<nodeId>` for Step 2. Leave `inputs` empty; Step 2 populates `inputs.detail`. Do not hand-author the definition. The CLI copies the manifest byte-for-byte from the registry into `definitions[]`, adds the node instance, registers `variables.nodes`, and inserts a `layout.nodes` placeholder. See [impl.md — Add the node](impl.md#add-the-node).

## Step 2 — Configure the node

Resolve missing values before composing `url`, `query`, or `body`, including IDs from names, required body fields, and the response shape. See [/uipath:uipath-platform — http-request.md](../../../../../../uipath-platform/references/integration-service/http-request.md).

Run:

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/endpoint",
    "query": {"param1": "value1"}
  }' --output json
```

The CLI builds `inputs.detail` with manual auth, `ImplicitConnection`, `bodyParameters`, and `essentialConfiguration`. It does **not** generate `bindings_v2.json` or a connection resource file; manual mode needs neither.

Set `url` to a full URL (scheme + host + path). Pass controlled auth headers under `headers`; for example, run:

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/me",
    "headers": {"Authorization": "=js:`Bearer ${$vars.apiToken}`"}
  }' --output json
```

HTTP input fields do not resolve `{$vars.x}` brace-templates. Use `=js:` expressions for dynamic `url`, `headers`, `body`, or `query`, and pass each `=js:` string verbatim in `--detail`. See [impl.md — Dynamic values](impl.md#dynamic-values-in-url--headers--body--query).

## Step 3 — (Optional) Response branches

Skip this step unless downstream paths must be routed from response content, such as `items.length > 0` versus empty. Use the `error` port in Step 4 for generic call-failure handling. See [impl.md — Conditional branches](impl.md#conditional-branches).

## Step 4 — Wire edges

The HTTP node's target port is `input`. Source ports are `default` (success), `error` (network/non-2xx), and `branch-{id}` (one per Step 3 entry).

Wire `default` to the next node. Wire `error` to a handler **only when the requirements specify what a failed call should do**. Without an `error` edge, the call faults the flow, which is the correct default. Do not set `inputs.errorHandlingEnabled: true` without an `error` edge: that swallows the failure into a run that reports success. See [file-format.md — Default: off](../../../../shared/file-format.md#default-off--enable-only-for-a-failure-the-flow-actually-handles).

See [impl.md — Wire edges](impl.md#wire-edges) for edge JSON shapes and all four examples: upstream→node, default→downstream, error→handler, and branch→downstream.

## Debug

See [impl.md — Debug](impl.md#debug). In manual mode, watch for `ImplicitConnection` errors; they indicate a missing `authentication: "manual"` flag or a non-URL `url` value.