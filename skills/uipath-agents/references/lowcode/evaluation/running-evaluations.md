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
| `--wait` | No | Poll until completion and show results | `false` |
| `--timeout <seconds>` | No | Polling timeout (with `--wait`) | 600 (10 min) |
| `--solution-id <id>` | No | Override solution ID | Auto-resolved from `SolutionStorage.json` |

Without `--wait`, the command returns immediately with an `EvalSetRunId`:

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

With `--wait`, the CLI polls every 5 seconds until completion, then outputs both a summary and per-test-case results.

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

### Failure detection

A test case is considered **failed** if any of these are true:
- Status is `failed`
- Has an error message
- Any evaluator score type is `error`
- Any exact-match evaluator returned `false`

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
# 1. Push agent to Studio Web (if not already done)
uip agent push --path ./my-agent --output json

# 2. Add test cases
uip agent eval add greeting-test \
  --set "Default Evaluation Set" \
  --inputs '{"input":"hi there"}' \
  --expected '{"content":"Hello! How can I help you?"}' \
  --expected-agent-behavior "Agent should respond with a friendly greeting" \
  --path ./my-agent --output json

# 3. Run and wait
uip agent eval run start \
  --set "Default Evaluation Set" \
  --path ./my-agent \
  --wait --output json

# 4. Review failures
uip agent eval run results <run_id> \
  --set "Default Evaluation Set" \
  --only-failed --verbose \
  --path ./my-agent --output json

# 5. Make changes, push, re-run, compare
uip agent push --path ./my-agent --output json
uip agent eval run start --set "Default Evaluation Set" --path ./my-agent --wait --output json
uip agent eval run compare <new_run_id> --compare-to <old_run_id> \
  --set "Default Evaluation Set" --path ./my-agent --output json
```
