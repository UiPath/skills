<!--skill-flavor:single-skill-exit-no-plan:start-->
1. Do NOT write a plan file. Do NOT call `EnterPlan`. Do NOT ask the Step 3 batch.
<!--skill-flavor:single-skill-exit-no-plan:end-->

<!--skill-flavor:approach-behavior:start-->
**If "explore first, then plan":**
- Call `EnterPlan` as soon as the user picks this option — before any further discovery, the Step 4 UI batch, or any plan writing. The host then names the plan file paths and attaches its plan-authoring contract.
- Inside plan mode, run only non-mutating discovery: reading `project.json` and other project files, `uip` commands that only list or read.
- Do NOT run commands that mutate the project (create files, register targets, install packages) — those belong to execution. While plan mode is active, the only files you may write are the host's two plan files.
- Run Step 4 inside plan mode, author the plan per Step 5, then present it per Step 6 (`ExitPlan`).

**If "explore, plan, and execute simultaneously":**
- Emit the plan as text in Step 5. The main agent loads the first specialist skill immediately and follows that skill's own workflow.
- Do NOT call `EnterPlan`.
<!--skill-flavor:approach-behavior:end-->

<!--skill-flavor:write-plan-target:start-->
Compose the plan per the schema in [plan-and-tasks-format.md → Non-PDD lane](plan-and-tasks-format.md#non-pdd-lane-featuremd). Plan body holds the task list with the same task row schema as Lane A. Where it goes depends on Q1:

- **Explore first, then plan:** author it inside plan mode as the host plan — at the paths the plan-mode context names, in the format its plan-authoring contract sets, mapped per [plan-and-tasks-format.md → Plan-mode integration](plan-and-tasks-format.md#plan-mode-integration). Do NOT write `<feature>.md` or anything under `docs/plans/`; skip Save location below.
- **Explore, plan, and execute simultaneously:** write `<feature>.md` per Save location below. **Every task's Skill prompt embeds the plan path** — the exact relative or absolute path of that file (mirroring Lane A's embedded SDD path); a bare "this plan" leaves a resumed task with no way to find its values.
<!--skill-flavor:write-plan-target:end-->

<!--skill-flavor:self-review-plan-path:start-->
6. **Plan reference present** — every Skill prompt names the plan file path (simultaneous) or the approved plan (explore-first), never "this plan".
<!--skill-flavor:self-review-plan-path:end-->

<!--skill-flavor:save-location-scope:start-->
Simultaneous approach only (an explore-first plan lives in the host plan files) — save as `YYYY-MM-DD-<feature-name>.md`:
<!--skill-flavor:save-location-scope:end-->

<!--skill-flavor:resume-choices:start-->
Option 1: read the existing plan → continue from its first task not marked `[x]`; the file's checkboxes are the task state → done.
Option 2: parse the request fresh, run identity-matching against the old file (preserve completed work), write the new plan, then present it per Step 6. Same regenerate algorithm as Lane A — see [plan-and-tasks-format.md → Regenerate logic](plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).
<!--skill-flavor:resume-choices:end-->

<!--skill-flavor:present-plan:start-->
- **Explore first, then plan:** plan mode is already active (entered when the user picked this option). Once the host plan and its HTML presentation are written, call `ExitPlan` with outcome `complete`. Approval exits plan mode, the host derives the task list from the approved plan, and execution starts. A rejection keeps plan mode active: revise the plan and call `ExitPlan` again. If the user asks to stop planning, call `ExitPlan` with outcome `abandon`. Create no tasks yourself — Studio Web has no task-creation tool.
- **Explore, plan, and execute simultaneously:** emit the plan as text. The main agent starts executing the first task right away.
<!--skill-flavor:present-plan:end-->
