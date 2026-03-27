# uip flow — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--format json` for programmatic use.

## uip flow init

Scaffold a new Flow project directory.

```bash
uip flow init <ProjectName>
uip flow init <ProjectName> --format json
```

Creates `<ProjectName>/` with `project.uiproj`, `flow_files/<ProjectName>.flow`, and `content/` files.

## uip flow validate

Validate a `.flow` file locally — no auth, no network.

```bash
uip flow validate <path/to/file.flow>
uip flow validate <path/to/file.flow> --format json
uip flow validate <path/to/file.flow> --verbose --format json
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
uip flow pack <ProjectDir> <OutputDir> --format json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

> **Note:** `pack` + `uip solution publish` deploys directly to Orchestrator — the user cannot visualize or edit the flow in Studio Web via this path. Only use this when the user explicitly asks to deploy to Orchestrator. The default publish path is `solution bundle` + `solution upload` (see below). See [uipath-platform](/uipath:uipath-platform) for `solution publish` commands.

## uip solution bundle

Bundle a local solution directory into a `.uis` file for upload to Studio Web.

```bash
uip solution bundle <solutionPath> --format json
uip solution bundle <solutionPath> --output <outputDir> --name <name> --format json
```

The `<solutionPath>` must be a directory containing a `.uipx` file. Output: a `.uis` zip file.

## uip solution upload

Upload a `.uis` solution file to Studio Web. **Requires `uip login`.**

```bash
uip solution upload <solutionFile.uis> --format json
```

Uploads the solution to Studio Web where the user can visualize, inspect, edit, and publish the flow from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, use `solution bundle` + `solution upload` to push to Studio Web. Share the resulting URL with the user.

## uip flow debug

Debug a Flow in the cloud via Studio Web + Orchestrator. **Requires `uip login`.**

```bash
uip flow debug <path/to/file.flow>
uip flow debug <path/to/file.flow> --format json
uip flow debug <path/to/file.flow> --poll-interval 2000
uip flow debug <path/to/file.flow> --folder-id <folderId>
```

What it does:
1. Converts `.flow` → BPMN XML
2. Builds `.uis` solution package
3. Uploads to Studio Web Import API
4. Triggers a debug session in Orchestrator
5. Polls for completion and streams element executions

Terminal statuses: `Completed`, `Faulted`, `Cancelled`, `Failed`

> Always run `uip flow validate` first — debug is a cloud round-trip and takes longer.

## uip flow process

Manage deployed Flow processes in Orchestrator. **Requires `uip login`.**

```bash
uip flow process list --format json
uip flow process list --folder-id <id> --format json
uip flow process get <process-key> <feed-id> --format json
uip flow process run <process-key> <folder-key> --format json
uip flow process run <process-key> <folder-key> --input '{"key":"value"}' --format json
```

## uip flow job

Monitor Flow jobs. **Requires `uip login`.**

```bash
uip flow job status <job-key> --format json
uip flow job traces <job-key> --format json
```

## uip flow registry

Manage the local node type cache. No auth required for OOTB nodes; login for tenant-specific connector nodes.

```bash
# Refresh cache from registry (expires after 30 min)
uip flow registry pull --format json
uip flow registry pull --force --format json      # force refresh regardless of TTL

# List all cached node types
uip flow registry list --format json
uip flow registry list --format yaml

# Search by keyword (matches nodeType, category, tags, label)
uip flow registry search <keyword> --format json
uip flow registry search agent --format json

# Get full schema for a specific node type
uip flow registry get <nodeType> --format json
# e.g.: uip flow registry get core.action.script --format json
```

The `Data.Node` object from `registry get` is what you paste into your `.flow` file's `definitions` array.

## Integration Service commands

For `uip is` commands (connectors, connections, activities, resources, triggers), see the **[/uipath:uipath-platform](/uipath:uipath-platform)** skill — it has the complete IS command reference and agent workflow. Use IS discovery in **Step 4** of the flow authoring workflow when your flow uses connector nodes.

## Global options (all commands)

| Option | Description |
|--------|-------------|
| `--format json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |
| `--help` | Show command help |
