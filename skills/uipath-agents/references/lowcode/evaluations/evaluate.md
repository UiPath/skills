# Evaluate Low-Code Agents

Design and run evaluations against low-code agents with the `uip agent eval` CLI. The CLI supports autonomous agents only; handle conversational-agent evaluations through Studio Web after uploading the Agent solution.

## Quick Reference

```bash
# Add a test case
uip agent eval add happy-path --set "Default Evaluation Set" --inputs '{"input":"hello"}' --expected '{"content":"greeting"}' --path ./my-agent --output json

# Run evals and wait for results
uip agent eval run start --set "Default Evaluation Set" --path ./my-agent --wait --output json

# Check results (failures only, with justifications)
uip agent eval run results <run_id> --set "Default Evaluation Set" --only-failed --verbose --path ./my-agent --output json
```

## Prerequisites and Connectivity

- Initialize the project with `uip agent init <path>`.
- Ensure `entry-points.json` exists; its `input`/`output` schema defines the required shapes for `--inputs` and `--expected`.
- Run `uip agent validate --output json`; validation checks evaluations and evaluators.
- Upload the solution with `uip solution upload`; cloud execution requires the uploaded solution because the Agent Runtime executes test cases in the cloud.
- Local evaluator, evaluation-set, and test-case management requires neither authentication nor cloud connectivity. Run `uip agent eval run *` commands only with cloud connectivity.

## Reference Navigation

- [Evaluators](evaluators.md) — evaluator types, adding/removing, and default prompts
- [Evaluation Sets and Test Cases](evaluation-sets.md) — sets, test cases, and simulation options
- [Running Evaluations](running-evaluations.md) — start, status, results, and compare
- [Orchestrator Runtime Eval Commands](orchestrator-eval-run.md) — full CRUD for evaluators, eval sets, data points, run/schedule/results against published Orchestrator packages

Read Evaluators before choosing an evaluator type and Evaluation Sets before writing test cases.

## File Structure

After `uip agent init`, expect:

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

The CLI auto-discovers evaluators in `evals/evaluators/` and eval sets, including inline test cases, in `evals/eval-sets/`. CLI-added evaluators use filenames `evaluator-<uuid8>.json` (the first 8 hex characters of the evaluator UUID); the `<name>` argument populates the JSON `name` field, not the filename. Reference evaluators in eval sets by UUID `id`, never by filename.

## Key Differences from Coded Agent Evals

| Aspect | Coded (`uip codedagent eval`) | Low-code (`uip agent eval`) |
|--------|-------------------------------|------------------------------|
| Execution | Local Python process | Cloud-based via Agent Runtime |
| Auth required | Only for `--report` | Always (cloud execution) |
| Prerequisite | `entry-points.json` | `uip solution upload` |
| Mocking | `@mockable()` decorator + declarative | Simulation instructions only |
| CLI prefix | `uip codedagent eval` | `uip agent eval` |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Solution ID could not be resolved | Agent's solution not uploaded to Studio Web | Run `uip solution upload . --output json` (add `--force` to replace an existing cloud solution), or pass `--solution-id <id>` explicitly to `uip agent eval run start` |
| `No evaluators found` | Empty `evals/evaluators/` directory | Run `uip agent eval evaluator add` or re-init with `uip agent init` |
| `No test cases in eval set` | Eval set has no evaluations | Run `uip agent eval add` to add test cases |
| `Unknown evaluator type "X"` | Wrong case on `--type` | Use kebab-case only: `semantic-similarity`, `trajectory` |
| `Evaluator '<id>' is an LLM-based evaluator but 'model' is not set in its evaluatorConfig.` | LLM evaluator JSON has empty/missing `model` and is not `same-as-agent` | Set `"model"` in the evaluator JSON to a valid model (e.g. `claude-haiku-4-5-20251001`), or set it to `"same-as-agent"` and ensure `agent.json` has a model |
| `'same-as-agent' model option requires agent settings. Ensure agent.json contains valid model settings.` | Evaluator uses `"model": "same-as-agent"` but `agent.json` has no resolvable model | Set a model in `agent.json`, or override the evaluator with an explicit model |
| `401 Unauthorized` | Auth expired | Run `uip login --output json` |
| Eval run timeout (with `--wait`) | Agent takes too long or is stuck | Increase `--timeout` or check agent health in Studio Web. This stops only the local CLI wait; the run continues server-side. Query it with `uip agent eval run status <run_id>` |
| Validate fails with eval errors | Eval set references a missing evaluator, evaluator JSON lacks a required field, or `category`/`type` mismatch (see [evaluators.md](evaluators.md) § What `uip agent validate` Checks) | Re-run `uip agent eval evaluator list`, reconcile `evaluatorRefs`, and fix the error |

The two model-resolution errors above are runtime checks in the cloud eval worker, not validate-time checks. `uip agent validate` will not catch them. Before uploading, inspect each evaluator's `model` field locally.

## Anti-patterns

- **Don't run `uip agent eval run start` before `uip solution upload`.** The Agent Runtime uses the uploaded agent; edits to `agent.json` after the last upload are not reflected.
- **Don't skip `uip agent validate` before upload.** Validation checks `evals/` and evaluators; broken eval JSON will not block upload but will surface as runtime errors.
- **Don't hand-edit `id` or `evaluatorRefs` UUIDs.** Eval sets reference evaluators by UUID; renaming an evaluator file or copying a UUID across evaluators silently breaks resolution.
- **Don't expect filenames to match `<name>`.** CLI-generated files use `evaluator-<uuid8>.json`; find evaluators by their JSON `name` field.
- **Don't pass `--type` in PascalCase.** The CLI rejects `SemanticSimilarity`; use kebab-case.
- **Don't reference evaluators across projects.** Each project has its own `evals/evaluators/` directory, and UUIDs are not portable.
