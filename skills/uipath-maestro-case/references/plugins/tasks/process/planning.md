# process task — Planning

An RPA-driven task invoking a UiPath or agentic process by name and folder.

## When to Use

Use this plugin when sdd.md describes `PROCESS`, `AGENTIC_PROCESS`, or generic “run automation X” where X is a published process. For RPA robot tasks, prefer [rpa](../rpa/planning.md); for Coded workflows / API-workflows, use [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|---|---|---|
| `display-name` | Task `Task Name` | UI label |
| `name` | Registry `selected.name` (NOT the sdd.md name) | Orchestrator release name — may differ from the project/package name. Default `name` binding and right-hand side of `resourceKey = <folder-path>.<name>`. |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT sdd.md "Folder") | Default `folderPath`; Orchestrator starts the job here. sdd.md "Folder" only seeds lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (below) | Enables auto-enrichment via `tasks describe`. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + `tasks describe` schema | Follow [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. Use `processOrchestration-index.json` as the primary cache for `PROCESS` and `AGENTIC_PROCESS`.
2. Use `entityKey` as the identifier.
3. If the primary cache has no exact match, query the other process cache with the same name and folder hint before recording `selected: null`, asking the empty-lookup question, or writing a placeholder. A `PROCESS` or `AGENTIC_PROCESS` miss in `processOrchestration-index.json` **MUST** be followed by a `process-index.json` lookup. The sdd.md label is not authoritative; a runnable process may be in either index. For a fallback match, use its `entityKey`, `name`, and full folder path, continue schema discovery, and do not preserve the primary miss as unresolved.
4. Match priority: exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > no match.
5. Use the SELECTED entry's `folders[0].fullyQualifiedName` for `folder-path`, not sdd.md "Folder". Only an unresolved task falls back to the sdd.md folder.
5a. **`name` = the SELECTED entry's `name`** (not the sdd.md name — the Orchestrator release name is what Orchestrator uses at runtime; it may differ from the package/project name). Record this as the `name` binding default; `resourceKey = <folder-path>.<name>`. Fall back to the sdd.md name only when there is no registry match.
6. After resolving `entityKey`, run `tasks describe` to fetch input/output schema; see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). Record input names/types and validate outputs using [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). For unrecognized sdd.md inputs, ask the user (**AskUserQuestion** with matching field names + "Something else").

## Unresolved Fallback

If `registry pull` finds no match across either cache:

- Mark the task line: `<UNRESOLVED: process "<name>" in folder "<folder>" not found in registry>`.
- Omit resolved-schema keys `inputs` / `outputs`; capture intended wiring in the entry's `wiringNotes` string array.
- Continue planning remaining tasks.
- Execution creates a placeholder task (empty `data: {}`, no bindings). See [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 10's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "process",
  "cacheFile": "processOrchestration-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<resource-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache; `selected` is the chosen match object, or `null` after a genuine empty lookup (see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else declared by the SDD — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only registry-lookup results; Phase 2 reads the contract directly from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->