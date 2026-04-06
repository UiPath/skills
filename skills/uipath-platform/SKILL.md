---
name: uipath-platform
description: "UiPath platform ops — auth, Orchestrator (folders, assets, queues, buckets, robots, packages, processes), solution lifecycle (pack, publish, deploy), Integration Service, Test Manager, uip CLI. Not for writing workflow code."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Development Environment Assistant

Comprehensive guide for setting up and managing UiPath development environments, Orchestrator resources, solutions, and CLI tooling.

## When to Use This Skill

- User wants to **authenticate** with UiPath Cloud (login, logout, switch tenants)
- User wants to **manage Orchestrator folders** (list, create, edit, move, delete)
- User wants to **manage Orchestrator assets** (list, create, get, update, delete)
- User wants to **manage resources** (assets, queues, queue items, storage buckets, bucket files)
- User wants to **work with solutions** (create, pack, publish, deploy, activate)
- User asks about **UiPath platform concepts** (tenants, folders, robots, queues, packages)
- User wants to **use Test Manager** (projects, test sets, test cases, executions, results, reports, attachments)
- User wants to **install or manage CLI tools** (search, install, update)
- User wants to set up a **CI/CD pipeline** for UiPath automation projects
- User asks **how to deploy** an automation to Orchestrator

## Auth token location

The CLI stores credentials at **`~/.uipath/.auth`** after login:
```
UIPATH_URL=https://alpha.uipath.com
UIPATH_ORG_NAME=my_org
UIPATH_TENANT_NAME=my_tenant
UIPATH_ACCESS_TOKEN=eyJ...
UIPATH_ORGANIZATION_ID=...
UIPATH_TENANT_ID=...
```

This token can be reused for direct Orchestrator REST API calls when CLI commands don't cover a use case.

## Quick Start

### Step 1 — Authenticate

Before interacting with Orchestrator, solutions, or Integration Service, the user must be logged in.

**Interactive login (browser OAuth2):**
```bash
uip login --output json
```

For a custom authority (e.g., alpha.uipath.com):
```bash
uip login --authority "https://alpha.uipath.com/identity_" --it --output json
```

For non-interactive (CI/CD) scenarios, use client credentials:
```bash
uip login --client-id "<ID>" --client-secret "<SECRET>" --tenant "<TENANT>" --output json
```

Check login status:
```bash
uip login status --output json
```

### Step 2 — Select a Tenant

List available tenants and set the active one:

```bash
uip login tenant list --output json
uip login tenant set "<TENANT_NAME>" --output json
```

### Step 3 — Explore Orchestrator

List folders to orient yourself:
```bash
uip or folders list --output json
```

### Step 4 — Work with Solutions or Orchestrator Resources

Choose the appropriate operation from the Task Navigation table below.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Authenticate / manage tenants** | [references/uip-commands.md - Authentication](references/uip-commands.md) |
| **Manage Orchestrator folders** | [references/orchestrator-guide.md - Folders](references/orchestrator-guide.md) |
| **Manage assets** (via `resources assets`, NOT `or`) | [references/resources/resources-guide.md](references/resources/resources-guide.md) |
| **Manage resources** (assets, queues, queue items, storage buckets, files via `resources`) | [references/resources/resources-guide.md](references/resources/resources-guide.md) |
| **Understand Orchestrator concepts** | [references/orchestrator-guide.md - Concepts](references/orchestrator-guide.md) |
| **Create / pack / publish solutions** | [references/solution-guide.md](references/solution-guide.md) |
| **Deploy / activate solutions** | [references/solution-guide.md - Deploy](references/solution-guide.md) |
| **Use Test Manager** (projects, test sets, test cases, executions, reports) | [references/test-manager/test-manager-guide.md](references/test-manager/test-manager-guide.md) |
| **Install / manage CLI tools** | [references/uip-commands.md - Tools](references/uip-commands.md) |
| **Set up CI/CD pipeline** | [references/solution-guide.md - CI/CD](references/solution-guide.md) |
| **Use Integration Service** (connectors, connections, activities, resources) | [references/integration-service/integration-service.md](references/integration-service/integration-service.md) |
| **Full CLI command reference** | [references/uip-commands.md](references/uip-commands.md) |
| **Build/run/validate coded workflows** | [/uipath-coded-workflows:uipath-coded-workflows](/uipath-coded-workflows:uipath-coded-workflows) |

## Resolving UiPath Studio

Some operations (creating projects, validating, running workflows, packing) require UiPath Studio. When Studio is needed:

1. **Check for a running instance first:**
   ```bash
   rpa-tool list-instances --output json
   ```

2. **If no instance is running, try the standard install location:**
   ```bash
   rpa-tool start-studio --output json
   ```

3. **If that fails (version too old, not found, etc.) — ASK THE USER where their Studio build is located.** Do NOT search the entire filesystem. Common locations include:
   - `C:\Program Files\UiPath\Studio`
   - A dev build directory (e.g., `dev4/Studio/Output/bin/Debug`)
   - A custom install path

