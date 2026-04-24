# stage-exit-conditions — Planning

Conditions that control **when and how a stage exits**. Attach to a stage; fire when the inbound rule is satisfied.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "stage exit condition"** (or close variants: "stage exit conditions", "stage completion condition", "exit rule on <stage>").

For when a stage **enters**, use [stage-entry-conditions](../stage-entry-conditions/planning.md).

## No omission — one T-task per sdd.md Exit Condition row

Every stage with an **Exit Condition** declared in sdd.md gets its own stage-exit-condition T-task — **including type `exit-only`, rule-type `required-tasks-completed`, and `marks-stage-complete: true`**. Never skip a condition because it looks like "the obvious default completion." If sdd.md wrote the row, `tasks.md` emits the T-task.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `<stage-id>` | Captured from stage creation | Target stage |
| `display-name` | sdd.md (optional) | |
| `type` | sdd.md exit style | `exit-only` / `wait-for-user` / `return-to-origin` |
| `exit-to-stage-id` | sdd.md routing target (optional) | Required when routing to a specific stage |
| `marks-stage-complete` | sdd.md (default depends on type) | `true` for completion exits, `false` for diverging routes |
| `rule-type` | From catalog below | |
| `selected-tasks-ids` | Required for `selected-tasks-completed` | Comma-separated task IDs |
| `condition-expression` | Required for `wait-for-connector` | |

## Exit Type Catalog

| Exit `type` | When to pick |
|-------------|--------------|
| `exit-only` | **Default.** Stage exits normally along configured edges. |
| `wait-for-user` | Exit requires manual user decision or approval. |
| `return-to-origin` | Rework / exception loop — sends the case back to the previous stage. |

## Rule-Type Catalog (stage-exit scope)

Allowed `rule-type` values depend on `marks-stage-complete`:

**When `marks-stage-complete: true`:**
| Rule type | Extra fields |
|-----------|--------------|
| `required-tasks-completed` | — |
| `wait-for-connector` | `condition-expression` |

**When `marks-stage-complete: false` (exit-only, routing):**
| Rule type | Extra fields |
|-----------|--------------|
| `selected-tasks-completed` | `selected-tasks-ids` (comma-separated) |
| `wait-for-connector` | `condition-expression` |

## Ordering

Stage exit conditions are created **after** all tasks in the stage have been added (so `selected-tasks-ids` can resolve). Planning records task names; implementation looks up captured IDs.

## tasks.md Entry Format

```markdown
## T<n>: Add stage-exit condition for "<stage>" — <summary>
- target-stage: "<stage-name>"
- display-name: "<name>"
- type: exit-only
- exit-to-stage: "<target-stage-name>"          # optional
- marks-stage-complete: true
- rule-type: required-tasks-completed
- selected-tasks: "<Task A>, <Task B>"          # only if rule-type requires
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```
