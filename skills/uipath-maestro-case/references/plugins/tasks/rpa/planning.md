# rpa task — Planning

An RPA robot task: sdd.md component type `RPA`, task node `type` `"rpa"`, and a cached registry entity typically in `process-index.json`, which does not distinguish `process` from `rpa` at storage time.

## When to Use

Pick this plugin when the sdd.md explicitly labels a task as `RPA` (e.g., "RPA robot does X"). The distinction from `process` is **semantic** (sdd.md intent) rather than structural (registry representation). If ambiguous between `PROCESS` and `RPA`, default to `process` unless sdd.md mentions UI automation, desktop apps, or robot-specific concerns.

## Required Fields from sdd.md

Same shape as [process/planning.md](../process/planning.md):

| Field | Notes |
|-------|-------|
| `display-name` | Task `Task Name`. |
| `name` | Registry `selected.name`, not the sdd.md name: Orchestrator release name, which may differ from the project/package name. It is the `name` binding default; `resourceKey = <folder-path>.<name>`. |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName`, not sdd.md `Folder` (which may be a parent path). Binds to `data.folderPath`; Orchestrator starts the job here. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry `entityKey` in `process-index.json`. |
| `inputs` | See [bindings-and-expressions.md](../../../bindings-and-expressions.md). |
| `outputs` | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce`, `isRequired` | From sdd.md; `runOnlyOnce` defaults false if omitted. Do not infer true from task type. |

## Registry Resolution

1. **Primary cache file:** `process-index.json` (RPA tasks share it with `process`).
2. **Identifier field:** `entityKey`.
3. Use the sdd.md `RPA` label to set the task node `type: "rpa"`. Record the cache `entityKey` in `registry-resolved.json`, not on the node; reference the resource through `data.name` / `data.folderPath` = `=bindings.<id>`.
4. If `process-index.json` has no match, search all other cache files as a fallback.
5. Set **`folder-path` to the SELECTED entry's `folders[0].fullyQualifiedName`**, not sdd.md `Folder`; use the sdd.md folder only when there is no registry match (Unresolved path).
5a. **`name` = the SELECTED entry's `name`** (not the sdd.md name — the Orchestrator release name may differ from the project/package name; e.g. "ProjectEuler RPA" → release "RPA Workflow"). Record this as the `name` binding default; `resourceKey = <folder-path>.<name>`.
6. Run `tasks describe` to discover inputs/outputs; see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

## Unresolved Fallback

Mark `<UNRESOLVED: rpa "<name>" in folder "<folder>" not found in registry>`. Omit resolved-schema keys `inputs` / `outputs`; record intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task—see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 10's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "rpa",
  "cacheFile": "process-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<resource-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache. `selected` is the chosen match object, or `null` after a genuine empty lookup—see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape).

Everything else declared by the SDD—inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text—stays in `sdd.md`. The ledger holds only registry-lookup results; Phase 2 reads the contract directly from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
