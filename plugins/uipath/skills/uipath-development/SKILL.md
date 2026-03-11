---
name: uipath-development
description: "UiPath development environment assistant — authentication, Orchestrator management (folders, assets), solution lifecycle (pack, publish, deploy), Integration Service, CLI tools, and general UiPath platform knowledge. TRIGGER when: User asks about UiPath platform operations (authentication, Orchestrator, folders, assets, robots, queues, packages, processes); User asks about solution lifecycle (pack, publish, deploy, activate); User references Integration Service (connectors, connections, activities, resources); User wants to use uipcli CLI commands; User asks about environment setup, credentials, or tenant configuration; User asks general UiPath platform questions (folders, robots, queues, triggers, machine policies). DO NOT TRIGGER when: User is writing or editing workflow code (use uipath-coded-workflows or uipath-rpa-workflows instead), or asking how to automate a specific task within a workflow."
metadata: 
   allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Development Environment Assistant

Comprehensive guide for setting up and managing UiPath development environments, Orchestrator resources, solutions, and CLI tooling.

## When to Use This Skill

- User wants to **authenticate** with UiPath Cloud (login, logout, switch tenants)
- User wants to **manage Orchestrator folders** (list, create, edit, move, delete)
- User wants to **manage Orchestrator assets** (list, create, get, delete)
- User wants to **work with solutions** (create, pack, publish, deploy, activate)
- User wants to **use Integration Service** (connectors, connections, activities, resources)
- User asks about **UiPath platform concepts** (tenants, folders, robots, queues, packages)
- User wants to **install or manage CLI tools** (search, install, upgrade)
- User wants to set up a **CI/CD pipeline** for UiPath automation projects
- User asks **how to deploy** an automation to Orchestrator
- User wants to **manage flow projects** (init, pack, validate, run jobs, trace)

## Critical: Two CLI Versions

There are **two different `uipcli` versions** that may be installed. They have completely different command structures:

| | Legacy CLI (.NET) | New CLI (Node.js/Bun) |
|---|---|---|
| **Install location** | `~/.dotnet/tools/uipcli` | `dev4/uipcli/packages/cli/dist/index.js` |
| **Version** | v25.10.x | v0.0.x |
| **Auth** | Inline on every command (`-u`/`-p`, `-I`/`-S`) | Session-based (`login` → token stored at `~/.uipcli/.env`) |
| **Asset commands** | `asset deploy <csv>` (CSV bulk) | `orch assets create <folder-id> <name> <value>` |
| **Pack** | `package pack <path> -o <output>` | `solution pack <path> <output>` |
| **Deploy** | `package deploy <nupkg> <url> <tenant> -I ... -S ...` | `solution publish <zip>` |

### Detecting which CLI is available

```bash
# Legacy CLI
which uipcli && uipcli --version

# New CLI — must be built first
ls dev4/uipcli/packages/cli/dist/index.js 2>/dev/null
```

### Building the new CLI (if not built)

```bash
cd dev4/uipcli
bun install
bun run build
# Then invoke via:
cd packages/cli && bun run dist/index.js <command> --format json
```

### Auth token location

The new CLI stores credentials at **`~/.uipcli/.env`** after login:
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

**New CLI (interactive OAuth2):**
```bash
cd dev4/uipcli/packages/cli && bun run dist/index.js login --format json
```

For a custom authority (e.g., alpha.uipath.com):
```bash
cd dev4/uipcli/packages/cli && bun run dist/index.js login --authority "https://alpha.uipath.com/identity_" --it --format json
```

For non-interactive (CI/CD) scenarios, use client credentials:
```bash
cd dev4/uipcli/packages/cli && bun run dist/index.js login --client-id "<ID>" --client-secret "<SECRET>" --tenant "<TENANT>" --format json
```

Check login status:
```bash
cd dev4/uipcli/packages/cli && bun run dist/index.js login status --format json
```

**Legacy CLI (no session — pass credentials per command):**
The legacy CLI does not have a `login` command. Auth is passed inline on every command via `-A`, `-I`, `-S`, `--applicationScope`.

### Step 2 — Select a Tenant

List available tenants and set the active one:

```bash
uipcli login tenant list --format json
uipcli login tenant set "<TENANT_NAME>" --format json
```

### Step 3 — Explore Orchestrator

List folders to orient yourself:
```bash
uipcli orch folders list --format json
```

### Step 4 — Work with Solutions or Orchestrator Resources

