# UiPath Platform — Concepts & CLI Reference

<!-- when: load when you need the platform object hierarchy, robot/folder/asset type enumerations, the `uip` command-group map, or the global-option table. Background reference; not needed to route or run a command. -->

## Platform Hierarchy

```
Organization
  └── Tenant(s)
        └── Folder(s)              ← Orchestrator folders (logical containers)
              ├── Processes         ← Published automation packages
              ├── Assets            ← Key-value configuration (Text, Bool, Integer, Credential, Secret)
              ├── Queues            ← Work item queues for distributed processing
              ├── Jobs              ← Running/completed process executions
              ├── Triggers          ← Event-based or queue-based job triggers
              ├── Schedules         ← Time-based job scheduling (cron)
              ├── Storage Buckets   ← File storage for automation data
              ├── Machines          ← Robot execution environments
              └── Robots            ← Attended/Unattended execution agents
```

## Robot Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Attended** | Runs alongside a human user, triggered via UiPath Assistant | Front-office tasks, user-assisted automation |
| **Unattended** | Runs autonomously in virtual environments, managed by Orchestrator | Back-office tasks, scheduled processing, 24/7 operations |

## Folder Types

| Type | Description |
|------|-------------|
| **Standard** | Default folder for organizing automations |
| **Personal** | User-specific workspace |
| **Virtual** | Logical grouping without physical separation |
| **Solution** | Folder created by solution deployment |
| **DebugSolution** | Debug variant of a solution folder |

## Asset Types

| Type | Description |
|------|-------------|
| **Text** | Plain text value |
| **Bool** | Boolean (true/false) |
| **Integer** | Numeric integer value |
| **Credential** | Username + password pair |
| **Secret** | Encrypted secret value |
| **DBConnectionString** | Database connection string |
| **HttpConnectionString** | HTTP connection string |
| **WindowsCredential** | Windows credential pair |

## CLI Command Groups

The UiPath CLI (`uip`) is a unified command-line tool for the UiPath platform:

| Command Group | Prefix | Description | Status |
|---|---|---|---|
| **Authentication** | `login`, `logout` | OAuth2, client credentials, PAT, tenant management | Available |
| **Orchestrator** | `or` | Folders, jobs, processes, releases | Available |
| **Resource** | `resource` | Assets, queues, queue items, storage buckets, bucket files | Available |
| **Integration Service** | `is` | Connectors, connections, activities, resources | Available |
| **Data Fabric** | `df` | Entities, records, files, choice sets (`@uipath/data-fabric-tool`) | Available |
| **Tools** | `tools` | CLI tool extension management | Available |
| **MCP** | `mcp` | Model Context Protocol server | Available |
| **Coded Agents** | `codedagent` | Python agent lifecycle (setup, exec) | Available |
| **RPA** | `rpa` | RPA workflow management (create, compile, validate, execute) | Available |

## Global Options

Every `uip` command accepts:

| Option | Description | Default |
|---|---|---|
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` | `table` (interactive), `json` (non-interactive) |
| `--output-filter <expression>` | JMESPath expression to filter JSON output | -- |
| `--profile <name>` | Use a named auth profile from `~/.uipath/profiles/<name>/.auth` | built-in default login |
| `--verbose` | Enable verbose/debug logging | Off |
| `--help` / `-h` | Display help for the command | -- |
| `--version` / `-v` | Display CLI version | -- |
