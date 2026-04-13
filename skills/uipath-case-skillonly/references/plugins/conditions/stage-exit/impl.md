# Stage Exit Conditions — Implementation

Exit conditions are placed in `stage.data.exitConditions`.

## exit-only — Standard Completion

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Required tasks completed",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## exit-only with Specific Tasks

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Assessment and approval done",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "selected-tasks-completed",
      "id": "Rule_<6chars>",
      "selectedTasksIds": ["tJJETUgZ2", "tYXPi6r8U"]
    }]]
  }
]
```

## exit-only with Expression Filter

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Approved and tasks done",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "required-tasks-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.action === 'approved'"
    }]]
  }
]
```

## exit-only with Explicit Target Stage

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Route to final stage",
    "type": "exit-only",
    "exitToStageId": "Stage_zlZulP",
    "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## wait-for-user — Human Selects Next Stage

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Awaiting user routing decision",
    "type": "wait-for-user",
    "marksStageComplete": false,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## return-to-origin — Returns to Calling Stage

Used on [exception stages](../../stage-types/exception-stage/impl.md) and stages invoked via re-entry:

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Return to origin",
    "type": "return-to-origin",
    "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## Multiple Exit Conditions (OR Logic)

A stage exits when any of its exit conditions fires:

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Approved path",
    "type": "exit-only",
    "exitToStageId": "Stage_approved",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "required-tasks-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.action === 'approved'"
    }]]
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Rejected path",
    "type": "exit-only",
    "exitToStageId": "Stage_rejected",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "required-tasks-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.action === 'rejected'"
    }]]
  }
]
```
