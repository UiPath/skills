# Creating Evaluations

This guide walks you through the process of creating comprehensive test cases for your UiPath agents.

## Overview

Creating evaluations involves defining test cases that validate your agent's behavior. Each evaluation set contains multiple test cases with inputs, expected outputs, and evaluation criteria.

## Workflow

### Phase 1: Setup Check

Before creating evaluations, ensure your project has:

- `uipath.json` - Project configuration
- `entry-points.json` - Agent definitions
- `evaluations/` directory for test cases

If missing, create an agent first. See the [Creating Agents](/uipath-coded-agents:build) guide for setup instructions.

### Phase 2: Define Evaluation Details

You'll be asked for:

- **Evaluation Set Name** - Identifier for this evaluation set
- **Description** - What scenarios this covers
- **Target Agent** - Which agent to test
- **Number of Test Cases** - How many tests to create

### Phase 3: Collect Test Cases

For each test case, you'll guide through:

- **Inputs** - Based on agent's input schema with validation
- **Expected Output** - What the agent should return
- **Evaluation Criteria** - How to validate using available evaluators
- **Test Metadata** - ID, name, and purpose

## Test Metadata

Each test case requires:

- **id** - Unique identifier within the evaluation set
- **name** - Human-readable description of what this test validates
- **purpose** - What aspect of the agent is being tested

Good naming examples:
- `test-1-basic-addition` - Basic functionality test
- `test-2-large-numbers` - Boundary value test
- `test-3-negative-input` - Edge case test
- `test-4-invalid-type` - Error handling test

## Input Validation

Inputs are validated against your agent's input schema defined in `entry-points.json`:

- Required fields must be provided
- Values must match the expected types
- Complex objects follow their schema definitions

## Expected Output

Define what your agent should return:

- For simple outputs: a string or number
- For complex outputs: a JSON object matching your agent's output schema
- Multiple output fields can be specified

## Evaluation Criteria

Each test case can use multiple evaluators. For each evaluator, provide:

- **Evaluator ID** - Which evaluator to use (e.g., "ExactMatchEvaluator")
- **Evaluation-specific criteria** - Parameters for that evaluator

Examples:

**For ExactMatchEvaluator:**
```json
"expectedOutput": {
  "result": "5.0"
}
```

**For ContainsEvaluator:**
```json
"searchText": "success"
```

**For JsonSimilarityEvaluator:**
```json
"expectedOutput": {
  "result": 5.0,
  "status": "complete"
}
```

**For TrajectoryEvaluator:**
```json
"expectedAgentBehavior": "The agent should call the calculator tool once and return the result."
```

## Organizing Test Cases

Organize your test cases by scenario:

### Happy Path Tests

Tests for normal operations with typical inputs:
- Expected successful outcomes
- Standard use cases
- Typical input ranges

Example: A calculator agent being given two positive numbers to add.

### Edge Case Tests

Tests for boundary conditions and unusual inputs:
- Boundary values (0, min, max)
- Empty/null values
- Large datasets
- Special characters
- Single vs. multiple items

Example: Calculator with zero, negative numbers, very large numbers.

### Error Scenario Tests

Tests for invalid inputs and error handling:
- Invalid input types
- Missing required fields
- Out-of-range values
- Expected error messages
- Handling of malformed data

Example: Calculator given non-numeric input or invalid format.

## Best Practices for Test Cases

### Be Specific

❌ Bad: "test-output" - vague, doesn't describe what's being tested

✅ Good: "test-large-json-output" - clear about what scenario is tested

### Test One Thing Per Case

❌ Bad: Testing multiple scenarios in one test case

✅ Good: Separate tests for each distinct scenario

### Use Realistic Data

❌ Bad: Generic placeholder values like "value1", "value2"

✅ Good: Realistic inputs based on actual use cases

### Cover the Input Space

- Test normal/common cases
- Test boundary conditions
- Test error conditions
- Test different input combinations

### Validate Multiple Aspects

❌ Bad: Only checking the main output field

✅ Good: Using multiple evaluators to validate:
- Output correctness (ExactMatchEvaluator)
- Response structure (JsonSimilarityEvaluator)
- Execution flow (TrajectoryEvaluator)

## File Organization

Tests are organized in the `evaluations/` directory:

```
evaluations/
├── eval-sets/
│   ├── happy-path.json
│   ├── edge-cases.json
│   └── error-scenarios.json
└── evaluators/
    ├── exact-match.json
    ├── json-similarity.json
    └── llm-judge-semantic-similarity.json
```

Evaluators are reusable across multiple evaluation sets. Reference them by their ID in your eval sets.

## Schema Validation

Your test inputs are validated against:

- Agent's input schema from `entry-points.json`
- Agent's output schema from `entry-points.json`
- Required field constraints
- Type compatibility

This ensures test cases are valid before execution.

## Mocking External Calls

Sometimes your agent calls external APIs or functions. You can mock these for testing:

### Function Mocking

Mock specific function calls with return values or exceptions:

```json
"mockingStrategy": {
  "type": "mockito",
  "behaviors": [
    {
      "function": "external_api_call",
      "arguments": {
        "args": ["param1"],
        "kwargs": {"key": "value"}
      },
      "then": [
        {
          "type": "return",
          "value": {
            "status": "success",
            "data": "mocked-response"
          }
        }
      ]
    }
  ]
}
```

**Mock Behavior Types:**
- `type: "return"` - Return a value
- `type: "raise"` - Throw an exception

### LLM Call Mocking

Mock LLM interactions for testing without API calls:

```json
"mockingStrategy": {
  "type": "llm",
  "prompt": "Test prompt describing the expected LLM behavior",
  "toolsToSimulate": [
    {
      "name": "tool_name"
    }
  ]
}
```

## Next Steps

After creating evaluation sets, you can:

1. **Run Evaluations** - Execute tests to see how your agent performs
2. **Create More Sets** - Add additional test scenarios
3. **View Details** - Examine specific test results
4. **Export Results** - Save results for analysis

See [Running Evaluations](running-evaluations.md) for execution details.
