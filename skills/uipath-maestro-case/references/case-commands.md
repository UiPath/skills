# uip — Surviving CLI Command Reference

`caseplan.json` mutations are direct file edits, not CLI calls. The commands below are the only `uip` invocations the skill issues — read-only metadata fetches, registry discovery, validation, debug, runtime/instance management, and solution scaffold/upload.

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

## Local vs cloud commands

`caseplan.json` mutations are direct file edits (Read + Write/Edit). CLI is used only for the operations below:

| Commands | What | Auth |
|----------|------|------|
| `solution init`, `solution projects add`, `solution resources refresh`, `solution upload` | Solution scaffold + resource sync + Studio Web upload | Yes (for `upload`) |
| `solution resources add --source local\|remote`, `solution resources remove <key>`, `solution resources edit <key>` | Atomic single-resource mutations (local stub or remote import; delete by key; patch spec via `--patch '<json>'`) — see [uipath-solution Step 9–11](/uipath:uipath-solution) | Only `--source remote` requires auth; `remove`/`edit` are offline |
| `registry pull/list/search`, `get-connector`, `get-connection`, `tasks describe`, `is resources/triggers describe` | Registry + metadata discovery (read-only) | Yes (for `pull`) |
| `validate` | Validate `caseplan.json` | No |
| `instance`, `processes`, `incidents`, `process run`, `job traces`, `debug` | Query/manage live Orchestrator state | Yes |

---

## uip solution init

Create a new solution directory + `.uipx` file.

```bash
uip solution init <SolutionName>
```

| Flag | Description |
|------|-------------|
| `<SolutionName>` | **(required)** Solution name |

Creates `<SolutionName>/` with `<SolutionName>.uipx` inside. The `case` plugin's § Scaffold writes the project files separately.

---

## uip maestro case init

Scaffold a basic Case project with the 5 boilerplate files and a starter `caseplan.json`. Use this for a blank case scaffold without an `sdd.md` (the SDD-driven JSON path writes the same files in a single plugin invocation — see [plugins/case/impl-json.md](plugins/case/impl-json.md)).

```bash
cd <SolutionDir> && uip maestro case init <ProjectName>
```

| Flag | Description |
|------|-------------|
| `<ProjectName>` | **(required)** Project directory name. Created inside the current directory |

> **The `cd <SolutionDir>` is mandatory; `&&`-chaining after `uip solution init` does NOT satisfy it.** `solution init` makes `<SolutionDir>` a *child* of cwd, so `uip solution init X && uip maestro case init X` still runs `case init` outside the new solution — with the auto-scaffold consequences described below.

`case init` always lands the project inside a solution. Run **from inside the solution directory** so the layout is `<SolutionDir>/<ProjectName>/` — it then auto-registers the project with the parent `.uipx` (`Data.SolutionRegistration.Status`: `Registered` or `AlreadyRegistered`). Run **outside any solution** and `case init` auto-scaffolds one: it creates `<ProjectName>Solution/<ProjectName>Solution.uipx`, nests the project at `<ProjectName>Solution/<ProjectName>/`, adds `Data.AutoCreatedSolution` (`{ Name, Path, SolutionFile }`), and reports `Status: Registered`. Pass `--skip-solution-registration` to opt out of **both** auto-scaffold and registration — the project lands at the bare `<ProjectName>/` path with `Status: OptedOut`. If a **non-empty** directory already exists at the path you typed, init warns and leaves it untouched — the project still lands in `<ProjectName>Solution/<ProjectName>/`, not the existing directory. Use `uip solution projects add ./<ProjectName>` as a fallback only when `Status` is `Skipped` (ambiguous discovery) or `Failed` (`.uipx` write error). Note: the SKILL's standard JSON-authoring path (see `plugins/case/impl-json.md`) does not invoke `case init` and still requires the explicit `solution projects add` step — see `implementation.md` § Step 6.

---

## uip solution projects add

