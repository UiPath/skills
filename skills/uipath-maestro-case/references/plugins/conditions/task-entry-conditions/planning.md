# task-entry-conditions — Planning

Conditions that control **when a specific task within a stage starts**. Attach to a task.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "task entry condition"** (or close variants: "task entry conditions", "entry rule on task", "task gate", "task precondition").

For **stage-level** conditions (entire stage enters/exits), use [stage-entry-conditions](../stage-entry-conditions/planning.md) / [stage-exit-conditions](../stage-exit-conditions/planning.md).

## No omission

One T-entry per SDD Entry Condition row, defaults-looking rows included — completeness contract in [planning.md § 4.0](../../../planning.md#40-completeness-principle-no-omissions).

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
| `escalation-display-name` | `sla-status-change` arg 3 — a `Display Name` from that target's SDD escalation table | Target-unique **at-risk** escalation title; resolves to its escalation ID. **At-risk only** — omit for a breach response, which references the SLA alone (K-SLA-3) |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — see [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline) |
| `condition-expression` | Optional | Extra `=js:` gate on case state only (K-EXPR-2) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning). |

## Rule-Type Catalog (task-entry scope)

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `current-stage-entered` | Fires when the containing stage is entered | — |
| `selected-tasks-completed` | Fires when specific non-adhoc sibling tasks in the same stage complete | `selectedTasksIds` |
| `wait-for-connector` | Waits for a connector event (binds an IS connector trigger under `uipath`) | connector fields; `conditionExpression` optional |
| `adhoc` | Ad hoc tasks run only when a user triggers them from the case app. This controls task activation only; choose the task type separately from what the task does. | `conditionExpression` (optional) |
| `runs-sequentially` | Sequential tasks run in the order they appear in the stage from top to bottom. The frontend toggle writes this rule as the task's entry condition. | `conditionExpression` (optional) |
| `sla-status-change` | Fires when a referenced case/stage SLA changes status — the `start-task` SLA response (K-SLA-4/5) | `sla-target`, `sla-display-name`, and (at-risk only) `escalation-display-name` |

### Frontend task-mode mapping

Mode ↔ rule grammar, sequential/parallel-after-predecessor task-set structure, and adhoc semantics are K-SEQ-1/2/3/4 ([case-knowledge/semantics/sequencing.md](../../../case-knowledge/semantics/sequencing.md)). Build-side specifics:

> **`event-triggered` classifies the entry rule, not the task type.** A task **typed** `wait-for-connector` (or `execute-connector-activity`) whose entry is positional keeps its connector event in its own `data`; its entry rule follows its activation mode (`current-stage-entered` on stage entry, `runs-sequentially` after a predecessor — K-SEQ-2). Arm listeners and clocks when the obligation is created, not after the response is expected.

A user-selected interrupting lane is a secondary stage with `user-selected-stage` — never `adhoc` (K-SEQ-4). **Phase 1 does not re-author a supplied or approved SDD:** if its task row explicitly says `selected-tasks-completed("<previous task>")`, preserve that exact rule and selector even when the selected task is immediately previous.

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

For sequential tasks, preserve the ordered `data.tasks` structure (K-SEQ-2) — never flatten a stage into one global chain or group a strict chain into one inner array. Lane/task-set placement is structural; the entry rule carries the sequential intent.

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
