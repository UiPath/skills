# Evaluators Reference

## Evaluator Selection Guide

| Agent Type | Primary Evaluator | Secondary | Notes |
|-----------|------------------|-----------|-------|
| Calculator/Deterministic | Exact Match | - | Binary pass/fail |
| Text/NLP | LLM Judge Output | Contains | Semantic matching |
| Multi-step Orchestration | LLM Judge Trajectory | Tool Call Order | Execution path + tool validation |
| API Integration | JSON Similarity | Exact Match | Structured data |
| Classification | Binary/Multiclass Classification | - | Label validation |

All evaluators return scores: **1.0** (pass), **0.5-0.9** (partial), **0.0** (fail).

## Evaluator File Structure

Every evaluator needs a JSON config in `evaluations/evaluators/`. All follow this structure:

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

---

## Output-Based Evaluators

### ExactMatchEvaluator (`uipath-exact-match`)

Strict string comparison. Binary scoring (1.0 or 0.0).

**Config:** `targetOutputKey` (default `"*"`), `ignoreCase` (default false), `negated` (default false)

**Eval criteria:**
```json
"ExactMatchEvaluator": { "expectedOutput": { "result": "8" } }
```

**Use for:** Deterministic outputs, exact numbers. **Avoid for:** Natural language, floats.

### ContainsEvaluator (`uipath-contains`)

Substring search. Binary scoring (1.0 or 0.0).

**Config:** `targetOutputKey` (default `"*"`), `caseSensitive` (default false), `negated` (default false)

**Eval criteria:**
```json
"ContainsEvaluator": { "searchText": "success" }
```

**Use for:** Keyword validation, required terms.

### JsonSimilarityEvaluator (`uipath-json-similarity`)

Tree-based JSON comparison. Continuous scoring (0.0-1.0). Strings use Levenshtein distance, numbers ~1% tolerance. Missing keys penalized, extra keys ignored.

**Eval criteria:**
```json
"JsonSimilarityEvaluator": { "expectedOutput": { "result": 5.0, "status": "complete" } }
```

**Use for:** Structured JSON output, API responses. **Avoid for:** Exact string matching.

LLM-based evaluators (all `uipath-llm-judge-*`) require `model` in `evaluatorConfig` — set it to a model available in your tenant. An empty or missing `model` fails at request time against the LLM Gateway.

### LLMJudgeOutputEvaluator (`uipath-llm-judge-output-semantic-similarity`)

LLM-powered semantic similarity. Continuous scoring (0.0-1.0). Accept 0.7+ as good match.

**Config:** `model`, `temperature` (default 0), `maxTokens` (default 4096), `targetOutputKey`, `prompt` (optional, placeholders: `{{ExpectedOutput}}`, `{{ActualOutput}}`)

**Eval criteria:**
```json
"LLMJudgeOutputEvaluator": { "expectedOutput": { "summary": "A helpful response about the topic" } }
```

**Use for:** Natural language, summaries. **Note:** Requires LLM API access.

### LLMJudgeStrictJSONSimilarityOutputEvaluator (`uipath-llm-judge-output-strict-json-similarity`)

Per-key JSON matching with LLM-powered penalty scoring. Continuous (0.0-1.0).

**Eval criteria:**
```json
"LLMJudgeStrictJSONSimilarityOutputEvaluator": { "expectedOutput": { "key1": "value1" } }
```

**Use for:** Structured outputs where each field matters independently.

---

## Trajectory & Tool Call Evaluators

### LLMJudgeTrajectoryEvaluator (`uipath-llm-judge-trajectory-similarity`)

LLM-powered execution path analysis. Continuous scoring (0.0-1.0).

**Config:** `model`, `temperature` (default 0), `prompt` (optional, placeholders: `{{AgentRunHistory}}`, `{{ExpectedAgentBehavior}}`, `{{UserOrSyntheticInput}}`)

**Eval criteria:**
```json
"LLMJudgeTrajectoryEvaluator": {
  "expectedAgentBehavior": "The agent should call the calculator tool once with the correct arguments and return the sum."
}
```

**Writing good behavior descriptions:** Be specific ("Agent calls fetch_data, then transform_data in order"), not vague ("Agent should work correctly").

**Use for:** Multi-step agents, tool call validation. **Note:** Requires LLM API access.

### LLMJudgeTrajectorySimulationEvaluator (`uipath-llm-judge-trajectory-simulation`)

Uses LLM simulation to evaluate agent trajectory. Continuous (0.0-1.0).

**Eval criteria:**
```json
"LLMJudgeTrajectorySimulationEvaluator": {
  "expectedAgentBehavior": "The agent should search for the product, compare prices, and return the cheapest option."
}
```

**Placeholders:** `{{ExpectedAgentBehavior}}`, `{{AgentRunHistory}}`, `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`

### ToolCallOrderEvaluator (`uipath-tool-call-order`)

