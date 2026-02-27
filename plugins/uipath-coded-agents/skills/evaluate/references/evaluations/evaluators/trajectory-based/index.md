# Trajectory-Based Evaluators

Trajectory-based evaluators examine execution patterns and decision sequences during agent execution. These evaluators validate **how** the agent produces results, not just **what** it produces.

## Overview

Trajectory-based evaluators are useful for:
- Validating agent decision-making processes
- Ensuring agents follow expected execution paths
- Evaluating tool usage patterns and sequencing
- Assessing agent behavior in complex scenarios
- Validating multi-step workflows

## What is a Trajectory?

An agent's **trajectory** is the sequence of:
- Tool calls made by the agent
- LLM reasoning steps
- Decision points and logic
- Intermediate results
- Action sequences

Trajectory-based evaluators analyze this execution trace to validate behavior.

## Available Trajectory-Based Evaluators

### 1. LLM Judge Trajectory Evaluator
**[Full Guide →](trajectory.md)**

Uses Language Models to assess the quality of agent execution trajectories and decision-making.

- **Best for:** Complex multi-step agents, flexible behavior assessment
- **Score:** Continuous (0.0-1.0)
- **Configuration:** model, temperature, prompt
- **Speed:** Slower (LLM API calls)
- **Cost:** Depends on trajectory length and LLM usage



## Common Patterns

### Pattern: Flexible Behavior Assessment

Use LLM Judge Trajectory when:
- Agent behavior is complex
- Multiple approaches acceptable
- Decision-making quality matters
- Human judgment needed

## When to Use Trajectory-Based vs Output-Based

### Trajectory-Based Evaluators validate:
- How the agent produces results
- Tool usage and sequencing
- Decision-making process
- Execution flow
- Behavior patterns

### Output-Based Evaluators validate:
- What the agent produces (final results)
- Correctness of outputs
- Presence of required content
- Structure and format

**Use both together for comprehensive validation:**
1. Trajectory-based to verify correct process
2. Output-based to verify correct results


## Best Practices

✅ **Do:**
- Start with tool call evaluators for simple cases
- Add LLM Judge Trajectory for complex behavior
- Combine multiple evaluators for robustness
- Be specific in behavior descriptions
- Use temperature 0.0 for consistent LLM evaluation
- Cache LLM responses for cost savings

❌ **Don't:**
- Overuse LLM evaluators if tool call evaluators sufficient
- Write vague behavior descriptions
- Mix strict and flexible expectations
- Use LLM for simple deterministic validation
- Skip trajectory validation for multi-step agents

## Integration with Output-Based Evaluators

### Complete Agent Testing

Combine trajectory and output-based for complete validation:

```
Test case: User booking a flight

Trajectory-Based:
- Agent calls search_flights first
- Then book_flight
- Finally send_confirmation_email

Output-Based:
- Result contains booking_id
- Status is "confirmed"
- JSON structure valid
```

## LLM Judge Trajectory Deep Dive

For detailed information on LLM-based trajectory evaluation:

1. **[LLM Judge Trajectory Guide](trajectory.md)**
   - Configuration and usage
   - Writing behavior descriptions
   - LLM service integration
   - Cost optimization

## Next Steps

- **Evaluate Complex Behavior?** See [LLM Judge Trajectory](trajectory.md)
- **Back to Overview?** See [Evaluators Overview](../README.md)
- **Output Validation?** See [Output-Based Overview](../output-based/index.md)
- **Running Tests?** See [Running Evaluations](../../running-evaluations.md)
