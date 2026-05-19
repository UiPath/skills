# Running Evaluations

Execute evaluations against the Agent Runtime, check status, view results, and compare runs.

All run commands require the agent to be pushed to Studio Web first (`uip agent push`). The Agent Runtime executes test cases in the cloud using the pushed agent definition.

## Start an Eval Run

```bash
uip agent eval run start --set "<eval_set_name>" --path <agent_dir> --wait --output json
```

**Options:**

| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--set <name>` | Yes | Eval set name or ID | — |
| `--path <path>` | No | Agent project directory | `.` |
| `--wait` | No | Block until the run completes, then print results | `false` |
| `--timeout <seconds>` | No | Maximum time to block when `--wait` is set | `600` (10 min) |
| `--solution-id <id>` | No | Override solution ID for this run | Auto-resolved from the pushed-agent state |

Without `--wait`, the command returns immediately with `Code: AgentEvalRunStarted`:

```json
{
  "Code": "AgentEvalRunStarted",
  "Data": {
    "EvalSetRunId": "a1b2c3d4-...",
    "EvalSetName": "Default Evaluation Set",
    "TestCases": 5,
    "Evaluators": 2
  }
}
```

With `--wait`, the CLI polls every 5 seconds (hardcoded interval) until the run reaches a terminal state (`completed` or `failed`) or `--timeout` elapses, then emits `AgentEvalRunCompleted` plus per-test `AgentEvalRunResults`. If `--timeout` elapses first, the run continues server-side; query progress with `eval run status <run_id>`.

### Output codes

| Subcommand | `Code` |
|------------|--------|
| `run start` (no `--wait`) | `AgentEvalRunStarted` |
| `run start --wait` (summary) | `AgentEvalRunCompleted` |
| `run start --wait` (per-case detail) | `AgentEvalRunResults` |
| `run status` | `AgentEvalRunStatus` |
| `run results` | `AgentEvalRunResults` |
| `run results --export-format` | `AgentEvalRunExported` |
| `run list` | `AgentEvalRunList` |
| `run compare` | `AgentEvalRunComparison` |

## Check Run Status

```bash
uip agent eval run status <eval_set_run_id> --set "<eval_set_name>" --path <agent_dir> --output json
```

**Output:**
```json
{
  "Code": "AgentEvalRunStatus",
  "Data": {
    "EvalSetRunId": "a1b2c3d4-...",
    "Status": "completed",
    "Score": 0.86,
    "Duration": "42.5s",
    "EvaluatorScores": "semantic: 0.9, trajectory: 0.82"
  }
}
```

Terminal states: `completed` or `failed`.

## View Results

```bash
uip agent eval run results <eval_set_run_id> \
  --set "<eval_set_name>" \
  --path <agent_dir> \
  --output json
```

**Options:**

| Flag | Description |
|------|-------------|
| `--only-failed` | Show only failed or errored test cases |
| `--verbose` | Include evaluator justifications in output |
| `--export-format <json\|csv>` | Export results to file (`eval-results-{timestamp}.json` or `.csv`) |

**Per-test-case output fields:** `TestCase`, `Status`, `Score`, `EvaluatorScores`, `Tokens`, `Duration`, `Error` (plus `Justifications` when `--verbose`).

### Filtering results with `--output-filter`

`--output-filter` takes a JMESPath expression and applies it to the JSON payload before printing. Useful for triage:

```bash
# Print only test cases with a specific name
uip agent eval run results <run_id> --set "Default Evaluation Set" --path ./my-agent \
  --output json --output-filter 'Data.Results[?TestCase==`greeting-test`]'

# Print only the score field for each test case
uip agent eval run results <run_id> --set "Default Evaluation Set" --path ./my-agent \
  --output json --output-filter 'Data.Results[*].{name: TestCase, score: Score}'
```

### Failure detection

`--only-failed` filters to test cases where any of these are true (`isFailedRun()` in the CLI):

1. `status === "failed"` (or numeric `"3"`)
2. `errorMessage` is non-null
3. `result.score.type === "error"` (or numeric `"2"`)
4. Any `assertionRuns[*].result.score.type === "error"` (or numeric `"2"`)
5. Any `assertionRuns[*].result.score.value === false` (exact-match evaluators that returned a false boolean)

Status enum values from the SDK: `0 = pending`, `1 = running`, `2 = completed`, `3 = failed`. The CLI normalizes string and numeric forms.

## List Past Runs

```bash
uip agent eval run list --set "<eval_set_name>" --path <agent_dir> --output json
```

**Per-row output:** `EvalSetRunId`, `Status`, `Score`, `TestCases`, `Duration`, `EvaluatorScores`, `CreatedAt`.

## Compare Runs

Compare two eval runs side by side to see score changes:

```bash
uip agent eval run compare <run_id_a> \
  --compare-to <run_id_b> \
  --set "<eval_set_name>" \
  --path <agent_dir> \
  --output json
```

**Output:**
```json
{
  "Code": "AgentEvalRunComparison",
  "Data": {
    "RunA": { "Id": "...", "Score": 0.86, "Status": "completed" },
    "RunB": { "Id": "...", "Score": 0.80, "Status": "completed" },
    "ScoreDelta": 0.06,
    "TestCases": [
      {
        "TestCase": "happy-path",
        "ScoreA": 1.0,
        "ScoreB": 0.9,
        "Delta": "+0.1",
        "StatusA": "completed",
        "StatusB": "completed"
      }
    ]
  }
}
```

Use `compare` after prompt changes to verify improvements without regressions.

## Workflow Example

```bash
# 1. Add test cases
uip agent eval add greeting-test \
  --set "Default Evaluation Set" \
  --inputs '{"input":"hi there"}' \
  --expected '{"content":"Hello! How can I help you?"}' \
  --expected-agent-behavior "Agent should respond with a friendly greeting" \
  --path ./my-agent --output json

# 2. Validate (catches schema drift, missing evaluator refs, broken eval JSON)
uip agent validate --path ./my-agent --output json

# 3. Push agent to Studio Web (required before running evals)
uip agent push --path ./my-agent --output json

# 4. Run and wait
uip agent eval run start \
  --set "Default Evaluation Set" \
  --path ./my-agent \
  --wait --timeout 600 --output json

# 5. Review failures
uip agent eval run results <run_id> \
  --set "Default Evaluation Set" \
  --only-failed --verbose \
  --path ./my-agent --output json

# 6. Make changes, validate, push, re-run, compare
uip agent validate --path ./my-agent --output json
uip agent push --path ./my-agent --output json
uip agent eval run start --set "Default Evaluation Set" --path ./my-agent --wait --output json
uip agent eval run compare <new_run_id> --compare-to <old_run_id> \
  --set "Default Evaluation Set" --path ./my-agent --output json
```

## Anti-patterns

- **Don't run `eval run start` without `uip agent push` first.** The Agent Runtime executes against the pushed agent, not local files. Local edits made after the last push will not affect results.
- **Don't assume `--timeout` cancels the server-side run.** It only stops the local CLI from blocking. The run continues and can be inspected with `run status`.
- **Don't skip `uip agent validate` between edits and push.** Validate catches eval-set / evaluator drift that push will accept silently and the runtime will reject.
- **Don't compare runs from different eval sets.** `compare` aligns by test case `name` within the eval set; cross-set deltas are meaningless.
- **Don't rely on `Score` alone — inspect `EvaluatorScores`.** A 0.86 aggregate can mask a faithful-but-wrong agent (high semantic, low trajectory). Use `--verbose` to read justifications when scores look surprising.
- **Don't mix score scales across evaluators in the same eval set.** Defaults written by `uip agent init` use 0–100 prompts; defaults written by `evaluator add` use 0–1 prompts. The runtime DTO normalizes to 0–100, but mixed-scale prompts produce confusing per-evaluator scores. Decide on one scale per eval set and edit prompts to match.
