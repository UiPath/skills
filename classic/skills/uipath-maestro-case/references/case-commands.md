# uip — Surviving CLI Command Reference

`caseplan.case` mutations are direct file edits, not CLI calls. The skill issues only metadata/discovery, validation, debug/runtime-management, solution scaffold/upload, and consent-gated Phase 7 pack/publish commands. Commands return `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`; use `--output json` programmatically.

## Local vs cloud commands

`caseplan.case` mutations use Read + Write/Edit. CLI is limited to:

| Commands | Purpose | Auth |
|---|---|---|
<!--skill-flavor:solution-commands-row:start-->
| `solution init`, `solution projects add`, `solution resources refresh`, `solution upload` | Scaffold, resource sync, Studio Web upload | Yes for `upload` |
<!--skill-flavor:solution-commands-row:end-->
<!--skill-flavor:phase-seven-row:start-->
| `maestro case pack`, `solution pack`, `solution publish` | Phase 7: recompile `caseplan.case.bpmn`, create `.zip`, publish to tenant solution feed (consent-gated) | Yes for `publish` |
<!--skill-flavor:phase-seven-row:end-->
<!--skill-flavor:resources-row:start-->
| `solution resources list [--source local]`, `solution resources add --source local\|remote`, `solution resources remove <key>`, `solution resources edit <key>` | Inventory read (`list`) + atomic single-resource mutations (local stub or remote import; delete by key; patch spec via `--patch '<json>'`) — see [uipath-solution Step 9–11](/uipath:uipath-solution) | Only `--source remote` requires auth; `remove`/`edit` are offline |
<!--skill-flavor:resources-row:end-->
| `registry pull/list/search`, `get-connector`, `get-connection`, `tasks describe`, `is resources/triggers describe` | Read-only registry/metadata discovery | Yes for `pull` |
| `validate` | Validate `caseplan.case` | No |
| `instance`, `processes`, `incidents`, `process run`, `job traces`, `debug` | Query/manage live Orchestrator state | Yes |

<!--skill-flavor:auth-column-note:start-->
<!--skill-flavor:auth-column-note:end-->

---

<!--skill-flavor:solution-init-section:start-->
## uip solution init

Run `uip solution init <SolutionName>` to create `<SolutionName>/` and `<SolutionName>.uipx`:

```bash
uip solution init <SolutionName>
```

`<SolutionName>` is required. The `case` plugin's § Scaffold writes project files separately.
<!--skill-flavor:solution-init-section:end-->

---

## uip maestro case init

**Run from inside the solution directory (SKILL.md Rule 24):** first run `cd <SolutionDir>`. Outside a solution, auto-scaffolding creates `<ProjectName>Solution/` around the project. The standard path creates six boilerplate files, including `project.uiproj`, and registers the project in the parent `.uipx`. The T01 direct-JSON path in [plugins/case/impl-json.md](plugins/case/impl-json.md) writes missing files or the full scaffold when unavailable.

<!--skill-flavor:case-init-command:start-->
```bash
cd <SolutionDir> && uip maestro case init <ProjectName>
```
<!--skill-flavor:case-init-command:end-->

`<ProjectName>` is required and is created inside the current directory.

<!--skill-flavor:cd-mandatory-note:start-->
> **Run `cd <SolutionDir>`; `&&`-chaining after `uip solution init` does not satisfy this.** `solution init` creates `<SolutionDir>` as cwd's child, so `uip solution init X && uip maestro case init X` runs outside it and triggers auto-scaffolding.
<!--skill-flavor:cd-mandatory-note:end-->

<!--skill-flavor:case-init-semantics:start-->
Run `case init` inside the solution to create `<SolutionDir>/<ProjectName>/` and auto-register it in the parent `.uipx` (`Data.SolutionRegistration.Status`: `Registered` or `AlreadyRegistered`). Outside one, it creates `<ProjectName>Solution/<ProjectName>Solution.uipx`, nests `<ProjectName>Solution/<ProjectName>/`, adds `Data.AutoCreatedSolution` (`{ Name, Path, SolutionFile }`), and reports `Status: Registered`. Pass `--skip-solution-registration` to skip both, creating bare `<ProjectName>/` with `Status: OptedOut`. If a **non-empty** directory already exists at the path you typed, init warns and leaves it untouched — the project still lands in `<ProjectName>Solution/<ProjectName>/`, not the existing directory. Run `uip solution projects add ./<ProjectName>` only for status `Skipped` (ambiguous discovery) or `Failed` (`.uipx` write error); it is redundant for `Registered`/`AlreadyRegistered`, and intentional opt-out may be registered later. After seeding, the case plugin (`plugins/case/impl-json.md`) writes only unseeded scaffold files; see `implementation.md` § Step 6.
<!--skill-flavor:case-init-semantics:end-->

