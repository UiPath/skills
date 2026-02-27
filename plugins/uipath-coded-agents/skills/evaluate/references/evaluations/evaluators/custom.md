# Custom Evaluators

Custom Python Evaluators enable you to implement domain-specific evaluation logic tailored to your agent's unique requirements. When the built-in evaluators don't cover your specific use case, you can create custom evaluators with full control over evaluation criteria and scoring logic.

## Overview

**Use Cases:**
- Domain-specific validation (healthcare data compliance, financial calculations)
- Complex multi-step verification logic
- Custom data extraction and comparison from tool calls
- Specialized scoring algorithms (Jaccard similarity, Levenshtein distance, etc.)
- Integration with external validation systems

**Returns:** Any `EvaluationResult` type (`NumericEvaluationResult`, `BooleanEvaluationResult`, or `ErrorEvaluationResult`)

## Project Structure

Custom evaluators must follow this directory structure:

```
your-project/
├── evals/
│   ├── evaluators/
│   │   ├── custom/
│   │   │   ├── your_evaluator.py       # Custom evaluator implementation
│   │   │   ├── another_evaluator.py    # Additional custom evaluators
│   │   │   └── types/                  # Auto-generated type schemas
│   │   │       ├── your-evaluator-types.json
│   │   │       └── another-evaluator-types.json
│   │   ├── your-evaluator.json         # Auto-generated config
│   │   └── another-evaluator.json
│   └── eval_sets/
│       └── your_eval_set.json
└── ...
```

**Important:** Custom evaluator files **must** be in `evals/evaluators/custom/` directory.

## Creating a Custom Evaluator

### Step 1: Generate Template

```bash
uipath add evaluator my-custom-evaluator
```

Creates `evals/evaluators/custom/my_custom_evaluator.py` with template structure.

### Step 2: Implement Evaluation Logic

A custom evaluator consists of three main components:

#### 1. Evaluation Criteria Class

Define the criteria specific to your evaluation:

```python
from pydantic import Field
from uipath.eval.evaluators import BaseEvaluationCriteria

class MyEvaluationCriteria(BaseEvaluationCriteria):
    """Criteria for my custom evaluator."""
    expected_values: list[str] = Field(default_factory=list)
```

#### 2. Evaluator Configuration Class

Define configuration options for your evaluator:

```python
from uipath.eval.evaluators import BaseEvaluatorConfig

class MyEvaluatorConfig(BaseEvaluatorConfig[MyEvaluationCriteria]):
    """Configuration for my custom evaluator."""
    name: str = "MyCustomEvaluator"
    threshold: float = 0.8  # Minimum score to consider passing
    case_sensitive: bool = False
```

#### 3. Evaluator Implementation Class

Implement the core evaluation logic:

```python
from uipath.eval.evaluators import BaseEvaluator
from uipath.eval.models import AgentExecution, NumericEvaluationResult

class MyCustomEvaluator(
    BaseEvaluator[MyEvaluationCriteria, MyEvaluatorConfig, str]
):
    """Custom evaluator with domain-specific logic."""

    async def evaluate(
        self,
        agent_execution: AgentExecution,
        evaluation_criteria: MyEvaluationCriteria
    ) -> NumericEvaluationResult:
        """Evaluate the agent execution against criteria."""
        # Extract data
        actual_values = self._extract_values(agent_execution)
        expected_values = evaluation_criteria.expected_values

        # Compute score
        score = self._compute_similarity(actual_values, expected_values)

        return NumericEvaluationResult(
            score=score,
            details=f"Expected: {expected_values}, Actual: {actual_values}"
        )

    def _extract_values(self, agent_execution: AgentExecution) -> list[str]:
        """Extract values from agent execution."""
        # Your custom extraction logic
        return []

    def _compute_similarity(self, actual: list[str], expected: list[str]) -> float:
        """Compute similarity score."""
        # Your custom scoring logic
        return 0.0

    @classmethod
    def get_evaluator_id(cls) -> str:
        """Get the unique evaluator identifier."""
        return "MyCustomEvaluator"
```

### Step 3: Register the Evaluator

```bash
uipath register evaluator my_custom_evaluator.py
```

This command:
1. Validates your evaluator implementation
2. Generates `evals/evaluators/custom/types/my-custom-evaluator-types.json`
3. Creates `evals/evaluators/my-custom-evaluator.json`

The generated configuration:

```json
{
  "version": "1.0",
  "id": "MyCustomEvaluator",
  "evaluatorTypeId": "file://types/my-custom-evaluator-types.json",
  "evaluatorSchema": "file://my_custom_evaluator.py:MyCustomEvaluator",
  "description": "Custom evaluator with domain-specific logic...",
  "evaluatorConfig": {
    "name": "MyCustomEvaluator",
    "threshold": 0.8,
    "caseSensitive": false
  }
}
```

### Step 4: Use in Evaluation Sets

Reference your custom evaluator in evaluation sets:

```json
{
  "version": "1.0",
  "id": "my-eval-set",
  "evaluatorRefs": ["MyCustomEvaluator"],
  "evaluationItems": [
    {
      "id": "test-1",
      "agentInput": {"query": "Process data"},
      "evaluations": [
        {
          "evaluatorId": "MyCustomEvaluator",
          "evaluationCriteria": {
            "expectedValues": ["value1", "value2"]
          }
        }
      ]
    }
  ]
}
```

## Working with Agent Traces

Custom evaluators often extract information from tool calls in the agent execution trace.

### Extracting Tool Calls

