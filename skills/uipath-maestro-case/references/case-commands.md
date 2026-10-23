# uip — Surviving CLI Command Reference

`caseplan.case` mutations are direct file edits, not CLI calls. The commands below are the only `uip` invocations issued: metadata/discovery, validation, debug, runtime management, solution scaffold/upload, and consent-gated Phase 7 pack/publish. Commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`; use `--output json` programmatically.

## Local vs cloud commands

`caseplan.case` mutations use Read + Write/Edit. CLI is limited to:

| Commands | What | Auth |
|---|---|---|
<!--skill-flavor:solution-commands-row:start-->
| `solution init`, `solution projects add`, `solution resources refresh`, `solution upload` | Scaffold, resource sync, Studio Web upload | Yes (`upload`) |
<!--skill-flavor:solution-commands-row:end-->
<!--skill-flavor:phase-seven-row:start-->
| `maestro case pack`, `solution pack`, `solution publish` | Phase 7: compile `caseplan.case.bpmn`, pack `.zip`, publish to tenant solution feed (consent-gated) | Yes (`publish`) |
<!--skill-flavor:phase-seven-row:end-->
<!--skill-flavor:resources-row:start-->
| `solution resources list [--source local]`, `solution resources add --source local\|remote`, `solution resources remove <key>`, `solution resources edit <key>` | Inventory and atomic resource mutations (local stub, remote import, delete, or `--patch '<json>'`); see [uipath-solution Step 9–11](/uipath:uipath-solution) | Only `--source remote` requires auth; `remove`/`edit` are offline |
<!--skill-flavor:resources-row:end-->
| `registry pull/list/search`, `get-connector`, `get-connection`, `tasks describe`, `is resources/triggers describe` | Read-only registry/metadata discovery | Yes (`pull`) |
| `validate` | Validate `caseplan.case` | No |
| `instance`, `processes`, `incidents`, `process run`, `job traces`, `debug` | Query/manage live Orchestrator state | Yes |

<!--skill-flavor:auth-column-note:start-->
<!--skill-flavor:auth-column-note:end-->

---

<!--skill-flavor:solution-init-section:start-->
## uip solution init

Create a solution directory and `.uipx`:

```bash
uip solution init <SolutionName>
```

`<SolutionName>` is required. Creates `<SolutionName>/<SolutionName>.uipx`; the `case` plugin's § Scaffold writes project files separately.
<!--skill-flavor:solution-init-section:end-->

---

## uip maestro case init

**Run from inside the solution directory (SKILL.md Rule 24):** `cd <SolutionDir>` first. The standard command scaffolds a Case project with 6 boilerplate files, including `project.uiproj`, and registers it in the parent `.uipx`; [plugins/case/impl-json.md](plugins/case/impl-json.md) writes only files not seeded and handles the hand-built T01 path when unavailable.

<!--skill-flavor:case-init-command:start-->
```bash
cd <SolutionDir> && uip maestro case init <ProjectName>
```
<!--skill-flavor:case-init-command:end-->

`<ProjectName>` is required and is created inside the current directory.

<!--skill-flavor:cd-mandatory-note:start-->
> **`cd <SolutionDir>` is mandatory; `&&`-chaining after `uip solution init` does not satisfy it.** `solution init X` creates child `X`, so `uip solution init X && uip maestro case init X` runs outside it and triggers auto-scaffold behavior.
<!--skill-flavor:cd-mandatory-note:end-->

<!--skill-flavor:case-init-semantics:start-->
`case init` always lands inside a solution. Inside one, it creates `<SolutionDir>/<ProjectName>/`, registers with the parent `.uipx`, and reports `Data.SolutionRegistration.Status`: `Registered` or `AlreadyRegistered`. Outside one, it creates `<ProjectName>Solution/<ProjectName>Solution.uipx`, nests `<ProjectName>Solution/<ProjectName>/`, adds `Data.AutoCreatedSolution` (`{ Name, Path, SolutionFile }`), and reports `Status: Registered`. `--skip-solution-registration` disables both, creating bare `<ProjectName>/` with `Status: OptedOut`. A non-empty typed path is left untouched; the project still goes under `<ProjectName>Solution/<ProjectName>/`. Run `uip solution projects add ./<ProjectName>` only when status is `Skipped` (ambiguous discovery) or `Failed` (`.uipx` write error). After seeding, the case plugin writes only missing scaffold files; see `implementation.md` § Step 6.
<!--skill-flavor:case-init-semantics:end-->

---

<!--skill-flavor:projects-add-section:start-->
## uip solution projects add

Register an existing project in a solution. Run when `case init` is unavailable and T01 wrote `project.uiproj` by hand, or when `Data.SolutionRegistration.Status` is `Skipped`/`Failed`. Do not redundantly run for `Registered`/`AlreadyRegistered`; `OptedOut` intentionally skipped registration and requires this only if later desired.

```bash
uip solution projects add <ProjectName> <SolutionName>.uipx
```

Both arguments are required; the project must already contain `project.uiproj`. Adds it to `.uipx.Projects[]`.
<!--skill-flavor:projects-add-section:end-->

---

## uip solution resources refresh

Run:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```