---

<!--skill-flavor:projects-add-section:start-->
## uip solution projects add

Register a project with an existing solution. Used in two scenarios in this skill:

1. **`case init` unavailable** — when the case plugin (T01 in `impl-json.md`) wrote `project.uiproj` by hand, the project is not auto-registered, so this command is required (see `implementation.md` § Step 6.0b).
2. **Fallback for `uip maestro case init`** — when `case init` returns `Data.SolutionRegistration.Status` of `Skipped` or `Failed`, run this manually to wire the project in. When `case init` returns `Registered` or `AlreadyRegistered` (the normal outcome both inside a solution and when it auto-scaffolds one outside), this command is redundant. When it returns `OptedOut` (`--skip-solution-registration` was passed), both auto-scaffold and registration were skipped intentionally — run this only if you later decide to register.

```bash
uip solution projects add <ProjectName> <SolutionName>.uipx
```

| Flag | Description |
|------|-------------|
| `<ProjectName>` | **(required)** Project directory name (must already exist with `project.uiproj`) |
| `<SolutionName>.uipx` | **(required)** Path to the solution `.uipx` |

Adds the project to `.uipx.Projects[]`. Run after `project.uiproj` exists.
<!--skill-flavor:projects-add-section:end-->

---

## uip solution resources refresh

<!--skill-flavor:refresh-before-debug:start-->
Run:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```

This rescans projects and syncs declarations from `bindings_v2.json`, creating missing resources and importing matching Orchestrator resources. `--solution-folder` is required outside the solution and may be omitted for ad-hoc local use inside it; the skill always passes it explicitly so the cwd doesn't matter. **Always run it before `uip solution upload` or `uip maestro case debug`** or Studio Web may report `Resource is not configured`. `bindings_v2.json` must be populated; `resources: []` syncs nothing.
<!--skill-flavor:refresh-before-debug:end-->

---

## uip solution upload

Requires `uip login`. Run:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"
```

Pass the directory containing `.uipx`; no bundling is needed. Upload goes to Studio Web. `--output-filter` is mandatory and projects response `Data` to `Status`, `Action`, `SolutionId`, and `DesignerUrl`; `Action` is `Imported` or `Overwritten`, and report which. If `DesignerUrl` is missing, re-run once without `--output-filter`, dump the unfiltered response to `tasks/upload-response.json`, and diagnose it; this second upload/overwrite is allowed at most once within existing publish consent. Default unspecified "publish" behavior: refresh, run the filtered upload, and share the URL.

---

## uip maestro case pack

Run offline on every Phase 7 pass immediately before `uip solution pack`, including skipped Phase 5/6 and existing `.bpmn` cases:

```bash
uip maestro case pack <project-path> <output-path> --output json
```

