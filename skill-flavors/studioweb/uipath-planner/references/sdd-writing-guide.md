<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section or a task list for implementation work. Those are owned by `plan` (task derivation). The SDD's `## Next Steps` section marks the boundary into `plan`, and that is the entire `design` output surface.
<!--skill-flavor:phase3-output-surface:end-->

<!--skill-flavor:design-deliverable:start-->
The SDD is the deliverable of `design`. **Do not generate an Implementation Plan section inside the SDD. Do not derive implementation tasks during `design`. Do not start executing.**
<!--skill-flavor:design-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin the genome or `plan` in the same turn as `design`.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue on the **next** turn with the sequence below. Rationale: `design` (read PDD + guides, author §1–§18), `author` (read the SDD, write and check the genome) and `plan` (parse SDD, derive tasks, write the tasks file) are each heavy; stacking two of them in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after each durable write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->
