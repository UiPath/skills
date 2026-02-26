# Best Practices & Common Patterns

This guide covers best practices for effective evaluation design and common patterns for different agent types.

## Evaluation Best Practices

### Do ✅

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

### Don't ❌

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

- **Use generic evaluator IDs**
  - Don't use generic names like "evaluator1"
  - Use descriptive names: "SumCalculatorEvaluator"
  - Makes eval sets self-documenting

- **Ignore performance metrics**
  - Monitor execution times
  - Track performance trends
  - Identify bottlenecks

## Common Evaluation Patterns

### Pattern 1: Calculator/Deterministic Agents

For agents that always produce the same output for the same input:

**Test Organization:**
```
eval-sets/
├── calculator-happy-path.json       # Normal operations
├── calculator-edge-cases.json       # Boundary values
└── calculator-error-cases.json      # Invalid inputs
```

**Evaluator Selection:**
- **Primary:** ExactMatchEvaluator
- **Secondary:** (optional) JsonSimilarityEvaluator for complex outputs

**Test Cases:**
```
Happy Path:
- Basic addition, subtraction, multiplication, division
- Standard values (1-100)

Edge Cases:
- Zero values
- Negative numbers
- Very large numbers (100000+)
- Decimal results
- Division by zero (error case)

Error Scenarios:
- Non-numeric input
- Missing parameters
- Invalid operator
```

**Scoring:**
- 1.0 (pass) or 0.0 (fail)
- No partial credit for exact match

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

**Test Organization:**
```
eval-sets/
├── nlp-agent-semantics.json         # Semantic correctness
├── nlp-agent-keyword-checks.json    # Required keywords
└── nlp-agent-length-constraints.json # Output size limits
```

**Evaluator Selection:**
- **Primary:** LLMJudgeOutputEvaluator (semantic matching)
- **Secondary:** ContainsEvaluator (keyword checks)
- **Tertiary:** (optional) JsonSimilarityEvaluator for structured outputs

**Test Cases:**
```
Semantic Equivalence:
- Different phrasings of same concept
- Variations in word order
- Synonymous expressions

Keyword Validation:
- Must contain specific terms
- Must mention key concepts
- Should include certain information

Format Validation:
- Output length constraints
- Specific JSON structure
- Required fields present
```

**Scoring:**
- 0.0-1.0 range based on semantic similarity
- Accept 0.7+ for good semantic match

**Example Eval Set:**

```json
{
  "version": "1.0",
  "id": "summarizer-nlp",
  "name": "Document Summarizer NLP Tests",
  "evaluatorRefs": [
    "LLMJudgeOutputEvaluator",
    "ContainsEvaluator"
  ],
  "evaluations": [
    {
      "id": "test-1-semantic-match",
      "name": "Semantic equivalence test",
      "inputs": {
        "text": "The quick brown fox jumps over the lazy dog"
      },
      "evaluationCriterias": {
        "LLMJudgeOutputEvaluator": {
          "expectedOutput": {
            "summary": "A brief description mentioning a fox and jumping motion"
          }
        }
      }
    },
    {
      "id": "test-2-keywords",
      "name": "Verify key concepts present",
      "inputs": {
        "text": "Machine learning is a subset of artificial intelligence"
      },
      "evaluationCriterias": {
        "ContainsEvaluator": {
          "searchText": "machine learning"
        }
      }
    }
  ]
}
```

### Pattern 3: Multi-Step Orchestration Agents

For agents that coordinate multiple tools or services:

**Test Organization:**
```
eval-sets/
├── orchestrator-happy-path.json     # Normal workflows
├── orchestrator-tool-sequences.json # Specific execution paths
└── orchestrator-error-handling.json # Fallback paths
```

**Evaluator Selection:**
- **Primary:** TrajectoryEvaluator (execution path validation)
- **Secondary:** JsonSimilarityEvaluator (output structure)
- **Tertiary:** (optional) LLMJudgeOutputEvaluator (semantic check)

**Test Cases:**
```
Tool Sequence Validation:
- Tools called in expected order
- Correct tool chosen for each step
- Arguments passed correctly

Tool Interaction:
- Output of one tool becomes input to next
- Data flows correctly through pipeline
- State maintained between steps

Error Handling:
- Fallback paths when tool fails
- Graceful degradation
- Error reporting
```

**Scoring:**
- Trajectory: 0.0-1.0 based on execution path match
- Output: 0.0-1.0 based on structure match
- Average across evaluators

**Example Eval Set:**

```json
{
  "version": "1.0",
  "id": "orchestrator-workflow",
  "name": "Orchestrator Workflow Tests",
  "evaluatorRefs": [
    "TrajectoryEvaluator",
    "JsonSimilarityEvaluator"
  ],
  "evaluations": [
    {
      "id": "test-1-pipeline",
      "name": "Data pipeline execution",
      "inputs": {
        "dataSource": "database",
        "operation": "transform"
      },
      "evaluationCriterias": {
        "TrajectoryEvaluator": {
          "expectedAgentBehavior": "Agent should call fetch_data, then transform_data, then save_results in that order"
        },
        "JsonSimilarityEvaluator": {
          "expectedOutput": {
            "status": "complete",
            "recordsProcessed": 1000,
            "transformedData": {}
          }
        }
      }
    }
  ]
}
```

### Pattern 4: API Integration Agents

For agents that interact with external APIs:

**Test Organization:**
```
eval-sets/
├── api-agent-success-paths.json     # Successful API responses
├── api-agent-error-responses.json   # API errors
└── api-agent-retry-logic.json       # Retry mechanisms
```

