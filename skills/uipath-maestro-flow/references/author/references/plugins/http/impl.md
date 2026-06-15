# HTTP Request Node — Implementation

## Node Type

`core.action.http.v2` (Managed HTTP Request)

> **Always use `core.action.http.v2`** for all HTTP requests. The older `core.action.http` (v1) is deprecated.

## Pre-flight: Vendor detection — pick the right mode BEFORE configuring

The prompt's vendor name decides `authentication` mode and which connector you wire. Get this wrong and the flow runs with hardcoded URLs + placeholder auth tokens that fail at runtime.

| Prompt mentions … | Mode | `targetConnector` | Source of URL + body shape |
|---|---|---|---|
| A specific SaaS vendor by name (slack, jira, outlook, gmail, salesforce, servicenow, hubspot, …) | **Connector** | The vendor's IS connector key (e.g. `uipath-salesforce-slack`, `uipath-atlassian-jira`, `uipath-microsoft-outlook365`) | StandardResource cache — see [sr-cache-authoring.md](sr-cache-authoring.md) |
| A public unauthenticated API or no-vendor URL the user pasted | **Manual** | (none — `ImplicitConnection`) | The pasted URL, agent-authored body |
| The user says "use the HTTP connector" / `uipath-uipath-http` explicitly | **Connector** | `uipath-uipath-http` | A real `uipath-uipath-http` connection's base URL |

**Default is connector mode.** Switch to manual ONLY when there is no IS connector for the vendor OR the user explicitly asked for manual.

The phrase "using http request activity" in the prompt names the NODE TYPE (`core.action.http.v2`), NOT the mode. It does NOT mean "use manual mode". Keep connector mode unless the vendor recognition table sends you elsewhere.

### Anti-pattern — what the wrong path looks like

This is the failure mode this skill exists to prevent. Do not produce flows shaped like:

```jsonc
// WRONG — manual mode for a vendor that has an IS connector
{
  "detail": {
    "connector": "uipath-uipath-http",           // generic, not the vendor's connector
    "connectionId": "ImplicitConnection",
    "bodyParameters": {
      "authentication": "manual",
      "url": "https://slack.com/api/chat.postMessage",   // vendor URL hardcoded
      "headers": { "Authorization": "Bearer <SLACK_BOT_TOKEN>" }, // placeholder token
      "body": { "channel": "#order-ops", "text": "Hello" }
    }
  }
}
```

Why it fails: `<SLACK_BOT_TOKEN>` is a literal string at runtime. Slack rejects. The flow never works without the user editing the file by hand to paste a real token, which defeats the connector model.

Correct shape for the same intent — connector mode + the Slack IS connection:

```jsonc
{
  "detail": {
    "authentication": "connector",
    "targetConnector": "uipath-salesforce-slack",
    "connectionId": "<real-slack-connection-id>",
    "folderKey": "<folder-key>",
    "method": "POST",
    "url": "/chat.postMessage",                 // RELATIVE — connector prepends base URL
    "body": { "channel": "<resolved-channel-id>", "text": "Hello" }
  }
}
```

Read URL + body shape + reference resolution rules from `uip is resources sr <connector> <object>` after running `uip is resources standardize` once. Full loop in [sr-cache-authoring.md](sr-cache-authoring.md).

### Anti-pattern — running `node configure` with an empty SR cache

```bash
# WRONG — skipping the SR cache loop and jumping straight to node configure
uip maestro flow node add <ProjectName>.flow core.action.http.v2 --label "Send Slack"
uip maestro flow node configure <ProjectName>.flow <id> --detail '{"authentication":"connector",...}'
# Cache for (connector, connection, object) is empty.
# The HTTP node WORKS at runtime — the connection proxy calls the vendor with whatever
# request shape the agent typed by hand into --detail.
# But the eventual `custom-{org}-{vendor}` connector built by the POC publish loop has
# NO response field metadata and is missing whatever request fields the agent omitted.
# This breaks the POC's "publish once, reuse everywhere" value proposition.
```

Why it fails: the publish-time pipeline reads from the SR cache, not from the .flow file. The flow node's `--detail` is the runtime payload — it has no response-shape information, and any request fields the agent didn't explicitly type are lost. The cache is the place where both request + response field metadata lives. An empty cache at publish time is an unrecoverable defect — the published connector has the wrong contract and consumers depending on it will see missing fields.

