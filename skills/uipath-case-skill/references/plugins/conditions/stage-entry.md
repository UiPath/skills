# Stage Entry Conditions

Stage entry conditions live under `stage.data.entryConditions`. They determine when a stage becomes active. Every stage needs at least one.

## Condition Object Shape

```json
{
  "id": "Condition_<6chars>",
  "displayName": "<human-readable label>",
  "isInterrupting": false,
  "rules": [[{ "rule": "<rule-type>", "id": "Rule_<6chars>", ...ruleFields }]]
}
```

- Rules are DNF: `[[ruleA, ruleB], [ruleC]]` = `(A AND B) OR C`. Most stages need only `[[rule]]`.
- Any rule can include `conditionExpression` — a `=js:` guard that must be true for activation.
- Set `isInterrupting: true` on the **condition** (not the rule) to preempt running work in the source stage — common for ExceptionStage entries.

## Patterns

### case-entered — first stage only

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case entered",
    "rules": [[{ "rule": "case-entered", "id": "Rule_<6chars>" }]]
  }
]
```

### selected-stage-completed — depends on another stage finishing

```json
"rules": [[{
  "rule": "selected-stage-completed",
  "id": "Rule_<6chars>",
  "selectedStageId": "Stage_f95rff"
}]]
```

Add `conditionExpression` to gate on a variable:

```json
"rules": [[{
  "rule": "selected-stage-completed",
  "id": "Rule_<6chars>",
  "selectedStageId": "Stage_f95rff",
  "conditionExpression": "=js:vars.approvalStatus === 'approved'"
}]]
```

### selected-stage-exited — depends on another stage exiting

Same shape as above, fires on exit regardless of completion:

```json
"rules": [[{
  "rule": "selected-stage-exited",
  "id": "Rule_<6chars>",
  "selectedStageId": "Stage_f95rff"
}]]
```

### current-stage-entered — activates on every entry

Fires each time the stage is entered, including re-entries:

```json
"rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
```

### adhoc — manual activation

```json
"rules": [[{ "rule": "adhoc", "id": "Rule_<6chars>" }]]
```

### OR logic — multiple rule sets

Stage activates when either inner array fires:

```json
"rules": [
  [{ "rule": "selected-stage-completed", "id": "Rule_<6chars>", "selectedStageId": "Stage_aaa111" }],
  [{ "rule": "selected-stage-completed", "id": "Rule_<6chars>", "selectedStageId": "Stage_bbb222" }]
]
```

## Rule Type Reference

| `rule` value | Companion fields | When to use |
|---|---|---|
| `case-entered` | `conditionExpression?` | First stage; activates when the case starts |
| `current-stage-entered` | `conditionExpression?` | Activates each time stage is entered (re-entry-aware) |
| `selected-stage-completed` | `selectedStageId`, `conditionExpression?` | Wait for another stage to complete |
| `selected-stage-exited` | `selectedStageId`, `conditionExpression?` | Wait for another stage to exit (regardless of completion) |
| `selected-tasks-completed` | `selectedTasksIds[]`, `conditionExpression?` | Wait for specific tasks across the case |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | External connector event |
| `adhoc` | `conditionExpression?` | Manually triggered at any point |

