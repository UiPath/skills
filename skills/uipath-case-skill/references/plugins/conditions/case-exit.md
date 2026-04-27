# Case Exit Conditions — Implementation

Case exit conditions live under `root.caseExitConditions`. They determine when the whole case should exit. The first condition that evaluates to true takes effect.

## Condition Object Shape

```json
{
  "id": "Condition_<6chars>",
  "displayName": "<human-readable label>",
  "rules": [[{ "rule": "<rule-type>", "id": "Rule_<6chars>", ...ruleFields }]],
  "marksCaseComplete": true | false | absent
}
```

| `marksCaseComplete` | Meaning |
|---|---|
| `true` | Case ends — recorded as successfully completed |
| `false` or absent | Case ends — recorded as exited-without-completion (withdrawn, denied, abandoned) |

## Patterns

### Standard — all required stages complete

```json
"caseExitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case resolved",
    "rules": [[{ "rule": "required-stages-completed", "id": "Rule_<6chars>" }]],
    "marksCaseComplete": true
  }
]
```

### With a guard expression

Add `conditionExpression` to require a variable condition on top of stage completion:

```json
"rules": [[{
  "rule": "required-stages-completed",
  "id": "Rule_<6chars>",
  "conditionExpression": "=js:vars.finalDecision === 'approved'"
}]]
```

### Multiple exit paths

Combine entries — e.g., happy-path completion + early exit from an exception stage:

```json
"caseExitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case complete",
    "rules": [[{ "rule": "required-stages-completed", "id": "Rule_<6chars>" }]],
    "marksCaseComplete": true
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Withdrawn",
    "rules": [[{
      "rule": "selected-stage-completed",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_withdrawn"
    }]]
  }
]
```

The second entry omits `marksCaseComplete` — the case closes but is not recorded as successfully completed.

## Rule Type Reference

| `rule` value | Companion fields | When to use |
|---|---|---|
| `required-stages-completed` | `conditionExpression?` | All `isRequired: true` stages finished — standard happy-path close |
| `selected-stage-completed` | `selectedStageId`, `conditionExpression?` | Specific stage completes (e.g., "Settled") |
| `selected-stage-exited` | `selectedStageId`, `conditionExpression?` | Specific stage exits (any reason) |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | External event |
| `adhoc` | `conditionExpression?` | Manual close at any time |
