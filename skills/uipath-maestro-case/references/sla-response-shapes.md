# SLA Response Shapes

Canonical rules for turning an SLA at-risk/breach event into case behavior. This is the single source of truth for SKILL.md Rule 22, planner case authoring (SLA response model—design side), [brownfield.md § SLA responses](brownfield.md#sla-responses-in-a-brownfield-edit), and the SLA, condition, and task plugins. An SLA **clock** ([plugins/sla/impl-json.md](plugins/sla/impl-json.md)) and response are separate decisions: read the response from the requirement, never the SLA scope.

## 1. Pick the response

| Response | Requirement says | Author |
|---|---|---|
| `notify-only` | notify / alert / email / page someone, nothing more | an escalation on the target's `slaRules[].escalationRule`; **no** stage, task, or condition |
| `start-task` | follow-up work in the **same** breached stage; the reviewer continues and also does something, or a manager/peer task is named | one task in the breached stage whose **own** entry condition is the `sla-status-change` rule (§3) |
| `enter-stage` | a separate lane owns it; handoff, escalation into `<Lane>`, ownership change, recovery, or visible lifecycle step | a separate stage with the `sla-status-change` entry condition |
| `exit-stage` | the breached stage ends, fails, or routes away | a stage-exit row |
| `exit-case` | the case closes, cancels, fails, or reaches another terminal outcome | a `metadata.caseExitRules[]` row |

**Default:** without a stated response, both at-risk and breached are `notify-only`. Never invent a stage, task, or routing change for notification alone.

Choose `start-task` versus `enter-stage` by where the work lives, not whether it interrupts. `enter-stage` may be non-interrupting; continuing team work does not decide it. A named **task** (for example, "raise a Senior Assessor Check approval") never justifies a new stage: when the target is a task name rather than an independently described lane, use `start-task` in the breached stage.

## 2. Status rides on the escalation reference

| Status | Rule fields | Requirement |
|---|---|---|
| Breached | `slaId` only—an **absent `escalationId` is the persisted representation of Breached** | none; a breach response needs no escalation |
| At-risk | `slaId` + concrete `escalationId` | the escalation is declared **on the same SLA** and has `triggerInfo.type: "at-risk"` |

Never author the Case Designer's `"any"` escalation sentinel.

## 3. Where the rule lives

`sla-status-change` is legal on **task entry** and **stage entry** (both validate—see § Verified):

- **`start-task`**: put it on the follow-up task's `entryConditions`, referencing the breached stage's own SLA. It fires on the SLA event itself; it does not re-enter the stage or rerun its other tasks. This is the **only** authorable `start-task` shape.
- **`enter-stage`**: put it on the destination stage's `entryConditions`.

**Never author `start-task` as a stage-entry rule on the breached stage.** Although `validate` accepts it, stage re-entry restarts every task whose `shouldRunOnlyOnce` is `false` (the default for every task type), so a breach intended to add one manager check silently reruns the whole stage. This is defect 4 in §5.

Rule JSON, per-scope emit details, and post-write checks: [plugins/conditions/stage-entry-conditions/impl-json.md § sla-status-change](plugins/conditions/stage-entry-conditions/impl-json.md) (stage scope) and [plugins/conditions/task-entry-conditions/impl-json.md](plugins/conditions/task-entry-conditions/impl-json.md) (task scope).

## 4. Interrupting

`isInterrupting` follows the response's effect on **active work**, never the SLA scope:

- `true`: stops, pauses, takes over, or reroutes work in flight.
- `false`: runs alongside continuing work (parallel oversight).

`isInterrupting` belongs to a **stage-entry** condition and therefore applies only to `enter-stage`. `start-task` is a task-entry rule with no interrupting cell; render `—`.

A non-interrupting SLA lane remains a secondary stage: keep `stageType: "secondary"` and `isRequired: false`; do **not** convert it to a regular stage to satisfy "every secondary-stage entry is interrupting". A regular stage joins the main flow and, when required, gates case completion. In `sdd.md`, the stage-level `Interrupting` field and its entry row must agree; `Yes` on the stage with `No` on its only entry row is a blocking render error.

## 5. Four defects `validate` cannot see

`validate` passes all four; prevent them:

1. **A task with no entry condition never starts.** `validate` accepts `entryConditions: []` and a missing key. Every task added for `start-task` carries its own entry condition (§3).
2. **A non-interrupting lane emitted as a regular stage** (§4) silently changes the completion contract.
3. **`escalationId: "any"` repaired by repointing.** Removing the key is the fix; substituting a concrete escalation also turns `validate` green but converts a Breached rule into an at-risk rule — a behavior change the user never asked for. The same conversion happens when a correct breach rule is "completed" by adding an escalation because a checklist looked like it required one: a breach rule carrying only `slaId` is finished, not missing a field.
4. **`start-task` authored as stage re-entry** (§3) reruns every `shouldRunOnlyOnce: false` task in the breached stage instead of only the follow-up.

## Verified

Probed with `uip maestro case validate` on **uip 1.198.0-preview.102** (2026-07-31):

| Shape | Result |
|---|---|
| breach on a separate stage (`slaId` only), `isInterrupting` `true` / `false` | valid / valid |
| breach as a **stage-entry** rule on the breached stage's own SLA, `isInterrupting` `true` / `false` | valid / valid—but **never author this**: defect 4 (§5), invisible to the CLI |
| breach / at-risk on a **task's** `entryConditions` (stage SLA and root SLA) | valid |
| at-risk with an escalation declared on that SLA | valid |
| at-risk borrowing another SLA's escalation | **invalid**—"The escalation referenced by rule … no longer exists" |
| `escalationId: "any"` | **invalid**—same error |
| dangling `slaId` | **invalid**—"The SLA referenced by rule … no longer exists" |
| task with `entryConditions: []` or the key absent | valid (defect is invisible to the CLI) |

<!-- END: sla-response-shapes.md -->