**Evaluator Selection:**
- **Primary:** JsonSimilarityEvaluator (response structure)
- **Secondary:** ExactMatchEvaluator (specific fields)
- **Tertiary:** (optional) TrajectoryEvaluator (request patterns)

**Mocking Strategy:**
- Mock all external API calls
- Use function mocking (mockito type)
- Simulate various response types

**Test Cases:**
```
Success Paths:
- Valid API responses
- Different response formats
- Pagination handling

Error Handling:
- API errors (500, 404, 403)
- Timeout handling
- Malformed responses

Edge Cases:
- Empty results
- Large responses
- Rate limiting
```

**Example Eval Set:**

```json
{
  "version": "1.0",
  "id": "api-agent-integration",
  "name": "API Integration Tests",
  "evaluatorRefs": ["JsonSimilarityEvaluator"],
  "evaluations": [
    {
      "id": "test-1-fetch-user",
      "name": "Fetch user from API",
      "inputs": {"userId": "123"},
      "evaluationCriterias": {
        "JsonSimilarityEvaluator": {
          "expectedOutput": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com"
          }
        }
      },
      "mockingStrategy": {
        "type": "mockito",
        "behaviors": [
          {
            "function": "api_call",
            "arguments": {
              "args": ["https://api.example.com/users/123"],
              "kwargs": {}
            },
            "then": [
              {
                "type": "return",
                "value": {
                  "id": "123",
                  "name": "John Doe",
                  "email": "john@example.com"
                }
              }
            ]
          }
        ]
      }
    },
    {
      "id": "test-2-api-error",
      "name": "Handle API error",
      "inputs": {"userId": "invalid"},
      "evaluationCriterias": {
        "JsonSimilarityEvaluator": {
          "expectedOutput": {
            "error": "User not found"
          }
        }
      },
      "mockingStrategy": {
        "type": "mockito",
        "behaviors": [
          {
            "function": "api_call",
            "arguments": {
              "args": ["https://api.example.com/users/invalid"],
              "kwargs": {}
            },
            "then": [
              {
                "type": "raise",
                "value": {
                  "_target_": "Exception",
                  "args": ["404 Not Found"]
                }
              }
            ]
          }
        ]
      }
    }
  ]
}
```

## Test Case Organization Tips

### By Scenario Type

```
eval-sets/
├── {agent}-happy-path.json
├── {agent}-edge-cases.json
├── {agent}-error-handling.json
└── {agent}-performance.json
```

### By Feature

```
eval-sets/
├── {agent}-feature-a.json
├── {agent}-feature-b.json
└── {agent}-feature-c.json
```

### By Evaluator Type

```
eval-sets/
├── {agent}-exact-match.json
├── {agent}-semantic.json
└── {agent}-trajectory.json
```

## Performance Optimization

### Test Execution

- **Use appropriate worker count**
  - 4 workers: good default
  - 8 workers: large evaluation sets
  - 1 worker: debugging failures

- **Enable caching for LLM evaluators**
  ```bash
  uv run uipath eval <agent> <eval-file> --mocker-cache
  ```
  - Faster re-runs
  - Lower API costs
  - Reproducible results

- **Run subset during development**
  - Create separate "smoke test" eval sets
  - Use for quick validation
  - Run full suite before committing

### Test Design

- **Minimize external dependencies**
  - Mock external API calls
  - Avoid real database calls
  - Use test data, not production data

- **Balance coverage vs. execution time**
  - Comprehensive test suite
  - But not so large it's slow
  - Run full suite in CI, smoke tests locally

- **Prioritize critical paths**
  - Test most important workflows first
  - Test happy path thoroughly
  - Add edge cases incrementally

## Maintenance

### Keeping Tests Current

- **Update when agent changes**
  - Agent input/output schema changes
  - New features added
  - Bug fixes require test updates

- **Review regularly**
  - Remove obsolete tests
  - Update test data
  - Refactor for clarity

- **Version evaluation sets**
  - Track changes over time
  - Maintain backward compatibility
  - Document breaking changes

### CI/CD Integration

- **Run evaluations in CI/CD**
  ```bash
  uv run uipath eval <agent> evaluations/eval-sets/smoke-tests.json \
    --workers 4 \
    --mocker-cache \
    --output-file eval-results.json
  ```

- **Fail pipeline on test failures**
  - Set clear pass/fail criteria
  - Monitor score trends
  - Alert on regressions

## Quick Reference

### Evaluation Set Template

```json
{
  "version": "1.0",
  "id": "my-eval-set",
  "name": "My Evaluation Set",
  "description": "Description of test scenarios",
  "evaluatorRefs": ["EvaluatorId"],
  "evaluations": [
    {
      "id": "test-1",
      "name": "Test name",
      "inputs": {},
      "evaluationCriterias": {
        "EvaluatorId": {}
      }
    }
  ]
}
```

### Evaluator Selection Quick Guide

| Agent Type | Primary Evaluator | Secondary | Notes |
|-----------|------------------|-----------|-------|
| Calculator | ExactMatch | - | Deterministic |
| Text Generator | LLMJudge | Contains | Natural language |
| Orchestrator | Trajectory | JsonSimilarity | Multi-step flow |
| API Client | JsonSimilarity | ExactMatch | Structured data |
| Summarizer | LLMJudge | Contains | Semantic matching |

## Next Steps

- [Creating Evaluations](creating-evaluations.md) - Start building tests
- [Evaluation Sets](evaluation-sets.md) - Structure your test files
- [Running Evaluations](running-evaluations.md) - Execute and analyze results
- [Evaluators Guide](evaluators/README.md) - Deep dive into evaluator types
