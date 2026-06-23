# HTTP Request Node — Manual Mode

Use this walkthrough when there is no IS connector for the target service, the API needs no auth (or auth you pass yourself in headers), or you are prototyping against an arbitrary REST endpoint. For connector-managed auth, use [impl-connector.md](impl-connector.md) instead.

**No connection lookup required.** Manual mode uses `ImplicitConnection` — there are no IS bindings.

Before starting, read [impl.md](impl.md) for the node type, registry validation, and the "always use `node configure`" rule. Follow Steps 1–4 in order.

## Step 1 — Add the node

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```

The CLI copies the manifest into `definitions[]`, adds the node instance, registers `variables.nodes`, and inserts a `layout.nodes` placeholder — byte-for-byte from the registry. Save the returned `<nodeId>` — Step 2 reuses it. Leave `inputs` empty; Step 2 populates `inputs.detail`. Do not hand-author the definition — see [impl.md — Add the node](impl.md#add-the-node).

## Step 2 — Configure the node

> **Find missing values first.** Before composing `url` / `query` / `body`, resolve any values the agent doesn't have (IDs from names, required body fields, response shape, …). See [/uipath:uipath-platform — http-request.md](../../../../../../uipath-platform/references/integration-service/http-request.md).

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/endpoint",
    "query": {"param1": "value1"}
  }' --output json
```

The CLI:

- Builds the full `inputs.detail` (manual auth, `ImplicitConnection`, bodyParameters, essentialConfiguration)
- Does **not** generate `bindings_v2.json` or a connection resource file — manual mode needs neither

`url` must be a full URL (scheme + host + path). For auth headers you control, pass them under `headers`:

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/me",
    "headers": {"Authorization": "=js:`Bearer ${$vars.apiToken}`"}
  }' --output json
```

**Dynamic values:** HTTP input fields do not resolve `{$vars.x}` brace-templates — use `=js:` expressions for any dynamic `url` / `headers` / `body` / `query`. Pass the `=js:` string verbatim in `--detail`. Full rationale and examples: [impl.md — Dynamic values](impl.md#dynamic-values-in-url--headers--body--query).

## Step 3 — (Optional) Response branches

Skip unless you need to route downstream paths based on response content (e.g., `items.length > 0` vs empty). For generic call-failure handling use the `error` port in Step 4 instead. Full syntax and rules: [impl.md — Conditional branches](impl.md#conditional-branches).

## Step 4 — Wire edges

The HTTP node's target port is `input`. Source ports: `default` (success), `error` (network/non-2xx), `branch-{id}` (one per Step 3 entry). Wire `default` to the next node and `error` to a handler — without an `error` edge, a failed call faults the flow.

Edge JSON shapes and all four examples (upstream→node, default→downstream, error→handler, branch→downstream): [impl.md — Wire edges](impl.md#wire-edges).

## Debug

See [impl.md — Debug](impl.md#debug). For manual mode, watch for `ImplicitConnection` errors — they signal a missing `authentication: "manual"` flag or a non-URL `url` value.