Register a project with an existing solution. Used in two scenarios in this skill:

1. **Standard SKILL path** — after the case plugin (T01 in `impl-json.md`) writes `project.uiproj` directly via JSON authoring without invoking `case init`, the project is not auto-registered, so this command is required (see `implementation.md` § Step 6.0b).
2. **Fallback for `uip maestro case init`** — when `case init` returns `Data.SolutionRegistration.Status` of `Skipped` or `Failed`, run this manually to wire the project in. When `case init` returns `Registered` or `AlreadyRegistered` (the normal outcome both inside a solution and when it auto-scaffolds one outside), this command is redundant. When it returns `OptedOut` (`--skip-solution-registration` was passed), both auto-scaffold and registration were skipped intentionally — run this only if you later decide to register.

```bash
uip solution projects add <ProjectName> <SolutionName>.uipx
```

| Flag | Description |
|------|-------------|
| `<ProjectName>` | **(required)** Project directory name (must already exist with `project.uiproj`) |
| `<SolutionName>.uipx` | **(required)** Path to the solution `.uipx` |

Adds the project to `.uipx.Projects[]`. Run after `project.uiproj` exists.

---

## uip solution resources refresh

Re-scan all projects in the solution and sync resource declarations from `bindings_v2.json`. Creates new resources for bindings not yet in the solution, imports from Orchestrator when a matching resource exists.

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```

> `--solution-folder` is required when invoking from outside the solution directory. Omit the flag (and run from inside the solution dir) only for ad-hoc local use; the skill always passes it explicitly so the cwd doesn't matter.

**Always run before `uip solution upload` or `uip maestro case debug`.** Without this step, connection resources may not be registered on Studio Web ("Resource is not configured" warning).

> Requires `bindings_v2.json` to be populated. If still the empty scaffold (`resources: []`), no resources will be synced.

---

## uip solution upload

Upload a solution directly to Studio Web. **Requires `uip login`.**

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory (the folder containing the `.uipx` file) directly — no intermediate bundling step. Uploads to Studio Web where the user can visualize, inspect, edit, and publish the case from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, run `resource refresh` then `uip solution upload <SolutionDir>`. Share the resulting URL with the user.

---

## uip maestro case pack

Pack a Case project directory into a `.nupkg` file. Only used when the user explicitly requests Orchestrator deployment via `uip solution publish` — not the default publish path.

```bash
uip maestro case pack <project-path> <output-path>
uip maestro case pack ./my-case-project ./dist --name MyCase --version 2.0.0
```

| Flag | Description |
|------|-------------|
| `<project-path>` | **(required)** Path to the Case project directory |
| `<output-path>` | **(required)** Output directory for the `.nupkg` |
| `-n, --name <name>` | Package name (default: project folder name) |
| `-v, --version <version>` | Package version (default: `1.0.0`) |

> `pack` + `uip solution publish` deploys directly to Orchestrator — bypasses Studio Web. Default publish path is `uip solution upload`.

---

## uip maestro case validate

Validate a case management JSON file against case management rules.

```bash
# full mode — Phase 4, and the Phase 2 gate on every CLI shipping today
uip maestro case validate <file> --output json
# narrower Phase 2 gate profile — not in any released CLI yet; probed for, adopted when it lands
uip maestro case validate <file> --skeleton-v2 --output json
# legacy structural profile — never the Phase 2 gate (skips rules + SLA)
uip maestro case validate <file> --skeleton --output json
```

| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--skeleton-v2` | **Preferred profile for the Phase 2 gate.** Structural checks (nodes, edges, identity, types) **plus** entry/exit rules, SLAs, and escalations. Skips task input `value` binding and connector task schemas. Matches what Phase 2 writes. **Not in any published CLI as of uip 1.199 — treat full mode as the working default until it ships.** |
| `--skeleton` | **Legacy skeleton profile.** Structural checks only. Skips tasks, SLAs, escalations, and entry/exit rules. Never the Phase 2 gate profile — it omits exactly what Phase 2 writes. |

