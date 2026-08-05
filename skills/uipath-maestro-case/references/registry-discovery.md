# Registry Discovery Reference

Resolve the correct task type and entity identifier for a case task by searching the local registry cache files directly.

## When to Use

During sdd.md → task.md interpretation, when you need to determine:
- What **task type** to use for a task (e.g., `agent`, `process`, `execute-connector-activity`)
- What **entity identifier** to reference in the task.md

## Prerequisites

Run `uip login status --output json`, then `uip maestro case registry pull`, before any cache inspection or lookup. This is a Phase 1 hard gate, not a conditional refresh: never inspect the cache first and use its absence to skip the pull. **One exception — same-session fast path (SKILL.md Rule 3):** when Phase 0's pull already succeeded in this session and `sdd.md` was just rendered from the confirmed in-memory model, reuse that cache instead of re-pulling; any doubt runs the gate in full. Login/pull failure stops Phase 1 before planning artifacts are written. Phase 0 grounds lazily: it starts the same login → pull chain in the background only when the case first shows tenant-bound work, then runs one light name-match pass — no schema discovery, no resource prompts; unclear items defer to build resolution. A successful pull populates the local cache at `~/.uip/case-resources/`. All subsequent discovery is done by reading these cache files directly — **do not** rely on `uip maestro case registry search` as the primary discovery method. See the "CLI Search Gaps" section below for the reason.

> **Missing file ≠ empty match.** Before searching any `<type>-index.json`, verify it exists. If no successful current-session Rule 3 pull exists, complete the login + normal-pull gate once; until it succeeds, an absent cache or index is a failed precondition, never zero matches. After success, a still-absent type index is a genuine zero-match result—do not issue another normal pull. Reserve `registry pull --force` for the user's Force-pull choice below. First resolve an existing local sibling for creatable types; then feed every genuine empty to the same batch gate. Label non-creatable items `placeholder only`, but never send them directly to placeholder.

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
Question: <N> resource(s) not found in the registry: <one entry per unique (name, type): "<name>" (<type>) — used by <Stage>/<Task>[, <Stage>/<Task>…]>. Append " — placeholder only" inside the (<type>) of any NON-creatable resource (RPA process, action, case-management, connector, agentic process). If NONE are creatable, add "(none can be built inline — placeholder only)" right after the count.
Header:   Resolve empties
Options:
  - Force pull and re-resolve
      → run `uip maestro case registry pull --force`, re-search caches, update registry-resolved.json with the
        second-pass results, then LOOP BACK to this prompt for any STILL-empty lookup.
  - Create missing resources inline   # shown ONLY when ≥1 still-empty is an `agent` or `api-workflow` AND the CLI has `registry --local`
      → the NEXT step lets you pick which to build inline (agent → uipath-agents,
        api-workflow → uipath-api-workflow); any you don't pick, plus all non-creatable
        empties (regular RPA process, action, case-management, connectors, agentic processes), become
        placeholders — mixing inline + placeholder is fine (§ Create-on-Missing).
  - Use placeholders for all
      → build nothing; EVERY missing resource (all <N>) becomes an `<UNRESOLVED>` placeholder (per-plugin Unresolved Fallback).