Correct sequence (mandatory per [SKILL.md Critical Rule #3 — POC override](../../../../../SKILL.md)):

```bash
# 1. Cache check first
uip is resources sr "<targetConnector>" "<object>" --connection-id "<id>" --output json

# 2. Cache miss → WebFetch vendor docs, build SR JSON with request + response
#    fields per the 10-field budget (see sr-cache-authoring.md)
# 3. Persist
uip is resources standardize "<targetConnector>" "<object>" --connection-id "<id>" \
  --from-sr /tmp/<vendor>.sr.json --output json

# 4. THEN configure the HTTP node
uip maestro flow node configure <ProjectName>.flow <id> --detail '{...}'
```

The agent does NOT call `node configure` for an HTTP node until step 1 returns a cache hit (either pre-existing or just-populated via step 3). No exceptions.

## Registry validation

```bash
uip maestro flow registry get core.action.http.v2 --output json
```

Confirm in `Data.Node.handleConfiguration`: target port `input`, source ports `branch-{item.id}` (dynamic, `repeat: inputs.branches`) and `default`. Also confirm `Data.Node.supportsErrorHandling: true` — HTTP v2 participates in the implicit `error` port pattern shared by every action node (see [Action Node Structure](../../../../shared/action-nodes.md)). Model `serviceType` is `Intsvc.UnifiedHttpRequest`.

## Critical: Use `node configure`

> **Do not hand-write `inputs.detail`, `bindings_v2.json`, or connection resource files.** Run `uip maestro flow node configure` — it builds everything from a simple `--detail` JSON. Hand-written configurations miss the `essentialConfiguration` block and fail at runtime. `core.action.http.v2` is CLI-owned per [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node) (same envelope rules as connector activities).

## Configuration Workflow

### Step 1 — Add the node

Use `Edit` / `Write` to add the `core.action.http.v2` node directly to the `.flow` file. Follow [Edit/Write: Add a node](../../editing-operations-json.md#add-a-node): copy the registry definition into `definitions[]`, add the node instance to `nodes[]`, add `variables.nodes`, and add a placeholder `layout.nodes` entry. Save the node ID for Step 3.

For the node instance shape, follow the [Action Node Structure — Standard JSON skeleton](../../../../shared/action-nodes.md#standard-json-skeleton) with `type: "core.action.http.v2"` and `typeVersion` set to the `version` field from the `registry get core.action.http.v2` response above (do not hardcode it — this node has advanced past `2.0`). Leave `inputs` empty at this stage — Step 3 populates `inputs.detail` via `uip maestro flow node configure`.

### Step 2 — Identify target connector and connection (connector mode only)

Skip this step for manual mode.

Discovery call is **always**:

```bash
uip is connections list "<target-connector-key>" --all-folders --output json
```

`--all-folders` is mandatory. Without it the CLI returns the active folder only and hides connections in other folders the user can see. Plain `uip is connections list "<target-connector-key>"` is forbidden for discovery.

> **MUST READ before any `uip is connections ...` call:** [/uipath:uipath-platform — connections.md](../../../../../../uipath-platform/references/integration-service/connections.md). Single source of truth for selection rules, empty-result recovery, ping verification.

Record the chosen connection's `Id` and `FolderKey` for Step 3.

> **HTTP-specific recovery — no usable connection.** If platform-skill recovery yields nothing (empty after `--all-folders` + `--refresh`, user declines to create one), the HTTP node has unique fallback options. **STOP** and use `AskUserQuestion`: **Create a new connection now** (`uip is connections create "<target-connector-key>"` starts the OAuth flow — user completes browser auth, then re-run list) / **Switch this node to manual mode** / **Skip this node** / **Something else**. Do not fall back to manual mode silently, do not invent a placeholder ID, do not skip the node without explicit user selection. See the AskUserQuestion dropdown rule in [SKILL.md](../../../../../SKILL.md).

### Step 2.5 — Populate the SR cache (mandatory before Step 3)

**Hard stop.** Do NOT proceed to Step 3 (`node configure`) until the SR cache holds an entry for this `(targetConnector, connectionId, object)` triple containing **both request and response fields**. The cache is the source of truth the publish-time pipeline reads from when promoting the HTTP node into a `custom-{org}-{vendor}` connector. Skipping this step leaves the published connector with input-only schemas (no documented response shape), forcing a second rebuild later.

Run the cache loop per [sr-cache-authoring.md — Lazy cache loop](sr-cache-authoring.md#lazy-cache-loop):

```bash
KEY="<targetConnector>"          # uipath-uipath-http for generic-proxy connections
OBJ="<operation-slug>"           # e.g. list_inbox_emails, create_lead, post_message
CID="<connection-id>"

uip is resources sr "$KEY" "$OBJ" --connection-id "$CID" --output json
# Cache hit → done. Proceed to Step 3.
# Cache miss → build the SR (WebFetch docs, capture request + response fields per
#              the 10-field budget heuristic), then:
# uip is resources standardize "$KEY" "$OBJ" --connection-id "$CID" --from-sr /tmp/<vendor>.sr.json
# uip is resources sr "$KEY" "$OBJ" --connection-id "$CID" --output json  # confirm hit
```

The SR's `elementKey` MUST be set to the design-side key for the eventual custom connector — `design-{org}-{vendor}` (e.g. `design-acmecorp-outlook`), NOT `uipath-uipath-http`. The agent derives the vendor identity from the connection's name / base URL during this step; that same identity becomes the published `custom-{org}-{vendor}` key after publish. See [sr-cache-authoring.md — Build an SR on cache miss](sr-cache-authoring.md#build-an-sr-on-cache-miss) for the full SR JSON shape including the response-field budget heuristic.

### Step 3 — Configure the node

> **Step 2.5 must be green before this step runs.** `node configure` reads request shape from the cached SR (via the user's `--detail`); the response shape lives in the cache for the publish-time pipeline. Running Step 3 with an empty cache works at runtime (the connection proxy doesn't care) but breaks the POC's connector-publish loop — the resulting `custom-*` connector has no documented response fields. There is no recovery path other than rebuilding the cache and re-publishing the connector.

**Connector mode** (IS connection auth):

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

**Manual mode** (no connector auth):

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "https://api.example.com/endpoint",
    "query": {"param1": "value1"}
  }' --output json
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

When calling `uip maestro flow node configure --detail`, pass the `=js:` string verbatim — the CLI stores it in `inputs.detail.bodyParameters` unchanged:

```bash
uip maestro flow node configure <Project>.flow <nodeId> \
  --detail '{
    "authentication": "manual",
    "method": "GET",
    "url": "=js:`https://api.example.com/users/${$vars.userId}`"
  }' --output json
```

### Step 4 — (Optional) Configure response branches for content-based routing

Skip this step unless you need to route downstream paths based on the *response content* (e.g., `items.length > 0` vs empty). Do **not** use `branches` just to handle call failures — for that, use the `error` port (Step 5).

Each branch entry creates a `branch-{id}` source port. `$self` refers to the current HTTP node's output inside the condition.

```bash
uip maestro flow node configure <ProjectName>.flow <nodeId> \
  --detail '{
    "branches": [
      { "id": "hasItems",  "name": "Has Items",  "conditionExpression": "$self.output.body.items.length > 0" },
      { "id": "empty",     "name": "Empty",      "conditionExpression": "$self.output.body.items.length == 0" }
    ]
  }' --output json
```

> **Do not prefix `conditionExpression` with `=js:`** — HTTP branch conditions are auto-evaluated as JS (same rule as decision/switch expressions).

### Step 5 — Wire edges

The managed HTTP node's target port is `input`. Its source ports are:

- `default` — primary success output (or fallback when configured branches don't match)
- `error` — fires when the HTTP call fails (network error, timeout, non-2xx not caught by a branch); wire this to an error handler to keep the flow from faulting
- `branch-{id}` — one per entry in `inputs.branches` (Step 4); use the exact `id` you set

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

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `not_authed` or 401/403 | Wrong node type (v1 instead of v2), missing bindings, or expired connection | Verify node type is `core.action.http.v2`, check `bindings_v2.json` exists, ping the connection |
| `configuration` field missing | Node not configured via CLI | Run `uip maestro flow node configure` — do not hand-write `inputs.detail` |
| Connection not found | Wrong connection ID or connector key | Re-run `uip is connections list` for the target connector |
| Wrong API response | Incorrect `url` or `query` | Check the target service's API documentation |
| `ImplicitConnection` errors | Manual mode misconfigured | Verify `authentication: "manual"` and `url` is a full URL |
| Flow faults on 4xx/5xx response | No `error` edge wired from the HTTP node | Add an edge with `sourcePort: "error"` to an error-handler node. See [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes) — same mechanism applies to all action nodes |
| Edge `source-port output` rejected | Referencing the variable namespace as a port name | HTTP source ports are `default`, `error`, and `branch-{id}` — not `output`. The `output` name is only a variable namespace (`$vars.{nodeId}.output`) |
