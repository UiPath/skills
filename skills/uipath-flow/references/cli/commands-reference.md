# uip CLI Command Reference

All `uip` commands support `--output json|yaml|table` and `--help`. Use `--output json` on every command when parsing output programmatically.

Standard JSON response envelope:

```json
{ "Result": "Success", "Code": "<CommandCode>", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

---

## uip login

### uip login

Authenticate to UiPath Cloud. Opens a browser for interactive OAuth.

```bash
uip login
uip login --authority https://alpha.uipath.com   # non-production environments
```

Required for: `flow debug`, `flow process`, `flow job`, `solution upload`, `is connections`, `is resources`, `is connectors`, and registry access to tenant-specific connector/resource nodes.

Not required for: `flow init`, `flow validate`, `flow node add/list`, `flow edge add`, `flow registry pull/list/search/get` (OOTB nodes only), `flow pack`, `solution new`, `solution bundle`, `solution project add`.

### uip login status

Check current authentication state.

```bash
uip login status --output json
```

---

## uip flow

### uip flow init

Scaffold a new Flow project directory. Always create a solution first (see `uip solution new`).

```bash
# 1. Create solution first
uip solution new "<SOLUTION_NAME>" --output json

# 2. Init the flow project inside the solution folder
cd <DIRECTORY>/<SOLUTION_NAME> && uip flow init <PROJECT_NAME>

# 3. Register the project with the solution
uip solution project add \
  <DIRECTORY>/<SOLUTION_NAME>/<PROJECT_NAME> \
  <DIRECTORY>/<SOLUTION_NAME>/<SOLUTION_NAME>.uipx
```

Creates `<PROJECT_NAME>/` with `project.uiproj`, `<PROJECT_NAME>.flow`, `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json` inside the solution directory.

### uip flow validate

Validate a `.flow` file locally. No auth, no network.

```bash
uip flow validate <FILE_PATH> --output json
uip flow validate <FILE_PATH> --verbose --output json
```

Checks:
- JSON parses correctly
- All required fields present (including `targetPort` on edges)
- Every node `type:typeVersion` has a matching entry in `definitions`
- Edge `sourceNodeId`/`targetNodeId` reference existing node `id`s
- Node `id`s are unique; edge `id`s are unique

Exit code 0 = valid, 1 = invalid.

### uip flow debug

Debug a Flow in the cloud via Studio Web + Orchestrator. **Requires `uip login`.**

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <PROJECT_DIR>

# Pass input arguments to the flow
UIPCLI_LOG_LEVEL=info uip flow debug <PROJECT_DIR> \
  --inputs '{"numberA": 5, "numberB": 7}'
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<PROJECT_NAME>/` from the solution dir, or `.` if already inside the project dir. Always run `uip flow validate` first.

Use `--inputs` to pass a JSON object of input arguments when the flow has input parameters (trigger inputs or workflow arguments).

Run `uip flow debug --help` to discover additional options.

> **Do NOT run without explicit user consent.** Debug executes the flow for real -- sends emails, posts messages, calls APIs.

### uip flow pack

Pack a Flow project into a `.nupkg` for Orchestrator deployment.

```bash
uip flow pack <PROJECT_DIR> <OUTPUT_DIR> --output json
uip flow pack <PROJECT_DIR> <OUTPUT_DIR> --version 2.0.0 --output json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

> **Only use when the user explicitly asks to deploy to Orchestrator.** The default publish path is `solution bundle` + `solution upload` (see below).

### uip flow node add

Add a node to a `.flow` file. Automatically manages the `definitions` array.

```bash
uip flow node add <FILE_PATH> <NODE_TYPE> --output json \
  --input '{"expression": "..."}' \
  --label "My Node" \
  --position 300,400
