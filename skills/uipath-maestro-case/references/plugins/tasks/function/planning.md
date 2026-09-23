# function task — Planning

A coded function task. Invokes a deployed UiPath Coded Function (Python or JS/TS, published from a Functions project) by entityKey for deterministic, code-first logic — no LLM, no UI automation.

## When to Use

Pick this plugin when the sdd.md labels a task `function` — a deployed Coded Function that takes typed inputs and returns typed outputs. Use it for deterministic computation, transformation, or validation that is already packaged as a Function. For reasoning or judgment over unstructured input, use [agent](../agent/planning.md); for a JSON API workflow (`document.dsl`), use [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Task `Resolved Resource` | Concrete intended resource name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator starts the function here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (below) | Enables auto-enrichment via `tasks describe` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Cache file:** `function-index.json`.
2. **Identifier field:** `entityKey`.
3. **No cross-type fallback.** A function binds with `resourceSubType: "Function"`, so only a `function-index.json` entry is a compatible match. A same-named entry in `agent-index.json`, `api-index.json`, or `process-index.json` is a different resource kind — never bind it to a `function` task.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. The same function name commonly appears in several folders (one per deployed solution) — pick by folder, and record every exact-name hit in `matches`. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 5). Do NOT treat a folder difference as no-match; the Rule 17 gate is only for names **no** registry entry carries.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder"). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. **Discover inputs/outputs** via `tasks describe --type function` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). A function with no input arguments returns an empty `Inputs` array; that is valid, not an error.

## Unresolved Fallback

> **Not creatable inline.** `function` is a placeholder-only kind at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback): offer `Force pull and re-resolve` and `Use placeholders for all`, never `Create missing resources inline`. Do not build a Functions project from this skill.

Mark `<UNRESOLVED: function "<name>" in folder "<folder>" not found in registry>`. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 9's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "function",
  "cacheFile": "function-index.json",
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
