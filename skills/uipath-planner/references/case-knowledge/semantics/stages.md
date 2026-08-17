# Stages — lifecycle, secondary lanes, global events, case completion

Single source for cross-skill stage semantics. Slot/pairing facts: [facts/pairing.yaml](../facts/pairing.yaml).

**[K-STG-1] Stage lifecycle.** A stage has entry conditions (when it activates), tasks (work inside),
and exit conditions split by `marksStageComplete`: `Yes` = completion (the stage is DONE — satisfies a
downstream `selected-stage-completed`), `No` = early exit/routing (satisfies `selected-stage-exited`).
Only completion counts toward `required-stages-completed`. Destination routing lives on the DESTINATION
stage's entry condition (`selected-stage-completed("Origin")` / `selected-stage-exited("Origin")`) — one
stage fans out to N stages via their entries, not via its own exit rows (exception: K-STG-5 diverting exit).

**[K-STG-2] Secondary stage = interrupting exception lane.** A `case-management:Stage` with
`data.stageType: "secondary"` (the `ExceptionStage` node type died at v22). Use it for work that is not a
fixed step on the line — errors, escalations, rejections, rework, cancellations — reached only by
condition. Always `isRequired: false`, never counted in `required-stages-completed`, never entered by an
edge. Stage-level `Interrupting: Yes` and every entry row `Interrupting: Yes` — ONE carve-out (K-STG-3).
If the work is an optional one-off inside the current stage, keep it an `adhoc` task (K-SEQ-4), not a lane.

**[K-STG-3] The parallel-oversight carve-out.** When an `sla-status-change` entry's response is parallel
oversight — breached work keeps running, nothing paused/taken over/rerouted — the stage-level
`Interrupting` field AND that entry row both read `No`. The lane stays `secondary` + `isRequired: false`;
promoting it to a regular stage would make it required for completion. Scoped to `sla-status-change` rows
only: `wait-for-connector`, `user-selected-stage`, and diverting `selected-stage-exited` entries are always
`Yes`. `Yes` on the stage with `No` on its only entry row is a contradiction — blocking.

**[K-STG-4] Secondary exits by intent.** Returning/rework lanes complete with `return-to-origin`
(re-activates the origin; ALWAYS requires `Interrupting: Yes` — `return-to-origin` + `No` is illegal, so a
parallel-oversight lane must complete `exit-only`). Terminal lanes (Rejected/Withdrawn/Cancelled) complete
`exit-only` PLUS a root case-exit row with `marksCaseComplete: false` (K-PAIR-6). Canonical returning
shape: `return-to-origin` + `Marks Stage Complete: Yes` + `required-tasks-completed`.

**[K-STG-5] Entry shape follows the lane's trigger.**
- Person launches it → `user-selected-stage`, paired with an upstream `wait-for-user` exit (K-PAIR-4).
- External/global event → ONE `wait-for-connector` entry on the destination lane.
- SLA response entering the lane → ONE scoped `sla-status-change` entry (K-SLA-4).
- Decision/signal divert → the ORIGIN stage carries a **gated diverting exit** (`Marks Stage Complete: No`,
  WHEN `selected-tasks-completed("<decider task>")`, `IF` on the signal, `exitToStageId` → the lane) and its
  completion exit carries the INVERSE `IF` so the two are mutually exclusive; the lane's entry is
  `selected-stage-exited(origin)` + the same `IF`. Without the diverting exit the decision path dual-fires
  or deadlocks. This is divert-and-return, not a true mid-stage interrupt — a variable-driven mid-stage
  interrupt is not expressible without a connector. Only a `selected-stage-exited` lane entry needs the
  matching origin diverting exit; a `selected-stage-completed(origin)` + `IF` lane keys off the origin's
  normal completion (guard only), and connector/SLA/user entries need nothing on origins.

**[K-STG-6] Global-event normalization.** An event that can fire at any point and requires case work
(withdrawal from a portal, an SLA status change) is modeled ONCE on the destination secondary stage's
entry — never duplicated as tasks/exit rules on every primary stage. A true interrupting entry exits
whichever stage is active. Two lanes with identical entry rules (same rule + selectors + expression) are
ambiguous routing — give each a distinct selector or guard. (Design rule; not validate-enforced as of
1.198.0-preview.102 — probe p07b.)

**[K-STG-7] Reachability is condition-only** ([edges retired](edges-retired.md)): every primary stage
reachable from a trigger through entry conditions; every primary stage has a completion consumed
downstream (or feeds a lane / case-exit); every non-start entry names a concrete producer (source stage,
task, connector event, paired wait-for-user, or declared SLA). A stage with no entry condition is orphaned.

<!-- END: stages.md -->
