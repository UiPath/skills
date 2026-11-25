---
name: uipath-platform
description: "UiPath platform ops via the uip CLI — use for ANY task hitting UiPath Cloud / Orchestrator / Studio Web / Integration Service / Data Fabric / LLM Gateway. Load BEFORE writing code calling a UiPath API. Covers auth/OAuth2, folders, assets, queues, buckets, libraries, packages, webhooks, triggers, processes, jobs, machines, robots, users, roles, sessions, calendars, IS connectors/connections/activities, `uip df` entities/records/files/choice-sets, BYO LLM configs/custom connectors, BYOG, context grounding, traces/spans/feedback, licensing, CLI/skills setup. Job metrics→uipath-insights; root-cause/'why did X fail'→uipath-troubleshoot; audit logs/login history→uipath-admin; `uip solution`/.uipx→uipath-solution; PDD/SDD→uipath-planner; .xaml/.cs→uipath-rpa; .flow/Data Fabric flow nodes→uipath-maestro-flow; .bpmn→uipath-maestro-bpmn; agents/`uip eval run`→uipath-agents; Test Manager→uipath-test."
when_to_use: "tenant; ROI; federated/virtual/zero-copy entities/choice sets; fields; insert/query/filter records, group-by/SUM/AVG; CSV/spreadsheet import; own LLM key, model substitution; BYOG; custom connector hooks, probe fails (MALFORMED_RESPONSE/VendorModelNotFound); uipath.com REST, `uip`/Node/npm/Python/.NET missing; local entity/entity in my solution; write/record/query a decision on a trace."
allowed-tools: Bash, Read, Write, Glob, Grep, Skill
---

# UiPath Platform — uip CLI Assistant

Comprehensive guide for UiPath Cloud / Orchestrator / Studio Web / Integration Service, end-to-end via the `uip` CLI. For `uip solution` lifecycle load [`uipath-solution`](/uipath:uipath-solution); for PDD/SDD design & task planning load [`uipath-planner`](/uipath:uipath-planner).

## Route Diagnostic Intent Before Platform Work

Classify the requested **outcome** before running any command:

1. **Causal outcome → hand off immediately.** User wants an explanation, diagnosis, or root cause for undesirable existing behavior → invoke the `Skill` tool with uipath-troubleshoot (name exactly as it appears in your available-skills list) before running anything. No preliminary job/log/trace fetching — troubleshoot owns evidence collection. Prose telling the user to use troubleshoot is not a substitute for the `Skill` call.
2. **Operational outcome → stay here.** Inspect current state without a causal question, perform CRUD or lifecycle actions, validate an input before applying it, or execute an already-diagnosed platform fix.
3. **Mixed request → troubleshoot first.** Hand off the diagnosis; return here only for the platform mutation that applies the confirmed fix.
4. **Sibling unavailable → degrade gracefully.** State the handoff could not run; give the entity, scope, and time window needed to retry the investigation. Do not improvise a platform-only root cause.

<!--skill-flavor:freeze-critical-rule:start-->
## Critical Rules

1. **In a frozen config, fix a freeze refusal without changing the freeze.** A freeze refusal is a `uip` failure with `ErrorCode: configuration_error` while the config has a `versions` block, or one whose `Message` names a freeze, a frozen config or a pin. On one, read [`references/cli-freeze-guide.md`](references/cli-freeze-guide.md) before the next command. Run only the fixes it names: no `--force` and no reinstall of the newest CLI without the user's agreement. Every other failure in a frozen repo (`Not logged in`, a 404, a validation error) is not a freeze refusal: handle it as usual.
<!--skill-flavor:freeze-critical-rule:end-->

## Use the CLI. Don't roll your own REST.

**Always reach for `uip` CLI commands first.** The CLI covers auth, Orchestrator (folders, processes, jobs, machines, users, roles, sessions, calendars, settings, audit logs, credential stores, feeds, attachments), resources (assets, queues, queue items, storage buckets, bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), traces, and licensing end-to-end.

Hand-rolling HTTP calls — fetching a token and POSTing to `/odata/...` or `/orchestrator_/...` — almost always misses something the CLI gets right: the `X-UIPATH-OrganizationUnitId` folder header, OData filter shape (`Key eq '...'` with escaped single quotes), pagination envelope, retry semantics, validation error shape, or `Result/Code/Data` output contract. **Reach for raw REST only after you've searched [`references/uip-commands.md`](references/uip-commands.md) for your task and confirmed no `uip` command covers it.** The CLI is the source of truth.

If you find yourself about to `curl` `https://cloud.uipath.com/...` — stop. Search the command index first. Examples of what people often miss:

