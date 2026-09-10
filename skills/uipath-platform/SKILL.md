---
name: uipath-platform
description: "UiPath platform ops via the uip CLI — use for ANY task hitting UiPath Cloud / Orchestrator / Studio Web / Integration Service / Data Fabric / LLM Gateway. Load BEFORE writing code that calls a UiPath API. Covers auth, folders, assets, queues, storage buckets, libraries, webhooks, triggers, processes, jobs, machines, users, roles, sessions, calendars, IS connectors/connections/activities, Data Fabric entities/records/files/choice-sets (`uip df`), BYO LLM product configurations, BYO guardrail (BYOG) configurations, context grounding, traces (execution traces and spans + trace feedback / annotation), licensing. For 'why did X fail' / root-cause→uipath-troubleshoot. For org/tenant audit trail / audit logs / login history→uipath-admin. For `uip solution` lifecycle→uipath-solution. For PDD/SDD design→uipath-planner. For workflow code (.xaml/.cs)→uipath-rpa, .flow (incl. Data Fabric connector nodes)→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn, agents (.py/agent.json)→uipath-agents, Test Manager→uipath-test."
when_to_use: "User mentions UiPath / Orchestrator / Studio Web / Integration Service / Data Fabric / LLM Gateway / 'uip' CLI / asset / queue / bucket / library / webhook / trigger / connector / connection / tenant / folder / robot / package / entity / record / choice set / trace / span / trace feedback / BYO LLM / BYO guardrail / BYOG. Also 'upload to UiPath', 'create asset', 'start job', 'list queues', 'deploy a single package to Orchestrator', 'OAuth2 token', 'list trace spans / add trace feedback', 'create entity', 'add field', 'delete field', 'list entities', 'insert record', 'update record', 'delete record', 'query Data Fabric', 'search records', 'show every <thing> tagged/where', 'filter records by tag/choice/field', 'count by group', 'unique tag combinations', 'group by field', 'aggregate COUNT/SUM/AVG', 'create choice-set', 'create choiceset', 'add choice set values', 'delete choice set', 'attach file to record', 'upload/download/delete file on entity record', 'swap record attachment', 'import CSV', 'load CSV into entity/list', 'load spreadsheet into entity', 'bulk load records from CSV', 'bulk import from CSV', 'register my own LLM key', 'configure a model substitution', 'my BYO LLM key stopped working / returns errors', 're-probe / audit a BYO configuration', 'list bring-your-own guardrail configurations', 'register/enable/disable/delete a BYOG guardrail configuration', 'who registered this BYOG guardrail', 'uipath.com REST'. For `uip solution` ops or `.uipx` deploys→uipath-solution. For Data Fabric connector nodes inside a `.flow`→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Glob, Grep, Skill
---

# UiPath Platform — uip CLI Assistant

Guide UiPath Cloud, Orchestrator, Studio Web, Integration Service, Data Fabric, licensing, traces, and related operations through `uip`. Load [`uipath-solution`](/uipath:uipath-solution) for `uip solution` lifecycle work and [`uipath-planner`](/uipath:uipath-planner) for PDD/SDD design and task planning.

## Route Diagnostic Intent First

Classify the requested outcome before platform work:

1. **Causal outcome:** For explanation, diagnosis, or root cause of undesirable existing behavior, invoke `Skill` with `uipath-troubleshoot` exactly as named in the available-skills list, immediately. Do not fetch jobs, logs, or traces first; troubleshoot owns evidence collection. Mentioning troubleshoot does not replace the `Skill` call.
2. **Operational outcome:** Stay here for state inspection without a causal question, CRUD/lifecycle work, pre-mutation validation, and applying an already-diagnosed fix.
3. **Mixed request:** Troubleshoot first, then return for the confirmed mutation.
4. **Unavailable sibling:** Say the handoff could not run and provide the entity, scope, and time window needed to retry. Do not invent a platform-only root cause.

## Use the CLI First

Always try `uip` and consult [`references/uip-commands.md`](references/uip-commands.md) before raw REST. Use REST only when no CLI command covers the task, with the authenticated profile selected by the CLI and [references/orchestrator/orchestrator.md](references/orchestrator/orchestrator.md). The CLI handles authentication, folder headers, OData filters and escaping, pagination, retries, validation errors, and the `Result/Code/Data` contract. Never read `~/.uipath/.auth` or hand-roll a known REST call merely because the endpoint is familiar.

Use `--output json` for programmatic calls. Prefer noun-level server-side filters (`--state`, `--type`, `--status`, `--name`, `--process-name`, or `--search`) so pagination remains correct. Use `--output-filter` with JMESPath only to reshape or select output when no server-side filter is available.

