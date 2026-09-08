<!--skill-flavor:upload-operate-intro:start-->
Capability index for the lifecycle of a flow as a deployed asset. Operate owns everything that touches the cloud — `uip flow debug`, `process run`, `job status/traces`, and `instance` lifecycle (pause, resume, cancel, retry). Publication runs through host-intercepted `uip solution publish`; deployment stays in Studio Web (`uip solution upload` / `deploy` are unavailable in the browser). Authentication is injected by the host on every `uip` call — never run `uip login`, `uip login status`, `uip logout`, `uip auth` or `uip config`; a 401/403 means the signed-in user lacks rights on the tenant or folder — report it, do not retry.
<!--skill-flavor:upload-operate-intro:end-->

<!--skill-flavor:upload-scope-bullets:start-->
- Run a flow end-to-end via `uip flow debug` (real execution of the saved open project, with real side effects)
- Trigger a deployed process via `uip maestro flow process run`
- Check job status or stream traces with `uip maestro flow job status` / `job traces`
- Manage a running instance — pause, resume, cancel, or retry
<!--skill-flavor:upload-scope-bullets:end-->

<!--skill-flavor:upload-refresh-rule:start-->
1. **Debug through the host.** `uip flow debug` runs the saved open project; there is no pack, upload, or refresh step. `uip solution resources refresh` is unavailable in Studio Web (it needs a local `.uipx` and fails with `not a UiPath solution`). When a run faults on a connection or process binding, re-run `uip maestro flow node configure` for that node and check the solution's Resources panel with `uip solution resources list --kind <Kind> --output json` / `uip solution resources add`.
<!--skill-flavor:upload-refresh-rule:end-->

<!--skill-flavor:upload-publish-default-rule:start-->
2. **Publish via the host-intercepted CLI; the destination is the user's choice.** `uip solution publish --help` lists `PublishLocations` (name, key, `IsPersonalWorkspace`, `Default`). Ask the user which destination when more than one exists and none was named, then run `uip solution publish --location "<key or name>"` (add `--personal-workspace` for that choice; optional `--version`, `--description`, `--release-notes`). Never run it without `--location` unless the user chose the personal workspace: with no flag the host publishes to the personal workspace immediately and without a second confirmation. No output state confirms deployment — confirm with `uip or packages versions <name> --folder-path <path>`. `uip solution upload` / `deploy` are refused in Studio Web and `uip flow pack` is an intercepted no-op (the three-token `uip maestro flow pack` reaches the bundle and fails); publishing packages server-side.
<!--skill-flavor:upload-publish-default-rule:end-->

<!--skill-flavor:debug-summary-rule:start-->
4. **Always report the status line and the `Trace ID:` as the first two lines of any debug summary.** `uip flow debug` prints plain text: line 1 is the status (`Successful`, `Faulted`, `Failed`, `TimedOut after 300s`), then `Trace ID: <id>` when the host determined one. Write `Trace ID: <not returned>` when the line is absent — never omit the line. The Trace ID is the job key for `uip maestro flow job status|traces <TRACE_ID>`. No URL is returned — the user is already in the designer.
<!--skill-flavor:debug-summary-rule:end-->

<!--skill-flavor:ship-journey-row:start-->
| Journey | Read |
| --- | --- |
| Run a flow on demand or check progress | [run.md](run.md) |
| Intervene in a running instance | [manage.md](manage.md) |
<!--skill-flavor:ship-journey-row:end-->

<!--skill-flavor:ship-common-tasks-rows:start-->
| I need to... | Read these |
| --- | --- |
| **Debug a flow end-to-end** | [run.md — Debug](run.md#debug--controlled-end-to-end-run) |
| **Pass input arguments to `flow debug`** | [run.md — Debug](run.md#debug--controlled-end-to-end-run) (the `--inputs` flag) |
| **Bind local files to file-typed inputs** | Not possible from `uip flow debug` in Studio Web (`--attachment` is ignored). For deployed processes see [run.md — Process run](run.md#process-run--trigger-a-deployed-process) (`--attachment <variableId>=<localPath>`, repeatable; overrides `--inputs` on key collisions) |
| **Trigger a deployed process** | [run.md — Process run](run.md#process-run--trigger-a-deployed-process) |
| **Check status of a running job** | [run.md — Job inspection](run.md#job-inspection--status-and-traces) |
| **Stream verbose execution traces** | [run.md — Job inspection](run.md#job-inspection--status-and-traces) (use sparingly — see [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md)) |
| **Pause a running instance** | [manage.md](manage.md) |
| **Resume a paused instance** | [manage.md](manage.md) |
| **Cancel an instance** | [manage.md](manage.md) |
| **Retry a faulted instance** | [manage.md](manage.md) (after diagnosing root cause via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md)) |
| **Look up `flow debug` / `process` / `job` / `instance` CLI syntax** | [shared/cli-commands.md](../shared/cli-commands.md) |
| **My flow run failed** | [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |
<!--skill-flavor:ship-common-tasks-rows:end-->

<!--skill-flavor:upload-antipatterns:start-->
- **Never run `flow debug` as a validation step, and never re-run a completed one to reshape its output.** Each run executes the flow again for real against real systems (nothing is uploaded); extract report fields from the text the completed run already returned, and when that run faulted, read the cause from it first — see [diagnose/troubleshooting-guide.md — Step 0](../diagnose/troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have). Use `uip maestro flow validate` for correctness checking.
<!--skill-flavor:upload-antipatterns:end-->

<!--skill-flavor:ship-reference-entry:start-->
<!--skill-flavor:ship-reference-entry:end-->

<!--skill-flavor:upload-shared-cli-entry:start-->
- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `uip flow debug`, `flow process`, `flow job`, `flow instance`
<!--skill-flavor:upload-shared-cli-entry:end-->

<!--skill-flavor:conventions-reference-entry:start-->
- [shared/cli-conventions.md](../shared/cli-conventions.md) — FOLDER_KEY, JSON output shape
<!--skill-flavor:conventions-reference-entry:end-->

<!--skill-flavor:upload-orchestrator-pointer:start-->
<!--skill-flavor:upload-orchestrator-pointer:end-->
