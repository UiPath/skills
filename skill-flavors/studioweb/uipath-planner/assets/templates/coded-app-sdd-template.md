<!--skill-flavor:planner-next-step:start-->
The planner detects the `## Planner Handoff` header, parses §10 Project Structure and §9 Integrated Components, derives the per-skill task list (routing each task to `uipath-coded-apps`, `uipath-platform`, etc.), writes `<APP_NAME_KEBAB>-tasks.md` alongside this SDD. If `Execution autonomy: interactive`, it presents the task list for approval in plan mode, and the approved plan becomes the live task list.
<!--skill-flavor:planner-next-step:end-->
