# Evaluate Low-Code Agents

Design and run evaluations against low-code agents using the `uip agent eval` CLI.

## Quick Reference

```bash
# Add a test case
uip agent eval add happy-path --set "Default Evaluation Set" --inputs '{"input":"hello"}' --expected '{"content":"greeting"}' --path ./my-agent --output json

# Run evals and wait for results
uip agent eval run start --set "Default Evaluation Set" --path ./my-agent --wait --output json

# Check results (failures only, with justifications)
uip agent eval run results <run_id> --set "Default Evaluation Set" --only-failed --verbose --path ./my-agent --output json
```

## Prerequisites

- Agent project initialized (`uip agent init`)
- Agent pushed to Studio Web (`uip agent push`) — required for running evals (the Agent Runtime executes test cases in the cloud)
- `SolutionStorage.json` exists in the agent project (created by `uip agent push`)

Local operations (managing evaluators, eval sets, test cases) do **not** require authentication or a cloud connection.

## Reference Navigation

- [Evaluators](evaluators.md) — evaluator types, adding/removing, default prompts
- [Evaluation Sets and Test Cases](evaluation-sets.md) — creating sets, adding test cases, simulation options
- [Running Evaluations](running-evaluations.md) — start, status, results, compare

Read Evaluators before choosing an evaluator type, and Evaluation Sets before writing test cases.

## File Structure

After `uip agent init`, the eval-related project structure is:

```
my-agent/
  agent.json
  SolutionStorage.json              # Created after `uip agent push`
  evals/
    evaluators/
      evaluator-default.json              # Semantic similarity evaluator
      evaluator-default-trajectory.json   # Trajectory evaluator
    eval-sets/
      evaluation-set-default.json         # Default eval set (references both evaluators)
```

Evaluators live in `evals/evaluators/` and eval sets (with inline test cases) live in `evals/eval-sets/`. Both are auto-discovered by the CLI from these directories.

## Key Differences from Coded Agent Evals

| Aspect | Coded (`uip codedagent eval`) | Low-code (`uip agent eval`) |
|--------|-------------------------------|------------------------------|
| Execution | Local Python process | Cloud-based via Agent Runtime |
| Auth required | Only for `--report` | Always (cloud execution) |
| Prerequisite | `entry-points.json` | `uip agent push` (SolutionStorage.json) |
| Mocking | `@mockable()` decorator + declarative | Simulation instructions only |
| CLI prefix | `uip codedagent eval` | `uip agent eval` |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `SolutionStorage.json not found` | Agent not pushed to Studio Web | Run `uip agent push --output json` |
| `No evaluators found` | Empty `evals/evaluators/` directory | Run `uip agent eval evaluator add` or re-init with `uip agent init` |
| `No test cases in eval set` | Eval set has no evaluations | Run `uip agent eval add` to add test cases |
| `401 Unauthorized` | Auth expired | Run `uip login --output json` |
| Eval run timeout | Agent taking too long or stuck | Increase `--timeout` or check agent health in Studio Web |
| `same-as-agent` model error | Evaluator model can't be resolved | Set an explicit model in the evaluator config instead of `"same-as-agent"` |
