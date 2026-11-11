<!--skill-flavor:bpmn-hitl-touchpoints:start-->
<!-- Flag userTask nodes. Authored INLINE by uipath-maestro-bpmn (Actions.HITL on bpmn:UserTask) — do NOT route
     to uipath-human-in-the-loop, which does not support .bpmn hosts. Record business intent only (who approves,
     what criteria); the BPMN specialist owns the task schema. -->
<!--skill-flavor:bpmn-hitl-touchpoints:end-->
<!--skill-flavor:bpmn-project-structure:start-->
<!-- Editable source layout per the owning skill: the .bpmn basename matches the project directory exactly.
     bindings_v2.json, entry-points.json, operate.json, package-descriptor.json are generated/CLI-managed
     package metadata — never scaffolded by hand. -->

```text
<BPMN_PROJECT_NAME>/
├── <BPMN_PROJECT_NAME>.bpmn
└── project.uiproj
```
<!--skill-flavor:bpmn-project-structure:end-->
<!--skill-flavor:planner-next-step:start-->
The planner detects the `## Planner Handoff` header, parses §4 Activities Inventory and §9 Integrated Components, derives the per-skill task list (routing each task to `uipath-maestro-bpmn`, `uipath-rpa`, `uipath-agents`, `uipath-api-workflow`, `uipath-platform`, etc. — userTask/HITL nodes stay inline with `uipath-maestro-bpmn`), writes `<PROCESS_NAME_KEBAB>-tasks.md` alongside this SDD. If `Execution autonomy: interactive`, it presents the task list for approval in plan mode, and the approved plan becomes the live task list.
<!--skill-flavor:planner-next-step:end-->
