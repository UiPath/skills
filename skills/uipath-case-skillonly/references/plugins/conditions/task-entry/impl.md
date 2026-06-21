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
      "conditionExpression": "=js:vars.claimAmount > 10000"
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
      [{ "rule": "current-stage-entered", "id": "Rule_<6chars>", "conditionExpression": "=js:vars.priority === 'high'" }],
      [{ "rule": "current-stage-entered", "id": "Rule_<6chars>", "conditionExpression": "=js:vars.escalated === true" }]
    ]
  }
]
```

## Rule Type Reference (full FE-aligned set for task entry)

| `rule` value | Companion fields | When to use here (task entry) |
|---|---|---|
| `current-stage-entered` | `conditionExpression?` | Default — task activates when its stage is entered |
| `selected-tasks-completed` | `selectedTasksIds[]`, `conditionExpression?` | Sequential within a stage — task waits for upstream task(s) |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | Task starts when an external connector event fires (uses `uip case tasks add-connector`) |
| `adhoc` | `conditionExpression?` | Task is manually triggered |

> **Stage-scope rules** (`case-entered`, `selected-stage-completed`, `selected-stage-exited`) generally don't apply to task entry — use them on stage entry conditions instead. The runtime accepts them on tasks but they're semantically off — a task waits for the stage entry, not for cross-stage events.

## Deprecated Fields

### `conditions` with `actionType` (deprecated)

The old `conditions` array with `actionType: "skip"|"run"` is **deprecated**. Do not use:

```json
// DEPRECATED — do not use
"conditions": [
  {
    "id": "...",
    "displayName": "Skip if already processed",
    "actionType": "skip",
    "rules": [[...]]
  }
]
```

**Migration:** Use `entryConditions` instead. The `actionType` semantic is inverted:
- Old `actionType: "skip"` → new `entryConditions` with the **negated** condition (task runs when entry fires)
- Old `actionType: "run"` → new `entryConditions` with the **same** condition

### `skipCondition` (legacy)

The `skipCondition` string field is also deprecated. Use `entryConditions` with a `conditionExpression` instead.
