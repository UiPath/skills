# Task activation — sequential, parallel, event, adhoc

Single source for task activation-mode grammar. Slot legality: [facts/pairing.yaml](../facts/pairing.yaml).

**[K-SEQ-1] Task-entry mode is exclusive.** Map the product's task modes exactly: *sequential* → one
`runs-sequentially` entry rule (only rule on the task); *event-triggered* → the explicit event rule
(`wait-for-connector` with connector config, or `sla-status-change` for a start-task SLA response);
*manually-triggered* → one `adhoc` rule + `isRequired: false`; *stage-started* → `current-stage-entered`.
Never add `current-stage-entered` alongside any of the others, and never infer a mode from `data.tasks`
lane layout.

**[K-SEQ-2] Sequential normalization.** When the source states order (`then`, `after`, `before`,
`in order`, an upstream-output prerequisite) for contiguous tasks in one stage, EVERY task in the ordered
run — including the first — carries exactly one `runs-sequentially` row. The first task set's rule means
"stage entered"; each later set's rule means "previous task set completed". Structure mirrors it in
`data.tasks` (2D): strict chain = consecutive single-task sets `[[A],[B],[C]]`; independent siblings after
one predecessor share the next set `[[A],[B,C]]`, each sibling still `runs-sequentially`
(*parallel-after-predecessor*). Never author duplicate `selected-tasks-completed("<prev>")` rows for
simple next-step ordering; a missing data binding does not erase stated ordering. Break an ordered run only
at tasks that are `adhoc`, condition-gated, dependent on non-immediate siblings, or whose ENTRY rule is
`wait-for-connector` (a task merely TYPED `wait-for-connector` stays in the run).

**[K-SEQ-3] `selected-tasks-completed` is for true fan-in,** branch convergence, condition-result routing,
non-immediate dependencies, or explicit gates. It must select only non-`adhoc` tasks in the SAME stage.
For race patterns (confirmation vs timeout/cancel), arm the listener and clock while the obligation is
pending and gate downstream work on the winning fact, not on the whole parallel set completing.

**[K-SEQ-4] `adhoc` is an activation mode, not a task type.** Task-entry only — never a stage-entry rule.
An adhoc task is `isRequired: false`, user-launched from the Case App, any task type, and never selected by
`required-tasks-completed` / `selected-tasks-completed` / any required flow.

**[K-SEQ-5] A task with no entry condition never starts.** `validate` accepts `entryConditions: []` and a
missing key; the task silently emits no plan entry. Every task carries ≥ 1 entry condition.

**[K-SEQ-6] Conditional-branch stages need a required convergence task.** Mutually-exclusive conditional
tasks (one per reason code, each `current-stage-entered` + `IF`) are all `Required: No` — only one runs, so
none can be the required completer. Add ONE required convergence task whose entry is a DNF OR covering
every branch (each `selected-tasks-completed("<branch>")` row, plus a `current-stage-entered` +
inverse-guard row for the no-branch path); `required-tasks-completed` then resolves deterministically.

**[K-SEQ-7] Re-entry safety (`return-to-origin` loops).** Classify before setting `Run Only Once`:
*new attempt/resubmission* (corrected, retry, appeal) → producer/review/decision tasks stay rerunnable
(`Run Only Once: No`) and live routing variables reset or attempt-scope; *re-evaluate existing fact* →
`Run Only Once: Yes` only on producers whose prior output must persist, documenting which rule re-reads it;
*optional repeat* → `adhoc`/non-required. A stale terminal value (`SendBack`, `Rejected`) must not remain
live at re-entry unless deliberately re-evaluated.

<!-- END: sequencing.md -->
