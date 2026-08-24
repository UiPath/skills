# SLA Response Shapes

Rules for turning an SLA at-risk / breach event into case behavior, on the BUILD side — SKILL.md Rule 21, [brownfield.md § SLA responses](brownfield.md#sla-responses-in-a-brownfield-edit), and the SLA / condition / task plugins all link here instead of restating it.

> **Twin of a canonical page in `uipath-planner`.** The case SLA response model is owned by `uipath-planner`'s case design layers guide (Layer 4) — that is where the product's case knowledge and guidance live. This page exists because skills in this repo must function with siblings absent and may not read another skill's files, and because a brownfield edit designs deltas with no SDD and no planner in the loop. **It is a twin, not a second source of truth: a change to the response model lands in the planner first, then here, in the same PR.** The invariants both sides must agree on are pinned by `tests/tasks/uipath-planner/_shared/test_case_twin_parity.py`.

An SLA **clock** ([plugins/sla/impl-json.md](plugins/sla/impl-json.md)) and its **response** are separate authoring decisions. Read the response off the requirement — never off the SLA's scope.

## 1. Pick the response

| Response | Source says | What you author |
|---|---|---|
| `notify-only` | notify / alert / email / page someone, nothing more | an escalation on the target's `slaRules[].escalationRule`. **No** stage, task, or condition. |
| `start-task` | follow-up work inside the **same** breached stage — "as part of the review", "the reviewer keeps working and also does X", a named task for a manager or peer | one task in the breached stage whose **own** entry condition is the `sla-status-change` rule (§3) |
| `enter-stage` | a separate lane owns it — "hand it to", "escalate into `<Lane>`", ownership change, recovery, a visible lifecycle step | a separate stage carrying the `sla-status-change` entry condition |
| `exit-stage` | the breached stage should end, fail, or route away | a stage-exit row |
| `exit-case` | the case should close, cancel, fail, or reach an alternate terminal outcome | a `metadata.caseExitRules[]` row |

**Default:** absent a stated response, at-risk and breached are both `notify-only`. Never invent a stage, task, or routing change for a requirement that only asks to notify someone.

**`start-task` vs `enter-stage` turns on WHERE the work lives — not on whether it interrupts.** `enter-stage` can itself be non-interrupting, so "the team keeps working" does not choose between them. A named **task** ("raise a Senior Assessor Check approval") never justifies a new stage: if the target you are about to write is a task name rather than a lane the source describes in its own right, the response is `start-task`, and the task goes in the breached stage.

## 2. Status rides on the escalation reference

| Status | Rule fields | Requires |
|---|---|---|
| Breached | `slaId` only — an **absent `escalationId` is the persisted representation of Breached** | nothing else; a breach response needs no escalation to exist |
| At-risk | `slaId` + a concrete `escalationId` | that escalation must be declared **on the same SLA** and have `triggerInfo.type: "at-risk"` |

Never author the Case Designer's `"any"` escalation sentinel.

## 3. Where the rule lives

`sla-status-change` is legal on **task entry** and on **stage entry** (both validate — see § Verified below):

- **`start-task`** — put the rule on the follow-up **task's** `entryConditions`, referencing the breached stage's own SLA. The task fires on the SLA event itself: no stage re-entry, no re-run of the stage's other tasks. It is the **only** authorable `start-task` shape.
- **`enter-stage`** — put the rule on the destination **stage's** `entryConditions`.

**Never author `start-task` as a stage-entry rule on the breached stage.** `validate` accepts it, but stage re-entry restarts every task in that stage whose `shouldRunOnlyOnce` is `false` — the default for every task type — so a breach meant to add one manager check silently re-runs the whole stage. This is defect 4 in §5.

Rule JSON, per-scope emit details, and post-write checks: [plugins/conditions/stage-entry-conditions/impl-json.md § sla-status-change](plugins/conditions/stage-entry-conditions/impl-json.md) (stage scope) and [plugins/conditions/task-entry-conditions/impl-json.md](plugins/conditions/task-entry-conditions/impl-json.md) (task scope).

## 4. Interrupting

`isInterrupting` follows what the response does to **active work**, never the SLA's scope:

- `true` — the response stops, pauses, takes over, or reroutes work in flight.
- `false` — the response runs alongside work that continues (parallel oversight).

`isInterrupting` is a property of a **stage-entry** condition, so it applies to `enter-stage` only. A `start-task` response is a task-entry rule and has no interrupting cell at all — render `—`.

**A non-interrupting SLA lane is still a secondary stage.** Keep `stageType: "secondary"` and `isRequired: false`; do NOT convert it to a regular stage to satisfy "every secondary-stage entry is interrupting" — a regular stage joins the main flow and, when required, gates case completion. In `sdd.md`, the stage-level `Interrupting` field and that entry row must agree; `Yes` on the stage with `No` on its only entry row is a blocking render error.

## 5. Four defects `validate` cannot see

It passes on all four, so they are on the author:

1. **A task with no entry condition never starts.** `validate` accepts `entryConditions: []` and even a missing key. Every task added for a `start-task` response carries its own entry condition (§3).
2. **A non-interrupting lane emitted as a regular stage** (§4) — silently changes the completion contract.
3. **`escalationId: "any"` repaired by repointing.** Removing the key is the fix; substituting a concrete escalation also turns `validate` green but converts a Breached rule into an at-risk rule — a behavior change the user never asked for. The same conversion happens when a correct breach rule is "completed" by adding an escalation because a checklist looked like it required one: a breach rule carrying only `slaId` is finished, not missing a field.
4. **`start-task` authored as stage re-entry** (§3) — re-runs every `shouldRunOnlyOnce: false` task in the breached stage, not just the follow-up.

## Verified

Probed with `uip maestro case validate` on **uip 1.198.0-preview.102** (2026-07-31):

| Shape | Result |
|---|---|
| breach on a separate stage (`slaId` only), `isInterrupting` `true` / `false` | valid / valid |
| breach as a **stage-entry** rule on the breached stage's own SLA, `isInterrupting` `true` / `false` | valid / valid — but **never author this**: it is defect 4 (§5), invisible to the CLI |
| breach / at-risk on a **task's** `entryConditions` (stage SLA and root SLA) | valid |
| at-risk with an escalation declared on that SLA | valid |
| at-risk borrowing another SLA's escalation | **invalid** — "The escalation referenced by rule … no longer exists" |
| `escalationId: "any"` | **invalid** — same error |
| dangling `slaId` | **invalid** — "The SLA referenced by rule … no longer exists" |
| task with `entryConditions: []` or the key absent | valid (defect is invisible to the CLI) |

<!-- END: sla-response-shapes.md -->
