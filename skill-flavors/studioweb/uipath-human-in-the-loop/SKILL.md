<!--skill-flavor:case-sdk-surface-row:start-->
| `caseplan.case` (any `*.json` or `*.case` whose `nodes[]` carry `data.parentElement.type: "case-management:root"` — the marker is per-node; there is no `root` node on disk) | **Case** | Write `action` task into stage — see [hitl-casetask-action.md](references/hitl-casetask-action.md) |
<!--skill-flavor:case-sdk-surface-row:end-->
<!--skill-flavor:case-sdk-hitl-stop:start-->
<!--skill-flavor:case-sdk-hitl-stop:end-->
<!--skill-flavor:flow-project-creation:start-->
**If no `.flow` file exists and the surface is Flow**, create the Flow project with the `CreateProjects` tool.
<!--skill-flavor:flow-project-creation:end-->
