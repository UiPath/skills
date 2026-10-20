<!--skill-flavor:progress-tasks:start-->
Studio Web has no task-creation tool, so Phase D creates no progress tasks: skip this step and every `> **Progress:**` line in this guide.

**Rule G-9 — the disk write is never last.** The order those lines describe still holds: [Phase 3 Step 0](#step-0-write-the-sdd-skeleton-to-disk--hard-gate) is a hard gate, so the SDD skeleton must be on disk before you generate a single Phase 3 section. Do NOT defer every write to the end. A long autonomous turn can be hard-killed by the per-turn watchdog mid-generation; a run that defers the only deliverable to its final write loses everything, while a skeleton already on disk leaves a detectable, gradeable `Status: draft` SDD.

Implementation tasks are owned by Lane A (task derivation), which runs after Phase D writes the SDD — do NOT plan implementation tasks here.
<!--skill-flavor:progress-tasks:end-->

<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section or a task list for implementation work. Those are owned by Lane A (task derivation). The SDD's `## Next Steps` section marks the boundary into Lane A, and that is the entire Phase D output surface.
<!--skill-flavor:phase3-output-surface:end-->

<!--skill-flavor:phase-d-deliverable:start-->
The SDD is the deliverable of Phase D. **Do not generate an Implementation Plan section inside the SDD. Do not derive implementation tasks during Phase D. Do not start executing.**
<!--skill-flavor:phase-d-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin Lane A in the same turn as Phase D.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue into Lane A on the **next** turn. Rationale: Phase D (read PDD + guides, author §1–§18) and Lane A (parse SDD, derive tasks, write the tasks file) are each heavy; stacking both in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after a durable SDD write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->
