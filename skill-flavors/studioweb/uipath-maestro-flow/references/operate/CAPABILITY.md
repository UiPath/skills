<!--skill-flavor:upload-operate-intro:start-->
Capability index for the lifecycle of a flow as a deployed asset. Operate owns everything that touches the cloud — `solution resources refresh`, `flow debug`, `process run`, `job status/traces`, and `instance` lifecycle (pause, resume, cancel, retry). Publication runs through host-intercepted `uip solution publish`; deployment stays in Studio Web (`uip solution upload` / `deploy` are unavailable in the browser).
<!--skill-flavor:upload-operate-intro:end-->

<!--skill-flavor:upload-scope-bullets:start-->
<!--skill-flavor:upload-scope-bullets:end-->

<!--skill-flavor:upload-refresh-rule:start-->
1. **Always run `uip solution resources refresh --solution-folder <SolutionDir>` before `flow debug`.** Stale resource declarations cause runtime binding failures even when the local `.flow` is correct. The refresh syncs connection and process resource declarations from the project's `bindings_v2.json` files into the solution. `refresh` has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.
<!--skill-flavor:upload-refresh-rule:end-->

<!--skill-flavor:upload-publish-default-rule:start-->
2. **Publish via the host-intercepted CLI; the destination is the user's choice.** For an explicit approved publish request, run `uip solution publish` for the active solution. With one destination it publishes there; with several it publishes nothing and lists them — ask the user which destination to use (personal workspace vs shared location), then rerun with `--location "<key or name>"` (or `--personal-workspace`). Skip the question when the user already named a destination. Success means the request was accepted; verify the terminal state in Studio Web's Publish history. Deployment stays in Studio Web — `uip solution deploy` is unavailable in the browser.
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