Output: `{ File, Status: "Valid" }` on success. Errors and warnings are reported inline.

### Phase 2 gate profile — probe once, cache, fall back to FULL mode

The Phase 2 gate needs a profile that checks conditions and SLA. Two do: `--skeleton-v2` (once it ships) and plain **full mode**. Legacy `--skeleton` does not, so it is never the fallback.

Resolve the profile at the gate validate and cache the answer in reasoning. There is normally one gate call per build, so the cache matters only on a re-entered or resumed run — never probe twice.

1. Run with `--skeleton-v2`.
2. **Supported** — the command validated: envelope has `"Code": "CaseValidate"` (success), or any envelope whose `ErrorCode` is `"unknown_error"` (it ran and reported a problem — `Instructions` usually carries `[error]` / `[warning]` lines, but a plain message like `File not found` is the same branch). Cache `profile = skeleton-v2`.
3. **Unsupported — the default branch.** Anything that does not match step 2 is treated as unsupported. Typically `"ErrorCode": "invalid_argument"`, a `Message` containing `unknown option`, or exit code 3. Re-run **once** with **no profile flag** (full mode). Cache `profile = full`. **Do not log an issue** — until `--skeleton-v2` ships this is the normal path, and the logging schema's `WARNING` severity would misdescribe it. Naming the profile in the summary line is the whole disclosure.
4. **Neither works** — full mode also fails to produce a parseable envelope. Cache `profile = none`, skip the gate, continue. The gate is advisory; its absence never halts a build.

**Discriminate on the failure envelope, not on `Code`.** The three real shapes:

| Outcome | Envelope | Exit |
|---|---|---|
| Valid | `{"Result":"Success","Code":"CaseValidate","Data":{…,"Status":"Valid"}}` | 0 |
| Found errors | `{"Result":"Failure","Message":"Validation failed for <path>","Instructions":"Found N error(s)…\n  - [error] …","ErrorCode":"unknown_error"}` — **no `Code` field** | 1 |
| Flag unsupported | `{"Result":"ValidationError","ErrorCode":"invalid_argument","Message":"error: unknown option '--skeleton-v2'…"}` | 3 |

Two traps here. A genuine validation failure carries **no** `Code` field, so testing for `Code == "CaseValidate"` misses the case it looks like it covers. And the unsupported-flag envelope's `Result` is literally `"ValidationError"` — do **not** read that as "the profile ran and found problems." Test `ErrorCode`: `invalid_argument` means the flag is unsupported; `unknown_error` means it validated and found real errors.

**Full mode is a safe gate profile — it does not false-positive on Phase 2 state.** Verified on uip 1.199: a complete Phase-2 caseplan returns `Status: Valid` with a connector task carrying only `typeId` + `connectionId` and no `data.inputs`, non-connector tasks with `value: ""`, root `slaRules` + escalation, an `sla-status-change` entry rule, and stub `wait-for-connector` rules. Full mode also catches the rule defects `--skeleton` reports as `Valid` — a dangling `selectedStageId` (`[error] Entry rule … stage selection invalid`) and an all-`marksCaseComplete:false` case (`[error] Case has no completion rules`). So the fallback loses nothing at the gate; it only spends a little more validation work.

**Name the resolved profile in every user-visible summary line:**

| Profile | Summary line |
|---|---|
| `skeleton-v2` | `Validate (skeleton-v2): <N> errors, <M> warnings — structure, conditions, and SLA checked. Task input values and connector schemas are checked at Phase 4.` |
| `full` | `Validate (full mode — skeleton-v2 unavailable on this CLI): <N> errors, <M> warnings — structure, conditions, and SLA checked.` |
| `none` | `Validate unavailable — structure, conditions, and SLA are all checked at Phase 4.` |

Both working profiles check the rules, so neither line needs a coverage caveat. Legacy `--skeleton` is not one of them and is never the gate profile.

