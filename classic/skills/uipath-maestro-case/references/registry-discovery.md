# Registry Discovery Reference

Resolve every case task type and entity identifier. First run `uip maestro case sdd resolve` for every task; inspect caches manually only for unresolved rows.

## When to Use

Use while interpreting sdd.md → task.md to determine task type (`agent`, `process`, `execute-connector-activity`, etc.) and entity identifier.

## Prerequisites

<!--skill-flavor:prerequisite-login:start-->
Run `uip login status --output json`, then
<!--skill-flavor:prerequisite-login:end-->
`uip maestro case registry pull`, before any cache inspection or lookup. This is a Phase 1 hard gate, not a conditional refresh: never inspect the cache first and use its absence to skip the pull. Exception: use SKILL.md Rule 3's same-session fast path when the delegated planner design pull (`uipath-planner`, SKILL.md Rule 16) succeeded and `sdd.md` was just written from its confirmed in-memory model; run verify-only against the planner's resolution ledger. Any doubt requires the full gate. Login/pull failure stops Phase 1 before planning artifacts. Exit 0 with `Data.Errors` is partial: read rows; route each 5xx `typecache-*` row to [connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx); 401/403 stops Phase 1 as a login/permission failure.

The planner’s case design starts the same login → pull chain in the background only when tenant-bound work first appears, then performs full identity resolution and the ambiguity/empty gate at Case Review; it does not discover schemas there. A successful pull populates `~/.uip/case-resources/`. Read those files through `sdd resolve` first, then directly for what remains; do not use `uip maestro case registry search` as primary discovery. See § When a search returns nothing.

