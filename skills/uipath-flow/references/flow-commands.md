# uip flow — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--format json` for programmatic use.

## uip flow init

Scaffold a new Flow project directory. **Always create a solution first** (see Quick Start Step 2 in SKILL.md).

```bash
# 1. Create solution first
uip solution new "<SolutionName>" --format json

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

Pack a Flow project into a `.nupkg` for publishing.

```bash
uip flow pack <ProjectDir> <OutputDir>
uip flow pack <ProjectDir> <OutputDir> --version 2.0.0
uip flow pack <ProjectDir> <OutputDir> --format json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

For publishing the package to Orchestrator, see [uipath-platform](/uipath:uipath-platform).

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
uip flow registry search --filter "category=agent" --format json
uip flow registry search <keyword> --filter "category=<cat>" --format json

# Get full schema for a specific node type
uip flow registry get <nodeType> --format json
# e.g.: uip flow registry get core.action.script --format json
```

The `Data.Node` object from `registry get` is what you paste into your `.flow` file's `definitions` array.

## Integration Service commands (for connector binding and reference resolution)

When a flow uses connector nodes, you need IS commands to fetch connections and resolve reference fields. These are used in **Steps 4a–4c** of the flow authoring workflow.

### Connection commands (Step 4a — run before `registry get`)

Fetch and verify connections **before** calling `registry get`. You need the connection ID to pass `--connection-id` for enriched metadata.

```bash
# List available connections for a connector
uip is connections list "<connector-key>" --format json

# Verify a connection is healthy before binding
uip is connections ping "<connection-id>" --format json

# Create a new connection (opens browser for OAuth)
uip is connections create "<connector-key>"

# Re-authenticate an existing connection
uip is connections edit "<connection-id>"
```

### Enriched node metadata (Step 4b — registry get with connection)

With the connection ID from Step 4a, call `registry get` with `--connection-id` to get connection-aware metadata. The flow tool internally calls `getInstanceObjectMetadata` (instead of `getObjectMetadata`) which returns custom fields specific to that connection/account:

```bash
uip flow registry get <nodeType> --connection-id <connection-id> --format json
```

### Reference resolution commands (Step 4c)

When `registry get` returns fields with a `reference` object (e.g., `reference.objectName: "project"`), resolve the actual values using `uip is resources execute list`.

**Read [/uipath:uipath-platform — Integration Service — resources.md § Reference Fields (CRITICAL)](/uipath:uipath-platform) for the full resolution workflow**, including: identifying reference fields, resolving via `execute list`, inferring references from naming conventions when describe fails, and read-only field recovery.

```bash
# List values for a referenced resource (e.g., issue types, projects, users)
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<id>" --format json

# With query parameters
uip is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "projectKey=ENGCE" --format json
```

## Global options (all commands)

| Option | Description |
|--------|-------------|
| `--format json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |
| `--help` | Show command help |
