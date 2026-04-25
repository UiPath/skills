# uip maestro case — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

---

## uip maestro case init

Scaffold a new Case project with boilerplate files.

```bash
uip maestro case init <name>
uip maestro case init my-case-project
uip maestro case init my-case-project --force
```

| Flag | Description |
|------|-------------|
| `<name>` | **(required)** Project name (letters, numbers, `_`, `-` only) |
| `--force` | Overwrite existing directory (does not clear existing files) |

Creates 5 files flat under `<name>/` (no `content/` subdirectory on disk): `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`. No `.bpmn` is emitted at init time — downstream tooling (`validate` / `pack` / `publish`) generates `caseplan.json.bpmn` later. The `content/` prefix in `package-descriptor.json.files` describes the packed `.nupkg` layout, not the on-disk layout.

> **Note.** This skill does NOT invoke `uip maestro case init` — the case plugin writes the 5 scaffold files directly. See [plugins/case/impl-json.md § Scaffold](plugins/case/impl-json.md) for the direct-write recipe. `init` is documented here for completeness of the `uip maestro case` surface.

---

## uip maestro case pack

Pack a Case project directory into a `.nupkg` file.

```bash
uip maestro case pack <projectPath> <outputPath>
uip maestro case pack ./my-case-project ./dist
uip maestro case pack ./my-case-project ./dist --name MyCase --version 2.0.0
```

| Flag | Description |
|------|-------------|
| `<projectPath>` | **(required)** Path to the Case project directory |
| `<outputPath>` | **(required)** Output directory for the `.nupkg` |
| `-n, --name <name>` | Package name (default: project folder name) |
| `-v, --version <version>` | Package version (default: `1.0.0`) |

---

> **Note:** `pack` + `uip solution publish` deploys directly to Orchestrator — the user cannot visualize or edit the case in Studio Web via this path. Only use this when the user explicitly asks to deploy to Orchestrator. The default publish path is `uip solution upload` (see below). See [uipath-platform](/uipath:uipath-platform) for `solution publish` commands.

## uip solution resource refresh

Re-scan all projects in the solution and sync resource declarations from their `bindings_v2.json` files. Creates new resources for bindings not yet in the solution, imports from Orchestrator when a matching resource exists.

```bash
uip solution resource refresh <SolutionDir> --output json
```

| Flag | Description |
|------|-------------|
| `<SolutionDir>` | Path to the solution directory (containing `.uipx`) |

**Always run before `uip solution upload` or `uip maestro case debug`** when the case uses connector tasks. Without this step, connection resources may not be registered on Studio Web ("Resource is not configured" warning).

> **Requires `bindings_v2.json` to be populated.** Connector plugins regenerate this file after writing root bindings (see [bindings-v2-sync.md](bindings-v2-sync.md)). If `bindings_v2.json` is still the empty scaffold (`resources: []`), no connection resources will be synced.

## uip solution upload

Upload a solution directly to Studio Web. **Requires `uip login`.**

```bash
uip solution resource refresh <SolutionDir> --output json
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory (the folder containing the `.uipx` file) directly — no intermediate bundling step is required. Uploads the solution to Studio Web where the user can visualize, inspect, edit, and publish the case from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, run `uip solution resource refresh` then `uip solution upload <SolutionDir>` to push to Studio Web. Share the resulting URL with the user.

## uip maestro case debug

Debug a Case JSON file via a Studio Web debug session. **Requires `uip login`.**

```bash
uip solution resource refresh <SolutionDir> --output json
uip maestro case debug <projectDirectory>
uip maestro case debug ./mySolution/myProject
uip maestro case debug ./mySolution/myProject --folder-id 42 --poll-interval 3000
```

> **Always run `uip solution resource refresh`** on the solution directory before debug when the case uses connector tasks.

| Flag | Description |
|------|-------------|
| `<projectDirectory>` | **(required)** Path to the case project directory (must contain `project.uiproj`) |
| `--folder-id <id>` | Orchestrator folder ID (`OrganizationUnitId`). Auto-detected if omitted. |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` (default: `json`) |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

---

## uip maestro case validate

Validate a case management JSON file against case management rules.

```bash
uip maestro case validate <file>
uip maestro case validate case.json
```

| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |

Output: `{ File, Status: "Valid" }` on success. Errors and warnings are reported inline.

---

## uip maestro case tasks

Skill uses only `tasks describe` (schema discovery for binding) and `tasks enrich` (populate task input/output shape). Mutation sub-commands (`add`, `add-connector`, `edit`, `get`, `remove`) are not used — the plugin JSON recipes write tasks directly to `caseplan.json`.

```bash
# Enrich a task with input/output schemas from the API
uip maestro case tasks enrich --type <type> --id <id>
uip maestro case tasks enrich --type process --id <entityKey>
uip maestro case tasks enrich --type agent --id <entityKey> --element-id <elementId>

# Describe a task type's input/output metadata (for binding discovery)
uip maestro case tasks describe --type <type> --id <id>
uip maestro case tasks describe --type process --id <entityKey>
uip maestro case tasks describe --type connector-activity --id <typeId> --connection-id <uuid>
uip maestro case tasks describe --type connector-trigger --id <typeId> --connection-id <uuid>
```

