# stage-entry-conditions — Planning

Conditions that control **when a stage is entered**. Attach to a stage; fire when the inbound rule is satisfied.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "stage entry condition"** (or close variants: "stage entry conditions", "entry rule on stage", "entry gate on <stage>").

For when a stage **exits**, use [stage-exit-conditions](../stage-exit-conditions/planning.md). For when a specific **task** starts, use [task-entry-conditions](../task-entry-conditions/planning.md).

## No omission — one T-task per sdd.md Entry Condition row

Every stage with an **Entry Condition** declared in sdd.md gets its own stage-entry-condition T-task — **including rule-type `case-entered`** and stages with `is-interrupting: false`. Never skip a condition because the rule-type or field values look like defaults. If sdd.md wrote the row, `tasks.md` emits the T-task.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `<stage-id>` | Previously captured from `stages add` | Target stage |
| `display-name` | sdd.md (optional) | e.g., "Pre-check", "Interrupt on Fraud" |
| `is-interrupting` | sdd.md (default `false`) | `true` if the condition interrupts the current stage |
| `rule-type` | Pick from the catalog below | See §Rule-type catalog |
| `selected-stage-id` | Required for `selected-stage-*` rule-types | ID of the referenced stage |
| `condition-expression` | Required for `wait-for-connector` rule-type (and optional for others) | |

## Rule-Type Catalog (stage-entry scope)

Allowed `--rule-type` values and when to pick each:

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `case-entered` | Fires the moment the case is entered (first stage pattern) | — |
| `selected-stage-completed` | Fires when a specific upstream stage completes | `--selected-stage-id` |
| `selected-stage-exited` | Fires when a specific upstream stage exits (even without completing) | `--selected-stage-id` |
| `user-selected-stage` | Fires when a user manually selects/routes to this stage (e.g., via a `return-to-origin` or stage-picker exit) | — |
| `wait-for-connector` | Waits for a connector event | `--condition-expression` |

`is-interrupting: true` means the condition can fire **while another stage is active** and will interrupt it. Use for exception/interrupt flows.

## Ordering

Stage entry conditions are created **after** all stages exist (Step 7 in implementation.md). Source/target stage IDs must both be captured by then.

## tasks.md Entry Format

```markdown
## T<n>: Add stage-entry condition for "<stage>" — <summary>
- target-stage: "<stage-name>"
- display-name: "<name>"
- is-interrupting: false
- rule-type: selected-stage-completed
- selected-stage: "<upstream-stage-name>"
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```
