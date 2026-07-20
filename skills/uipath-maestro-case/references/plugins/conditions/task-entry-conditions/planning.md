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
| `display-name` | sdd.md Display Name column (optional) | Carry the SDD value verbatim. Omit when the SDD cell is blank / `—` — do NOT invent one; impl defaults it to `Entry Rule {N}`. |
| `rule-type` | From catalog below | |
| `selected-tasks-ids` | Required for `selected-tasks-completed` | Comma-separated task IDs |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — see [connector-trigger-common.md § Planning Pipeline](../../../connector-trigger-common.md#planning-pipeline) |
| `condition-expression` | Optional | Extra `=js:` gate on **case state** (`=js:vars.X ...`) — NOT the event payload (no `event` namespace) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-common.md § tasks.md fields (planning)](../../../connector-trigger-common.md#tasksmd-fields-planning). |

## Rule-Type Catalog (task-entry scope)

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `current-stage-entered` | Fires when the containing stage is entered | — |
| `selected-tasks-completed` | Fires when specific sibling tasks in the same stage complete | `selectedTasksIds` |
| `wait-for-connector` | Waits for a connector event (binds an IS connector trigger under `uipath`) | connector fields; `conditionExpression` optional |
| `adhoc` | Ad hoc tasks run only when a user triggers them from the case app. | `conditionExpression` (optional) |
| `runs-sequentially` | Sequential tasks run in the order they appear in the stage from top to bottom. The frontend toggle writes this rule as the task's entry condition. | `conditionExpression` (optional) |

### Frontend task-mode mapping

The Case App selector has three distinct modes:

| UI mode | JSON/task-entry meaning | Required behavior |
|---|---|---|
| Sequential | `runs-sequentially` only | Preserve task order. The first task starts when the stage is entered; each later task starts after its predecessor completes. |
| Event-triggered | An authored event/condition, normally `wait-for-connector` for an external event | Do not add `runs-sequentially`. A stage-entered task is not automatically an event-triggered task; retain the explicit event rule and its connector configuration. |
| Manually-triggered (adhoc) | `adhoc` only | Set `isRequired: false`; the user launches it from the Case App. Do not add another entry event or treat it as sequential. |

`adhoc` is task-entry-only. It is never a stage entry rule and never a substitute for `wait-for-connector`.

## Ordering

Task entry conditions are created **after** all tasks in the stage have been added (so `selected-tasks-ids` can resolve).

For a sequential chain, preserve the task order in the stage's `data.tasks` structure and add one `runs-sequentially` entry condition to every task in the chain. The first task uses the rule as its stage-entry trigger; later tasks use it as the preceding-task-completed trigger. Do not add a separate `current-stage-entered` condition to the first sequential task.

## tasks.md Entry Format

```markdown
## T<n>: Add task-entry condition for "<task>" in "<stage>" — <summary>
- target-stage: "<stage-name>"
- target-task: "<task-name>"
- display-name: "<name>"                  # optional — omit when SDD Display Name cell is blank; impl defaults to "Entry Rule {N}"
- rule-type: selected-tasks-completed
- selected-tasks: "<Task A>, <Task B>"
- condition-expression: "=js:vars.X..."   # optional gate on case state, NOT the event payload
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-common.md § tasks.md fields (planning)](../../../connector-trigger-common.md#tasksmd-fields-planning).
