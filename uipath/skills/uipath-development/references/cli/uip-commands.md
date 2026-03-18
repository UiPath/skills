# UiPath CLI (uip) Command Reference

Complete reference for all `uip` commands. Commands are organized by functional area.

> **This reference covers implemented commands.** Some command groups (Assets, Queues, Packages, etc.) are planned but not yet available. See the "Planned Commands" section at the end.

---

## Authentication

### `uip login`

Authenticate with UiPath Cloud using OAuth2, client credentials, or PAT tokens.

```bash
uip login [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-f, --file <path>` | Path to .env file with credentials | `.env` |
| `--authority <url>` | Custom authority URL | -- |
| `--client-id <id>` | OAuth2 client ID (for non-interactive auth) | -- |
| `--client-secret <secret>` | Client Secret or Application Secret | -- |
| `-s, --scope <scopes>` | Custom scopes (space-separated) | -- |
| `-t, --tenant <name>` | Tenant name (non-interactive mode) | -- |
| `--it, --interactive` | Interactively select tenant from list | -- |

**Interactive login (browser OAuth2):**
```bash
uip login --format json
```

**Non-interactive login (CI/CD, client credentials):**
```bash
uip login --client-id "my-app-id" --client-secret "my-secret" --tenant "MyTenant" --format json
```

**Login with .env file:**
```bash
uip login --file .env.production --format json
```

### `uip login status`

Show current login status and session information.

```bash
uip login status --format json
```

### `uip login tenant list`

List all available tenants for the authenticated organization.

```bash
uip login tenant list --format json
```

### `uip login tenant set <name>`

Set the active tenant by name.

```bash
uip login tenant set "Production" --format json
```

### `uip logout`

End current session and clear stored tokens.

```bash
uip logout --format json
```

---

## Orchestrator — Folders (`or folders`)

### `uip or folders list`

List all folders.

```bash
uip or folders list [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-f, --filter <filter>` | OData filter expression | -- |
| `-c, --count <number>` | Number of items to return | 50 |

### `uip or folders create <name>`

Create a new folder.

```bash
uip or folders create <name> [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-d, --description <desc>` | Folder description | -- |
| `-p, --parent <parentId>` | Parent folder ID (for nested folders) | -- |

**Examples:**
```bash
# Create a top-level folder
uip or folders create "Finance" --format json

# Create a nested folder
uip or folders create "Invoicing" --parent 12345 --description "Invoice processing automations" --format json
```

### `uip or folders get <id>`

Get folder by ID.

```bash
uip or folders get 12345 --format json
```

### `uip or folders get-all-for-current-user`

Get all folders accessible to the current user with pagination.

