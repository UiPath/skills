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
| `rationale` | sdd.md task Design Rationale | Required reviewer context for the activation/sequencing choice. Not emitted into caseplan JSON. |
| `display-name` | sdd.md Display Name column (optional) | Carry the SDD value verbatim. Omit when the SDD cell is blank / `—` — do NOT invent one; impl defaults it to `Entry Rule {N}`. |
| `rule-type` | From catalog below | |
| `selected-tasks-ids` | Required for `selected-tasks-completed` | Comma-separated task IDs |
| `sla-target` | `sla-status-change` arg 1 | `"root"` (case-level SLA) or the SLA-owning stage name — normally the stage containing this task. Scopes the lookups below to that one SLA table. Required for `sla-status-change` |
| `sla-display-name` | `sla-status-change` arg 2 — the target's SDD `SLA Title` (or a Variable SLA Rules `Display Name`) | Target-unique SLA rule title; resolves to the SLA rule ID emitted from §4.8 during Phase 2. Required |
| `escalation-display-name` | `sla-status-change` arg 3 — a `Display Name` from that target's SDD escalation table | Target-unique **at-risk** escalation title; resolves to its escalation ID. **At-risk only** — omit for a breach response, which references the SLA alone ([sla-response-shapes.md § Status](../../../sla-response-shapes.md)) |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — see [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline) |
| `condition-expression` | Optional | Extra `=js:` gate on **case state** (`=js:vars.X ...`) — NOT the event payload (no `event` namespace) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning). |

## Rule-Type Catalog (task-entry scope)

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `current-stage-entered` | Fires when the containing stage is entered | — |
| `selected-tasks-completed` | Fires when specific non-adhoc sibling tasks in the same stage complete | `selectedTasksIds` |
| `wait-for-connector` | Waits for a connector event (binds an IS connector trigger under `uipath`) | connector fields; `conditionExpression` optional |
| `adhoc` | Ad hoc tasks run only when a user triggers them from the case app. This controls task activation only; choose the task type separately from what the task does. | `conditionExpression` (optional) |
| `runs-sequentially` | Sequential tasks run in the order they appear in the stage from top to bottom. The frontend toggle writes this rule as the task's entry condition. | `conditionExpression` (optional) |
| `sla-status-change` | Fires when a referenced case/stage SLA changes status — the `start-task` SLA response ([sla-response-shapes.md](../../../sla-response-shapes.md)) | `sla-target`, `sla-display-name`, and (at-risk only) `escalation-display-name` |

### Frontend task-mode mapping

The Case App selector has three distinct modes:

| UI mode | JSON/task-entry meaning | Required behavior |
|---|---|---|
| Sequential | `runs-sequentially` only | Preserve the frontend's ordered `data.tasks` structure. A strict chain is consecutive single-task sets (`[[A], [B], [C]]`); explicit parallel siblings after the same predecessor share one later set (`[[A], [B, C], [D]]`) and each member of that set also uses `runs-sequentially` so it starts when the previous task set completes. The first sequential task starts when the stage is entered, and later sequential tasks use the upstream-task-set completion trigger represented by the preserved task-set/order structure. |
| Event-triggered | An authored event/condition, normally `wait-for-connector` for an external event | Do not add `runs-sequentially`. A stage-entered task is not automatically an event-triggered task; retain the explicit event rule and its connector configuration. |
| Manually-triggered (adhoc) | `adhoc` only | Set `isRequired: false`; the user launches it from the Case App. Do not add another entry event or treat it as sequential. Do not change the task type merely because it is manual. |

> **`event-triggered` classifies the entry rule, not the task type.** `wait-for-connector` is both a task type and a rule type. A task whose **entry rule** is the connector event is `event-triggered` and must not carry `runs-sequentially`. A task **typed** `wait-for-connector` (or `execute-connector-activity`) whose entry is positional keeps its connector event in its own `data`, and its entry rule follows its activation mode: `current-stage-entered` when it arms on stage entry, or `runs-sequentially` when it must arm only after a predecessor creates the obligation (`activation-mode: parallel-after-predecessor`). Arm listeners and clocks when the obligation is created, not after the response is expected.