Options for `enrich`:
| Flag | Description |
|------|-------------|
| `--type <type>` | **(required)** Enrichable task type |
| `--id <id>` | **(required)** Unique ID of the task (entityKey or action-app id) |
| `--element-id <elementId>` | Element ID for variable binding |

Options for `describe`:
| Flag | Description |
|------|-------------|
| `--type <type>` | **(required)** Task type: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `connector-activity`, `connector-trigger` |
| `--id <id>` | **(required)** Unique ID of the task (entityKey or action-app id) |
| `--connection-id <id>` | Connection UUID (required for `connector-activity` and `connector-trigger` types) |

Enrichable types: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`.

---

## uip maestro case registry

Manage the local resource cache. Requires `uip login` for tenant-specific resources.

```bash
# Refresh cache from all resource types
uip maestro case registry pull
uip maestro case registry pull --force             # ignore 30-min TTL and force refresh
uip maestro case registry pull --solution-id <id>  # include a specific solution's resources

# List all cached resources
uip maestro case registry list --output json

# Search for resources by keyword and/or field filters
uip maestro case registry search <keyword>
uip maestro case registry search <keyword> --type process
uip maestro case registry search --filter "name:contains=Apple,category=Pipelines"
uip maestro case registry search <keyword> --filter "name:contains=Foo" --type agent

# Get a resource by identifier (entityKey, id, or uiPathActivityTypeId)
uip maestro case registry get <identifier>
uip maestro case registry get <identifier> --type agent
uip maestro case registry get <uiPathActivityTypeId> --type typecache-activities --connection-id <uuid>
```

Resource types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `typecache-activities`, `typecache-triggers`, `action-apps`, `solution`.

Options for `pull`:
| Flag | Description |
|------|-------------|
| `-f, --force` | Force refresh, ignore 30-min cache TTL |
| `-s, --solution-id <id>` | Include the registry of the specified solution |

Options for `search`:
| Flag | Description |
|------|-------------|
| `[keyword]` | Optional keyword to search by |
| `-t, --type <type>` | Limit search to a specific resource type |
| `-f, --filter <filter>` | Field filters, e.g. `name:contains=Apple,category=Pipelines` |

Filter format: `field=value` or `field:operator=value`. Supported fields: `name`, `description`, `category`, `tags`. Supported operators: `equals`, `contains`, `in`, `startsWith`, `endsWith`. At least one of keyword or `--filter` is required.

Options for `get`:
| Flag | Description |
|------|-------------|
| `<identifier>` | **(required)** The entityKey (process types), id (action-apps), or uiPathActivityTypeId (typecache) of the resource |
| `-t, --type <type>` | Limit to a specific resource type: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `typecache-activities`, `typecache-triggers`, `action-apps`, `solution` |
| `--connection-id <id>` | Connection UUID for connector-specific IS field metadata. Only applies to `typecache-activities` / `typecache-triggers` results — enriches the resource with input/output definitions from Integration Service |

Output: `{ MatchCount, Resources: [{ ResourceType, Resource }] }`.

Cache lives at `~/.uipcli/case-resources/` and expires after 30 minutes.

### uip maestro case registry get-connector

Look up a connector activity or trigger from the local TypeCache index. Returns the raw cache entry and its connector config (connector key, connector type, operation name). Does NOT fetch connections — use `get-connection` for that.

```bash
uip maestro case registry get-connector --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connector --type typecache-triggers --activity-type-id <uuid>
```

| Flag | Description |
|------|-------------|
| `-t, --type <type>` | **(required)** `typecache-activities` or `typecache-triggers` |
| `--activity-type-id <id>` | **(required)** The `uiPathActivityTypeId` to look up |

Output: `{ Entry, Config }`.

### uip maestro case registry get-connection

Look up a connector and fetch available connections from Integration Service. **Requires `uip login`.**

```bash
uip maestro case registry get-connection --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connection --type typecache-triggers --activity-type-id <uuid>
```

| Flag | Description |
|------|-------------|
| `-t, --type <type>` | **(required)** `typecache-activities` or `typecache-triggers` |
| `--activity-type-id <id>` | **(required)** The `uiPathActivityTypeId` to look up |

Output: `{ Entry, Config, Connections }` — use a `Connections[].id` value as `--connection-id` in `tasks add-connector` or `triggers add-event`.

---

## uip maestro case process

Manage and run Case processes. **Requires `uip login`.**

```bash
# List available Case processes
uip maestro case process list
uip maestro case process list --folder-key <guid>
uip maestro case process list --filter "Name eq 'MyCase'"

# Get process schema and entry point details
uip maestro case process get <process-key> <feed-id>
uip maestro case process get <process-key> <feed-id> --folder-key <guid>

