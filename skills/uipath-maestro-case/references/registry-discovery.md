# Registry Discovery Reference

Resolve the correct task type and entity identifier for a case task by searching the local registry cache files directly.

## When to Use

During sdd.md → task.md interpretation, when you need to determine:
- What **task type** to use for a task (e.g., `agent`, `process`, `execute-connector-activity`)
- What **entity identifier** to reference in the task.md

## Prerequisites

Run `uip maestro case registry pull` before any lookups. This populates the local cache at `~/.uip/case-resources/`. All subsequent discovery is done by reading these cache files directly — **do not** rely on `uip maestro case registry search` as the primary discovery method. See the "CLI Search Gaps" section below for the reason.

> **Missing file ≠ empty match.** Before searching any `<type>-index.json`, verify it exists on disk. If it does not, run `uip maestro case registry pull` (not `--force` — a normal pull is enough for first-time population). A missing file **before** a pull is a precondition failure, not a 0-result lookup. **After a successful pull, a still-absent index means the tenant has zero resources of that type — which IS the genuine 0-matches case.** For **non-creatable** types (regular RPA process, agentic processes / Process Orchestration, action, case-management, connectors) → proceed to placeholder. For a **creatable** type (`agent`, `api-workflow`), a zero-resource tenant index is the genuine 0-matches case where inline **Create** applies — but **first resolve any in-solution sibling** (a prior run may have already built it; see the per-type pre-gate checks — [agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution), [api-workflow/planning.md](plugins/tasks/api-workflow/planning.md#registry-resolution) — and § Handle Empty Results below). Only a resource absent from **both** the tenant index **and** the local siblings is genuinely empty → feed it to the [Rule 17 / § MUST-Confirm gate](#must-confirm-before-placeholder-fallback) (Create offered), NOT straight to placeholder.

## CLI Search Gaps

The `uip maestro case registry search` command has known gaps. In particular, it fails to return results for certain resource types even when the resource is present in the cache (most commonly affecting **action-apps** / HITL tasks). When search returns an empty or incomplete result for a resource you know exists:

1. Do **not** retry the same search with different keywords.
2. Fall back to reading the cache files directly using the procedure in this document.
3. Record the gap in `registry-resolved.json` so the audit trail reflects the fallback.

Direct cache-file inspection is the authoritative discovery method for this skill.

## MUST Confirm Before Placeholder Fallback

> **Hard gate.** If the planning-phase lookup batch returns ≥1 empty result (no match across all relevant cache files for any task / trigger / connector), STOP. Run AskUserQuestion before invoking any per-plugin Unresolved Fallback path or writing any placeholder T-entry.

Required prompt shape:

```
Question: <N> registry lookup(s) returned 0 matches: <comma-list of <name> in <folder>>.
Header:   Resolve empties
Options:
  - Force pull and re-resolve
      → run `uip maestro case registry pull --force`, re-search caches, update registry-resolved.json with the
        second-pass results, then LOOP BACK to this prompt for any STILL-empty lookup.
  - Create the missing resource(s) inline   # shown ONLY when ≥1 still-empty is an `agent` or `api-workflow` AND the CLI has `registry --local`
      → multi-select which to build as in-solution siblings (agent → uipath-agents,
        api-workflow → uipath-api-workflow); build them (§ Create-on-Missing). Unselected items
        + all non-creatable empties (regular RPA process, action, case-management, connectors, agentic
        processes) → placeholder.
  - Skip and use placeholders
      → proceed to per-plugin Unresolved Fallback paths for the unmatched lookups.
```

**Apply once per planning batch, not per-task.** Each option is batch-level — never a per-task yes/no chain. Force pull loops back to this same prompt for whatever stays empty. The **Create** option covers **agents and API workflows only** (never regular RPA process, action apps, child cases, connectors, or agentic processes); it appears only when ≥1 still-empty is creatable AND the CLI supports `registry --local` (capability probe — see [§ Create-on-Missing](#create-on-missing-build-and-rediscovery)). When `--local` is absent the gate degrades to Force pull / Skip exactly as before.

**Do NOT pre-judge.** Resource-name heuristics ("looks vendor-specific, won't be in registry anyway", "this is an obvious custom connector") are the user's call to make, not the agent's. Always ask. SKILL.md Rule 17.

## Cache File Index

Each resource type has a `<type>-index.json` file at `~/.uip/case-resources/`:

| File | Identifier field | Name field | Folder field |
|------|-----------------|------------|--------------|
| `agent-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `process-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `api-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `processOrchestration-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `caseManagement-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `action-apps-index.json` | `id` | `deploymentTitle` | `deploymentFolder.fullyQualifiedName` |
| `typecache-activities-index.json` | `uiPathActivityTypeId` | `displayName` | *(none)* |
| `typecache-triggers-index.json` | `uiPathActivityTypeId` | `displayName` | *(none)* |

Each file is a JSON array of resource entries.

## Create-on-Missing build and rediscovery

When the user picks **Create** at the gate, the skill builds each selected resource as an **in-solution sibling** (during Phase-1 planning) and wires it in as a normal resolved task — no placeholder. **v1 builds two kinds — `agent` (via `uipath-agents`) and `api-workflow` (via `uipath-api-workflow`)**; the orchestration below is type-agnostic so other non-connector kinds can be enabled later via their own type skill. Connectors, regular RPA process, and agentic processes (Process Orchestration) are never built here. Action Apps and child cases are also never built here.

> **Create depends on the type skill being installed.** The build runs in a sub-agent that invokes the resource's type skill (`uipath-agents` / `uipath-api-workflow`). The Step-2 brief instructs the sub-agent: if it cannot locate/load that skill, return `{built:false, error:"skill <name> not installed"}` — do NOT improvise a build. That `built:false` (or a sub-agent that dies) degrades to a placeholder via the per-plugin Failure contract, and §4 rediscovery is the backstop (no exact-name `--local` match → Failure contract regardless of what the sub-agent reports) — Create never hard-fails the run.

### 0 — Prerequisite (solution must exist) + capability probe (once per run)

**Solution prerequisite.** Register (§3) and `--local` rediscovery (§0/§4) all require an enclosing solution `.uipx` (the CLI walks cwd → parent → grandparent — that walk MUST resolve to the case's *own* solution: keep the working root free of an unrelated ancestor `.uipx`, else the built sibling registers into the wrong solution). The Create gate fires in **Phase 1 planning**, *before* [Phase 2 Step 6.0](implementation.md) normally scaffolds the solution — so on a fresh run no `.uipx` exists yet. **When the user selects Create and no `.uipx` is found, run `uip solution init <SolutionName>` first — deriving `<SolutionName>` and its working-root location EXACTLY as Step 6.0 does** (the canonical rule: [plugins/case/planning.md § Naming](plugins/case/planning.md#project-structure-prerequisites)). Do NOT invent a different name/location: Step 6.0 keys its idempotent skip on that exact `.uipx`, so a mismatch double-inits or forks the solution (sibling in one `.uipx`, case project in another). Everything below assumes the `.uipx` now exists.

**Capability probe.** Confirm the CLI supports local discovery: run `uip maestro case registry list --local --output json`. Distinguish the failure modes: an **unknown-option** error → `--local` is unsupported → **suppress the Create option entirely** (the gate stays Force pull / Skip), use placeholders. A **`No solution found for --local`** error is NOT a suppress signal — it confirms `--local` IS supported (a missing-solution error, not unknown-option). **Do NOT scaffold at probe time.** At the pre-gate in-solution sibling check (which fires before Create is offered), "No solution found" simply means no sibling exists yet — a solution holds no siblings before it exists — so record "no local sibling" and proceed to the gate. Scaffolding (`uip solution init`, the Solution prerequisite above) happens **only inside the Create flow, after the user selects Create** — never during the probe or the pre-gate sibling check. Offer Create unless the probe returns the unknown-option (unsupported) case. Run the probe **at first need and cache the result for the rest of the run** — whichever comes first: the pre-gate in-solution sibling check ([agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution) / [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution), which also gates on `--local`) or this gate.

### 1 — Select

On Create, present an `AskUserQuestion` **multiSelect** of the still-empty **creatable** resources — agents and API workflows. The option list is capped at 4; when >4 creatable resources are empty, batch the selection across successive prompts (≤4 each). Checked → build. Unchecked items **and all non-creatable empties** (regular RPA process, action, connectors, agentic processes, …) → `<UNRESOLVED>` placeholder. If two selected resources share a name — or a selected resource's name is already used by an existing in-solution sibling of another kind (`registry list --local`) — AskUserQuestion to rename before building: the `solution_folder.<name>` sentinel resourceKey and the exact-name `search --local` rediscovery (§4) both key on the name, which must be unique across kinds (the namespace is shared).

### 1b — Choose build kind

For each selected **agent**, ask the build kind before building: an `AskUserQuestion` with options **Low-code** and **Coded (Python)** — presented as **equal choices** (neither marked recommended); **one `AskUserQuestion` question per agent** (header = agent name; ≤4 questions per call) — **never one shared question applied to all**. For a non-interactive run the fallback is **Low-code** (`uip agent init`, the platform default kind); coded is `uip codedagent`. The choice sets the brief's `Kind:` line ([agent/planning.md § Creating an Agent inline → Step 2](plugins/tasks/agent/planning.md#creating-an-agent-inline)) and the sub-agent builds that kind. Kind is **never inferred from the SDD**. Coded integration is kind-agnostic on the case side but carries an Orchestrator-deploy caveat — see [agent/planning.md § Coded agents](plugins/tasks/agent/planning.md#creating-an-agent-inline). **API workflows have no kind choice** — skip this step for them; the build is always the JSON-DSL `Workflow.json`.

### 2 — Build (parallel, capped, skip-registration)

For each selected resource, compute its build brief — agents per [agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline), API workflows per [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline) — and **spawn one sub-agent per resource that invokes its type skill** (`uipath-agents` / `uipath-api-workflow`). Spawn **up to 10 concurrently; process in waves** if more are selected (cap is a resource throttle, not a safety mechanism). Each sub-agent builds **without registering the project into the solution** (agents: per the §1b kind — low-code `uip agent init --skip-solution-registration` or coded `uip codedagent`; API workflows: `uip api-workflow init <Name> --skip-solution-registration`; the parent registers either way, § 3) and returns `{ built, path, finalInputs[], finalOutputs[], error? }`.

The skill itself never runs the type CLI's `init` — build knowledge lives in the type skill. Only gate-selected resources are built; SDD content alone never triggers a build.

### 3 — Register (sequential)

The `.uipx` is a shared file; concurrent registration races. So build skips registration, and **the parent registers each built sibling sequentially** after the wave returns:

```bash
uip solution project add "<built path>" "<solution .uipx>" --output json   # one per built sibling, sequential
```

Both positionals MUST be absolute paths — the relative form fails with `Failed to add project to solution` regardless of CWD (see [implementation.md](implementation.md) § Step 6.0b). Then run `uip solution resources refresh` (Rule 14) so the solution-level resource files + `debug_overwrites.json` are generated before any upload/debug.

### 3b — "Already exists" = adopt (kind-agnostic residual)

An interrupted prior run can leave a built sibling **on disk but unregistered**. Nothing that reads `.uipx` `Projects[]` sees it — the pre-gate `--local` check misses, the gate fires, and the build/register step collides: the type's `init` fails *"directory exists / not empty"*, or `uip solution project add` returns *"Project name already exists"*. **Neither is a failure.** Adopt:

1. **Kind-check the collision.** Name present in `uip maestro case registry list --local --output json` → its `Category` identifies a registered owner; a different kind = cross-kind name collision, NOT a prior build → rename the new resource (§1 name-uniqueness) and rebuild. Name absent (`list --local` also reads only `Projects[]`) → read the colliding directory's `project.uiproj` `ProjectType`. Matching kind → adopt:
2. **Register.** `uip solution project add` (absolute paths). It can refuse *"Project name already exists"* even when the name is absent from `.uipx` `Projects[]` — its collision check keys on **stale resource declaration files** from a prior registration, not the manifest. Delete `resources/solution_folder/package/<Name>.json` and the kind's `resources/solution_folder/process/<category>/<Name>.json`, re-run `project add`, then `uip solution resources refresh` regenerates them.
3. **Continue at §4** (rediscover, verify, bind). Never rebuild, never Retry/Skip, never placeholder — the sibling is already built.

Per-type verbs and kind markers: each plugin's § Failure blockquote.

### 4 — Rediscover + verify + bind (offline `--local`)

Rediscover **by name** with `search` (not `get`): `registry get <id> --local` matches only on `entityKey`/project Id, never the display name, so `get "<Name>"` returns 0. `search` matches the keyword against the name. Read keys in **PascalCase** (`--output json` PascalCases recursively):

```bash
uip maestro case registry search "<Name>" --type <agent|api> --local --output json   # `agent` for an agent sibling, `api` for an api-workflow sibling
```

`Code: "ResourceSearchSuccess"`, `Data.ResultCount`, `Data.Resources[]` each `{ ResourceType, Resource: {...} }`. Select the entry whose `Resource.Name` exactly equals `<Name>` and `Resource.Source == "local"` (keyword search may return partial-name matches — filter to the exact name). Use this `--local` result to **confirm the sibling exists** and registered (`Source == "local"`, `Folders[0].FullyQualifiedName == "solution_folder"`). `Resource.EntityKey` is an opaque, derived local key (NOT the `.uipx` `Projects[].Id`, NOT any on-disk id) — **audit-only**; the node binds by name+folder, so never write it. No exact-name local match → the build/registration didn't take → failure contract.

> ⚠️ **Do NOT read I/O field names from `Resource.{Inputs,Outputs}`.** `--output json` PascalCases object keys recursively, so the declared property keys come back mis-cased (`poText` → `PoText`, `classification` → `Classification`) — wiring against those names would bind to fields the resource doesn't have. Read the **case-preserving** names + types from the sibling's raw `entry-points.json` on disk instead (`<sibling path>/entry-points.json`), under `entryPoints[0].input.properties` / `.output.properties`. Reading the wrong/absent key returns `undefined`, yielding an empty contract → silent mis-wire. For **api-workflow** siblings apply the fallback chain (flat `input.properties` → `input.schema.document.properties` wrapper → `Workflow.json` root schemas; warn on any fallback — see [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution)). Use `--local` only to locate/confirm the sibling.

> Shapes: `search`/`get` nest each entry under `Data.Resources[].Resource.*`; `list --local` flattens to `Data.Resources[].{EntityKey,Name,Category,Source}` (no `Resource` wrapper, no I/O). Use `search` here because it matches by name and confirms the sibling; the sub-agent's returned `finalInputs/finalOutputs` are a liveness signal only — the on-disk `entry-points.json` is authoritative.

Then, in order:

- **Verify** — reconcile the sibling's declared I/O (case-preserving names from `entry-points.json` per the warning above; agents: CLI-synced; api-workflows: build-kept-consistent — no CLI verb writes entry-point I/O, the builder back-fills it and `validate` won't flag drift) against the pinned contract → matched / missing-in-sibling / extra-in-sibling.
- **Record** the reconciled contract into `tasks.md` + `registry-resolved.json` and resolve the task (taskTypeId/folder-path filled) — now a normal resolved task. `taskTypeId` holds the local audit-only `EntityKey` as a resolution marker only — **Phase 2 must NOT tenant-`tasks describe` it**; the I/O schema recorded here (from the sibling's `entry-points.json`) is authoritative, and [Phase 2 Step 9 Phase A](implementation.md) + the per-type Built-inline notes ([agent/impl-json.md](plugins/tasks/agent/impl-json.md), [api-workflow/impl-json.md](plugins/tasks/api-workflow/impl-json.md)) skip the gather for inline siblings. (The `caseplan.json` `data.inputs[]`/`data.outputs[]` write and the io-binding pass happen in Phase 2/3 when the resolved task is materialized, exactly like any other resolved resource — **NOT in Phase 1**.)
- **Warn+diff** missing/extra into the completion report; **never block**. A **missing-in-sibling** pinned output means the Case Variable it feeds is never set — record in the completion report that any downstream reference (task input, condition, SLA) will resolve empty at runtime, so the user can decide to re-invoke the build to add the field or accept it. **Never auto-fabricate** the missing output to silence the warning.
- **Bind** with `resourceKey="solution_folder.<Name>"` **and `folderPath` binding `default` = `""`** (runtime folder — empty = co-located; the `solution_folder` sentinel lives ONLY in `resourceKey`, NOT in `folderPath`, else runtime `folder not exist` — see [agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline) / [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline)). It binds by name+folder, so `EntityKey` stays audit-only.

### Reject case

If a built sibling's task is later dropped (user aborts or removes it on `Request changes`), leave the sibling **on disk** (it is reusable) and **name it in the completion report** ("built but not referenced"). It stays **registered in the `.uipx`** (Step 3 already added it), so it co-deploys with the solution as an unused sibling — harmless; do **not** silently deregister. If the user wants it gone, that is manual cleanup (deregister from the `.uipx` and delete the directory), flagged in the report. Never silently delete it, never silently omit it.

## Procedure

### 1. Determine Which Cache Files to Search

Use the component type from the sdd.md to identify the **primary** cache file, then always include related files as fallbacks. This is important because the sdd.md component type label may not match the actual registry resource type (e.g., an "RPA" task in the sdd.md may be registered as `process` in the registry).

| sdd.md component type | Primary cache file |
|---|---|
| API_WORKFLOW | `api-index.json` |
| AGENTIC_PROCESS | `processOrchestration-index.json` |
| HITL | `action-apps-index.json` |
| RPA | `process-index.json` |
| AGENT | `agent-index.json` |
| CASE_MANAGEMENT | `caseManagement-index.json` |
| CONNECTOR_ACTIVITY | `typecache-activities-index.json` |
| CONNECTOR_TRIGGER | `typecache-triggers-index.json` |
| PROCESS | `process-index.json` |
| EXTERNAL_AGENT | *(not in cache)* |
| TIMER | *(not in cache)* |

For types marked "not in cache" (`EXTERNAL_AGENT`, `TIMER`), skip the cache lookup — these have no registry representation. `TIMER` → emit the `wait-for-timer` plugin shape. **`EXTERNAL_AGENT` has no generation plugin here — never write `type: external-agent`; model as `api-workflow` / `execute-connector-activity` per Rule 16.**

**Cross-type fallback:** The sdd.md component type label is not always accurate — the actual registry resource may be stored under a different type. For example, an "RPA" process may appear in `process-index.json`, or an "AGENTIC_PROCESS" might be in `process-index.json` instead of `processOrchestration-index.json`. If the primary cache file yields no match, search the other cache files using the task's type-specific portable name, preserving the existing fallback behavior. **Exception: do not cross-type-fallback an `action` or `case-management` lookup.** An Action App ID is valid only from `action-apps-index.json`, and a child-case `entityKey` is valid only from `caseManagement-index.json`; a same-named process is not a compatible substitute for either task type.

### 2. Search by Name and Folder Path

For each task in the sdd.md, extract its concrete portable name from the type-specific field below. Use the corresponding folder only when it is concrete; `<UNRESOLVED>` means name-only discovery.

| Task type | Portable name query | Folder hint |
|---|---|---|
| `process` / `agent` / `rpa` / `api-workflow` | `Resolved Resource` | `Folder Path` |
| `action` | `Action App: <deploymentTitle>` in `HITL Implementation` | `Deployment Folder` |
| `case-management` | `Child Case` | `Folder Path` |

The portable name is REQUIRED and never `<UNRESOLVED>`. Do not fall back to the task display name. Then filter the cache file:

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

**Match priority:**
1. **Exact name + exact folder** — strongest match, use directly.
2. **Exact name, multiple folders** — pick the one matching the sdd.md folder path.
3. **Exact name, no folder specified in sdd.md** — pick the first exact-name match; note alternatives in `registry-resolved.json`.
4. **No match in primary cache file** — apply the compatible cross-type fallback above. For `action` and `case-management`, do not search another cache type; proceed to the empty-result gate.

### 3. Handle Empty Results

> **Required precondition.** Before reaching this step, the [§ MUST: Confirm Before Placeholder Fallback](#must-confirm-before-placeholder-fallback) gate above MUST have been satisfied. If you have not yet run AskUserQuestion for the empty-result batch, do that first. Force pull and per-plugin Unresolved Fallback both flow through that gate.

> **Agents & API workflows: resolve in-solution siblings before counting a lookup empty.** For an `agent` or `api-workflow` that misses the tenant index, first check for an existing in-solution sibling via `registry search "<name>" --type <agent|api> --local --output json` (per [agent/planning.md](plugins/tasks/agent/planning.md#registry-resolution) / [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution)). A `Source: "local"` exact-name match **resolves** it (bind via `solution_folder.<name>`) — it is NOT empty and does NOT reach the gate or Create. Only resources absent from **both** the tenant index and the local siblings are empty here. (This keeps re-runs idempotent: an already-built sibling resolves instead of rebuilding.)

If no match is found across all relevant cache files:

1. **Already gated above.** AskUserQuestion confirmation already ran. If the user picked `Force pull and re-resolve`, the force pull has already executed; this step is reached for lookups that remained empty after the second-pass search.
   ```bash
   # already executed during the gate's Force-pull branch:
   uip maestro case registry pull --force
   ```
2. If still no match (or the user picked `Skip and use placeholders`, and any creatable resource was not selected for Create), mark it in tasks.md: `[REGISTRY LOOKUP FAILED: <name> in <folder>]` and proceed to the per-plugin Unresolved Fallback path.

### 4. Return All Matches

Collect all matching results for the `registry-resolved.json` debug output. Record Rule 9's exact keys:
- `stage`: exact SDD stage name
- `task`: exact SDD task name
- `taskType`: the SDD schema-kebab task type
- `cacheFile`: basename of the cache file actually searched
- `searchQuery`: the concrete type-specific portable name
- `matches`: the full exact-name objects from that cache (empty array when none)
- `selected`: the selected full object, or `null` when unresolved
- `rationale`: why that object was selected, or why no compatible match exists

## Type Mapping

After finding a match, map the **cache file type** (not the sdd.md component type) to the JSON `type` value written into the task node:

| Cache file | Task `type` | Identifier field |
|---|---|---|
| `agent-index.json` | `agent` | `entityKey` |
| `process-index.json` | `process` | `entityKey` |
| `api-index.json` | `api-workflow` | `entityKey` |
| `processOrchestration-index.json` | `process` | `entityKey` |
| `caseManagement-index.json` | `case-management` | `entityKey` |
| `action-apps-index.json` | `action` | `id` |
| `typecache-activities-index.json` | `execute-connector-activity` | `uiPathActivityTypeId` |
| `typecache-triggers-index.json` | `wait-for-connector` | `uiPathActivityTypeId` |

Additional `type` values not discoverable through cache: `rpa`, `wait-for-timer`. (`external-agent` is a real CLI type but has **no generation plugin here** — never emit it; model as `api-workflow` / `execute-connector-activity` per Rule 16.)

**Important:** The sdd.md component type determines the JSON `type` to write; the **cache file** supplies the entity identifier (`entityKey`). E.g. if sdd.md says "RPA" and the match is in `process-index.json`, write `type: "rpa"` (from sdd.md). The `entityKey` is recorded in `registry-resolved.json` and confirms the resource during planning — it is **not** written to the task node; non-connector tasks reference the resource via `data.name` / `data.folderPath` = `=bindings.<id>` (per the type's `impl-json.md`).

## Connector Tasks

For entries in `typecache-activities-index.json` or `typecache-triggers-index.json`, the resolution pipeline (get-connection + `case spec`) lives in [connector-integration.md](connector-integration.md). Registry discovery provides only the `uiPathActivityTypeId`; everything else is handled there.

After registry pull, `uip maestro case spec` is the unified metadata endpoint for connector tasks — it returns identity, connection details, inputs/outputs/filter contract, references with pre-built discoverCommand, and (in Phase 3) a populated `caseShape` ready to drop into `caseplan.json`. This replaces the legacy `case tasks describe` + `is resources describe` dance for connector activities and triggers. See [connector-integration.md § Step 3](connector-integration.md) for the call shape.

- **Only use entries that have a `uiPathActivityTypeId` field.** Skip entries without it — these are non-connector activities and are not supported as case tasks at this time.

## Output Contract

The discovery result for each match should include the **entity identifier** (the value from the "Identifier field" column above) so `tasks.md` can reference it. For **connector** tasks the implementation agent writes this identifier into `data.typeId`. For **non-connector** tasks it is not written to the node — it stays in `registry-resolved.json` (audit) and the node references the resource via `data.name` / `data.folderPath` = `=bindings.<id>`.

### `registry-resolved.json` content discipline

Structured log only — per Rule 9, each entry uses exact keys `{stage, task, taskType, cacheFile, searchQuery, matches, selected, rationale}`. The file may be re-ingested as a performance cache only after association by `stage` + `task` and the strict SDD match in [planning.md § Phase 0 carryover](planning.md#step-2--locate-and-parse-the-design-document); it never overrides the SDD. Any free-form prose written here gets parroted back into `tasks.md`. `rationale` MUST explain the selection choice (e.g., `"exact name match in caseManagement folder"`); never use it for verify-text drafts, SDD-vs-spec field translations, or downstream-plugin-behavior claims.
