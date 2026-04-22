# task-entry-conditions — Implementation (Direct JSON Write)

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
7. Append the condition object to `task.entryConditions[]`

> **Connector tasks.** `execute-connector-activity` and `wait-for-connector` tasks already carry an auto-injected `current-stage-entered` default entry condition from task-creation time. Append — never overwrite or remove the default.

## Rule Types

### current-stage-entered — default gate

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "current-stage-entered" } ]]
```

Matches the shape of the auto-injected default on connector tasks.

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
    "conditionExpression": "in.riskScore > 700"
  }
]]
```

Expression syntax per [`../../../bindings-and-expressions.md`](../../../bindings-and-expressions.md). Use `=js:(...)` for expressions with operators.

### wait-for-connector — external event

```json
"rules": [[
  {
    "id": "rxxxxxxxx",
    "rule": "wait-for-connector",
    "conditionExpression": "event.type = 'order_received'"
  }
]]
```

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `current-stage-entered` | — |
| `selected-tasks-completed` | `selectedTasksIds` (array) |
| `wait-for-connector` | — |
| `adhoc` | — |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires.

## Post-Write Verification

Confirm target task's `entryConditions[]` contains the new object with `id` (prefix `c`) and `rules` carrying the expected `rule` value plus any required side field. For connector tasks, verify the auto-injected `current-stage-entered` default is still present and precedes the new condition.
