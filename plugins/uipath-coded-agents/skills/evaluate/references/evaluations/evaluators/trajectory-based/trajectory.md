# LLM Judge Trajectory Evaluator

Uses Language Models to assess the quality of agent execution trajectories - the sequence of decisions and actions an agent takes.

## Overview

**Evaluator ID:** `llm-judge-trajectory-similarity`

**Use Cases:**
- Validate agent decision-making processes
- Ensure agents follow expected execution paths
- Evaluate tool usage patterns and sequencing
- Assess agent behavior in complex scenarios
- Validate multi-step workflows

**Returns:** Continuous score from 0.0 to 1.0 with justification

## Variants

Two variants available:

1. **LLM Judge Trajectory Evaluator** - General trajectory evaluation
2. **LLM Judge Trajectory Simulation Evaluator** - For tool simulation scenarios

## Configuration

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"LLMJudgeTrajectoryEvaluator"` | Display name |
| `model` | `str` | Required | LLM model to use |
| `temperature` | `float` | `0.0` | LLM temperature (0.0 for deterministic) |
| `max_tokens` | `int` | `None` | Maximum tokens for response |
| `prompt` | `str` | Default | Custom evaluation prompt |
| `default_evaluation_criteria` | `dict` | `None` | Default criteria |

## Evaluation Criteria

```json
{
  "expected_agent_behavior": "Detailed description of expected behavior"
}
```

## Prompt Placeholders

The prompt template supports these placeholders:

- `{{AgentRunHistory}}` - The agent's execution trace/trajectory
- `{{ExpectedAgentBehavior}}` - The expected behavior description
- `{{UserOrSyntheticInput}}` - The input provided to the agent

## Understanding Agent Traces

The agent execution trace contains spans showing:

- **Tool calls** made by the agent
- **LLM reasoning** steps
- **Decision points** and choices
- **Action sequences** in order
- **Intermediate results** between steps

Example trace structure:
```python
agent_trace = [
    {
        "name": "search_flights",
        "type": "tool",
        "inputs": {"destination": "Paris"},
        "output": {"flights": [...]}
    },
    {
        "name": "llm_reasoning",
        "type": "llm",
        "content": "User wants cheapest option..."
    },
    {
        "name": "book_flight",
        "type": "tool",
        "inputs": {"flight_id": "FL123"},
        "output": {"status": "confirmed"}
    }
]
```

## Usage Examples

### Basic Trajectory Evaluation

```json
{
  "version": "1.0",
  "id": "TrajectoryJudge",
  "evaluatorTypeId": "llm-judge-trajectory-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectoryEvaluator",
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.0
  }
}
```

Test:
- Input: `{"user_query": "Book a flight to Paris"}`
- Expected behavior: `"Agent should search flights, present options, process booking, confirm"`
- Actual trace: Shows search → present → book → confirm sequence
- **Score: ~0.95** (followed expected sequence with good decision-making)

### Detailed Behavior Description

```json
{
  "expected_agent_behavior": """
  The agent should follow this sequence:

  1. Validate user authentication status
     - If not authenticated, request login
     - If authenticated, proceed to step 2

  2. Fetch user's order history
     - Use the get_orders tool with user_id

  3. Identify the problematic order
     - Search for orders with 'delayed' status

  4. Provide explanation to user
     - Include order details and delay reason

  5. Offer resolution
     - Present refund or expedited shipping options

  The agent should maintain a helpful tone throughout
  and adapt responses based on user reactions.
  """
}
```

### Custom Evaluation Prompt

```json
{
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectoryEvaluator",
    "model": "gpt-4o-2024-11-20",
    "prompt": "Analyze the agent's execution path and compare it with the expected behavior.\n\nAgent Run History:\n{{AgentRunHistory}}\n\nExpected Agent Behavior:\n{{ExpectedAgentBehavior}}\n\nUser Input:\n{{UserOrSyntheticInput}}\n\nEvaluate:\n1. Did the agent follow the expected sequence?\n2. Were all necessary steps completed?\n3. Was the decision-making logical and efficient?\n\nProvide a score from 0-100."
  }
}
```

## Writing Good Behavior Descriptions

### Good Example (Specific and Clear)

```
The agent should:
1. First validate the user exists and is authenticated
   - If not authenticated, request login credentials
   - If not found, return error
