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
6. Append the condition object to `stageNode.data.exitConditions[]`

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

### wait-for-connector — external event

```json
"type": "exit-only",
"marksStageComplete": true,
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "wait-for-connector",
    "conditionExpression": "=js:event.type === 'approved'"
  }
]]
```

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
| `true` | `wait-for-connector` | — |
| `false` | `selected-tasks-completed` | `selectedTasksIds` (array) |
| `false` | `wait-for-connector` | — |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); for combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm target stage's `data.exitConditions[]` contains the new object with `id`, `type`, `exitToStageId` (if set), `marksStageComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field.