```

**Apply once per planning batch, not per-task.** Each option is batch-level. Group by unique `(name, type)`, list all usages, and keep that mapping for selected-build deduplication and binding. Force pull loops back with only the resources still empty. Establish local capability once during the first agent/API pre-gate sibling search: an unknown `--local` option means unsupported; `No solution found for --local` means supported with no sibling. Cache the result and never scaffold during the probe. Show **Create** only when a genuine empty agent/API exists and that result is supported; otherwise use the two-option gate. Do not read a Create guide yet. Emit no placeholder T-entry and invoke no per-plugin fallback until this gate assigns that resource to fallback.

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

This is a compatibility router, not the Create algorithm. Only after the gate records **Create missing resources inline** should the skill read [inline-resource-creation-guide.md](inline-resource-creation-guide.md), then [create-inline-common.md](plugins/tasks/create-inline-common.md) and only the selected [agent](plugins/tasks/agent/inline-creation-guide.md) or [API-workflow](plugins/tasks/api-workflow/inline-creation-guide.md) guide. Those owners cover selection through binding. Unselected, non-creatable, unavailable-skill, failed, or skipped resources return here already assigned to fallback; only then may their placeholder path run.

### 0 — Prerequisite (solution must exist) + capability probe (once per run)

Compatibility route: read [the complete prerequisite and one-time capability contract](inline-resource-creation-guide.md#0--prerequisite-solution-must-exist--capability-probe-once-per-run) only after Create is selected.

### 1 — Select

Compatibility route: read [the complete selection contract](inline-resource-creation-guide.md#1--select).

### 1b — Choose build kind

Compatibility route: the selected [agent guide](plugins/tasks/agent/inline-creation-guide.md#choose-the-agent-kind) owns kind choice; API workflows have no corresponding step.

### 1c — Dedup the selected builds (one resource per name and type)

Compatibility route: read [the complete deduplication, intent-split, and rename-consent contract](inline-resource-creation-guide.md#1c--dedup-the-selected-builds-one-resource-per-name-and-type).

### 2 — Build (parallel, capped, skip-registration)

Compatibility route: read [the complete capped build and graceful-delegation contract](inline-resource-creation-guide.md#2--build-parallel-capped-skip-registration).

### 3 — Register (sequential)

Compatibility route: read [the complete absolute-path sequential registration contract](inline-resource-creation-guide.md#3--register-sequential).

### 3b — "Already exists" = adopt (kind-agnostic residual)

Compatibility route: read [the complete interrupted-build adoption contract](inline-resource-creation-guide.md#3b--already-exists--adopt-kind-agnostic-residual).

### 4 — Rediscover + verify + bind (offline `--local`)

Compatibility route: read [the complete exact-name rediscovery, case-preserving verification, and binding contract](inline-resource-creation-guide.md#4--rediscover--verify--bind-offline---local).

### Reject case

Compatibility route: read [the complete reject-case visibility contract](inline-resource-creation-guide.md#reject-case).

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
| PROCESS | `processOrchestration-index.json` |
| EXTERNAL_AGENT | *(not in cache)* |
| TIMER | *(not in cache)* |

For types marked "not in cache" (`EXTERNAL_AGENT`, `TIMER`), skip the cache lookup — these have no registry representation. `TIMER` → emit the `wait-for-timer` plugin shape. **`EXTERNAL_AGENT` has no generation plugin here — never write `type: external-agent`; model as `api-workflow` / `execute-connector-activity` per Rule 16.**

**Cross-type fallback:** The sdd.md component type label is not always accurate — the actual registry resource may be stored under a different type. For example, an "RPA" process may appear in `process-index.json`, or an "AGENTIC_PROCESS" might be in `process-index.json` instead of `processOrchestration-index.json`. If the primary cache file yields no match, search the other cache files using the task's type-specific portable name, preserving the existing fallback behavior. For `process` tasks the fallback is a hard gate before any unresolved/placeholder outcome — see [`plugins/tasks/process/planning.md` § Registry Resolution](plugins/tasks/process/planning.md#registry-resolution). **Exception: do not cross-type-fallback an `action` or `case-management` lookup.** An Action App ID is valid only from `action-apps-index.json`, and a child-case `entityKey` is valid only from `caseManagement-index.json`; a same-named process is not a compatible substitute for either task type.

### 2. Search by Name and Folder Path

For each task in the sdd.md, extract its concrete portable name from the type-specific field below. Use the corresponding folder only when it is concrete; `<UNRESOLVED>` means name-only discovery.

| Task type | Portable name query | Folder hint |
|---|---|---|
| `process` / `agent` / `rpa` / `api-workflow` | `Resolved Resource` | `Folder Path` |
| `action` | `Action App: <deploymentTitle>` in `HITL Implementation` | `Deployment Folder` |
| `case-management` | `Child Case` | `Folder Path` |

The portable name is REQUIRED and never `<UNRESOLVED>`. Do not fall back to the task display name. Then filter the cache file using `cat ... | python3 -c "..."` or the `Read` tool. **Do NOT use `node -e 'const fs=require("fs")...'` for cache reads — this violates Rule 13 even when the target is a resource cache file, not a skill artifact.**

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
2. If still no match (or the user picked `Use placeholders for all`, and any creatable resource was not selected for Create), mark it in tasks.md: `[REGISTRY LOOKUP FAILED: <name> in <folder>]` and proceed to the per-plugin Unresolved Fallback path.

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

## Identifier Mapping — Cache File Never Controls Task `type`

The validated SDD schema-kebab task type controls the JSON `type` written to `caseplan.json`. A compatible fallback cache supplies an identifier only; it can never rewrite the task type.

| Cache file | Identifier field |
|---|---|
| `agent-index.json` | `entityKey` |
| `process-index.json` | `entityKey` |
| `api-index.json` | `entityKey` |
| `processOrchestration-index.json` | `entityKey` |
| `caseManagement-index.json` | `entityKey` |
| `action-apps-index.json` | `id` |
| `typecache-activities-index.json` | `uiPathActivityTypeId` |
| `typecache-triggers-index.json` | `uiPathActivityTypeId` |

For example, an SDD `rpa` task matched compatibly in `process-index.json` remains `type: "rpa"`; use the entry's `entityKey` only as resolution evidence. `wait-for-timer` needs no registry identifier. `external-agent` has no generation plugin and is never emitted. For non-connectors, the identifier stays in `registry-resolved.json` and the node references name/folder bindings; connector plugins write their resolved type identifier to `data.typeId`.

## Connector Tasks

For entries in `typecache-activities-index.json` or `typecache-triggers-index.json`, the resolution pipeline (get-connection + `case spec`) lives in [connector-integration.md](connector-integration.md). Registry discovery provides only the `uiPathActivityTypeId`; everything else is handled there.

After registry pull, `uip maestro case spec` is the unified metadata endpoint for connector tasks — it returns identity, connection details, inputs/outputs/filter contract, references with pre-built discoverCommand, and (in Phase 3) a populated `caseShape` ready to drop into `caseplan.json`. This replaces the legacy `case tasks describe` + `is resources describe` dance for connector activities and triggers. See [connector-integration.md § Step 3](connector-integration.md) for the call shape.

- **Only use entries that have a `uiPathActivityTypeId` field.** Skip entries without it — these are non-connector activities and are not supported as case tasks at this time.

## Output Contract

The discovery result for each match should include the **entity identifier** (the value from the "Identifier field" column above) so `tasks.md` can reference it. For **connector** tasks the implementation agent writes this identifier into `data.typeId`. For **non-connector** tasks it is not written to the node — it stays in `registry-resolved.json` (audit) and the node references the resource via `data.name` / `data.folderPath` = `=bindings.<id>`.

### `registry-resolved.json` content discipline

Structured log only — per Rule 9, each entry uses exact keys `{stage, task, taskType, cacheFile, searchQuery, matches, selected, rationale}`. The file may be re-ingested as a performance cache only after association by `stage` + `task` and the strict SDD match in [planning.md § Phase 0 carryover](planning.md#step-2--locate-and-parse-the-design-document); it never overrides the SDD. Any free-form prose written here gets parroted back into `tasks.md`. `rationale` MUST explain the selection choice (e.g., `"exact name match in caseManagement folder"`); never use it for verify-text drafts, SDD-vs-spec field translations, or downstream-plugin-behavior claims.

<!-- END: registry-discovery.md -->
