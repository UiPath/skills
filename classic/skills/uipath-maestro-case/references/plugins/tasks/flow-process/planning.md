# flow-process task — Planning

A flow-process task. Starts a deployed UiPath Maestro Flow (published from a Flow project) by name and folder and returns its outputs.

## When to Use

Pick this plugin when the sdd.md labels a task `flow-process` — a deployed Flow the case starts as one step. For a BPMN agentic process or an orchestration process, use [process](../process/planning.md); for a JSON API workflow, use [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

The task block names the flow the way a `process` task names its process: `**Resolved Resource:**` and `**Folder Path:**`.

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Task `Resolved Resource` | Concrete intended flow name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder Path") | Binds to `data.folderPath`; Orchestrator starts the flow here. The sdd.md folder only seeds the lookup. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (below) | Enables enrichment via `tasks describe` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Cache file:** `flow-index.json` (`uip maestro case registry pull` fills it). The type and its index differ in name.
2. **Identifier field:** `entityKey`.
3. **No cross-type fallback.** Only a `flow-index.json` entry is a flow. A same-named entry in `processOrchestration-index.json`, `process-index.json` or `api-index.json` is a different resource kind — never bind it to a `flow-process` task.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**, as in [registry-discovery.md § 2](../../../registry-discovery.md#2-search-by-name-and-folder-path). A flow is often deployed to several folders (one per solution): pick by folder and record every exact-name hit in `matches`. An exact-name hit in a different folder is an **exact name only** match — resolve it; the Rule 18 gate is only for names no registry entry carries.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`.** Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. **Discover inputs/outputs** with `uip maestro case tasks describe --type flow-process --id "<entityKey>" --output json`. A flow with no input arguments returns an empty `Inputs` array; that is valid.

## Unresolved Fallback

> **Not creatable inline.** `flow-process` is a placeholder-only kind at the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback): offer `Force pull and re-resolve` and `Use placeholders for all`, never `Create missing resources inline`. Do not build a Flow project from this skill.

Mark `<UNRESOLVED: flow-process "<name>" in folder "<folder>" not found in registry>`. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 10's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "flow-process",
  "cacheFile": "flow-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<flow-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

<!-- END: planning.md -->
