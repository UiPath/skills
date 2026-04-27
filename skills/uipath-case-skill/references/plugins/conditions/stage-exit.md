# Stage Exit Conditions

Stage exit conditions live under `stage.data.exitConditions`. They determine when a stage completes and what happens afterward. The first condition that evaluates to true takes effect.

## Condition Object Shape

```json
{
  "id": "Condition_<6chars>",
  "displayName": "<human-readable label>",
  "type": "<exit-type>",
  "marksStageComplete": true | false,
  "exitToStageId": "<Stage_id>",
  "rules": [[{ "rule": "<rule-type>", "id": "Rule_<6chars>", ...ruleFields }]]
}
```

- `marksStageComplete`: `true` = counts toward `required-stages-completed`; `false`/absent = does not.
- `exitToStageId`: required only for `send-to-stage` and `rework-stage-and-return`.

## Patterns

### exit-only — standard completion

Most common pattern — `required-tasks-completed` + `marksStageComplete: true`:

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

### return-to-origin — re-entry loop variant

Regular stage returns after re-entry (not first pass). Use `marksStageComplete: false` since the first-pass exit already marked complete:

```json
"rules": [[{
  "rule": "selected-tasks-completed",
  "id": "Rule_<6chars>",
  "selectedTasksIds": ["<followupTaskId>"],
  "conditionExpression": "=js:(vars.finishedRunCountIntake != null && vars.finishedRunCountIntake > 0)"
}]]
```

### Multiple exit conditions (OR logic)

A stage exits when any condition fires — use for branching paths:

```json
"exitConditions": [
  { "type": "exit-only", "exitToStageId": "Stage_approved", "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>",
      "conditionExpression": "=js:vars.action === 'approved'" }]] },
  { "type": "exit-only", "exitToStageId": "Stage_rejected", "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>",
      "conditionExpression": "=js:vars.action === 'rejected'" }]] }
]
```
## Exit Types

| `type` | Behavior | Needs `exitToStageId` |
|---|---|---|
| `exit-only` | Stage exits, flow follows the next edge | no |
| `wait-for-user` | Tasks finish, then a human selects the next stage | no |
| `return-to-origin` | Returns to whichever stage triggered entry | no |
| `terminal` | Stage completion ends the entire case | no |
| `send-to-stage` | Explicitly routes to a target stage (overrides edges) | yes |
| `rework-stage-and-return` | Branches to target stage for rework, then returns here | yes |

## Rule Type Reference

| Rule | Companion fields | When to use |
|---|---|---|
| `required-tasks-completed` | `conditionExpression?` | `marksStageComplete: true` All tasks with `isRequired: true` finish — most common |
| `selected-tasks-completed` | `selectedTasksIds[]`, `conditionExpression?` | `marksStageComplete: false` Specific subset of tasks finish (V12 preferred) |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | External connector event |