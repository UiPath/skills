# process task — Planning

An RPA-driven automated process task. Invokes a UiPath process (or agentic process) by name and folder.

## When to Use

Pick this plugin when the sdd.md describes a task as any of:

- `PROCESS` — a regular UiPath process
- `AGENTIC_PROCESS` — an agentic process orchestrated by UiPath
- Generic "run automation X" where X is a published process

For RPA robot tasks specifically, prefer [rpa](../rpa/planning.md). For Coded workflows / API-workflows, use [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Registry `selected.name` (NOT the sdd.md name) | Orchestrator release name — may differ from the project/package name. Becomes the `name` binding default and the right-hand segment of `resourceKey = <folder-path>.<name>`. |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | This is the binding's `folderPath` default — Orchestrator starts the job here at runtime. The sdd.md "Folder" only seeds the registry lookup; it may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (see below) | Enables auto-enrichment via `tasks describe`. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + `tasks describe` schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type.  |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Primary cache file:** `processOrchestration-index.json` for both `PROCESS` and `AGENTIC_PROCESS`.
2. **Identifier field:** `entityKey`.
3. **Cross-type fallback — mandatory before unresolved fallback.** If the primary cache file has no exact match, query the *other* process cache with the same name and folder hint before recording `selected: null`, asking the empty-lookup question, or writing a placeholder. Therefore a `PROCESS` or `AGENTIC_PROCESS` miss in `processOrchestration-index.json` **MUST** be followed by a `process-index.json` lookup. The sdd.md label is not authoritative: a runnable process can be registered under either index. When the fallback matches, use that entry's `entityKey`, `name`, and full folder path, then continue to schema discovery — do not preserve the primary miss as an unresolved task.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > no match.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
5a. **`name` = the SELECTED entry's `name`** (not the sdd.md name — the Orchestrator release name is what Orchestrator uses at runtime; it may differ from the package/project name). Record this as the `name` binding default; `resourceKey = <folder-path>.<name>`. Fall back to the sdd.md name only when there is no registry match.
6. **Discover inputs/outputs:** after resolving the `entityKey`, fetch the input/output schema via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). Record input names/types and validate outputs using the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). Unrecognized inputs in sdd.md → ask the user (**AskUserQuestion** with matching field names + "Something else").

## Unresolved Fallback

If no match is found across both cache files after `registry pull`:

- Mark the task line: `<UNRESOLVED: process "<name>" in folder "<folder>" not found in registry>`
- Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array.
- Continue planning for remaining tasks.
- Execution creates a placeholder task (empty `data: {}`, no bindings). See [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 9's keys plus this type's lookup output:

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

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else the SDD declares — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only what the registry lookup produced; Phase 2 reads the contract straight from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