4. **Once you have the path, pass it explicitly:**
   ```bash
   rpa-tool start-studio --studio-dir "<STUDIO_DIR>" --output json
   ```

> **Never spend time searching for Studio automatically.** If the default doesn't work, ask immediately — the user knows where their build is.

## Key Concepts

### UiPath Platform Hierarchy

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

### Robot Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Attended** | Runs alongside a human user, triggered via UiPath Assistant | Front-office tasks, user-assisted automation |
| **Unattended** | Runs autonomously in virtual environments, managed by Orchestrator | Back-office tasks, scheduled processing, 24/7 operations |

### Folder Types

| Type | Description |
|------|-------------|
| **Standard** | Default folder for organizing automations |
| **Personal** | User-specific workspace |
| **Virtual** | Logical grouping without physical separation |
| **Solution** | Folder created by solution deployment |
| **DebugSolution** | Debug variant of a solution folder |

### Asset Types

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

## CLI Overview

The UiPath CLI (`uip`) is a unified command-line tool for interacting with the UiPath platform:

| Command Group | Prefix | Description | Status |
|---|---|---|---|
| **Authentication** | `login`, `logout` | OAuth2, client credentials, PAT, tenant management | Available |
| **Orchestrator** | `or` | Folders, jobs, processes, releases | Available |
| **Resources** | `resources` | Assets, queues, queue items, storage buckets, bucket files | Available |
| **Solutions** | `solution` | Create, pack, publish, deploy solutions | Available |
| **Integration Service** | `is` | Connectors, connections, activities, resources | Available |
| **Test Manager** | `tm` | Test projects, test sets, test cases, executions, reports | Available |
| **Tools** | `tools` | CLI tool extension management | Available |
| **MCP** | `mcp` | Model Context Protocol server | Available |
| **Coded Agents** | `codedagents` | Python agent lifecycle (setup, exec) | Available |
| **RPA** | `rpa` | RPA workflow management (create, compile, validate, execute) | Available |

### Global Options

Every `uip` command accepts:

| Option | Description | Default |
|---|---|---|
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` | `table` (interactive), `json` (non-interactive) |
| `--output-filter <expression>` | JMESPath expression to filter JSON output | -- |
| `--verbose` | Enable verbose/debug logging | Off |
| `--help` / `-h` | Display help for the command | -- |
| `--version` / `-v` | Display CLI version | -- |

> **Always use `--output json`** when calling `uip` commands programmatically. JSON is compact and machine-readable.
>
> **Use `--output-filter` to extract specific fields** instead of piping output to `python3`, `jq`, or other post-processing tools. The filter uses [JMESPath](https://jmespath.org/) syntax. Example: `--output json --output-filter "Data[].{id: id, name: name}"`

## Deployment Lifecycle

The typical deployment workflow for a UiPath automation:

```
1. Develop    → Create/edit coded workflows or RPA projects locally
2. Validate   → uip rpa get-errors --use-studio
3. Pack       → uip solution pack
4. Login      → uip login
5. Publish    → uip solution publish
6. Deploy     → uip solution deploy run -n "<NAME>" -c "<CONFIG_KEY>"
```

### Practical Deployment Notes

- **Starting jobs requires runtimes.** If you get error 2818 "no runtimes configured", the target folder needs machine templates with Unattended/Development runtimes assigned.
- **Fallback: direct REST API.** When CLI tools don't support an operation, use the Orchestrator REST API with the access token from `~/.uipath/.auth`. See [references/orchestrator-guide.md - REST API](references/orchestrator-guide.md).

## Orchestrator REST API (Fallback)

When CLI commands are insufficient, use the Orchestrator REST API directly with the stored access token:

```bash
source ~/.uipath/.auth

# Upload a .nupkg package
curl -X POST "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.UploadPackage" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -F "file=@./MyProject.1.0.0.nupkg"

# Create a process (release) from an uploaded package
curl -X POST "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Releases" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"Name":"MyProcess","ProcessKey":"MyProject","ProcessVersion":"1.0.0"}'

# Start a job
curl -X POST "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"startInfo":{"ReleaseKey":"<RELEASE_KEY>","Strategy":"ModernJobsCount","JobsCount":1,"RuntimeType":"Unattended","InputArguments":"{}"}}'
```

The `X-UIPATH-OrganizationUnitId` header is the **folder ID** (get it from `uip or folders list`).

## References

- **[Complete CLI Command Reference](references/uip-commands.md)** — Every `uip` command with parameters
- **[Orchestrator Guide](references/orchestrator-guide.md)** — Concepts, folders, assets, and planned features
- **[Resources Guide](references/resources/resources-guide.md)** — Assets, queues, queue items, storage buckets, bucket files
- **[Solution Guide](references/solution-guide.md)** — Solution lifecycle: create, pack, publish, deploy
- **[Test Manager Guide](references/test-manager/test-manager-guide.md)** — Test projects, test sets, test cases, executions, reports, attachments
- **[Integration Service](references/integration-service/integration-service.md)** — Connectors, connections, activities, resources for third-party services
- **[Coded Workflows](/uipath-coded-workflows:uipath-coded-workflows)** — Building coded automation projects