---

## uip maestro case debug

Debug a Case JSON file via a Studio Web debug session. **Requires `uip login`. Executes the case for real — sends emails, posts messages, calls APIs. Only run on explicit user consent.**

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip maestro case debug <project-path> --log-level debug --output json
```

> **Always run `uip solution resources refresh`** on the solution directory before debug.

| Flag | Description |
|------|-------------|
| `<project-path>` | **(required)** Path to the case project directory (must contain `project.uiproj`) |
| `--folder-id <id>` | Orchestrator folder ID (`OrganizationUnitId`). Auto-detected if omitted. |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` (default: `json`) |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

---

## uip maestro case spec

Read-only unified metadata + scaffold endpoint for connector activities and triggers. **The preferred command for connector tasks** — replaces the legacy `case tasks describe` + `is resources describe` two-call dance with a single normalized response (identity, connection, inputs, outputs, filter, references, and a populated `caseShape` ready for `caseplan.json`).

```bash
# Planning phase — lean response (no caseShape payload)
uip maestro case spec --type <activity|trigger> \
  --activity-type-id <uiPathActivityTypeId> \
  --connection-id <uuid> \
  --skip-case-shape --output json

# Phase 3 (implementation) — populated caseShape from --input-details
uip maestro case spec --type <activity|trigger> \
  --activity-type-id <uiPathActivityTypeId> \
  --connection-id <uuid> \
  --input-details '<json>' --output json
```

| Flag | Description |
|------|-------------|
| `--type <activity\|trigger>` | **(required)** Whether the typeId is an activity or trigger TypeCache entry. |
| `--activity-type-id <uuid>` | **(required)** Studio Web `uiPathActivityTypeId` from the relevant TypeCache index. |
| `--connection-id <uuid>` | **(required)** IS connection UUID. Pick from `case registry get-connection` first. |
| `--object-name <name>` | Override the typecache `objectName`. Required in two cases: (1) **entity-typed Curated triggers** whose typecache stores a placeholder (e.g. Data Service `{tenantEntityName\|folderEntityName}`); (2) **Generic-typed activities/triggers** (activity typecache `activityType === "Generic"`; trigger typecache `activityType === "GenericTrigger"`) whose typecache definition is shared across every object the connector exposes (e.g. Salesforce `InsertRecord` covering Account/Contact/Lead/...). The CLI errors at spec-fetch time when missing in case (2) — opaque `unknown_error`, see [`connector-trigger-common.md`](connector-trigger-common.md). Discovery: `uip is resources list/describe` (Generic) or `uip is triggers objects` (entity-typed Curated). See [`connector-integration.md`](connector-integration.md) and [`connector-trigger-common.md`](connector-trigger-common.md). |
| `--skip-case-shape` | Omit `caseShape` from the response. Use during planning for a leaner payload. Mutually exclusive with `--input-details`. |
| `--input-details <json>` | Pre-fill values into the generated `caseShape`. Activity accepts `{bodyParameters?, queryParameters?, pathParameters?, filter?}`; trigger accepts `{eventParameters?, filter?}`. Connection identity is NOT in input — derived from `--connection-id` and TypeCache. Mutually exclusive with `--skip-case-shape`. Full contract: [`case-spec-input-details.md`](case-spec-input-details.md). |