> **Missing file ≠ empty match.** Before searching `<type>-index.json`, verify it exists. If absent, run `uip maestro case registry pull` (not `--force`); before that pull, absence is a precondition failure. After a pull listing the type in `Data.ResourceTypes[]` rather than `Data.Errors[]`, an absent index means zero resources of that type; a type in `Data.Errors[]` is not empty. Route `typecache-*` errors to [connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx). For non-creatable types (regular RPA process, agentic processes / Process Orchestration, action, case-management, connectors), proceed to placeholder. For creatable `agent`, `api-workflow`, or `business-rule`, first resolve an in-solution sibling using [agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution), [api-workflow/planning.md](plugins/tasks/api-workflow/planning.md#registry-resolution), or [business-rule/planning.md](plugins/tasks/business-rule/planning.md#registry-resolution), and § Handle Empty Results. Only a resource absent from **both** the tenant index **and** the local siblings is genuinely empty → feed it to the [Rule 18 / § MUST-Confirm gate](#must-confirm-before-placeholder-fallback) (Create offered), NOT straight to placeholder.

## Resolve with the CLI first

After the pull, resolve every task in one call. With a solution, run from the directory containing its `.uipx`; it searches cwd, parent, and grandparent, never below, and reads solution projects. Run:

```bash
cd "<SOLUTION_DIR>" && uip maestro case sdd resolve "<SDD_PATH>" --out "<PROJECT_ROOT>/tasks/registry-resolved.json" --output json
```

`<SDD_PATH>` and `<PROJECT_ROOT>` are absolute or relative to `<SOLUTION_DIR>`; the ledger is beside `sdd.md` in `tasks/`. Without a solution, run from the `sdd.md` folder.

It does the part of discovery that has one right answer — which index each task type uses, the exact-name search on the task's portable name, the narrowing by the SDD's folder — and writes the whole Rule 10 ledger, creating `tasks/`. It reads caches only: no tenant, no network. Never hand-author the ledger it writes.

Read `Data.Counts` (`tasks`, `selected`, `ambiguous`, `absent`), `Data.Unresolved[]` (`reason`, `usages`, `creatable`), and `Data.Scope.siblingsChecked`. A local sibling is `selected` with `source: "local"` and `folder: solution_folder`, and beats a same-named tenant entry in `matches`. `siblingsChecked: false` (no solution or CLI older than `@uipath/maestro-tool` 1.205.0-dev.9328) requires the per-type `registry search --local` check.

| `reason` | Meaning/action |
|---|---|
| `absent` | No index entry, and when siblings were checked no solution project: run § Procedure step 1 cross-type fallback, then § 3 sibling check when not already done, then the [MUST Confirm gate](#must-confirm-before-placeholder-fallback). |
| `ambiguous` | Several exact-name entries and folder did not narrow them: never choose by position; use the gate with one folder-labelled option per candidate; unanswered → `<UNRESOLVED>`. |

Edit each outcome into that task's `resolved`; never re-search a selected task. Resolve normalizes resources as `{name, identifierField, identifier, folder}`; `identifierField` is `id` for action apps and `entityKey` otherwise. Read identity from those fields. `wait-for-timer` has `selected: null` because it needs no tenant resource. Connector tasks likewise have `null`; resolve them through [connector-integration.md](connector-integration.md), whose outcome controls markers.

### Two shapes, one record

`uip maestro case registry search "<Name>" --type <type> --output json` and `~/.uip/case-resources/<type>-index.json` contain equivalent records in different shapes: the index is a flat camelCase array (`entityKey`, `folders`); search wraps hits as `Data.Resources[] = {ResourceType, Resource: {…}}` with recursively PascalCase keys.

> **Version guard.** If `sdd resolve` is unknown (`ErrorCode: "invalid_argument"`, exit 3), resolve every task manually with § Procedure and say so in one line. Exit 3 without that message is a real failure.

## When a search returns nothing

Action-app search matches `deploymentTitle` and slug `title`; older CLI versions matched neither, returning `Success` and `ResultCount: 0` for deployed apps. Do not retry with different keywords. Read the cache directly using § Procedure, determine absent versus unmatched, and record the gap in `registry-resolved.json`. Direct cache inspection is authoritative.

## MUST Confirm Before Placeholder Fallback

> **Design-time gate short-circuit.** If the planner's case design ledger (SKILL.md Rule 16) has a `gateDecision`, do not re-ask unless stale against the current SDD ([planning.md](planning.md)) or the picked entry is gone. Execute `pick:<name>` by binding it; `resolve-at-build` via placeholder; `create-during-build` via Create-on-Missing as if Create was selected. A defaulted `resolve at build` has no decision and runs the full gate.

> **Hard gate.** If the planning lookup batch has ≥1 empty result across relevant cache files for any task / trigger / connector, STOP. Run AskUserQuestion before any per-plugin Unresolved Fallback or placeholder.

Prompt:

```text
Question: <N> resource(s) not found in the registry: <one unique (name, type): "<name>" (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]>. Put " — placeholder only" inside (<type>) for every NON-creatable resource (RPA process, action, case-management, connector, agentic process). If none are creatable, add "(none can be built inline — placeholder only)" after the count.
Header:   Resolve empties
Options:
  - Force pull and re-resolve
      → run `uip maestro case registry pull --force`, re-search caches, update registry-resolved.json with second-pass results, then loop to this prompt for still-empty lookups.
  - Create missing resources inline   # only when ≥1 still-empty agent, api-workflow, or business-rule and CLI has registry --local
      → next select which to build (agent → uipath-agents, api-workflow → uipath-api-workflow, business-rule → uipath-rules); unselected and all non-creatable empties become placeholders (§ Create-on-Missing).
  - Use placeholders for all
      → build nothing; every missing resource becomes an `<UNRESOLVED>` placeholder (per-plugin Unresolved Fallback).
```

Group empties by unique `(name, type)`, listing all usages, not by task. Ambiguous resources join as their own group with one folder-labelled option plus `Use a placeholder`; unanswered/non-interactive remains `<UNRESOLVED>`. Apply once per planning batch, not per task. Always ask; never pre-judge by resource-name heuristics. Create applies only to `agent`, `api-workflow`, and `business-rule`, only when `registry --local` is supported; without `--local`, offer only Force pull / Use placeholders. Force pull loops to this prompt.

## Cache File Index

Each file is a JSON array at `~/.uip/case-resources/`:

| File | Identifier | Name | Folder |
|---|---|---|---|
| `agent-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `process-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `api-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `processOrchestration-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `caseManagement-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `businessRule-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `action-apps-index.json` | `id` | `deploymentTitle` | `deploymentFolder.fullyQualifiedName` |
| `typecache-activities-index.json` | `uiPathActivityTypeId` | `displayName` | none |
| `typecache-triggers-index.json` | `uiPathActivityTypeId` | `displayName` | none |

## Create-on-Missing build and rediscovery

Create selected resources as in-solution siblings during Phase-1 planning and wire them as normal resolved tasks. v1 supports only `agent` via `uipath-agents`, `api-workflow` via `uipath-api-workflow`, and `business-rule` via `uipath-rules`; never build connectors, regular RPA processes, agentic processes, Action Apps, or child cases here. The sub-agent must load the type skill; if unavailable return `{built:false, error:"skill <name> not installed"}` and do not improvise. `built:false`, death, or no exact-name `--local` result becomes a placeholder through the per-plugin Failure contract; Create never hard-fails the run.

### 0 — Prerequisite (solution must exist) + capability probe (once per run)

<!--skill-flavor:solution-prerequisite:start-->
**Solution prerequisite.** Register (§3) and `--local` rediscovery (§0/§4) require the case's enclosing `.uipx`; the CLI walks cwd → parent → grandparent, so keep the working root free of an unrelated ancestor `.uipx`. The Create gate runs in Phase 1 before [Phase 2 Step 6.0](implementation.md) normally scaffolds the solution. If Create is selected without a `.uipx`, run `uip solution init <SolutionName>` first, deriving name and working-root location EXACTLY as Step 6.0 and [plugins/case/planning.md § Naming](plugins/case/planning.md#project-structure-prerequisites). Do not invent a name/location; mismatch double-inits or forks the solution. Everything below assumes `.uipx` exists.
<!--skill-flavor:solution-prerequisite:end-->

<!--skill-flavor:capability-probe:start-->
**Capability probe.** At first need, run `uip maestro case registry list --local --output json` and cache the result for the run. Unknown-option means `--local` unsupported: suppress Create and use placeholders. `No solution found for --local` confirms support and is not a suppress signal. Do not scaffold at probe or pre-gate sibling check; record no local sibling and proceed. Scaffold only after Create is selected. First need is whichever comes first: the pre-gate checks in [agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution), [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution), or [business-rule/planning.md § Registry Resolution](plugins/tasks/business-rule/planning.md#registry-resolution), or this gate.
<!--skill-flavor:capability-probe:end-->

### 1 — Select

For Create, ask an `AskUserQuestion` `multiSelect` with one option per unique `(name, type)` still-empty creatable resource (agents, API workflows, business rules), labelled `<Name> (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]`; cap each prompt at 4, batching larger sets. Checked builds once for all usages; unchecked references become placeholders. Non-creatable resources never appear.

If an existing in-solution sibling of another kind (`registry list --local`) already uses the selected name, ask to rename before building because the `solution_folder.<name>` namespace and exact-name `search --local` are shared. The same name under two selected types is handled by § 1c step 1's deterministic auto-rename, with only the step-4 write-back prompt.

```text
Question: Build which of these inline? Checked → built as an in-solution sibling for all its usages; unchecked → every task using that name becomes an <UNRESOLVED> placeholder.
Header:   Build inline
multiSelect: true
Options:  one per unique (name, type): "<Name> (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]"
```

### 1b — Choose build kind

For each selected `agent`, ask one `AskUserQuestion` (header = agent name; ≤4 questions per call) with equal options **Low-code** and **Coded (Python)**; never share one question among agents or infer from the SDD. Non-interactive defaults to **Low-code** (`uip agent init`); coded is `uip codedagent`. Put the choice in the brief's `Kind:` line ([agent/planning.md § Creating an Agent inline → Step 2](plugins/tasks/agent/planning.md#creating-an-agent-inline)). Coded integration is kind-agnostic on the case side but carries an Orchestrator-deploy caveat — see [agent/planning.md § Coded agents](plugins/tasks/agent/planning.md#creating-an-agent-inline). API workflows and business rules have no kind choice; API workflows always use JSON-DSL `Workflow.json`.

### 1c — Dedup the selected builds (one resource per name and type)

Run after § 1/§ 1b and before § 2; scope is create-selected tasks only. Placeholders and existing resolved references are independent. Use each task's concrete SDD `Resolved Resource`, trimmed and case-insensitive; it is authoritative even without `tasks/registry-resolved.json`. Group by `(intended resource name, type)`; folder is not part of the key.

1. Resolve cross-type collisions first: the name-only namespace permits one type to retain the name—the group whose earliest task is first in SDD order. Auto-rename the other with a stage-derived, uniqueness-checked suggestion.
2. A single-task group is an ordinary build.
3. For multi-task groups, compare each task's canonical pinned contract from [§ Step 1](plugins/tasks/create-inline-common.md#step-1--compute-the-pinned-io-contract): input type comes from the bound Case Variable's `Type`; extract outputs are typed from their Case Variable; `=` outputs are excluded; cross-task refs, literals, and `=metadata.*` are type-deferred. Do not re-derive types or read an input type from the Inputs row's `Type`. Greedily assign tasks in SDD order to the first sub-group whose known field types agree; field-name sets must match, known types must agree, deferred matches anything and is filled by a known type but cannot bridge different known types (`integer ↔ deferred ↔ string` does not collapse). The first-task sub-group is the anchor and keeps the name. Rename every other I/O-distinct sub-group once to a stage-derived `<Name><Stage>`, unique against selections, in-solution siblings of any kind, and tenant caches, bumping suffixes on collision.
4. Within a same-I/O group of differing intent, ask with no recommendation, quoting descriptions: `Same resource — build once` / `Different — split off the task(s) that don't belong` / `Abort`. On Different, the user marks tasks to split; repeat until each result is singleton or user-confirmed same-intent. Non-interactive splits to singletons, gives each non-anchor task a unique name, and emits one `high` review item per automatic split. Never put divergent tasks behind one rename. Same-I/O, same-intent members share one resource. Note the shared build and its call sites in the completion report.
5. For every resulting resource, run one § 2 sub-agent, not one per task. Purpose comes from the first task in SDD order among members ([create-inline-common.md § Step 1b](plugins/tasks/create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd)); pinned contract comes from any member ([§ Step 1](plugins/tasks/create-inline-common.md#step-1--compute-the-pinned-io-contract)).

Every rename gets one AskUserQuestion; never edit the SDD non-interactively:

```text
Question: Task(s) <TaskName(s)> need a resource distinct from the anchor because <reason>. Per § 1c they build as a separate sibling: "<old>" → "<new>". Update their `Resolved Resource` cell(s) in sdd.md?
Header:   Rename write-back
Options:
  - Update sdd.md      → apply the edit now; re-runs then resolve by the new name (fully idempotent).
  - Keep sdd.md as-is  → rename in-memory THIS run only; a re-run binds the ORIGINAL sibling (completion-report warning, § Reject case). NEVER edit the SDD non-interactively.
```

Use exactly one reason: I/O mismatch (`their pinned I/O differs from the anchor (<concise field/type diff, e.g. adds output riskBand>)`); cross-type collision (`another selected <anchor-type> resource already uses "<old>", and the solution_folder namespace is shared across resource types`); or distinct intent (`their descriptions have the same I/O but the user confirmed they represent a function distinct from the anchor`). Do not mention I/O for the latter two. If granted, atomically update both SDD mirrors: Section 2 `Resolved Resource` cells and Section 4 dedup roll-up (`Used By Tasks`, with `<new>` row and later `Folder Path` + `Resource Identity`). If denied/non-interactive, rename only in memory; warn that reruns bind the original sibling and leave the renamed sibling unreferenced, handled by [§ Reject case](#reject-case).

### 2 — Build (parallel, capped, skip-registration)

Compute each brief per [agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline), [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline), or [business-rule/planning.md § Creating a business rule inline](plugins/tasks/business-rule/planning.md#creating-a-business-rule-inline). Spawn one sub-agent per unique resource invoking `uipath-agents`, `uipath-api-workflow`, or `uipath-rules`, up to 10 concurrently in waves. Build without solution registration: low-code `uip agent init --skip-solution-registration`, coded `uip codedagent`, API workflow `uip api-workflow init <Name> --skip-solution-registration`, business rule `uip rules init <Name> --skip-solution-registration`. Return `{ built, path, finalInputs[], finalOutputs[], error? }`. The parent registers; this skill never runs type `init`, and SDD content alone never triggers a build.

### 3 — Register (sequential)

<!--skill-flavor:register-step:start-->
Build skips registration because `.uipx` is shared. After each wave, register each built sibling sequentially:

```bash
uip solution projects add "<built path>" "<solution .uipx>" --output json   # one per built sibling, sequential
```

Both positionals MUST be absolute paths; relative paths fail with `Failed to add project to solution` regardless of CWD (see [implementation.md](implementation.md) § Step 6.0b). Then run `uip solution resources refresh` (Rule 15) before upload/debug so solution resource files and `debug_overwrites.json` exist.
<!--skill-flavor:register-step:end-->

### 3b — "Already exists" = adopt (kind-agnostic residual)

An interrupted prior run can leave a built sibling **on disk but unregistered**. Nothing that reads `.uipx` `Projects[]` sees it — the pre-gate `--local` check misses, the gate fires, and the build/register step collides: the type's `init` fails *"directory exists / not empty"*, or `uip solution projects add` returns *"Project name already exists"*. **Neither is a failure.** Adopt:

1. **Kind-check the collision.** Name present in `uip maestro case registry list --local --output json` → its `Category` identifies a registered owner; a different kind = cross-kind name collision, NOT a prior build → rename the new resource (§1 name-uniqueness) and rebuild. Name absent (`list --local` also reads only `Projects[]`) → read the colliding directory's `project.uiproj` `ProjectType`. Matching kind → adopt:
<!--skill-flavor:adopt-register:start-->
2. **Register.** `uip solution projects add` (absolute paths). It can refuse *"Project name already exists"* even when the name is absent from `.uipx` `Projects[]` — its collision check keys on **stale resource declaration files** from a prior registration, not the manifest. Clear the stale declaration with `uip solution resources remove <ResourceKey> --solution-folder <SolutionDir> --output json` (key from `uip solution resources list --source local`; removing the `process` entry cascades to its `package` declaration — never delete either file by hand, see [bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)), re-run `project add`, then `uip solution resources refresh` regenerates them.
<!--skill-flavor:adopt-register:end-->
3. **Continue at §4** (rediscover, verify, bind). Never rebuild, never Retry/Skip, never placeholder — the sibling is already built.

Per-type verbs and kind markers: each plugin's § Failure blockquote.

### 4 — Rediscover + verify + bind (offline `--local`)

Rediscover by `search`, never `get`: `registry get <id> --local` matches only `entityKey`/project Id, not display name. Run:

```bash
uip maestro case registry search "<Name>" --type <agent|api|businessRule> --local --output json   # `agent` for an agent sibling, `api` for an api-workflow sibling, `businessRule` for a business-rule sibling
```

Read PascalCase recursively: `Code: "ResourceSearchSuccess"`, `Data.ResultCount`, and `Data.Resources[]` entries `{ ResourceType, Resource: {...} }`. Select exact `Resource.Name == <Name>` and `Resource.Source == "local"`; filter partial keyword matches. Confirm `Folders[0].FullyQualifiedName == "solution_folder"`. `Resource.EntityKey` is opaque, derived, and audit-only—not `.uipx` `Projects[].Id` or an on-disk id; never write it. No exact local match is a build/registration failure.

> ⚠️ **Do NOT read I/O field names from `Resource.{Inputs,Outputs}`.** `--output json` PascalCases object keys recursively, so the declared property keys come back mis-cased (`poText` → `PoText`, `classification` → `Classification`) — wiring against those names would bind to fields the resource doesn't have. Read the **case-preserving** names + types from the sibling's raw `entry-points.json` on disk instead (`<sibling path>/entry-points.json`), under `entryPoints[0].input.properties` / `.output.properties`. Reading the wrong/absent key returns `undefined`, yielding an empty contract → silent mis-wire. For **api-workflow** siblings apply the fallback chain (flat `input.properties` → `input.schema.document.properties` wrapper → `Workflow.json` root schemas; warn on any fallback — see [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution)). Use `--local` only to locate/confirm the sibling.

> Shapes: `search`/`get` nest each entry under `Data.Resources[].Resource.*`; `list --local` flattens to `Data.Resources[].{EntityKey,Name,Category,Source}` (no `Resource` wrapper, no I/O). Use `search` here because it matches by name and confirms the sibling; the sub-agent's returned `finalInputs/finalOutputs` are a liveness signal only — the on-disk `entry-points.json` is authoritative.

Then:

- **Verify** declared I/O from `entry-points.json` against the pinned contract as matched / missing-in-sibling / extra-in-sibling. Agents and business rules are CLI-synced; API workflows are builder-consistent because no CLI verb writes entry-point I/O and `validate` does not flag drift.
- **Record** the reconciled contract in `registry-resolved.json`; resolve the task with taskTypeId/folder-path. `taskTypeId` may hold local audit-only `EntityKey`; Phase 2 must not tenant-`tasks describe` it. The disk schema is authoritative; [Phase 2 Step 9 Phase A](implementation.md) and Built-inline notes ([agent/impl-json.md](plugins/tasks/agent/impl-json.md), [api-workflow/impl-json.md](plugins/tasks/api-workflow/impl-json.md), [business-rule/impl-json.md](plugins/tasks/business-rule/impl-json.md)) skip the gather. `caseplan.case` `data.inputs[]`/`data.outputs[]` and io-binding occur in Phase 2/3, not Phase 1.
- **Warn+diff**, never block. A missing pinned output means its Case Variable is never set; report that downstream task input, condition, or SLA references resolve empty at runtime. Never fabricate it.
- **Bind** `resourceKey="solution_folder.<Name>"` and `folderPath` binding `default` = `""`; `solution_folder` is only in `resourceKey`, otherwise runtime reports `folder not exist` ([create-inline-common.md § Step 3](plugins/tasks/create-inline-common.md#step-3--binding-invariants)). For merged groups, record/resolve/bind every task to one sibling and one deduped binding pair per [bindings § Deduplication](plugins/variables/bindings/impl-json.md#deduplication), not N pairs.

### Reject case

If a built sibling's task is later dropped, leave it on disk and name it in the completion report (`built but not referenced`). It remains registered in `.uipx` and co-deploys harmlessly; never silently deregister/delete/omit it. Manual cleanup means deregistering from `.uipx` and deleting the directory, flagged in the report.

## Procedure

Run this manual lookup only for `Data.Unresolved[]`, or every task after the version guard.

### 1. Determine Which Cache Files to Search

Use the sdd.md component type for the primary file and related files as fallbacks:

| sdd.md component type | Primary cache file |
|---|---|
| API_WORKFLOW | `api-index.json` |
| AGENTIC_PROCESS | `processOrchestration-index.json` |
| HITL | `action-apps-index.json` |
| RPA | `process-index.json` |
| AGENT | `agent-index.json` |
| FUNCTION | `function-index.json` |
| FLOW | `flow-index.json` |
| `business-rule` | `businessRule-index.json` |
| CASE_MANAGEMENT | `caseManagement-index.json` |
| CONNECTOR_ACTIVITY | `typecache-activities-index.json` |
| CONNECTOR_TRIGGER | `typecache-triggers-index.json` |
| PROCESS | `processOrchestration-index.json` |
| `external-agent` | `typecache-external-agent-activities-index.json` |
| `external-workflow` | `typecache-external-automation-activities-index.json` |
| TIMER | *(not in cache)* |

For `TIMER` ("not in cache"), skip the cache lookup — it has no registry representation; emit the `wait-for-timer` plugin shape. `external-agent` / `external-workflow` are built like a connector activity — see [connector-activity § External agents and automations](plugins/tasks/connector-activity/planning.md#external-agents-and-automations).

**Cross-type fallback:** The sdd.md component type label is not always accurate — the actual registry resource may be stored under a different type. For example, an "RPA" process may appear in `process-index.json`, or an "AGENTIC_PROCESS" might be in `process-index.json` instead of `processOrchestration-index.json`. If the primary cache file yields no match, search the other cache files using the task's type-specific portable name, preserving the existing fallback behavior. For `process` tasks the fallback is a hard gate before any unresolved/placeholder outcome — see [`plugins/tasks/process/planning.md` § Registry Resolution](plugins/tasks/process/planning.md#registry-resolution). **Exception: do not cross-type-fallback an `action`, `case-management`, `function`, `flow-process`, or `business-rule` lookup.** An Action App ID is valid only from `action-apps-index.json`, a child-case `entityKey` is valid only from `caseManagement-index.json`, a function `entityKey` is valid only from `function-index.json`, and a rule `entityKey` is valid only from `businessRule-index.json`, a flow `entityKey` is valid only from `flow-index.json`; a same-named process, agent, or API workflow is not a compatible substitute for any of these task types.

### 2. Search by Name and Folder Path

| Task type | Portable name | Folder hint |
|---|---|---|
| `process` / `agent` / `rpa` / `api-workflow` / `function` / `business-rule` | `Resolved Resource` | `Folder Path` |
| `action` | `Action App: <deploymentTitle>` in `HITL Implementation` | `Deployment Folder` |
| `case-management` | `Child Case` | `Folder Path` |

Portable name is required and never `<UNRESOLVED>`; do not use task display name. Filter with `cat ... | python3 -c "..."` or Read; never use `node -e 'const fs=require("fs")...'` for cache reads (Rule 14).

```bash
cat ~/.uip/case-resources/<type>-index.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    name = item.get('name', '') or item.get('deploymentTitle', '')
    if '<task_name>' in name:
        folders = item.get('folders', [])
        folder = folders[0].get('fullyQualifiedName', '') if folders else ''
        if not folder:
            df = item.get('deploymentFolder', {})
            folder = df.get('fullyQualifiedName', '') if df else ''
        ident = item.get('entityKey') or item.get('id') or item.get('uiPathActivityTypeId', '')
        print(json.dumps({'identifier': ident, 'name': name, 'folder': folder}))
"
```

Match priority: (1) exact name + exact folder; (2) exact name narrowed by sdd.md folder; (3) multiple exact matches without a folder—never choose by order, record all in `matches`, leave `selected: null` with `<UNRESOLVED>`, and use the gate with one folder-labelled option per candidate; (4) no primary match—compatible fallback, except action/function/business-rule/case-management proceed to empty gate.

### 3. Handle Empty Results

The [§ MUST: Confirm Before Placeholder Fallback](#must-confirm-before-placeholder-fallback) gate must already have run. If you have not yet run AskUserQuestion for the empty-result batch, do that first. Force pull and per-plugin Unresolved Fallback both flow through that gate. For `agent`, `api-workflow`, and `business-rule`, check an in-solution exact-name local sibling with `registry search "<name>" --type <agent|api|businessRule> --local --output json` per [agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution), [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution), or [business-rule/planning.md § Registry Resolution](plugins/tasks/business-rule/planning.md#registry-resolution). A `Source: "local"` match resolves and binds via `solution_folder.<name>`; it is not empty, does not reach the gate, and does not Create. Only absence from tenant and local is empty.

If no match is found across all relevant cache files:

1. **Already gated above.** AskUserQuestion confirmation already ran. If the user picked `Force pull and re-resolve`, the force pull has already executed; this step is reached for lookups that remained empty after the second-pass search.
   ```bash
   # already executed during the gate's Force-pull branch:
   uip maestro case registry pull --force
   ```
2. If still no match (or the user picked `Use placeholders for all`, and any creatable resource was not selected for Create), mark it in `registry-resolved.json`: `[REGISTRY LOOKUP FAILED: <name> in <folder>]` and proceed to the per-plugin Unresolved Fallback path.

### 4. Return All Matches

For each result record Rule 10 keys exactly: `stage` (exact SDD stage), `task` (exact SDD task), `taskType` (SDD schema-kebab type), `cacheFile` (searched basename), `searchQuery` (concrete type-specific portable name), `matches` (full exact-name objects; `[]` when none), `selected` (full selected object or `null`), and `rationale` (why selected or why no compatible match).

## Type Mapping

After finding a match, map the **cache file type** (not the sdd.md component type) to the JSON `type` value written into the task node:

| Cache file | Task `type` | Identifier |
|---|---|---|
| `agent-index.json` | `agent` | `entityKey` |
| `process-index.json` | `rpa` | `entityKey` |
| `api-index.json` | `api-workflow` | `entityKey` |
| `function-index.json` | `function` | `entityKey` |
| `flow-index.json` | `flow-process` | `entityKey` |
| `businessRule-index.json` | `business-rule` | `entityKey` |
| `processOrchestration-index.json` | `process` | `entityKey` |
| `caseManagement-index.json` | `case-management` | `entityKey` |
| `action-apps-index.json` | `action` | `id` |
| `typecache-activities-index.json` | `execute-connector-activity` | `uiPathActivityTypeId` |
| `typecache-triggers-index.json` | `wait-for-connector` | `uiPathActivityTypeId` |
| `typecache-external-agent-activities-index.json` | `external-agent` | `uiPathActivityTypeId` |
| `typecache-external-automation-activities-index.json` | `external-workflow` | `uiPathActivityTypeId` |

Additional non-cache types are `rpa` and `wait-for-timer`. The sdd.md component type determines task-node `type`; the cache supplies `entityKey`. An RPA match in `process-index.json` still writes `type: "rpa"`. The identifier belongs in `registry-resolved.json`, not the task node; non-connectors use `data.name` / `data.folderPath` = `=bindings.<id>` per the type's `impl-json.md`.

## Connector Tasks

For `typecache-activities-index.json` and `typecache-triggers-index.json`, use [connector-integration.md](connector-integration.md). Registry discovery supplies only `uiPathActivityTypeId`; connection, `case spec`, identity, contract, and references are handled there. After pull, `uip maestro case spec` is the unified endpoint replacing legacy `case tasks describe` + `is resources describe`; in Phase 3 it can return a populated `caseShape`. See [connector-integration.md § Step 3](connector-integration.md). Use only entries containing `uiPathActivityTypeId`; skip other activities.

## Output Contract

Every match includes its entity identifier from the table. Connector implementations write it to `data.typeId`; non-connectors keep it in `registry-resolved.json`, while nodes reference `data.name` / `data.folderPath` = `=bindings.<id>`.

### `registry-resolved.json` content discipline

This is a structured Rule-10 log only. Every entry has exactly `{stage, task, taskType, cacheFile, searchQuery, matches, selected, rationale}`. Re-ingest as a performance cache only after associating by `stage` + `task` and strict SDD matching in [planning.md § Design carryover](planning.md#step-2--locate-and-parse-the-design-document); it never overrides the SDD. `rationale` must explain selection (for example, `"exact name match in caseManagement folder"`), never hold verify-text drafts, SDD-vs-spec translations, or downstream-plugin behavior claims.

<!-- END: registry-discovery.md -->
