<!--skill-flavor:planner-next-step:start-->
The planner detects the `## Planner Handoff` header, parses the project structure, derives the per-skill task list (routing each task to `uipath-agents`, `uipath-rpa`, `uipath-platform`, etc.), writes `<AGENT_NAME_KEBAB>-tasks.md` alongside this SDD. If `Execution autonomy: interactive`, it presents the task list for approval in plan mode, and the approved plan becomes the live task list.
<!--skill-flavor:planner-next-step:end-->
