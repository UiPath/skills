<!--skill-flavor:plan-job:start-->
2. **Plan** — derive the per-skill task list from an SDD (or a non-PDD request) and route to specialists. A plan the user reviews goes through Studio Web's plan mode (`EnterPlanMode` → `ExitPlanMode`); the host derives the live task list from the approved plan.
<!--skill-flavor:plan-job:end-->

<!--skill-flavor:plan-design-only-outputs:start-->
1. **Plan & design only — never author automation code.** Outputs: SDD markdown (Phase D), plan/tasks markdown (Lanes A/B), and the host plan authored in plan mode when the plan is reviewed. NEVER write XAML, C#, Python, JSON, or project/scaffold files. Implementation always routes to a specialist. (SDD/plan authoring is the *only* file authoring this skill does.)
<!--skill-flavor:plan-design-only-outputs:end-->

<!--skill-flavor:sdd-no-task-lists:start-->
4. **The SDD is architecture only — no task lists.** Phase D produces the SDD (Project Structure, Data Definitions, Testing Strategy, …). Task derivation is Lane A's job. Never put Task 1 / Task N templates or implementation tasks in the SDD. End the SDD with a `## Next Steps` section.
<!--skill-flavor:sdd-no-task-lists:end-->

<!--skill-flavor:solution-terminal-artifact:start-->
11. **In Studio Web the deliverable is the open solution.** The SDD's `## Next Steps` section tells the user each project is created inside the open Studio Web solution (`uip <family> init <ProjectName>` per project); there is no solution to create and no packing step. Plan each project by what Studio Web supports for its type: flow, case, agent, api-workflow and bpmn projects are created, built, run and debugged end to end here; an rpa project is created and run here, but its workflows are authored in the Studio Web designer or Studio Desktop, so its build tasks go to the user; function and coded-app projects cannot be created here — their existing files can be edited, but scaffolding, running and deploying go to the user's local CLI. Exception: when the Constraint Gate blocks Solutions for the delivery model — standalone, Automation Suite older than 2.2510, or a user exclusion — rewrite Next Steps to per-package Orchestrator publish routed via `uipath-platform`.
<!--skill-flavor:solution-terminal-artifact:end-->

<!--skill-flavor:lane-a-review-handoff:start-->
6. If `Execution autonomy: interactive` → review in plan mode: `EnterPlanMode`, author the host plan from `<process>-tasks.md`, then `ExitPlanMode` for approval; the host derives the task list from the approved plan. If `autonomous` → no review; the tasks file is the task list.
7. Hand off. Studio Web has no task-creation tool — create no tasks yourself.
<!--skill-flavor:lane-a-review-handoff:end-->

<!--skill-flavor:lane-b-write-and-present:start-->
5. Explore-first → call `EnterPlanMode` as soon as the user picks it, before any further discovery or the Step 4 UI batch. Discover read-only inside plan mode, author the plan where and how the plan-mode context says (not `docs/plans/`), then call `ExitPlanMode` for approval. Nothing changes in the project before approval; the host derives the task list from the approved plan.
6. Simultaneous → write `YYYY-MM-DD-<feature>.md` to `docs/plans/` (project) or `./plans/` (no project), every task prompt embedding the plan path; emit the plan as text and start the first task.
<!--skill-flavor:lane-b-write-and-present:end-->

<!--skill-flavor:plan-and-tasks-format-row:start-->
| [Plan and Tasks Format](references/plan-and-tasks-format.md) | Header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, plan-mode mapping, anti-hallucination rule, quality rules |
<!--skill-flavor:plan-and-tasks-format-row:end-->
