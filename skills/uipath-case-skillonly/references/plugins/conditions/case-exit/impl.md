# Case Exit Conditions — Implementation

Case exit conditions are placed at `root.caseExitConditions`. They define when the entire case is considered complete.

## Standard Pattern — All Required Stages Complete

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

> Use `required-stages-completed` to end the case when all stages with `isRequired: true` have finished. This is the standard pattern.

## Conditional Completion

Case ends only if a variable condition is true when all required stages complete:

```json
"caseExitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case approved and resolved",
    "rules": [[{
      "rule": "required-stages-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.finalDecision === 'approved'"
    }]],
    "marksCaseComplete": true
  }
]
```

## Multiple Exit Paths

Case can end via different conditions — first to fire wins:

```json
"caseExitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Approved and resolved",
    "rules": [[{
      "rule": "required-stages-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.outcome === 'approved'"
    }]],
    "marksCaseComplete": true
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Rejected and closed",
    "rules": [[{
      "rule": "required-stages-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "$vars.outcome === 'rejected'"
    }]],
    "marksCaseComplete": true
  }
]
```

## Rules

| Rule | When to use |
|---|---|
| `required-stages-completed` | All stages with `isRequired: true` have finished |
| `adhoc` | Case can be closed manually at any time |

> Do **not** use `required-tasks-completed` in case exit conditions — that rule is for stage exit conditions only.