Examples: `uip or bucket-files upload`, `uip or assets create`, `uip or jobs start <process-key>`, `uip is connections create <connector-key>`, and `uip df files upload <entity-id> <record-id> <field-name> --file <path>`. Data Fabric record insert/update silently strips `FILE` values; use dedicated file verbs.

## Scope and Routing

Load this skill before writing code that talks to UiPath. It covers authentication, profiles, tokens, organizations, tenants, Orchestrator folders/resources, Integration Service, Data Fabric, LLM Gateway BYO configurations, AI Trust Layer BYO guardrails, traces, context-grounding indexes, licensing, CLI tools, and MCP. Load [`uipath-solution`](/uipath:uipath-solution) for `uip solution` lifecycle operations (`init`, `pack`, `publish`, `deploy`, `activate`, `upload`) and CI/CD.

### Data Fabric gate

**Before any `uip df` command, read [`references/data-fabric/data-fabric.md`](references/data-fabric/data-fabric.md).** It contains folder-scope prompts, irreversible-operation gates, complex-field configuration, request schemas, operator matrices, and links to [`entity-schema.md`](references/data-fabric/entity-schema.md), [`records-query.md`](references/data-fabric/records-query.md), [`filter-platform-contract.md`](references/data-fabric/filter-platform-contract.md), [`choice-sets.md`](references/data-fabric/choice-sets.md), [`file-attachments.md`](references/data-fabric/file-attachments.md), and [`bulk-import.md`](references/data-fabric/bulk-import.md).

