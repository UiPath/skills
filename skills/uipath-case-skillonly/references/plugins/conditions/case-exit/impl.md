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
      "conditionExpression": "=js:vars.finalDecision === 'approved'"
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
      "conditionExpression": "=js:vars.outcome === 'approved'"
    }]],
    "marksCaseComplete": true
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Rejected and closed",
    "rules": [[{
      "rule": "required-stages-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "=js:vars.outcome === 'rejected'"
    }]],
    "marksCaseComplete": true
  }
]
```

## Exit Without Successful Completion

A case can exit via a path that **does not** count as a successful completion — for example, an early exit triggered when an exception stage like "Withdrawn" or "Denied" finishes. Omit `marksCaseComplete` (or set it to `false`) on such conditions, and pair them with a primary `required-stages-completed` rule that does mark complete:

```json
"caseExitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case complete rule",
    "rules": [[{ "rule": "required-stages-completed", "id": "Rule_<6chars>" }]],
    "marksCaseComplete": true
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Case exit from 'Withdrawn'",
    "rules": [[{
      "rule": "selected-stage-completed",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_withdrawn"
    }]]
    // marksCaseComplete intentionally absent — this exit closes the case but
    // does not register it as "successfully completed" in reporting / metrics
  }
]
```

| `marksCaseComplete` | Meaning |
|---|---|
| `true` | Case ends and is recorded as successfully completed |
| `false` or absent | Case ends but is recorded as exited-without-completion (e.g., withdrawn, denied, abandoned) |

Use this distinction to keep happy-path completion metrics clean while still allowing early exits via exception stages.

## Rule Type Reference (full FE-aligned set for case exit)

| `rule` value | Companion fields | When to use here (case exit) |
|---|---|---|
| `required-stages-completed` | `conditionExpression?` | All stages with `isRequired: true` have finished — the standard "happy path" close |
| `selected-stage-completed` | `selectedStageId`, `conditionExpression?` | Case ends when a specific stage completes (e.g., a "Settled" stage) |
| `selected-stage-exited` | `selectedStageId`, `conditionExpression?` | Case ends when a specific stage exits (any reason) |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | Case ends on an external event |
| `adhoc` | `conditionExpression?` | Case can be closed manually at any time |

> **Do not use `required-tasks-completed` here** — that rule is stage-scoped only.
>
> **Alternative pattern**: instead of declaring a `caseExitConditions` entry, mark a specific stage's exit as `type: "terminal"` (see [stage-exit/impl.md](../stage-exit/impl.md)). That's the canonical way to express "reaching this stage's completion ends the case" — no entry in `caseExitConditions` needed.
