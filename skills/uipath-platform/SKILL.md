---
name: uipath-platform
description: "UiPath platform ops via the uip CLI — use this skill for ANY task hitting UiPath Cloud / Orchestrator / Studio Web / Integration Service / LLM Gateway. Load BEFORE writing any code that calls a UiPath API. Covers auth, folders, assets, queues, storage buckets, bucket files, libraries, webhooks, triggers, processes, jobs, machines, users, roles, sessions, calendars, IS connectors/connections/activities, BYO LLM product configurations (`uip llm-configuration byo-connections` — register / audit / re-probe / troubleshoot tenant-owned OpenAI / Azure OpenAI / Bedrock / Vertex / Anthropic keys against UiPath products), traces, licensing. For `uip solution` lifecycle→uipath-solution. For PDD/SDD authoring→uipath-design. For workflow code (.xaml/.cs)→uipath-rpa, .flow→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn, agents (.py/agent.json)→uipath-agents, Test Manager→uipath-test."
when_to_use: "User mentions UiPath / Orchestrator / Studio Web / Integration Service / LLM Gateway / 'uip' CLI / asset / queue / bucket / library / webhook / trigger / connector / connection / tenant / folder / robot / package / BYO LLM. Also 'upload to UiPath', 'create asset', 'start job', 'list queues', 'deploy a single package to Orchestrator', 'OAuth2 token', 'register my own LLM key', 'configure a model substitution', 'my BYO LLM key stopped working / returns errors', 're-probe / audit a BYO configuration', 'uipath.com REST'. Load BEFORE composing any HTTP request — most UiPath tasks have a `uip` command. For `uip solution` ops or `.uipx` deploys→uipath-solution."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Platform — uip CLI Assistant

Comprehensive guide for UiPath Cloud / Orchestrator / Studio Web / Integration Service, end-to-end via the `uip` CLI. For `uip solution` lifecycle load [`uipath-solution`](/uipath:uipath-solution); for PDD/SDD authoring load [`uipath-design`](/uipath:uipath-design).

## Use the CLI. Don't roll your own REST.

**Always reach for `uip` CLI commands first.** The CLI covers auth, Orchestrator (folders, processes, jobs, machines, users, roles, sessions, calendars, settings, audit logs, credential stores, feeds, attachments), resources (assets, queues, queue items, storage buckets, bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), traces, and licensing end-to-end.

Hand-rolling HTTP calls — reading `~/.uipath/.auth` and POSTing to `/odata/...` or `/orchestrator_/...` — almost always misses something the CLI gets right: the `X-UIPATH-OrganizationUnitId` folder header, OData filter shape (`Key eq '...'` with escaped single quotes), pagination envelope, retry semantics, validation error shape, or `Result/Code/Data` output contract. **Reach for raw REST only after you've searched [`references/uip-commands.md`](references/uip-commands.md) for your task and confirmed no `uip` command covers it.** The CLI is the source of truth.

If you find yourself about to `curl` `https://cloud.uipath.com/...` — stop. Search the command index first. Examples of what people often miss:

- "upload a file to a storage bucket" → `uip or bucket-files upload` (NOT a `PUT /buckets/.../signedUrl` dance)
- "create an asset" → `uip or assets create` (NOT a `POST /odata/Assets`)
- "start a job for a process" → `uip or jobs start <process-key>` (NOT `POST /odata/Jobs/UiPath.Server.Configuration.OData.StartJobs`)
- "configure an Integration Service connection" → `uip is connections create <connector-key>` (NOT a hand-rolled OAuth flow)

## When to Use This Skill

Load this skill BEFORE writing any code that talks to UiPath. Specific triggers:

