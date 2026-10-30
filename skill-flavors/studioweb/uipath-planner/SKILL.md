<!--skill-flavor:plan-job:start-->
| `plan` | An SDD with the `## Planner Handoff` header or the `<!-- planner-handoff:v1 -->` marker | `<process>-tasks.md`; a plan the user reviews goes through Studio Web's plan mode (`EnterPlanMode` → `ExitPlanMode`), and the host derives the live task list from the approved plan | [plan-guide.md](references/plan-guide.md) |
| `decompose` | A request spanning separate buildable projects, with no SDD | A dated plan; reviewed through plan mode, the host derives the live task list from it | [decompose-guide.md](references/decompose-guide.md) |
<!--skill-flavor:plan-job:end-->

<!--skill-flavor:plan-design-only-outputs:start-->
1. **Plan, design and specify — never author automation code yourself.** `design`, `plan`, `decompose`, `author`, `extract` and `edit` write only SDD, plan/tasks and genome markdown, and the host plan authored in plan mode when a plan is reviewed; they NEVER write XAML, C#, Python, JSON, or project or scaffold files. Implementation always routes to a specialist, and every genome build to `uipath-genome-builder`.
<!--skill-flavor:plan-design-only-outputs:end-->

<!--skill-flavor:plan-and-tasks-format-row:start-->
| `plan`, `decompose`: format | [plan-and-tasks-format.md](references/plan-and-tasks-format.md) — header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, plan-mode mapping, anti-hallucination rule, quality rules |
<!--skill-flavor:plan-and-tasks-format-row:end-->