```

| Flag | Required | Description |
|------|----------|-------------|
| `<FILE_PATH>` | Required | Path to the `.flow` file |
| `<NODE_TYPE>` | Required | Node type identifier (e.g., `core.action.script`) |
| `--output json` | Required | Structured output |
| `--input '<JSON>'` | Optional | Node-specific inputs (script body, expression, URL, etc.) |
| `--label "<LABEL>"` | Optional | Display label for the node |
| `--position x,y` | Optional | Canvas position as `x,y` coordinates |

The command inserts the node into `nodes` and its definition into `definitions`. After adding nodes, use `node list` to get the assigned IDs for wiring edges.

> **Shell quoting tip:** If `--input` JSON contains special characters (quotes, braces, `$vars`), write the JSON to a temp file: `uip flow node add <FILE_PATH> <NODE_TYPE> --input "$(cat /tmp/input.json)" --output json`

### uip flow node list

List all nodes in a `.flow` file with their assigned IDs.

```bash
uip flow node list <FILE_PATH> --output json
```

Use after `node add` to discover assigned node IDs for wiring edges.

### uip flow node configure

Configure a connector node with connection details and parameter values. Run after `node add` for connector nodes.

```bash
uip flow node configure <FILE_PATH> <NODE_ID> \
  --detail '{"connectionId": "<ID>", "folderKey": "<KEY>", "method": "POST", "endpoint": "/issues", "bodyParameters": {"field": "value"}}'
```

| Flag | Required | Description |
|------|----------|-------------|
| `<FILE_PATH>` | Required | Path to the `.flow` file |
| `<NODE_ID>` | Required | ID of the connector node to configure |
| `--detail '<JSON>'` | Required | Configuration JSON (see below) |

The `--detail` JSON structure:

| Field | Description |
|-------|-------------|
| `connectionId` | The bound IS connection UUID |
| `folderKey` | The Orchestrator folder key |
| `method` | HTTP method from `connectorMethodInfo` (e.g., `POST`) |
| `endpoint` | API path from `connectorMethodInfo` (e.g., `/issues`) |
| `bodyParameters` | Field-value pairs for the request body |
| `queryParameters` | Field-value pairs for query string parameters |

The command populates `inputs.detail` and creates workflow-level `bindings` entries. Use **resolved IDs**, not display names.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip flow node configure <FILE_PATH> <NODE_ID> --detail "$(cat /tmp/detail.json)"`

### uip flow edge add

Add an edge between two nodes in a `.flow` file.

```bash
uip flow edge add <FILE_PATH> <SOURCE_NODE_ID> <TARGET_NODE_ID> --output json \
  --source-port success \
  --target-port input
```

| Flag | Required | Description |
|------|----------|-------------|
| `<FILE_PATH>` | Required | Path to the `.flow` file |
| `<SOURCE_NODE_ID>` | Required | ID of the source node |
| `<TARGET_NODE_ID>` | Required | ID of the target node |
| `--source-port <PORT>` | Required | Source handle ID (e.g., `success`, `output`, `true`) |
| `--target-port <PORT>` | Required | Target handle ID (e.g., `input`, `loopBack`) |
| `--output json` | Required | Structured output |

Run `uip flow edge --help` for additional options.

### uip flow registry pull

Refresh the local node type cache. Cache expires after 30 minutes.

```bash
uip flow registry pull
uip flow registry pull --force
```

Without `uip login`, the registry shows OOTB nodes only. After login, tenant-specific connector and resource nodes are also available.

### uip flow registry list

List all cached node types.

```bash
uip flow registry list --output json
```

### uip flow registry search

Search the registry by name, tag, or category.

```bash
uip flow registry search <KEYWORD> --output json
```

Run `uip flow registry search --help` for filter options.

### uip flow registry get

Get the full schema for a specific node type.

```bash
uip flow registry get <NODE_TYPE> --output json

# With connection for enriched metadata (connector nodes)
uip flow registry get <NODE_TYPE> --connection-id <CONNECTION_ID> --output json
```

The `Data.Node` object from the response is what goes into the `.flow` file's `definitions` array. For connector nodes, pass `--connection-id` to get connection-aware field metadata including custom fields, dynamic enums, and reference resolution info.

