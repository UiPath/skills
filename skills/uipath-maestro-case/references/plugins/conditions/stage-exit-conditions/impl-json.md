# stage-exit-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 3 only. Phase 2 does not write conditions. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the stage-exit condition directly to the target stage's `data.exitConditions[]`. No CLI command needed.

## Condition JSON Shape

> **ID format.** Condition `id` is `Condition_` + 6 random chars. Rule `id` is `Rule_` + 6 random chars.

```json
{
  "id": "Condition_xC1XyX",
  "displayName": "All tasks done",
  "type": "exit-only",
  "marksStageComplete": true,
  "rules": [
    [
      { "id": "Rule_jdBFrJ", "rule": "required-tasks-completed" }
    ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

## Procedure

1. Generate condition ID: `Condition_` + 6 alphanumeric chars
2. Generate rule ID: `Rule_` + 6 alphanumeric chars
3. Locate the target stage in `schema.nodes` by ID
4. Initialize `stageNode.data.exitConditions = []` if absent (regular Stage is created without this key — see [`../../stages/impl-json.md`](../../stages/impl-json.md))
5. Read `type`, `exit-to-stage`, `marks-stage-complete`, and `rule-type` from tasks.md; pick the recipe below
6. Set `displayName`: use tasks.md `display-name` if present; else default by `marks-stage-complete`: `true` → `Complete Rule {N}`, `false` → `Exit Rule {N}`. `N` = 1-based index **within the same label kind** — at append time, count existing entries in `stageNode.data.exitConditions[]` whose `marksStageComplete` equals this condition's value, then `N = count + 1`. FE numbers complete and exit rules with independent counters — do NOT use the array's overall length. Never emit a blank or omitted `displayName`.
7. Append the condition object to `stageNode.data.exitConditions[]`

## Exit Types

| `type` | When to pick |
|---|---|
| `exit-only` | Default — stage exits normally along configured edges |
| `wait-for-user` | Manual user decision required |
| `return-to-origin` | Rework / exception loop — sends the case back to the previous stage |

## Rule Types

### required-tasks-completed — default completion

```json
"type": "exit-only",
"marksStageComplete": true,
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-tasks-completed" } ]]
```

### selected-tasks-completed — routing on specific tasks

```json
"type": "exit-only",
"marksStageComplete": false,
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "selected-tasks-completed",
    "selectedTasksIds": ["t8GQTYo8O", "tWm4Vx9Tp"]
  }
]]
```

`selectedTasksIds` is a JSON string array, not a comma-separated string.

### wait-for-connector — bind a connector event

Write `rule.uipath` per [connector-trigger-common.md § Target: connector-bound condition rule](../../../connector-trigger-common.md#target-connector-bound-condition-rule) (canonical rule JSON + procedure there) — a bare rule (no `uipath`) is rejected by Studio Web. **Stage-scoped: `elementId = <stageId>-<ruleId>`.** Place it in the exit condition with `type` / `marksStageComplete` like the other exit rules above. `conditionExpression` optional. If `type-id` / `connection-id` / `connector-key` is `<UNRESOLVED>`, emit the **stub `uipath` placeholder** (2 `"placeholder"` context fields: `connectorKey` + `operation` — see [connector-trigger-common.md § Placeholder fallback](../../../connector-trigger-common.md#placeholder-fallback)).

**Rule output binding.** If the T-entry has `outputs:`, dispatch `rule.uipath.outputs[]` per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules) **as the last step — after rule write, before root bindings**. `elementId` stays `<stageId>-<ruleId>` on every output entry. Skip when the rule has no `uipath.outputs[]` (stub placeholder).

### wait-for-user — manual decision gate

```json
"type": "wait-for-user",
"marksStageComplete": true,
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-tasks-completed" } ]]
```

The case pauses after the rule fires; the user picks the next stage from candidates that carry a `user-selected-stage` entry rule.

### return-to-origin — rework loop

```json
"type": "return-to-origin",
"marksStageComplete": true,
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-tasks-completed" } ]]
```

Routes the case back to the originating stage.

## Rule-Type × marksStageComplete Matrix

| `marksStageComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-tasks-completed` | — |
| `true` | `wait-for-connector` | `uipath` connector configuration |
| `false` | `selected-tasks-completed` | `selectedTasksIds` (array) |
| `false` | `wait-for-connector` | `uipath` connector configuration |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); for combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm target stage's `data.exitConditions[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksStageComplete`), `type`, `exitToStageId` (if set), `marksStageComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field. For `wait-for-connector`: verify `rule.uipath.serviceType` is `"Intsvc.WaitForEvent"`, `rule.uipath.context[]` is populated (placeholders substituted), inputs/outputs `elementId` is `<stageId>-<ruleId>`, and the ConnectionId + FolderKey root bindings exist.
