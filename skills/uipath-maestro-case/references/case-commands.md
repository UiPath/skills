# uip — Surviving CLI Command Reference

`caseplan.json` mutations are direct file edits, not CLI calls. The commands below are the only `uip` invocations the skill issues — read-only metadata fetches, registry discovery, validation, debug, runtime/instance management, and solution scaffold/upload.

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

## Local vs cloud commands

| Commands | What | Auth |
|----------|------|------|
| `cases`, `stages`, `tasks`, `edges`, `var`, `sla` | Edit local `caseplan.json` | No |
| `registry pull/list/search`, `get-connector`, `get-connection` | Registry discovery (cached after `pull`) | Yes (for `pull`) |
| `instance`, `processes`, `incidents`, `process run`, `job traces`, `debug` | Query/manage live Orchestrator state | Yes |

---

## uip solution new

Create a new solution directory + `.uipx` file.

```bash
uip solution new <SolutionName>
```

| Flag | Description |
|------|-------------|
| `<SolutionName>` | **(required)** Solution name |

Creates `<SolutionName>/` with `<SolutionName>.uipx` inside. The `case` plugin's § Scaffold writes the project files separately.

---

## uip solution project add

Register a project with an existing solution.

```bash
uip solution project add <ProjectName> <SolutionName>.uipx
```

| Flag | Description |
|------|-------------|
| `<ProjectName>` | **(required)** Project directory name (must already exist with `project.uiproj`) |
| `<SolutionName>.uipx` | **(required)** Path to the solution `.uipx` |

Adds the project to `.uipx.Projects[]`. Run after the case plugin has scaffolded `project.uiproj`.

---

## uip solution upload

Upload a solution directly to Studio Web. **Requires `uip login`.**

```bash
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory (the folder containing the `.uipx` file) directly — no intermediate bundling step. Uploads to Studio Web where the user can visualize, inspect, edit, and publish the case from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, run `uip solution upload <SolutionDir>` to push to Studio Web. Share the resulting URL with the user.

---

## uip maestro case pack

Pack a Case project directory into a `.nupkg` file. Only used when the user explicitly requests Orchestrator deployment via `uip solution publish` — not the default publish path.

```bash
uip maestro case pack <projectPath> <outputPath>
uip maestro case pack ./my-case-project ./dist --name MyCase --version 2.0.0
```

| Flag | Description |
|------|-------------|
| `<projectPath>` | **(required)** Path to the Case project directory |
| `<outputPath>` | **(required)** Output directory for the `.nupkg` |
| `-n, --name <name>` | Package name (default: project folder name) |
| `-v, --version <version>` | Package version (default: `1.0.0`) |

> `pack` + `uip solution publish` deploys directly to Orchestrator — bypasses Studio Web. Default publish path is `uip solution upload`.

---

## uip maestro case validate

Validate a case management JSON file against case management rules.

```bash
uip maestro case validate <file> --output json
```

| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |

Output: `{ File, Status: "Valid" }` on success. Errors and warnings are reported inline.

---

## uip maestro case debug

Debug a Case JSON file via a Studio Web debug session. **Requires `uip login`. Executes the case for real — sends emails, posts messages, calls APIs. Only run on explicit user consent.**

```bash
uip maestro case debug <projectDirectory> --log-level debug --output json
```

| Flag | Description |
|------|-------------|
| `<projectDirectory>` | **(required)** Path to the case project directory (must contain `project.uiproj`) |
| `--folder-id <id>` | Orchestrator folder ID (`OrganizationUnitId`). Auto-detected if omitted. |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` (default: `json`) |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

---

## uip maestro case tasks describe

Read-only metadata fetch for a task type's input/output schema. Used during planning + Phase 2b execution to discover the per-resource schema.

```bash
uip maestro case tasks describe --type <type> --id <id> --output json
uip maestro case tasks describe --type process --id <entityKey>
uip maestro case tasks describe --type connector-activity --id <typeId> --connection-id <uuid>
uip maestro case tasks describe --type connector-trigger --id <typeId> --connection-id <uuid>
```

| Flag | Description |
|------|-------------|
| `--type <type>` | **(required)** Task type: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `connector-activity`, `connector-trigger`. Use `processOrchestration` for `AGENTIC_PROCESS`. |
| `--id <id>` | **(required)** Unique ID of the task (entityKey or action-app id) |
| `--connection-id <id>` | Connection UUID (required for `connector-activity` and `connector-trigger` types) |

Returns input/output schema with names, types, and IDs. The schema is the source of truth for `data.inputs[]` / `data.outputs[]` when writing the task into `caseplan.json`.

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
| `-t, --type <type>` | Limit to a specific resource type |
| `--connection-id <id>` | Connection UUID for connector-specific IS field metadata. Only applies to `typecache-activities` / `typecache-triggers` results |

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

Output: `{ Entry, Config, Connections }` — use a `Connections[].id` value as the `connectionId` written into a connector task's `data` in `caseplan.json`.

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
