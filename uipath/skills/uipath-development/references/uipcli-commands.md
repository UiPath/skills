# UiPath CLI (uipcli) Command Reference

Complete reference for all `uipcli` commands. Commands are organized by functional area.

> **This reference covers implemented commands.** Some command groups (Jobs, Queues, Processes, Packages, etc.) are planned but not yet available. See the "Planned Commands" section at the end.

---

## Authentication

### `uipcli login`

Authenticate with UiPath Cloud using OAuth2, client credentials, or PAT tokens.

```bash
uipcli login [options] --format json
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
uipcli login --format json
```

**Non-interactive login (CI/CD, client credentials):**
```bash
uipcli login --client-id "my-app-id" --client-secret "my-secret" --tenant "MyTenant" --format json
```

**Login with .env file:**
```bash
uipcli login --file .env.production --format json
```

### `uipcli login status`

Show current login status and session information.

```bash
uipcli login status --format json
```

### `uipcli login tenant list`

List all available tenants for the authenticated organization.

```bash
uipcli login tenant list --format json
```

### `uipcli login tenant set <name>`

Set the active tenant by name.

```bash
uipcli login tenant set "Production" --format json
```

### `uipcli logout`

End current session and clear stored tokens.

```bash
uipcli logout --format json
```

---

## Orchestrator — Assets (`orch assets`)

### `uipcli orch assets list <parent-folder-id>`

List all assets in a folder.

```bash
uipcli orch assets list <parent-folder-id> [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-f, --filter <filter>` | OData filter expression | -- |
| `-c, --count <number>` | Number of items to return | 50 |

**Example:**
```bash
uipcli orch assets list 12345 --format json
uipcli orch assets list 12345 --filter "Name eq 'ApiKey'" --format json
```

### `uipcli orch assets get <parent-folder-id> <asset-id>`

Get asset by ID.

```bash
uipcli orch assets get 12345 67890 --format json
```

### `uipcli orch assets create <parent-folder-id> <name> <value>`

Create a new asset.

```bash
uipcli orch assets create <parent-folder-id> <name> <value> [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `--type <type>` | Asset type (Text, Bool, Integer, Credential, Secret, DBConnectionString, HttpConnectionString, WindowsCredential) | Text |
| `-s, --scope <scope>` | Asset scope (Global, PerRobot) | Global |
| `-d, --description <desc>` | Asset description | -- |
| `--has-default` | Asset has default value | true |
| `--tags <tags>` | Comma-separated list of tag names | -- |

**Examples:**
```bash
# Create a text asset
uipcli orch assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json

# Create a secret asset
uipcli orch assets create 12345 "ApiKey" "sk-abc123" --type Secret --format json

