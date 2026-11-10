<!--skill-flavor:planner-next-step:start-->
The planner detects the `## Planner Handoff` header, parses Section 2: Stages & Tasks and Section 4: Integrations, derives the per-skill task list. If `Execution autonomy: interactive`, it presents the task list for approval in plan mode, and the approved plan becomes the live task list.
<!--skill-flavor:planner-next-step:end-->
<!--skill-flavor:case-build-handoff-row:start-->
| **Build handoff** | this SDD is the build skill's contract — `uipath-maestro-case` resolves resources into `tasks/registry-resolved.json` and writes `caseplan.json` directly; the case build has no tasks file |
<!--skill-flavor:case-build-handoff-row:end-->
<!--skill-flavor:case-template-validation-row:start-->
| **Template validation** | <pending \| passed — set to passed with the ready flip. A ROW of this table, never an HTML comment or a bold line: `uipath-maestro-case` rule 2 and the eval harness both read it here> |
<!--skill-flavor:case-template-validation-row:end-->
