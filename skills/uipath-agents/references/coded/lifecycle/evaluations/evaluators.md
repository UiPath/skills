# Evaluators Reference

## Evaluator Selection Guide

| Agent Type | Primary Evaluator | Secondary | Notes |
|---|---|---|---|
| Calculator/Deterministic | Exact Match | - | Binary pass/fail |
| Text/NLP | LLM Judge Output | Contains | Semantic matching |
| Multi-step Orchestration | LLM Judge Trajectory | Tool Call Order | Execution path + tool validation |
| API Integration | JSON Similarity | Exact Match | Structured data |
| Classification | Binary/Multiclass Classification | - | Label validation |

All evaluators return **1.0** (pass), **0.5-0.9** (partial), or **0.0** (fail).

## Evaluator File Structure

Every evaluator needs a JSON config in `evaluations/evaluators/`:

```json
{
  "version": "1.0",
  "id": "<EvaluatorId>",
  "evaluatorTypeId": "<uipath-type-id>",
  "description": "...",
  "evaluatorConfig": {
    "name": "<EvaluatorId>",
    "defaultEvaluationCriteria": { ... }
  }
}
```

## Output-Based Evaluators

| Evaluator | Type ID and scoring | Configuration | Use |
|---|---|---|---|
| **ExactMatchEvaluator** | `uipath-exact-match`; strict string comparison, binary (1.0 or 0.0) | `targetOutputKey` (default `"*"`), `ignoreCase` (default false), `negated` (default false) | Deterministic outputs and exact numbers; avoid for natural language and floats |
| **ContainsEvaluator** | `uipath-contains`; substring search, binary (1.0 or 0.0) | `targetOutputKey` (default `"*"`), `caseSensitive` (default false), `negated` (default false) | Keyword validation and required terms |
| **JsonSimilarityEvaluator** | `uipath-json-similarity`; tree-based JSON comparison, continuous (0.0-1.0) | — | Structured JSON outputs and API responses; avoid for exact string matching |
| **LLMJudgeOutputEvaluator** | `uipath-llm-judge-output-semantic-similarity`; LLM semantic similarity, continuous (0.0-1.0); accept 0.7+ as a good match | `model`, `temperature` (default 0), `maxTokens` (default 4096), `targetOutputKey`, optional `prompt` with `{{ExpectedOutput}}` and `{{ActualOutput}}` | Natural language and summaries; requires LLM API access |
| **LLMJudgeStrictJSONSimilarityOutputEvaluator** | `uipath-llm-judge-output-strict-json-similarity`; per-key LLM penalty scoring, continuous (0.0-1.0) | — | Structured outputs where each field matters independently |

`JsonSimilarityEvaluator` uses Levenshtein distance for strings, approximately 1% tolerance for numbers, penalizes missing keys, and ignores extra keys.

All LLM-based evaluators (`uipath-llm-judge-*`) require `model` in `evaluatorConfig`. Set it to a model available in your tenant; an empty or missing `model` fails at request time against the LLM Gateway.

Eval criteria examples:

```json
"ExactMatchEvaluator": { "expectedOutput": { "result": "8" } }
"ContainsEvaluator": { "searchText": "success" }
"JsonSimilarityEvaluator": { "expectedOutput": { "result": 5.0, "status": "complete" } }
"LLMJudgeOutputEvaluator": { "expectedOutput": { "summary": "A helpful response about the topic" } }
"LLMJudgeStrictJSONSimilarityOutputEvaluator": { "expectedOutput": { "key1": "value1" } }
```

## Trajectory and Tool Call Evaluators

