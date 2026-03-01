# UiPath Evaluations

Create comprehensive test cases and execute evaluations for your UiPath agents using the UiPath evaluation framework.

## What is an Evaluation?

Evaluations assess agent performance by comparing actual outputs against expected results. The framework provides tools to create test cases, define evaluation criteria, and run comprehensive test suites.

## Two Types of Evaluators

**📊 Output-Based Evaluators** - Measure final results and validate outputs:
- ExactMatchEvaluator
- JsonSimilarityEvaluator
- LLMJudgeOutputEvaluator
- ContainsEvaluator

**🔄 Trajectory-Based Evaluators** - Examine execution patterns and decision sequences:
- TrajectoryEvaluator

## Documentation

### Detailed Guides

- **[Creating Evaluations](evaluations/creating-evaluations.md)**
  - Define evaluation details
  - Collect test cases
  - Organize by scenario (happy path, edge cases, errors)
  - Mock external calls

- **[Evaluators Guide](evaluations/evaluators/README.md)**
  - All available evaluator types
  - Configuration options
  - Choosing the right evaluator
  - Creating custom evaluators
  - Evaluation scoring

- **[Evaluation Sets](evaluations/evaluation-sets.md)**
  - Evaluation set file structure
  - Test case schema
  - Complete examples
  - Mocking strategies
  - Best practices for organization

- **[Running Evaluations](evaluations/running-evaluations.md)**
  - Execution configuration
  - Understanding results
  - Detailed analysis
  - Performance optimization
  - Troubleshooting

- **[Best Practices & Common Patterns](evaluations/best-practices.md)**
  - Evaluation best practices
  - Common patterns by agent type
  - Test organization strategies
  - Performance optimization
  - Quick reference guides

## Generated File Structure

```
evaluations/
├── eval-sets/
│   ├── <eval-name>.json
│   └── <another-eval>.json
└── evaluators/
    ├── exact-match.json
    ├── json-similarity.json
    └── llm-judge-semantic-similarity.json
```

## Evaluator Setup & Registration

### Creating Evaluator Files

Evaluators must be created in `evaluations/evaluators/` directory. Each evaluator file defines:
- **id** - Unique identifier (referenced in `evaluatorRefs` in eval sets)
- **evaluatorTypeId** - Built-in evaluator type (e.g., `uipath-exact-match`)
- **evaluatorConfig** - Type-specific configuration

The evaluator's `id` field **must match** what you reference in your evaluation set's `evaluatorRefs` array.

For configuration examples for each evaluator type, see:
- **[Exact Match Evaluator](evaluations/evaluators/output-based/exact-match.md)** - Deterministic outputs
- **[Contains Evaluator](evaluations/evaluators/output-based/contains.md)** - Keyword validation
- **[JSON Similarity Evaluator](evaluations/evaluators/output-based/json-similarity.md)** - JSON structures
- **[LLM Judge Output Evaluator](evaluations/evaluators/output-based/llm-judge-output.md)** - Semantic matching
- **[Trajectory Evaluator](evaluations/evaluators/trajectory-based/trajectory.md)** - Execution flow validation

### Evaluator Discovery

Evaluators are **auto-discovered** from the `evaluations/evaluators/` directory:
1. Place evaluator JSON files in `evaluations/evaluators/`
2. The `id` field in the file must match `evaluatorRefs` in your eval sets
3. When you run `uv run uipath eval`, the framework loads all evaluators automatically

### Reference by ID

In your evaluation sets, reference evaluators by their `id`:
```json
{
  "evaluatorRefs": ["ExactMatchEvaluator", "JsonSimilarityEvaluator"],
  "evaluations": [...]
}
```

### Built-in Evaluator Types

Available `evaluatorTypeId` values:
- `uipath-exact-match` → ExactMatchEvaluator
- `uipath-contains` → ContainsEvaluator
- `uipath-json-similarity` → JsonSimilarityEvaluator
- `uipath-llm-judge-output` → LLMJudgeOutputEvaluator
- `uipath-trajectory` → TrajectoryEvaluator

See [Evaluators Guide](evaluations/evaluators/README.md) for configuration options for each type.