> **Phase 1 planning: do NOT call `registry get`.** Use `registry search`/`list` for discovery. Save `registry get` for Phase 2 implementation resolution.

### uip flow process list

List deployed Flow processes in Orchestrator. **Requires `uip login`.**

```bash
uip flow process list --output json
```

### uip flow process run

Run a deployed Flow process. **Requires `uip login`.**

```bash
uip flow process run <PROCESS_KEY> <FOLDER_KEY> --output json
```

Run `uip flow process --help` for all subcommands and options.

### uip flow job status

Get the status of a running Flow job. **Requires `uip login`.**

```bash
uip flow job status <JOB_KEY> --output json
```

### uip flow job traces

Get execution traces for a Flow job. **Requires `uip login`.**

```bash
uip flow job traces <JOB_KEY> --output json
```

---

## uip solution

### uip solution new

Create a new solution directory with a `.uipx` manifest.

```bash
uip solution new "<SOLUTION_NAME>" --output json
```

### uip solution project add

Register a project with a solution.

```bash
uip solution project add <PROJECT_DIR> <SOLUTION_FILE.uipx>
```

### uip solution bundle

Bundle a local solution directory into a `.uis` file for upload to Studio Web.

```bash
uip solution bundle <SOLUTION_PATH>
uip solution bundle <SOLUTION_PATH> --output <OUTPUT_DIR> --name <NAME>
```

The `<SOLUTION_PATH>` must be a directory containing a `.uipx` file. Output: a `.uis` zip file.

### uip solution upload

Upload a `.uis` solution file to Studio Web. **Requires `uip login`.**

```bash
uip solution upload <SOLUTION_FILE.uis> --output json
```

Uploads the solution to Studio Web where the user can visualize, inspect, edit, and publish the flow from the browser. Share the resulting URL with the user.

> **This is the default publish path.** When the user asks to "publish" without specifying where, use `solution bundle` + `solution upload` to push to Studio Web.

---

## uip is (Integration Service)

### uip is connectors list

List all available connectors in the tenant.

```bash
uip is connectors list --output json
```

Useful when a connector key fails or to discover available integrations.

### uip is connections list

List connections for a specific connector. **Requires `uip login`.**

```bash
uip is connections list "<CONNECTOR_KEY>" --output json
uip is connections list "<CONNECTOR_KEY>" --folder-key "<FOLDER_KEY>" --output json
```

Pick the default enabled connection (`IsDefault: Yes`, `State: Enabled`). The `--folder-key` parameter specifies which Orchestrator folder to list connections in. If omitted, defaults to UiPath's Personal Workspace folder.

### uip is connections ping

Verify that a connection is healthy. **Requires `uip login`.**

```bash
uip is connections ping "<CONNECTION_ID>" --output json
```

### uip is connections create

Create a new connection for a connector (interactive). **Requires `uip login`.**

```bash
uip is connections create "<CONNECTOR_KEY>"
```

### uip is resources describe

Fetch and cache full operation metadata for a connector resource. **Requires `uip login`.**

```bash
uip is resources describe "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" --operation Create --output json
```

The response includes a `metadataFile` path. Read that file for complete field details including descriptions, types, references, and query/path parameters.

### uip is resources execute list

Resolve reference fields by listing live data from a connector. **Requires `uip login`.**

```bash
uip is resources execute list "<CONNECTOR_KEY>" "<RESOURCE>" \
  --connection-id "<CONNECTION_ID>" --output json
```

Use resolved IDs (not display names) in the flow's node inputs.

Run `uip is connections --help` or `uip is resources --help` for all options.

---

## Global Options

All `uip` commands support:

| Flag | Description |
|------|-------------|
| `--output json\|yaml\|table` | Output format (always use `json` for programmatic use) |
| `--help` | Show all available options for the command |

The `--localstorage-file` warning in some environments is benign and can be ignored.
