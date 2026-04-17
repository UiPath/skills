# HTTP Request Node — Implementation

## Node Type

`core.action.http.v2` (Managed HTTP Request)

> **Always use `core.action.http.v2`** for all HTTP requests. The older `core.action.http` (v1) is deprecated.

## Registry Validation

```bash
uip flow registry get core.action.http.v2 --output json
```

Confirm: input port `input`, output port `output`, model serviceType `Intsvc.UnifiedHttpRequest`.

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

### Step 4 — Wire edges

The managed HTTP node uses port `output`:

```bash
uip flow edge add <ProjectName>.flow <upstreamNodeId> <nodeId> \
  --source-port <port> --target-port input --output json

uip flow edge add <ProjectName>.flow <nodeId> <downstreamNodeId> \
  --source-port output --target-port input --output json
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `not_authed` or 401/403 | Wrong node type (v1 instead of v2), missing bindings, or expired connection | Verify node type is `core.action.http.v2`, check `bindings_v2.json` exists, ping the connection |
| `configuration` field missing | Node not configured via CLI | Run `uip flow node configure` — do not hand-write `inputs.detail` |
| Connection not found | Wrong connection ID or connector key | Re-run `uip is connections list` for the target connector |
| Wrong API response | Incorrect `url` or `query` | Check the target service's API documentation |
| `ImplicitConnection` errors | Manual mode misconfigured | Verify `authentication: "manual"` and `url` is a full URL |