# Run a Case process
uip maestro case process run <process-key> <folder-key>
uip maestro case process run <process-key> <folder-key> --inputs '{"key":"value"}'
uip maestro case process run <process-key> <folder-key> --inputs @inputs.json --validate
```

Options for `list`:
| Flag | Description |
|------|-------------|
| `-t, --tenant <name>` | Tenant name (defaults to authenticated tenant) |
| `-f, --folder-key <key>` | **(required)** Filter by folder key (GUID) |
| `--filter <odata>` | Additional OData filter expression |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

Options for `get`:
| Flag | Description |
|------|-------------|
| `<process-key>` | **(required)** Process key (from `list`) |
| `<feed-id>` | **(required)** Feed ID (from `list`) |
| `-t, --tenant <name>` | Tenant name |
| `-f, --folder-key <key>` | **(required)** Folder key (GUID) |
| `--login-validity <minutes>` | Min minutes before token refresh |

Options for `run`:
| Flag | Description |
|------|-------------|
| `<process-key>` | **(required)** Process key |
| `<folder-key>` | **(required)** Folder key (GUID) |
| `-i, --inputs <json>` | Input parameters as JSON string or `@file.json` (also reads from stdin) |
| `-t, --tenant <name>` | Tenant name |
| `--release-key <key>` | Release key (GUID, from `list`) |
| `--feed-id <id>` | Feed ID for package lookup |
| `--robot-ids <ids>` | Comma-separated robot IDs |
| `--validate` | Validate inputs against process schema before running |
| `--login-validity <minutes>` | Min minutes before token refresh |

Output on `run`: `{ jobKey, state, traceId }` — use `jobKey` with `uip maestro case job traces`.

---

## uip maestro case job

Monitor Case jobs. **Requires `uip login`.**

```bash
# Stream traces for a running job
uip maestro case job traces <job-key>
uip maestro case job traces <job-key> --pretty
uip maestro case job traces <job-key> --poll-interval 5000

# Get job status
uip maestro case job status <job-key>
uip maestro case job status <job-key> --detailed
```

Options for `traces`:
| Flag | Description |
|------|-------------|
| `<job-key>` | **(required)** Job key (GUID from `process run`) |
| `-t, --tenant <name>` | Tenant name |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--traces-service <name>` | Traces service name (default: `llmopstenant_`) |
| `--pretty` | Human-readable trace output instead of raw JSON |
| `--login-validity <minutes>` | Min minutes before token refresh |

Options for `status`:
| Flag | Description |
|------|-------------|
| `<job-key>` | **(required)** Job key (GUID from `process run`) |
| `-t, --tenant <name>` | Tenant name |
| `--folder-key <key>` | Folder key (GUID, defaults to authenticated folder) |
| `--detailed` | Show full response with all fields |
| `--login-validity <minutes>` | Min minutes before token refresh |

---

## uip maestro case instance

Manage live Case process instances. **Requires `uip login`.**

```bash
# List instances
uip maestro case instance list
uip maestro case instance list --limit 20 --offset 0
uip maestro case instance list --process-key <key> --folder-key <key>
uip maestro case instance list --package-id <id> --error-code <code>

# Get a specific instance
uip maestro case instance get <instance-id>
uip maestro case instance get <instance-id> --folder-key <key>

# Lifecycle operations (all accept --folder-key and --comment)
uip maestro case instance pause <instance-id>
uip maestro case instance resume <instance-id>
uip maestro case instance cancel <instance-id>
uip maestro case instance retry <instance-id>

# Variables
uip maestro case instance variables <instance-id>
uip maestro case instance variables <instance-id> --parent-element-id <id>

# Incidents for a specific instance
uip maestro case instance incidents <instance-id>

# Get the Case definition (JSON) for a process instance
uip maestro case instance asset <instance-id>

# Migration: migrate instance to a different package version
uip maestro case instance migrate <instance-id> <new-version>

# Go-to: move execution cursor from one element to another
uip maestro case instance goto <instance-id> '[{"sourceElementId":"A","targetElementId":"B"}]'
uip maestro case instance cursors <instance-id>
uip maestro case instance element-executions <instance-id>
```

---

## uip maestro case processes

View Case process summaries. **Requires `uip login`.**

```bash
# List all Case process summaries
uip maestro case processes list

# Get incidents for a specific process
uip maestro case processes incidents <process-key>
uip maestro case processes incidents <process-key> --folder-key <key>
```

---

## uip maestro case incident

View and retrieve Case incidents across all processes. **Requires `uip login`.**

```bash
# Get incident summaries across all processes
uip maestro case incident summary

# Get a single incident by ID
uip maestro case incident get <incident-id> --folder-key <key>
```

Options for `get`:
| Flag | Description |
|------|-------------|
| `<incident-id>` | **(required)** Incident ID |
| `--folder-key <key>` | **(required)** Folder key |

---

## Global options (all commands)

| Option | Description |
|--------|-------------|
| `--output json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |