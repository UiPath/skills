<!--skill-flavor:sw-eval-ref-intro:start-->
Complete syntax reference for every subcommand under `uip maestro flow eval`. All commands accept the global flags `--output <table|json|yaml|plain>` (default `json`), `--output-filter <jmespath>`, `--log-level <debug|info|warn|error>`, and `--log-file <path>` (point it at `/tmp/…` — files written under `/solution` cannot be deleted). Repeated reminders below: always pass `--output json` when an agent will parse the result. Every `run` subcommand additionally needs `--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>` from the context and should be called with `timeoutSeconds: 120`, never `--wait`.
<!--skill-flavor:sw-eval-ref-intro:end-->

<!--skill-flavor:sw-eval-common-options:start-->
| `--path <path>` | **Yes in Studio Web** | The Flow project directory, `/solution/<Project>` (`CurrentProject.AbsolutePath`). The shell's cwd `/solution` is the solution root, not a project, so `.` never works here |
<!--skill-flavor:sw-eval-common-options:end-->

<!--skill-flavor:sw-eval-add-example:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-add-example:end-->

<!--skill-flavor:sw-eval-list-example:start-->
uip maestro flow eval list --set "Smoke Tests" --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-list-example:end-->

<!--skill-flavor:sw-eval-simulation-add-examples:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-add-examples:end-->

<!--skill-flavor:sw-eval-simulation-add-examples-2:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-add-examples-2:end-->

<!--skill-flavor:sw-eval-simulation-add-examples-3:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-add-examples-3:end-->

<!--skill-flavor:sw-eval-simulation-add-examples-4:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-add-examples-4:end-->

<!--skill-flavor:sw-eval-simulation-list-examples:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-list-examples:end-->

<!--skill-flavor:sw-eval-simulation-list-examples-2:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-list-examples-2:end-->

<!--skill-flavor:sw-eval-simulation-remove-examples:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-remove-examples:end-->

<!--skill-flavor:sw-eval-simulation-remove-examples-2:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-simulation-remove-examples-2:end-->

<!--skill-flavor:upload-safety-run-start-prereq:start-->
Start a Studio Web evaluation run against the open solution — Studio Web owns it, so nothing needs uploading first. `eval run *` works from the Studio Web shell only when both ids are passed explicitly (`--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>`; there is no `.uipx`/`SolutionStorage.json` to resolve them from) and it can hang on first use: call it with `timeoutSeconds: 120`, never with `--wait`, and if the call times out (exit 124) hand the run to the user via the Studio Web Evaluations panel instead of retrying in a loop. Poll `eval run status` for progress.
<!--skill-flavor:upload-safety-run-start-prereq:end-->

<!--skill-flavor:sw-eval-run-start-options:start-->
| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--set <name>` | Yes | Eval set name or ID | — |
| `--solution-id <id>` | **Yes in Studio Web** | `CurrentSolution.SolutionId` from the context; nothing on disk to auto-resolve from | — |
| `--project-id <id>` | **Yes in Studio Web** | `CurrentProject.ProjectId` from the context | — |
| `--path <path>` | Yes | `/solution/<Project>` (see Common Options) | — |
| `--entry-point <entry>` | No | Flow entry point path or start node ID | Eval set's `selectedEntrypoint` |
| `--folder-key <key>` | No | Orchestrator folder key | Personal workspace |
| `--debug-mode <mode>` | No | Studio Web debug mode override | (server default) |
| `--wait` | No | Block until terminal state, then print results. Avoid here: the shell tool stops at 180 s by default, 600 s at most | `false` |
| `--timeout <seconds>` | No | Max time to block on `--wait` — not used here; the 120 s budget is the shell call's `timeoutSeconds` | `600` (10 min) |

Without `--wait`, returns immediately with `EvalSetRunId` — the form to use here; poll with `eval run status`. With `--wait`, the CLI polls until `Completed` or `Failed`, or `--timeout` elapses (the server-side run continues regardless).
<!--skill-flavor:sw-eval-run-start-options:end-->

<!--skill-flavor:sw-eval-run-status-options:start-->
| `--solution-id <id>` | Yes in Studio Web | `CurrentSolution.SolutionId` from the context |
| `--project-id <id>` | Yes in Studio Web | `CurrentProject.ProjectId` from the context |
| `--path <path>` | Yes | `/solution/<Project>` (see Common Options) |
<!--skill-flavor:sw-eval-run-status-options:end-->

<!--skill-flavor:sw-eval-run-results-options:start-->
| `--export-format <json\|csv>` | No | Write results to a file in the project folder — files under `/solution` cannot be deleted; prefer plain `--output json` and keep the data in the response |
| `--solution-id`, `--project-id`, `--path` | Yes in Studio Web | (see start) |
<!--skill-flavor:sw-eval-run-results-options:end-->

<!--skill-flavor:sw-eval-run-list-example:start-->
uip maestro flow eval run list --set "Smoke Tests" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json
<!--skill-flavor:sw-eval-run-list-example:end-->

<!--skill-flavor:sw-eval-run-compare-options:start-->
| `--solution-id`, `--project-id`, `--path` | Yes in Studio Web | (see start) |
<!--skill-flavor:sw-eval-run-compare-options:end-->
