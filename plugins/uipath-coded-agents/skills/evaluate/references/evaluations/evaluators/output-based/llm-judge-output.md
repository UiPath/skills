# LLM Judge Output Evaluators

Uses Language Models to assess the quality and semantic similarity of agent outputs. These evaluators are ideal when deterministic comparison is insufficient and human-like judgment is needed.

## Overview

There are two variants:

1. **LLM Judge Output Evaluator** - General semantic similarity evaluation
2. **LLM Judge Strict JSON Similarity Output Evaluator** - Strict JSON structure matching with LLM judgment

**Use Cases:**
- Evaluate natural language outputs
- Assess semantic similarity beyond exact matching
- Judge output quality based on intent and meaning
- Validate structured outputs with flexible criteria

**Returns:** Continuous score from 0.0 to 1.0 with LLM justification

## LLM Service Integration

LLM Judge evaluators use the **UiPathLlmService** by default, which:
- Integrates with configured LLM providers through the UiPath platform
- Supports multiple providers (OpenAI, Anthropic, etc.)
- Allows custom LLM service if needed

### Model Selection

Specify the model according to your LLM service's conventions:

```json
{
  "model": "gpt-4o-2024-11-20",  // OpenAI
  "model": "claude-3-5-sonnet-20241022"  // Anthropic
}
```

## LLM Judge Output Evaluator

### Overview

**Evaluator ID:** `llm-judge-output-semantic-similarity`

General semantic similarity evaluation using LLM judgment.

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"LLMJudgeOutputEvaluator"` | Display name |
| `model` | `str` | Required | LLM model to use |
| `temperature` | `float` | `0.0` | LLM temperature (0.0 for deterministic) |
| `max_tokens` | `int` | `None` | Maximum tokens for response |
| `prompt` | `str` | Default | Custom evaluation prompt |
| `target_output_key` | `str` | `"*"` | Specific field to evaluate |
| `default_evaluation_criteria` | `dict` | `None` | Default criteria |

### Evaluation Criteria

```json
{
  "expected_output": {
    "result": "Expected text or description"
  }
}
```

### Prompt Placeholders

The prompt template supports these placeholders:

- `{{ActualOutput}}` - The output produced by the agent
- `{{ExpectedOutput}}` - The expected output from criteria

### Usage Examples

#### Basic Semantic Similarity

```json
{
  "version": "1.0",
  "id": "LLMJudgeOutputEvaluator",
  "evaluatorTypeId": "uipath-llm-judge-output-semantic-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeOutputEvaluator",
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.0,
    "targetOutputKey": "answer"
  }
}
```

Test:
- Input: `{"query": "What is the capital of France?"}`
- Actual output: `{"answer": "Paris is the capital city of France."}`
- Expected: `{"answer": "The capital of France is Paris."}`
- **Score: ~0.95** (semantically equivalent, different wording)

#### Custom Evaluation Prompt

```json
{
  "evaluatorConfig": {
    "name": "LLMJudgeOutputEvaluator",
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.0,
    "prompt": "Compare the actual output with the expected output.\nFocus on semantic meaning and intent rather than exact wording.\n\nActual Output: {{ActualOutput}}\nExpected Output: {{ExpectedOutput}}\n\nProvide a score from 0-100 based on semantic similarity."
  }
}
```

#### Natural Language Quality Assessment

Evaluate email quality:
- Actual: Multi-sentence professional response
- Expected: Professional, courteous response addressing the inquiry
- **Score: 0.9-0.95** (LLM judges professionalism and tone)

### Best Practices

1. **Use temperature 0.0** for deterministic evaluations
2. **Craft clear prompts** - Be specific about evaluation criteria
3. **Include both placeholders** - Always use `{{ActualOutput}}` and `{{ExpectedOutput}}`
4. **Set score thresholds** - Define minimum acceptable scores (e.g., ≥ 0.8)
5. **Review justifications** - Use LLM explanations to understand scores
6. **Cost awareness** - LLM evaluations use API calls, monitor token costs

## LLM Judge Strict JSON Similarity Output Evaluator

### Overview

**Evaluator ID:** `llm-judge-output-strict-json-similarity`

Performs **per-key matching** on JSON structures with penalty-based scoring.

### How It Works

1. **Key Inventory:** Identifies all top-level keys in expected and actual outputs
2. **Per-Key Matching:** For each expected key, checks if it exists in actual output
3. **Content Assessment:** For matching keys, evaluates content similarity (identical/similar/different)
4. **Penalty-Based Scoring:** Calculates score using penalties per key (where N = total expected keys):
   - **Missing key** (not in actual): `100/N` penalty
   - **Wrong key** (exists but different content): `100/N` penalty
   - **Similar key** (similar content): `50/N` penalty
   - **Identical key** (identical content): `0` penalty
   - **Extra key** (in actual but not expected): `10/N` penalty

**Final Score:** `100 - total_penalty` (normalized to 0-1 scale)

### Why "Strict"?

Unlike standard `LLMJudgeOutputEvaluator` which evaluates semantic similarity holistically:
- **Enforces structural matching** - Each expected key must be present
- **Penalizes missing keys heavily** - Same as wrong content (100/N penalty)
- **Evaluates per-key** - Independence between key evaluations
- **Deterministic scoring formula** - Mechanical calculation based on key-level assessments

### Configuration

Same as LLMJudgeOutputEvaluator

### Usage Example

```json
{
  "version": "1.0",
  "id": "LLMJudgeStrictJSONSimilarity",
  "evaluatorTypeId": "uipath-llm-judge-output-strict-json-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeStrictJSONSimilarityOutputEvaluator",
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.0
  }
}
```

Test with 4 expected keys:
- Actual output has all 4 keys with similar/identical content
- **Score: 100 - penalties** based on per-key matching
- Example: 1 identical (0), 2 similar (50/4 + 50/4 = 25), 1 wrong (100/4 = 25) → Score: 50

## When to Use vs Other Evaluators

### Use LLM Judge Output when:
- Semantic meaning matters more than exact wording
- Natural language outputs need human-like judgment
- Context and intent are important
- Flexible evaluation criteria needed
- Cost is acceptable for improved accuracy

### Use Deterministic Evaluators when:
- Exact matches are required
- Output format is predictable
- Speed and cost are priorities
- No ambiguity in correctness

### Use Strict JSON when:
- JSON structure is critical
- Each key must be present
- Per-key evaluation needed
- Less flexible than standard LLM Judge

## Configuration Tips

### Temperature Settings

- **0.0** (recommended): Deterministic, consistent results
- **0.1**: Slight variation for nuanced judgment
- **>0.3**: Not recommended (too inconsistent for evaluation)

### Cost Considerations

- Each evaluation makes one LLM API call
- Token usage depends on:
  - Length of actual output
  - Length of expected output
  - Prompt length
- Consider caching for repeated evaluations

## Error Handling

The evaluator will raise `UiPathEvaluationError` if:
- LLM service is unavailable
- Prompt doesn't contain required placeholders
- LLM response cannot be parsed
- Model returns invalid JSON

## Related Evaluators

- [Exact Match Evaluator](exact-match.md): For strict string matching
- [JSON Similarity Evaluator](json-similarity.md): For deterministic JSON comparison
- [Contains Evaluator](contains.md): For substring matching
- [LLM Judge Trajectory Evaluator](../trajectory-based/trajectory.md): For evaluating execution paths

## Next Steps

- [Back to Output-Based Overview](index.md)
- [Running Evaluations](../../running-evaluations.md)
- [Best Practices](../../best-practices.md)