`<project-path>` and `<output-path>` are required; use `<SolutionDir>/dist`, never inside the case project. It compiles `caseplan.case` to `caseplan.case.bpmn` and packs a `.nupkg`. `-n, --name <name>` defaults to the project folder; `-v, --version <version>` to `1.0.0`; `--author <author>` to `UiPath`; `--description <text>` to `Created by UiPath`. `package-descriptor.json` is required; on `Missing package-descriptor.json in: <project-path>`, restore it and never skip. This `.nupkg` is not the deploy artifact: `uip solution publish` accepts the solution `.zip`, while `uip solution pack` creates its own project `.nupkg`. See [phased-execution.md § Why `case pack` is mandatory](phased-execution.md#why-case-pack-is-mandatory).

---

## uip solution pack

Phase 7 step 3; consent-gated and offline. Run `uip maestro case pack` first, then:

```bash
uip solution pack <SolutionDir> <SolutionDir>/dist --output json
uip solution pack ./MySolution ./MySolution/dist --version 2.0.0 --output json
```

`<solutionPath>` (directory containing `.uipx`, not the case project) and `<output-path>` are required. `-n, --name <name>` defaults to the solution folder; `-v, --version <version>` to `1.0.0`. Run `uip solution resources refresh` first (Rule 15). The command packs projects into `.nupkg` files and bundles `<name>_<version>.zip` (underscore, not dot); read the filename from `Data.Packages` or list `<output-path>`, never construct it. It does not compile BPMN and bundles `caseplan.case.bpmn` only if already present; run [`uip maestro case pack`](#uip-maestro-case-pack) every time.

---

## uip solution publish

Phase 7 step 4; consent-gated; requires `uip login`. Run:

```bash
uip solution publish <packagePath> --wait --output json
```

`<packagePath>` is required and must be the `.zip` from `uip solution pack`. `--wait` blocks until `Ready` / `Active`; `--timeout <seconds>` defaults to `360`; `--personal-workspace` selects the current user's Personal Workspace feed instead of the tenant feed. Duplicate `name+version` pairs are rejected; on `processKey` collision, bump `--version` during `uip solution pack` and re-run. On failure, print the CLI error verbatim, log it in `build-issues.md`, and re-show the Phase 7 prompt; see [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). Publishing only lists the package; installation requires `uip solution deploy run` and is out of scope.

---

## uip maestro case validate

```bash
uip maestro case validate <file> --strict --sdd sdd.md --output json
uip maestro case validate <file> --strict --output json
uip maestro case validate <file> --skeleton-v2 --output json
uip maestro case validate <file> --skeleton --output json
```

`<file>` is required. `--strict` is the authoritative Phase 3-exit/Phase 4 profile: default checks plus empty stage, surviving `$xref(`, hoisted `conditionExpression`, incomplete connector context, empty task `data`, output-shape and input-reference form; failures use `STRICT_*` in `Data.Issues[]`. `--sdd <path>` audits every SDD-declared stage, task/type, condition row, SLA, trigger, and case variable, implies `--strict`, and uses `STRICT_SDD_*`. Use whenever an `sdd.md` exists. `--strict`/`--sdd` are mutually exclusive with `--skeleton`/`--skeleton-v2`. `--skeleton-v2` is the preferred Phase 2 preview (structure, entry/exit, SLA, escalation; incomplete task values/schemas); `--skeleton` is the legacy Phase 2 fallback (structure only). Success is `{ File, Status: "Valid" }`; findings are inline.

### Phase 2 profile probe

1. Run `validate ... --skeleton-v2 --output json`.
2. Only if the parser names `--skeleton-v2` unknown/unsupported, typically `ErrorCode: "invalid_argument"` and exit code 3, run `--skeleton` once. Exit code 3 alone is insufficient.
3. Any genuine v2 result, including validation errors, proves v2 ran; report it and do not fall back.

Name the selected profile in the Phase 2 summary. Legacy `--skeleton` checks structure only; authoritative full validation covers conditions/SLA in Phase 4.

### Which profile in which phase

Section-end validates in Phases 2–3 use the plain profile — a half-built plan fails strict by design. The Phase 3 exit and every Phase 4 validate carry `--strict --sdd sdd.md --output json`, and no plain-profile result after Phase 3 entry is ever quoted as a close: a `Valid` without `"Profile": "strict"` does not close the build (SKILL.md Rule 7). **Run strict validation alone, never chained with another validate**; otherwise the first response envelope is read and the second is discarded.

### Version guard — `--strict` / `--sdd` require CLI 1.202

Fall back to plain `validate` only when the response is `invalid_argument` naming `--strict` or `--sdd` unknown. Exit 3 alone and strict failure are insufficient. On fallback, record `strict profile unavailable on CLI <version>` in `build-issues.md` and the completion report, and run [implementation.md § Step 12](implementation.md#step-12--end-of-phase-3-validator-pass) Checks 1–15 by hand.

---

## uip maestro case format

Run after every plan write; it is the only sanctioned reformat (Rule 14):

```bash
uip maestro case format <file> --output json
```

`<file>` is required. It rewrites in place with 2-space indentation and one key per line. `Data.Changed` is `true` when rewritten and `false` when already formatted. Unparseable input is refused and untouched; key order is preserved, numbers use shortest form, and duplicate keys collapse to the last occurrence as JSON round-trip behavior. Same verb family as `maestro flow format` and `maestro bpmn format`.

---

## uip maestro case bindings sync

Derive `bindings_v2.json` from the plan's root `bindings[]` and write it next to the plan. Never author or edit the sidecar by hand.

```bash
uip maestro case bindings sync <caseplan.case> --output json
```

Output is `Code: CaseBindingsSync` with `Data.BindingsPath`, `Data.ResourceCount`, `Data.ConnectionCount`. `ResourceCount: 0` is still `Result: Success`; the empty sidecar faithfully represents no bindings, and the gate is `validate --strict` (`STRICT_BINDINGS_ABSENT`), not sync. See [bindings-v2-sync.md](bindings-v2-sync.md).

---

## uip maestro case splice

The only sanctioned writer of `data.context`/`data.inputs`/`data.outputs` for `execute-connector-activity`, `wait-for-connector`, `external-agent`, and `external-workflow`; never hand-author them. It also writes root connection bindings from a saved `case spec` envelope.

```bash
uip maestro case splice <caseplan.case> --task-id <taskId> --spec tasks/spec-cache.<elementId>.json \
  --connection-id <connection-uuid> [--out <file>] --output json
```

`--task-id <id>` is required unless `--task-name`; it is the task `id` in `nodes[].data.tasks[][].id`. `--task-name <name>` is the exact `displayName`; pass exactly one. `--spec <file>` is required unless `--described`; it must be the verbatim `case spec` response with `Data.CaseShape` (spec must not use `--skip-case-shape`). `--connection-id <id>` is required and keys/reuses root bindings. Omit `--folder-key`: splice reads `Data.Connection.FolderKey` from the spec and refuses disagreement with exit 1 and no write. Never copy another task's folder key.

`--described <file>` accepts a verbatim `uip maestro case tasks describe` result and merges `type`/`_jsonSchema`/`options`/`displayName` into existing input/output rows by `name`, preserving `id`/`var`/`elementId` and SDD values; use for resource tasks. Pass exactly one of `--spec`/`--described`; both are refused. `--out <file>` writes elsewhere. Output is `Code: ConnectorShapeSpliced` with `Data.Summary` (`TaskType`, `ServiceType`, `ContextEntries`, `Inputs`, `Outputs`, `ConnectionBindingId`, `FolderBindingId`, `BindingsReused`) and `Data.NextSteps`. It is offline and idempotent (same arguments produce byte-identical output); mismatched spec/connection ids are refused, naming both, with no write.

---

<!--skill-flavor:case-debug-command:start-->
## uip maestro case debug

Requires `uip login`; executes the case for real (emails, messages, APIs), so run only on explicit user consent. Always refresh first:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip maestro case debug <project-path> --log-level debug --output json
```

`<project-path>` is required and must contain `project.uiproj`. `--folder-id <id>` is Orchestrator `OrganizationUnitId`, auto-detected if omitted; `--poll-interval <ms>` defaults to `2000`; `--output <format>` accepts `table`, `json`, `yaml`, `plain` and defaults to `json`; `--login-validity <minutes>` defaults to `10`.
<!--skill-flavor:case-debug-command:end-->

---

## uip maestro case spec

Preferred read-only unified metadata/scaffold endpoint for connector activities/triggers; it replaces the two-call `case tasks describe` + `is resources describe` flow and returns identity, connection, inputs, outputs, filter, references, and optional populated `caseShape`.

```bash
uip maestro case spec --type <activity|trigger> \
  --activity-type-id <uiPathActivityTypeId> \
  --connection-id <uuid> \
  --skip-case-shape --output json

uip maestro case spec --type <activity|trigger> \
  --activity-type-id <uiPathActivityTypeId> \
  --connection-id <uuid> \
  --input-details '<json>' --output json
```

Required: `--type <activity\|trigger>`, `--activity-type-id <uuid>` (TypeCache `uiPathActivityTypeId`), and `--connection-id <uuid>` (choose from `case registry get-connection`). `--object-name <name>`: Override the typecache `objectName`. Required in two cases: (1) **entity-typed Curated triggers** whose typecache stores a placeholder (e.g. Data Service `{tenantEntityName\|folderEntityName}`); (2) **Generic-typed activities/triggers** (activity typecache `activityType === "Generic"`; trigger typecache `activityType === "GenericTrigger"`) whose typecache definition is shared across every object the connector exposes (e.g. Salesforce `InsertRecord` covering Account/Contact/Lead/...). The CLI errors at spec-fetch time when missing in case (2) — opaque `unknown_error`, see [`connector-trigger-planning.md`](connector-trigger-planning.md). Discovery: `uip is resources list/describe` (Generic) or `uip is triggers objects` (entity-typed Curated). See [`connector-integration.md`](connector-integration.md) and [`connector-trigger-planning.md`](connector-trigger-planning.md). `--skip-case-shape` omits `caseShape` for planning and is mutually exclusive with `--input-details`. `--input-details <json>` populates `caseShape`: activities accept `{bodyParameters?, queryParameters?, pathParameters?, filter?}`, triggers `{eventParameters?, filter?}`; connection identity is derived from `--connection-id` and TypeCache, not input. Full contract: [`case-spec-input-details.md`](case-spec-input-details.md).

Returns `ConnectorTaskSpec` with `identity`, `operation`, `connection`, `inputs`, `outputs`, optional `filter`, `essentialConfiguration`, `references[]` (including `discoverCommand`), `diagnostics`, and, unless skipped, FE-canonical `caseShape` inputs/outputs/context. Webhook URL is intentionally absent and deterministic from `connectionId` + `elementInstanceId` + `connectorKey` + `eventOperation`; fetch via `getWebhookConfig` only when needed. `--input-details.filter` compiles to CEQL (activity) or JMESPath (trigger) per [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

---

## uip maestro case tasks describe

Use for non-connector tasks (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`); connector tasks should use [`uip maestro case spec`](#uip-maestro-case-spec).

```bash
uip maestro case tasks describe --type <type> --id <id> --output json
uip maestro case tasks describe --type process --id <entityKey>
uip maestro case tasks describe --type connector-activity --id <typeId> --connection-id <uuid>
uip maestro case tasks describe --type connector-trigger --id <typeId> --connection-id <uuid>
```

`--type <type>` is required and accepts `process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `connector-activity`, `connector-trigger`; use `processOrchestration` for `AGENTIC_PROCESS`. `--id <id>` is required (entityKey or action-app id). `--connection-id <id>` is required for connector types. Output schemas with names/types/IDs are authoritative for `data.inputs[]`/`data.outputs[]`; connector commands remain supported but `case spec` is richer and FE-canonical.

---

## uip maestro case registry

Manage `~/.uip/case-resources/`; cache expires after 24 hours. Tenant-specific resources require `uip login`. Ask via `AskUserQuestion` before `--force` because it bypasses the TTL, is network-heavy, and may be slow. Exception: if `uip maestro case sdd resolve` reports stale cache in `Data.Warnings`, run once without asking, then resolve again ([SKILL.md Rule 3](../SKILL.md)).

```bash
uip maestro case registry pull
uip maestro case registry pull --force
uip maestro case registry pull --solution-id <id>
uip maestro case registry list --output json
uip maestro case registry search <keyword>
uip maestro case registry search <keyword> --type process
uip maestro case registry search --filter "name:contains=Apple,category=Pipelines"
uip maestro case registry search <keyword> --filter "name:contains=Foo" --type agent
uip maestro case registry get <identifier>
uip maestro case registry get <identifier> --type agent
uip maestro case registry get <uiPathActivityTypeId> --type typecache-activities --connection-id <uuid>
# --local: in-solution (offline) discovery of sibling projects (.uipx in cwd/parent/grandparent), no tenant/login
uip maestro case registry list --local --output json
uip maestro case registry search "<Name>" --type <agent|api|businessRule> --local --output json    # matches by name (keyword); `agent` = agent sibling, `api` = api-workflow sibling, `businessRule` = business-rule sibling
uip maestro case registry get "<entityKey-or-projectId>" --type <agent|api|businessRule> --local --output json   # matches by key, NOT name
```

Resource types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `businessRule`, `typecache-activities`, `typecache-triggers`, `action-apps`, `solution`. `pull`: `-f, --force` (ignore 24-hour TTL), `-s, --solution-id <id>`. `search`: optional `[keyword]`, `-t, --type <type>`, `-f, --filter <filter>`; syntax is `field=value` or `field:operator=value`, fields `name`, `description`, `category`, `tags`, operators `equals`, `contains`, `in`, `startsWith`, `endsWith`; keyword or filter is required. `get` requires `<identifier>` (entityKey, id, or `uiPathActivityTypeId`), accepts `-t, --type <type>`, `--connection-id <id>` only for `typecache-activities`/`typecache-triggers`, and `--local`. `--local` resolves against in-solution sibling projects (offline; no login), on `list`/`search`/`get`. Local types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `function`, `businessRule`.

`--local` walks cwd → parent → grandparent for an enclosing solution `.uipx`, with no tenant/login. `search`/`get` return matches under `Data.Resources[].Resource.{EntityKey,Name,Category,Folders[].FullyQualifiedName,Inputs,Outputs,Source}`; `list` returns flat `Data.Resources[].{EntityKey,Name,Category,Source}` without wrapper/I/O. `get --local` matches only `entityKey`/`.uipx` project Id, never display name; use `search "<Name>" --local` for names. A freshly built unpacked sibling's `EntityKey` equals its `.uipx` project Id. If no solution: `Result:"Failure"`, `Message:"No solution found for --local"`, exit 1. Normal output: `{ MatchCount, Resources: [{ ResourceType, Resource }] }`.

### uip maestro case registry get-connector

Read the local TypeCache entry/config; it does not fetch connections.

```bash
uip maestro case registry get-connector --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connector --type typecache-triggers --activity-type-id <uuid>
```

`-t, --type <type>` is required and is `typecache-activities` or `typecache-triggers`; `--activity-type-id <id>` is required. Output: `{ Entry, Config }` (connector key/type and operation name included).

### uip maestro case registry get-connection

Requires `uip login`; look up TypeCache and fetch Integration Service connections:

```bash
uip maestro case registry get-connection --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connection --type typecache-triggers --activity-type-id <uuid>
```

Required: `-t, --type <type>` (`typecache-activities` or `typecache-triggers`) and `--activity-type-id <id>`. Output `{ Entry, Config, Connections }`; use `Connections[].Id` as connector-task `connectionId` in `caseplan.case`.

---

## uip maestro case process

Requires `uip login`.

```bash
uip maestro case process list --folder-key <guid>
uip maestro case process list --folder-key <guid> --filter "Name eq 'MyCase'"
uip maestro case process get <process-key> <feed-id> --folder-key <guid>
uip maestro case process run <process-key> <folder-key>
uip maestro case process run <process-key> <folder-key> --inputs '{"key":"value"}'
uip maestro case process run <process-key> <folder-key> --inputs @inputs.json --validate
```

`list`: `-t, --tenant <name>` defaults to authenticated tenant; `-f, --folder-key <key>` required GUID; `--filter <odata>`; `--login-validity <minutes>` default `10`. `get`: required `<process-key>`, `<feed-id>`, `-f, --folder-key <key>`; `-t, --tenant <name>`; `--login-validity <minutes>`. `run`: required `<process-key>`, `<folder-key>`; `-i, --inputs <json>` accepts JSON, `@file.json`, or stdin; `-t, --tenant <name>`; `--release-key <key>`; `--feed-id <id>`; `--robot-ids <ids>` comma-separated; `--validate`; `--login-validity <minutes>`. Output `{ jobKey, state, traceId }`; pass `jobKey` to `uip maestro case job traces`.

---

## uip maestro case job

Requires `uip login`.

```bash
uip maestro case job traces <job-key>
uip maestro case job traces <job-key> --pretty
uip maestro case job traces <job-key> --poll-interval 5000
uip maestro case job status <job-key>
uip maestro case job status <job-key> --detailed
```

For `traces`, `<job-key>` is required GUID from `process run`; accept `-t, --tenant <name>`, `--poll-interval <ms>` default `2000`, `--traces-service <name>` default `llmopstenant_`, `--pretty`, `--login-validity <minutes>`. For `status`, `<job-key>` is required; accept `-t, --tenant <name>`, `--folder-key <key>` (defaults authenticated folder), `--detailed`, `--login-validity <minutes>`.

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

Requires `uip login`.

```bash
uip maestro case processes list
uip maestro case processes incidents <process-key>
uip maestro case processes incidents <process-key> --folder-key <key>
```

---

## uip maestro case incident

Requires `uip login`.

```bash
uip maestro case incident summary
uip maestro case incident get <incident-id> --folder-key <key>
```

`<incident-id>` and `--folder-key <key>` are required for `get`.

---

## Global options (all commands)

| Option | Description |
|---|---|
| `--output json\|yaml\|table` | Format; default is table in TTY and json otherwise |
| `--verbose` | Enable debug logging |

<!-- END: case-commands.md -->