- **Entities:** Respect typed schemas plus `lengthLimit`, `minValue`, `maxValue`, and `decimalPrecision`; evolve schemas with `addFields`, `updateFields`, and `removeFields`.
- **Records:** Insert, update, delete, list, get, and `query` support server-side filters, sorting, pagination, group-by, and `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX`. Filter bodies use `filterGroup.queryFilters[]`.
- **Files:** `FILE` fields require `files upload`, `download`, and `delete`; record writes silently remove file values.
- **Choice sets:** Shared enumerations support `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE`; use immutable integer `NumberId` values, not labels.
- **Folder scope:** Scope may be tenant- or folder-level. Use `--folder-key <GUID>` on every write and `--include-folders` for `entities list` and `choice-sets list`.
- **CSV import:** `uip df records import <entity-id> --file <path.csv> --output json` supports basic types only. Use `records insert --file <json>` for `CHOICE_SET`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` fields.
- Query/Create/Update/Delete/GetById connector nodes inside a `.flow` belong to `uipath-maestro-flow`, which owns node JSON, `bindings_v2.json`, and connection-resource layout.

### LLM Gateway BYO configurations

Use `uip llm-configuration byo-connections` (`list`, `get`, `create`, `update`, `delete`, `list-product-configs`) for tenant-owned OpenAI, Azure OpenAI, AWS Bedrock, Google Vertex, Anthropic, or OpenAI-compatible credentials for supported UiPath features. Use the single-mapping shape for `AnyModelWithOwnAdditions`; use repeated `--mapping` for `AllModels` and `AnyModel`. Server-side validation is mandatory.

For a failing configuration, run `byo-connections get <id> --force-refresh`; force a fresh idempotent probe with `update`; audit with `list --include-connection-details` filtered where `connectionState != Enabled`; check catalog drift with `list-product-configs`; and inspect `uip traces spans get <trace-id>`. The CLI exposes no per-request invocation logs, so use current state and trace evidence. See [`references/llmgateway/byo-connections.md` § Diagnostics](references/llmgateway/byo-connections.md#diagnostics). Tenant-wide AI Trust Layer routing policy may also matter; see [uipath-governance](/uipath:uipath-governance).

### AI Trust Layer BYO guardrails

Use `uip guardrails byo-configurations` (`list`, `list-validators`, `probe`, `create`, `update`, `delete`) for tenant-registered external validator providers backed by Integration Service connections.

`ValidatorName` is tenant-unique and the only agent-facing value (`ByoValidator(<ValidatorName>)`); the connection resolves server-side. Before `create`, list configurations to ensure the name is free and run `uip is connections list` to obtain `--connection-id`. `create` always probes the connection/validator pair, has no skip flag, and saves nothing if probing fails. `update` re-probes when `--connection-id` changes, merges supplied fields, and can enable or disable a configuration. `probe` and `list-validators` do not save. `delete` requires `--force`; there is no `get` verb. See [`references/guardrails/byo-configurations.md`](references/guardrails/byo-configurations.md). Authoring guardrails belongs to [uipath-agents](/uipath:uipath-agents).

## Auth Token Location and Profiles

The default login stores credentials in `~/.uipath/.auth`; named profiles use `~/.uipath/profiles/<name>/.auth`:

```text
UIPATH_URL=https://cloud.uipath.com
UIPATH_ORGANIZATION_NAME=my_org
UIPATH_TENANT_NAME=my_tenant
UIPATH_ACCESS_TOKEN=eyJ...
UIPATH_ORGANIZATION_ID=...
UIPATH_TENANT_ID=...
```

```bash
uip login --profile dev --output json
uip login status --profile dev --output json
uip login which --profile dev --output json
```

- `--profile <name>` is global and must be passed on every command, for example `uip --profile dev or folders list --output json`.
- `default` means the unprofiled login at `~/.uipath/.auth`.
- Profile names may contain only letters, numbers, `.`, `_`, and `-`; never use paths such as `../prod`.
- `--profile` and auth-command `--file <folder>` are mutually exclusive.
- A missing profile never falls back to default auth or Robot credentials; tell the user to run `uip login --profile <name>`.
- With a named profile, obtain its auth path using `uip login which --profile <name> --output json`, not by assuming the default path.

## Quick Start

### Step 1 — Authenticate

Check first:

```bash
uip login status --output json
```

If it reports `Logged in`, continue. There is no `--check` flag; `status` verifies authentication. Check a requested profile explicitly with `uip login status --profile dev --output json`.

Do not run interactive login through an agent shell, with or without `--no-browser`; ask the user to run it directly (in Claude Code, prefix with `!`):

```text
! uip login
```

Then confirm with `uip login status --output json`. `--no-browser` still blocks for the callback and is intended for automation that opens the URL itself; relaying its URL is fragile. A stale callback may cause `EADDRINUSE` or “Port 8104 is already in use”; it releases within five minutes, or the user may end the stale process.

When the environment is a sandbox or not connected to a live tenant, still run the requested read / query / CRUD commands with the parameters given (pass the tenant name verbatim) — they return an auth or `tenant not found` error, which is expected and demonstrates the correct command. Do not abort the task, retry indefinitely, or ask the user to run `uip login` before running the non-`login` commands; only interactive `uip login` itself must be run by the user.

Named login: `uip login --profile dev --output json`.

Custom authority: `uip login --authority "https://alpha.uipath.com/identity_" --it --output json`.

Non-interactive CI/CD login: `uip login --client-id "<ID>" --client-secret "<SECRET>" --tenant "<TENANT>" --output json`.

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

Use the Task Navigation table. For solutions, load [`uipath-solution`](/uipath:uipath-solution).

## Task Navigation

| I need to... | Read these |
|---|---|
| Authenticate / manage tenants | [references/uip-commands.md](references/uip-commands.md) |
| Set up folders, users, machines | [references/orchestrator/setup-environment.md](references/orchestrator/setup-environment.md) |
| Run and monitor jobs | [references/orchestrator/run-jobs.md](references/orchestrator/run-jobs.md) |
| Manage sessions and runtimes | [references/orchestrator/manage-sessions.md](references/orchestrator/manage-sessions.md) |
| Tenant settings, calendars, audit logs | [references/orchestrator/tenant-admin.md](references/orchestrator/tenant-admin.md) |
| Understand Orchestrator concepts | [references/orchestrator/orchestrator.md](references/orchestrator/orchestrator.md) |
| Manage assets | [references/orchestrator/manage-assets.md](references/orchestrator/manage-assets.md) |
| Work with queues and queue items | [references/orchestrator/process-queues.md](references/orchestrator/process-queues.md) |
| Work with storage buckets and files | [references/orchestrator/work-with-storage.md](references/orchestrator/work-with-storage.md) |
| Set up triggers and webhooks | [references/orchestrator/triggers-and-webhooks.md](references/orchestrator/triggers-and-webhooks.md) |
| Develop / pack / publish / deploy / activate solutions; set up CI/CD | [/uipath:uipath-solution](/uipath:uipath-solution) |
| Debug LLM/agent traces | [references/traces/traces.md](references/traces/traces.md) |
| Annotate traces with feedback | [references/traces/feedback.md](references/traces/feedback.md) |
| Use Integration Service | [references/integration-service/integration-service.md](references/integration-service/integration-service.md) |
| Use Data Fabric | [references/data-fabric/data-fabric.md](references/data-fabric/data-fabric.md) |
| Build entity schemas and complex fields | [references/data-fabric/entity-schema.md](references/data-fabric/entity-schema.md) |
| Query records, filters, pagination, aggregates | [references/data-fabric/records-query.md](references/data-fabric/records-query.md) |
| Filter operator support by field type | [references/data-fabric/filter-platform-contract.md](references/data-fabric/filter-platform-contract.md) |
| Manage choice sets and values | [references/data-fabric/choice-sets.md](references/data-fabric/choice-sets.md) |
| Manage record file attachments | [references/data-fabric/file-attachments.md](references/data-fabric/file-attachments.md) |
| Bulk import records from CSV | [references/data-fabric/bulk-import.md](references/data-fabric/bulk-import.md) |
| Configure BYO LLM keys | [references/llmgateway/byo-connections.md](references/llmgateway/byo-connections.md) |
| Diagnose, audit, or re-probe BYO LLM | [references/llmgateway/byo-connections.md#diagnostics](references/llmgateway/byo-connections.md#diagnostics) |
| Manage BYO guardrail configurations | [references/guardrails/byo-configurations.md](references/guardrails/byo-configurations.md) |
| Test a BYOG validator connection | [references/guardrails/byo-configurations.md#validation-and-diagnostics](references/guardrails/byo-configurations.md#validation-and-diagnostics) |
| Diagnose a BYOG configuration | [references/guardrails/byo-configurations.md#validation-and-diagnostics](references/guardrails/byo-configurations.md#validation-and-diagnostics) |
| Allocate licenses to tenants | [references/licensing/tenant-allocations.md](references/licensing/tenant-allocations.md) |
| Assign user/group license bundles | [references/licensing/user-licenses-allocations.md](references/licensing/user-licenses-allocations.md) |
| Report license consumption | [references/licensing/consumables-report.md](references/licensing/consumables-report.md) |
| Understand licensing concepts | [references/licensing/licensing.md](references/licensing/licensing.md) |
| Diagnose licensing symptoms | [references/licensing/diagnose/CAPABILITY.md](references/licensing/diagnose/CAPABILITY.md) |
| Full CLI command reference | [references/uip-commands.md](references/uip-commands.md) |
| Build/run/validate coded workflows | [/uipath:uipath-rpa](/uipath:uipath-rpa) |

## Resolving UiPath Studio

For Studio operations such as creating projects, validating, running workflows, or packing:

1. Check for a running instance:
   ```bash
   rpa-tool list-instances --output json
   ```
2. If none is running, try:
   ```bash
   rpa-tool start-studio --output json
   ```
3. If that fails, ask where the Studio build is located. Never search the entire filesystem automatically. Possible locations include `C:\Program Files\UiPath\Studio` or a development build directory.
4. Pass the supplied path explicitly:
   ```bash
   rpa-tool start-studio --studio-dir "<STUDIO_DIR>" --output json
   ```

## Key Concepts and CLI Output

Platform hierarchy, robot/folder/asset enumerations, command groups, and global options are in [references/platform-concepts.md](references/platform-concepts.md). Command groups include `login`, `or`, `resource`, `is`, `df`, `traces`, `tools`, `mcp`, `codedagent`, and `rpa`; common options include `--output`, `--output-filter`, `--profile`, and `--verbose`.

## Deployment Notes

- Starting jobs requires runtimes. Error 2818 (“no runtimes configured”) means the target folder needs machine templates with Unattended or Development runtimes assigned.
- Solution pack/publish/deploy/activate flows belong to [`uipath-solution`](/uipath:uipath-solution).
- If the CLI lacks an operation, use the Orchestrator REST API with the access token from the active profile; see [references/orchestrator/orchestrator.md - REST API](references/orchestrator/orchestrator.md).

## References

- **[CLI Command Reference](references/uip-commands.md)** — Commands and workflow links
- **[Orchestrator](references/orchestrator/orchestrator.md)** — Concepts, folders, jobs, processes, machines, users
- **[Resources](references/orchestrator/resources.md)** — Assets, queues, buckets, triggers, libraries, webhooks
<!--skill-flavor:solutions-index-row:start-->
- **[Solutions](/uipath:uipath-solution)** — Solution lifecycle (`uip solution init/pack/publish/deploy/activate`)
<!--skill-flavor:solutions-index-row:end-->
- **[Planner](/uipath:uipath-planner)** — PDD/SDD design and multi-skill task planning
- **[Traces — Spans](references/traces/traces.md)** — LLM execution trace observability
- **[Traces — Feedback](references/traces/feedback.md)** — Trace sentiment and comments
- **[Integration Service](references/integration-service/integration-service.md)** — Connectors, connections, activities, resources
- **[Data Fabric](references/data-fabric/data-fabric.md)** — Entity schemas, records, queries, choice sets, files, CSV import, folder scoping
- **[LLM Gateway — BYO Connections](references/llmgateway/byo-connections.md)** — Tenant-owned LLM keys
- **[Guardrails — BYOG Configurations](references/guardrails/byo-configurations.md)** — BYOG management and diagnostics
- **[Licensing](references/licensing/licensing.md)** — Allocations, bundles, consumption, and diagnosis
- **[Coded Workflows](/uipath:uipath-rpa)** — Building coded automation projects

> **Trouble?** If something did not work as expected, use `/uipath-feedback` to send a report.