## Quick-Start Examples

### Calculator/Deterministic Agent

**Step 1: Set up evaluator**

Create `evaluations/evaluators/exact-match.json` by following the [Exact Match Evaluator guide](evaluations/evaluators/output-based/exact-match.md).

**Step 2: Create evaluation set**

Create `evaluations/eval-sets/calculator-tests.json` by following the [Evaluation Sets guide](evaluations/evaluation-sets.md). Reference `ExactMatchEvaluator` in the `evaluatorRefs` array.

**Step 3: Run evaluations**
```bash
uv run uipath eval main evaluations/eval-sets/calculator-tests.json --workers 4
```

## Common Patterns at a Glance

### Calculator/Deterministic Agents
```
Evaluators: ExactMatchEvaluator
Tests: Happy path, boundary values, error cases
Scoring: 1.0 (pass) or 0.0 (fail)
```
See [Best Practices](evaluations/best-practices.md#pattern-1-calculatordeterministic-agents)

### Natural Language Agents
```
Evaluators: LLMJudgeOutputEvaluator, ContainsEvaluator
Tests: Semantic equivalence, required keywords, various phrasings
Scoring: 0.0-1.0 range based on semantic similarity
```
See [Best Practices](evaluations/best-practices.md#pattern-2-natural-language-agents)

### Multi-Step Orchestration Agents
```
Evaluators: TrajectoryEvaluator, JsonSimilarityEvaluator
Tests: Tool sequences, decision flows, output structure
Scoring: 0.0-1.0 based on execution path and output match
```
See [Best Practices](evaluations/best-practices.md#pattern-3-multi-step-orchestration-agents)

### API Integration Agents
```
Evaluators: JsonSimilarityEvaluator, ExactMatchEvaluator
Tests: Success paths, error responses, mocked API calls
Scoring: 0.0-1.0 based on response structure match
```
See [Best Practices](evaluations/best-practices.md#pattern-4-api-integration-agents)

## Key Concepts

All evaluators return numeric scores: **1.0** (perfect pass), **0.5-0.9** (partial success), **0.0** (failure). Results also include justification, execution metrics, and complete traces.

For detailed guidance on test case organization, schema validation, and scoring interpretation, see [Creating Evaluations](evaluations/creating-evaluations.md) and [Running Evaluations](evaluations/running-evaluations.md).

## Mocking External Calls with `@mockable()`

Sometimes your agent calls external APIs or functions. The `@mockable()` decorator enables mocking during evaluations so you can test agent logic without making real external calls.

### Using `@mockable()`

Apply `@mockable()` to any function that calls an external service. Define `example_calls` to provide deterministic return values during evaluations:

```python
from uipath.testing import mockable

@mockable(example_calls=[
    {"args": {"query": "weather in NYC"}, "return_value": {"temp": 72, "condition": "sunny"}},
    {"args": {"query": "weather in London"}, "return_value": {"temp": 55, "condition": "cloudy"}},
])
def fetch_weather(query: str) -> dict:
    """In production, calls a real weather API. During evaluations, returns mock data."""
    return call_weather_api(query)
```

**Key points:**
- `example_calls` — list of dicts with `args` (input matching) and `return_value` (mock output)
- During evaluations, if the function is called with matching args, the mock return value is used
- During normal execution (`uv run uipath run`), the real function runs as usual
- Combine with `@traced()` for both observability and testability

### Function Mocking
Mock specific function calls with return values or exceptions.

### LLM Call Mocking
Mock LLM interactions without making real API calls.

See [Evaluation Sets](evaluations/evaluation-sets.md#mocking-strategies) for detailed examples.

## Integration with UiPath Cloud

Results can be reported to UiPath Cloud for monitoring, integrated with CI/CD pipelines, compared with previous runs, and used for performance tracking. See [Running Evaluations](evaluations/running-evaluations.md) for details.

For comprehensive best practices, patterns by agent type, and optimization tips, see [Best Practices](evaluations/best-practices.md).

## Additional Resources

For detailed information about the evaluation framework, scoring, and advanced features:
https://uipath.github.io/uipath-python/eval/
