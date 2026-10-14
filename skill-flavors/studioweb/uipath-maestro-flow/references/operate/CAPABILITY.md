<!--skill-flavor:upload-operate-intro:start-->
Capability index for the lifecycle of a flow as a deployed asset. Operate owns everything that touches the cloud — `solution resources refresh`, `flow debug`, `process run`, `job status/traces`, and `instance` lifecycle (pause, resume, cancel, retry). Shipping runs from this CLI: publication through host-intercepted `uip solution publish`, deployment into an Orchestrator folder through `uip solution deploy run`. Only `pack`, `restore`, and `upload` are out of scope in the browser — the host packages and authenticates, and `/solution` already IS the open project so there is nothing to upload.
<!--skill-flavor:upload-operate-intro:end-->

<!--skill-flavor:upload-scope-bullets:start-->
- Publish the active solution to a feed (`uip solution publish` — packaging and auth handled by Studio Web)
- Deploy the published package into an Orchestrator folder (`uip solution deploy run`)
<!--skill-flavor:upload-scope-bullets:end-->

<!--skill-flavor:upload-refresh-rule:start-->
1. **Always run `uip solution resources refresh --solution-folder <SolutionDir>` before `flow debug`.** Stale resource declarations cause runtime binding failures even when the local `.flow` is correct. The refresh syncs connection and process resource declarations from the project's `bindings_v2.json` files into the solution. `refresh` has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.
<!--skill-flavor:upload-refresh-rule:end-->
<!--skill-flavor:upload-publish-default-rule:start-->
2. **Publish via the host-intercepted CLI; the destination is the user's choice.** For an explicit approved publish request, run `uip solution publish` for the active solution. With one destination it publishes there; with several it publishes nothing and lists them — ask the user which destination to use (personal workspace vs shared location), then rerun with `--location "<key or name>"` (or `--personal-workspace`). Skip the question when the user already named a destination. Success means the request was accepted; verify the terminal state in Studio Web's Publish history. Publishing to the personal workspace auto-deploys; publishing to a shared location never auto-deploys — finish it with `uip solution deploy run` (available in this host), or leave it as a package deliberately. See [ship.md](ship.md) for the deploy contract before the first `deploy run`: it creates a NEW folder every time and cannot install into an existing one.
<!--skill-flavor:upload-publish-default-rule:end-->

<!--skill-flavor:ship-journey-row:start-->
| Ship a flow (publish to a feed, deploy to a folder) | [ship.md](ship.md) |
<!--skill-flavor:ship-journey-row:end-->

<!--skill-flavor:ship-common-tasks-rows:start-->
| **Publish the active solution** | [ship.md — Publish](ship.md#publish--put-a-package-in-a-feed) |
| **Deploy a published package into an Orchestrator folder** | [ship.md — Deploy](ship.md#deploy--install-the-package-into-a-folder) |
| **Sync solution resource declarations** | [ship.md — Pre-flight](ship.md#pre-flight) (the `uip solution resources refresh` step) |
<!--skill-flavor:ship-common-tasks-rows:end-->

<!--skill-flavor:upload-antipatterns:start-->
- **Never report that publishing or deploying is impossible from this environment or "owned by Studio Web".** Both work from this CLI: `uip solution publish`, then `uip solution deploy run` for shared destinations. Only `pack`, `restore`, and `upload` are absent in the browser.
- **Never run `uip solution upload` here.** `/solution` already IS the open Studio Web project; the host declines the command.
<!--skill-flavor:upload-antipatterns:end-->

<!--skill-flavor:ship-reference-entry:start-->
- [ship.md](ship.md) — publish (host-intercepted, ask-first destination) and deploy (`uip solution deploy run`)
<!--skill-flavor:ship-reference-entry:end-->

<!--skill-flavor:upload-shared-cli-entry:start-->
- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `solution resources refresh`, `solution publish`, `solution deploy run`, `flow debug`, `flow process`, `flow job`, `flow instance`
<!--skill-flavor:upload-shared-cli-entry:end-->

<!--skill-flavor:upload-orchestrator-pointer:start-->
For the full deployment contract — deploy configs, activation, upgrading a deployed solution — see [/uipath:uipath-solution](/uipath:uipath-solution).
<!--skill-flavor:upload-orchestrator-pointer:end-->
