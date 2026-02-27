# Contains Evaluator

Checks whether the agent's output contains a specific search text (substring matching).

## Overview

**Evaluator ID:** `contains`

**Use Cases:**
- Verify specific keywords or phrases appear in output
- Check for presence of expected content
- Test that error messages contain specific text
- Validate outputs include required information

**Returns:** Binary score (1.0 if found, 0.0 if not found)

## Configuration

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"ContainsEvaluator"` | Display name |
| `case_sensitive` | `bool` | `False` | Case-sensitive search |
| `negated` | `bool` | `False` | If True, passes when text is NOT found |
| `target_output_key` | `str` | `"*"` | Specific field to search (use "*" for entire output) |
| `default_evaluation_criteria` | `dict` | `None` | Default criteria if not specified per test |

**Important:** Agent output must be a dictionary. The value is converted to a string before checking.

## Evaluation Criteria

```json
{
  "search_text": "text-to-search-for"
}
```

## Scoring

- **1.0** - Search text found in output
- **0.0** - Search text not found

## Usage Examples

### Basic Keyword Search

```json
{
  "version": "1.0",
  "id": "ContainsEvaluator",
  "description": "Validates keyword presence",
  "evaluatorTypeId": "uipath-contains",
  "evaluatorConfig": {
    "name": "ContainsEvaluator",
    "case_sensitive": false,
    "targetOutputKey": "response"
  }
}
```

In test: Search for `"Paris"` in response `"The capital of France is Paris."` → **Score: 1.0**

### Case-Sensitive Search

```json
{
  "evaluatorConfig": {
    "name": "ContainsEvaluator",
    "case_sensitive": true,
    "targetOutputKey": "message"
  }
}
```

Search for `"hello"` in `"Hello World"` with case-sensitive=true → **Score: 0.0** (case mismatch)

### Negated Search

Pass when text is NOT present:

```json
{
  "evaluatorConfig": {
    "name": "ContainsEvaluator",
    "negated": true,
    "targetOutputKey": "status"
  }
}
```

Search for `"error"` in `"Success: Operation completed"` with negated=true → **Score: 1.0** (error not found, which is what we want)

### Target Specific Field

Only search within one field:

```json
{
  "evaluatorConfig": {
    "name": "ContainsEvaluator",
    "targetOutputKey": "message"
  }
}
```

Agent output:
```json
{
  "status": "success",
  "message": "User profile updated successfully"
}
```

Search for `"updated"` → Only searches in "message" field → **Score: 1.0**

## Best Practices

1. **Use case-insensitive matching** by default to make tests more robust
2. **Combine with other evaluators** for comprehensive validation
3. **Use negated mode** to ensure error messages or sensitive data are NOT present
4. **Target specific fields** when evaluating structured outputs to reduce false positives
5. **Remember substring matching** - this evaluator uses substring search, not full-text or regex

## Common Use Cases

### Validate Required Keywords

Multiple evaluators for different keywords:

```json
{
  "evaluations": [
    {
      "evaluatorId": "contains-greeting",
      "evaluationCriteria": {"search_text": "hello"}
    },
    {
      "evaluatorId": "contains-name",
      "evaluationCriteria": {"search_text": "John"}
    }
  ]
}
```

### Ensure No Error Messages

Use negated mode:

```json
{
  "evaluatorId": "no-errors",
  "evaluationCriteria": {"search_text": "error"},
  "config": {"negated": true}
}
```

### Email Validation

Check email contains required domain:

```json
{
  "evaluatorId": "email-domain",
  "evaluationCriteria": {"search_text": "@company.com"},
  "config": {"targetOutputKey": "email"}
}
```

## When to Use

✅ Use Contains when:
- Specific keywords must be present
- Partial text matching is sufficient
- Flexible text variations acceptable
- Checking for required information in long responses

❌ Don't use when:
- Exact match required
- Complex pattern matching needed (use regex in custom evaluator)
- Entire JSON structure needs validation (use JSON Similarity)

## When NOT to Use

- For exact text matching (use [Exact Match Evaluator](exact-match.md))
- For complex pattern matching (use custom evaluator with regex)
- For natural language semantic matching (use [LLM Judge](llm-judge-output.md))
- For JSON structure validation (use [JSON Similarity](json-similarity.md))

## Related Evaluators

- [Exact Match Evaluator](exact-match.md): For exact string matching
- [JSON Similarity Evaluator](json-similarity.md): For structural comparison
- [LLM Judge Output Evaluator](llm-judge-output.md): For semantic similarity

## Next Steps

- [Back to Output-Based Overview](index.md)
- [JSON Similarity Evaluator](json-similarity.md)
- [Running Evaluations](../../running-evaluations.md)
