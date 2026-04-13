# Task Entry Conditions — Implementation

Task entry conditions are placed in `task.entryConditions`.

## current-stage-entered — Default (Always Include)

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage entered",
    "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
  }
]
```

## current-stage-entered with Conditional Filter

Task only runs if the expression is true when the stage is entered:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "High-value claim",
    "rules": [[{
      "rule": "current-stage-entered",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.claimAmount > 10000"
    }]]
  }
]
```

## adhoc — Manual Trigger

Task is not triggered automatically; a user or orchestration layer activates it manually:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Manually triggered",
    "rules": [[{ "rule": "adhoc", "id": "Rule_<6chars>" }]]
  }
]
```

## selected-tasks-completed — Depends on Other Tasks

Task triggers when specific sibling tasks finish:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "After assessment and approval",
    "rules": [[{
      "rule": "selected-tasks-completed",
      "id": "Rule_<6chars>",
      "selectedTasksIds": ["tJJETUgZ2", "tYXPi6r8U"]
    }]]
  }
]
```

## Multiple Conditions (OR)

Task triggers when either condition fires:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "High priority or escalated",
    "rules": [
      [{ "rule": "current-stage-entered", "id": "Rule_<6chars>", "conditionExpression": "$vars.priority === 'high'" }],
      [{ "rule": "current-stage-entered", "id": "Rule_<6chars>", "conditionExpression": "$vars.escalated === true" }]
    ]
  }
]
```
