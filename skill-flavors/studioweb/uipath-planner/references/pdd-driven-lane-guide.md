<!--skill-flavor:resume-continue:start-->
- **Choice 1:** read the existing tasks.md → continue from its first task not marked `[x]`; the file's checkboxes are the task state → no SDD re-parsing needed → done.
<!--skill-flavor:resume-continue:end-->

<!--skill-flavor:plan-mode-review:start-->
If `Execution autonomy: interactive`, review the task list in Studio Web's plan mode:

1. Call `EnterPlan`. The host names the plan file paths and attaches its plan-authoring contract.
2. Author the host plan from the tasks.md written in Step 7 — one plan step per task row, mapped per [plan-and-tasks-format.md → Plan-mode integration](plan-and-tasks-format.md#plan-mode-integration). While plan mode is active, the only files you may write are the host's two plan files.
3. Call `ExitPlan` with outcome `complete`. The user approves or rejects the plan on the host's review card.

- Approval exits plan mode, and the host derives the task list from the approved plan → Step 9.
- A rejection or change request keeps plan mode active: revise the host plan and call `ExitPlan` again. If the user asks to stop planning, call `ExitPlan` with outcome `abandon`.
- If the review changed any task, update tasks.md to match after approval, before the first task starts — it stays the durable record.
<!--skill-flavor:plan-mode-review:end-->

<!--skill-flavor:defaulted-fields-review:start-->
In `Execution autonomy: interactive` mode, put the same "Defaulted handoff fields" block (when applicable) in the host plan's first section so the reviewer sees it at approval time.
<!--skill-flavor:defaulted-fields-review:end-->

<!--skill-flavor:live-tasks-and-handoff:start-->
## Step 9 — Live tasks

Studio Web has no task-creation tool — create no tasks yourself. In `interactive` mode the host derived the task list from the plan approved in Step 8. In `autonomous` mode there is no live task list: the tasks.md rows are the task list.

## Step 10 — Hand off

The planner's job is done. The main agent walks the tasks in dependency order — the host's task list (interactive) or the tasks.md rows (autonomous) — loading the appropriate specialist for each. As tasks complete, the corresponding checkbox in tasks.md is refreshed (`[ ]` → `[~]` → `[x]`) so that future sessions see current state.

> Implementation note: keeping tasks.md in sync lives in the main agent's session loop, not in this skill. This skill writes the file once and trusts the agent to keep it in sync. On next entry to Lane A, the planner re-reads the file and proceeds.
<!--skill-flavor:live-tasks-and-handoff:end-->

<!--skill-flavor:budget-first-run:start-->
| First run, no UI apps in §9 | **0** (plan-mode review uses `EnterPlan` / `ExitPlan`, not AskUserQuestion) |
<!--skill-flavor:budget-first-run:end-->