- "upload a file to a storage bucket" → `uip or bucket-files upload` (NOT a `PUT /buckets/.../signedUrl` dance)
- "create an asset" → `uip or assets create` (NOT a `POST /odata/Assets`)
- "start a job for a process" → `uip or jobs start <process-key>` (NOT `POST /odata/Jobs/UiPath.Server.Configuration.OData.StartJobs`)
- "configure an Integration Service connection" → `uip is connections create <connector-key>` (NOT a hand-rolled OAuth flow)
- "attach a file to a Data Fabric record" → `uip df files upload <entity-id> <record-id> <field-name> --file <path>` (NOT `records insert` / `records update` with the file value — the platform silently strips FILE columns and returns Success, see `references/data-fabric/data-fabric.md` Rule 6)

## CLI Bootstrap for Fresh Machines

<!--skill-flavor:freeze-bootstrap:start-->
In a repo whose `.uipath/config.json` has `versions.cli`, run the installers below from inside the repo folder: they read the freeze there and put the CLI on its pin.
<!--skill-flavor:freeze-bootstrap:end-->

When `uip --version` fails, Node/npm is missing, or a coding agent needs a workstation prepared for UiPath work, use the official onboarding installers instead of reconstructing package-manager logic. They are idempotent and safe to rerun.

macOS/Linux:

```bash
curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://download.uipath.com/uipath-cli/install.ps1 | iex
```

The installers:

- Ensure Node.js >= 20 and npm.
- Install `@uipath/cli` from public npm.
- Run `uip skills install --no-interactive` so installed AI coding agents (Claude Code, Codex, Gemini CLI, Cursor, etc.) can use the UiPath skills.
- Best-effort install .NET SDK 8.0 and Python 3.11-3.14 for RPA, coded-agent, and tool workflows.

For CI or a CLI-only machine where agent skills and runtimes are not needed, skip them explicitly:

```bash
curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash -s -- --skip-skills --skip-runtimes
```

```powershell
iwr https://download.uipath.com/uipath-cli/install.ps1 -OutFile install.ps1
./install.ps1 -SkipSkills -SkipRuntimes
```

Useful flags: `--skip-node`, `--skip-skills`, `--skip-dotnet`, `--skip-python`, `--skip-runtimes`, `--dry-run` on macOS/Linux; `-SkipNode`, `-SkipSkills`, `-SkipDotnet`, `-SkipPython`, `-SkipRuntimes`, `-DryRun` on Windows. The matching environment variables are `UIP_SKIP_NODE`, `UIP_SKIP_SKILLS`, `UIP_SKIP_DOTNET`, `UIP_SKIP_PYTHON`, `UIP_SKIP_RUNTIMES`, and `UIP_DRY_RUN`.

## When to Use This Skill

Load this skill BEFORE writing any code that talks to UiPath. Specific triggers:

- **CLI bootstrap / workstation setup**: fresh machine, `uip` missing, Node/npm missing, Python or .NET SDK missing, or an LLM coding agent needs UiPath skills installed
- **Auth & tenant**: login, logout, switch tenant, named login profiles via `--profile <name>`, session details (`uip login status`), REST calls the CLI does not cover (`uip api`), organization
- **Orchestrator core**: folders (`list/get/create/edit/move/delete/runtimes`), processes/releases, jobs (`start/stop/logs/traces/healing-data`), packages (`upload/download/versions`), machines, users / roles / sessions (incl. DirectoryUser/DirectoryGroup/DirectoryRobot/DirectoryExternalApplication), licenses, calendars, settings, audit logs, credential stores, feeds, attachments
- **Resources (Orchestrator-scoped)**: assets (text/integer/bool/credential), queues + queue items, storage buckets + bucket files (`upload/download/get-download-url/get-upload-url`), libraries (`.nupkg`), webhooks (HMAC signing), triggers (time/queue/api)
- **Integration Service**: connectors, connections (OAuth flow), activities, IS triggers, agent-workflow reference resolution
- **Data Fabric **: UiPath's structured, typed data store. \*\*⛔ STOP — before ANY `uip df` command, Read [`references/data-fabric/data-fabric.md`](references/data-fabric/data-fabric.md).The reference carries Critical Rules (folder-scope prompt flow, irreversible-op gates, complex-field config), request-body schema, per-type operator matrix, and routes to topic files: [`entity-schema.md`](references/data-fabric/entity-schema.md), [`federated-entity-creation.md`](references/data-fabric/federated-entity-creation.md) (federated / virtual data object / zero-copy entities — backed by a connector or another entity), [`records-query.md`](references/data-fabric/records-query.md), [`filter-platform-contract.md`](references/data-fabric/filter-platform-contract.md), [`choice-sets.md`](references/data-fabric/choice-sets.md), [`file-attachments.md`](references/data-fabric/file-attachments.md), [`bulk-import.md`](references/data-fabric/bulk-import.md), [`local-entities.md`](references/data-fabric/local-entities.md), [`entities-from-schema-guide.md`](references/data-fabric/entities-from-schema-guide.md) (a whole approved entity set from one `entities.json`, by script). Surfaces:
  - **Entities** — schemas with typed columns, per-type constraints (`lengthLimit`, `minValue` / `maxValue`, `decimalPrecision`), choice-set / relationship / file fields, `addFields` / `updateFields` / `removeFields` evolution.
  - **Local entities** — `uip df entities <verb> --local` authors an entity into a solution on disk instead of on the tenant; it becomes a real entity at deploy. No login. Use only when the user explicitly asks for the entity to live in or ship with a solution; tenant is the default. Same field types as tenant entities minus choice sets and relationships. See [`local-entities.md`](references/data-fabric/local-entities.md).
  - **Records** — insert / update / delete / list / get / `query` with server-side filters, sorting, pagination, group-by, and aggregates (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).
    - DF filter body uses `filterGroup.queryFilters[]` — full shape in [`records-query.md`](references/data-fabric/records-query.md).
  - **Files** — binary attachments stored on `FILE`-typed fields via `files upload / download / delete` (record-level writes silently strip FILE values; the dedicated verbs are mandatory).
  - **Choice sets** — shared enumerations consumed by `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` fields; values use immutable integer `NumberId`s, not labels.
  - **Folder scoping** — tenant-level OR folder-scoped via `--folder-key <GUID>` on every write, `--include-folders` on `entities list` / `choice-sets list`.
  - **CSV bulk import** — `uip df records import <entity-id> --file <path.csv> --output json`. Basic field types only; complex fields (CHOICE_SET, RELATIONSHIP, FILE, AUTO_NUMBER) and text holding line breaks or double quotes require `records insert --file <json>`.

  For Query / Create / Update / Delete / GetById connector nodes **inside a `.flow`**, hand off to `uipath-maestro-flow` — that skill owns the in-flow node JSON, `bindings_v2.json`, and connection-resource layout.

