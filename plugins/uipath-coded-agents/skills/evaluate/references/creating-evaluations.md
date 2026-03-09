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

If missing, create an agent first using `uv run uipath new` and `uv run uipath init`.

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

**For LLMJudgeTrajectoryEvaluator:**
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

### Edge Case Tests

Tests for boundary conditions and unusual inputs:
- Boundary values (0, min, max)
- Empty/null values
- Large datasets
- Special characters

### Error Scenario Tests

Tests for invalid inputs and error handling:
- Invalid input types
- Missing required fields
- Out-of-range values
- Expected error messages

## Best Practices for Test Cases

- **Be Specific** - Use descriptive test names like "test-large-json-output"
- **Test One Thing Per Case** - Separate tests for each distinct scenario
- **Use Realistic Data** - Realistic inputs based on actual use cases
- **Cover the Input Space** - Normal, boundary, error, and combination cases
- **Validate Multiple Aspects** - Use multiple evaluators (output + structure + flow)

## Mocking External Calls

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

