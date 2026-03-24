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

Create custom Python evaluators in `evaluations/custom_evaluators/`:

```python
from uipath.eval.evaluators import BaseEvaluationCriteria, BaseEvaluatorConfig, BaseEvaluator

class MyEvaluationCriteria(BaseEvaluationCriteria):
    my_field: str

class MyEvaluatorConfig(BaseEvaluatorConfig[MyEvaluationCriteria]):
    name: str = "MyCustomEvaluator"

class MyCustomEvaluator(BaseEvaluator[MyEvaluationCriteria, MyEvaluatorConfig, ...]):
    @classmethod
    def get_evaluator_id(cls) -> str:
        return "MyCustomEvaluator"

    async def evaluate(self, agent_execution, evaluation_criteria) -> EvaluationResult:
        pass
```

Config JSON references the Python file: `"evaluatorSchema": "file://my_evaluator.py:MyCustomEvaluator"`

---

## Field Naming Convention

JSON files use **camelCase**, Python uses **snake_case**. Key mappings: `expectedOutput`, `expectedAgentBehavior`, `searchText`, `targetOutputKey`, `defaultEvaluationCriteria`, `maxTokens`, `toolCallsCount`, `toolCallsOrder`, `expectedClass`, `positiveClass`.

## Built-in evaluatorTypeId Values

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