2. Fetch the user's current order status from database
3. Compare actual status with 'shipped' status
4. If shipped, provide tracking number
5. If not shipped, provide estimated delivery date
6. Ask if user needs further assistance
```

### Poor Example (Vague and Ambiguous)

```
Help the user with their order problem
```

### Best Practices for Descriptions

**Include:**
1. Sequential steps (numbered or ordered list)
2. Decision points (when agent should make choices)
3. Conditional logic ("If X, then Y" scenarios)
4. Success criteria (what constitutes good behavior)
5. Error handling expectations

**Be specific about:**
- Tool names that should be called
- Data that should be extracted
- Decisions to make at key points
- Order and sequencing

## LLM Judge Trajectory Simulation Evaluator

### Overview

**Evaluator ID:** `llm-judge-trajectory-simulation`

Specialized variant for evaluating agent behavior in **tool simulation scenarios**, where tool responses are mocked.

### What is Tool Simulation?

In tool simulation:
1. **Simulation Engine:** Mocks tool responses based on simulation instructions
2. **Agent Unawareness:** Agent doesn't know responses are simulated
3. **Controlled Testing:** Test agent behavior with predictable tool responses
4. **Evaluation Focus:** Assess if agent behaves correctly given simulated responses

### How It Differs

The evaluator checks:
- Simulation was successful (tools responded as instructed)
- Agent behaved according to expectations given simulated responses
- Agent's decision-making aligns with expected behavior in simulated scenario

### Configuration

Same as standard LLM Judge Trajectory Evaluator

### Additional Prompt Placeholder

- `{{SimulationInstructions}}` - Tool simulation instructions specifying expected tool responses

### Usage Example

```json
{
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectorySimulationEvaluator",
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.0
  }
}
```

Test with mocked tools:
- Simulate search_flights returning 3 options
- Simulate book_flight returning confirmation
- Simulate email sending returning success
- Agent should follow expected sequence with simulated responses
- **Score: ~0.9** based on behavior with mocked tools

## Best Practices

1. **Write clear behavior descriptions** - Be specific about expected sequences and decision logic
2. **Use temperature 0.0** for consistent evaluations
3. **Include context** - Provide enough detail in expected behavior
4. **Consider partial credit** - LLM can give partial scores for mostly correct trajectories
5. **Review justifications** - Understand why trajectories scored high or low

## When to Use vs Other Evaluators

### Use LLM Judge Trajectory when:
- Decision-making process matters more than just output
- Agent behavior patterns need validation
- Tool usage sequence is complex
- Human-like judgment of execution quality is needed
- Multiple valid execution paths exist

### Use Output-Based Evaluators when:
- Only final results matter
- What the agent produces is important
- How it got there is less important

## Configuration Tips

### Temperature Settings

- **0.0** (recommended): Deterministic, consistent results
- **0.1**: Slight variation for nuanced judgment
- **>0.3**: Not recommended (too inconsistent)

### Cost Optimization

- Token usage depends on trajectory length
- Cache evaluations for repeated runs
- Use in CI/CD pipelines carefully (may incur API costs)

## Error Handling

The evaluator will raise `UiPathEvaluationError` if:
- LLM service is unavailable
- Prompt doesn't contain required placeholders
- Agent trace cannot be converted to readable format
- LLM response cannot be parsed

## Performance Considerations

- **Token usage:** Trajectories can be long (more tokens used)
- **Evaluation time:** LLM calls take longer than deterministic evaluators
- **Caching:** Consider caching evaluations for repeated test runs
- **Batch processing:** Evaluate multiple trajectories in parallel when possible

## Related Evaluators

- [Tool Call Evaluators](tool-calls.md): For strict deterministic sequence validation
- [LLM Judge Output Evaluator](../output-based/llm-judge-output.md): For evaluating outputs instead of processes
- [Output-Based Evaluators](../output-based/index.md): For final result validation

## Next Steps

- [Back to Trajectory Overview](index.md)
- [Tool Call Evaluators](tool-calls.md)
- [Running Evaluations](../../running-evaluations.md)
- [Best Practices](../../best-practices.md)
