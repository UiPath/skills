<!--skill-flavor:planner-next-step:start-->
The planner detects the `## Planner Handoff` header, parses §3 Nodes Inventory and §7 Integrated Components, derives the per-skill task list (routing each task to `uipath-maestro-flow`, `uipath-rpa`, `uipath-agents`, `uipath-platform`, `uipath-human-in-the-loop`, etc.), writes `<FLOW_NAME_KEBAB>-tasks.md` alongside this SDD. If `Execution autonomy: interactive`, it presents the task list for approval in plan mode, and the approved plan becomes the live task list.
<!--skill-flavor:planner-next-step:end-->