This rescans projects and syncs declarations from `bindings_v2.json`, creating missing resources or importing matching Orchestrator resources. `--solution-folder` is required outside the solution; omit only for ad-hoc local use; the skill always passes it explicitly. **Always run before `uip solution upload` or `uip maestro case debug`;** otherwise Studio Web may warn `Resource is not configured`. A still-empty scaffold (`resources: []`) syncs nothing.

## uip solution upload

Requires `uip login`; run:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"
```

Pass the solution directory containing `.uipx`, not an intermediate bundle. `--output-filter` is mandatory: it projects the response envelope's `Data` to `Status`, `Action`, `SolutionId`, and `DesignerUrl`, preventing truncation; `Action` is `Imported` or `Overwritten`, and report which. If `DesignerUrl` is missing, re-run once without `--output-filter` and dump the unfiltered response to `tasks/upload-response.json`; this second upload is another overwrite/version and is allowed at most once within publish consent. Default unspecified “publish” path: run refresh, then the filtered upload, and share the URL.

## uip maestro case pack

Pack one Case project and compile `caseplan.case` to `caseplan.case.bpmn` inside it; run offline:

```bash
uip maestro case pack <project-path> <output-path> --output json
```

`<project-path>` and `<output-path>` are required; output must be `<SolutionDir>/dist`, never inside the case project. Options: `-n, --name <name>` (default project folder), `-v, --version <version>` (default `1.0.0`), `--author <author>` (default `UiPath`), `--description <text>` (default `Created by UiPath`). Run before every `uip solution pack`, including skipped Phase 5/6 and existing `.bpmn`; see [phased-execution.md § Why `case pack` is mandatory](phased-execution.md#why-case-pack-is-mandatory). Restore missing `package-descriptor.json`; never skip. Its `.nupkg` (`<Name>.case.Case.<version>.nupkg`) is not the deploy artifact: publish the `.zip` from `solution pack`.

## uip solution pack

Phase 7 step 3, consent-gated and offline:

```bash
uip solution pack <SolutionDir> <SolutionDir>/dist --output json
uip solution pack ./MySolution ./MySolution/dist --version 2.0.0 --output json
```

`<solutionPath>` (directory containing `.uipx`, not case project) and `<output-path>` are required. Options: `-n, --name <name>` (default solution folder), `-v, --version <version>` (default `1.0.0`). It packs projects into `.nupkg` and bundles `<name>_<version>.zip` (underscore, not dot). Read the filename from `Data.Packages` or list `<output-path>`; do not construct it. Run `uip solution resources refresh` first (Rule 15). It does **not** compile BPMN: immediately before it, every time, run [`uip maestro case pack`](#uip-maestro-case-pack), or a missing/stale `.bpmn` may ship despite successful pack/publish.

## uip solution publish

Requires `uip login`; Phase 7 step 4, consent-gated:

```bash
uip solution publish <packagePath> --wait --output json
```

`<packagePath>` is the required `.zip` from `solution pack`; `--wait` waits for `Ready` / `Active`; `--timeout <seconds>` defaults to `360`; `--personal-workspace` targets the current user's Personal Workspace instead of tenant feed. Duplicate `name+version` is rejected; on `processKey` collision, bump `--version` on `uip solution pack` and rerun. On failure, print the CLI error verbatim, log it in `build-issues.md`, and re-show the Phase 7 prompt; see [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). Publishing only lists the package; installation requires `uip solution deploy run` and is out of scope.

## uip maestro case validate

```bash
uip maestro case validate <file> --strict --sdd sdd.md --output json
uip maestro case validate <file> --strict --output json
uip maestro case validate <file> --skeleton-v2 --output json
uip maestro case validate <file> --skeleton --output json
```

`<file>` is required. `--strict` is mutually exclusive with `--skeleton`/`--skeleton-v2` and adds case-wide completeness checks: empty stage, surviving `$xref(`, hoisted `conditionExpression`, incomplete connector context, empty task `data`, output shape, and input-reference form; failures use `STRICT_*` in `Data.Issues[]`. `--sdd <path>` implies strict and audits every SDD-declared stage, task/type, condition row, SLA, trigger, and case variable with `STRICT_SDD_*`. `--skeleton-v2` is the preferred Phase 2 preview (structure, entry/exit, SLA, escalation; incomplete task values/schemas); `--skeleton` is the legacy structural fallback (skips tasks, SLAs, escalations, entry/exit). Success is `{ File, Status: "Valid" }`; errors/warnings are inline.

### Phase 2 profile probe

1. Run `validate ... --skeleton-v2 --output json`.
2. Only if the parser names `--skeleton-v2` unknown/unsupported (typically `ErrorCode: "invalid_argument"` and exit code 3), rerun once with `--skeleton`; exit code 3 alone is insufficient.
3. Any genuine v2 result, including validation errors, proves v2 ran; report it and do not fallback.

Name the selected profile in the Phase 2 summary. Legacy `--skeleton` checks structure only; authoritative full validation covers conditions/SLA in Phase 4.

### Which profile in which phase

Section-end validation in Phases 2–3 uses plain profile. Phase 3 exit and every Phase 4 validation use `--strict --sdd sdd.md --output json`; never quote a post-Phase-3 plain result as close. `Valid` without `"Profile": "strict"` does not close the build (SKILL.md Rule 7). **Run strict validate alone, never chained with another validate:** two envelopes on stdout cause the first to be read and the second discarded.

### Version guard — `--strict` / `--sdd` require CLI 1.202

Fallback to plain `validate` only when response is `invalid_argument` naming `--strict` or `--sdd` unknown; exit 3 alone is insufficient, and strict failure never justifies dropping flags. On fallback, record `strict profile unavailable on CLI <version>` in `build-issues.md` and the completion report, and run [implementation.md § Step 12](implementation.md#step-12--end-of-phase-3-validator-pass) Checks 1–15 by hand.

## uip maestro case format

Rewrite `caseplan.case` pretty-printed in place (2-space indentation, one key per line) after every write; this is the only sanctioned reformat (Rule 14):

```bash
uip maestro case format <file> --output json
```

`<file>` is required. `Data.Changed` is `true` when rewritten and `false` when already formatted. Unparseable input is refused untouched; key order is preserved, numbers use shortest form, and duplicate keys collapse to the last occurrence (JSON round-trip behavior). Same verb family as `maestro flow format` and `maestro bpmn format`.

## uip maestro case bindings sync

Never hand-author/edit the sidecar; derive it from root `bindings[]`:

```bash
uip maestro case bindings sync <caseplan.case> --output json
```

Output `Code: CaseBindingsSync` with `Data.BindingsPath`, `Data.ResourceCount`, `Data.ConnectionCount`. `ResourceCount: 0` is still success; the gate is `validate --strict` (`STRICT_BINDINGS_ABSENT`), not sync. See [bindings-v2-sync.md](bindings-v2-sync.md).

## uip maestro case splice

The only sanctioned writer of `data.context`/`data.inputs`/`data.outputs` for `execute-connector-activity`, `wait-for-connector`, `external-agent`, and `external-workflow`; never hand-author them:

```bash
uip maestro case splice <caseplan.case> --task-id <taskId> --spec tasks/spec-cache.<elementId>.json \
  --connection-id <connection-uuid> [--out <file>] --output json
```

`--task-id <id>` is required unless `--task-name`; `--task-name <name>` is exact `displayName`; pass exactly one, never both. `--spec <file>` is required unless `--described`, must be a verbatim `case spec` response carrying `Data.CaseShape` (spec without `--skip-case-shape`). `--connection-id <id>` is required and keys/reuses root bindings. Omit `--folder-key`: read `Data.Connection.FolderKey` from spec; disagreement is refused (exit 1, nothing written), and never copy another task's key. `--described <file>` is a verbatim `uip maestro case tasks describe` result; it merges `type`/`_jsonSchema`/`options`/`displayName` into existing input/output rows by `name`, preserving `id`/`var`/`elementId` and SDD values; use for resource tasks. `--spec` and `--described` are mutually exclusive. `--out <file>` writes elsewhere.

Output `Code: ConnectorShapeSpliced`, `Data.Summary` (`TaskType`, `ServiceType`, `ContextEntries`, `Inputs`, `Outputs`, `ConnectionBindingId`, `FolderBindingId`, `BindingsReused`) and `Data.NextSteps`. Offline and idempotent (same arguments produce byte-identical output). A spec for another connection is refused, names both ids, and writes nothing.

## uip maestro case debug

Requires `uip login`, executes for real (emails, messages, APIs), and requires explicit user consent. Always refresh first:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip maestro case debug <project-path> --log-level debug --output json
```

`<project-path>` is required and must contain `project.uiproj`; `--folder-id <id>` is Orchestrator `OrganizationUnitId` (auto-detected if omitted); `--poll-interval <ms>` defaults `2000`; `--output <format>` is `table`, `json`, `yaml`, or `plain` (default `json`); `--login-validity <minutes>` defaults `10`.

## uip maestro case spec

Read-only unified connector activity/trigger metadata and scaffold; preferred over the legacy two-call describe flow.

```bash
uip maestro case spec --type <activity|trigger> \
  --activity-type-id <uiPathActivityTypeId> --connection-id <uuid> \
  --skip-case-shape --output json

uip maestro case spec --type <activity|trigger> \
  --activity-type-id <uiPathActivityTypeId> --connection-id <uuid> \
  --input-details '<json>' --output json
```

Required: `--type <activity\|trigger>`, `--activity-type-id <uuid>` from TypeCache, and `--connection-id <uuid>` from `case registry get-connection`. `--object-name <name>` is required for entity-typed Curated placeholders and Generic activities/triggers (`activityType === "Generic"` or `"GenericTrigger"`), whose shared definition covers multiple objects; missing Generic object name yields opaque `unknown_error`. Discover Generic objects with `uip is resources list/describe`, entity-typed Curated objects with `uip is triggers objects`; see [`connector-trigger-planning.md`](connector-trigger-planning.md), [`connector-integration.md`](connector-integration.md). `--skip-case-shape` omits `caseShape` for planning and is mutually exclusive with `--input-details`. `--input-details <json>` pre-fills activity `{bodyParameters?, queryParameters?, pathParameters?, filter?}` or trigger `{eventParameters?, filter?}`; connection identity comes from `--connection-id`/TypeCache, not input. See [`case-spec-input-details.md`](case-spec-input-details.md).

Returns `ConnectorTaskSpec` with `identity`, `operation`, `connection`, `inputs`, `outputs`, optional `filter`, `essentialConfiguration`, `references[]` (pre-built `discoverCommand`), `diagnostics`, and, unless skipped, FE-canonical `caseShape` inputs/outputs/context arrays. Webhook URL is intentionally NOT in the output; fetch via `getWebhookConfig`. Filter trees compile to CEQL (activity) or JMESPath (trigger) per [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

## uip maestro case tasks describe

Use for non-connector task types (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`); connector tasks use [`uip maestro case spec`](#uip-maestro-case-spec).

```bash
uip maestro case tasks describe --type <type> --id <id> --output json
uip maestro case tasks describe --type process --id <entityKey>
uip maestro case tasks describe --type connector-activity --id <typeId> --connection-id <uuid>
uip maestro case tasks describe --type connector-trigger --id <typeId> --connection-id <uuid>
```

`--type <type>` is required: `process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `connector-activity`, or `connector-trigger`; use `processOrchestration` for `AGENTIC_PROCESS`. `--id <id>` is required (entityKey or action-app id). `--connection-id <id>` is required for connector types. Returns input/output names, types, IDs; schema is authoritative for `data.inputs[]`/`data.outputs[]`. Connector flags remain supported but `case spec` is richer and FE-canonical.

## uip maestro case registry

Local resource cache; tenant resources require login. Before `--force`, ask via `AskUserQuestion` because it bypasses the 24-hour cache and is network-heavy/slow. Exception: if `uip maestro case sdd resolve` reports stale cache in `Data.Warnings`, run once without asking, then resolve again ([SKILL.md Rule 3](../SKILL.md)).

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
uip maestro case registry list --local --output json
uip maestro case registry search "<Name>" --type <agent|api|businessRule> --local --output json
uip maestro case registry get "<entityKey-or-projectId>" --type <agent|api|businessRule> --local --output json
```

Types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `businessRule`, `typecache-activities`, `typecache-triggers`, `action-apps`, `solution`. `pull`: `-f, --force`, `-s, --solution-id <id>`. `search`: optional `[keyword]`, `-t, --type <type>`, `-f, --filter <filter>`; filters use `field=value` or `field:operator=value`, fields `name`, `description`, `category`, `tags`, operators `equals`, `contains`, `in`, `startsWith`, `endsWith`; keyword or filter required. `get`: required `<identifier>` (entityKey, id, or `uiPathActivityTypeId`), `-t, --type <type>`, `--connection-id <id>` only for typecache connector metadata, `--local`.

`--local` walks cwd → parent → grandparent for the enclosing `.uipx`. Local types also include `function`. Search/get JSON nests each match under `Data.Resources[].Resource.{EntityKey,Name,Category,Folders[].FullyQualifiedName,Inputs,Outputs,Source}`; list flattens `Data.Resources[].{EntityKey,Name,Category,Source}`. `get --local` matches only entityKey/`.uipx` project Id, never display name; use `search "<Name>" --local` for names. Fresh unpacked sibling `EntityKey` equals `.uipx` project Id. No solution: `Result:"Failure"`, `Message:"No solution found for --local"`, exit 1. General output: `{ MatchCount, Resources: [{ ResourceType, Resource }] }`. Cache: `~/.uip/case-resources/`, expiry 24 hours.

### uip maestro case registry get-connector

```bash
uip maestro case registry get-connector --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connector --type typecache-triggers --activity-type-id <uuid>
```

`-t, --type <type>` and `--activity-type-id <id>` are required; type is `typecache-activities` or `typecache-triggers`. Returns `{ Entry, Config }` (raw cache entry and connector config); it does not fetch connections.

### uip maestro case registry get-connection

Requires login:

```bash
uip maestro case registry get-connection --type typecache-activities --activity-type-id <uuid>
uip maestro case registry get-connection --type typecache-triggers --activity-type-id <uuid>
```

Required `-t, --type <type>` (`typecache-activities` or `typecache-triggers`) and `--activity-type-id <id>`. Returns `{ Entry, Config, Connections }`; use `Connections[].Id` as connector-task `connectionId`.

## uip maestro case process

Requires login:

```bash
uip maestro case process list
uip maestro case process list --folder-key <guid>
uip maestro case process list --filter "Name eq 'MyCase'"
uip maestro case process get <process-key> <feed-id>
uip maestro case process get <process-key> <feed-id> --folder-key <guid>
uip maestro case process run <process-key> <folder-key>
uip maestro case process run <process-key> <folder-key> --inputs '{"key":"value"}'
uip maestro case process run <process-key> <folder-key> --inputs @inputs.json --validate
```

`list`: `-t, --tenant <name>` defaults authenticated tenant; `-f, --folder-key <key>` required; `--filter <odata>`; `--login-validity <minutes>` default `10`. `get`: required process key/feed id and `-f, --folder-key <key>`; also tenant/login-validity. `run`: required process/folder keys; `-i, --inputs <json>` string, `@file.json`, or stdin; `-t, --tenant <name>`, `--release-key <key>`, `--feed-id <id>`, `--robot-ids <ids>` comma-separated, `--validate`, `--login-validity <minutes>`. Output `{ jobKey, state, traceId }`; use `jobKey` with `uip maestro case job traces`.

## uip maestro case job

Requires login:

```bash
uip maestro case job traces <job-key>
uip maestro case job traces <job-key> --pretty
uip maestro case job traces <job-key> --poll-interval 5000
uip maestro case job status <job-key>
uip maestro case job status <job-key> --detailed
```

`traces`: required GUID `<job-key>`, `-t, --tenant <name>`, `--poll-interval <ms>` default `2000`, `--traces-service <name>` default `llmopstenant_`, `--pretty`, `--login-validity <minutes>`. `status`: required `<job-key>`, tenant, `--folder-key <key>` default authenticated folder, `--detailed`, login-validity.

## uip maestro case instance

Requires login:

```bash
uip maestro case instance list
uip maestro case instance list --limit 20 --offset 0
uip maestro case instance list --process-key <key> --folder-key <key>
uip maestro case instance list --package-id <id> --error-code <code>
uip maestro case instance get <instance-id>
uip maestro case instance get <instance-id> --folder-key <key>
uip maestro case instance pause <instance-id>
uip maestro case instance resume <instance-id>
uip maestro case instance cancel <instance-id>
uip maestro case instance retry <instance-id>
uip maestro case instance variables <instance-id>
uip maestro case instance variables <instance-id> --parent-element-id <id>
uip maestro case instance incidents <instance-id>
uip maestro case instance asset <instance-id>
uip maestro case instance migrate <instance-id> <new-version>
uip maestro case instance goto <instance-id> '[{"sourceElementId":"A","targetElementId":"B"}]'
uip maestro case instance cursors <instance-id>
uip maestro case instance element-executions <instance-id>
```

Lifecycle commands accept `--folder-key` and `--comment`. Other commands list/get instances, variables, incidents, definition asset, migration, cursor movement, cursors, and element executions as shown.

## uip maestro case processes

Requires login:

```bash
uip maestro case processes list
uip maestro case processes incidents <process-key>
uip maestro case processes incidents <process-key> --folder-key <key>
```

## uip maestro case incident

Requires login:

```bash
uip maestro case incident summary
uip maestro case incident get <incident-id> --folder-key <key>
```

`<incident-id>` and `--folder-key <key>` are required for `get`.

## Global options (all commands)

| Option | Description |
|---|---|
| `--output json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |

<!-- END: case-commands.md -->