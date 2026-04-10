# Best Practices & Common Patterns

This guide covers best practices for effective evaluation design and common patterns for different agent types.

## Evaluation Best Practices

### Do

- **Use multiple evaluators** for comprehensive validation
  - Don't rely on a single evaluator
  - Combine output-based and trajectory-based evaluators for complex agents
  - Example: Use both ExactMatchEvaluator and JsonSimilarityEvaluator

- **Create separate eval sets for different scenarios**
  - Happy path scenarios
  - Edge cases
  - Error scenarios
  - Performance tests
  - This makes it easier to maintain and debug

- **Mix evaluator types appropriately**
  - Output-based evaluators for result validation
  - Trajectory evaluators for multi-step agents
  - LLM evaluators for natural language outputs

- **Use trajectory evaluators for multi-step agents**
  - Validates execution flow and tool usage
  - Ensures agent takes expected decision paths
  - Useful for orchestration agents

- **Use LLM evaluators for natural language or fuzzy matching**
  - Better for semantic equivalence
  - More flexible than exact matching
  - Handles variations in wording

- **Start with ExactMatch, then add flexibility**
  - Begin with strict ExactMatchEvaluator during development
  - Add LLM evaluators for production as needed
  - Allows refinement as agent matures

- **Mock external dependencies consistently**
  - Mock all external API calls
  - Use mocking for deterministic testing
  - Cache LLM responses in CI/CD

- **Version your evaluation sets**
  - Use semantic versioning in IDs
  - Track changes over time
  - Example: `calculator-v1`, `calculator-v2`

- **Document test purposes clearly**
  - Use descriptive test names
  - Explain what each test validates
  - Make it easy for others to understand

- **Review failed tests carefully**
  - Examine execution traces
  - Understand why tests failed
  - Fix either the agent or test expectations

### Don't

- **Use only ExactMatch for natural language outputs**
  - Too strict, fails on minor variations
  - Use LLMJudgeOutputEvaluator instead

- **Forget to test edge cases and error scenarios**
  - Test boundary values (0, min, max)
  - Test empty/null values
  - Test invalid inputs

- **Use trajectory evaluators when output-based is sufficient**
  - Trajectory evaluation is more expensive
  - Only use when execution path matters
  - For simple agents, output validation is enough

- **Set too strict criteria early in development**
  - Allow flexibility while agent is evolving
  - Tighten criteria as agent stabilizes
  - Start with 80%, improve to 95%+

- **Skip schema validation during test creation**
  - Always validate inputs against schema
  - Prevents invalid test data
  - Catches type mismatches early

- **Mix unrelated tests in one eval set**
  - Keep eval sets focused and organized
  - Separate happy path from error cases
  - Makes debugging easier

## Common Evaluation Patterns

### Pattern 1: Calculator/Deterministic Agents

For agents that always produce the same output for the same input:

**Evaluator Selection:**
- **Primary:** ExactMatchEvaluator
- **Secondary:** (optional) JsonSimilarityEvaluator for complex outputs

**Test Cases:**
```
Happy Path: Basic addition, subtraction, multiplication, division
Edge Cases: Zero values, negative numbers, very large numbers, decimal results
Error Scenarios: Non-numeric input, missing parameters, division by zero
```

**Scoring:** 1.0 (pass) or 0.0 (fail). No partial credit for exact match.

**Example Eval Set:**

```json
{
  "version": "1.0",
  "id": "calculator-comprehensive",
  "name": "Calculator Comprehensive Tests",
  "evaluatorRefs": ["ExactMatchEvaluator"],
  "evaluations": [
    {
      "id": "test-1-add",
      "name": "Basic addition",
      "inputs": {"a": 5, "b": 3},
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": {"result": "8"}
        }
      }
    },
    {
      "id": "test-2-divide-by-zero",
      "name": "Error handling",
      "inputs": {"a": 10, "b": 0},
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": {"error": "Division by zero"}
        }
      }
    }
  ]
}
```

### Pattern 2: Natural Language Agents

For agents that generate text, summaries, or natural language output:

**Evaluator Selection:**
- **Primary:** LLMJudgeOutputEvaluator (semantic matching)
- **Secondary:** ContainsEvaluator (keyword checks)

**Test Cases:**
```
Semantic Equivalence: Different phrasings of same concept, synonymous expressions
Keyword Validation: Must contain specific terms, key concepts
Format Validation: Output length constraints, required fields
```

**Scoring:** 0.0-1.0 range based on semantic similarity. Accept 0.7+ for good match.

### Pattern 3: Multi-Step Orchestration Agents

For agents that coordinate multiple tools or services:

**Evaluator Selection:**
- **Primary:** LLMJudgeTrajectoryEvaluator (execution path validation)
- **Secondary:** JsonSimilarityEvaluator (output structure)

**Test Cases:**
```
Tool Sequence: Tools called in expected order, correct arguments
Tool Interaction: Output of one tool becomes input to next
Error Handling: Fallback paths when tool fails, graceful degradation
```

### Pattern 4: API Integration Agents

For agents that interact with external APIs:

**Evaluator Selection:**
- **Primary:** JsonSimilarityEvaluator (response structure)
- **Secondary:** ExactMatchEvaluator (specific fields)

**Mocking Strategy:** Mock all external API calls using mockito type.

**Test Cases:**
```
Success Paths: Valid API responses, different formats, pagination
Error Handling: API errors (500, 404, 403), timeouts, malformed responses
Edge Cases: Empty results, large responses, rate limiting
```

## Test Organization

### By Scenario Type

```
eval-sets/
├── {agent}-happy-path.json
├── {agent}-edge-cases.json
├── {agent}-error-handling.json
└── {agent}-performance.json
```

## CI/CD Integration

```bash
uip codedagent eval <agent> evaluations/eval-sets/smoke-tests.json \
  --workers 4 \
  --mocker-cache \
  --output-file eval-results.json
```

## Evaluator Selection Quick Guide

| Agent Type | Primary Evaluator | Secondary | Notes |
|-----------|------------------|-----------|-------|
| Calculator | ExactMatch | - | Deterministic |
| Text Generator | LLMJudge | Contains | Natural language |
| Orchestrator | LLMJudgeTrajectory | JsonSimilarity | Multi-step flow |
| API Client | JsonSimilarity | ExactMatch | Structured data |
| Summarizer | LLMJudge | Contains | Semantic matching |
