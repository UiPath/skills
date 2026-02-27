# Evaluation Sets

Evaluation sets define test cases and organize them with their evaluation criteria. This guide covers the structure and creation of evaluation set files.

## What is an Evaluation Set?

An evaluation set is a JSON file containing:

- **Metadata** - Name, description, version information
- **Evaluator References** - Which evaluators this set uses
- **Test Cases** - Individual evaluations with inputs and criteria
- **Optional Mocking** - Mock external calls for isolated testing

## File Location

Evaluation sets are stored in:

```
evaluations/eval-sets/
```

Create one JSON file per evaluation set. Example:

```
evaluations/
├── eval-sets/
│   ├── happy-path-scenarios.json
│   ├── edge-cases.json
│   ├── error-scenarios.json
│   └── performance-tests.json
└── evaluators/
    ├── exact-match.json
    ├── json-similarity.json
    └── ...
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

### version

The schema version. Currently: `"1.0"`

### id

Unique identifier for this evaluation set. Used internally and in references.

Examples: `"happy-path"`, `"edge-cases"`, `"calculator-tests"`

### name

Human-readable name for the evaluation set.

Example: `"Happy Path Scenarios"`, `"Calculator Edge Cases"`

### description

(Optional) Longer description of what this evaluation set covers.

Example: `"Tests basic calculator operations with standard inputs"`

### evaluatorRefs

Array of evaluator IDs that this eval set uses.

These must match the `id` field of evaluators in `evaluations/evaluators/`.

Example:
```json
"evaluatorRefs": ["ExactMatchEvaluator", "JsonSimilarityEvaluator"]
```

### evaluations

Array of test cases. See "Test Case Structure" below.

## Test Case Structure

Each test case in the `evaluations` array has this structure:

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
      "expectedOutput": {
        "result": "expected-value"
      }
    },
    "JsonSimilarityEvaluator": {
      "expectedOutput": {
        "result": "expected-value"
      }
    }
  },
  "mockingStrategy": {}  // optional
}
```

### Test Case Fields

#### id

Unique identifier within this evaluation set.

Convention: `test-<number>-<scenario>` or `<scenario>-<variant>`

Examples:
- `test-1-basic`
- `test-2-large-input`
- `test-3-empty-field`
- `calculator-add`
- `calculator-subtract`

#### name

Human-readable description of the test case.

Examples:
- "Basic addition test"
- "Addition with large numbers"
- "Empty input handling"

#### inputs

Input parameters for the agent. Must match the agent's input schema.

```json
"inputs": {
  "num1": 5,
  "num2": 3,
  "operation": "add"
}
```

For complex inputs with nested objects:

```json
"inputs": {
  "user": {
    "id": "123",
    "name": "John Doe"
  },
  "filters": {
    "status": "active",
    "role": "admin"
  }
}
```

#### evaluationCriterias

Map of evaluator ID to evaluation criteria for that evaluator.

Each evaluator has different required fields:

**ExactMatchEvaluator:**
```json
"ExactMatchEvaluator": {
  "expectedOutput": {
    "result": "5.0"
  }
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
  "expectedOutput": {
    "result": 5.0,
    "status": "complete"
  }
}
```

**TrajectoryEvaluator:**
```json
"TrajectoryEvaluator": {
  "expectedAgentBehavior": "The agent should call the calculator tool once and return the sum."
}
```

**LLMJudge Evaluators:**
```json
"LLMJudgeOutputEvaluator": {
  "expectedOutput": {
    "result": "A helpful response"
  }
}
```

See [Evaluators Guide](evaluators.md) for detailed field documentation.

#### mockingStrategy (optional)

