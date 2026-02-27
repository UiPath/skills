# JSON Similarity Evaluator

Performs flexible structural comparison of JSON-like outputs using a tree-based matching algorithm.

## Overview

**Evaluator ID:** `json-similarity`

**Use Cases:**
- Compare complex nested JSON structures
- Validate API responses with tolerance for minor differences
- Test structured outputs where exact matches are too strict
- Measure similarity when numeric values may vary slightly

**Returns:** Continuous score from 0.0 to 1.0 (0-100% similarity)

## How It Works

### Tree-Based Matching Algorithm

1. **Tree Structure:** Treats JSON/dictionary as tree with nested objects and arrays
2. **Leaf Comparison:** Only leaf nodes (actual values) are compared using type-specific similarity:
   - **Strings:** Levenshtein distance (edit distance) for textual similarity
   - **Numbers:** Absolute difference with tolerance (within 1% considered similar)
   - **Booleans:** Exact match required (binary comparison)
3. **Structural Recursion:** Recursively traverses and compares:
   - **Objects:** All expected keys (extra keys in actual output ignored)
   - **Arrays:** Elements by position (index-based matching)
4. **Score Calculation:** `matched_leaves / total_leaves`

The final score represents the percentage of matching leaf nodes in the tree structure.

## Configuration

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"JsonSimilarityEvaluator"` | Display name |
| `target_output_key` | `str` | `"*"` | Specific field to evaluate (use "*" for entire output) |
| `default_evaluation_criteria` | `dict` | `None` | Default expected structure |

## Evaluation Criteria

```json
{
  "expected_output": {
    "field1": "value1",
    "nested": {
      "field2": "value2"
    }
  }
}
```

## Scoring

| Score Range | Interpretation |
|-------------|----------------|
| **1.0** | Perfect match (all leaves identical) |
| **0.9-0.99** | Very high similarity (minor differences) |
| **0.7-0.89** | Good similarity (some differences) |
| **0.5-0.69** | Moderate similarity (significant differences) |
| **0.0-0.49** | Low similarity (major differences) |

## Usage Examples

### Basic JSON Comparison

```json
{
  "version": "1.0",
  "id": "JsonSimilarityEvaluator",
  "evaluatorTypeId": "uipath-json-similarity",
  "evaluatorConfig": {
    "name": "JsonSimilarityEvaluator",
    "targetOutputKey": "*"
  }
}
```

Test:
- Input: `{"name": "John Doe", "age": 30, "city": "New York"}`
- Expected: `{"name": "John Doe", "age": 30, "city": "New York"}`
- **Score: 1.0** (perfect match, 3/3 leaves matched)

### Numeric Tolerance

Numbers within ~1% are considered similar:

```json
{
  "temperature": 20.5,
  "humidity": 65
}
```

vs expected:

```json
{
  "temperature": 20.3,
  "humidity": 65
}
```

- Temperature: 20.5 vs 20.3 (0.2 difference, ~1%) → Similar
- Humidity: 65 vs 65 → Exact
- **Score: ~0.99** (very high similarity despite numeric difference)

### String Similarity

Typos don't cause complete failure (Levenshtein distance):

```json
{
  "status": "completed sucessfully"  // typo: "sucessfully" not "successfully"
}
```

vs expected:

```json
{
  "status": "completed successfully"
}
```

- String similarity calculated using edit distance
- **Score: ~0.95** (high similarity despite typo)

### Nested Structures

Recursively compares all levels:

```json
{
  "user": {
    "name": "Alice",
    "profile": {
      "age": 25,
      "location": "Paris"
    }
  },
  "status": "active"
}
```

All fields from different nesting levels are compared as leaf nodes.

### Array Comparison

Arrays compared by position (index-based):

```json
{
  "items": ["apple", "banana", "orange"]
}
```

vs expected:

```json
{
  "items": ["apple", "banana", "grape"]
}
```

- Position 0: "apple" = "apple" ✓
- Position 1: "banana" = "banana" ✓
- Position 2: "orange" ≠ "grape" ✗
- **Score: ~0.67** (2/3 correct)

### Handling Extra Keys

Extra keys in actual output are ignored:

```json
{
  "name": "Bob",
  "age": 30,
  "extra_field": "ignored"
}
```

vs expected:

```json
{
  "name": "Bob",
  "age": 30
}
```

Only expected keys evaluated → **Score: 1.0**

### Target Specific Field

Only compare one field from output:

```json
{
  "evaluatorConfig": {
    "name": "JsonSimilarityEvaluator",
    "targetOutputKey": "result"
  }
}
```

Agent output:
```json
{
  "result": {"score": 95, "passed": true},
  "metadata": {"timestamp": "2024-01-01"}
}
```

Only "result" field compared → metadata ignored.

## Best Practices

1. **Use for structured data** like JSON, dictionaries, or objects
2. **Set score thresholds** based on your tolerance (e.g., require score ≥ 0.9)
3. **Combine with exact match** for critical fields that must match exactly
4. **Only expected keys matter** - extra keys in actual output are automatically ignored
5. **Consider array order** - elements are compared by position
6. **Useful for API testing** where responses may have minor variations

## When to Use vs Other Evaluators

**Use JSON Similarity when:**
- Comparing complex nested structures
- Minor numeric differences are acceptable
- String typos shouldn't cause complete failure
- You need a granular similarity score
- API responses may have minor variations

**Use Exact Match when:**
- Output must match precisely
- No tolerance for any differences
- Simple string comparison needed

**Use LLM Judge when:**
- Semantic meaning matters more than structure
- Natural language comparison needed
- Context and intent should be considered

## Common Issues

### Array Order Matters

If order shouldn't matter, use custom evaluator with set-based comparison instead.

### Missing Fields

If actual output lacks expected field, it scores lower than with all fields present.

### Type Mismatch

`5` (number) vs `"5"` (string) are compared differently:
- Numbers use numeric tolerance
- Strings use Levenshtein distance
- Result: Different similarity scores

### Floating Point Precision

Numbers with floating point differences:
- `3.14159` vs `3.14160` → Very high similarity (within 1%)

## Performance

- **Speed:** Fast (no LLM calls, pure algorithmic)
- **Complexity:** O(n) where n = total number of leaf nodes
- **Memory:** Efficient (doesn't require full tree materialization)

## Related Evaluators

- [Exact Match Evaluator](exact-match.md): For strict matching
- [Contains Evaluator](contains.md): For substring matching
- [LLM Judge Output Evaluator](llm-judge-output.md): For semantic comparison

## Next Steps

- [Back to Output-Based Overview](index.md)
- [LLM Judge Evaluator](llm-judge-output.md)
- [Running Evaluations](../../running-evaluations.md)
