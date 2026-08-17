# SLAs & Escalations

Clocks, escalations, and what an at-risk or breached SLA does to the case. Stage semantics and the
interrupting rules for SLA-entered lanes: [model.md](model.md). SDD rendering (SLA cells, the SLA
Response Map): [render-case-definition.md](render-case-definition.md).

## Where SLAs live

| Surface | Location | Notes |
|---|---|---|
| Case | `metadata.slaRules` | |
| Stage | stage `data.slaRules` | Secondary stages included |
| `action` task | The task's own timer/SLA fields | NOT a `slaRules` entry. Add case behavior only when the missed task must change the case graph |

No SLA cells on any other task type.

## slaRules entries

Conditional overrides first (priority order), then a trailing default entry with expression
`=js:true`; the first truthy expression wins.

1. Every entry requires `id` AND a non-empty target-unique `displayName` without `:` — validate
   rejects a missing name (`SLA name is missing`) and a missing id (schema error) (verified on
   uip 1.198.0-preview.102).
2. `count`/`unit` may be omitted only as a pair, on a bare escalation-only entry. Units:
   `min | h | d | w | m`; minute counts bounded 15–1000.
3. Non-default entries require a non-empty expression.
4. Escalations: `id` + non-empty element-unique `displayName` + ≥ 1 recipient (scope `User` /
   `UserGroup`); `atRiskPercentage` required exactly when the trigger type is `at-risk`.

## Breached vs at-risk — how status is selected

| Status | The `sla-status-change` rule references | Requires |
|---|---|---|
| Breached | The SLA alone — an absent escalation reference IS the persisted breached shape | Nothing else. Never "complete" a breach rule with an escalation: that converts it to at-risk |
| At-risk | The SLA + one concrete at-risk escalation declared on that same SLA | That escalation must exist on that SLA |

Never the designer's `any` escalation sentinel. Borrowed and dangling references fail validate:
`The escalation referenced by rule … no longer exists` / `The SLA referenced by rule … no longer
exists`.

## Choosing the response

Pick from the source's words — WHERE the work lives, never whether it interrupts. A named task never
justifies a new stage.

| Response | Source says | What you author | Interrupting cell |
|---|---|---|---|
| `notify-only` | notify / alert / page someone, nothing more | An escalation on the target's `slaRules` — no stage, task, or condition | `n/a` |
| `start-task` | Follow-up work inside the SAME breached stage ("as part of the review", a named task for a manager or peer) | One task in the breached stage carrying `sla-status-change` as its OWN task-entry row, against that stage's (or the case's) SLA | `—` — a task entry interrupts nothing; never `Yes`/`No` |
| `enter-stage` | A separate lane owns it ("hand it to", "escalate into <Lane>") | A separate stage carrying the `sla-status-change` entry row | `Yes` when the response pauses, takes over, or reroutes active work; `No` for parallel oversight |
| `exit-stage` | The breached stage should end or route away | A stage-exit row | Per exit semantics |
| `exit-case` | The case should close, cancel, or reach an alternate terminal | A case-exit row | Per exit semantics |

Never author `start-task` as a stage-entry row on the breached stage: it validates, but stage
re-entry re-runs every task whose `shouldRunOnlyOnce` is `false` — a breach meant to add one manager
check silently re-runs the whole stage.

## Defaults when the source is silent

- No stated response → both statuses `notify-only`. Never invent a stage, task, or routing change.
- At-risk threshold: SLA ≤ 3 days → 75%; 3–10 days → 70%; > 10 days → 80%.
- Recipients: at-risk → the owner persona's user group; breached → the leadership tier (Compliance
  for regulation-driven cases). Record substituted defaults with provenance.

## Verified behavior (uip 1.198.0-preview.102)

| Shape | Result |
|---|---|
| Breach entry on a separate stage, either interrupting value | valid |
| Breach / at-risk on a task's `entryConditions` (stage or case SLA) | valid |
| At-risk with a same-SLA escalation | valid |
| At-risk borrowing another SLA's escalation | invalid |
| `escalationId: "any"` | invalid |
| Dangling SLA reference | invalid |
| Task with empty or absent `entryConditions` | valid — and the task never starts |
