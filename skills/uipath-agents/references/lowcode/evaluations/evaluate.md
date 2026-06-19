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

- Agent project initialized (`uip agent init <path>`)
- `entry-points.json` present (defines `input`/`output` schema that test case `--inputs`/`--expected` must conform to)
- `uip agent validate --output json` passes (validate also checks evals and evaluators)
- Agent pushed to Studio Web (`uip agent push`) — required for running evals (the Agent Runtime executes test cases in the cloud)

Local operations (managing evaluators, eval sets, test cases) do **not** require authentication or a cloud connection. Only `uip agent eval run *` commands require cloud connectivity.

## Reference Navigation

- [Evaluators](evaluators.md) — evaluator types, adding/removing, default prompts
- [Evaluation Sets and Test Cases](evaluation-sets.md) — creating sets, adding test cases, simulation options
- [Running Evaluations](running-evaluations.md) — start, status, results, compare

Read Evaluators before choosing an evaluator type, and Evaluation Sets before writing test cases.

## File Structure

After `uip agent init`, the project structure is:

```
my-agent/
  agent.json
  entry-points.json                       # Input/output schema — test case --inputs / --expected must match
  project.uiproj
  flow-layout.json
  evals/
    evaluators/
      evaluator-default.json              # name: "Default Evaluator" (semantic-similarity)
      evaluator-default-trajectory.json   # name: "Default Trajectory Evaluator"
    eval-sets/
      evaluation-set-default.json         # name: "Default Evaluation Set" (references both evaluators)
```

Evaluators live in `evals/evaluators/` and eval sets (with inline test cases) live in `evals/eval-sets/`. Both are auto-discovered by the CLI from these directories.

CLI-added evaluators are written as `evaluator-<uuid8>.json` (first 8 hex chars of the evaluator UUID). The `<name>` argument populates the `name` field inside the JSON, NOT the filename. Reference evaluators in eval sets by `id` (UUID), not filename.

## Key Differences from Coded Agent Evals

| Aspect | Coded (`uip codedagent eval`) | Low-code (`uip agent eval`) |
|--------|-------------------------------|------------------------------|
| Execution | Local Python process | Cloud-based via Agent Runtime |
| Auth required | Only for `--report` | Always (cloud execution) |
| Prerequisite | `entry-points.json` | `uip agent push` |
| Mocking | `@mockable()` decorator + declarative | Simulation instructions only |
| CLI prefix | `uip codedagent eval` | `uip agent eval` |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Solution ID could not be resolved | Agent not pushed to Studio Web | Run `uip agent push --output json`, or pass `--solution-id <id>` explicitly to `uip agent eval run start` |
| `No evaluators found` | Empty `evals/evaluators/` directory | Run `uip agent eval evaluator add` or re-init with `uip agent init` |
| `No test cases in eval set` | Eval set has no evaluations | Run `uip agent eval add` to add test cases |
| `Unknown evaluator type "X"` | Wrong case on `--type` value | Use kebab-case only: `semantic-similarity`, `trajectory` |
| `Evaluator '<id>' is an LLM-based evaluator but 'model' is not set in its evaluatorConfig.` | LLM evaluator JSON has empty/missing `model` and is not `same-as-agent` | Set `"model"` in the evaluator JSON to a valid model (e.g. `claude-haiku-4-5-20251001`), or set it to `"same-as-agent"` and ensure `agent.json` has a model |
| `'same-as-agent' model option requires agent settings. Ensure agent.json contains valid model settings.` | Evaluator uses `"model": "same-as-agent"` but `agent.json` has no resolvable model | Set a model in `agent.json`, or override the evaluator with an explicit model |
| `401 Unauthorized` | Auth expired | Run `uip login --output json` |
| Eval run timeout (with `--wait`) | Agent taking too long or stuck | Increase `--timeout` or check agent health in Studio Web. Note: this only stops the local CLI from blocking; the run continues server-side — query with `uip agent eval run status <run_id>` |
| Validate fails with eval errors | Eval set references an evaluator that no longer exists, OR evaluator JSON missing required field, OR `category`/`type` mismatch (see [evaluators.md](evaluators.md) § What `uip agent validate` Checks) | Re-run `uip agent eval evaluator list` and reconcile `evaluatorRefs`; fix per the validate error message |

The two model-resolution errors above are **runtime checks in the cloud eval worker**, not validate-time checks — `uip agent validate` will not catch them. They surface only after `uip agent eval run start`. To pre-empt them, inspect each evaluator's `model` field locally before pushing.

## Anti-patterns

- **Don't run `uip agent eval run start` before `uip agent push`.** The Agent Runtime executes against the pushed agent. Local edits to `agent.json` after the last push will not be reflected in the run.
- **Don't skip `uip agent validate` before push.** Validate checks `evals/` and `evaluators/`; broken eval JSON will not block push but will surface as runtime errors.
- **Don't hand-edit `id` or `evaluatorRefs` UUIDs.** Eval sets reference evaluators by UUID. Renaming an evaluator file or copy-pasting a UUID across evaluators silently breaks resolution.
- **Don't expect filenames to match `<name>`.** CLI-generated evaluator files use `evaluator-<uuid8>.json`, not `<name>.json`. Look up evaluators by the `name` field inside the JSON, not by filename.
- **Don't pass `--type` in PascalCase.** The CLI rejects `SemanticSimilarity`. Only kebab-case is accepted.
- **Don't reference evaluators across projects.** Each agent project has its own `evals/evaluators/` directory; UUIDs are not portable.
