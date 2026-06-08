# Evaluate UiPath Agents

Design and run tests against coded agents using the UiPath evaluation framework.

## Quick Reference

```bash
# Local only (no cloud connection, no auth needed)
uip codedagent eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report

# With output file
uip codedagent eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report --output-file results.json

# Run only selected test cases
uip codedagent eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report --eval-ids '["test-1-happy-path"]'

# Report results to Studio Web (requires auth + UIPATH_PROJECT_ID)
uip codedagent eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --report --workers 4
```

## Prerequisites

- `entry-points.json` exists (run `uip codedagent init`).
- For `--report`: authenticated session and `UIPATH_PROJECT_ID` in `.env` (obtained by pushing the agent to Studio Web — see [file-sync.md](file-sync.md)). Use `--no-report` to skip both.

## Reference Navigation

- [Evaluators Reference](evaluations/evaluators.md) — every evaluator type, required config, scoring, and `evaluatorTypeId` values
- [Evaluation Sets](evaluations/evaluation-sets.md) — test-case file format, mocking strategies, examples
- [Creating Evaluations](evaluations/creating-evaluations.md) — test-case design and organization
- [Running Evaluations](evaluations/running-evaluations.md) — command options, score interpretation
- [Best Practices](evaluations/best-practices.md) — patterns by agent type, CI/CD integration

Read Evaluators Reference before choosing an evaluator type, and Evaluation Sets before writing test cases.

## File Structure

```
evaluations/
├── eval-sets/
│   └── smoke-test.json              # Test cases
└── evaluators/
    └── llm-judge-trajectory.json    # Evaluator config
```

Every evaluator referenced in an eval set's `evaluatorRefs` must have a matching config file in `evaluations/evaluators/` — the `id` in the config must match the `evaluatorRefs` value exactly. Evaluators are auto-discovered from this directory.

Example `evaluations/evaluators/llm-judge-trajectory.json`:

```json
{
  "version": "1.0",
  "id": "LLMJudgeTrajectoryEvaluator",
  "evaluatorTypeId": "uipath-llm-judge-trajectory-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectoryEvaluator",
    "model": "gpt-4o-mini-2024-07-18",
    "defaultEvaluationCriteria": {
      "expectedAgentBehavior": "Agent should process the input and return a response."
    }
  }
}
```

## Mocking External Calls

Two mocking paths are available:

**In-code** — Apply `@mockable()` to functions that call external services:

```python
from uipath.eval.mocks import mockable, ExampleCall

@mockable(example_calls=[
    ExampleCall(id="sunny-nyc", input="weather in NYC", output='{"temp": 72, "condition": "sunny"}'),
])
def fetch_weather(query: str) -> dict:
    return call_weather_api(query)
```

During evaluations, calls matching an `ExampleCall.input` return the paired `output`. During normal execution, the real function runs.

`@mockable` only *registers* the function as interceptable — mock values come from the test case's `mockingStrategy`. `example_calls` matter only for LLM-driven mocking:

| Mock values supplied by | `example_calls` needed? |
|---|---|
| Declarative `mockingStrategy: mockito` behaviors | No — bare `@mockable()` is correct; mockito ignores `example_calls` |
| LLM mocking (`mockingStrategy: llm`, or user wants LLM-decided substitution values) | Yes — they ground the LLM mocker; without them outputs are nondeterministic and structured-output evaluators score erratically |

When `example_calls` are needed, provide ≥1 `ExampleCall` per decorated function with `output` matching the real return shape. Do NOT add `example_calls` to mockito-mocked functions. If no mock matches at runtime, the real function runs.

**Declarative** — Set `mockingStrategy` on each test case in the eval set (`type: "mockito"` for function mocks, `type: "llm"` for LLM mocks). See [Evaluation Sets](evaluations/evaluation-sets.md) § Mocking Strategies.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `typing.Any must be a subclass of BaseEvaluatorConfig` | Invalid `evaluatorTypeId` in evaluator JSON | Check [evaluators.md](evaluations/evaluators.md) for valid type IDs |
| `target_output_key: Input should be a valid string` | ContainsEvaluator missing required config | Set `target_output_key` to the output field name in the evaluator JSON |
| `UIPATH_PROJECT_ID not found` | Agent not pushed to Studio Web (only needed for `--report`) | Push with `uip codedagent push` and set `UIPATH_PROJECT_ID` in `.env`, or use `--no-report` |
| LLM evaluator fails at runtime | Missing or empty `model` in evaluator JSON | Set `"model"` in `evaluatorConfig` to a model available in your tenant |