Mock external function calls or LLM interactions. Two types:

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
          "value": {
            "status": "success",
            "data": "mocked-response"
          }
        }
      ]
    },
    {
      "function": "another_function",
      "arguments": {
        "args": [],
        "kwargs": {}
      },
      "then": [
        {
          "type": "raise",
          "value": {
            "_target_": "ValueError"
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

```json
"mockingStrategy": {
  "type": "llm",
  "prompt": "Test prompt describing the expected LLM behavior",
  "toolsToSimulate": [
    {
      "name": "tool_name"
    },
    {
      "name": "another_tool"
    }
  ]
}
```

## Complete Examples

### Simple Calculator Test Set

```json
{
  "version": "1.0",
  "id": "calculator-basic",
  "name": "Calculator Basic Tests",
  "description": "Basic tests for calculator agent with happy path and simple edge cases",
  "evaluatorRefs": ["ExactMatchEvaluator"],
  "evaluations": [
    {
      "id": "test-1-add",
      "name": "Basic addition",
      "inputs": {
        "num1": 5,
        "num2": 3
      },
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": {
            "result": "8"
          }
        }
      }
    },
    {
      "id": "test-2-subtract",
      "name": "Basic subtraction",
      "inputs": {
        "num1": 10,
        "num2": 4
      },
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": {
            "result": "6"
          }
        }
      }
    },
    {
      "id": "test-3-zero",
      "name": "Edge case with zero",
      "inputs": {
        "num1": 0,
        "num2": 5
      },
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": {
            "result": "5"
          }
        }
      }
    }
  ]
}
```

### Complex Agent Test Set with Mocking

```json
{
  "version": "1.0",
  "id": "api-agent-tests",
  "name": "API Agent Tests",
  "description": "Tests for agent that calls external APIs with mocked responses",
  "evaluatorRefs": ["JsonSimilarityEvaluator", "ExactMatchEvaluator"],
  "evaluations": [
    {
      "id": "test-1-fetch-user",
      "name": "Fetch user data from API",
      "inputs": {
        "userId": "123"
      },
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
            "function": "fetch_user_from_api",
            "arguments": {
              "args": ["123"],
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
      "inputs": {
        "userId": "invalid"
      },
      "evaluationCriterias": {
        "ExactMatchEvaluator": {
          "expectedOutput": {
            "error": "User not found"
          }
        }
      },
      "mockingStrategy": {
        "type": "mockito",
        "behaviors": [
          {
            "function": "fetch_user_from_api",
            "arguments": {
              "args": ["invalid"],
              "kwargs": {}
            },
            "then": [
              {
                "type": "raise",
                "value": {
                  "_target_": "Exception",
                  "args": ["User not found"]
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

### Multi-Evaluator Test Set

```json
{
  "version": "1.0",
  "id": "summarizer-comprehensive",
  "name": "Document Summarizer Comprehensive Tests",
  "description": "Comprehensive tests using multiple evaluators for document summarization agent",
  "evaluatorRefs": [
    "ExactMatchEvaluator",
    "ContainsEvaluator",
    "LLMJudgeOutputEvaluator"
  ],
  "evaluations": [
    {
      "id": "test-1-summary-quality",
      "name": "Check summary contains key points",
      "inputs": {
        "document": "The quick brown fox jumps over the lazy dog. This is an important animal behavior study.",
        "maxLength": 50
      },
      "evaluationCriterias": {
        "ContainsEvaluator": {
          "searchText": "fox"
        },
        "ContainsEvaluator": {
          "searchText": "jumps"
        },
        "LLMJudgeOutputEvaluator": {
          "expectedOutput": {
            "summary": "A concise summary capturing the main idea"
          }
        }
      }
    }
  ]
}
```

## Referencing Evaluators

Evaluators are referenced by their `id` field in the evaluator definition.

If you have an evaluator file `evaluations/evaluators/exact-match.json` with:

```json
{
  "id": "ExactMatchEvaluator",
  ...
}
```

Reference it in your eval set as:

```json
"evaluatorRefs": ["ExactMatchEvaluator"]
```

## Best Practices

- **Use Descriptive IDs** - Make test IDs self-documenting
- **Group Related Tests** - Put similar tests in the same eval set
- **Reuse Evaluators** - Create evaluator files once, reference in multiple eval sets
- **Comment Complex Inputs** - For complex test inputs, add context in the test name
- **Version Your Eval Sets** - Use semantic versioning in eval set IDs as they evolve
- **Document Edge Cases** - Make test names clear about what edge case is being tested

## Next Steps

- [Running Evaluations](running-evaluations.md) - Execute your evaluation sets
- [Evaluators Guide](evaluators.md) - Learn more about evaluator types
- [Creating Evaluations](creating-evaluations.md) - Workflow for creating test cases
