# Stage Entry Conditions — Implementation

Entry conditions are placed in `stage.data.entryConditions`.

## case-entered — First Stage Only

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case entered",
    "rules": [[{ "rule": "case-entered", "id": "Rule_<6chars>" }]]
  }
]
```

## selected-stage-completed — Depends on Another Stage Finishing

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage 1 completed",
    "rules": [[{
      "rule": "selected-stage-completed",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_f95rff"
    }]]
  }
]
```

With filter expression (only activate if condition is true when stage completes):

```json
{
  "rule": "selected-stage-completed",
  "id": "Rule_<6chars>",
  "selectedStageId": "Stage_f95rff",
  "conditionExpression": "$vars.approvalStatus === 'approved'"
}
```

## selected-stage-exited — Depends on Another Stage Exiting

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Review stage exited",
    "rules": [[{
      "rule": "selected-stage-exited",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_f95rff"
    }]]
  }
]
```

## current-stage-entered — Activates on Every Entry

Used when the stage should trigger every time it is entered, including re-entries:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage entered",
    "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
  }
]
```

With filter expression:

```json
{
  "rule": "current-stage-entered",
  "id": "Rule_<6chars>",
  "conditionExpression": "$vars.priority === 'high'"
}
```

## adhoc — Manual Activation

Stage can be triggered manually at any point during the case:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Adhoc activation",
    "rules": [[{ "rule": "adhoc", "id": "Rule_<6chars>" }]]
  }
]
```

## isInterrupting

Add to any entry condition to allow mid-execution stage interruption:

```json
{
  "id": "Condition_<6chars>",
  "displayName": "High priority interrupt",
  "isInterrupting": true,
  "rules": [[{
    "rule": "selected-stage-completed",
    "id": "Rule_<6chars>",
    "selectedStageId": "Stage_f95rff",
    "conditionExpression": "$vars.escalated === true"
  }]]
}
```

## OR Logic — Multiple Rule Sets

Stage activates when either condition fires (Stage 1 completes OR Stage 2 completes):

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage 1 or Stage 2 completed",
    "rules": [
      [{ "rule": "selected-stage-completed", "id": "Rule_<6chars>", "selectedStageId": "Stage_aaa111" }],
      [{ "rule": "selected-stage-completed", "id": "Rule_<6chars>", "selectedStageId": "Stage_bbb222" }]
    ]
  }
]
```