# Create with description and tags
uipcli orch assets create 12345 "MaxRetries" "3" --type Integer --description "Max retry attempts" --tags "config,retry" --format json
```

### `uipcli orch assets delete <parent-folder-id> <asset-id>`

Delete an asset.

```bash
uipcli orch assets delete 12345 67890 --format json
```

---

## Orchestrator — Folders (`orch folders`)

### `uipcli orch folders list`

List all folders.

```bash
uipcli orch folders list [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `-f, --filter <filter>` | OData filter expression | -- |
| `-c, --count <number>` | Number of items to return | 50 |

### `uipcli orch folders create <name>`

Create a new folder.

```bash
uipcli orch folders create <name> [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-d, --description <desc>` | Folder description | -- |
| `-p, --parent <parentId>` | Parent folder ID (for nested folders) | -- |

**Examples:**
```bash
# Create a top-level folder
uipcli orch folders create "Finance" --format json

# Create a nested folder
uipcli orch folders create "Invoicing" --parent 12345 --description "Invoice processing automations" --format json
```

### `uipcli orch folders get <id>`

Get folder by ID.

```bash
uipcli orch folders get 12345 --format json
```

### `uipcli orch folders get-all-for-current-user`

Get all folders accessible to the current user with pagination.

```bash
uipcli orch folders get-all-for-current-user [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `--take <number>` | Number of items to return | 50 |
| `--skip <number>` | Number of items to skip | 0 |

### `uipcli orch folders delete <id>`

Delete a folder by ID.

```bash
uipcli orch folders delete 12345 --format json
```

### `uipcli orch folders move <id> <parent-folder-id>`

Move folder to a new parent.

```bash
uipcli orch folders move 12345 67890 --format json
```

### `uipcli orch folders edit <id>`

Edit folder properties.

```bash
uipcli orch folders edit <id> [options] --format json
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

### `uipcli solution new <solutionName>`

Create a new empty UiPath solution file (.uipx).

```bash
uipcli solution new "MySolution" --format json
```

The command automatically adds `.uipx` extension if not provided.

### `uipcli solution pack <solutionPath> <outputPath>`

Pack a solution from a folder or .uis file into a .zip package.

```bash
uipcli solution pack <solutionPath> <outputPath> [options] --format json
```

| Option | Description | Default |
|---|---|---|
| `-n, --name <name>` | Package name | Solution folder name |
| `-v, --version <version>` | Package version | 1.0.0 |
| `--verbose` | Enable verbose logging | Off |

**Example:**
```bash
uipcli solution pack ./MySolution ./output --version 2.0.0 --format json
```

### `uipcli solution publish <packagePath>`

Publish a solution package (.zip) to UiPath.

```bash
uipcli solution publish <packagePath> [options] --format json
```

| Option | Description |
|---|---|
| `-t, --tenant <name>` | Tenant override |
| `-l, --location-key <guid>` | Location key (optional GUID) |

**Example:**
```bash
uipcli solution publish ./output/MySolution.1.0.0.zip --format json
```

### `uipcli solution project add <projectPath> [solutionFile]`

Add an existing project to a solution.

```bash
uipcli solution project add ./MyProject --format json
# or specify solution file explicitly:
uipcli solution project add ./MyProject ./MySolution.uipx --format json
```

The project folder must contain `project.uiproj` or `project.json`. If `solutionFile` is omitted, searches upward for the nearest `.uipx`.

### `uipcli solution project remove <projectPath> [solutionFile]`

Remove a project from a solution.

```bash
uipcli solution project remove ./MyProject --format json
```

---

## Flow (`flow`)

### `uipcli flow init <name>`

Create a new Flow project with boilerplate files.

```bash
uipcli flow init "MyFlow" --format json
```

| Option | Description |
|---|---|
| `--force` | Force initialization even if target directory is not empty |

### `uipcli flow pack <projectPath> <outputPath>`

Pack a Flow project into a .nupkg file.

```bash
uipcli flow pack ./MyFlow ./output --name "MyFlow" --version "1.0.0" --format json
```

### `uipcli flow validate <flowFile>`

Validate a .flow file against the Flow schema.

```bash
uipcli flow validate ./MyFlow/main.flow --format json
```

### `uipcli flow process list`

List available Flow projects.

```bash
uipcli flow process list [options] --format json
```

| Option | Description |
|---|---|
| `-t, --tenant <name>` | Tenant override |
| `-f, --folder-key <key>` | Filter by folder key (GUID) |
| `--filter <odata>` | Additional OData filter |

### `uipcli flow job traces <job-key>`

Stream traces for a running Flow job.

```bash
uipcli flow job traces <job-key> [options]
```

| Option | Description | Default |
|---|---|---|
| `--poll-interval <ms>` | Polling interval in milliseconds | 2000 |
| `--pretty` | Human-readable trace output | Off (raw JSON) |

### `uipcli flow job status <job-key>`

Get detailed status of a Flow job.

```bash
uipcli flow job status <job-key> --detailed --format json
```

### `uipcli flow node pull`

Pull and sync node data from Flow registry.

```bash
uipcli flow node pull --format json
```

### `uipcli flow node list`

List all nodes cached locally.

```bash
uipcli flow node list --format json
```

### `uipcli flow node get [filters...]`

Get specific node(s) by filter criteria.

```bash
uipcli flow node get <filter> --format json
```

### `uipcli flow node search [query]`

Search for nodes by name or category.

```bash
uipcli flow node search "email" --format json
```

---

## Integration Service (`is`)

### `uipcli is connectors list`

List all connectors.

```bash
uipcli is connectors list [options] --format json
```

| Option | Description |
|---|---|
| `-f, --filter <filter>` | Filter connectors by name or key |
| `--refresh` | Force re-fetch from API, ignoring cache |

### `uipcli is connectors get <connector-key>`

Get connector details by key.

```bash
uipcli is connectors get "uipath-zoho-desk" --format json
```

### `uipcli is connections list [connector-key]`

List connections, optionally filtered by connector.

```bash
uipcli is connections list --format json
uipcli is connections list "uipath-salesforce" --format json
uipcli is connections list --folder-key "<GUID>" --format json
```

### `uipcli is connections create <connector-key>`

Create a new connection for a connector. Opens an OAuth flow in the browser by default.

```bash
uipcli is connections create <connector-key> [options] --format json
```

| Option | Description |
|---|---|
| `--no-browser` | Print the auth URL instead of opening a browser (for headless environments) |

**Example:**
```bash
# Create a Slack connection (opens browser for OAuth)
uipcli is connections create "uipath-salesforce-slack" --format json

# Create without auto-opening browser
uipcli is connections create "uipath-salesforce-slack" --no-browser --format json
```

### `uipcli is connections ping <connection-id>`

Test a connection's health/connectivity.

```bash
uipcli is connections ping "<CONNECTION_ID>" --format json
```

### `uipcli is connections edit <connection-id>`

Edit an existing connection's configuration.

```bash
uipcli is connections edit "<CONNECTION_ID>" --format json
```

### `uipcli is activities list <connector-key>`

List activities for a connector. By default lists non-trigger activities only.

```bash
uipcli is activities list "uipath-salesforce" --format json
uipcli is activities list "uipath-salesforce" --triggers --format json
```

| Option | Description |
|---|---|
| `--triggers` | List trigger activities only (isTrigger=true) |
| `--refresh` | Force re-fetch from API, ignoring cache |

### `uipcli is triggers objects <connector-key> <operation>`

List objects available for a trigger operation.

```bash
uipcli is triggers objects "uipath-salesforce-sfdc" CREATED --format json
uipcli is triggers objects "uipath-salesforce-sfdc" CREATED --connection-id "<ID>" --format json
```

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID (for custom objects) |
| `--refresh` | Force re-fetch from API, ignoring cache |

### `uipcli is triggers describe <connector-key> <operation> <object-name>`

Get field metadata for a trigger object.

```bash
uipcli is triggers describe "uipath-salesforce-sfdc" CREATED "AccountHistory" --format json
uipcli is triggers describe "uipath-salesforce-sfdc" CREATED "AccountHistory" --connection-id "<ID>" --format json
```

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID (for custom fields) |
| `--refresh` | Force re-fetch from API, ignoring cache |

### `uipcli is resources list <connector-key> [object-name]`

List resources for a connector.

```bash
uipcli is resources list "uipath-salesforce" --format json
uipcli is resources list "uipath-salesforce" "Account" --operation List --format json
```

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID |
| `--operation <op>` | Filter by operation (List, Retrieve, Create, Update, Delete, Replace) |

### `uipcli is resources describe <connector-key> <object-name>`

Describe a resource object and its operations.

```bash
uipcli is resources describe "uipath-salesforce" "Account" --format json
```

### `uipcli is resources execute <connector-key> <object-name>`

Execute an operation on a resource.

```bash
uipcli is resources execute "uipath-salesforce" "Account" --connection-id "<ID>" --body '{"Name":"Acme"}' --format json
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
| `uipcli rpa restore --path <dir>` | Restore NuGet packages |
| `uipcli rpa compile --project-path <dir>` | Compile a project |
| `uipcli rpa validate --project-path <dir>` | Validate a project |
| `uipcli rpa analyze --project-path <dir>` | Analyze a project |
| `uipcli rpa execute project --project-path <dir>` | Execute project's main workflow |
| `uipcli rpa execute workflow --workflow-path <file>` | Execute a specific workflow file |
| `uipcli rpa workflow list --project-path <dir>` | List workflows in project |
| `uipcli rpa workflow create --project-path <dir> --name <name>` | Create a new workflow |
| `uipcli rpa workflow outline --workflow-path <file>` | Get activity tree structure |
| `uipcli rpa activity add --workflow-path <file> --parent-idref <id> --activity-type <type>` | Add activity to workflow |
| `uipcli rpa activity edit --workflow-path <file> --idref <id>` | Edit activity properties |
| `uipcli rpa packages list --project-path <dir>` | List packages in project |
| `uipcli rpa packages search-activities --project-path <dir> --keyword <kw>` | Search for activities |
| `uipcli rpa dependencies add-package --project-path <dir> --package-name <pkg> --version <ver>` | Add a package dependency |

---

## Tools Management (`tools`)

### `uipcli tools installed`

List all currently installed CLI tools.

```bash
uipcli tools installed --format json
```

### `uipcli tools search [query]`

Search for available tools in the configured registry.

```bash
uipcli tools search --format json
uipcli tools search "orchestrator" --format json
```

### `uipcli tools install <package-name>`

Install a tool from the registry.

```bash
uipcli tools install "@uipath/orchestrator-tool" --format json
```

| Option | Description |
|---|---|
| `-g, --global` | Install globally |

### `uipcli tools upgrade`

Upgrade installed tools.

```bash
uipcli tools upgrade --format json
uipcli tools upgrade --name "@uipath/orchestrator-tool" --version "1.2.0" --format json
```

---

## MCP Server (`mcp`)

### `uipcli mcp serve`

Start the Model Context Protocol (MCP) server using stdio transport.

```bash
uipcli mcp serve --format json
```

---

## Coded Agents (`codedagents`)

### `uipcli codedagents setup`

Detect Python installation and verify package is installed.

```bash
uipcli codedagents setup --format json
```

### `uipcli codedagents exec [args...]`

Execute the uipath-python package with provided arguments.

Unknown commands are automatically forwarded to exec:
```bash
uipcli codedagents dev       # → uipcli codedagents exec dev
uipcli codedagents init      # → uipcli codedagents exec init
```

---

## Planned Commands (Not Yet Available)

These commands are proposed or in development and are **not yet available** in the CLI:

### Orchestrator (Proposed)

| Command Group | Commands |
|---|---|
| **Jobs** | `orch jobs start`, `orch jobs list`, `orch jobs get`, `orch jobs stop`, `orch jobs wait` |
| **Processes** | `orch processes list`, `orch processes get`, `orch processes upload`, `orch processes delete` |
| **Queues** | `orch queues list`, `orch queues create`, `orch queues delete`, `orch queues items add/list/get/set-status` |
| **Storage Buckets** | `orch storage-buckets list`, `create`, `delete`, `upload`, `download` |
| **Packages** | `orch packages list`, `upload`, `download`, `delete` |
| **Libraries** | `orch libraries list`, `upload`, `delete` |
| **Machines** | `orch machines list`, `get` |
| **Execution Logs** | `orch logs list`, `get` |
| **Triggers** | `orch triggers list`, `create`, `update`, `delete`, `enable`, `disable` |
| **Schedules** | `orch schedules list`, `create`, `update`, `delete` |
| **Connections** | `orch connections list`, `create` |
| **Robots** | `orch robots list` |
| **Environments** | `orch environments list`, `create` |

### Solution (In Progress)

| Command | Description |
|---|---|
| `solution restore` | Restore solution dependencies |
| `solution validate` | Validate solution structure |
| `solution build` | Build solution project |
| `solution deploy` | Deploy solution to an environment |
| `solution activate` | Activate a deployed solution |
| `solution uninstall` | Remove a solution from an environment |

### Other (Proposed)

| Command Group | Description |
|---|---|
| **Agentic Process** | Create, restore, build, pack agentic process projects |
| **API Workflows** | Create, restore, build, pack API workflow projects |
| **Apps / Coded Apps** | Create, restore, build, pack app projects |
| **Test Manager** | Upload results, list/execute test sets, get reports |
