---
name: evaluate
description: Create and run evaluations for UiPath coded agents. Handles evaluator setup, test case design, evaluation execution with uipath eval, and result analysis. Supports ExactMatch, Contains, JsonSimilarity, LLMJudge, Trajectory, ToolCall, and Classification evaluators. Use when the user says "evaluate my agent", "run evals", "create test cases", or "test agent quality".
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Evaluate UiPath Agents

Design and run tests for your agents using the UiPath evaluation framework.

## Prerequisites

- `entry-points.json` exists (run `uv run uipath init`)

### Local-only vs Studio Web

Before proceeding, determine whether the user wants to run evaluations **locally only** or also **report evaluation results in Studio Web**:

- **Local-only** — No authentication or `UIPATH_PROJECT_ID` needed. Use `--no-report` flag when running evals. Skip auth checks entirely.
- **Studio Web** — Required when the user wants to report evaluation results to Studio Web or use `--report`. In this case:
  - Authentication must be configured — if not authenticated, use the [Auth skill](/uipath-coded-agents:auth) first
  - `UIPATH_PROJECT_ID` must be set in `.env` — this is obtained by pushing the agent to Studio Web via `uv run uipath push` (see [Sync skill](/uipath-coded-agents:sync))

## Quick Reference

```bash
# Run evaluations locally (no cloud connection needed)
uv run uipath eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report --workers 4

# With output file
uv run uipath eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report --output-file results.json

# Report results to Studio Web (requires auth + UIPATH_PROJECT_ID)
uv run uipath eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --report --workers 4
```

## Documentation

- **[Evaluators Reference](references/evaluators.md)** — All evaluator types, configs, scoring, and `evaluatorTypeId` values
- **[Evaluation Sets](references/evaluation-sets.md)** — Test case file format, mocking strategies, and examples
- **[Creating Evaluations](references/creating-evaluations.md)** — Test case design and organization
- **[Running Evaluations](references/running-evaluations.md)** — Command options, score interpretation, troubleshooting
- **[Best Practices](references/best-practices.md)** — Patterns by agent type, CI/CD integration

## File Structure

```
evaluations/
├── eval-sets/
│   └── smoke-test.json              # Test cases
└── evaluators/
    └── llm-judge-trajectory.json    # Evaluator config (REQUIRED)
```

**Every evaluator referenced in `evaluatorRefs` must have a matching config file in `evaluations/evaluators/`.** The `id` field in the config must match the `evaluatorRefs` value exactly.

Example `evaluations/evaluators/llm-judge-trajectory.json`:
```json
{
  "version": "1.0",
  "id": "LLMJudgeTrajectoryEvaluator",
  "evaluatorTypeId": "uipath-llm-judge-trajectory-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectoryEvaluator",
    "defaultEvaluationCriteria": {
      "expectedAgentBehavior": "Agent should process the input and return a response."
    }
  }
}
```

## Mocking External Calls

Apply `@mockable()` to functions that call external services:

```python
from uipath.testing import mockable

@mockable(example_calls=[
    {"args": {"query": "weather in NYC"}, "return_value": {"temp": 72, "condition": "sunny"}},
])
def fetch_weather(query: str) -> dict:
    return call_weather_api(query)
```

During evaluations, matching args return the mock value. During normal execution, the real function runs.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `typing.Any must be a subclass of BaseEvaluatorConfig` | Invalid `evaluatorTypeId` in evaluator JSON | Check `references/evaluators.md` for valid evaluator type IDs |
| `target_output_key: Input should be a valid string` | ContainsEvaluator missing required config | Set `"target_output_key"` to the output field name in the evaluator JSON |
| `UIPATH_PROJECT_ID not found` | Agent not pushed to Studio Web (only needed for `--report`) | Push the agent first with `uv run uipath push` and set `UIPATH_PROJECT_ID=<id>` in `.env`. For local-only evals, use `--no-report` to skip this requirement |
| All scores are 0 | Mock data missing or wrong args | Check `@mockable()` `example_calls` match the args used in eval set inputs |

## Additional Instructions

- Read [Evaluators Reference](references/evaluators.md) first to choose the right evaluator.
- Read [Evaluation Sets](references/evaluation-sets.md) for file format before creating test cases.
- Evaluators are auto-discovered from `evaluations/evaluators/` — the `id` field must match `evaluatorRefs` in eval sets.
