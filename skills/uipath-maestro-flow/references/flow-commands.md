# uip flow — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

## uip flow init

Scaffold a new Flow project directory. **Always create a solution first** (see Quick Start Step 2 in SKILL.md).

```bash
# 1. Create solution first
uip solution new "<SolutionName>" --output json

# 2. Init the flow project inside the solution folder
cd <directory>/<SolutionName> && uip flow init <ProjectName>

# 3. Register the project with the solution
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

Creates `<ProjectName>/` with `project.uiproj`, `<ProjectName>.flow`, `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json` inside the solution directory.

## uip flow validate

Validate a `.flow` file locally — no auth, no network.

```bash
uip flow validate <path/to/file.flow>
uip flow validate <path/to/file.flow> --output json
uip flow validate <path/to/file.flow> --verbose --output json
```

Checks:
- JSON parses correctly
- All required fields present (including `targetPort` on edges)
- Every node `type:typeVersion` has a matching entry in `definitions`
- Edge `sourceNodeId`/`targetNodeId` reference existing node `id`s
- Node `id`s are unique; edge `id`s are unique

Exit code 0 = valid, 1 = invalid.

## uip flow pack

Pack a Flow project into a `.nupkg` for Orchestrator deployment.

```bash
uip flow pack <ProjectDir> <OutputDir>
uip flow pack <ProjectDir> <OutputDir> --version 2.0.0
uip flow pack <ProjectDir> <OutputDir> --output json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

> **Note:** `pack` + `uip solution publish` deploys directly to Orchestrator — the user cannot visualize or edit the flow in Studio Web via this path. Only use this when the user explicitly asks to deploy to Orchestrator. The default publish path is `solution bundle` + `solution upload` (see below). See [uipath-platform](/uipath:uipath-platform) for `solution publish` commands.

## uip solution bundle

Bundle a local solution directory into a `.uis` file for upload to Studio Web.

```bash
uip solution bundle <solutionPath>
uip solution bundle <solutionPath> --output <outputDir> --name <name>
```

The `<solutionPath>` must be a directory containing a `.uipx` file. Output: a `.uis` zip file.

## uip solution upload

Upload a `.uis` solution file to Studio Web. **Requires `uip login`.**

```bash
uip solution upload <solutionFile.uis> --output json
```

Uploads the solution to Studio Web where the user can visualize, inspect, edit, and publish the flow from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, use `solution bundle` + `solution upload` to push to Studio Web. Share the resulting URL with the user.

## uip flow debug

Debug a Flow in the cloud via Studio Web + Orchestrator. **Requires `uip login`.**

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <path-to-project-dir>

# Pass input arguments to the flow
UIPCLI_LOG_LEVEL=info uip flow debug <path-to-project-dir> \
  --inputs '{"numberA": 5, "numberB": 7}'
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir. Always run `uip flow validate` first.

Use `--inputs` to pass a JSON object of input arguments when the flow has input parameters (e.g. trigger inputs or workflow arguments).

Run `uip flow debug --help` to discover additional options.

## uip flow process

Manage deployed Flow processes in Orchestrator. **Requires `uip login`.**

```bash
uip flow process list --output json
uip flow process run <process-key> <folder-key> --output json
```

Run `uip flow process --help` for all subcommands and options.

## uip flow job

Monitor Flow jobs. **Requires `uip login`.**

```bash
uip flow job status <job-key> --output json
uip flow job traces <job-key> --output json
```

## uip flow node

Add and list nodes in a `.flow` file. Automatically manages the `definitions` array.

```bash
uip flow node add <ProjectName>.flow <nodeType> --output json \
  --input '{"expression": "..."}' \
  --label "My Node" \
  --position 300,400

uip flow node list <ProjectName>.flow --output json
```

`node add` inserts the node into `nodes` and its definition into `definitions`. Use `--input` to set node-specific inputs (script body, expression, URL, etc.). After adding nodes, use `node list` to get the assigned IDs for wiring edges.

> **Shell quoting tip:** If `--input` JSON contains special characters, write it to a temp file: `uip flow node add <file> <nodeType> --input "$(cat /tmp/input.json)" --output json`

### uip flow node configure

Configure a connector node with connection details and parameter values. Run after `node add` for connector nodes. See the relevant node guide in `nodes/` for the full `--detail` JSON schema.

## uip flow edge

Add edges between nodes in a `.flow` file.

```bash
uip flow edge add <ProjectName>.flow <sourceNodeId> <targetNodeId> --output json \
  --source-port success \
  --target-port input
```

Run `uip flow node --help` or `uip flow edge --help` for all options.

## uip flow registry

Manage the local node type cache. No auth required for OOTB nodes; login for tenant-specific connector nodes.

```bash
uip flow registry pull                             # refresh local cache (expires after 30 min)
uip flow registry list --output json               # list all cached node types
uip flow registry search <keyword> --output json   # search by name, tag, or category
uip flow registry get <nodeType> --output json     # get full schema for a node type
```

The `Data.Node` object from `registry get` is what you paste into your `.flow` file's `definitions` array.

Run `uip flow registry <subcommand> --help` for additional options (e.g., `--force`, `--filter`, `--connection-id`).

## Connector commands (binding and reference resolution)

See the relevant node guide in `nodes/` for connector CLI commands and the configuration workflow.

## Global options (all commands)

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover all available options.