`adhoc` is task-entry-only. It is never a stage entry rule, never a case trigger, never a substitute for `wait-for-connector`, and never the way to model a user-selected interrupting lane. Use a secondary stage with `user-selected-stage` for that.

During design-lane authoring (`uipath-planner`), any requirement that says `then`, `after`, `before`, `in order`, or otherwise declares an immediate dependency should be authored as `runs-sequentially` on every task in that run. Do not convert it to parallel `current-stage-entered` tasks merely because no data binding links them. Use parallel mode only when the rationale says the tasks are independent. **Phase 1 does not re-author a supplied or approved SDD:** if its task row explicitly says `selected-tasks-completed("<previous task>")`, preserve that exact rule and selector even when the selected task is immediately previous.

## Phase 1 Plan Presentation Contract

The task T-entry in `tasks.md §4.6` must already expose the task mode before this condition T-entry is created:

```markdown
- activation-mode: sequential
- entry-rule: runs-sequentially
```

This pair lives on the task's own §4.6 T-entry, not on this condition T-entry. This file's own entry format below uses `rule-type:`, not `entry-rule:` — the two fields are not interchangeable and belong to two different T-entries. Writing `rule-type:` here does NOT retroactively satisfy the §4.6 requirement; if the task's own T-entry is missing `entry-rule:`, go back and add it there.

For every task-entry-condition T-entry, verify the task's `activation-mode` and this condition's `rule-type` agree:

| activation-mode | Allowed rule-type |
|---|---|
| `sequential` | `runs-sequentially` |
| `parallel` | `current-stage-entered` |
| `event-triggered` | `wait-for-connector` or another explicitly authored event/condition rule |
| `adhoc` | `adhoc` |
| `fan-in` | `selected-tasks-completed` with multiple selected tasks or an explicit convergence rationale |
| `conditional-gate` | `selected-tasks-completed` with a branch/non-immediate dependency rationale, or the explicitly authored gate rule |

During design-lane authoring (`uipath-planner`), a plain immediate ordered run with no fan-in, branch, event, or non-immediate dependency rationale should be modeled as `activation-mode: sequential` with `rule-type: runs-sequentially`. During Phase 1, never use that heuristic to rewrite an explicit supplied/approved SDD row: preserve `selected-tasks-completed` and its selector as `conditional-gate` or `fan-in`, including when all tasks are placeholders.

## Ordering

Task entry conditions are created **after** all tasks in the stage have been added (so `selected-tasks-ids` can resolve).

For sequential tasks, preserve the frontend's ordered `data.tasks` structure, including any explicitly parallel sibling sets; do not flatten the stage into one global chain and do not group a strict chain into one inner array. Add one `runs-sequentially` entry condition to each sequential task. The first task uses the rule as its stage-entry trigger; later tasks use it as the upstream-task-set-completed trigger. Do not add a separate `current-stage-entered` condition to the first sequential task. Lane or task-set placement is structural; the entry rule carries the sequential intent.

## tasks.md Entry Format

```markdown
## T<n>: Add task-entry condition for "<task>" in "<stage>" — <summary>
- target-stage: "<stage-name>"
- target-task: "<task-name>"
- activation-mode: sequential | parallel | event-triggered | adhoc | fan-in | conditional-gate
- rationale: "<why this activation/sequencing mode fits>"
- display-name: "<name>"                  # optional — omit when SDD Display Name cell is blank; impl defaults to "Entry Rule {N}"
- rule-type: selected-tasks-completed
- selected-tasks: "<Task A>, <Task B>"
- condition-expression: "=js:vars.X..."   # optional gate on case state, NOT the event payload
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning).

<!-- END: planning.md -->
