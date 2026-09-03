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

- Run `uip codedagent init` to create `entry-points.json`.
- For `--report`, authenticate and set `UIPATH_PROJECT_ID` in `.env`; obtain it by pushing the agent to Studio Web (see [file-sync.md](file-sync.md)). Run with `--no-report` to avoid both requirements.

## Reference Navigation

- [Evaluators Reference](evaluations/evaluators.md) — evaluator types, required config, scoring, and `evaluatorTypeId` values
- [Evaluation Sets](evaluations/evaluation-sets.md) — test-case format, mocking strategies, and examples
- [Creating Evaluations](evaluations/creating-evaluations.md) — test-case design and organization
- [Running Evaluations](evaluations/running-evaluations.md) — command options and score interpretation
- [Best Practices](evaluations/best-practices.md) — agent-type patterns and CI/CD integration

Read [Evaluators Reference](evaluations/evaluators.md) before choosing an evaluator type and [Evaluation Sets](evaluations/evaluation-sets.md) before writing test cases.

## File Structure

```text
evaluations/
├── eval-sets/
│   └── smoke-test.json              # Test cases
└── evaluators/
    └── llm-judge-output.json        # Evaluator config
```

Every evaluator in an eval set's `evaluatorRefs` must have a config file in `evaluations/evaluators/`; its `id` must exactly match the `evaluatorRefs` value. Evaluators are auto-discovered there.

Choose by output type: deterministic/structured → `uipath-exact-match` / `uipath-contains` / `uipath-json-similarity`; natural language → `uipath-llm-judge-output-semantic-similarity`. Use trajectory/tool-call evaluators only for multi-step or tool-using agents; they score 0.0 on single-step agents. See [evaluators.md](evaluations/evaluators.md) and [best-practices.md](evaluations/best-practices.md).

Example `evaluations/evaluators/llm-judge-output.json`:

```json
{
  "version": "1.0",
  "id": "LLMJudgeOutputEvaluator",
  "evaluatorTypeId": "uipath-llm-judge-output-semantic-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeOutputEvaluator",
    "model": "gpt-4o-mini-2024-07-18",
    "defaultEvaluationCriteria": {
      "expectedOutput": {"<output_field>": "A correct, on-topic response for the given input."}
    }
  }
}
```

## Mocking External Calls

Use in-code mocking or declarative test-case mocking.

### In-code

Apply `@mockable()` to functions that call external services:

```python
from uipath.eval.mocks import mockable, ExampleCall

@mockable(example_calls=[
    ExampleCall(id="sunny-nyc", input="weather in NYC", output='{"temp": 72, "condition": "sunny"}'),
])
def fetch_weather(query: str) -> dict:
    return call_weather_api(query)
```

During evaluations, matching `ExampleCall.input` returns its paired `output`; normal execution runs the real function. `@mockable` only registers interception—test-case `mockingStrategy` supplies mock values.

| Mock values supplied by | `example_calls` needed? |
|---|---|
| Declarative `mockingStrategy: mockito` behaviors | No — use bare `@mockable()`; mockito ignores `example_calls` |
| LLM mocking (`mockingStrategy: llm`, or user wants LLM-decided substitution values) | Yes — they ground the LLM mocker; without them outputs are nondeterministic and structured-output evaluators score erratically |

When needed, provide ≥1 `ExampleCall` per decorated function and make `output` match the real return shape. Do not add `example_calls` to mockito-mocked functions. If no mock matches at runtime, run the real function.

### Declarative

Set `mockingStrategy` on each eval-set test case: use `type: "mockito"` for function mocks or `type: "llm"` for LLM mocks. See [Evaluation Sets](evaluations/evaluation-sets.md) § Mocking Strategies.

## Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| `typing.Any must be a subclass of BaseEvaluatorConfig` | Invalid `evaluatorTypeId` in evaluator JSON | Check [evaluators.md](evaluations/evaluators.md) for valid type IDs |
| `target_output_key: Input should be a valid string` | ContainsEvaluator missing required config | Set `target_output_key` to the output field name in the evaluator JSON |
| `UIPATH_PROJECT_ID not found` | Agent not pushed to Studio Web (only needed for `--report`) | Push with `uip codedagent push` and set `UIPATH_PROJECT_ID` in `.env`, or use `--no-report` |
| LLM evaluator fails at runtime | Missing or empty `model` in evaluator JSON | Set `"model"` in `evaluatorConfig` to a model available in your tenant |
