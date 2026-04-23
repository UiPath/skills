# task-entry-conditions — Planning

Conditions that control **when a specific task within a stage starts**. Attach to a task.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "task entry condition"** (or close variants: "task entry conditions", "entry rule on task", "task gate", "task precondition").

For **stage-level** conditions (entire stage enters/exits), use [stage-entry-conditions](../stage-entry-conditions/planning.md) / [stage-exit-conditions](../stage-exit-conditions/planning.md).

## No omission — one T-task per sdd.md Entry Condition row

Every task in sdd.md that declares an **Entry Condition** row gets its own task-entry-condition T-task — **including rule-type `current-stage-entered`**. Do NOT skip, collapse, or omit a condition because the rule-type looks like a default. If sdd.md wrote the row, `tasks.md` emits the T-task. "The default behavior would already cover it" is not a valid reason to omit.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `<stage-id>`, `<task-id>` | Captured from prior steps | |
| `display-name` | sdd.md (optional) | |
| `rule-type` | From catalog below | |
| `selected-tasks-ids` | Required for `selected-tasks-completed` | Comma-separated task IDs |
| `condition-expression` | Optional | |

## Rule-Type Catalog (task-entry scope)

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `current-stage-entered` | Fires when the containing stage is entered | — |
| `selected-tasks-completed` | Fires when specific sibling tasks in the same stage complete | `--selected-tasks-ids` |
| `wait-for-connector` | Waits for a connector event | `--condition-expression` |
| `adhoc` | Ad hoc tasks run only when a user triggers them from the case app. | `--condition-expression` (optional) |

## Ordering

Task entry conditions are created **after** all tasks in the stage have been added (so `selected-tasks-ids` can resolve).

## tasks.md Entry Format

```markdown
## T<n>: Add task-entry condition for "<task>" in "<stage>" — <summary>
- target-stage: "<stage-name>"
- target-task: "<task-name>"
- display-name: "<name>"
- rule-type: selected-tasks-completed
- selected-tasks: "<Task A>, <Task B>"
- condition-expression: "<expr>"          # for adhoc / wait-for-connector
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```
