---
name: uipath-platform
description: "UiPath platform ops via the uip CLI — use this skill for ANY task hitting UiPath Cloud / Orchestrator / Studio Web / Integration Service / Solutions. Load BEFORE writing any code that calls a UiPath API. Covers auth, folders, assets, queues, storage buckets, bucket files, libraries, webhooks, triggers, processes, jobs, machines, users, roles, sessions, calendars, IS connectors/connections/activities, solution pack/publish/deploy/activate, traces. For workflow code (.xaml/.cs)→uipath-rpa, .flow→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn, agents (.py/agent.json)→uipath-agents, Test Manager→uipath-test."
when_to_use: "User mentions UiPath / Orchestrator / Studio Web / Integration Service / 'uip' CLI / solution / package / agent / process / workflow / asset / queue / bucket / library / webhook / trigger / connector / connection / activity / pack / publish / deploy / activate / tenant / folder / robot. Also any 'upload to UiPath', 'create asset', 'start job', 'list queues', 'deploy to Orchestrator', 'IS connection', 'OAuth2 token', or 'uipath.com REST' phrasing. Load BEFORE composing any HTTP request — almost every UiPath task has a `uip` command that does it correctly."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Platform — uip CLI Assistant

Comprehensive guide for UiPath Cloud / Orchestrator / Studio Web / Integration Service / Solutions, end-to-end via the `uip` CLI.

## Use the CLI. Don't roll your own REST.

**Always reach for `uip` CLI commands first.** The CLI covers auth, Orchestrator (folders, processes, jobs, machines, users, roles, sessions, calendars, settings, audit logs, credential stores, feeds, attachments), resources (assets, queues, queue items, storage buckets, bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), and solution lifecycle (new, pack, publish, deploy, activate, uninstall) end-to-end.

Hand-rolling HTTP calls — reading `~/.uipath/.auth` and POSTing to `/odata/...` or `/orchestrator_/...` — almost always misses something the CLI gets right: the `X-UIPATH-OrganizationUnitId` folder header, OData filter shape (`Key eq '...'` with escaped single quotes), pagination envelope, retry semantics, validation error shape, or `Result/Code/Data` output contract. **Reach for raw REST only after you've searched [`references/uip-commands.md`](references/uip-commands.md) for your task and confirmed no `uip` command covers it.** The CLI is the source of truth.

If you find yourself about to `curl` `https://cloud.uipath.com/...` — stop. Search the command index first. Examples of what people often miss:

- "upload a file to a storage bucket" → `uip resource bucket-files upload` (NOT a `PUT /buckets/.../signedUrl` dance)
- "create an asset" → `uip resource assets create` (NOT a `POST /odata/Assets`)
- "start a job for a process" → `uip or jobs start <process-key>` (NOT `POST /odata/Jobs/UiPath.Server.Configuration.OData.StartJobs`)
- "configure an Integration Service connection" → `uip is connections create <connector-key>` (NOT a hand-rolled OAuth flow)
- "deploy a solution" → `uip solution deploy run` (NOT a `pipelinesInstall` direct call)

## When to Use This Skill

Load this skill BEFORE writing any code that talks to UiPath. Specific triggers:

- **Auth & tenant**: login, logout, switch tenant, `~/.uipath/.auth`, OAuth token, organization
- **Orchestrator core**: folders (`list/get/create/edit/move/delete/runtimes`), processes/releases, jobs (`start/stop/logs/traces/healing-data`), packages (`upload/download/versions`), machines, users / roles / sessions (incl. DirectoryUser/DirectoryGroup/DirectoryRobot/DirectoryExternalApplication), licenses, calendars, settings, audit logs, credential stores, feeds, attachments
- **Resources (Orchestrator-scoped)**: assets (text/integer/bool/credential), queues + queue items, storage buckets + bucket files (`upload/download/get-download-url/get-upload-url`), libraries (`.nupkg`), webhooks (HMAC signing), triggers (time/queue/api)
- **Integration Service**: connectors, connections (OAuth flow), activities, IS triggers, agent-workflow reference resolution
- **Solutions**: `solution init/pack/publish/deploy run/deploy activate/deploy status/deploy uninstall/upload/resource list/refresh/get`, deploy config
- **Traces**: `uip traces spans get [trace-id]` (LLM/agentic execution observability)
- **CI/CD**: pipeline that builds, publishes, and deploys UiPath solutions
- **CLI tooling itself**: `uip tools list/search/install`, `uip mcp serve`

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

## CLI Surface Probe

Before the first `uip solution …` command in a session, probe the `solution` surface to detect pre- vs post-rename CLI:

```bash
uip solution init --help --output json
```

- Result `Success` → post-rename CLI (default). Use the commands and flags below as-is.
- `unknown command` / non-zero exit → pre-rename CLI. Translate via the table below before each call. Re-probe on any later `unknown command` error.

### Pre-rename fallbacks

| Post-rename (default) | Pre-rename equivalent |
|---|---|
| `uip solution init <NAME>` | `uip solution new <NAME>` |
| `uip solution deploy run --parent-folder-path <PATH>` | `uip solution deploy run --folder-path <PATH>` |
| `uip solution deploy run --parent-folder-key <KEY>` | `uip solution deploy run --folder-key <KEY>` |

