# Registry Discovery Reference

Resolve the correct task type and entity identifier for a case task by searching the local registry cache files directly.

## When to Use

During sdd.md → task.md interpretation, when you need to determine:
- What **task type** to use for a task (e.g., `agent`, `process`, `execute-connector-activity`)
- What **entity identifier** to reference in the task.md

## Prerequisites

Run `uip maestro case registry pull` before any lookups. This populates the local cache at `~/.uip/case-resources/`. All subsequent discovery is done by reading these cache files directly — **do not** rely on `uip maestro case registry search` as the primary discovery method. See the "CLI Search Gaps" section below for the reason.

> **Missing file ≠ empty match.** Before searching any `<type>-index.json`, verify it exists on disk. If it does not, run `uip maestro case registry pull` (not `--force` — a normal pull is enough for first-time population). The Rule 17 / § MUST-Confirm-Before-Skeleton-Fallback gate only applies to **empty matches inside an existing cache**; a missing file is a precondition failure, not a 0-result lookup. If the file is still absent after a successful pull, the tenant has no resources of that type — proceed to skeleton.

## CLI Search Gaps

The `uip maestro case registry search` command has known gaps. In particular, it fails to return results for certain resource types even when the resource is present in the cache (most commonly affecting **action-apps** / HITL tasks). When search returns an empty or incomplete result for a resource you know exists:

1. Do **not** retry the same search with different keywords.
2. Fall back to reading the cache files directly using the procedure in this document.
3. Record the gap in `registry-resolved.json` so the audit trail reflects the fallback.

Direct cache-file inspection is the authoritative discovery method for this skill.

## MUST Confirm Before Skeleton Fallback

> **Hard gate.** If the planning-phase lookup batch returns ≥1 empty result (no match across all relevant cache files for any task / trigger / connector), STOP. Run AskUserQuestion before invoking any per-plugin Unresolved Fallback path or writing any skeleton T-entry.

Required prompt shape:

```
Question: <N> registry lookup(s) returned 0 matches: <comma-list of <name> in <folder>>.
          Run `uip maestro case registry pull --force` to bypass the cache and re-resolve?
Header:   Force pull
Options:
  - Yes, force pull and re-resolve
      → run `uip maestro case registry pull --force`, re-search caches, update registry-resolved.json with the second-pass results.
        Any STILL-empty lookups go to skeleton ONLY after this round.
  - Skip and use skeletons
      → proceed to per-plugin Unresolved Fallback paths for the unmatched lookups.
```

**Apply once per planning batch, not per-task.** A single prompt covers every empty in that batch.

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

For types marked "not in cache" (`EXTERNAL_AGENT`, `TIMER`), skip the cache lookup — these have no registry representation. Use the JSON `type` value directly.

**Cross-type fallback:** The sdd.md component type label is not always accurate — the actual registry resource may be stored under a different type. For example, an "RPA" process may appear in `process-index.json`, or an "AGENTIC_PROCESS" might be in `process-index.json` instead of `processOrchestration-index.json`. If the primary cache file yields no match, search **all** cache files listed above for the task name. When a match is found in a different cache file than expected, use that cache file's identifier field and type mapping for the `taskTypeId`, but keep the sdd.md's component type for the JSON `type` field.

### 2. Search by Name and Folder Path

For each task in the sdd.md, extract the **name** and **folder path** from the Process References table, then filter the cache file:

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
4. **No match in primary cache file** — search all other cache files (the resource may be registered under a different type than expected).

### 3. Handle Empty Results

> **Required precondition.** Before reaching this step, the [§ MUST: Confirm Before Skeleton Fallback](#must-confirm-before-skeleton-fallback) gate above MUST have been satisfied. If you have not yet run AskUserQuestion for the empty-result batch, do that first. Force pull and per-plugin Unresolved Fallback both flow through that gate.

If no match is found across all relevant cache files:

1. **Already gated above.** AskUserQuestion confirmation already ran. If the user picked `Yes, force pull and re-resolve`, the force pull has already executed; this step is reached for lookups that remained empty after the second-pass search.
   ```bash
   # already executed during the gate's "Yes" branch:
   uip maestro case registry pull --force
   ```
2. If still no match (or user picked `Skip`), mark it in tasks.md: `[REGISTRY LOOKUP FAILED: <name> in <folder>]` and proceed to the per-plugin Unresolved Fallback path.

### 4. Return All Matches

Collect all matching results for the `registry-resolved.json` debug output. Record:
- The cache file searched
- All entries that matched the name
- Which entry was selected and why (folder match, first-match, etc.)

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

Additional `type` values not discoverable through cache: `rpa`, `external-agent`, `wait-for-timer`.

**Important:** The sdd.md component type determines the JSON `type` to write, but the **cache file** determines the `taskTypeId`. For example, if the sdd.md says "RPA" and the cache match is in `process-index.json`, write `type: "rpa"` (from sdd.md) and `data.context.taskTypeId: "<entityKey>"` (from cache).

## Connector Tasks

For entries in `typecache-activities-index.json` or `typecache-triggers-index.json`, the full resolution pipeline (get-connector → get-connection → pick connection → describe) lives in [connector-integration.md](connector-integration.md). Registry discovery provides only the `uiPathActivityTypeId`; everything else is handled there.

- **Only use entries that have a `uiPathActivityTypeId` field.** Skip entries without it — these are non-connector activities and are not supported as case tasks at this time.

## Output Contract

The discovery result for each match should include the **entity identifier** (the value from the "Identifier field" column above) so `tasks.md` can reference it. The implementation agent writes this identifier into `data.context.taskTypeId` (or `data.typeId` for connectors) on the task node.
