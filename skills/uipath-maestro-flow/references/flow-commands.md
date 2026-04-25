# uip maestro flow — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

> For node and edge commands (`node add/delete/list/configure`, `edge add/delete/list`), see [flow-editing-operations-cli.md](flow-editing-operations-cli.md). This file covers project setup, validation, registry, debug, and publishing commands.

## uip maestro flow init

Scaffold a new Flow project directory. **Always create a solution first** (see Quick Start Step 2 in SKILL.md).

```bash
# 1. Create solution first
uip solution new "<SolutionName>" --output json

# 2. Init the flow project inside the solution folder
cd <directory>/<SolutionName> && uip maestro flow init <ProjectName>

# 3. Register the project with the solution
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

Creates `<ProjectName>/` with `project.uiproj`, `<ProjectName>.flow`, `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json` inside the solution directory.

## uip maestro flow validate

Validate a `.flow` file locally — no auth, no network.

```bash
uip maestro flow validate <path/to/file.flow>
uip maestro flow validate <path/to/file.flow> --output json
uip maestro flow validate <path/to/file.flow> --verbose --output json
```

Checks:

- JSON parses correctly
- All required fields present (including `targetPort` on edges)
- Every node `type:typeVersion` has a matching entry in `definitions`
- Edge `sourceNodeId`/`targetNodeId` reference existing node `id`s
- Node `id`s are unique; edge `id`s are unique

Exit code 0 = valid, 1 = invalid.

## uip maestro flow tidy

Auto-layout nodes in the `.flow` file. Run after validation passes and before publishing or debugging — without tidy, hand-written or stale `layout` data can render as misshapen rectangles in Studio Web.

```bash
uip maestro flow tidy <path/to/file.flow>
uip maestro flow tidy <path/to/file.flow> --output json
```

Tidy:
- Arranges nodes horizontally (left-to-right) and anchors to the leftmost node's original position so the user's general layout intent is preserved
- Sets every non-`stickyNote` node's `size` to `{ "width": 96, "height": 96 }` — preserving sticky-note custom sizes
- Recurses into subflows and rewrites `subflows[<id>].layout` for each
- Backfills missing `position`/`size` entries
- Does not modify node logic, edges, definitions, or variables — only layout coordinates

JSON output (`--output json`) reports counts in `Data`: `NodesTotal`, `EdgesTotal`, `NodesRepositioned`, `NodesResized`, `SubflowsTidied`.

## uip maestro flow pack

Pack a Flow project into a `.nupkg` for Orchestrator deployment.

```bash
uip maestro flow pack <ProjectDir> <OutputDir>
uip maestro flow pack <ProjectDir> <OutputDir> --version 2.0.0
uip maestro flow pack <ProjectDir> <OutputDir> --output json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

> **Note:** `pack` + `uip solution publish` deploys directly to Orchestrator — the user cannot visualize or edit the flow in Studio Web via this path. Only use this when the user explicitly asks to deploy to Orchestrator. The default publish path is `uip solution upload` (see below). See [uipath-platform](/uipath:uipath-platform) for `solution publish` commands.

## uip solution resource refresh

Re-scan all projects in the solution and sync resource declarations (connections, processes, queues, etc.) from their `bindings_v2.json` files. Creates new resources for bindings not yet in the solution, imports from Orchestrator when a matching resource exists. **Always run this before `uip solution upload` or `uip maestro flow debug`.**

```bash
uip solution resource refresh <SolutionDir> --output json
```

The argument is the solution directory (containing the `.uipx` file). Defaults to the current directory if omitted.

## uip solution upload

Upload a solution directly to Studio Web. **Requires `uip login`.**

```bash
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory (the folder containing the `.uipx` file) directly — no intermediate bundling step is required. Uploads the solution to Studio Web where the user can visualize, inspect, edit, and publish the flow from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, run `uip solution upload <SolutionDir>` to push to Studio Web. Share the resulting URL with the user.

## uip maestro flow debug

Debug a Flow in the cloud via Studio Web + Orchestrator. **Requires `uip login`.**

```bash
UIPCLI_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json

# Pass input arguments to the flow
UIPCLI_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir. Always run `uip maestro flow validate` first.

Use `--inputs` to pass a JSON object of input arguments when the flow has input parameters (e.g. trigger inputs or workflow arguments).

Run `uip maestro flow debug --help` to discover additional options.

### Reporting the run back to the user

The CLI response includes a **Studio Web URL** (where the user can inspect the run) and an **instanceId** (for log/trace correlation). Parse both from the JSON output — typically `Data.studioWebUrl` and `Data.instanceId` — and **always show them as the first two lines of the summary** you report back to the user:

```
Studio Web URL: <url>
Instance ID: <instanceId>

<run status, node traces, errors, etc.>
```

If either value is not present in the response, emit the label with `<not returned by CLI>` rather than dropping the line. Do not bury these values below the run summary — the user should see them immediately without scrolling.

## uip maestro flow process

Manage deployed Flow processes in Orchestrator. **Requires `uip login`.**

```bash
uip maestro flow process list --output json
uip maestro flow process run <process-key> <folder-key> --output json
```

Run `uip maestro flow process --help` for all subcommands and options.

## uip maestro flow job

Monitor Flow jobs. **Requires `uip login`.**

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

## uip maestro flow node / uip maestro flow edge

See [flow-editing-operations-cli.md](flow-editing-operations-cli.md) for complete `node add/delete/list/configure` and `edge add/delete/list` syntax, flags, and auto-managed behaviors.

## uip maestro flow registry

Manage the local node type cache. No auth required for OOTB nodes; login for tenant-specific connector nodes.

```bash
uip maestro flow registry pull                             # refresh local cache (expires after 30 min)
uip maestro flow registry list --output json               # list all cached node types
uip maestro flow registry search <keyword> --output json   # search by name, tag, or category
uip maestro flow registry get <nodeType> --output json     # get full schema for a node type
```

The `Data.Node` object from `registry get` is what you paste into your `.flow` file's `definitions` array.

Run `uip maestro flow registry <subcommand> --help` for additional options (e.g., `--force`, `--filter`, `--connection-id`).

## Connector commands (binding and reference resolution)

See the relevant node guide in `nodes/` for connector CLI commands and the configuration workflow.

## Global options (all commands)

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover all available options.
