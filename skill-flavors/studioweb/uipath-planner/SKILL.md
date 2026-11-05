<!--skill-flavor:plan-job:start-->
| `decompose` | A request spanning separate buildable projects, with no SDD | A dated plan; reviewed through plan mode, the host derives the live task list from it | [decompose-guide.md](references/decompose/decompose-guide.md) |
<!--skill-flavor:plan-job:end-->

<!--skill-flavor:plan-design-only-outputs:start-->
1. **Plan, design and specify — never author automation code yourself.** `design`, `decompose`, `author`, `extract` and `edit` write only SDD, plan and genome markdown, and the host plan authored in plan mode when a plan is reviewed; they NEVER write XAML, C#, Python, JSON, or project or scaffold files. Implementation always routes to a specialist, and every genome build to `uipath-build-from-genome`.
<!--skill-flavor:plan-design-only-outputs:end-->

<!--skill-flavor:plan-and-tasks-format-row:start-->
| `decompose`: format | [plan-and-tasks-format.md](references/shared/plan-and-tasks-format.md) — header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, plan-mode mapping, anti-hallucination rule, quality rules |
<!--skill-flavor:plan-and-tasks-format-row:end-->

<!--skill-flavor:host-tools-task-list:start-->
Studio Web has no task tools, so create no tasks: the host derives the task list from the approved plan, and the plan file records progress;
<!--skill-flavor:host-tools-task-list:end-->

<!--skill-flavor:deploy-after-build:start-->
- **Build → publish, only when asked.** The build is local and writes nothing to a tenant. Publishing the open Studio Web solution (`uip solution publish`) is the user's call: when the request asks to publish, deploy or go live, the closing summary tells the user to publish it. When Solutions (`.uipx`) are blocked for the SDD's `Delivery model` — standalone, Automation Suite older than 2.2510, or a user exclusion ([platform-availability-guide.md](references/shared/platform-availability-guide.md)) — the publish goes per package to Orchestrator through `uipath-platform`.
<!--skill-flavor:deploy-after-build:end-->
