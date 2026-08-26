<!--skill-flavor:upload-operate-intro:start-->
Capability index for the lifecycle of a flow as a deployed asset. Operate owns everything that touches the cloud — `solution resources refresh`, `flow debug`, `process run`, `job status/traces`, and `instance` lifecycle (pause, resume, cancel, retry). Studio Web owns publication; the agent does not push or deploy solutions.
<!--skill-flavor:upload-operate-intro:end-->

<!--skill-flavor:upload-scope-bullets:start-->
<!--skill-flavor:upload-scope-bullets:end-->

<!--skill-flavor:upload-refresh-rule:start-->
1. **Always run `uip solution resources refresh --solution-folder <SolutionDir>` before `flow debug`.** Stale resource declarations cause runtime binding failures even when the local `.flow` is correct. The refresh syncs connection and process resource declarations from the project's `bindings_v2.json` files into the solution. `refresh` has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.
<!--skill-flavor:upload-refresh-rule:end-->

<!--skill-flavor:upload-publish-default-rule:start-->
2. **Publication is owned by Studio Web.** When the user asks to publish or deploy, report that the host owns publication and let them drive it from Studio Web.
<!--skill-flavor:upload-publish-default-rule:end-->

<!--skill-flavor:ship-journey-row:start-->
<!--skill-flavor:ship-journey-row:end-->

<!--skill-flavor:ship-common-tasks-rows:start-->
<!--skill-flavor:ship-common-tasks-rows:end-->

<!--skill-flavor:upload-antipatterns:start-->
<!--skill-flavor:upload-antipatterns:end-->

<!--skill-flavor:ship-reference-entry:start-->
<!--skill-flavor:ship-reference-entry:end-->

<!--skill-flavor:upload-shared-cli-entry:start-->
- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `solution resources refresh`, `flow debug`, `flow process`, `flow job`, `flow instance`
<!--skill-flavor:upload-shared-cli-entry:end-->

<!--skill-flavor:upload-orchestrator-pointer:start-->
<!--skill-flavor:upload-orchestrator-pointer:end-->
