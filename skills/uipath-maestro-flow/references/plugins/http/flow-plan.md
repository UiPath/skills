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
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.output` — `{ body, code, method, rawStringBody, request }`

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

## Registry Validation

```bash
uip flow registry get core.action.http.v2 --output json
```

Confirm: input port `input`, output port `default`, model serviceType `Intsvc.UnifiedHttpRequest`.

## Adding / Editing — Use `node configure`

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

### Step 4 — Wire edges

The managed HTTP node uses port `default`:

```bash
uip flow edge add <ProjectName>.flow <upstreamNodeId> <nodeId> \
  --source-port <port> --target-port input --output json

uip flow edge add <ProjectName>.flow <nodeId> <downstreamNodeId> \
  --source-port default --target-port input --output json
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `not_authed` or 401/403 | Wrong node type (v1 instead of v2), missing bindings, or expired connection | Verify node type is `core.action.http.v2`, check `bindings_v2.json` exists, ping the connection |
| `configuration` field missing | Node not configured via CLI | Run `uip flow node configure` — do not hand-write `inputs.detail` |
| Connection not found | Wrong connection ID or connector key | Re-run `uip is connections list` for the target connector |
| Wrong API response | Incorrect `url` or `query` | Check the target service's API documentation |
| `ImplicitConnection` errors | Manual mode misconfigured | Verify `authentication: "manual"` and `url` is a full URL |