All other `solution` subcommands (`pack`, `publish`, `deploy activate/status/uninstall`, `upload`, `resource …`, `project add/import`) are unchanged on both surfaces.

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
| **Authenticate / manage tenants** | [references/uip-commands.md](references/uip-commands.md) |
| **Set up folders, users, machines** | [references/orchestrator/setup-environment.md](references/orchestrator/setup-environment.md) |
| **Run and monitor jobs** | [references/orchestrator/run-jobs.md](references/orchestrator/run-jobs.md) |
| **Manage sessions and runtimes** | [references/orchestrator/manage-sessions.md](references/orchestrator/manage-sessions.md) |
| **Tenant settings, calendars, audit logs** | [references/orchestrator/tenant-admin.md](references/orchestrator/tenant-admin.md) |
| **Understand Orchestrator concepts** | [references/orchestrator/orchestrator.md](references/orchestrator/orchestrator.md) |
| **Manage assets** | [references/resources/manage-assets.md](references/resources/manage-assets.md) |
| **Work with queues and queue items** | [references/resources/process-queues.md](references/resources/process-queues.md) |
| **Work with storage buckets and files** | [references/resources/work-with-storage.md](references/resources/work-with-storage.md) |
| **Set up triggers and webhooks** | [references/resources/triggers-and-webhooks.md](references/resources/triggers-and-webhooks.md) |
| **Develop a solution** | [references/solution/develop-solution.md](references/solution/develop-solution.md) |
| **Pack, publish, deploy solutions** | [references/solution/pack-and-deploy.md](references/solution/pack-and-deploy.md) |
| **Activate / uninstall deployments** | [references/solution/activate-and-manage.md](references/solution/activate-and-manage.md) |
| **Set up CI/CD pipeline** | [references/solution/pack-and-deploy.md](references/solution/pack-and-deploy.md) |
| **Debug LLM/agent traces (spans)** | [references/traces/traces.md](references/traces/traces.md) |
| **Annotate traces with feedback** | [references/traces/feedback.md](references/traces/feedback.md) |
| **Use Integration Service** | [references/integration-service/integration-service.md](references/integration-service/integration-service.md) |
| **Full CLI command reference** | [references/uip-commands.md](references/uip-commands.md) |
| **Build/run/validate coded workflows** | [/uipath:uipath-rpa](/uipath:uipath-rpa) |

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
| **Resource** | `resource` | Assets, queues, queue items, storage buckets, bucket files | Available |
| **Solutions** | `solution` | Create, pack, publish, deploy solutions | Available |
| **Integration Service** | `is` | Connectors, connections, activities, resources | Available |
| **Test Manager** | `tm` | Test projects, test sets, test cases, executions, reports | Available |
| **Tools** | `tools` | CLI tool extension management | Available |
| **MCP** | `mcp` | Model Context Protocol server | Available |
| **Coded Agents** | `codedagent` | Python agent lifecycle (setup, exec) | Available |
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
> **To narrow `list` results, use the noun's own filter flag** (`--state Faulted`, `--type Text`, `--status New`, `--name`, `--process-name`, `--search`). The backend filters before sending; pagination stays correct. Per-noun flags: [references/uip-commands.md](references/uip-commands.md). Never list-everything-then-filter-mentally.
>
> **Use `--output-filter` (JMESPath) for output reshaping** or for fields with no server-side flag — e.g., `--output-filter "Data[].{id: id, name: name}"`, or filtering by a derived/computed value. Don't reach for it when the server already has a filter for that attribute.

## Deployment Lifecycle

The typical deployment workflow for a UiPath automation:

```
1. Develop    → Create/edit coded workflows or RPA projects locally
2. Validate   → uip rpa validate --use-studio
3. Pack       → uip solution pack
4. Login      → uip login
5. Publish    → uip solution publish
6. Deploy     → uip solution deploy run -n "<NAME>" -c "<CONFIG_KEY>"
```

### Practical Deployment Notes

- **Starting jobs requires runtimes.** If you get error 2818 "no runtimes configured", the target folder needs machine templates with Unattended/Development runtimes assigned.
- **Fallback: direct REST API.** When CLI tools don't support an operation, use the Orchestrator REST API with the access token from `~/.uipath/.auth`. See [references/orchestrator/orchestrator.md - REST API](references/orchestrator/orchestrator.md).

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

- **[CLI Command Reference](references/uip-commands.md)** — Every `uip` command with workflow links
- **[Orchestrator](references/orchestrator/orchestrator.md)** — Concepts, folders, jobs, processes, machines, users
- **[Resources](references/resources/resources.md)** — Assets, queues, buckets, triggers, libraries, webhooks
- **[Solutions](references/solution/solution.md)** — Solution lifecycle: create, pack, publish, deploy
- **[Traces — Spans](references/traces/traces.md)** — LLM execution trace observability
- **[Traces — Feedback](references/traces/feedback.md)** — Annotate traces with sentiment and comments
- **[Integration Service](references/integration-service/integration-service.md)** — Connectors, connections, activities, resources
- **[Coded Workflows](/uipath:uipath-rpa)** — Building coded automation projects

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
