# Task Entry Conditions

Task entry conditions live under `task.entryConditions`. They determine when a task within a stage is triggered.

## Condition Object Shape

```json
{
  "id": "Condition_<6chars>",
  "displayName": "<human-readable label>",
  "rules": [[{ "rule": "<rule-type>", "id": "Rule_<6chars>", ...ruleFields }]]
}
```

Rules are DNF: `[[ruleA, ruleB], [ruleC]]` = `(A AND B) OR C`. Most tasks need only `[[rule]]`.

## Patterns

### current-stage-entered — default

Task runs every time the stage is entered:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage entered",
    "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
  }
]
```

Add `conditionExpression` to gate on a variable:

```json
"rules": [[{
  "rule": "current-stage-entered",
  "id": "Rule_<6chars>",
  "conditionExpression": "=js:vars.claimAmount > 10000"
}]]
```

### selected-tasks-completed — depends on sibling tasks

```json
"rules": [[{
  "rule": "selected-tasks-completed",
  "id": "Rule_<6chars>",
  "selectedTasksIds": ["tJJETUgZ2", "tYXPi6r8U"]
}]]
```

### adhoc — manual trigger

Task is not triggered automatically; activated by a user or orchestration layer:

```json
"rules": [[{ "rule": "adhoc", "id": "Rule_<6chars>" }]]
```

### OR logic — multiple rule sets

Task triggers when either inner array fires:

```json
"rules": [
  [{ "rule": "current-stage-entered", "id": "Rule_<6chars>", "conditionExpression": "=js:vars.priority === 'high'" }],
  [{ "rule": "current-stage-entered", "id": "Rule_<6chars>", "conditionExpression": "=js:vars.escalated === true" }]
]
```

## Rule Type Reference

| `rule` value | Companion fields | When to use |
|---|---|---|
| `current-stage-entered` | `conditionExpression?` | Default — task activates when its stage is entered |
| `selected-tasks-completed` | `selectedTasksIds[]`, `conditionExpression?` | Sequential — task waits for upstream sibling task(s) |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | External connector event (uses `uip case tasks add-connector`) |
| `adhoc` | `conditionExpression?` | Manually triggered |

