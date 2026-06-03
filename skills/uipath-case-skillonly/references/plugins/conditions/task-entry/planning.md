# Task Entry Conditions — Planning

Task entry conditions control when a task within a stage is triggered.

## Default Behaviour

Most tasks use `current-stage-entered` — the task runs automatically when the stage is entered. Always set this as the default entry condition unless you need something different.

## When to Override the Default

| Scenario | Rule to use |
|---|---|
| Task runs on every stage entry (default) | `current-stage-entered` |
| Task should only run if a variable condition is true | `current-stage-entered` + `conditionExpression` |
| Task is triggered manually by a user (not automatically) | `adhoc` |
| Task triggers when an external connector event fires | `wait-for-connector` |
| Task triggers only after specific other tasks complete | `selected-tasks-completed` |

## conditionExpression on Task Entry

Use to conditionally skip a task based on case variable values at stage entry time:

```
vars.claimAmount > 10000        // only run for high-value claims
vars.region === 'EU'            // only for EU region
vars.escalated === true         // only if escalated
```