Validates tool call sequence.

**Eval criteria:**
```json
"ToolCallOrderEvaluator": { "toolCallsOrder": ["search_products", "compare_prices", "format_result"] }
```

### ToolCallArgsEvaluator (`uipath-tool-call-args`)

Validates arguments passed to tool calls.

**Config:** `strict` (default false), `subset` (default false)

**Eval criteria:**
```json
"ToolCallArgsEvaluator": {
  "toolCalls": [{ "name": "calculator", "arguments": { "a": 5, "b": 3, "operation": "add" } }]
}
```

### ToolCallCountEvaluator (`uipath-tool-call-count`)

Validates tool call counts. Operators: `"="`, `">"`, `"<"`, `">="`, `"<="`.

**Eval criteria:**
```json
"ToolCallCountEvaluator": { "toolCallsCount": { "search": ["=", 1], "format": ["=", 2] } }
```

### ToolCallOutputEvaluator (`uipath-tool-call-output`)

Validates tool call outputs.

**Eval criteria:**
```json
"ToolCallOutputEvaluator": {
  "toolOutputs": [{ "name": "get_temperature", "output": "{'temperature': 25.0, 'unit': 'fahrenheit'}" }]
}
```

---

## Classification Evaluators

### BinaryClassificationEvaluator (`uipath-binary-classification`)

**Config:** `classes` (string[]), `positiveClass` (string), `metricType` (`"precision"`, `"recall"`, `"f-score"`)

**Eval criteria:**
```json
"BinaryClassificationEvaluator": { "expectedClass": "positive" }
```

### MulticlassClassificationEvaluator (`uipath-multiclass-classification`)

**Config:** `classes` (string[]), `metricType` (`"precision"`, `"recall"`, `"f-score"`), `averaging` (`"micro"`, `"macro"`)

**Eval criteria:**
```json
"MulticlassClassificationEvaluator": { "expectedClass": "spam" }
```

---

## Custom Evaluators

Two commands — run in order:

```bash
# 1. Scaffold the evaluator class at evaluations/evaluators/custom/<name>.py
uip codedagent add evaluator <EVALUATOR_NAME>

# 2. Generate the evaluator JSON spec from the Python class
uip codedagent register evaluator <EVALUATOR_NAME>.py
```

`add` scaffolds `evaluations/evaluators/custom/<name>.py`. Edit it, then run `register` to generate `evaluations/evaluators/<name>-evaluator.json`. The spec references the Python file via `"evaluatorSchema": "file://<name>.py:<ClassName>"`.

### Criteria class requirements

The criteria class holds per-test-case data:

```python
class MyEvaluationCriteria(BaseEvaluationCriteria):
    expected_value: str = ""          # field with default — required
```

Criteria with no fields (`pass`) causes **"No evaluation criteria provided"** at runtime.

### evaluationCriterias per-case values

| Value | Behavior |
|-------|----------|
| `"MyEvaluator": { "expectedValue": "x" }` | Run with these criteria, overriding `defaultEvaluationCriteria` from the spec |
| `"MyEvaluator": null` | Run using `defaultEvaluationCriteria` from the evaluator spec |
| evaluator id absent / `evaluationCriterias: {}` | Skip the evaluator for this test case |

### defaultEvaluationCriteria

`register` generates `"defaultEvaluationCriteria": null`. Set it manually in the spec so tests that omit criteria in the eval set still run:

```json
"evaluatorConfig": {
  "name": "MyEvaluator",
  "defaultEvaluationCriteria": { "expectedValue": "" }
}
```

JSON uses camelCase — `expected_value` → `expectedValue`.

### Wiring into an eval set

Reference the evaluator `id` from the spec in `evaluatorRefs`, then key each test case's `evaluationCriterias` on that same id:

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

### Evaluating trace spans

Custom evaluators receive `agent_execution.agent_trace` — a list of OpenTelemetry `ReadableSpan` objects from the agent run. Use this to evaluate execution behavior that output-based evaluators cannot: timing, call order, named operations.

Add `@traced(name="<span-name>")` to any function in the agent to emit a named span, then match by `span.name` in the evaluator. Always use explicit names — it keeps span lookup clean and unambiguous. See [tracing.md](../../capabilities/tracing.md) for the full decorator API.

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

---

## Field Naming Convention

JSON files use **camelCase**, Python uses **snake_case**. Key mappings: `expectedOutput`, `expectedAgentBehavior`, `searchText`, `targetOutputKey`, `defaultEvaluationCriteria`, `maxTokens`, `toolCallsCount`, `toolCallsOrder`, `expectedClass`, `positiveClass`.

## Built-in evaluatorTypeId Values

The SDK exposes 13 public built-in `evaluatorTypeId` values in the enum below.[^templates]

| evaluatorTypeId | Evaluator | Scoring |
|----------------|-----------|---------|
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