Returns a `ConnectorTaskSpec` with `identity`, `operation`, `connection`, `inputs`, `outputs`, optional `filter`, `essentialConfiguration`, `references[]` (with pre-built `discoverCommand` strings), `diagnostics`, and (when `--skip-case-shape` is NOT set) `caseShape` with FE-canonical inputs/outputs/context arrays. Webhook URL is intentionally NOT in the output (deterministic from `connectionId` + `elementInstanceId` + `connectorKey` + `eventOperation`); fetch via `getWebhookConfig` for the rare flow that needs it. Filter trees inside `--input-details.filter` compile to CEQL (activity) or JMESPath (trigger) per [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

---

## uip maestro case tasks describe

Read-only metadata fetch for a task type's input/output schema. Used during planning + Phase 2 Step 9 execution for **non-connector tasks** (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`). For connector tasks, use [`uip maestro case spec`](#uip-maestro-case-spec) instead.

```bash
uip maestro case tasks describe --type <type> --id <id> --output json
uip maestro case tasks describe --type process --id <entityKey>
uip maestro case tasks describe --type connector-activity --id <typeId> --connection-id <uuid>
uip maestro case tasks describe --type connector-trigger --id <typeId> --connection-id <uuid>
```

| Flag | Description |
|------|-------------|
| `--type <type>` | **(required)** Task type: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `connector-activity`, `connector-trigger`. Use `processOrchestration` for `AGENTIC_PROCESS`. |
| `--id <id>` | **(required)** Unique ID of the task (entityKey or action-app id) |
| `--connection-id <id>` | Connection UUID (required for `connector-activity` and `connector-trigger` types) |

Returns input/output schema with names, types, and IDs. The schema is the source of truth for `data.inputs[]` / `data.outputs[]` when writing the task into `caseplan.json`. The `connector-activity` / `connector-trigger` flags still work but `case spec` returns a richer, FE-canonical `caseShape` for connector tasks.

---

## uip maestro case registry

Manage the local resource cache. Requires `uip login` for tenant-specific resources.

> **`--force`:** confirm with the user via the `AskUserQuestion` tool before running — bypasses the 24-hour cache, is network-heavy, and may be slow.

```bash
# Refresh cache from all resource types
uip maestro case registry pull
uip maestro case registry pull --force             # ignore 24-hours TTL and force refresh (ask via AskUserQuestion tool first)
uip maestro case registry pull --solution-id <id>  # include a specific solution's resources

# List all cached resources
uip maestro case registry list --output json

# Search for resources by keyword and/or field filters
uip maestro case registry search <keyword>
uip maestro case registry search <keyword> --type process
uip maestro case registry search --filter "name:contains=Apple,category=Pipelines"
uip maestro case registry search <keyword> --filter "name:contains=Foo" --type agent

# Get a resource by identifier (entityKey, id, or uiPathActivityTypeId)
uip maestro case registry get <identifier>
uip maestro case registry get <identifier> --type agent
uip maestro case registry get <uiPathActivityTypeId> --type typecache-activities --connection-id <uuid>

# --local: in-solution (offline) discovery of sibling projects (.uipx in cwd/parent/grandparent), no tenant/login
uip maestro case registry list --local --output json
uip maestro case registry search "<Name>" --type <agent|api> --local --output json    # matches by name (keyword); `agent` = agent sibling, `api` = api-workflow sibling
uip maestro case registry get "<entityKey-or-projectId>" --type <agent|api> --local --output json   # matches by key, NOT name
```

Resource types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `typecache-activities`, `typecache-triggers`, `action-apps`, `solution`.

Options for `pull`:
| Flag | Description |
|------|-------------|
| `-f, --force` | Force refresh, ignore 24-hour cache TTL |
| `-s, --solution-id <id>` | Include the registry of the specified solution |

Options for `search`:
| Flag | Description |
|------|-------------|
| `[keyword]` | Optional keyword to search by |
| `-t, --type <type>` | Limit search to a specific resource type |
| `-f, --filter <filter>` | Field filters, e.g. `name:contains=Apple,category=Pipelines` |

Filter format: `field=value` or `field:operator=value`. Supported fields: `name`, `description`, `category`, `tags`. Supported operators: `equals`, `contains`, `in`, `startsWith`, `endsWith`. At least one of keyword or `--filter` is required.

Options for `get`:
| Flag | Description |
|------|-------------|
| `<identifier>` | **(required)** The entityKey (process types), id (action-apps), or uiPathActivityTypeId (typecache) of the resource |
| `-t, --type <type>` | Limit to a specific resource type |
| `--connection-id <id>` | Connection UUID for connector-specific IS field metadata. Only applies to `typecache-activities` / `typecache-triggers` results |
| `--local` | Resolve against in-solution sibling projects (offline; no login). On `list`/`search`/`get`. Local types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`. |

**`--local` semantics.** Discovers sibling projects from the enclosing solution `.uipx` (walks cwd → parent → grandparent). Keys (`--output json`, PascalCased): `search`/`get` nest each match under `Data.Resources[].Resource.{EntityKey,Name,Category,Folders[].FullyQualifiedName,Inputs,Outputs,Source}`; `list` flattens to `Data.Resources[].{EntityKey,Name,Category,Source}` (no `Resource` wrapper, no I/O). **`get --local` matches the identifier only against `entityKey`/`.uipx` project Id — never the display name; to find a sibling by name use `search "<Name>" --local`.** A freshly-built, unpacked sibling's `EntityKey` equals its `.uipx` project Id. No solution found → `Result:"Failure"`, `Message:"No solution found for --local"`, exit 1.

Output: `{ MatchCount, Resources: [{ ResourceType, Resource }] }`.

Cache lives at `~/.uip/case-resources/` and expires after 24 hours.

### uip maestro case registry get-connector

Look up a connector activity or trigger from the local TypeCache index. Returns the raw cache entry and its connector config (connector key, connector type, operation name). Does NOT fetch connections — use `get-connection` for that.

```bash
uip maestro case registry get-connector --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connector --type typecache-triggers --activity-type-id <uuid>
```

| Flag | Description |
|------|-------------|
| `-t, --type <type>` | **(required)** `typecache-activities` or `typecache-triggers` |
| `--activity-type-id <id>` | **(required)** The `uiPathActivityTypeId` to look up |

Output: `{ Entry, Config }`.

### uip maestro case registry get-connection

Look up a connector and fetch available connections from Integration Service. **Requires `uip login`.**

```bash
uip maestro case registry get-connection --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connection --type typecache-triggers --activity-type-id <uuid>
```

| Flag | Description |
|------|-------------|
| `-t, --type <type>` | **(required)** `typecache-activities` or `typecache-triggers` |
| `--activity-type-id <id>` | **(required)** The `uiPathActivityTypeId` to look up |

Output: `{ Entry, Config, Connections }` — use a `Connections[].id` value as the `connectionId` written into a connector task's `data` in `caseplan.json`.

---

## uip maestro case process

Manage and run Case processes. **Requires `uip login`.**

```bash
# List available Case processes
uip maestro case process list
uip maestro case process list --folder-key <guid>
uip maestro case process list --filter "Name eq 'MyCase'"

# Get process schema and entry point details
uip maestro case process get <process-key> <feed-id>
uip maestro case process get <process-key> <feed-id> --folder-key <guid>

# Run a Case process
uip maestro case process run <process-key> <folder-key>
uip maestro case process run <process-key> <folder-key> --inputs '{"key":"value"}'
uip maestro case process run <process-key> <folder-key> --inputs @inputs.json --validate
```

Options for `list`:
| Flag | Description |
|------|-------------|
| `-t, --tenant <name>` | Tenant name (defaults to authenticated tenant) |
| `-f, --folder-key <key>` | **(required)** Filter by folder key (GUID) |
| `--filter <odata>` | Additional OData filter expression |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

Options for `get`:
| Flag | Description |
|------|-------------|
| `<process-key>` | **(required)** Process key (from `list`) |
| `<feed-id>` | **(required)** Feed ID (from `list`) |
| `-t, --tenant <name>` | Tenant name |
| `-f, --folder-key <key>` | **(required)** Folder key (GUID) |
| `--login-validity <minutes>` | Min minutes before token refresh |

Options for `run`:
| Flag | Description |
|------|-------------|
| `<process-key>` | **(required)** Process key |
| `<folder-key>` | **(required)** Folder key (GUID) |
| `-i, --inputs <json>` | Input parameters as JSON string or `@file.json` (also reads from stdin) |
| `-t, --tenant <name>` | Tenant name |
| `--release-key <key>` | Release key (GUID, from `list`) |
| `--feed-id <id>` | Feed ID for package lookup |
| `--robot-ids <ids>` | Comma-separated robot IDs |
| `--validate` | Validate inputs against process schema before running |
| `--login-validity <minutes>` | Min minutes before token refresh |

Output on `run`: `{ jobKey, state, traceId }` — use `jobKey` with `uip maestro case job traces`.

---

## uip maestro case job

Monitor Case jobs. **Requires `uip login`.**

```bash
# Stream traces for a running job
uip maestro case job traces <job-key>
uip maestro case job traces <job-key> --pretty
uip maestro case job traces <job-key> --poll-interval 5000

# Get job status
uip maestro case job status <job-key>
uip maestro case job status <job-key> --detailed
```

Options for `traces`:
| Flag | Description |
|------|-------------|
| `<job-key>` | **(required)** Job key (GUID from `process run`) |
| `-t, --tenant <name>` | Tenant name |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--traces-service <name>` | Traces service name (default: `llmopstenant_`) |
| `--pretty` | Human-readable trace output instead of raw JSON |
| `--login-validity <minutes>` | Min minutes before token refresh |

Options for `status`:
| Flag | Description |
|------|-------------|
| `<job-key>` | **(required)** Job key (GUID from `process run`) |
| `-t, --tenant <name>` | Tenant name |
| `--folder-key <key>` | Folder key (GUID, defaults to authenticated folder) |
| `--detailed` | Show full response with all fields |
| `--login-validity <minutes>` | Min minutes before token refresh |

---

## uip maestro case instance

Manage live Case process instances. **Requires `uip login`.**

```bash
# List instances
uip maestro case instance list
uip maestro case instance list --limit 20 --offset 0
uip maestro case instance list --process-key <key> --folder-key <key>
uip maestro case instance list --package-id <id> --error-code <code>

# Get a specific instance
uip maestro case instance get <instance-id>
uip maestro case instance get <instance-id> --folder-key <key>

# Lifecycle operations (all accept --folder-key and --comment)
uip maestro case instance pause <instance-id>
uip maestro case instance resume <instance-id>
uip maestro case instance cancel <instance-id>
uip maestro case instance retry <instance-id>

# Variables
uip maestro case instance variables <instance-id>
uip maestro case instance variables <instance-id> --parent-element-id <id>

# Incidents for a specific instance
uip maestro case instance incidents <instance-id>

# Get the Case definition (JSON) for a process instance
uip maestro case instance asset <instance-id>

# Migration: migrate instance to a different package version
uip maestro case instance migrate <instance-id> <new-version>

# Go-to: move execution cursor from one element to another
uip maestro case instance goto <instance-id> '[{"sourceElementId":"A","targetElementId":"B"}]'
uip maestro case instance cursors <instance-id>
uip maestro case instance element-executions <instance-id>
```

---

## uip maestro case processes

View Case process summaries. **Requires `uip login`.**

```bash
# List all Case process summaries
uip maestro case processes list

# Get incidents for a specific process
uip maestro case processes incidents <process-key>
uip maestro case processes incidents <process-key> --folder-key <key>
```

---

## uip maestro case incident

View and retrieve Case incidents across all processes. **Requires `uip login`.**

```bash
# Get incident summaries across all processes
uip maestro case incident summary

# Get a single incident by ID
uip maestro case incident get <incident-id> --folder-key <key>
```

Options for `get`:
| Flag | Description |
|------|-------------|
| `<incident-id>` | **(required)** Incident ID |
| `--folder-key <key>` | **(required)** Folder key |

---

## Global options (all commands)

| Option | Description |
|--------|-------------|
| `--output json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |
