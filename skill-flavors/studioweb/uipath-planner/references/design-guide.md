<!--skill-flavor:progress-tasks:start-->
Studio Web has no task-creation tool, so `design` creates no progress tasks: skip this step and every `> **Progress:**` line in this guide.

**Rule G-9 — the disk write is never last.** The order those lines describe still holds: [Phase 3 Step 0](sdd-writing-guide.md#step-0-write-the-sdd-skeleton-to-disk--hard-gate) is a hard gate, so the SDD skeleton must be on disk before you generate a single Phase 3 section. Do NOT defer every write to the end. A long autonomous turn can be hard-killed by the per-turn watchdog mid-generation; a run that defers the only deliverable to its final write loses everything, while a skeleton already on disk leaves a detectable, gradeable `Status: draft` SDD.

Implementation tasks are owned by `plan` (task derivation), which runs after `design` writes the SDD and its genome (the genome is written from the `ready` SDD on the next turn) — do NOT plan implementation tasks here.
<!--skill-flavor:progress-tasks:end-->

<!--skill-flavor:sdd-no-task-lists:start-->
2. **The SDD is architecture only — no task lists.** `design` produces the SDD (Project Structure, Data Definitions, Testing Strategy, …). Task derivation is `plan`'s job. Never put Task 1 / Task N templates or implementation tasks in the SDD. End the SDD with a `## Next Steps` section.
<!--skill-flavor:sdd-no-task-lists:end-->

<!--skill-flavor:solution-terminal-artifact:start-->
6. **In Studio Web the deliverable is the open solution.** The SDD's `## Next Steps` section tells the user each project is created inside the open Studio Web solution (`uip <family> init <ProjectName>` per project); there is no solution to create and no packing step. Plan each project by what Studio Web supports for its type: flow, case, agent, api-workflow and bpmn projects are created, built, run and debugged end to end here; an rpa project is created and run here, but its workflows are authored in the Studio Web designer or Studio Desktop, so its build tasks go to the user; function and coded-app projects cannot be created here — their existing files can be edited, but scaffolding, running and deploying go to the user's local CLI. Exception: when the Constraint Gate blocks Solutions for the delivery model — standalone, Automation Suite older than 2.2510, or a user exclusion — rewrite Next Steps to per-package Orchestrator publish routed via `uipath-platform`.
<!--skill-flavor:solution-terminal-artifact:end-->