| Evaluator | Type ID / behavior | Criteria or configuration |
|---|---|---|
| **LLMJudgeTrajectoryEvaluator** | `uipath-llm-judge-trajectory-similarity`; LLM execution-path analysis, continuous (0.0-1.0) | `model`, `temperature` (default 0), optional `prompt` with `{{AgentRunHistory}}`, `{{ExpectedAgentBehavior}}`, and `{{UserOrSyntheticInput}}`; criteria uses `expectedAgentBehavior` |
| **LLMJudgeTrajectorySimulationEvaluator** | `uipath-llm-judge-trajectory-simulation`; LLM simulation-based trajectory evaluation, continuous (0.0-1.0) | Placeholders: `{{ExpectedAgentBehavior}}`, `{{AgentRunHistory}}`, `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}` |
| **ToolCallOrderEvaluator** | `uipath-tool-call-order`; validates tool-call sequence | `toolCallsOrder` |
| **ToolCallArgsEvaluator** | `uipath-tool-call-args`; validates tool-call arguments | `strict` (default false), `subset` (default false), and `toolCalls` |
| **ToolCallCountEvaluator** | `uipath-tool-call-count`; validates counts | `toolCallsCount`; operators: `"="`, `">"`, `"<"`, `">="`, `"<="` |
| **ToolCallOutputEvaluator** | `uipath-tool-call-output`; validates tool-call outputs | `toolOutputs` |

Write trajectory behavior specifically, such as “Agent calls fetch_data, then transform_data in order,” not vaguely, such as “Agent should work correctly.” LLM-based trajectory evaluators require LLM API access.

Criteria examples:

```json
"LLMJudgeTrajectoryEvaluator": {
  "expectedAgentBehavior": "The agent should call the calculator tool once with the correct arguments and return the sum."
}
"LLMJudgeTrajectorySimulationEvaluator": {
  "expectedAgentBehavior": "The agent should search for the product, compare prices, and return the cheapest option."
}
"ToolCallOrderEvaluator": { "toolCallsOrder": ["search_products", "compare_prices", "format_result"] }
"ToolCallArgsEvaluator": {
  "toolCalls": [{ "name": "calculator", "arguments": { "a": 5, "b": 3, "operation": "add" } }]
}
"ToolCallCountEvaluator": { "toolCallsCount": { "search": ["=", 1], "format": ["=", 2] } }
"ToolCallOutputEvaluator": {
  "toolOutputs": [{ "name": "get_temperature", "output": "{'temperature': 25.0, 'unit': 'fahrenheit'}" }]
}
```

## Classification Evaluators

### BinaryClassificationEvaluator (`uipath-binary-classification`)

Configuration: `classes` (string[]), `positiveClass` (string), and `metricType` (`"precision"`, `"recall"`, `"f-score"`).

```json
"BinaryClassificationEvaluator": { "expectedClass": "positive" }
```

### MulticlassClassificationEvaluator (`uipath-multiclass-classification`)

Configuration: `classes` (string[]), `metricType` (`"precision"`, `"recall"`, `"f-score"`), and `averaging` (`"micro"`, `"macro"`).

```json
"MulticlassClassificationEvaluator": { "expectedClass": "spam" }
```

## Custom Evaluators

Run these commands in order:

```bash
# 1. Scaffold the evaluator class at evaluations/evaluators/custom/<name>.py
uip codedagent add evaluator <EVALUATOR_NAME>

# 2. Generate the evaluator JSON spec from the Python class
uip codedagent register evaluator <EVALUATOR_NAME>.py
```

`add` scaffolds `evaluations/evaluators/custom/<name>.py`. Edit it, then run `register` to generate `evaluations/evaluators/<name>-evaluator.json`. The spec references the Python file via `"evaluatorSchema": "file://<name>.py:<ClassName>"`.

### Criteria Class Requirements

The criteria class holds per-test-case data:

```python
class MyEvaluationCriteria(BaseEvaluationCriteria):
    expected_value: str = ""          # field with default — required
```

Criteria with no fields (`pass`) causes **"No evaluation criteria provided"** at runtime.

### `evaluationCriterias` Per-Case Values

| Value | Behavior |
|---|---|
| `"MyEvaluator": { "expectedValue": "x" }` | Run with these criteria, overriding `defaultEvaluationCriteria` from the spec |
| `"MyEvaluator": null` | Run using `defaultEvaluationCriteria` from the evaluator spec |
| Evaluator ID absent / `evaluationCriterias: {}` | Skip the evaluator for this test case |

### `defaultEvaluationCriteria`

`register` generates `"defaultEvaluationCriteria": null`. Set it manually in the spec so tests that omit criteria in the eval set still run:

```json
"evaluatorConfig": {
  "name": "MyEvaluator",
  "defaultEvaluationCriteria": { "expectedValue": "" }
}
```

JSON uses camelCase; Python uses snake_case. For example, `expected_value` becomes `expectedValue`.

### Wiring into an Eval Set

Reference the evaluator `id` from the spec in `evaluatorRefs`, then key each test case's `evaluationCriterias` on that same ID:

```json
{
  "version": "1.0",
  "id": "my-eval-set",
  "name": "My Eval Set",
  "evaluatorRefs": ["MyEvaluator"],
  "evaluations": [
    {
      "id": "test-1",
      "name": "test-1",
      "inputs": { "param": "value" },
      "evaluationCriterias": {
        "MyEvaluator": { "expectedValue": "value" }
      }
    }
  ]
}
```

### Evaluating Trace Spans

Custom evaluators receive `agent_execution.agent_trace`, a list of OpenTelemetry `ReadableSpan` objects from the agent run. Use it to evaluate timing, call order, and named operations that output-based evaluators cannot evaluate.

Add `@traced(name="<span-name>")` to any agent function to emit a named span, then match by `span.name` in the evaluator. Always use explicit names to keep span lookup clean and unambiguous. See [tracing.md](../../capabilities/tracing.md) for the full decorator API.

```python
# In the agent
from uipath.tracing import traced

@traced(name="my-operation")
def my_function(input):
    ...
```

```python
# In the evaluator
async def evaluate(self, agent_execution, criteria):
    spans = agent_execution.agent_trace
    named = [s for s in spans if s.name == "my-operation"]
    if not named:
        return NumericEvaluationResult(score=0.0, details="span not found")
    duration_ms = (named[0].end_time - named[0].start_time) / 1_000_000
    passed = duration_ms <= criteria.max_ms
    return NumericEvaluationResult(score=1.0 if passed else 0.0, details=f"{duration_ms:.2f}ms")
```

## Field Naming Convention

JSON files use **camelCase**; Python uses **snake_case**. Key mappings: `expectedOutput`, `expectedAgentBehavior`, `searchText`, `targetOutputKey`, `defaultEvaluationCriteria`, `maxTokens`, `toolCallsCount`, `toolCallsOrder`, `expectedClass`, `positiveClass`.

## Built-in evaluatorTypeId Values

The SDK exposes 13 public built-in `evaluatorTypeId` values in the enum below.[^templates]

| evaluatorTypeId | Evaluator | Scoring |
|---|---|---|
| `uipath-exact-match` | ExactMatchEvaluator | Binary (0/1) |
| `uipath-contains` | ContainsEvaluator | Binary (0/1) |
| `uipath-json-similarity` | JsonSimilarityEvaluator | Continuous (0-1) |
| `uipath-llm-judge-output-semantic-similarity` | LLMJudgeOutputEvaluator | Continuous (0-1) |
| `uipath-llm-judge-output-strict-json-similarity` | LLMJudgeStrictJSONSimilarityOutputEvaluator | Continuous (0-1) |
| `uipath-llm-judge-trajectory-similarity` | LLMJudgeTrajectoryEvaluator | Continuous (0-1) |
| `uipath-llm-judge-trajectory-simulation` | LLMJudgeTrajectorySimulationEvaluator | Continuous (0-1) |
| `uipath-binary-classification` | BinaryClassificationEvaluator | Binary (0/1) |
| `uipath-multiclass-classification` | MulticlassClassificationEvaluator | Continuous (0-1) |
| `uipath-tool-call-order` | ToolCallOrderEvaluator | Binary/Fractional |
| `uipath-tool-call-args` | ToolCallArgsEvaluator | Binary/Fractional |
| `uipath-tool-call-count` | ToolCallCountEvaluator | Binary/Fractional |
| `uipath-tool-call-output` | ToolCallOutputEvaluator | Binary/Fractional |

[^templates]: The package currently ships 11 bundled evaluator config templates under `uipath/eval/evaluators_types/`; classification evaluators are valid built-in type IDs but do not have bundled template JSON files.