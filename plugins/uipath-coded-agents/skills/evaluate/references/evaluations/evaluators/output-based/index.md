# Output-Based Evaluators

Output-based evaluators measure final results and validate what your agent returns. These evaluators focus on the outputs produced by your agent, not how it produced them.

## Overview

Output-based evaluators are useful for:
- Validating agent outputs against expected results
- Testing deterministic and non-deterministic outputs
- Checking for required keywords or content
- Validating JSON structure and content similarity

## Available Output-Based Evaluators

### 1. Exact Match Evaluator
**[Full Guide →](exact-match.md)**

Verifies exact string matching between agent output and expected output.

- **Best for:** Deterministic outputs, status codes, calculator agents
- **Score:** Binary (1.0 or 0.0)
- **Configuration:** case_sensitive, negated, target_output_key
- **Speed:** Very fast (no LLM calls)

### 2. Contains Evaluator
**[Full Guide →](contains.md)**

Checks if output contains specific search text.

- **Best for:** Keyword validation, error message checking
- **Score:** Binary (1.0 or 0.0)
- **Configuration:** case_sensitive, negated, target_output_key, search_text
- **Speed:** Very fast (no LLM calls)

### 3. JSON Similarity Evaluator
**[Full Guide →](json-similarity.md)**

Performs flexible structural comparison of JSON-like outputs.

- **Best for:** Complex JSON responses, API validation
- **Score:** Continuous (0.0-1.0)
- **Configuration:** target_output_key
- **Algorithm:** Tree-based matching with type-specific similarity
- **Speed:** Fast (no LLM calls)

### 4. LLM Judge Output Evaluator
**[Full Guide →](llm-judge-output.md)**

Uses Language Models to assess semantic similarity of outputs.

- **Best for:** Natural language outputs, semantic equivalence
- **Score:** Continuous (0.0-1.0)
- **Configuration:** model, temperature, prompt, target_output_key
- **Speed:** Slower (LLM API calls)
- **Cost:** Depends on LLM usage

### LLM Judge Strict JSON Similarity
**[In LLM Judge Guide →](llm-judge-output.md#llm-judge-strict-json-similarity)**

Variant of LLM Judge with per-key matching and penalty-based scoring.

- **Best for:** Strict JSON validation with LLM intelligence
- **Score:** Continuous (0.0-1.0)
- **Scoring:** Penalty-based per key (missing/wrong keys heavily penalized)

## Comparison Table

| Feature | Exact Match | Contains | JSON Similarity | LLM Judge |
|---------|------------|----------|-----------------|-----------|
| **Speed** | ⚡⚡⚡ Very Fast | ⚡⚡⚡ Very Fast | ⚡⚡ Fast | 🐢 Slow (LLM) |
| **Cost** | Free | Free | Free | API Cost |
| **Deterministic** | Yes | Yes | Yes | No (varies by temp) |
| **Best for** | Exact outputs | Keywords | JSON structures | Natural language |
| **Tolerance** | None | None | Type-specific | High (semantic) |
| **Nested JSON** | Limited | No | Yes | Yes |
| **String Typos** | Fail | Fail | High tolerance | High tolerance |
| **Numeric Tolerance** | None | N/A | ~1% tolerance | Yes |

## Common Patterns

### Pattern 1: Simple Output Validation
```
Use Exact Match when:
- Agent produces status codes
- Output must be precise
- Exact format required
- Testing deterministic functions
```

### Pattern 2: Keyword Validation
```
Use Contains when:
- Must verify specific keywords present
- Checking for required information
- Validating error messages
- Partial matches acceptable
```

### Pattern 3: Complex JSON Responses
```
Use JSON Similarity when:
- Agent returns JSON structures
- Minor differences acceptable
- Nested objects present
- Numeric values may vary slightly
```

### Pattern 4: Natural Language Assessment
```
Use LLM Judge when:
- Agent generates text
- Multiple phrasings acceptable
- Semantic meaning matters
- Quality assessment needed
```

## When to Use Output-Based vs Others

**Output-Based Evaluators validate:**
- What the agent produces (final results)
- Correctness of outputs
- Presence of required content
- Structure and format of responses

**Trajectory-Based Evaluators validate:**
- How the agent produces results
- Tool usage and sequencing
- Decision-making process
- Execution flow

**Use both together for comprehensive validation:**
1. Output-based to verify correctness
2. Trajectory-based to verify process

## Best Practices

✅ **Do:**
- Start with simpler evaluators (Exact Match, Contains)
- Add JSON Similarity for structured data
- Use LLM Judge for natural language
- Combine multiple evaluators for robustness
- Set appropriate score thresholds

❌ **Don't:**
- Use only Exact Match for flexible outputs
- Use LLM Judge for simple deterministic checks (waste of cost/time)
- Mix incompatible evaluators
- Skip testing with edge cases

## Next Steps

- **Exact Matching?** See [Exact Match Evaluator](exact-match.md)
- **Keyword Validation?** See [Contains Evaluator](contains.md)
- **JSON Data?** See [JSON Similarity Evaluator](json-similarity.md)
- **Natural Language?** See [LLM Judge Evaluator](llm-judge-output.md)
- **Back to Overview?** See [Evaluators Overview](../README.md)