```python
from uipath.eval._helpers.evaluators_helpers import extract_tool_calls

def _process_tool_calls(self, agent_execution: AgentExecution) -> list[str]:
    """Extract and process tool calls from the execution trace."""
    tool_calls = extract_tool_calls(agent_execution.agent_trace)

    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.name
        args = tool_call.args or {}

        if tool_name == "SpecificTool":
            data = args.get("parameter_name", "")
            results.append(data)

    return results
```

### Available Helper Functions

```python
from uipath.eval._helpers.evaluators_helpers import (
    extract_tool_calls,          # Extract tool calls with arguments
    extract_tool_calls_names,     # Extract just tool names
    extract_tool_calls_outputs,   # Extract tool outputs
    trace_to_str,                 # Convert trace to string
)
```

## Best Practices

### 1. Type Annotations and Documentation

```python
def _extract_data(
    self,
    agent_execution: AgentExecution,
    tool_name: str
) -> list[str]:
    """Extract data from specific tool calls.

    Args:
        agent_execution: The agent execution to process
        tool_name: The name of the tool to extract data from

    Returns:
        List of extracted data strings

    Raises:
        ValueError: If the tool call format is invalid
    """
```

### 2. Error Handling

```python
from uipath.eval.models import ErrorEvaluationResult

async def evaluate(
    self,
    agent_execution: AgentExecution,
    evaluation_criteria: MyCriteria
) -> EvaluationResult:
    """Evaluate with error handling."""
    try:
        score = self._compute_score(agent_execution)
        return NumericEvaluationResult(score=score)
    except Exception as e:
        return ErrorEvaluationResult(
            error=f"Evaluation failed: {str(e)}"
        )
```

### 3. Clear Scoring Logic

```python
def _compute_score(
    self,
    actual: list[str],
    expected: list[str]
) -> float:
    """Compute evaluation score.

    Scoring algorithm:
    - 1.0: Perfect match (all expected items found)
    - 0.5-0.99: Partial match (some items found)
    - 0.0: No match (no items found)
    """
    if not expected:
        return 1.0 if not actual else 0.0

    matches = len(set(actual).intersection(set(expected)))
    return matches / len(expected)
```

### 4. Testing

```python
import pytest
from uipath.eval.models import AgentExecution

@pytest.mark.asyncio
async def test_custom_evaluator() -> None:
    """Test custom evaluator logic."""
    agent_execution = AgentExecution(
        agent_input={"query": "test"},
        agent_output={"result": "test output"},
        agent_trace=[],
    )

    evaluator = MyCustomEvaluator(
        id="test-evaluator",
        config={
            "name": "MyCustomEvaluator",
            "threshold": 0.8,
        }
    )

    criteria = MyEvaluationCriteria(expected_values=["value1"])
    result = await evaluator.evaluate(agent_execution, criteria)

    assert result.score >= 0.0
    assert result.score <= 1.0
```

## Common Patterns

### Pattern 1: Extract Data from Specific Tools

```python
def _extract_from_specific_tool(
    self, agent_execution: AgentExecution
) -> str:
    """Extract data from a specific tool call."""
    tool_calls = extract_tool_calls(agent_execution.agent_trace)

    for tool_call in tool_calls:
        if tool_call.name == "TargetTool":
            args = tool_call.args or {}
            return str(args.get("target_parameter", ""))

    return ""
```

### Pattern 2: Set-Based Similarity

```python
def _compute_set_similarity(
    self, actual: list[str], expected: list[str]
) -> float:
    """Compute similarity using set operations (Jaccard similarity)."""
    expected_set = set(expected) if expected else set()
    actual_set = set(actual) if actual else set()

    if len(expected_set) == 0 and len(actual_set) == 0:
        return 1.0

    intersection = len(expected_set.intersection(actual_set))
    union = len(expected_set.union(actual_set))
    return intersection / union if union > 0 else 0.0
```

## Troubleshooting

### Evaluator Not Found

**Error:** `Could not find '<filename>' in evals/evaluators/custom folder`

**Solution:** Ensure file is in `evals/evaluators/custom/` directory.

### Class Not Inheriting from BaseEvaluator

**Error:** `Could not find a class inheriting from BaseEvaluator`

**Solution:** Verify class properly inherits:

```python
from uipath.eval.evaluators import BaseEvaluator

class MyEvaluator(BaseEvaluator[...]):  # ✓ Correct
    pass
```

### Missing get_evaluator_id Method

**Error:** `Error getting evaluator ID`

**Solution:** Implement required class method:

```python
@classmethod
def get_evaluator_id(cls) -> str:
    return "MyUniqueEvaluatorId"
```

## Generic Type Parameters

```python
class MyEvaluator(BaseEvaluator[T, C, J]):
    """
    T: Evaluation criteria type (subclass of BaseEvaluationCriteria)
    C: Configuration type (subclass of BaseEvaluatorConfig[T])
    J: Justification type (str, None, or BaseEvaluatorJustification)
    """
```

## Related Documentation

- [Output-Based Evaluators](output-based/index.md): Built-in output evaluators
- [Trajectory-Based Evaluators](trajectory-based/index.md): Built-in trajectory evaluators
- [Running Evaluations](../running-evaluations.md): How to execute evaluations
- [Evaluation Sets](../evaluation-sets.md): Defining test cases

## Next Steps

- [Back to Evaluators Overview](README.md)
- [Running Evaluations](../running-evaluations.md)
- [Best Practices](../best-practices.md)
