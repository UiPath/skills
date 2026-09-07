<!--skill-flavor:sw-eval-run-intro:start-->
`uip maestro flow eval run *` — start, monitor, inspect, and compare evaluation runs. Authentication is injected by the host (no `uip login`) and the runs target the open solution. `eval run *` works from the Studio Web shell only when both ids are passed explicitly (`--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>`; there is no `.uipx`/`SolutionStorage.json` to resolve them from) and it can hang on first use: call it with `timeoutSeconds: 120`, never with `--wait`, and if the call times out (exit 124) hand the run to the user via the Studio Web Evaluations panel instead of retrying in a loop. Poll `eval run status` for progress.
<!--skill-flavor:sw-eval-run-intro:end-->

<!--skill-flavor:upload-safety-guide-gate:start-->
> **Before running any of these:** have the ids from the context ready and pass `--path /solution/<Project>` — Studio Web owns the solution, so there is no upload or "solution must be in Studio Web" step.
<!--skill-flavor:upload-safety-guide-gate:end-->

<!--skill-flavor:sw-eval-run-start-syntax:start-->
```bash
# Call with timeoutSeconds: 120; never --wait
uip maestro flow eval run start \
  --set "<set_name>" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> \
  --project-id <CurrentProject.ProjectId> \
  [--entry-point <entry>] \
  [--folder-key <key>] \
  [--debug-mode <mode>] \
  --output json
```
<!--skill-flavor:sw-eval-run-start-syntax:end-->

<!--skill-flavor:sw-eval-id-resolution:start-->
### `--solution-id` / `--project-id` in Studio Web

The CLI normally auto-resolves these from `SolutionStorage.json` and the parent `.uipx`. Neither exists in Studio Web (the solution is a backend entity), so auto-resolution can never succeed here: always pass both ids from the context — `--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>`.

If a run command still errors with both ids passed, report it as a host gap with the exact error — never guess or invent ids. If it times out instead (exit 124), hand the run to the user's Evaluations panel rather than retrying in a loop.
<!--skill-flavor:sw-eval-id-resolution:end-->

<!--skill-flavor:sw-eval-wait-timeout:start-->
Without `--wait`, the command returns immediately with `EvalSetRunId` — the only form to use here. With `--wait`, the CLI blocks until the run reaches a terminal state (`Completed` or `Failed`) or `--timeout` elapses; its default of 600 s is the shell tool's maximum (a call stops at 180 s by default), so a blocked start is cut off before the run finishes. Call every run command with `timeoutSeconds: 120` instead.

The server-side run continues regardless of what the shell call did. Query progress with:

```bash
uip maestro flow eval run status <eval_set_run_id> \
  --set "<set_name>" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json
```

Poll in separate calls; polling cadence is not part of the public CLI contract — do not depend on a specific interval.
<!--skill-flavor:sw-eval-wait-timeout:end-->

<!--skill-flavor:sw-eval-run-status-syntax:start-->
```bash
uip maestro flow eval run status <eval_set_run_id> \
  --set "<set_name>" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json
```
<!--skill-flavor:sw-eval-run-status-syntax:end-->

<!--skill-flavor:sw-eval-run-results-syntax:start-->
```bash
uip maestro flow eval run results <eval_set_run_id> \
  --set "<set_name>" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  [--only-failed] \
  [--verbose] \
  --output json
```
<!--skill-flavor:sw-eval-run-results-syntax:end-->

<!--skill-flavor:sw-eval-export-format-note:start-->
Writes results to a file in the project folder (e.g., `eval-results-<timestamp>.json` or `.csv`). Files under `/solution` cannot be deleted, so prefer plain `--output json` (optionally with `--output-filter`) and keep the results in the response; use `--export-format` only when the user wants the file kept in the project.
<!--skill-flavor:sw-eval-export-format-note:end-->

<!--skill-flavor:sw-eval-output-filter-examples:start-->
```bash
# Show only data points named "checkout-flow"
uip maestro flow eval run results <run_id> \
  --set "Smoke Tests" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json \
  --output-filter 'Data.Results[?DataPoint==`checkout-flow`]'

# Show only score and name per row
uip maestro flow eval run results <run_id> \
  --set "Smoke Tests" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json \
  --output-filter 'Data.Results[*].{name: DataPoint, score: Score}'
```
<!--skill-flavor:sw-eval-output-filter-examples:end-->

<!--skill-flavor:sw-eval-run-list-syntax:start-->
```bash
uip maestro flow eval run list \
  --set "<set_name>" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json
```
<!--skill-flavor:sw-eval-run-list-syntax:end-->

<!--skill-flavor:sw-eval-run-compare-syntax:start-->
```bash
uip maestro flow eval run compare <run_id_a> \
  --compare-to <run_id_b> \
  --set "<set_name>" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json
```
<!--skill-flavor:sw-eval-run-compare-syntax:end-->

<!--skill-flavor:sw-eval-workflow-example:start-->
```bash
# 1. The solution already exists in Studio Web — the host owns it; nothing to upload.
#    Ids for every run command come from the context:
#    CurrentSolution.SolutionId / CurrentProject.ProjectId. Call each with timeoutSeconds: 120.
uip maestro flow eval run list --set "Smoke Tests" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json

# 2. Start the run (no --wait)
uip maestro flow eval run start \
  --set "Smoke Tests" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json

# 3. Poll until Status is Completed or Failed (separate calls)
uip maestro flow eval run status <run_id> \
  --set "Smoke Tests" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json

# 4. Inspect failures with justifications
uip maestro flow eval run results <run_id> \
  --set "Smoke Tests" \
  --only-failed --verbose \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json

# 5. After fixing the flow, re-run (steps 2–3) and compare
uip maestro flow eval run compare <new_run_id> --compare-to <old_run_id> \
  --set "Smoke Tests" --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --output json
```

If any of these calls times out (exit 124), hand the run to the user — "Open the Evaluations panel, run 'Smoke Tests', and paste the result here" — instead of retrying in a loop.
<!--skill-flavor:sw-eval-workflow-example:end-->

<!--skill-flavor:upload-safety-guide-antipattern:start-->
<!--skill-flavor:upload-safety-guide-antipattern:end-->

<!--skill-flavor:sw-eval-run-antipatterns:start-->
- **Don't use `--wait`.** Its 600 s default is the shell tool's maximum; start without it and poll `eval run status` with `timeoutSeconds: 120` per call.
- **Don't compare runs from different eval sets.** `compare` aligns by data point name; cross-set deltas are meaningless.
- **Don't rely on aggregate `Score` alone.** Inspect per-evaluator scores. A 0.86 aggregate can mask a high-similarity-but-wrong-trajectory failure.
- **Don't retry a timed-out run call in a loop.** Studio Web has one shell: on exit 124, hand the run to the user's Evaluations panel and read back the result they paste.
<!--skill-flavor:sw-eval-run-antipatterns:end-->
