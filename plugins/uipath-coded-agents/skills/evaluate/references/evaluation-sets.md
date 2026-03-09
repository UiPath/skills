# Evaluation Sets

Evaluation sets define test cases and organize them with their evaluation criteria.

## What is an Evaluation Set?

An evaluation set is a JSON file containing:

- **Metadata** - Name, description, version information
- **Evaluator References** - Which evaluators this set uses
- **Test Cases** - Individual evaluations with inputs and criteria
- **Optional Mocking** - Mock external calls for isolated testing

## File Location

```
evaluations/eval-sets/
```

## Basic Schema

```json
{
  "version": "1.0",
  "id": "my-eval-set",
  "name": "My Evaluation Set",
  "description": "Description of what this eval set tests",
  "evaluatorRefs": ["EvaluatorId1", "EvaluatorId2"],
  "evaluations": [
    {
      "id": "test-1",
      "name": "Test case name",
      "inputs": {
        "param1": "value1",
        "param2": 42
      },
      "evaluationCriterias": {
        "EvaluatorId1": {
          // Evaluator-specific criteria
        }
      }
    }
  ]
}
```

## Top-Level Fields

| Field | Description |
|-------|-------------|
| `version` | Schema version. Currently: `"1.0"` |
| `id` | Unique identifier (e.g., `"happy-path"`, `"calculator-tests"`) |
| `name` | Human-readable name |
| `description` | (Optional) Longer description |
| `evaluatorRefs` | Array of evaluator IDs matching `id` in evaluator files |
| `evaluations` | Array of test cases |

## Test Case Structure

```json
{
  "id": "test-1-basic",
  "name": "Basic test case",
  "inputs": {
    "param1": "value1",
    "param2": 42
  },
  "evaluationCriterias": {
    "ExactMatchEvaluator": {
      "expectedOutput": { "result": "expected-value" }
    }
  },
  "mockingStrategy": {}
}
```

### Test Case Fields

- **id** - Unique within this eval set. Convention: `test-<number>-<scenario>`
- **name** - Human-readable description
- **inputs** - Must match the agent's input schema from `entry-points.json`
- **evaluationCriterias** - Map of evaluator ID to criteria for that evaluator
- **mockingStrategy** - (Optional) Mock external calls

### Evaluator-Specific Criteria

**ExactMatchEvaluator:**
```json
"ExactMatchEvaluator": {
  "expectedOutput": { "result": "5.0" }
}
```

**ContainsEvaluator:**
```json
"ContainsEvaluator": {
  "searchText": "success"
}
```

**JsonSimilarityEvaluator:**
```json
"JsonSimilarityEvaluator": {
  "expectedOutput": { "result": 5.0, "status": "complete" }
}
```

**LLMJudgeTrajectoryEvaluator:**
```json
"LLMJudgeTrajectoryEvaluator": {
  "expectedAgentBehavior": "The agent should call the calculator tool once and return the sum."
}
```

**LLMJudgeOutputEvaluator:**
```json
"LLMJudgeOutputEvaluator": {
  "expectedOutput": { "result": "A helpful response" }
}
```

## Mocking Strategies

### Function Mocking (mockito)

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
          "value": { "status": "success", "data": "mocked-response" }
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

```json
"mockingStrategy": {
  "type": "llm",
  "prompt": "Test prompt describing the expected LLM behavior",
  "toolsToSimulate": [
    { "name": "tool_name" }
  ]
}
```

## Complete Example

```json
{
  "version": "1.0",
  "id": "calculator-basic",
  "name": "Calculator Basic Tests",
  "description": "Basic tests for calculator agent",
  "evaluatorRefs": ["ExactMatchEvaluator"],
  "evaluations": [
    {
      "id": "test-1-add",
      "name": "Basic addition",
      "inputs": { "num1": 5, "num2": 3 },
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": { "result": "8" }
        }
      }
    },
    {
      "id": "test-2-zero",
      "name": "Edge case with zero",
      "inputs": { "num1": 0, "num2": 5 },
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": { "result": "5" }
        }
      }
    }
  ]
}
```

## Best Practices

- **Use Descriptive IDs** - Make test IDs self-documenting
- **Group Related Tests** - Put similar tests in the same eval set
- **Reuse Evaluators** - Create evaluator files once, reference in multiple eval sets
- **Version Your Eval Sets** - Use semantic versioning as they evolve