Choose the appropriate operation from the Task Navigation table below.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Authenticate / manage tenants** | [references/uipcli-commands.md - Authentication](references/uipcli-commands.md) |
| **Manage Orchestrator folders** | [references/orchestrator-guide.md - Folders](references/orchestrator-guide.md) |
| **Manage Orchestrator assets** | [references/orchestrator-guide.md - Assets](references/orchestrator-guide.md) |
| **Understand Orchestrator concepts** | [references/orchestrator-guide.md - Concepts](references/orchestrator-guide.md) |
| **Create / pack / publish solutions** | [references/solution-guide.md](references/solution-guide.md) |
| **Deploy / activate solutions** | [references/solution-guide.md - Deploy](references/solution-guide.md) |
| **Use Integration Service** | [references/integration-service-guide.md](references/integration-service-guide.md) |
| **Manage flow projects** | [references/uipcli-commands.md - Flow](references/uipcli-commands.md) |
| **Install / manage CLI tools** | [references/uipcli-commands.md - Tools](references/uipcli-commands.md) |
| **Set up CI/CD pipeline** | [references/solution-guide.md - CI/CD](references/solution-guide.md) |
| **Full CLI command reference** | [references/uipcli-commands.md](references/uipcli-commands.md) |
| **Build/run/validate coded workflows** | [/uipath-coded-workflows:uipath-coded-workflows](/uipath-coded-workflows:uipath-coded-workflows) |

## Resolving UiPath Studio

Some operations (creating projects, validating, running workflows, packing) require UiPath Studio. When Studio is needed:

1. **Check for a running instance first:**
   ```bash
   rpa-tool list-instances --format json
   ```

2. **If no instance is running, try the standard install location:**
   ```bash
   rpa-tool start-studio --format json
   ```

3. **If that fails (version too old, not found, etc.) — ASK THE USER where their Studio build is located.** Do NOT search the entire filesystem. Common locations include:
   - `C:\Program Files\UiPath\Studio`
   - A dev build directory (e.g., `dev4/Studio/Output/bin/Debug`)
   - A custom install path

4. **Once you have the path, pass it explicitly:**
   ```bash
   rpa-tool start-studio --studio-dir "<STUDIO_DIR>" --format json
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

The UiPath CLI (`uipcli`) is a unified command-line tool for interacting with the UiPath platform:

| Command Group | Prefix | Description | Status |
|---|---|---|---|
| **Authentication** | `login`, `logout` | OAuth2, client credentials, PAT, tenant management | Available |
| **Orchestrator** | `orch` | Folders, assets management | Available |
| **Solutions** | `solution` | Create, pack, publish, deploy, activate solutions | Available |
| **Flow** | `flow` | Flow project lifecycle (init, pack, validate, run, trace) | Available |
| **Integration Service** | `is` | Connectors, connections, activities, resources | Available |
| **Tools** | `tools` | CLI tool extension management | Available |
| **MCP** | `mcp` | Model Context Protocol server | Available |
| **Coded Agents** | `codedagents` | Python agent lifecycle (setup, exec) | Available |
| **RPA** | `rpa` | RPA workflow management (create, compile, validate, execute) | Available |

### Global Options

Every `uipcli` command accepts:

| Option | Description | Default |
|---|---|---|
| `--format <format>` | Output format: `table`, `json`, `yaml`, `plain` | `table` (interactive), `json` (non-interactive) |
| `--verbose` | Enable verbose/debug logging | Off |
| `--help` / `-h` | Display help for the command | -- |
| `--version` / `-v` | Display CLI version | -- |

> **Always use `--format json`** when calling uipcli commands programmatically. JSON is compact and machine-readable.

## Deployment Lifecycle

The typical deployment workflow for a UiPath automation:

```
1. Develop    → Create/edit coded workflows or RPA projects locally
2. Validate   → rpa-tool validate / uipcli rpa validate
3. Pack       → uipcli solution pack / uipcli flow pack
4. Login      → uipcli login
5. Publish    → uipcli solution publish
6. Deploy     → uipcli solution deploy --folder "<FOLDER>"
7. Activate   → uipcli solution activate --deployment "<NAME>" --folder "<FOLDER>"
```

### Practical Deployment Notes

- **Studio locks the project database.** If `package pack` fails with "project is already opened in another Studio instance", close the project first: `rpa-tool close-project --project-dir "<DIR>" --format json`
- **Starting jobs requires runtimes.** If you get error 2818 "no runtimes configured", the target folder needs machine templates with Unattended/Development runtimes assigned.
- **Fallback: direct REST API.** When CLI tools don't support an operation, use the Orchestrator REST API with the access token from `~/.uipcli/.env`. See [references/orchestrator-guide.md - REST API](references/orchestrator-guide.md).

## Orchestrator REST API (Fallback)

When CLI commands are insufficient, use the Orchestrator REST API directly with the stored access token:

```bash
source ~/.uipcli/.env

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

The `X-UIPATH-OrganizationUnitId` header is the **folder ID** (get it from `orch folders list`).

## References

- **[Complete CLI Command Reference](references/uipcli-commands.md)** — Every uipcli command with parameters
- **[Orchestrator Guide](references/orchestrator-guide.md)** — Concepts, folders, assets, and planned features
- **[Solution Guide](references/solution-guide.md)** — Solution lifecycle: create, pack, publish, deploy
- **[Integration Service Guide](references/integration-service-guide.md)** — Connectors, connections, activities, resources
- **[Coded Workflows](/uipath-coded-workflows:uipath-coded-workflows)** — Building coded automation projects
