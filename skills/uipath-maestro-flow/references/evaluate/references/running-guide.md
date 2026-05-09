# Running Flow Evaluations

`uip maestro flow eval run *` — start, monitor, inspect, and compare evaluation runs. All run commands require `uip login` and a Flow solution that already exists in Studio Web.

> **Before running any of these:** read [upload-safety.md](upload-safety.md). The skill must NOT auto-run `uip solution upload` to satisfy the "solution must be in Studio Web" prerequisite. If the solution isn't in Studio Web, ask the user.

## Start a Run

```bash
uip maestro flow eval run start \
  --set "<set_name>" \
  --path <flow_project> \
  [--entry-point <entry>] \
  [--solution-id <id>] \
  [--project-id <id>] \
  [--folder-key <key>] \
  [--debug-mode <mode>] \
  [--wait [--timeout <seconds>]] \
  --output json
```

### Resolution order for `--solution-id` / `--project-id`

The CLI auto-resolves these from project metadata in the working tree (typically `SolutionStorage.json` and the parent `.uipx`). Pass `--solution-id` or `--project-id` explicitly only when the working tree does not have those IDs (e.g., a freshly scaffolded local project that has never been uploaded).

If the auto-resolution fails AND you have not passed explicit IDs, the start command will error. Do NOT respond by running `uip solution upload` automatically — see [upload-safety.md](upload-safety.md) for the right action.

### `--folder-key`

The Orchestrator folder key that scopes the run. Defaults to the user's personal workspace. Pass an explicit folder key when the eval should run in a shared/team folder.

### `--wait` and `--timeout`

Without `--wait`, the command returns immediately with `EvalSetRunId`. With `--wait`, the CLI blocks until the run reaches a terminal state (`Completed` or `Failed`) or `--timeout` elapses (default 600s, hardcoded by the CLI).

`--timeout` only stops the local CLI from blocking. The server-side run continues regardless. Query progress with:

```bash
uip maestro flow eval run status <eval_set_run_id> \
  --set "<set_name>" --path <flow_project> --output json
```

Polling cadence is not part of the public CLI contract — do not depend on a specific interval.

### Output (no `--wait`)

```json
{
  "Code": "MaestroFlowEvalRunStarted",
  "Data": {
    "EvalSetRunId": "a1b2c3d4-...",
    "EvalSetName": "Smoke Tests",
    "DataPoints": 3,
    "Evaluators": 2
  }
}
```

### Output (`--wait`, on completion)

The CLI emits a summary plus per-data-point results. Use `run results` for the same data on a completed run.

## Check Status

```bash
uip maestro flow eval run status <eval_set_run_id> \
  --set "<set_name>" \
  --path <flow_project> \
  --output json
```

```json
{
  "Code": "MaestroFlowEvalRunStatus",
  "Data": {
    "EvalSetRunId": "a1b2c3d4-...",
    "Status": "Completed",
    "Score": 0.86,
    "Duration": "42.5s"
  }
}
```

Status values: `Pending`, `Running`, `Completed`, `Failed`. `Completed` and `Failed` are terminal.

## Detailed Results

```bash
uip maestro flow eval run results <eval_set_run_id> \
  --set "<set_name>" \
  --path <flow_project> \
  [--only-failed] \
  [--verbose] \
  [--export-format json|csv] \
  --output json
```

Per-data-point fields: `DataPoint`, `Status`, `EvaluatorScores`, `Duration`, `Error` (plus `Justifications` when `--verbose`).

### `--only-failed`

Filter to data points that errored or scored a hard failure. Triage faster on large sets.

### `--verbose`

Include the LLM judge's free-text justification per evaluator. Essential when a score is surprising.

### `--export-format <json|csv>`

Write results to a file alongside the project (e.g., `eval-results-<timestamp>.json` or `.csv`). Useful for archiving or feeding into a dashboard.

### Filtering with `--output-filter`

`--output-filter` takes a JMESPath expression and applies it to the JSON payload before printing. Useful for triage:

```bash
# Show only data points named "checkout-flow"
uip maestro flow eval run results <run_id> \
  --set "Smoke Tests" --path ./MySolution/MyFlow --output json \
  --output-filter 'Data.Results[?DataPoint==`checkout-flow`]'

# Show only score and name per row
uip maestro flow eval run results <run_id> \
  --set "Smoke Tests" --path ./MySolution/MyFlow --output json \
  --output-filter 'Data.Results[*].{name: DataPoint, score: Score}'
```

## List Past Runs

```bash
uip maestro flow eval run list \
  --set "<set_name>" \
  --path <flow_project> \
  --output json
```

Per-row: `EvalSetRunId`, `Status`, `Score`, `DataPoints`, `Duration`, `CreatedAt`.

## Compare Two Runs

```bash
uip maestro flow eval run compare <run_id_a> \
  --compare-to <run_id_b> \
  --set "<set_name>" \
  --path <flow_project> \
  --output json
```

Output:

```json
{
  "Code": "MaestroFlowEvalRunComparison",
  "Data": {
    "RunA": { "Id": "...", "Score": 0.86, "Status": "Completed" },
    "RunB": { "Id": "...", "Score": 0.80, "Status": "Completed" },
    "ScoreDelta": 0.06,
    "DataPoints": [
      {
        "DataPoint": "hello-test",
        "ScoreA": 1.0, "ScoreB": 0.9, "Delta": "+0.1",
        "StatusA": "Completed", "StatusB": "Completed"
      }
    ]
  }
}
```

`compare` aligns by data point `name` within the eval set. Comparing runs from different eval sets is not supported — the deltas would be meaningless.

Use `compare` after each prompt or flow change to verify the change improved scores without regressing other data points.

## Workflow Example

```bash
# 1. Verify the solution is in Studio Web (do NOT auto-upload — see upload-safety.md)
#    If unsure, list runs first; absence of any error here implies the solution exists.
uip maestro flow eval run list --set "Smoke Tests" --path ./MySolution/MyFlow --output json

# 2. Start the run, block on completion
uip maestro flow eval run start \
  --set "Smoke Tests" \
  --path ./MySolution/MyFlow \
  --wait --timeout 600 --output json

# 3. Inspect failures with justifications
uip maestro flow eval run results <run_id> \
  --set "Smoke Tests" \
  --only-failed --verbose \
  --path ./MySolution/MyFlow --output json

# 4. After fixing the flow, re-run and compare
uip maestro flow eval run start --set "Smoke Tests" --path ./MySolution/MyFlow --wait --output json
uip maestro flow eval run compare <new_run_id> --compare-to <old_run_id> \
  --set "Smoke Tests" --path ./MySolution/MyFlow --output json
```

## Failure Detection

A data point is considered failed when any of these are true:

- `Status` is `Failed`
- `Error` is non-null
- Any evaluator score type is `error`
- An exact-match evaluator returned `false`

Use `--only-failed` to filter to these rows. Use `--verbose` to read the justifications.

## Anti-patterns

- **Don't auto-run `uip solution upload`** when `eval run start` errors with a missing-solution error. Stop and ask the user — see [upload-safety.md](upload-safety.md).
- **Don't depend on `--wait`'s polling cadence.** Treat as a black-box block.
- **Don't compare runs from different eval sets.** `compare` aligns by data point name; cross-set deltas are meaningless.
- **Don't rely on aggregate `Score` alone.** Inspect per-evaluator scores. A 0.86 aggregate can mask a high-similarity-but-wrong-trajectory failure.
- **Don't keep retrying `eval run status` while `--wait` is still blocking from another shell.** Pick one — either `--wait` or polling status — to avoid race conditions on the same run ID.
