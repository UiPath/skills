# business-rule task — Planning

A business rule task. Evaluates a deployed UiPath Business Rule (a DMN decision table from a Business Rules project) and returns its decision outputs — deterministic, no LLM, no robot.

## When to Use

Pick this plugin when the sdd.md labels a task `business-rule` — a deployed rule that maps typed inputs to decision outputs. For code-first computation, use [function](../function/planning.md); for reasoning over unstructured input, use [agent](../agent/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Registry `selected.name` (NOT the sdd.md name) | Deployed rule name; may differ from the project name. Becomes the `name` binding default and `resourceKey = <folder-path>.<name>`. |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; the engine runs the rule from this folder. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (below) | Enables enrichment via `tasks describe` |
| `inputs` | sdd.md task data mapping | Names come from `tasks describe`; see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | One output, `output`, holding the whole result keyed by decision; downstream reads `vars.<output var>.<decision>.<column>`. To store one column in a case variable, write the extract row `result.<decision>.<column> -> <case variable>`. Otherwise follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Cache file:** `businessRule-index.json` (`uip maestro case registry pull` fills it from the Resource Catalog). Search with `uip maestro case registry search "<name>" --type businessRule --output json`.
2. **Identifier field:** `entityKey`.
3. **No cross-type fallback.** Only a `businessRule-index.json` entry is a rule. A same-named process, function, or agent is a different resource kind — never bind it to a `business-rule` task.
4. **No in-solution fallback.** Never resolve a rule with `registry search --local`; a rule defined only in this solution is deployed first (uipath-solution), then pulled and resolved here.
5. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**, as in [registry-discovery.md § 2](../../../registry-discovery.md#2-search-by-name-and-folder-path).
6. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder"). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
7. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

## Unresolved Fallback

> **Not creatable inline.** `business-rule` is a placeholder-only kind at the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback): offer `Force pull and re-resolve` and `Use placeholders for all`, never `Create missing resources inline`.

Mark `<UNRESOLVED: business-rule "<name>" in folder "<folder>" not found in registry>`. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 10's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "business-rule",
  "cacheFile": "businessRule-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<rule-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else the SDD declares — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only what the registry lookup produced; Phase 2 reads the contract straight from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
