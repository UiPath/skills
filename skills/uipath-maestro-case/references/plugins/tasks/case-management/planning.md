# case-management task — Planning

A nested case task. Invokes another case definition as a sub-case within the current one. Enables hierarchical / recursive case structures.

## When to Use

Pick this plugin when the sdd.md describes a task that spawns or delegates to another case definition. Typical patterns:

- Parent case orchestrates multiple sub-cases
- Long-running sub-workflow packaged as its own case

If sdd.md describes a simple stage-to-stage flow within the same case, do not use this — use regular stages wired by entry/exit conditions.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name | Human-readable parent task label. |
| `name` | sdd.md `Child Case` | Concrete registry query and binding name; REQUIRED and never `<UNRESOLVED>`. Do not substitute `display-name`. |
| `folder-path` | Selected registry `folders[0].fullyQualifiedName` | Binds to `data.folderPath`; use the SDD `Folder Path` only as a concrete lookup hint. `<UNRESOLVED>` means name-only discovery. |
| `task-type-id` | Registry resolution (below) | `entityKey` in `caseManagement-index.json`; mirrors sdd.md `Resource Identity` when already resolved. |
| `inputs` | sdd.md task data mapping | Passed as case-instance inputs to the sub-case |
| `outputs` | sdd.md task Outputs + `tasks describe` schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. **Primary cache file:** `caseManagement-index.json`.
2. **Identifier field:** `entityKey`.
3. Match the exact concrete sdd.md `Child Case` name. Use sdd.md `Folder Path` only when concrete; `<UNRESOLVED>` means name-only discovery.
4. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`**. Never substitute a parent folder or the parent task's display name.
5. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

Case-management lookups stay in `caseManagement-index.json` — never adopt a same-named process or other resource type. A missing child case is non-creatable and goes through the Rule-17 placeholder gate.

## Unresolved Fallback

Mark `<UNRESOLVED: case "<name>" in folder "<folder>" not found in caseManagement-index.json>`, using the preserved sdd.md `Child Case` name even when folder/identity are unresolved. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md). Note: if the referenced sub-case has not been deployed yet, it will not appear in the registry — the user must deploy it before the parent case can reference it.

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 9's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "case-management",
  "cacheFile": "caseManagement-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<child-case-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else the SDD declares — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only what the registry lookup produced; Phase 2 reads the contract straight from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
