# Exact Match Evaluator

Verifies exact string matching between agent output and expected output. This is the most strict deterministic evaluator.

## Overview

**Evaluator ID:** `exact-match`

**Use Cases:**
- Validate exact responses (status codes, IDs)
- Test deterministic outputs
- Ensure precise formatting is maintained
- Verify exact data values

**Returns:** Binary score (1.0 if exact match, 0.0 otherwise)

## Configuration

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"ExactMatchEvaluator"` | Display name |
| `case_sensitive` | `bool` | `False` | Case-sensitive comparison |
| `negated` | `bool` | `False` | If True, passes when outputs do NOT match |
| `target_output_key` | `str` | `"*"` | Specific field to evaluate (use "*" for entire output) |
| `default_evaluation_criteria` | `dict` | `None` | Default expected output if not specified per test |

**Important:** Agent output must always be a dictionary (e.g., `{"result": "value"}`). Use `target_output_key` to extract specific fields.

## Evaluation Criteria

```json
{
  "expected_output": {
    "result": "exact-value-here"
  }
}
```

## Scoring

- **1.0** - Exact match found
- **0.0** - No match

## Usage Examples

### Basic Exact Match

Compare the entire output as a dictionary:

```json
{
  "version": "1.0",
  "id": "ExactMatchEvaluator",
  "description": "Exact string matching validator",
  "evaluatorTypeId": "uipath-exact-match",
  "evaluatorConfig": {
    "name": "ExactMatchEvaluator",
    "targetOutputKey": "*",
    "case_sensitive": false,
    "negated": false,
    "defaultEvaluationCriteria": {
      "expectedOutput": {
        "status": "success",
        "code": 200
      }
    }
  }
}
```

### Case-Sensitive Matching

Fail on case mismatch:

```json
{
  "evaluatorConfig": {
    "name": "ExactMatchEvaluator",
    "case_sensitive": true,
    "targetOutputKey": "status"
  }
}
```

### Target Specific Field

Only compare one field from output:

```json
{
  "evaluatorConfig": {
    "name": "ExactMatchEvaluator",
    "targetOutputKey": "result"
  }
}
```

Agent output `{"result": "approved", "timestamp": "2024-01-01"}` with `expected_output: {"result": "approved"}` → **Score: 1.0** (timestamp ignored)

### Negated Mode

Pass when outputs do NOT match:

```json
{
  "evaluatorConfig": {
    "name": "ExactMatchEvaluator",
    "negated": true,
    "targetOutputKey": "error"
  }
}
```

Agent output `{"error": null}` vs expected `{"error": "validation error"}` → **Score: 1.0** (they don't match, which is what we want)

## Best Practices

1. **Use for deterministic outputs** where exact matches are expected
2. **Consider case sensitivity** - use insensitive mode by default for robustness
3. **Use case-insensitive mode** by default for more robust tests
4. **For structured data**, consider using [JSON Similarity Evaluator](json-similarity.md) instead
5. **Combine with other evaluators** for comprehensive testing
6. **Be careful with whitespace** - exact match includes all whitespace characters

## Common Issues

### Whitespace Sensitivity

Exact Match includes all whitespace:
- `"hello"` ≠ `"hello "` (trailing space)
- `"hello\nworld"` ≠ `"hello world"` (newline vs space)

**Solution:** Trim whitespace in your agent output or use JSON Similarity for tolerance.

### Case Sensitivity

By default, case-insensitive. Enable only if case matters:
```json
{
  "case_sensitive": true
}
```

### Type Mismatch

Expected `"5"` (string) but got `5` (number):
- Case-sensitive: Fails
- Use JSON Similarity if type flexibility needed

## When NOT to Use

- When output can vary slightly but still be correct
- For natural language outputs (use [LLM Judge](llm-judge-output.md) instead)
- When comparing complex JSON structures (use [JSON Similarity](json-similarity.md))
- When partial matches are acceptable (use [Contains](contains.md))

## Related Evaluators

- [Contains Evaluator](contains.md): For partial string matching
- [JSON Similarity Evaluator](json-similarity.md): For flexible JSON comparison
- [LLM Judge Output Evaluator](llm-judge-output.md): For semantic similarity

## Next Steps

- [Back to Output-Based Overview](index.md)
- [JSON Similarity Evaluator](json-similarity.md)
- [Running Evaluations](../../running-evaluations.md)
