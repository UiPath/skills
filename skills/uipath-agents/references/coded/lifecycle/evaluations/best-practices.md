# Best Practices & Common Patterns

Use these patterns to design effective evaluations for different agent types.

## Evaluation Best Practices

### Do

- Use multiple evaluators when appropriate, combining output- and trajectory-based evaluators for complex agents (for example, `ExactMatchEvaluator` and `JsonSimilarityEvaluator`).
- Create focused eval sets for happy paths, edge cases, errors, and performance.
- Match evaluators to the task: output-based for results, trajectory-based for multi-step execution, and LLM evaluators for natural-language or fuzzy matching.
- Use trajectory evaluators when execution flow, tool usage, or orchestration decisions matter.
- Start development with `ExactMatchEvaluator`; add LLM evaluators for production flexibility as the agent stabilizes.
- Mock all external API calls consistently for deterministic testing, and cache LLM responses in CI/CD.
- Version evaluation sets with semantic versioning in IDs (for example, `calculator-v1`, `calculator-v2`).
- Use descriptive test names and document each test’s purpose.
- Review failed tests and execution traces to determine whether the agent or expectations need correction.

### Don't

- Do not use only `ExactMatchEvaluator` for natural-language output; use `LLMJudgeOutputEvaluator` for semantic variation.
- Do not omit boundary, empty/null, invalid-input, or error scenarios; test 0, minimum, and maximum values.
- Do not use trajectory evaluation when output validation is sufficient; reserve it for cases where the path matters because it is more expensive.
- Do not set overly strict criteria early. Allow flexibility while the agent evolves, then tighten criteria as it stabilizes; start with 80% and improve toward 95%+.
- Do not skip schema validation during test creation; validate inputs to catch invalid data and type mismatches early.
- Do not mix unrelated scenarios in one eval set; separate happy paths from error cases for easier debugging.

## Common Evaluation Patterns

### 1. Calculator/Deterministic Agents

For identical outputs given identical inputs:

- **Primary evaluator:** `ExactMatchEvaluator`
- **Optional secondary evaluator:** `JsonSimilarityEvaluator` for complex outputs
- **Scoring:** 1.0 (pass) or 0.0 (fail); exact match receives no partial credit.

Test basic arithmetic; zero, negative, very large, and decimal values; non-numeric input; missing parameters; and division by zero.

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

### 2. Natural Language Agents

For text, summaries, and other natural-language output:

- **Primary evaluator:** `LLMJudgeOutputEvaluator`
- **Secondary evaluator:** `ContainsEvaluator`
- Test semantic equivalence, required keywords or concepts, and format constraints such as length and required fields.
- Score from 0.0 to 1.0 based on semantic similarity; accept 0.7+ for a good match.

### 3. Multi-Step Orchestration Agents

For agents coordinating tools or services:

- **Primary evaluator:** `LLMJudgeTrajectoryEvaluator`
- **Secondary evaluator:** `JsonSimilarityEvaluator`
- Test expected tool order and arguments, passing one tool’s output to the next, fallback paths, and graceful degradation after failures.

### 4. API Integration Agents

For agents interacting with external APIs:

- **Primary evaluator:** `JsonSimilarityEvaluator`
- **Secondary evaluator:** `ExactMatchEvaluator` for specific fields
- Mock all external API calls using mockito type.
- Test valid responses and formats, pagination, 500/404/403 errors, timeouts, malformed responses, empty and large results, and rate limiting.

## Test Organization

Organize eval sets by scenario:

```
eval-sets/
├── {agent}-happy-path.json
├── {agent}-edge-cases.json
├── {agent}-error-handling.json
└── {agent}-performance.json
```

## CI/CD Integration

Run:

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