---
name: uipath-platform
description: "UiPath platform ops via the uip CLI — use for ANY task on UiPath Cloud / Orchestrator / Studio Web / Integration Service / Data Fabric / LLM Gateway; load BEFORE writing code calling a UiPath API. Covers login/auth/tenants, folders, assets, queues, storage buckets, libraries, webhooks, triggers, processes, jobs, machines/robots, users, roles, IS connectors/connections, Data Fabric entities/records/files/choice-sets (`uip df`), BYO LLM (`uip llm-configuration`) and BYO guardrail (BYOG) configs, context grounding, traces, licensing. Historical job metrics→uipath-insights. Why did X fail / root cause→uipath-troubleshoot. Audit logs / login history→uipath-admin. `uip solution`→uipath-solution. PDD/SDD→uipath-planner. .xaml/.cs→uipath-rpa, .flow (incl. Data Fabric nodes)→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn, agents→uipath-agents, Test Manager→uipath-test."
when_to_use: "User mentions UiPath / Orchestrator / Studio Web / Integration Service / Data Fabric / LLM Gateway / 'uip' CLI / asset / queue / bucket / library / webhook / trigger / connector / connection / tenant / folder / robot / package / entity(incl. federated / virtual data object / zero-copy) / record / record / choice set(incl. federated / virtual choice set / zero-copy, entity using connector) / trace / span / trace feedback / BYO LLM / BYO guardrail / BYOG. Also 'upload to UiPath', 'create asset', 'start job', 'list faulted / running jobs', 'list queues', 'set ROI for a process', 'business ROI of a queue', 'deploy a single package to Orchestrator', 'OAuth2 token', 'list trace spans / add trace feedback', 'create entity', 'add field', 'delete field', 'add an entity to my solution', 'local entity', 'entity in my solution', 'list entities', 'insert record', 'update record', 'delete record', 'query Data Fabric', 'search records', 'show every <thing> tagged/where', 'filter records by tag/choice/field', 'count by group', 'unique tag combinations', 'group by field', 'aggregate COUNT/SUM/AVG', 'create choice-set', 'create choiceset', 'add choice set values', 'delete choice set', 'attach file to record', 'upload/download/delete file on entity record', 'swap record attachment', 'import CSV', 'load CSV into entity/list', 'load spreadsheet into entity', 'bulk load records from CSV', 'bulk import from CSV', 'register my own LLM key', 'configure a model substitution', 'my BYO LLM key stopped working / returns errors', 're-probe / audit a BYO configuration', 'list bring-your-own guardrail configurations', 'register/enable/disable/delete a BYOG guardrail configuration', 'who registered this BYOG guardrail', 'uipath.com REST'. For `uip solution` ops or `.uipx` deploys→uipath-solution. For runtime evals of published agents / `uip eval run`→uipath-agents. For Data Fabric connector nodes inside a `.flow`→uipath-maestro-flow. CLI bootstrap: 'install UiPath CLI', 'prepare workstation for UiPath', 'install UiPath skills', `uip` missing / not found, Node or npm missing, Python or .NET SDK missing."
allowed-tools: Bash, Read, Write, Glob, Grep, Skill
---

# UiPath Platform — uip CLI Assistant

Guide UiPath Cloud, Orchestrator, Studio Web, and Integration Service through `uip`. For `uip solution` lifecycle load [`uipath-solution`](/uipath:uipath-solution); for PDD/SDD design and task planning load [`uipath-planner`](/uipath:uipath-planner).

## Route Diagnostic Intent Before Platform Work

Classify the requested **outcome** before running commands:

1. **Causal outcome → hand off immediately.** For explanation, diagnosis, or root cause of undesirable existing behavior, invoke the `Skill` tool with uipath-troubleshoot (exact available-skills name) before anything else. Do not fetch jobs/logs/traces first; troubleshoot owns evidence collection. Telling the user to use troubleshoot does not replace the `Skill` call.
2. **Operational outcome → stay here.** This includes state inspection without a causal question, CRUD/lifecycle actions, input validation before application, and executing an already-diagnosed fix.
3. **Mixed request → troubleshoot first.** Hand off diagnosis, then return for the platform mutation applying the confirmed fix.
4. **Sibling unavailable → degrade gracefully.** State that handoff could not run and provide the entity, scope, and time window needed to retry. Do not invent a platform-only root cause.