- **Auth & tenant**: login, logout, switch tenant, `~/.uipath/.auth`, OAuth token, organization
- **Orchestrator core**: folders (`list/get/create/edit/move/delete/runtimes`), processes/releases, jobs (`start/stop/logs/traces/healing-data`), packages (`upload/download/versions`), machines, users / roles / sessions (incl. DirectoryUser/DirectoryGroup/DirectoryRobot/DirectoryExternalApplication), licenses, calendars, settings, audit logs, credential stores, feeds, attachments
- **Resources (Orchestrator-scoped)**: assets (text/integer/bool/credential), queues + queue items, storage buckets + bucket files (`upload/download/get-download-url/get-upload-url`), libraries (`.nupkg`), webhooks (HMAC signing), triggers (time/queue/api)
- **Integration Service**: connectors, connections (OAuth flow), activities, IS triggers, agent-workflow reference resolution
- **LLM Gateway — BYO product configurations**: `uip llm-configuration byo-connections` (`list / get / create / update / delete / list-product-configs`). Register tenant-owned OpenAI / Azure OpenAI / AWS Bedrock / Google Vertex / Anthropic / OpenAI-compatible keys against UiPath product features (agents, agenthub, jarvis, IXP, agent builder, ECS). Two input shapes: single-mapping (for `AnyModelWithOwnAdditions` features) and repeated `--mapping` (required for `AllModels` / `AnyModel`). Server-side validation is mandatory.
- **LLM Gateway — diagnose a failing BYO config**: re-probe the underlying IS connection with `byo-connections get <id> --force-refresh`, force a fresh server-side probe with an idempotent `update`, audit the tenant with `list --include-connection-details` filtered on `connectionState != Enabled`, check catalog drift with `list-product-configs`, and cross-reference trace evidence with `uip traces spans get <trace-id>`. The gateway does **not** expose per-request invocation logs via CLI — diagnosis is current-state + trace evidence only. See [`references/llmgateway/byo-connections.md` § Diagnostics](references/llmgateway/byo-connections.md#diagnostics). For tenant-wide AI Trust Layer policy that may be overriding routing, see [uipath-governance](/uipath:uipath-governance).
- **Traces**: `uip traces spans get [trace-id]` (LLM/agentic execution observability)
- **Platform licensing**: tenant license allocations, user/group bundle assignments, consumables reporting (`uip platform tenants licenses`, `users licenses`, `groups rules`, `licenses consumables`)
- **CLI tooling itself**: `uip tools list/search/install`, `uip mcp serve`

For `uip solution` lifecycle (init / pack / publish / deploy / activate / upload) and CI/CD pipelines that build and deploy UiPath solutions, load [`uipath-solution`](/uipath:uipath-solution).

## Auth token location

The CLI stores credentials at **`~/.uipath/.auth`** after login:
```
UIPATH_URL=https://alpha.uipath.com
UIPATH_ORGANIZATION_NAME=my_org
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

### Step 4 — Work with Orchestrator Resources

Choose the appropriate operation from the Task Navigation table below. For `uip solution` ops, load [`uipath-solution`](/uipath:uipath-solution).

## Task Navigation

| I need to... | Read these |
|---|---|
| **Authenticate / manage tenants** | [references/uip-commands.md](references/uip-commands.md) |
| **Set up folders, users, machines** | [references/orchestrator/setup-environment.md](references/orchestrator/setup-environment.md) |
| **Run and monitor jobs** | [references/orchestrator/run-jobs.md](references/orchestrator/run-jobs.md) |
| **Manage sessions and runtimes** | [references/orchestrator/manage-sessions.md](references/orchestrator/manage-sessions.md) |
| **Tenant settings, calendars, audit logs** | [references/orchestrator/tenant-admin.md](references/orchestrator/tenant-admin.md) |
| **Understand Orchestrator concepts** | [references/orchestrator/orchestrator.md](references/orchestrator/orchestrator.md) |
| **Manage assets** | [references/orchestrator/manage-assets.md](references/orchestrator/manage-assets.md) |
| **Work with queues and queue items** | [references/orchestrator/process-queues.md](references/orchestrator/process-queues.md) |
| **Work with storage buckets and files** | [references/orchestrator/work-with-storage.md](references/orchestrator/work-with-storage.md) |
| **Set up triggers and webhooks** | [references/orchestrator/triggers-and-webhooks.md](references/orchestrator/triggers-and-webhooks.md) |
| **Develop / pack / publish / deploy / activate solutions; set up CI/CD** | [/uipath:uipath-solution](/uipath:uipath-solution) |
| **Debug LLM/agent traces (spans)** | [references/traces/traces.md](references/traces/traces.md) |
| **Annotate traces with feedback** | [references/traces/feedback.md](references/traces/feedback.md) |
| **Use Integration Service** | [references/integration-service/integration-service.md](references/integration-service/integration-service.md) |
| **Configure BYO LLM keys (OpenAI / Azure OpenAI / Bedrock / Vertex / Anthropic)** | [references/llmgateway/byo-connections.md](references/llmgateway/byo-connections.md) |
| **Diagnose / audit / re-probe a BYO LLM configuration** | [references/llmgateway/byo-connections.md#diagnostics](references/llmgateway/byo-connections.md#diagnostics) |
| **Allocate licenses to tenants** | [references/licensing/tenant-allocations.md](references/licensing/tenant-allocations.md) |
| **Assign user/group license bundles** | [references/licensing/user-licenses-allocations.md](references/licensing/user-licenses-allocations.md) |
| **Report on license consumption** | [references/licensing/consumables-report.md](references/licensing/consumables-report.md) |
| **Understand licensing concepts** | [references/licensing/licensing.md](references/licensing/licensing.md) |
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

## Deployment Notes

- **Starting jobs requires runtimes.** If you get error 2818 "no runtimes configured", the target folder needs machine templates with Unattended/Development runtimes assigned.
- **For `uip solution` pack / publish / deploy / activate flows, load [`uipath-solution`](/uipath:uipath-solution).** This skill owns the auth and Orchestrator surface those flows depend on; the solution skill owns the lifecycle commands.
- **Fallback: direct REST API.** When CLI tools don't support an operation, use the Orchestrator REST API with the access token from `~/.uipath/.auth`. See [references/orchestrator/orchestrator.md - REST API](references/orchestrator/orchestrator.md).

## References

- **[CLI Command Reference](references/uip-commands.md)** — Every `uip` command with workflow links
- **[Orchestrator](references/orchestrator/orchestrator.md)** — Concepts, folders, jobs, processes, machines, users
- **[Resources](references/orchestrator/resources.md)** — Assets, queues, buckets, triggers, libraries, webhooks
- **[Solutions](/uipath:uipath-solution)** — Solution lifecycle (`uip solution init/pack/publish/deploy/activate`)
- **[Design](/uipath:uipath-design)** — PDD/SDD authoring (Process → Solution Design Document)
- **[Traces — Spans](references/traces/traces.md)** — LLM execution trace observability
- **[Traces — Feedback](references/traces/feedback.md)** — Annotate traces with sentiment and comments
- **[Integration Service](references/integration-service/integration-service.md)** — Connectors, connections, activities, resources
- **[LLM Gateway — BYO Connections](references/llmgateway/byo-connections.md)** — Register tenant-owned LLM keys against UiPath products
- **[Licensing](references/licensing/licensing.md)** — Tenant allocations, user/group bundles, consumables reporting
- **[Coded Workflows](/uipath:uipath-rpa)** — Building coded automation projects

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
