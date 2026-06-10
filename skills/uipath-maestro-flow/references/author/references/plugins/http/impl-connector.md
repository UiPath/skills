# HTTP Request Node — Connector Mode

Use this walkthrough when the target service has an IS connector and you want managed auth (OAuth / API key) handled by an existing IS connection.

**Prerequisite:** a healthy IS connection for the target connector. Step 2 verifies this. If none exists, propose manual mode as the fallback and confirm the switch with the user via `AskUserQuestion` before finalizing — do not switch modes without that confirmation.

Before starting, read [impl.md](impl.md) for the node type, registry validation, and the "always use `node configure`" rule. Follow Steps 1–5 in order.

## Step 1 — Add the node

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```

The CLI copies the manifest into `definitions[]`, adds the node instance, registers `variables.nodes`, and inserts a `layout.nodes` placeholder — byte-for-byte from the registry. Save the returned `<nodeId>` — Steps 2 and 3 reuse it. Leave `inputs` empty; Step 3 populates `inputs.detail`. Do not hand-author the definition — see [impl.md — Add the node](impl.md#add-the-node).

## Step 2 — Identify target connection

**Connector mode only works if the connector supports the HTTP request activity** — verify by running `uip is connectors get "<target-connector-key>"` and checking the `HasHttpRequest` flag. If the flag is false, **STOP** — a connection cannot help. Use the recovery `AskUserQuestion` below (switch to manual mode / skip / something else; the create-a-connection option does not apply) and do not switch modes without confirmation.

```bash
uip is connections list "<target-connector-key>" --all-folders --output json
```

`--all-folders` is mandatory for discovery. Selection rules, empty-result recovery, and ping verification live in the platform skill — do not duplicate them here.

> **MUST READ before any `uip is connections ...` call:** [/uipath:uipath-platform — connections.md](../../../../../../uipath-platform/references/integration-service/connections.md).

Record the chosen connection's `Id` and `FolderKey` — Step 3 needs both.

> **HTTP-specific recovery — no usable connection.** If platform-skill recovery yields nothing (empty after `--all-folders` + `--refresh`, user declines to create one), the HTTP node has unique fallback options. Use `AskUserQuestion` to confirm the path — **manual mode is the recommended auto-fallback**, pre-selected, since it unblocks the node without a connection:
>
> - **Switch this node to manual mode** *(recommended)* — abandon this walkthrough and follow [impl-manual.md](impl-manual.md). Manual changes the auth model (you supply auth yourself), so this needs explicit confirmation.
> - **Create a new connection now** — `uip is connections create "<target-connector-key>"` starts the OAuth flow. User completes browser auth themselves, then re-run `uip is connections list` to pick up the new connection.
> - **Skip this node**.
> - **Something else**.
>
> Auto-try the fallback, but do not finalize a mode switch without the user's confirmation; do not invent a placeholder ID; do not skip the node without explicit selection. See the `AskUserQuestion` dropdown rule in [SKILL.md](../../../../../SKILL.md).

## Step 3 — Configure the node

> **Find missing values first.** Before composing `url` / `query` / `body`, resolve any values the agent doesn't have (IDs from names, required body fields, response shape, …). See [/uipath:uipath-platform — http-request.md](../../../../../../uipath-platform/references/integration-service/http-request.md).

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "connector",
    "targetConnector": "<target-connector-key>",
    "connectionId": "<target-connection-id>",
    "folderKey": "<folder-key>",
    "method": "GET",
    "url": "/api/endpoint",
    "query": {"param1": "value1"}
  }' --output json
```

> **Connector mode supports `application/json` request and response bodies only.**

The CLI:

- Builds the full `inputs.detail` (connector, connectionId, bodyParameters, essentialConfiguration)
- Auto-fills both `bodyParameters.path` and `bodyParameters.url` from the single `url` value you pass
- Generates `bindings_v2.json`
- Creates a connection resource file under `resources/solution_folder/connection/`

**Dynamic values:** connector input fields do not resolve `{$vars.x}` brace-templates — use `=js:` expressions for any dynamic `url` / `headers` / `body` / `query`. Pass the `=js:` string verbatim in `--detail`. Full rationale and examples: [impl.md — Dynamic values](impl.md#dynamic-values-in-url--headers--body--query).

## Step 4 — (Optional) Response branches

Skip unless you need to route downstream paths based on response content (e.g., `items.length > 0` vs empty). For generic call-failure handling use the `error` port in Step 5 instead. Full syntax and rules: [impl.md — Conditional branches](impl.md#conditional-branches).

## Step 5 — Wire edges

The HTTP node's target port is `input`. Source ports: `default` (success), `error` (network/non-2xx), `branch-{id}` (one per Step 4 entry). Wire `default` to the next node and `error` to a handler — without an `error` edge, a failed call faults the flow.

Edge JSON shapes and all four examples (upstream→node, default→downstream, error→handler, branch→downstream): [impl.md — Wire edges](impl.md#wire-edges).

## Debug

See [impl.md — Debug](impl.md#debug). For connector mode, the most common errors are `not_authed` / 401/403 (expired connection — ping it) and `Connection not found` (wrong connector key or connection ID — re-list).
