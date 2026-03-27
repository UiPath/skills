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

Creates `<ProjectName>/` with `project.uiproj`, `flow_files/<ProjectName>.flow`, and `content/` files inside the solution directory.

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

Pack a Flow project into a `.nupkg` for publishing.

```bash
uip flow pack <ProjectDir> <OutputDir>
uip flow pack <ProjectDir> <OutputDir> --version 2.0.0
uip flow pack <ProjectDir> <OutputDir> --output json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

For publishing the package to Orchestrator, see [uipath-platform](/uipath:uipath-platform).

## uip flow debug

Debug a Flow in the cloud via Studio Web + Orchestrator. **Requires `uip login`.**

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <ProjectName>/
```

Uploads the project to Studio Web and triggers a debug session in Orchestrator. Always run `uip flow validate` first.

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

## Integration Service commands (for connector binding and reference resolution)

When a flow uses connector nodes, you need IS commands to fetch connections and resolve reference fields. These are used in **Steps 4a–4c** of the flow authoring workflow.

```bash
# Connections
uip is connections list "<connector-key>" --output json
uip is connections ping "<connection-id>" --output json
uip is connections create "<connector-key>"

# Enriched node metadata (pass connection for custom fields)
uip flow registry get <nodeType> --connection-id <connection-id> --output json

# Reference resolution
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json
```

Run `uip is connections --help` or `uip is resources --help` for all options.

## Global options (all commands)

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover all available options.
