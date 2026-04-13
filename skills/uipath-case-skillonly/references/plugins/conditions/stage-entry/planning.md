# Stage Entry Conditions — Planning

Stage entry conditions control when a stage becomes active. Every stage needs at least one entry condition.

## Rule Type Selection

| Scenario | Rule type |
|---|---|
| First stage — activates when the case starts | `case-entered` |
| Stage activates when a specific preceding stage **finishes** | `selected-stage-completed` |
| Stage activates when a specific preceding stage **exits** (even if not marked complete) | `selected-stage-exited` |
| Stage activates every time it is entered (re-entry aware) | `current-stage-entered` |
| Stage can be activated manually at any point by a user | `adhoc` |
| Stage activates when all required stages are done | Use case-exit conditions instead |

## Combining Rules (DNF)

Rules are arrays of arrays: `[[ruleA, ruleB], [ruleC]]` means `(A AND B) OR C`.

Most stages need only a single rule in a single set: `[[rule]]`.

## conditionExpression

Any rule can include an optional `conditionExpression` — a JavaScript expression evaluated when the rule fires. The condition must be true for the entry condition to activate.

```
$vars.priority === 'high'
$vars.amount > 10000
$vars.region === 'EU' && $vars.claimType === 'property'
```

Do **not** prefix with `=js:` — these expressions are always evaluated as JavaScript.

## isInterrupting

Set `isInterrupting: true` when this entry condition should interrupt the current stage mid-execution to redirect to this stage. Leave `false` (default) for standard sequential entry.
