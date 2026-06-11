# task-entry-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 3 only. Phase 2 does not write conditions. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the task-entry condition directly to the target task's `entryConditions[]`. No CLI command needed.

## Condition JSON Shape

> **ID format.** Task-level condition `id` is `c` + 8 random chars. Rule `id` is `r` + 8 random chars. These differ from stage/case-level conditions (`Condition_`/`Rule_`).

```json
{
  "id": "c4fGhJ2Mn",
  "displayName": "After Approval",
  "rules": [
    [
      {
        "id": "rK9xQw3Lp",
        "rule": "selected-tasks-completed",
        "selectedTasksIds": ["t8GQTYo8O"]
      }
    ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

## Procedure

1. Generate condition ID: `c` + 8 alphanumeric chars
2. Generate rule ID: `r` + 8 alphanumeric chars
3. Locate the target stage in `schema.nodes` by ID
4. Locate the target task inside `stageNode.data.tasks[lane][index]` (search every lane until the task ID is found)
5. Initialize `task.entryConditions = []` if absent
6. Read `rule-type` from tasks.md; pick the recipe below
7. Set `displayName`: use tasks.md `display-name` if present; else default to `Entry Rule {N}`, where `N` = the 1-based index this condition takes in `task.entryConditions[]` (i.e. `entryConditions.length + 1` at append time). Never emit a blank or omitted `displayName`.
8. Append the condition object to `task.entryConditions[]`

## Rule Types

### current-stage-entered

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "current-stage-entered" } ]]
```

### selected-tasks-completed — sibling task gating

```json
"rules": [[
  {
    "id": "rxxxxxxxx",
    "rule": "selected-tasks-completed",
    "selectedTasksIds": ["t8GQTYo8O", "tWm4Vx9Tp"]
  }
]]
```

`selectedTasksIds` is a JSON string array.

### adhoc — expression gate

```json
"rules": [[
  {
    "id": "rxxxxxxxx",
    "rule": "adhoc",
    "conditionExpression": "=js:vars.riskScore > 700"
  }
]]
```

`conditionExpression` uses bare `=js:<expr>` (no outer parens) — per FE convention for conditions. Operators (`>`, `<`, `===`, etc.) and function calls go inline. Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim). For combined boolean expressions, wrap each sub-clause in parens before joining: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

### wait-for-connector — bind a connector event

Write `rule.uipath` per [connector-trigger-common.md § Target: connector-bound condition rule](../../../connector-trigger-common.md#target-connector-bound-condition-rule) (canonical rule JSON + procedure there) — a bare rule (no `uipath`) is rejected by Studio Web. **Stage-scoped: `elementId = <stageId>-<ruleId>`.** `conditionExpression` optional. If `type-id` / `connection-id` / `connector-key` is `<UNRESOLVED>`, emit the **stub `uipath` placeholder** (2 `"placeholder"` context fields: `connectorKey` + `operation` — see [connector-trigger-common.md § Placeholder fallback](../../../connector-trigger-common.md#placeholder-fallback)).

**Rule output binding.** If the T-entry has `outputs:`, dispatch `rule.uipath.outputs[]` per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules) **as the last step — after rule write, before root bindings**. `elementId` stays `<stageId>-<ruleId>` on every output entry. Skip when the rule has no `uipath.outputs[]` (stub placeholder).

### runs-sequentially — sequential group with optional parallel siblings

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "runs-sequentially" } ]]
```

**Lane semantics for this rule type:** Among tasks sharing a `runs-sequentially` task-entry condition, group members meant to run in **parallel** with each other MUST share the same `lane` in `stageNode.data.tasks[lane][index]` (shared lane = parallel siblings inside the sequential group, semantic — not just FE layout). Solo members of the group get their own lane. Tasks outside any `runs-sequentially` group still follow the default one-task-per-lane rule with layout-only semantics.

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `current-stage-entered` | — |
| `selected-tasks-completed` | `selectedTasksIds` (array) |
| `wait-for-connector` | `uipath` connector configuration (see [common](../../../connector-trigger-common.md#target-connector-bound-condition-rule)) |
| `adhoc` | — |
| `runs-sequentially` | — |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires.

## Post-Write Verification

Confirm target task's `entryConditions[]` length equals the number of task-entry T-tasks tasks.md wrote for this task. Each entry carries `id` (prefix `c`), non-empty `displayName` (SDD value or `Entry Rule {N}` default), and `rules` with the expected `rule` value plus any required side field. For `wait-for-connector`: verify `rule.uipath.serviceType` is `"Intsvc.WaitForEvent"`, `rule.uipath.context[]` is populated, inputs/outputs `elementId` is `<stageId>-<ruleId>`, and ConnectionId + FolderKey root bindings exist. Full `validate` flags a missing `rule.uipath`/`context` (`connector activity missing`) but not its internals (a wrong `serviceType` passes) — confirm the connector resolves in Studio Web.
