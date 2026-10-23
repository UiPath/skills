# Registry Discovery Reference

Resolve task types and entity identifiers for every case task. First run `uip maestro case sdd resolve`; inspect cache files manually only for its unresolved tasks (§ [Procedure](#procedure)).

## When to Use

During sdd.md → task.md interpretation, determine each task's **task type** (`agent`, `process`, `execute-connector-activity`, etc.) and entity identifier.

## Prerequisites

Run `uip login status --output json`, then `uip maestro case registry pull`, before inspecting caches. This unconditional Phase 1 gate must not be skipped because a cache is absent. **Exception — same-session fast path (SKILL.md Rule 3):** when the delegated design lane pull (`uipath-planner`, SKILL.md Rule 16) succeeded and `sdd.md` was just written from the confirmed in-memory model, reuse that cache, run verify-only against the planner's resolution ledger (SKILL.md Rule 3), and run the full gate on any doubt. Login/pull failure stops Phase 1 before planning artifacts are written.

The design lane lazily starts the same login → pull chain only when tenant-bound work first appears, then performs full identity resolution and the ambiguity/empty gate at Case Review; schema discovery remains Phase 2/3. A successful pull populates `~/.uip/case-resources/`. Discover through `sdd resolve` first; inspect only what it leaves. Do not use `uip maestro case registry search` as primary discovery. See [When a search returns nothing](#when-a-search-returns-nothing).

> **Missing file ≠ empty match.** Before searching `<type>-index.json`, verify it exists. If absent, run `uip maestro case registry pull` (not `--force`). Before pull, absence is a precondition failure, not zero results. After a successful pull, an absent index means zero tenant resources of that type: for non-creatable types (regular RPA process, agentic processes / Process Orchestration, action, case-management, connectors), proceed to placeholder; for creatable `agent`, `api-workflow`, and `business-rule`, first resolve any in-solution sibling using the per-type pre-gates ([agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution), [api-workflow/planning.md](plugins/tasks/api-workflow/planning.md#registry-resolution), [business-rule/planning.md](plugins/tasks/business-rule/planning.md#registry-resolution)) and [Handle Empty Results](#3-handle-empty-results). Only absence from both tenant index and local siblings is genuine empty and reaches the [Rule 18 / MUST-Confirm gate](#must-confirm-before-placeholder-fallback), where Create may be offered.

## Resolve with the CLI first

After pulling, resolve every task in one call. With a solution, run from the directory containing its `.uipx` so solution projects are read; the CLI searches cwd, parent, and grandparent only:

```bash
cd "<SOLUTION_DIR>" && uip maestro case sdd resolve "<SDD_PATH>" --out "<PROJECT_ROOT>/tasks/registry-resolved.json" --output json
```

`<SDD_PATH>` and `<PROJECT_ROOT>` are absolute or relative to `<SOLUTION_DIR>`; the ledger remains beside `sdd.md` in `tasks/`. Without a solution, run from the `sdd.md` directory; there are no siblings.

The command reads caches only, creates `tasks/`, performs index selection, exact portable-name matching, and SDD-folder narrowing, and writes the complete Rule 10 ledger; never author that ledger manually. Read `Data.Counts` (`tasks`, `selected`, `ambiguous`, `absent`), every `Data.Unresolved[]` row (one per `(name, taskType)` not settled, with `reason`, `usages`, and `creatable`), and `Data.Scope.siblingsChecked`. `siblingsChecked: true` means solution projects were read; a found sibling is `selected` with `source: "local"` and folder `solution_folder`, and beats same-named tenant entries in `matches`. `false` (no solution or CLI older than `@uipath/maestro-tool` 1.205.0-dev.9328) requires the per-type `registry search --local` check.

| `reason` | Meaning | Action |
|---|---|---|
| `absent` | No index entry, and when `siblingsChecked` is true no solution project | § [Procedure](#procedure) step 1 cross-type fallback, then § 3's in-solution sibling check ([Handle Empty Results](#3-handle-empty-results)) — skipped when `siblingsChecked` is `true` — then [MUST Confirm](#must-confirm-before-placeholder-fallback) |
| `ambiguous` | Several exact-name entries not narrowed by SDD folder | Never choose by position; use [MUST Confirm](#must-confirm-before-placeholder-fallback), one folder-labelled candidate; unanswered → `<UNRESOLVED>` |

Write each outcome into its task's `resolved`; never re-search a selected task. Normalized resources are `{name, identifierField, identifier, folder}`; `identifierField` is `id` for action apps and `entityKey` otherwise.

`wait-for-timer` has `selected: null` because it uses no tenant resource and is not a miss. Connector tasks likewise have `null`; resolve them through [connector-integration.md](connector-integration.md), whose outcome controls any marker.

> **Version guard.** If `sdd resolve` is unknown (`ErrorCode: "invalid_argument"`, exit 3), resolve every task manually with [Procedure](#procedure) and say so in one line. Exit 3 without that statement is failure, not fallback.

## When a search returns nothing

`uip maestro case registry search` may match an action app by `deploymentTitle` or slug `title`; older versions matched neither and returned `Success` with `ResultCount: 0`. When an expected resource searches empty: (1) do not retry different keywords; (2) read the cache directly using [Procedure](#procedure) and distinguish absence from unmatched; (3) record the gap in `registry-resolved.json`. Direct cache inspection is authoritative.

## MUST Confirm Before Placeholder Fallback

> **Design-time gate short-circuit.** If the same-session planner Case Design Lane ledger (SKILL.md Rule 16) has a `gateDecision`, the gate already ran. Execute `pick:<name>` by binding it, `resolve-at-build` by taking the placeholder path, and `create-during-build` through Create-on-Missing as if Create was selected. Re-ask only if stale against the current SDD ([planning.md](planning.md)) or the picked entry is no longer cached. A defaulted `resolve at build` has no `gateDecision` and takes the full gate.

> **Hard gate.** If the planning lookup batch has ≥1 empty result across relevant caches for any task / trigger / connector, STOP. Run AskUserQuestion before invoking any per-plugin Unresolved Fallback path or writing any placeholder element.

Use this prompt shape:

```
Question: <N> resource(s) not found in the registry: <one entry per unique (name, type): "<name>" (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]>. Append " — placeholder only" inside the (<type>) of any NON-creatable resource (RPA process, action, case-management, connector, agentic process). If NONE are creatable, add "(none can be built inline — placeholder only)" right after the count.
Header:   Resolve empties
Options:
  - Force pull and re-resolve
      → run `uip maestro case registry pull --force`, re-search caches, update registry-resolved.json with the
        second-pass results, then LOOP BACK to this prompt for any STILL-empty lookup.
  - Create missing resources inline   # shown ONLY when ≥1 still-empty is an `agent`, `api-workflow`, or `business-rule` AND the CLI has `registry --local`
      → the NEXT step lets you pick which to build inline (agent → uipath-agents,
        api-workflow → uipath-api-workflow, business-rule → uipath-rules); any you don't pick, plus all non-creatable
        empties (regular RPA process, action, case-management, connectors, agentic processes), become
        placeholders — mixing inline + placeholder is fine (§ Create-on-Missing).
  - Use placeholders for all
      → build nothing; EVERY missing resource (all <N>) becomes an `<UNRESOLVED>` placeholder (per-plugin Unresolved Fallback).
```

Group empties by unique `(name,type)`, listing all usages (`<Stage>/<Task>`), not by task. Ambiguous resources join the batch as folder-labelled candidate options plus `Use a placeholder`; unanswered or non-interactive remains `<UNRESOLVED>`. Apply once per planning batch, never as per-task yes/no. Force pull loops to this prompt. Create is only for `agent`, `api-workflow`, and `business-rule`, only when ≥1 remains empty and `registry --local` is supported; otherwise offer only Force pull/placeholders. Do not pre-judge names; always ask (SKILL.md Rule 18).

## Cache File Index

Each file under `~/.uip/case-resources/` is a JSON array:

| File | Identifier | Name | Folder |
|---|---|---|---|
| `agent-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `process-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `api-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `processOrchestration-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `caseManagement-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `businessRule-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `action-apps-index.json` | `id` | `deploymentTitle` | `deploymentFolder.fullyQualifiedName` |
| `typecache-activities-index.json` | `uiPathActivityTypeId` | `displayName` | *(none)* |
| `typecache-triggers-index.json` | `uiPathActivityTypeId` | `displayName` | *(none)* |

## Create-on-Missing build and rediscovery

Create only selected `agent`, `api-workflow`, and `business-rule` resources as in-solution siblings during Phase-1 planning; resolve them normally without placeholders. Use `uipath-agents`, `uipath-api-workflow`, and `uipath-rules`; never build connectors, regular RPA, agentic processes (Process Orchestration), Action Apps, or child cases here. The orchestration is type-agnostic for future non-connector kinds.

The sub-agent must invoke the installed type skill. Its brief must state that inability to locate/load it returns `{built:false, error:"skill <name> not installed"}` and does not improvise. `built:false` or death degrades to the per-plugin Failure contract; §4 rediscovery is the backstop; no exact-name `--local` match means Failure regardless of the report. Create never hard-fails the run.

### 0 — Prerequisite (solution must exist) + capability probe (once per run)

<!--skill-flavor:solution-prerequisite:start-->
**Solution prerequisite.** Register (§3) and `--local` rediscovery (§0/§4) require the case's enclosing `.uipx`; CLI walks cwd → parent → grandparent, which MUST resolve to the case's own solution, not an unrelated ancestor. The Create gate is Phase 1, before [Phase 2 Step 6.0](implementation.md) normally scaffolds it. If Create is selected without a `.uipx`, run `uip solution init <SolutionName>` using exactly the name and working-root location of Step 6.0 ([plugins/case/planning.md § Naming](plugins/case/planning.md#project-structure-prerequisites)); do not invent another. Everything below assumes the `.uipx` exists.
<!--skill-flavor:solution-prerequisite:end-->

<!--skill-flavor:capability-probe:start-->
**Capability probe.** At first need, run `uip maestro case registry list --local --output json` and cache the result. Unknown-option means `--local` unsupported: suppress Create and use placeholders. `No solution found for --local` confirms support; do not suppress. Do not scaffold during probe or pre-gate sibling check; there, record no local sibling and continue. Scaffold only inside Create after selection via `uip solution init`. First need is whichever comes first: the pre-gate per-type check ([agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution), [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution), [business-rule/planning.md § Registry Resolution](plugins/tasks/business-rule/planning.md#registry-resolution)) or this gate.
<!--skill-flavor:capability-probe:end-->

### 1 — Select

On Create, use `AskUserQuestion` with `multiSelect: true` for still-empty creatable resources, one option per unique `(name,type)`, labelled `<Name> (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]`. Non-creatable resources never appear and become placeholders. Cap at 4 options; batch successive prompts above 4. Checked builds once for all usages; unchecked makes every reference `<UNRESOLVED>`.

If an existing in-solution sibling of another kind already uses the name, ask to rename before building; the shared `solution_folder.<name>` and exact-name `search --local` namespace requires uniqueness. The same name under two selected types is handled by § 1c step 1's deterministic anchor/auto-rename, not another § 1 prompt.

```
Question: Build which of these inline? Checked → built as an in-solution sibling for all its usages; unchecked → every task using that name becomes an <UNRESOLVED> placeholder.
Header:   Build inline
multiSelect: true
Options:  one per unique (name, type): "<Name> (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]"
```

### 1b — Choose build kind

For each selected **agent**, ask one `AskUserQuestion` per agent, with equal options **Low-code** and **Coded (Python)**, header = agent name, no more than 4 questions per call. Never share one choice across agents. Non-interactive fallback: **Low-code** (`uip agent init`, platform default); coded uses `uip codedagent`. Put the choice in the brief's `Kind:` line ([agent/planning.md § Creating an Agent inline → Step 2](plugins/tasks/agent/planning.md#creating-an-agent-inline)); never infer from SDD. Coded agents carry the Orchestrator-deploy caveat ([agent/planning.md § Coded agents](plugins/tasks/agent/planning.md#creating-an-agent-inline)). API workflows and business rules skip this step; API workflow always uses JSON-DSL `Workflow.json`.

### 1c — Dedup the selected builds (one resource per name and type)

Run after § 1/§ 1b and before § 2, only for create-selected tasks. Placeholder/unchecked tasks remain independent; resolved tenant references are out of scope and use [io-binding Check 5](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness).

1. Group by `(intended resource name,type)` from each task's concrete SDD `Resolved Resource`, trimmed and case-insensitive. This is authoritative even without `tasks/registry-resolved.json`; it never contains `<UNRESOLVED>`. Ignore folder because inline siblings share one flat namespace. Resolve cross-type same-name collisions first: the earliest SDD task keeps the name; auto-rename the other type's group with a stage-derived, uniqueness-checked suggestion, then step 4.
2. A single-task group uses § 2.
3. Partition multi-task groups by the canonical pinned contract from [§ Step 1](plugins/tasks/create-inline-common.md#step-1--compute-the-pinned-io-contract): input type from the bound Case Variable's `Type`; `->` outputs typed from their Case Variable; `=` outputs excluded; cross-task-ref, literal, and `=metadata.*` fields type-deferred. Do not re-derive or read input type from the Inputs row's `Type` cell. Contracts unify only with identical field-name sets and agreeing known types. Deferred matches anything but cannot bridge different known types (`integer ↔ deferred ↔ string` remains separate). Greedily assign in SDD order to the first compatible subgroup; deferred may later be filled. The first-task subgroup is anchor and keeps the name.
   - Rename every other I/O-distinct subgroup once, using `<Name><Stage>` made unique against selections, all in-solution siblings, and tenant caches; then step 4.
   - For any multi-task same-I/O subgroup with differing intent, ask with no recommendation: `Same resource — build once` / `Different — split off the task(s) that don't belong` / `Abort`, quoting descriptions. On Different, mark split tasks and repeat until every subgroup is single-task or user-confirmed same-intent. Each resulting subgroup is renamed once. Non-interactive: split to singletons, rename each non-anchor in memory only, and emit one `high` review item per automatic split. A same-I/O, same-intent subgroup is one resource for all members.
4. For each rename, ask once; never edit SDD non-interactively. State `<old> → <new>`, exact cause, and permission to update `Resolved Resource` cells. If granted, atomically update both SDD identity mirrors: Section 2 cells and Section 4 dedup roll-up (`Used By Tasks`, with `Folder Path` and `Resource Identity` filled after registration). If denied/non-interactive, use the new name in memory only, warn that reruns bind the original sibling, and report the leftover per [Reject case](#reject-case). Never edit non-interactively.
5. Spawn § 2 one sub-agent per resulting resource, not per task. Purpose comes from the first SDD task ([create-inline-common.md § Step 1b](plugins/tasks/create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd)); canonical contract comes from [§ Step 1](plugins/tasks/create-inline-common.md#step-1--compute-the-pinned-io-contract).

Rename prompt:

```
Question: Task(s) <TaskName(s)> need a resource distinct from the anchor because <reason>. Per § 1c they build as a separate sibling: "<old>" → "<new>". Update their `Resolved Resource` cell(s) in sdd.md?
Header:   Rename write-back
Options:
  - Update sdd.md      → apply the edit now; re-runs then resolve by the new name (fully idempotent).
  - Keep sdd.md as-is  → rename in-memory THIS run only; the SDD keeps "<old>" (a re-run binds the ORIGINAL sibling — completion-report warning, § Reject case). NEVER edit the SDD non-interactively.
```

Use exactly one reason: I/O mismatch `their pinned I/O differs from the anchor (<concise field/type diff, e.g. adds output riskBand>)`; cross-type collision `another selected <anchor-type> resource already uses "<old>", and the solution_folder namespace is shared across resource types`; distinct intent `their descriptions have the same I/O but the user confirmed they represent a function distinct from the anchor`. Do not describe I/O for the latter two.

### 2 — Build (parallel, capped, skip-registration)

For every § 1c resource, compute its type brief ([agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline), [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline), [business-rule/planning.md § Creating a business rule inline](plugins/tasks/business-rule/planning.md#creating-a-business-rule-inline)) and spawn one sub-agent invoking its type skill. Spawn up to 10 concurrently and use waves above 10. Each skips registration and returns `{ built, path, finalInputs[], finalOutputs[], error? }`: agents use low-code `uip agent init --skip-solution-registration` or coded `uip codedagent`; API workflows use `uip api-workflow init <Name> --skip-solution-registration`; business rules use `uip rules init <Name> --skip-solution-registration`. The parent registers. The skill never runs a type `init`; only gate-selected resources build, never SDD content alone.

### 3 — Register (sequential)

<!--skill-flavor:register-step:start-->
Builds skip registration because `.uipx` is shared. After each wave, register each built sibling sequentially:

```bash
uip solution projects add "<built path>" "<solution .uipx>" --output json   # one per built sibling, sequential
```

Both positionals MUST be absolute; relative paths fail with `Failed to add project to solution` regardless of CWD ([implementation.md](implementation.md) § Step 6.0b). Then run `uip solution resources refresh` (Rule 15) before upload/debug.
<!--skill-flavor:register-step:end-->

### 3b — "Already exists" = adopt (kind-agnostic residual)

A prior interrupted build may be on disk but unregistered. If type `init` says directory exists/not empty or `project add` says `Project name already exists`, neither is failure. Check `uip maestro case registry list --local --output json`: if the name exists, `Category` identifies the registered owner; a different kind is a cross-kind collision—rename and rebuild. If absent, read the directory's `project.uiproj` `ProjectType`; matching kind means adopt:

<!--skill-flavor:adopt-register:start-->
1. Register with `uip solution projects add` using absolute paths. If it still says `Project name already exists`, stale declarations caused the collision. Get the key from `uip solution resources list --source local`, then run `uip solution resources remove <ResourceKey> --solution-folder <SolutionDir> --output json`; removing `process` cascades to `package`. Never delete declaration files manually ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)). Re-run project add, then `uip solution resources refresh`.
<!--skill-flavor:adopt-register:end-->
2. Continue at § 4. Never rebuild, Retry/Skip, or placeholder. Per-type verbs and kind markers are each plugin's § Failure blockquote.

### 4 — Rediscover + verify + bind (offline `--local`)

Rediscover by name with `search`, not `get`: `registry get <id> --local` matches only `entityKey`/project Id, so `get "<Name>"` returns 0. Run:

```bash
uip maestro case registry search "<Name>" --type <agent|api|businessRule> --local --output json   # `agent` for an agent sibling, `api` for an api-workflow sibling, `businessRule` for a business-rule sibling
```

Read PascalCase fields: `Code: "ResourceSearchSuccess"`, `Data.ResultCount`, and `Data.Resources[]` entries `{ ResourceType, Resource: {...} }`. Select exact `Resource.Name == <Name>` and `Resource.Source == "local"`; partial keyword results are insufficient. Confirm `Folders[0].FullyQualifiedName == "solution_folder"`. `Resource.EntityKey` is opaque local audit-only—not `.uipx` `Projects[].Id` or an on-disk id—and must never be written. No exact local match means failure contract.

Do not read I/O names from `Resource.{Inputs,Outputs}`: recursive PascalCase changes names (`poText` → `PoText`, `classification` → `Classification`). Read case-preserving names/types from `<sibling path>/entry-points.json`, under `entryPoints[0].input.properties` / `.output.properties`; wrong or absent keys silently produce an empty contract. For API workflows use fallback order flat `input.properties` → `input.schema.document.properties` → `Workflow.json` root schemas and warn on fallback ([api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution)). `--local` only locates/confirms.

`search`/`get` nest entries under `Data.Resources[].Resource.*`; `list --local` flattens `Data.Resources[].{EntityKey,Name,Category,Source}` and has no I/O. Sub-agent `finalInputs/finalOutputs` are liveness only; on-disk `entry-points.json` is authoritative.

Then:

- **Verify** sibling I/O against the pinned contract: matched, missing-in-sibling, extra-in-sibling. Agents/business rules are CLI-synced; API workflows are builder-consistent because no CLI verb writes entry-point I/O and `validate` does not flag drift.
- **Record** the reconciled contract in `registry-resolved.json`, resolve the task with `taskTypeId`/folder-path, and treat local `EntityKey` only as an audit resolution marker. Phase 2 must not tenant-`tasks describe` it; the recorded schema is authoritative. [Phase 2 Step 9 Phase A](implementation.md) and inline notes ([agent/impl-json.md](plugins/tasks/agent/impl-json.md), [api-workflow/impl-json.md](plugins/tasks/api-workflow/impl-json.md), [business-rule/impl-json.md](plugins/tasks/business-rule/impl-json.md)) skip the gather. Do not write `caseplan.case` data inputs/outputs or run io-binding in Phase 1.
- **Warn+diff** missing/extra; never block. A missing pinned output means its Case Variable and downstream task input, condition, or SLA reference will be empty at runtime; report it and never fabricate it.
- **Bind** `resourceKey="solution_folder.<Name>"` with `folderPath` binding `default` = `""`; `solution_folder` belongs only in `resourceKey` ([create-inline-common.md § Step 3](plugins/tasks/create-inline-common.md#step-3--binding-invariants)). For merged groups, resolve and bind every task to one sibling and one deduped binding pair ([bindings § Deduplication](plugins/variables/bindings/impl-json.md#deduplication)).

### Reject case

If a built sibling's task is later dropped, leave it on disk and registered in `.uipx`; report `built but not referenced`. It co-deploys harmlessly. Never silently deregister/delete/omit it. User-requested cleanup is manual: deregister from `.uipx` and delete the directory, and report it.

## Procedure

Use this manual lookup only for `Data.Unresolved[]`, or all tasks after the version guard.

### 1. Determine Which Cache Files to Search

Use the SDD component type's primary file, then compatible fallbacks:

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

For TIMER, skip lookup and emit `wait-for-timer`. `external-agent`/`external-workflow` are built as connector activities ([connector-activity § External agents and automations](plugins/tasks/connector-activity/planning.md#external-agents-and-automations)). If the primary has no match, search compatible cache files by portable name. For `process`, this fallback is a hard gate before unresolved/placeholder ([`plugins/tasks/process/planning.md` § Registry Resolution](plugins/tasks/process/planning.md#registry-resolution)). Do not cross-type-fallback `action`, `case-management`, `function`, `flow-process`, or `business-rule`: their identifiers are valid only in `action-apps-index.json`, `caseManagement-index.json`, `function-index.json`, `flow-index.json`, and `businessRule-index.json` respectively.

### 2. Search by Name and Folder Path

Extract the required concrete portable name; never use task display name or accept `<UNRESOLVED>`:

| Task type | Portable name | Folder hint |
|---|---|---|
| `process` / `agent` / `rpa` / `api-workflow` / `function` / `business-rule` | `Resolved Resource` | `Folder Path` |
| `action` | `Action App: <deploymentTitle>` in `HITL Implementation` | `Deployment Folder` |
| `case-management` | `Child Case` | `Folder Path` |

Use the corresponding folder only when it is concrete; an `<UNRESOLVED>` folder means name-only discovery. Filter with `cat ... | python3 -c "..."` or `Read`; do **not** use `node -e 'const fs=require("fs")...'` for cache reads (Rule 14).

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

Priority: exact name + folder; exact name with multiple folders narrowed by SDD folder; exact name with several candidates and no folder → record all in `matches`, `selected: null`, identity marker `<UNRESOLVED>`, and use the gate with one folder-labelled candidate each; no primary match → compatible fallback, except action/function/business-rule/case-management, which go directly to empty gate. Never use cache order as evidence.

### 3. Handle Empty Results

The [MUST Confirm](#must-confirm-before-placeholder-fallback) gate is a precondition. Agents, API workflows, and business rules missing tenant index must first search local siblings with `registry search "<name>" --type <agent|api|businessRule> --local --output json` ([agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution) / [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution) / [business-rule/planning.md § Registry Resolution](plugins/tasks/business-rule/planning.md#registry-resolution)). An exact `Source: "local"` match resolves and binds `solution_folder.<name>`; it is not empty. Only absence from tenant and local indexes reaches the gate.

After the gate, if Force pull was chosen it has already run:

```bash
uip maestro case registry pull --force
```

If still absent, or placeholders were chosen and Create was not selected, write `[REGISTRY LOOKUP FAILED: <name> in <folder>]` to `registry-resolved.json` and use the per-plugin Unresolved Fallback.

### 4. Return All Matches

Each Rule 10 entry must contain exactly:

- `stage`: exact SDD stage name
- `task`: exact SDD task name
- `taskType`: SDD schema-kebab task type
- `cacheFile`: basename actually searched
- `searchQuery`: concrete portable name
- `matches`: full exact-name objects, empty when none
- `selected`: selected full object or `null`
- `rationale`: selection or incompatibility reason

## Type Mapping

Map cache file to task-node `type` and identifier:

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

Additional undiscoverable types: `rpa`, `wait-for-timer`. The SDD component type determines task-node `type`; the cache supplies the identifier. SDD RPA matched in `process-index.json` remains `type: "rpa"`. Store `entityKey` in `registry-resolved.json`, not the task node; non-connectors reference `data.name` / `data.folderPath` = `=bindings.<id>` per their `impl-json.md`.

## Connector Tasks

For `typecache-activities-index.json` and `typecache-triggers-index.json`, use [connector-integration.md](connector-integration.md) for get-connection and `case spec`; discovery supplies only `uiPathActivityTypeId`. After pull, `uip maestro case spec` is the unified endpoint for identity, connection, inputs/outputs/filter contract, references with pre-built discoverCommand, and Phase-3 `caseShape`; it replaces `case tasks describe` + `is resources describe`. See [connector-integration.md § Step 3](connector-integration.md) for its call shape. Use only entries containing `uiPathActivityTypeId`; skip all others.

## Output Contract

Every match includes the entity identifier from the table. Connector implementations write it to `data.typeId`; non-connectors keep it only in `registry-resolved.json` and reference resources through `data.name` / `data.folderPath` = `=bindings.<id>`.

### `registry-resolved.json` content discipline

This is a structured log only. Each entry uses exactly `{stage, task, taskType, cacheFile, searchQuery, matches, selected, rationale}`. Re-ingest it as a performance cache only after association by `stage` + `task` and strict SDD matching in [planning.md § Design-lane carryover](planning.md#step-2--locate-and-parse-the-design-document); it never overrides SDD. `rationale` must explain selection (for example, `"exact name match in caseManagement folder"`), never verify-text drafts, SDD-vs-spec translations, or downstream-plugin behavior.

<!-- END: registry-discovery.md -->