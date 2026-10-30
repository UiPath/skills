<!--skill-flavor:progress-tasks:start-->
Studio Web has no task-creation tool, so `design` creates no progress tasks: skip this step and every `> **Progress:**` line in this guide.

**Rule G-9 — the disk write is never last.** The order those lines describe still holds: [Phase 3 Step 0](#step-0-write-the-sdd-skeleton-to-disk--hard-gate) is a hard gate, so the SDD skeleton must be on disk before you generate a single Phase 3 section. Do NOT defer every write to the end. A long autonomous turn can be hard-killed by the per-turn watchdog mid-generation; a run that defers the only deliverable to its final write loses everything, while a skeleton already on disk leaves a detectable, gradeable `Status: draft` SDD.

Implementation tasks are owned by `plan` (task derivation), which runs after `design` writes the SDD — do NOT plan implementation tasks here.
<!--skill-flavor:progress-tasks:end-->

<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section or a task list for implementation work. Those are owned by `plan` (task derivation). The SDD's `## Next Steps` section marks the boundary into `plan`, and that is the entire `design` output surface.
<!--skill-flavor:phase3-output-surface:end-->

<!--skill-flavor:design-deliverable:start-->
The SDD is the deliverable of `design`. **Do not generate an Implementation Plan section inside the SDD. Do not derive implementation tasks during `design`. Do not start executing.**
<!--skill-flavor:design-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin `plan` in the same turn as `design`.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue into `plan` on the **next** turn. Rationale: `design` (read PDD + guides, author §1–§18) and `plan` (parse SDD, derive tasks, write the tasks file) are each heavy; stacking both in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after a durable SDD write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->

<!--skill-flavor:sdd-no-task-lists:start-->
2. **The SDD is architecture only — no task lists.** `design` produces the SDD (Project Structure, Data Definitions, Testing Strategy, …). Task derivation is `plan`'s job. Never put Task 1 / Task N templates or implementation tasks in the SDD. End the SDD with a `## Next Steps` section.
<!--skill-flavor:sdd-no-task-lists:end-->

<!--skill-flavor:solution-terminal-artifact:start-->
6. **In Studio Web the deliverable is the open solution.** The SDD's `## Next Steps` section tells the user each project is created inside the open Studio Web solution (`uip <family> init <ProjectName>` per project); there is no solution to create and no packing step. Plan each project by what Studio Web supports for its type: flow, case, agent, api-workflow and bpmn projects are created, built, run and debugged end to end here; an rpa project is created and run here, but its workflows are authored in the Studio Web designer or Studio Desktop, so its build tasks go to the user; function and coded-app projects cannot be created here — their existing files can be edited, but scaffolding, running and deploying go to the user's local CLI. Exception: when the Constraint Gate blocks Solutions for the delivery model — standalone, Automation Suite older than 2.2510, or a user exclusion — rewrite Next Steps to per-package Orchestrator publish routed via `uipath-platform`.
<!--skill-flavor:solution-terminal-artifact:end-->