- **LLM Gateway — BYO product configurations**: `uip llm-configuration byo-connections` (`list / get / create / update / delete / list-product-configs`). Register tenant-owned OpenAI / Azure OpenAI / AWS Bedrock / Google Vertex / Anthropic / OpenAI-compatible keys against UiPath product features (agents, agenthub, jarvis, IXP, agent builder, ECS). Two input shapes: single-mapping (for `AnyModelWithOwnAdditions` features) and repeated `--mapping` (required for `AllModels` / `AnyModel`). Server-side validation is mandatory.
- **LLM Gateway — diagnose a failing BYO config**: re-probe the underlying IS connection with `byo-connections get <id> --force-refresh`, force a fresh server-side probe with an idempotent `update`, audit the tenant with `list --include-connection-details` filtered on `connectionState != Enabled`, check catalog drift with `list-product-configs`, and cross-reference trace evidence with `uip traces spans get <trace-id>`. The gateway does **not** expose per-request invocation logs via CLI — diagnosis is current-state + trace evidence only. See [`references/llmgateway/byo-connections.md` § Diagnostics](references/llmgateway/byo-connections.md#diagnostics). For tenant-wide AI Trust Layer policy that may be overriding routing, see [uipath-governance](/uipath:uipath-governance).
- **LLM Gateway — BYO LLM custom connector**: when no built-in connector speaks to the customer's LLM endpoint (an in-house gateway, custom auth, a non-standard body), build an Integration Service connector whose pre/post-request hooks bridge the product's API flavor to it, test the unpublished draft, publish it, and save the BYO configuration with `--connector-type Custom`. ⛔ Read [`references/llmgateway/custom-connector/custom-connector-guide.md`](references/llmgateway/custom-connector/custom-connector-guide.md) completely before the first command: its Critical Rules prevent a connector the gateway cannot call.
- **AI Trust Layer — BYO guardrail (BYOG) configurations**: `uip guardrails byo-configurations` (`list / list-validators / probe / create / update / delete`) — manage tenant-registered external guardrail validator providers (e.g. Azure AI Content Safety, Databricks AI Guardrails), each backed by an Integration Service connection. `ValidatorName` is tenant-unique and is the only value agents reference (`ByoValidator(<ValidatorName>)` — the connection resolves server-side). Before creating, `list` (the name must be free) and `uip is connections list` (for `--connection-id`); `create` always probes the connection/validator pair server-side and aborts if the probe fails, with no skip flag, and `update` re-probes whenever `--connection-id` changes. `probe` and `list-validators` test a pairing without saving anything; `update` merges supplied fields and can flip `--enabled`/`--disabled`; `delete` requires `--force`; no `get` verb. See [`references/guardrails/byo-configurations.md`](references/guardrails/byo-configurations.md). For authoring a guardrail against one of these configurations (low-code or coded), see [uipath-agents](/uipath:uipath-agents).
- **Traces**: `uip traces spans get <trace-id>` (LLM/agentic execution observability); `uip traces decisions create|get|list` to write and read decisions on a trace
- **Context grounding**: knowledge indexes for semantic search / RAG — `uip context-grounding` (`list / create` from a bucket or connection `/ ingest / retrieve` to poll ingestion status `/ search / delete`). Agents and flows consume these indexes as tools. See [`references/context-grounding/index-management.md`](references/context-grounding/index-management.md).
- **Platform licensing**: tenant license allocations, user/group bundle assignments, consumables reporting (`uip platform tenants licenses`, `users licenses`, `groups rules`, `licenses consumables get` — the only consumables verb; summary/daily/folders are `--mode` values), per-user consumption and top-ups (`users usage list/get`, `users top-ups create/get/request` — see [`references/licensing/user-usage-topups.md`](references/licensing/user-usage-topups.md)), and folder outcome billing / Fully Loaded Transactions (`tenants folder-outcome-billing get/set` — see [`references/licensing/folder-outcome-billing.md`](references/licensing/folder-outcome-billing.md))
- **CLI tooling itself**: `uip tools list/search/install`, `uip mcp serve`

For `uip solution` lifecycle (init / pack / publish / deploy / activate / upload) and CI/CD pipelines that build and deploy UiPath solutions, load [`uipath-solution`](/uipath:uipath-solution).

## Session Details and REST Authentication

The CLI owns its credentials file. Never read, `cat`, `grep`, or `source` it: it holds the access token and the refresh token, and anything read lands in the conversation.

**Organization, tenant, base URL, expiry** — read them from `uip login status --output json`:

| Field | Value |
|---|---|
| `Data.Status` | Session state, e.g. `Logged in` |
| `Data.BaseUrl` | Cloud base URL, e.g. `https://cloud.uipath.com` |
| `Data.Organization` / `Data.OrganizationId` | Organization name / UUID |
| `Data.Tenant` / `Data.TenantId` | Tenant name / UUID |
| `Data.Identity` | Logged-in user or application |
| `Data.ExpirationDate` | Access-token expiry |

A status other than `Logged in` does not end the task: still run the requested command, then report its result. If it fails with an authentication error, tell the user to run `uip login`.

**REST call the CLI does not cover** — use `uip api`. The CLI adds base URL, organization, tenant and a fresh access token, and prints only the response; the token never reaches the shell or the conversation:

```bash
uip api "orchestrator_/odata/Folders?\$top=1" --output json
uip api "<SERVICE_PATH>" --method POST --input "<BODY_FILE>" --output json
uip api "<SERVICE_PATH>" --level organization --header "x-uipath-tenantid: <TENANT_ID>" --output json
```

| Option | Use |
|---|---|
| `<SERVICE_PATH>` | Path under `<BASE_URL>/<ORG>/<TENANT>` (or `<BASE_URL>/<ORG>` with `--level organization`), e.g. `orchestrator_/odata/Releases?...`. Omit the leading `/` (Git Bash on Windows rewrites it). Never a full URL |
| `--method <METHOD>` | `GET` (default), `POST`, `PUT`, `PATCH`, `DELETE` |
| `--input <FILE>` | Request body; `Content-Type` defaults to `application/json` |
| `--folder-key <FOLDER_KEY>` | Sends `X-UIPATH-FolderKey` |
| `--header "<NAME>: <VALUE>"` | Extra headers (variadic). `Authorization` cannot be set |
| `--output-file <FILE>` | Save body to a file (binary downloads) |

Response: `Data.StatusCode`, `Data.Body` (parsed JSON or text). Non-2xx fails with `Context.HttpStatus` and the service's error in `Data.Body`; `401` exits `2` → ask the user to run `uip login`. If `uip api` is an unknown command, run `uip update`, then retry.

Never extract the access token: no `uip login refresh --output json` for REST, no `curl` with a bearer header, never ask the user to paste a token.

Named profiles keep several UiPath logins on one machine:

```bash
uip login --profile dev --output json
uip login status --profile dev --output json
uip login which --profile dev --output json
```

`uip login which` returns the path of the credentials file behind a login, never its contents. Use it to locate a profile's file; never open the file it names.

Rules:

- `--profile <name>` is a global option. Pass it on every `uip` command that should use that login, for example `uip --profile dev or folders list --output json` and `uip --profile dev api "orchestrator_/odata/Folders" --output json`.
- `default` means the built-in unprofiled login.
- Profile names may contain only letters, numbers, `.`, `_`, and `-`. Never use paths like `../prod`.
- `--profile` and auth-command `--file <folder>` are mutually exclusive. Use one or the other.
- A missing named profile does not fall back to the default login or Robot credentials. Tell the user to run `uip login --profile <name>`.

## Quick Start

### Step 0 — Ensure the CLI Exists

Check first:

```bash
uip --version
```

<!--skill-flavor:freeze-step0-install:start-->
If the command is missing, use the official installer from [CLI Bootstrap for Fresh Machines](#cli-bootstrap-for-fresh-machines), then open a new shell if the installer added PATH entries. In a frozen repo, run the installer from inside the repo folder so it installs the pinned CLI.
<!--skill-flavor:freeze-step0-install:end-->

### Step 1 — Authenticate

Before interacting with Orchestrator, solutions, or Integration Service, the user must be logged in.

**Always check first** — most sessions are already authenticated:

```bash
uip login status --output json
```

If `Data.Status` is `Logged in`, skip the rest of this step. There is no `--check` flag — `status` is the verification subcommand. `Data.Status` alone is the session's state: `uip` renews an expired access token from its refresh token, and reports `Refresh Failed` when that renewal fails and `Expired` when none ran (no refresh token, as with a client-credentials or environment-variable login); `ExpirationDate`, in UTC, is the current access token's.

If the user names a profile, check that profile explicitly:

```bash
uip login status --profile dev --output json
```

**Interactive login (browser OAuth2):** `uip login` opens a browser window on the user's machine and blocks until they complete it. **Never run an interactive login through your own shell tool — with or without `--no-browser`.** Run by an agent, the person who must sign in sees only a spinner: the printed URL and the blocking wait live in your tool output, not in front of them. `--no-browser` does not make the command agent-runnable — it exists for automation that opens the URL _itself_; it still blocks until the sign-in callback arrives, and relaying the printed URL by copy/paste is fragile (a line-wrapped or truncated copy is rejected by the identity server with an opaque browser-side error). Instead, ask the user to run the command directly in their own terminal — in Claude Code, prefixing it with `!` runs it inside the session:

```text
! uip login
```

Then confirm with `uip login status --output json` once they say it's done. If a retry fails with `EADDRINUSE` / "Port 8104 is already in use", an abandoned earlier attempt is still holding the callback port — it releases itself within 5 minutes, or the user can end the stale `uip login` process.

For a named interactive login:

```bash
uip login --profile dev --output json
```

For a custom authority (Automation Suite, dedicated, or other non-default host):

```bash
uip login --authority "<AUTHORITY_URL>" --it --output json
```

For non-interactive (CI/CD) scenarios, use client credentials read from environment variables with the CLI's `env.<NAME>` syntax. Never ask the user to paste the secret into chat or put it on the command line:

```bash
uip login --client-id env.UIPATH_CLIENT_ID --client-secret env.UIPATH_CLIENT_SECRET --tenant "<TENANT>" --output json
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

**Confirm the target and its key with the user before any delete, unless the user authorized that exact delete.** This covers every `delete` command in the references; Data Fabric deletes keep the stricter gate in [`data-fabric.md`](references/data-fabric/data-fabric.md) (Destructive Operations).

## Task Navigation

| I need to...                                                                                                             | Read these                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Authenticate / manage tenants**                                                                                        | [references/uip-commands.md](references/uip-commands.md)                                                                                                     |
| **Set up folders, users, machines**                                                                                      | [references/orchestrator/setup-environment.md](references/orchestrator/setup-environment.md)                                                                 |
| **Give a user or robot account access (pick a standard role)**                                                           | [references/orchestrator/choose-roles.md](references/orchestrator/choose-roles.md)                                                                           |
| **Offer or plan publish → schedule → run end to end (check robots first)**                                               | [references/orchestrator/end-to-end-readiness-guide.md](references/orchestrator/end-to-end-readiness-guide.md)                                               |
| **Run and monitor jobs**                                                                                                 | [references/orchestrator/run-jobs.md](references/orchestrator/run-jobs.md)                                                                                   |
| **Manage sessions and runtimes**                                                                                         | [references/orchestrator/manage-sessions.md](references/orchestrator/manage-sessions.md)                                                                     |
| **Tenant settings, calendars, audit logs**                                                                               | [references/orchestrator/tenant-admin.md](references/orchestrator/tenant-admin.md)                                                                           |
| **Understand Orchestrator concepts**                                                                                     | [references/orchestrator/orchestrator.md](references/orchestrator/orchestrator.md)                                                                           |
| **Manage assets**                                                                                                        | [references/orchestrator/manage-assets.md](references/orchestrator/manage-assets.md)                                                                         |
| **Work with queues and queue items**                                                                                     | [references/orchestrator/process-queues.md](references/orchestrator/process-queues.md)                                                                       |
| **Set or read Business ROI for a process or queue**                                                                      | [references/orchestrator/business-roi.md](references/orchestrator/business-roi.md)                                                                           |
| **Work with storage buckets and files**                                                                                  | [references/orchestrator/work-with-storage.md](references/orchestrator/work-with-storage.md)                                                                 |
| **Set up triggers and webhooks**                                                                                         | [references/orchestrator/triggers-and-webhooks.md](references/orchestrator/triggers-and-webhooks.md)                                                         |
| **Poll jobs / queue items, export logs, handle a 429, or check field size caps**                                         | [references/orchestrator/api-limits.md](references/orchestrator/api-limits.md)                                                                               |
| **Develop / pack / publish / deploy / activate solutions; set up CI/CD**                                                 | [/uipath:uipath-solution](/uipath:uipath-solution)                                                                                                           |
| **Run runtime evals on a published agent**                                                                               | [/uipath:uipath-agents](/uipath:uipath-agents)                                                                                                               |
| **Debug LLM/agent traces (spans)**                                                                                       | [references/traces/traces.md](references/traces/traces.md)                                                                                                   |
| **Annotate traces with feedback**                                                                                        | [references/traces/feedback.md](references/traces/feedback.md)                                                                                               |
| **Write or query decisions on a trace**                                                                                  | [references/traces/decisions.md](references/traces/decisions.md)                                                                                             |
| **Use Integration Service**                                                                                              | [references/integration-service/integration-service.md](references/integration-service/integration-service.md)                                               |
| **Use Data Fabric — entities, records, files, choice sets**                                                              | [references/data-fabric/data-fabric.md](references/data-fabric/data-fabric.md)                                                                               |
| **Build an entity schema / add fields / complex field types**                                                            | [references/data-fabric/entity-schema.md](references/data-fabric/entity-schema.md)                                                                           |
| **Create / update a federated entity (a.k.a. virtual data object / zero-copy) from a connector or another entity** | [references/data-fabric/federated-entity-creation.md](references/data-fabric/federated-entity-creation.md)                                                   |
| **Author an entity into a solution (`entities … --local`)**                                                              | [references/data-fabric/local-entities.md](references/data-fabric/local-entities.md)                                                                         |
| **Create an approved entity set (choice sets, natives, federated) from one `entities.json`** | [references/data-fabric/entities-from-schema-guide.md](references/data-fabric/entities-from-schema-guide.md) |
| **Query records — filters, pagination, aggregates, choice/relationship semantics**                                       | [references/data-fabric/records-query.md](references/data-fabric/records-query.md)                                                                           |
| **Filter operator support matrix per field type**                                                                        | [references/data-fabric/filter-platform-contract.md](references/data-fabric/filter-platform-contract.md)                                                     |
| **Manage choice sets and choice-set values**                                                                             | [references/data-fabric/choice-sets.md](references/data-fabric/choice-sets.md)                                                                               |
| **Upload / download / delete file attachments on records**                                                               | [references/data-fabric/file-attachments.md](references/data-fabric/file-attachments.md)                                                                     |
| **Bulk import records from CSV**                                                                                         | [references/data-fabric/bulk-import.md](references/data-fabric/bulk-import.md)                                                                               |
| **Configure BYO LLM keys (OpenAI / Azure OpenAI / Bedrock / Vertex / Anthropic)**                                        | [references/llmgateway/byo-connections.md](references/llmgateway/byo-connections.md)                                                                         |
| **Diagnose / audit / re-probe a BYO LLM configuration**                                                                  | [references/llmgateway/byo-connections.md#diagnostics](references/llmgateway/byo-connections.md#diagnostics)                                                 |
| **Build / test / publish / change a BYO LLM custom connector for a customer LLM endpoint (hooks, probes, `--connector-type Custom`)** | [references/llmgateway/custom-connector/custom-connector-guide.md](references/llmgateway/custom-connector/custom-connector-guide.md) |
| **Manage BYO guardrail (BYOG) configurations (list/create/update/delete)**                                               | [references/guardrails/byo-configurations.md](references/guardrails/byo-configurations.md)                                                                   |
| **Test whether a connection can serve a BYOG validator (probe / list-validators)**                                       | [references/guardrails/byo-configurations.md#validation-mandatory-before-save](references/guardrails/byo-configurations.md#validation-mandatory-before-save) |
| **Diagnose a BYO guardrail (dead connection, disabled config)**                                                          | [references/guardrails/byo-configurations.md#diagnostics](references/guardrails/byo-configurations.md#diagnostics)                                           |
| **Allocate licenses to tenants**                                                                                         | [references/licensing/tenant-allocations.md](references/licensing/tenant-allocations.md)                                                                     |
| **Assign user/group license bundles**                                                                                    | [references/licensing/user-licenses-allocations.md](references/licensing/user-licenses-allocations.md)                                                       |
| **Report on license consumption**                                                                                        | [references/licensing/consumables-report.md](references/licensing/consumables-report.md)                                                                     |
| **See a user's consumption, grant or request a top-up**                                                                  | [references/licensing/user-usage-topups.md](references/licensing/user-usage-topups.md)                                                                       |
| **Turn outcome billing (Fully Loaded Transactions) on or off for a folder**                                              | [references/licensing/folder-outcome-billing.md](references/licensing/folder-outcome-billing.md)                                                             |
| **Understand licensing concepts**                                                                                        | [references/licensing/licensing.md](references/licensing/licensing.md)                                                                                       |
| **Diagnose a licensing symptom**                                                                                         | [references/licensing/diagnose/CAPABILITY.md](references/licensing/diagnose/CAPABILITY.md)                                                                   |
| **Full CLI command reference**                                                                                           | [references/uip-commands.md](references/uip-commands.md)                                                                                                     |
| **Bootstrap `uip`, Node, Python, .NET, and agent skills**                                                                | [CLI Bootstrap for Fresh Machines](#cli-bootstrap-for-fresh-machines)                                                                                        |
<!--skill-flavor:freeze-nav-row:start-->
| **Fix a command refused by a frozen config (`uip config freeze`)**                                                       | [references/cli-freeze-guide.md](references/cli-freeze-guide.md)                                                                                             |
<!--skill-flavor:freeze-nav-row:end-->
| **Build/run/validate coded workflows**                                                                                   | [/uipath:uipath-rpa](/uipath:uipath-rpa)                                                                                                                     |

## Resolving UiPath Studio

Some operations (creating projects, validating, running workflows, packing) require UiPath Studio. When Studio is needed:

1. **Check for a running instance first:**

   ```bash
   uip rpa instances list --output json
   ```

2. **If no instance is running, try the standard install location:**

   ```bash
   uip rpa studio start --output json
   ```

3. **If that fails (version too old, not found, etc.) — ASK THE USER where their Studio build is located.** Do NOT search the entire filesystem. Common locations include:
   - `C:\Program Files\UiPath\Studio`
   - A dev build directory (e.g., `dev4/Studio/Output/bin/Debug`)
   - A custom install path

4. **Once you have the path, pass it explicitly:**
   ```bash
   uip rpa studio start --studio-dir "<STUDIO_DIR>" --output json
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

| Type           | Description                                                        | Use Case                                                 |
| -------------- | ------------------------------------------------------------------ | -------------------------------------------------------- |
| **Attended**   | Runs alongside a human user, triggered via UiPath Assistant        | Front-office tasks, user-assisted automation             |
| **Unattended** | Runs autonomously in virtual environments, managed by Orchestrator | Back-office tasks, scheduled processing, 24/7 operations |

### Folder Types

| Type              | Description                                  |
| ----------------- | -------------------------------------------- |
| **Standard**      | Default folder for organizing automations    |
| **Personal**      | User-specific workspace                      |
| **Virtual**       | Logical grouping without physical separation |
| **Solution**      | Folder created by solution deployment        |
| **DebugSolution** | Debug variant of a solution folder           |

### Asset Types

| Type                     | Description                |
| ------------------------ | -------------------------- |
| **Text**                 | Plain text value           |
| **Bool**                 | Boolean (true/false)       |
| **Integer**              | Numeric integer value      |
| **Credential**           | Username + password pair   |
| **Secret**               | Encrypted secret value     |
| **DBConnectionString**   | Database connection string |
| **HttpConnectionString** | HTTP connection string     |
| **WindowsCredential**    | Windows credential pair    |

## CLI Overview

The UiPath CLI (`uip`) is a unified command-line tool for interacting with the UiPath platform:

| Command Group           | Prefix            | Description                                                                                                       | Status    |
| ----------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------- | --------- |
| **Authentication**      | `login`, `logout` | OAuth2, client credentials, PAT, tenant management                                                                | Available |
| **Orchestrator**        | `or`              | Folders, jobs, processes, packages, machines, users, assets, queues, queue items, buckets, bucket files, triggers | Available |
| **Integration Service** | `is`              | Connectors, connections, activities, resources                                                                    | Available |
| **Data Fabric**         | `df`              | Entities, records, files, choice sets (`@uipath/data-fabric-tool`)                                                | Available |
| **Tools**               | `tools`           | CLI tool extension management                                                                                     | Available |
| **MCP**                 | `mcp`             | Model Context Protocol server                                                                                     | Available |
| **Coded Agents**        | `codedagent`      | Coded agent lifecycle (setup, init, run, eval, pack, publish, deploy)                                             | Available |
| **RPA**                 | `rpa`             | RPA workflow management (create, compile, validate, execute)                                                      | Available |

> Assets, queues, queue items, buckets and bucket files are Orchestrator groups: `uip or assets`, `uip or queues`, `uip or queue-items`, `uip or buckets` and `uip or bucket-files`. The CLI has no separate `resource` group for them.

### Global Options

Every `uip` command accepts:

| Option                         | Description                                                     | Default                                    |
| ------------------------------ | --------------------------------------------------------------- | ------------------------------------------ |
| `--output <format>`            | Output format: `table`, `json`, `yaml`, `plain`, `markdown`     | `json` (`UIP_DEFAULT_OUTPUT` overrides it) |
| `--output-filter <expression>` | JMESPath expression to filter JSON output                       | --                                         |
| `--profile <name>`             | Use a named auth profile from `~/.uipath/profiles/<name>/.auth` | built-in default login                     |
| `--log-level <level>`          | Log level: `debug`, `info`, `warn`, `error`                     | `warn`                                     |
| `--log-file <path>`            | Write logs to a file instead of stderr                          | stderr                                     |
| `--help` / `-h`                | Display help for the command                                    | --                                         |
| `--version` / `-v`             | Display CLI version                                             | --                                         |

> **Always use `--output json`** when calling `uip` commands programmatically. JSON is compact and machine-readable.
>
> **To narrow `list` results, use the noun's own filter flag** (`--state Faulted`, `--type Text`, `--status New`, `--name`, `--process-name`, `--search`). The backend filters before sending; pagination stays correct. Per-noun flags: [references/uip-commands.md](references/uip-commands.md). Never list-everything-then-filter-mentally.
>
> **Use `--output-filter` (JMESPath) for output reshaping** or for fields with no server-side flag — e.g., `--output-filter "[].{id: Id, name: Name}"`, or filtering by a derived/computed value. Don't reach for it when the server already has a filter for that attribute. When the command has a `--limit` option, always pass it with `--output-filter`: the filter sees only the rows one call fetched, so the CLI refuses `--output-filter` when `--limit` falls back to its default. A command with no `--limit` option (such as `uip is connections list`) takes none, so omit it. To search a whole Orchestrator list, use `--limit 1000` (the most a `uip or` list accepts; `uip or queue-items list` takes at most 100) and repeat with `--offset` while `Pagination.HasMore` is `true`. Two things make a filter silently return nothing, since JMESPath reports no match and no error for either. The expression is evaluated against the `Data` payload, so it starts inside `Data` and never names it: write `[].Key`, never `Data[].Key`, which looks for a `Data` key inside `Data`. And field lookups are case-sensitive against keys the CLI PascalCases before filtering: match `DisplayName`, not `displayName`, unless the command is one of the few that preserves its raw casing (`maestro flow registry get`, `api-workflow registry`, conversational commands).

## Deployment Notes

- **Starting jobs requires runtimes — check before you offer.** Before proposing to publish, schedule or run anything, check the target folder's runtimes and tell the user which stages can and cannot complete ([end-to-end-readiness-guide.md](references/orchestrator/end-to-end-readiness-guide.md)). Error 2818 "no runtimes configured" means the folder needs machine templates with Unattended/Development runtimes assigned.
- **For `uip solution` pack / publish / deploy / activate flows, load [`uipath-solution`](/uipath:uipath-solution).** This skill owns the auth and Orchestrator surface those flows depend on; the solution skill owns the lifecycle commands.
- **Fallback: direct REST API.** When CLI tools don't support an operation, use the Orchestrator REST API through `uip api` ([Session Details and REST Authentication](#session-details-and-rest-authentication)). See [references/orchestrator/orchestrator.md - REST API](references/orchestrator/orchestrator.md).
- **Orchestrator rate-limits some endpoints per tenant.** Filtered `jobs list` / `queue-items list` calls are budgeted per minute, and `--export` on `jobs logs` / `audit-logs list` has a quota of 100 per day. The CLI does not retry a 429 (`ErrorCode: rate_limited`). Read [references/orchestrator/api-limits.md](references/orchestrator/api-limits.md) before writing any poller, loop or script over these commands.

## References

- **[CLI Command Reference](references/uip-commands.md)** — Every `uip` command with workflow links
- **[Orchestrator](references/orchestrator/orchestrator.md)** — Concepts, folders, jobs, processes, machines, users
- **[Resources](references/orchestrator/resources.md)** — Assets, queues, buckets, triggers, libraries, webhooks
- **[Orchestrator API Limits](references/orchestrator/api-limits.md)** — Per-tenant rate limits, export quotas, 429 handling, field size caps
<!--skill-flavor:solutions-index-row:start-->
- **[Solutions](/uipath:uipath-solution)** — Solution lifecycle (`uip solution init/pack/publish/deploy/activate`)
<!--skill-flavor:solutions-index-row:end-->
- **[Planner](/uipath:uipath-planner)** — PDD/SDD design + multi-skill task planning (Process → Solution Design Document → task list)
- **[Traces — Spans](references/traces/traces.md)** — LLM execution trace observability
- **[Traces — Feedback](references/traces/feedback.md)** — Annotate traces with sentiment and comments
- **[Traces — Decisions](references/traces/decisions.md)** — Write and query decisions recorded against a trace
- **[Integration Service](references/integration-service/integration-service.md)** — Connectors, connections, activities, resources
- **[Data Fabric](references/data-fabric/data-fabric.md)** — Entity schemas, records CRUD, query filters and aggregates, choice sets, file attachments, CSV bulk import, folder scoping, [local entities](references/data-fabric/local-entities.md)
- **[LLM Gateway — BYO Connections](references/llmgateway/byo-connections.md)** — Register tenant-owned LLM keys against UiPath products
- **[LLM Gateway — BYO Custom Connector](references/llmgateway/custom-connector/custom-connector-guide.md)** — Build, test and publish an Integration Service connector that bridges a product's LLM API to a customer endpoint, then save its BYO configuration
- **[Guardrails — BYOG Configurations](references/guardrails/byo-configurations.md)** — Manage tenant-registered bring-your-own guardrail (BYOG) configurations and diagnose their underlying Integration Service connections
- **[Licensing](references/licensing/licensing.md)** — Tenant allocations, user/group bundles, consumables reporting, [diagnose](references/licensing/diagnose/CAPABILITY.md)
- **[Coded Workflows](/uipath:uipath-rpa)** — Building coded automation projects

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
