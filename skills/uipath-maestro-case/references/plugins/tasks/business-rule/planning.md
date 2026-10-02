# business-rule task — Planning

A business rule task. Evaluates a deployed UiPath Business Rule (a DMN decision-table project, published from a rules solution) by entityKey: typed inputs in, decision-column outputs back — no LLM, no UI automation, no code.

## When to Use

Pick this plugin when the sdd.md labels a task `business-rule` — a deployed rule whose decision tables map input values to outputs (eligibility, risk band, routing, approval tier). For deterministic logic packaged as code, use [function](../function/planning.md); for judgment over unstructured input, use [agent](../agent/planning.md); for a single threshold check on a case variable, use a condition `=js:` expression instead of a task.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Task `Resolved Resource` | Concrete intended rule name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator evaluates the rule here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (below) | Enables auto-enrichment via `tasks describe` |
| `inputs` | sdd.md task data mapping | The rule's input columns. See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | The rule's decision output columns, **flattened** (see [§ Outputs are flat](#outputs-are-flat)). Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Cache file:** `businessRule-index.json` (Resource Catalog `BusinessRule` entities; `registry pull` caches it as resource type `businessRule`).
2. **Identifier field:** `entityKey`.
3. **No cross-type fallback.** A business rule binds with `resource: "BusinessRule"`, so only a `businessRule-index.json` entry is a compatible match. A same-named entry in `process-index.json`, `function-index.json`, or any other index is a different resource kind — never bind it to a `business-rule` task.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. Record every exact-name hit in `matches`. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 5). Do NOT treat a folder difference as no-match; the Rule 18 gate is only for names **no** registry entry carries.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder"). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. **In-solution sibling:** a rules project inside the same solution is listed by `uip maestro case registry list --local --output json` with `Category: "businessRule"` before it is deployed. Its `Outputs` schema is already flattened.
7. **Discover inputs/outputs** via `tasks describe --type business-rule` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). It requires a logged-in session (the contract comes from the rule's exported resource spec).

### Outputs are flat

A rule's result is keyed by decision (`decision1.output1`), but a case task reads it **flat**: `tasks describe` merges every decision's output columns into one list (first column of a name wins) and appends `Error`. Bind SDD outputs to those column names (`output1`), never to a decision name or a dotted `decision.column` path.

## Unresolved Fallback

> **Not creatable inline.** `business-rule` is a placeholder-only kind at the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback): offer `Force pull and re-resolve` and `Use placeholders for all`, never `Create missing resources inline`. Do not author the rule (`uip rules`) from this skill.

Mark `<UNRESOLVED: business-rule "<name>" in folder "<folder>" not found in registry>`. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md). `uip maestro case validate` reports the placeholder as a `TASK_NOT_CONFIGURED` warning, not an error.

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
  "name": "<resource-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else the SDD declares — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only what the registry lookup produced; Phase 2 reads the contract straight from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