## Use the CLI. Don't roll your own REST.

**Always reach for `uip` first.** It covers authentication; Orchestrator folders, processes, jobs, machines, users, roles, sessions, calendars, settings, audit logs, credential stores, feeds, attachments, assets, queues, queue items, storage buckets/files, libraries, webhooks, triggers, Integration Service connectors/connections/activities/triggers, traces, and licensing. Search [`references/uip-commands.md`](references/uip-commands.md) before raw REST; use REST only when no CLI command covers the task. The CLI is authoritative for the `X-UIPATH-OrganizationUnitId` folder header, OData filter shape (`Key eq '...'` with escaped single quotes), pagination, retries, validation errors, and the `Result/Code/Data` contract. Do not read `~/.uipath/.auth` and POST to `/odata/...` or `/orchestrator_/...` by default. Before `curl` to `https://cloud.uipath.com/...`, stop and search the index.

Use CLI equivalents: `uip or bucket-files upload`, `uip or assets create`, `uip or jobs start <process-key>`, `uip is connections create <connector-key>`, and `uip df files upload <entity-id> <record-id> <field-name> --file <path>` instead of a `PUT /buckets/.../signedUrl` dance, `POST /odata/Assets`, `POST /odata/Jobs/UiPath.Server.Configuration.OData.StartJobs`, a hand-rolled OAuth flow, or `records insert` / `records update` with the file value. FILE values passed via `records insert` / `records update` are silently stripped and return Success; see `references/data-fabric/data-fabric.md` Rule 6.

## CLI Bootstrap for Fresh Machines

**MUST read [references/cli-bootstrap.md](references/cli-bootstrap.md) § CLI Bootstrap for Fresh Machines before installing or bootstrapping the uip CLI, Node, .NET, Python, or agent skills on a machine where `uip --version` fails.**

## When to Use This Skill

Load this skill BEFORE writing code that talks to UiPath. It covers:

- **Bootstrap/setup:** fresh machines, missing `uip`, Node/npm, Python, or .NET SDK, and LLM coding agents needing UiPath skills.
- **Auth/tenant:** login, logout, tenant switching, named profiles (`--profile <name>`), `~/.uipath/.auth`, OAuth tokens, and organizations.
- **Orchestrator:** folders (`list/get/create/edit/move/delete/runtimes`), processes/releases, jobs (`start/stop/logs/traces/healing-data`), packages (`upload/download/versions`), machines, users, roles, sessions (including DirectoryUser/DirectoryGroup/DirectoryRobot/DirectoryExternalApplication), licenses, calendars, settings, audit logs, credential stores, feeds, and attachments.
- **Resources:** assets (text/integer/bool/credential), queues/items, storage buckets/files (`upload/download/get-download-url/get-upload-url`), libraries (`.nupkg`), HMAC webhooks, and time/queue/API triggers.
- **Integration Service:** connectors, OAuth connections, activities, IS triggers, and agent-workflow reference resolution.
- **Data Fabric:** **⛔ STOP — before ANY `uip df` command, Read [`references/data-fabric/data-fabric.md`](references/data-fabric/data-fabric.md).** It contains Critical Rules (folder-scope prompt flow, irreversible-operation gates, complex-field configuration), request-body schema, per-type operator matrix, and [`entity-schema.md`](references/data-fabric/entity-schema.md), [`federated-entity-creation.md`](references/data-fabric/federated-entity-creation.md) (federated/virtual data object/zero-copy entities backed by a connector or another entity), [`records-query.md`](references/data-fabric/records-query.md), [`filter-platform-contract.md`](references/data-fabric/filter-platform-contract.md), [`choice-sets.md`](references/data-fabric/choice-sets.md), [`file-attachments.md`](references/data-fabric/file-attachments.md), [`bulk-import.md`](references/data-fabric/bulk-import.md), and [`local-entities.md`](references/data-fabric/local-entities.md). Entities have typed columns, constraints (`lengthLimit`, `minValue` / `maxValue`, `decimalPrecision`), choice-set/relationship/file fields, and `addFields` / `updateFields` / `removeFields` evolution. `uip df entities <verb> --local` authors an entity into a solution on disk rather than the tenant; it becomes real at deploy and needs no login. Use it only when explicitly requested; tenant is default. Local entities support tenant field types except choice sets and relationships; see [`local-entities.md`](references/data-fabric/local-entities.md). Records support insert/update/delete/list/get/`query`, server-side filtering, sorting, pagination, group-by, and `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`; filter bodies use `filterGroup.queryFilters[]`; see [`records-query.md`](references/data-fabric/records-query.md). Files are binary attachments on `FILE` fields through `files upload / download / delete`; dedicated verbs are mandatory because record writes strip FILE values. Choice sets are shared enumerations for `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE`; use immutable integer `NumberId`s, not labels. **Folder scoping** — tenant-level OR folder-scoped via `--folder-key <GUID>` on every write, `--include-folders` on `entities list` / `choice-sets list`. CSV bulk import is `uip df records import <entity-id> --file <path.csv> --output json`; it supports basic types only. Complex fields (`CHOICE_SET`, `RELATIONSHIP`, `FILE`, `AUTO_NUMBER`) and text containing line breaks or double quotes require `records insert --file <json>`. For Query/Create/Update/Delete/GetById connector nodes inside a `.flow`, hand off to `uipath-maestro-flow`, which owns in-flow node JSON, `bindings_v2.json`, and connection-resource layout.
- **LLM Gateway BYO configurations:** `uip llm-configuration byo-connections` (`list / get / create / update / delete / list-product-configs`) registers tenant-owned OpenAI, Azure OpenAI, AWS Bedrock, Google Vertex, Anthropic, or OpenAI-compatible keys for agents, agenthub, jarvis, IXP, agent builder, and ECS. Single-mapping input is for `AnyModelWithOwnAdditions`; repeated `--mapping` is required for `AllModels` / `AnyModel`; server-side validation is mandatory.
- **Diagnosing a failing BYO configuration:** run `byo-connections get <id> --force-refresh`; force a fresh server probe with idempotent `update`; audit with `list --include-connection-details` filtered on `connectionState != Enabled`; check catalog drift with `list-product-configs`; and cross-reference `uip traces spans get <trace-id>`. The gateway exposes no per-request invocation logs via CLI: use current state plus traces. See [`references/llmgateway/byo-connections.md` § Diagnostics](references/llmgateway/byo-connections.md#diagnostics). For tenant-wide AI Trust Layer routing policy, see [uipath-governance](/uipath:uipath-governance).
- **AI Trust Layer BYOG:** `uip guardrails byo-configurations` (`list / list-validators / probe / create / update / delete`) manages tenant-registered external validator providers backed by Integration Service connections. `ValidatorName` is tenant-unique and the only agent reference (`ByoValidator(<ValidatorName>)`; the connection resolves server-side). Before creating, run `list` to ensure the name is free and `uip is connections list` for `--connection-id`. `create` always probes and aborts on failure with no skip flag; `update` re-probes when `--connection-id` changes. `probe` and `list-validators` test without saving; `update` merges supplied fields and can switch `--enabled`/`--disabled`; `delete` requires `--force`; there is no `get`. See [`references/guardrails/byo-configurations.md`](references/guardrails/byo-configurations.md). For authoring guardrails, see [uipath-agents](/uipath:uipath-agents).
- **Traces:** `uip traces spans get <trace-id>`.
- **Context grounding:** `uip context-grounding` (`list / create` from a bucket or connection / ingest / retrieve / search / delete); `retrieve` polls ingestion status. Agents and flows consume these indexes as tools. See [`references/context-grounding/index-management.md`](references/context-grounding/index-management.md).
- **Licensing:** `uip platform tenants licenses`, `users licenses`, `groups rules`, and `licenses consumables get`; consumables has only that verb, with summary/daily/folders as `--mode` values.
- **CLI tooling:** `uip tools list/search/install`, `uip mcp serve`.

For `uip solution` init/pack/publish/deploy/activate/upload and CI/CD, load [`uipath-solution`](/uipath:uipath-solution).

## Auth token location

The default login stores credentials at **`~/.uipath/.auth`**:

```
UIPATH_URL=https://cloud.uipath.com
UIPATH_ORGANIZATION_NAME=my_org
UIPATH_TENANT_NAME=my_tenant
UIPATH_ACCESS_TOKEN=eyJ...
UIPATH_ORGANIZATION_ID=...
UIPATH_TENANT_ID=...
```

Named profiles store credentials at **`~/.uipath/profiles/<name>/.auth`**. Use named profiles when the user asks to keep multiple UiPath logins on the same machine:

```bash
uip login --profile dev --output json
uip login status --profile dev --output json
uip login which --profile dev --output json
```

`--profile <name>` is global and must accompany every command using that login, e.g. `uip --profile dev or folders list --output json`. `default` is the built-in unprofiled login and maps to `~/.uipath/.auth`. Names may contain only letters, numbers, `.`, `_`, and `-`; never use paths such as `../prod`. `--profile` and auth-command `--file <folder>` are mutually exclusive. A missing named profile never falls back to `~/.uipath/.auth` or Robot credentials; tell the user to run `uip login --profile <name>`.

Reuse tokens for direct Orchestrator REST only when CLI coverage is absent. For an active named profile, obtain its path from `uip login which --profile <name> --output json`, never by assuming `~/.uipath/.auth`.

## Quick Start

### Step 0 — Ensure the CLI Exists

Run:

```bash
uip --version
```

If missing, use the official installer in [CLI Bootstrap for Fresh Machines](references/cli-bootstrap.md#cli-bootstrap-for-fresh-machines), then open a new shell if it added PATH entries.

### Step 1 — Authenticate

Before Orchestrator, solutions, or Integration Service, always check:

```bash
uip login status --output json
```

If it reports `Logged in`, stop this step; there is no `--check` flag. For a named profile, check it explicitly:

```bash
uip login status --profile dev --output json
```

**Interactive browser OAuth2:** `uip login` opens a browser and blocks until completion. **Never run interactive login through your shell tool, with or without `--no-browser`.** It hides the URL and wait from the person who must sign in. `--no-browser` is for automation that opens the URL itself; it still blocks, and copied URLs are fragile because line-wrapped/truncated URLs are rejected with an opaque browser error. Ask the user to run it in their terminal; in Claude Code, prefix with `!`:

```text
! uip login
```

Afterward confirm with `uip login status --output json`. If retrying yields `EADDRINUSE` / "Port 8104 is already in use", an abandoned attempt owns the callback port; it releases within 5 minutes, or the user can end the stale process.

Named login:

```bash
uip login --profile dev --output json
```

Custom authority (Automation Suite, dedicated, or other non-default host):

```bash
uip login --authority "<AUTHORITY_URL>" --it --output json
```

For CI/CD, use client credentials from environment variables via `env.<NAME>`; never request a secret in chat or put it on the command line:

```bash
uip login --client-id env.UIPATH_CLIENT_ID --client-secret env.UIPATH_CLIENT_SECRET --tenant "<TENANT>" --output json
```

### Step 2 — Select a Tenant

```bash
uip login tenant list --output json
uip login tenant set "<TENANT_NAME>" --output json
```

### Step 3 — Explore Orchestrator

```bash
uip or folders list --output json
```

### Step 4 — Work with Orchestrator Resources

Use the Task Navigation table. For `uip solution`, load [`uipath-solution`](/uipath:uipath-solution).

## Task Navigation

| Need | Reference |
|---|---|
| Authenticate/manage tenants; full CLI reference | [references/uip-commands.md](references/uip-commands.md) |
| Folders, users, machines | [references/orchestrator/setup-environment.md](references/orchestrator/setup-environment.md) |
| Jobs; sessions/runtimes; tenant settings/calendars/audit logs | [references/orchestrator/run-jobs.md](references/orchestrator/run-jobs.md); [references/orchestrator/manage-sessions.md](references/orchestrator/manage-sessions.md); [references/orchestrator/tenant-admin.md](references/orchestrator/tenant-admin.md) |
| Orchestrator concepts | [references/orchestrator/orchestrator.md](references/orchestrator/orchestrator.md) |
| Assets; queues/items; storage buckets/files; triggers/webhooks | [references/orchestrator/manage-assets.md](references/orchestrator/manage-assets.md); [references/orchestrator/process-queues.md](references/orchestrator/process-queues.md); [references/orchestrator/work-with-storage.md](references/orchestrator/work-with-storage.md); [references/orchestrator/triggers-and-webhooks.md](references/orchestrator/triggers-and-webhooks.md) |
| Business ROI | [references/orchestrator/business-roi.md](references/orchestrator/business-roi.md) |
| Polling/export logs/429/field caps | [references/orchestrator/api-limits.md](references/orchestrator/api-limits.md) |
| Solutions and CI/CD | [/uipath:uipath-solution](/uipath:uipath-solution) |
| Runtime evals on a published agent | [/uipath:uipath-agents](/uipath:uipath-agents) |
| Traces/spans and feedback | [references/traces/traces.md](references/traces/traces.md); [references/traces/feedback.md](references/traces/feedback.md) |
| Integration Service | [references/integration-service/integration-service.md](references/integration-service/integration-service.md) |
| Data Fabric overview | [references/data-fabric/data-fabric.md](references/data-fabric/data-fabric.md) |
| Data Fabric schemas, federated entities (virtual data object / zero-copy), local entities | [references/data-fabric/entity-schema.md](references/data-fabric/entity-schema.md); [references/data-fabric/federated-entity-creation.md](references/data-fabric/federated-entity-creation.md); [references/data-fabric/local-entities.md](references/data-fabric/local-entities.md) |
| Data Fabric queries, filters, choice sets, files, CSV | [references/data-fabric/records-query.md](references/data-fabric/records-query.md); [references/data-fabric/filter-platform-contract.md](references/data-fabric/filter-platform-contract.md); [references/data-fabric/choice-sets.md](references/data-fabric/choice-sets.md); [references/data-fabric/file-attachments.md](references/data-fabric/file-attachments.md); [references/data-fabric/bulk-import.md](references/data-fabric/bulk-import.md) |
| BYO LLM configuration/diagnostics | [references/llmgateway/byo-connections.md](references/llmgateway/byo-connections.md); [references/llmgateway/byo-connections.md#diagnostics](references/llmgateway/byo-connections.md#diagnostics) |
| BYOG manage; validation; diagnostics | [references/guardrails/byo-configurations.md](references/guardrails/byo-configurations.md); [references/guardrails/byo-configurations.md#validation-mandatory-before-save](references/guardrails/byo-configurations.md#validation-mandatory-before-save); [references/guardrails/byo-configurations.md#diagnostics](references/guardrails/byo-configurations.md#diagnostics) |
| Licensing allocations, bundles, consumption, concepts, diagnosis | [references/licensing/tenant-allocations.md](references/licensing/tenant-allocations.md); [references/licensing/user-licenses-allocations.md](references/licensing/user-licenses-allocations.md); [references/licensing/consumables-report.md](references/licensing/consumables-report.md); [references/licensing/licensing.md](references/licensing/licensing.md); [references/licensing/diagnose/CAPABILITY.md](references/licensing/diagnose/CAPABILITY.md) |
| Bootstrap `uip`, Node, Python, .NET, agent skills | [CLI Bootstrap for Fresh Machines](references/cli-bootstrap.md#cli-bootstrap-for-fresh-machines) |
| Build/run/validate coded workflows | [/uipath:uipath-rpa](/uipath:uipath-rpa) |

## Resolving UiPath Studio

Some operations (creating projects, validating, running workflows, packing) require UiPath Studio. When Studio is needed:

1. **Check for a running instance first:**
   ```bash
   uip rpa instances list --output json
   ```
2. **If none is running, try the standard install location:**
   ```bash
   uip rpa studio start --output json
   ```
3. **If that fails** (version too old, not found, etc.), **ASK THE USER where their Studio build is located.** Do NOT search the entire filesystem. Common locations include `C:\Program Files\UiPath\Studio`, a dev build directory (e.g., `dev4/Studio/Output/bin/Debug`), or a custom install path.
4. **Once you have the path, pass it explicitly:**
   ```bash
   uip rpa studio start --studio-dir "<STUDIO_DIR>" --output json
   ```

> **Never spend time searching for Studio automatically.** If the default fails, ask immediately—the user knows where their build is.

## Key Concepts

**MUST read [references/key-concepts.md](references/key-concepts.md) § Key Concepts before explaining UiPath platform hierarchy, robot types, folder types, or asset types.**

## CLI Overview

`uip` is the unified UiPath CLI:

| Group | Prefix | Scope | Status |
|---|---|---|---|
| Authentication | `login`, `logout` | OAuth2, client credentials, PAT, tenants | Available |
| Orchestrator | `or` | Folders, jobs, processes, releases | Available |
| Resource | `resource` | Assets, queues/items, buckets/files | Available |
| Integration Service | `is` | Connectors, connections, activities, resources | Available |
| Data Fabric | `df` | Entities, records, files, choice sets (`@uipath/data-fabric-tool`) | Available |
| Tools | `tools` | CLI extensions | Available |
| MCP | `mcp` | Model Context Protocol server | Available |
| Coded Agents | `codedagent` | Python agent lifecycle (setup, exec) | Available |
| RPA | `rpa` | Workflow create, compile, validate, execute | Available |

### Global Options

| Option | Meaning | Default |
|---|---|---|
| `--output <format>` | `table`, `json`, `yaml`, `plain` | `table` interactive; `json` non-interactive |
| `--output-filter <expression>` | JMESPath JSON filter | -- |
| `--profile <name>` | Profile at `~/.uipath/profiles/<name>/.auth` | built-in default |
| `--verbose` | Debug logging | Off |
| `--help` / `-h` | Help | -- |
| `--version` / `-v` | Version | -- |

Always use `--output json` programmatically. Narrow lists with the noun's server-side filter (`--state Faulted`, `--type Text`, `--status New`, `--name`, `--process-name`, `--search`) rather than listing everything and filtering mentally; see [references/uip-commands.md](references/uip-commands.md). Use `--output-filter` for JMESPath reshaping or attributes lacking a server filter, e.g. `--output-filter "[].{id: Id, name: Name}"`. It evaluates inside `Data`: use `[].Key`, never `Data[].Key`; keys are case-sensitive and normally PascalCased (`DisplayName`, not `displayName`), except commands preserving raw casing (`maestro flow registry get`, `api-workflow registry`, conversational commands). A nonmatch silently returns nothing.

## Deployment Notes

- Starting jobs requires runtimes. Error 2818, "no runtimes configured", means the target folder needs machine templates with Unattended/Development runtimes assigned.
- For `uip solution` pack/publish/deploy/activate, load [`uipath-solution`](/uipath:uipath-solution); it owns lifecycle commands while this skill owns dependent auth and Orchestrator surfaces.
- Use direct REST only when CLI coverage is absent, with the access token from `~/.uipath/.auth`; see [references/orchestrator/orchestrator.md - REST API](references/orchestrator/orchestrator.md).
- Orchestrator rate-limits some tenant endpoints. Filtered `jobs list` / `queue-items list` calls are budgeted per minute; `--export` on `jobs logs` / `audit-logs list` has a quota of 100/day. The CLI does not retry 429 (`ErrorCode: rate_limited`). Read [references/orchestrator/api-limits.md](references/orchestrator/api-limits.md) before pollers, loops, or scripts.

## References

- **[CLI Command Reference](references/uip-commands.md)** — Every command and workflow links
- **[Orchestrator](references/orchestrator/orchestrator.md)** — Concepts, folders, jobs, processes, machines, users
- **[Resources](references/orchestrator/resources.md)** — Assets, queues, buckets, triggers, libraries, webhooks
- **[Orchestrator API Limits](references/orchestrator/api-limits.md)** — Rate limits, export quotas, 429 handling, field caps
<!--skill-flavor:solutions-index-row:start-->
- **[Solutions](/uipath:uipath-solution)** — Solution lifecycle (`uip solution init/pack/publish/deploy/activate`)
<!--skill-flavor:solutions-index-row:end-->
- **[Planner](/uipath:uipath-planner)** — PDD/SDD design and multi-skill planning (Process → Solution Design Document → task list)
- **[Traces — Spans](references/traces/traces.md)** — LLM execution trace observability
- **[Traces — Feedback](references/traces/feedback.md)** — Annotate traces with sentiment and comments
- **[Integration Service](references/integration-service/integration-service.md)** — Connectors, connections, activities, resources
- **[Data Fabric](references/data-fabric/data-fabric.md)** — Schemas, records, queries, choice sets, files, CSV, folder scoping, [local entities](references/data-fabric/local-entities.md)
- **[LLM Gateway — BYO Connections](references/llmgateway/byo-connections.md)** — Register tenant-owned LLM keys
- **[Guardrails — BYOG Configurations](references/guardrails/byo-configurations.md)** — Manage and diagnose BYOG configurations and their Integration Service connections
- **[Licensing](references/licensing/licensing.md)** — Allocations, bundles, consumption, [diagnose](references/licensing/diagnose/CAPABILITY.md)
- **[Coded Workflows](/uipath:uipath-rpa)** — Building coded automation projects

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.