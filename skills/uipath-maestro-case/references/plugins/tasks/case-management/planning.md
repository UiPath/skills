# case-management task — Planning

A nested case task invokes another case definition as a sub-case for hierarchical or recursive structures. For a same-case stage flow, use regular stages with entry/exit conditions.

## When to Use

Use when sdd.md describes a task that spawns or delegates to another case definition, including parent orchestration or a long-running sub-workflow.

## Required Fields from sdd.md

| Field | Source | Notes |
|---|---|---|
| `display-name` | sdd.md task name | Human-readable parent-task label. |
| `name` | sdd.md `Child Case` | Concrete registry query and binding name; REQUIRED, never `<UNRESOLVED>`, and never replaced by `display-name`. |
| `folder-path` | Selected registry `folders[0].fullyQualifiedName` | Binds to `data.folderPath`; use SDD `Folder Path` only as a concrete lookup hint. `<UNRESOLVED>` means name-only discovery. |
| `task-type-id` | Registry resolution below | `entityKey` in `caseManagement-index.json`; mirrors sdd.md `Resource Identity` when already resolved. |
| `inputs` | sdd.md task data mapping | Passed as sub-case instance inputs. |
| `outputs` | sdd.md task Outputs + `tasks describe` schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md, default `false` | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md, default `true` | |

## Registry Resolution

1. Use `caseManagement-index.json` as the primary cache and `entityKey` as the identifier field.
2. Match the exact concrete sdd.md `Child Case` name; use sdd.md `Folder Path` only when concrete. `<UNRESOLVED>` means name-only discovery.
3. Set **`folder-path` to the SELECTED entry's `folders[0].fullyQualifiedName`**; never use a parent folder or the parent task's display name.
4. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

Keep case-management lookups in `caseManagement-index.json`; never adopt a same-named process or other resource type. A missing child case is non-creatable and goes through the Rule-17 placeholder gate.

## Unresolved Fallback

Mark `<UNRESOLVED: case "<name>" in folder "<folder>" not found in caseManagement-index.json>`, preserving the sdd.md `Child Case` name even when folder or identity is unresolved. Omit resolved-schema keys `inputs` / `outputs`; record intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md). If the sub-case has not been deployed, it will not appear in the registry; the user must deploy it before the parent can reference it.

## Fields to Resolve

The ledger entry in `tasks/registry-resolved.json` contains Rule 10's keys plus this type's lookup output:

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

`matches` is the complete exact-name set from the refreshed cache. `selected` is the chosen match object, or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape).

All other SDD declarations—inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text—remain in `sdd.md`. The ledger stores only registry-lookup results; Phase 2 reads the contract directly from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->