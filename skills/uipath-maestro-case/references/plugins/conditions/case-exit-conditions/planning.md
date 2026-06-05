# case-exit-conditions — Planning

Conditions that control **when the entire case completes (or exits non-completing)**. Attach at the case root level, not to any stage.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "case exit condition"** (or close variants: "case exit conditions", "case completion condition", "case close condition").

For stage-level conditions, use [stage-entry-conditions](../stage-entry-conditions/planning.md) / [stage-exit-conditions](../stage-exit-conditions/planning.md). For task-level, use [task-entry-conditions](../task-entry-conditions/planning.md).

## No omission — one T-task per sdd.md case-exit row

Every case-exit condition declared in sdd.md gets its own T-task — **including rule-type `required-stages-completed` with `marks-case-complete: true`** (the "preferred pattern"). Never skip a condition because it's the default completion shape. If sdd.md wrote the row, `tasks.md` emits the T-task.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md Display Name column (optional) | Carry the SDD value verbatim. Omit when the SDD cell is blank / `—` — do NOT invent one; impl defaults it to `Complete Rule {N}` (marks-case-complete `true`) / `Exit Rule {N}` (`false`). e.g., "Case resolved", "Closed — escalation path" |
| `marks-case-complete` | sdd.md | `true` for normal completion, `false` for non-completing exits |
| `rule-type` | From catalog below | See §Rule-type catalog |
| `selected-stage-id` | Required for `selected-stage-*` rule-types | Resolved from stage capture map |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — see [connector-trigger-common.md § Planning Pipeline](../../../connector-trigger-common.md#planning-pipeline) |
| `condition-expression` | Optional on any rule-type | Extra `=js:` gate on **case state** (`=js:vars.X ...`) — NOT the event payload (no `event` namespace) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-common.md § tasks.md fields (planning)](../../../connector-trigger-common.md#tasksmd-fields-planning). |

## Rule-Type Catalog (case-exit scope)

Allowed `ruleType` values depend on `marks-case-complete`:

**When `marks-case-complete: true`** (the case completes):

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `required-stages-completed` | **Preferred.** Case completes when every stage with `isRequired: true` (set in the stage node's `data.isRequired`) has completed. No stage list needed. | — |
| `wait-for-connector` | Wait for an external connector event to close the case (fills `uipath`). | connector fields; `conditionExpression` optional |

**When `marks-case-complete: false`** (the case exits without closing):

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `selected-stage-completed` | Exit triggered by a specific stage completing. | `selectedStageId` |
| `selected-stage-exited` | Exit triggered by a specific stage being exited (even without completing). | `selectedStageId` |
| `wait-for-connector` | Wait for an external connector event (fills `uipath`). | connector fields; `conditionExpression` optional |

## Preferred Pattern

For most cases, define a single completion condition with `required-stages-completed` + `marks-case-complete: true`. The `isRequired` flag on each stage (from [`plugins/stages/`](../../stages/planning.md)) controls which stages count toward completion.

Add non-completing exit conditions only when the sdd.md explicitly describes an exit path that does NOT close the case (rare).

## Ordering

Case exit conditions are created **after** all stages exist (so `selectedStageId` can resolve via the stage capture map). In `tasks.md`, place these between stage conditions and SLA.

## tasks.md Entry Format

```markdown
## T<n>: Add case-exit condition — <summary>
- display-name: "<name>"                 # optional — omit when blank; impl defaults to "Complete Rule {N}"/"Exit Rule {N}" per marks-case-complete
- marks-case-complete: true
- rule-type: required-stages-completed
- selected-stage: "<stage-name>"        # only for selected-stage-* rule-types
- condition-expression: "=js:vars.X..."  # optional gate on case state, NOT the event payload
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-common.md § tasks.md fields (planning)](../../../connector-trigger-common.md#tasksmd-fields-planning).