```bash
uip or folders get-all-for-current-user [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `--take <number>` | Number of items to return | 50 |
| `--skip <number>` | Number of items to skip | 0 |

### `uip or folders delete <id>`

Delete a folder by ID.

```bash
uip or folders delete 12345 --format json
```

### `uip or folders move <id> <parent-folder-id>`

Move folder to a new parent.

```bash
uip or folders move 12345 67890 --format json
```

### `uip or folders edit <id>`

Edit folder properties.

```bash
uip or folders edit <id> [options] --format json
```

| Option | Description |
|---|---|
| `-n, --name <name>` | New display name |
| `-d, --description <desc>` | New description |
| `--folder-type <type>` | Folder type (Standard, Personal, Virtual, Solution, DebugSolution) |
| `-p, --provision-type <type>` | Robot provisioning (Manual, Automatic) |
| `-m, --permission-model <model>` | Permission model (InheritFromTenant, FineGrained) |
| `-f, --feed-type <type>` | Feed type (Undefined, Processes, Libraries, PersonalWorkspace, FolderHierarchy) |

---

## Solution (`solution`)

### `uip solution new <solutionName>`

Create a new empty UiPath solution file (.uipx).

```bash
uip solution new "MySolution" --format json
```

The command automatically adds `.uipx` extension if not provided.

### `uip solution pack <solutionPath> <outputPath>`

Pack a solution from a folder or .uis file into a .zip package.

```bash
uip solution pack <solutionPath> <outputPath> [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-n, --name <name>` | Package name | Solution folder name |
| `-v, --version <version>` | Package version | 1.0.0 |
| `--verbose` | Enable verbose logging | Off |

**Example:**
```bash
uip solution pack ./MySolution ./output --version 2.0.0 --format json
```

### `uip solution publish <packagePath>`

Publish a solution package (.zip) to UiPath.

```bash
uip solution publish <packagePath> [options] --format json
```

| Option | Description |
|---|---|
| `-t, --tenant <name>` | Tenant override |
| `-l, --location-key <guid>` | Location key (optional GUID) |

**Example:**
```bash
uip solution publish ./output/MySolution.1.0.0.zip --format json
```

### `uip solution project add <projectPath> [solutionFile]`

Add an existing project to a solution.

```bash
uip solution project add ./MyProject --format json
# or specify solution file explicitly:
uip solution project add ./MyProject ./MySolution.uipx --format json
```

The project folder must contain `project.uiproj` or `project.json`. If `solutionFile` is omitted, searches upward for the nearest `.uipx`.

### `uip solution project remove <projectPath> [solutionFile]`

Remove a project from a solution.

```bash
uip solution project remove ./MyProject --format json
```

---

## Flow (`flow`)

### `uip flow init <name>`

Create a new Flow project with boilerplate files.

```bash
uip flow init "MyFlow" --format json
```

| Option | Description |
|---|---|
| `--force` | Force initialization even if target directory is not empty |

### `uip flow pack <projectPath> <outputPath>`

Pack a Flow project into a .nupkg file.

```bash
uip flow pack ./MyFlow ./output --name "MyFlow" --version "1.0.0" --format json
```

### `uip flow validate <flowFile>`

Validate a .flow file against the Flow schema.

```bash
uip flow validate ./MyFlow/main.flow --format json
```

### `uip flow process list`

List available Flow projects.

```bash
uip flow process list [options] --format json
```

| Option | Description |
|---|---|
| `-t, --tenant <name>` | Tenant override |
| `-f, --folder-key <key>` | Filter by folder key (GUID) |
| `--filter <odata>` | Additional OData filter |

### `uip flow job traces <job-key>`

Stream traces for a running Flow job.

```bash
uip flow job traces <job-key> [options]
```

| Option | Description | Default |
|---|---|---|
| `--poll-interval <ms>` | Polling interval in milliseconds | 2000 |
| `--pretty` | Human-readable trace output | Off (raw JSON) |

### `uip flow job status <job-key>`

Get detailed status of a Flow job.

```bash
uip flow job status <job-key> --detailed --format json
```

### `uip flow registry pull`

Pull and sync node data from Flow registry.

```bash
uip flow registry pull --format json
```

### `uip flow registry list`

List all nodes cached locally.

```bash
uip flow registry list --format json
```

### `uip flow registry get [filters...]`

Get specific node(s) by filter criteria.

```bash
uip flow registry get <filter> --format json
```

### `uip flow registry search [query]`

Search for nodes by name or category.

```bash
uip flow registry search "email" --format json
```

---

## Integration Service (`is`)

### `uip is connectors list`

List all connectors.

```bash
uip is connectors list [options] --format json
```

| Option | Description |
|---|---|
| `-f, --filter <filter>` | Filter connectors by name or key |
| `--refresh` | Force re-fetch from API, ignoring cache |

### `uip is connectors get <connector-key>`

Get connector details by key.

```bash
uip is connectors get "uipath-zoho-desk" --format json
```

### `uip is connections list [connector-key]`

List connections, optionally filtered by connector.

```bash
uip is connections list --format json
uip is connections list "uipath-salesforce" --format json
uip is connections list --folder-key "<GUID>" --format json
```

### `uip is connections create <connector-key>`

Create a new connection for a connector. Opens an OAuth flow in the browser by default.

```bash
uip is connections create <connector-key> [options] --format json
```

| Option | Description |
|---|---|
| `--no-browser` | Print the auth URL instead of opening a browser (for headless environments) |

**Example:**
```bash
# Create a Slack connection (opens browser for OAuth)
uip is connections create "uipath-salesforce-slack" --format json

# Create without auto-opening browser
uip is connections create "uipath-salesforce-slack" --no-browser --format json
```

### `uip is connections ping <connection-id>`

Test a connection's health/connectivity.

```bash
uip is connections ping "<CONNECTION_ID>" --format json
```

### `uip is connections edit <connection-id>`

Edit an existing connection's configuration.

```bash
uip is connections edit "<CONNECTION_ID>" --format json
```

### `uip is activities list <connector-key>`

List activities for a connector. By default lists non-trigger activities only.

```bash
uip is activities list "uipath-salesforce" --format json
uip is activities list "uipath-salesforce" --triggers --format json
```

| Option | Description |
|---|---|
| `--triggers` | List trigger activities only (isTrigger=true) |
| `--refresh` | Force re-fetch from API, ignoring cache |

### `uip is resources list <connector-key> [object-name]`

List resources for a connector.

```bash
uip is resources list "uipath-salesforce" --format json
uip is resources list "uipath-salesforce" "Account" --operation List --format json
```

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID |
| `--operation <op>` | Filter by operation (List, Retrieve, Create, Update, Delete, Replace) |

### `uip is resources describe <connector-key> <object-name>`

Describe a resource object and its operations.

```bash
uip is resources describe "uipath-salesforce" "Account" --format json
```

### `uip is resources execute <connector-key> <object-name>`

Execute an operation on a resource.

```bash
uip is resources execute "uipath-salesforce" "Account" --connection-id "<ID>" --body '{"Name":"Acme"}' --format json
```

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID (required for execution) |
| `--body <json>` | Request body as JSON string |
| `--query <json>` | Query parameters as JSON string |

---

## RPA (`rpa`)

Commands for managing RPA workflow projects (XAML-based, not coded workflows).

### Key Commands

| Command | Description |
|---|---|
| `uip rpa restore --path <dir>` | Restore NuGet packages |
| `uip rpa compile --project-path <dir>` | Compile a project |
| `uip rpa validate --project-path <dir>` | Validate a project |
| `uip rpa analyze --project-path <dir>` | Analyze a project |
| `uip rpa execute project --project-path <dir>` | Execute project's main workflow |
| `uip rpa execute workflow --workflow-path <file>` | Execute a specific workflow file |
| `uip rpa workflow list --project-path <dir>` | List workflows in project |
| `uip rpa workflow create --project-path <dir> --name <name>` | Create a new workflow |
| `uip rpa workflow outline --workflow-path <file>` | Get activity tree structure |
| `uip rpa activity add --workflow-path <file> --parent-idref <id> --activity-type <type>` | Add activity to workflow |
| `uip rpa activity edit --workflow-path <file> --idref <id>` | Edit activity properties |
| `uip rpa packages list --project-path <dir>` | List packages in project |
| `uip rpa packages search-activities --project-path <dir> --keyword <kw>` | Search for activities |
| `uip rpa dependencies add-package --project-path <dir> --package-name <pkg> --version <ver>` | Add a package dependency |

---

## Tools Management (`tools`)

### `uip tools list`

List all currently installed CLI tools.

```bash
uip tools list --format json
```

### `uip tools search [query]`

Search for available tools in the configured registry.

```bash
uip tools search --format json
uip tools search "orchestrator" --format json
```

### `uip tools install <package-name>`

Install a tool from the registry.

```bash
uip tools install "@uipath/orchestrator-tool" --format json
```

| Option | Description |
|---|---|
| `-g, --global` | Install globally |

### `uip tools update`

Update installed tools.

```bash
uip tools update --format json
uip tools update --name "@uipath/orchestrator-tool" --version "1.2.0" --format json
```

---

## MCP Server (`mcp`)

### `uip mcp serve`

Start the Model Context Protocol (MCP) server using stdio transport.

```bash
uip mcp serve --format json
```

---

## Coded Agents (`codedagents`)

### `uip codedagents setup`

Detect Python installation and verify package is installed.

```bash
uip codedagents setup --format json
```

### `uip codedagents exec [args...]`

Execute the uipath-python package with provided arguments.

Unknown commands are automatically forwarded to exec:
```bash
uip codedagents dev       # → uip codedagents exec dev
uip codedagents init      # → uip codedagents exec init
```

---

## Orchestrator — Jobs (`or jobs`)

### `uip or jobs list <folder-id>`

List jobs in a folder.

```bash
uip or jobs list <folder-id> --format json
```

### `uip or jobs get <folder-id> <job-id>`

Get job details by ID.

```bash
uip or jobs get <folder-id> <job-id> --format json
```

### `uip or jobs start <folder-id> <release-key>`

Start a job from a release.

```bash
uip or jobs start <folder-id> <release-key> --format json
```

| Option | Description | Default |
|---|---|---|
| `--strategy <strategy>` | Execution strategy (ModernJobsCount, All, Specific, JobsCount) | ModernJobsCount |
| `--jobs-count <number>` | Number of jobs to create | 1 |
| `--input-arguments <json>` | Input arguments as JSON string | -- |
| `--job-priority <priority>` | Job priority (Low, Normal, High) | -- |
| `--reference <reference>` | User-specified reference for the job | -- |

### `uip or jobs stop <folder-id> <job-id>`

Stop a running job.

```bash
uip or jobs stop <folder-id> <job-id> --format json
```

### `uip or jobs stop-multiple <folder-id>`

Stop multiple jobs.

```bash
uip or jobs stop-multiple <folder-id> --format json
```

### `uip or jobs restart <folder-id> <job-id>`

Restart a job.

```bash
uip or jobs restart <folder-id> <job-id> --format json
```

### `uip or jobs resume <folder-id> <job-id>`

Resume a suspended job.

```bash
uip or jobs resume <folder-id> <job-id> --format json
```

---

## Orchestrator — Processes (`or processes`)

### `uip or processes list <folder-id>`

List processes (releases) in a folder.

```bash
uip or processes list <folder-id> --format json
```

### `uip or processes get <folder-id> <process-id>`

Get process details by ID.

```bash
uip or processes get <folder-id> <process-id> --format json
```

### `uip or processes versions <folder-id> <process-id>`

List versions of a process.

```bash
uip or processes versions <folder-id> <process-id> --format json
```

---

## Orchestrator — Releases (`or releases`)

### `uip or releases list <folder-id>`

List releases in a folder.

```bash
uip or releases list <folder-id> --format json
```

---

## Solution Deploy (`solution deploy`)

### `uip solution deploy run`

Deploy a solution to a folder.

```bash
uip solution deploy run -n "<deployment-name>" -c "<configuration-key>" [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-n, --name <name>` | Name for the deployment (required) | -- |
| `-c, --configuration-key <key>` | Configuration key (required) | -- |
| `-f, --folder-path <path>` | Fully qualified folder path (e.g. 'Shared') | -- |
| `-k, --folder-key <guid>` | Installation folder key (GUID) | -- |
| `--no-force-activate` | Disable force activation | Force activate |
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--poll-interval <ms>` | Polling interval for status | 2000 |

### `uip solution deploy status <deploymentKey>`

Check status of a deployment.

```bash
uip solution deploy status "<deployment-key>" --format json
```

### `uip solution packages list`

List published solution packages.

```bash
uip solution packages list --format json
```

---

## Planned Commands (Not Yet Available)

These commands are proposed or in development and are **not yet available** in the CLI:

### Orchestrator (Proposed)

| Command Group | Commands |
|---|---|
| **Assets** | `or assets list`, `or assets create`, `or assets get`, `or assets delete` |
| **Queues** | `or queues list`, `or queues create`, `or queues delete`, `or queues items add/list/get/set-status` |
| **Storage Buckets** | `or storage-buckets list`, `create`, `delete`, `upload`, `download` |
| **Packages** | `or packages list`, `upload`, `download`, `delete` |
| **Libraries** | `or libraries list`, `upload`, `delete` |
| **Machines** | `or machines list`, `get` |
| **Execution Logs** | `or logs list`, `get` |
| **Triggers** | `or triggers list`, `create`, `update`, `delete`, `enable`, `disable` |
| **Schedules** | `or schedules list`, `create`, `update`, `delete` |
| **Robots** | `or robots list` |

### Other (Proposed)

| Command Group | Description |
|---|---|
| **Coded Apps** (`codedapp`) | Create, restore, build, pack app projects |
| **Test Manager** (`tm`) | Upload results, list/execute test sets, get reports |
| **API Workflows** (`api-workflow`) | Create, restore, build, pack API workflow projects |
| **Resources** (`resources`) | Resource management |
| **DocsAI** (`docsai`) | Documentation AI features |
