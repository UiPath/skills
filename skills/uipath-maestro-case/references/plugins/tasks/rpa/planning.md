# rpa task — Planning

An RPA robot task. The sdd.md component type is `RPA`. The task node's `type` field is `"rpa"`, but the cached registry entity typically lives in `process-index.json` — the registry does not separate "process" from "rpa" at storage time.

## When to Use

Pick this plugin when the sdd.md explicitly labels a task as `RPA` (e.g., "RPA robot does X"). The distinction from `process` is **semantic** (sdd.md intent) rather than structural (registry representation).

If sdd.md is ambiguous between `PROCESS` and `RPA`, default to `process` unless the sdd.md mentions UI automation, desktop apps, or robot-specific concerns.

## Required Fields from sdd.md

Same shape as [process/planning.md](../process/planning.md):

| Field | Notes |
|-------|-------|
| `display-name` | from task `Task Name` |
| `name` | Registry `selected.name` (NOT the sdd.md name) — Orchestrator release name; may differ from the project/package name. Becomes the `name` binding default and `resourceKey = <folder-path>.<name>`. |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` — NOT the sdd.md "Folder" (which may be a parent path). Binds to `data.folderPath`; Orchestrator starts the job here at runtime. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | from registry (`entityKey` in `process-index.json`) |
| `inputs` | see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list) |
| `runOnlyOnce`, `isRequired` | from sdd.md (`runOnlyOnce` defaults false if omitted; do not infer true from task type) |

## Registry Resolution

1. **Primary cache file:** `process-index.json` (yes — RPA tasks share this cache with `process`).
2. **Identifier field:** `entityKey`.
3. Use the sdd.md `RPA` label to set `type: "rpa"` on the task node; the cache `entityKey` is recorded in `registry-resolved.json` (not written to the node — the task references the resource via `data.name` / `data.folderPath` = `=bindings.<id>`).
4. If no match in `process-index.json`, search all other cache files as a fallback.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
5a. **`name` = the SELECTED entry's `name`** (not the sdd.md name — the Orchestrator release name may differ from the project/package name; e.g. "ProjectEuler RPA" → release "RPA Workflow"). Record this as the `name` binding default; `resourceKey = <folder-path>.<name>`.
6. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

## Unresolved Fallback

Mark `<UNRESOLVED: rpa "<name>" in folder "<folder>" not found in registry>`. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 9's keys plus this type's lookup output:

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

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else the SDD declares — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only what the registry lookup produced; Phase 2 reads the contract straight from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
