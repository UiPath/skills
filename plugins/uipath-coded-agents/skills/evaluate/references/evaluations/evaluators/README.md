# Evaluators

Evaluators are the core components that validate agent output and execution. This guide provides detailed information on all available evaluator types and how to create custom evaluators.

## Quick Navigation

### Output-Based Evaluators

Measure final results and validate what your agent returns:

- **[Exact Match Evaluator](output-based/exact-match.md)** - Verify exact string matching
- **[Contains Evaluator](output-based/contains.md)** - Check if output contains specific text
- **[JSON Similarity Evaluator](output-based/json-similarity.md)** - Compare JSON structure similarity
- **[LLM Judge Output Evaluator](output-based/llm-judge-output.md)** - LLM-powered semantic assessment

See [Output-Based Overview](output-based/index.md) for comparison and selection guidance.

### Trajectory-Based Evaluators

Examine execution patterns and decision sequences during agent execution:

- **[LLM Judge Trajectory Evaluator](trajectory-based/trajectory.md)** - Validate execution paths and decision-making
- **[Tool Call Evaluators](trajectory-based/tool-calls.md)** - Validate tool sequences, counts, arguments, and outputs

See [Trajectory-Based Overview](trajectory-based/index.md) for detailed information.

### Custom Evaluators

When built-in evaluators don't meet your needs:

- **[Custom Python Evaluators](custom.md)** - Implement domain-specific evaluation logic

## Evaluator Selection Guide

| Agent Type | Recommended Evaluators | Why |
|-----------|----------------------|-----|
| Calculator/Deterministic | Exact Match | Deterministic results need exact match |
| Natural Language | LLM Judge Output, Contains | Semantic equivalence and keyword checks |
| Multi-Step Orchestration | Trajectory, JSON Similarity | Validate execution flow and output structure |
| API Integration | JSON Similarity, Exact Match | Flexible JSON matching with strict field validation |
| Multi-Tool Workflows | Tool Call Order/Count, Trajectory | Validate tool sequences and usage patterns |

## Evaluation Scoring

All evaluators return numeric scores:

- **1.0** - Perfect pass
- **0.5-0.9** - Partial success (for similarity-based evaluators)
- **0.0** - Complete failure

Results also include:
- **Justification** - Why the score was given
- **Execution metrics** - Performance data
- **Complete traces** - Full execution history for debugging

## Best Practices

✅ **Do:**
- Use multiple evaluators for comprehensive validation
- Mix output-based and trajectory-based evaluators for complex agents
- Create separate eval sets for different scenarios (happy path, edge cases, errors)
- Use trajectory evaluators for agents with multiple steps/tools
- Use LLM evaluators for natural language or fuzzy matching scenarios
- Start with exact match for deterministic outputs, then add LLM evaluators

❌ **Don't:**
- Use only exact match for natural language outputs
- Forget to test edge cases and error scenarios
- Use trajectory evaluators when output-based is sufficient
- Set too strict criteria early in development
- Skip schema validation during test creation

## Next Steps

- **Getting Started?** Start with [Output-Based Overview](output-based/index.md)
- **Complex Workflows?** Check [Trajectory-Based Overview](trajectory-based/index.md)
- **Domain-Specific Logic?** See [Custom Evaluators](custom.md)
- **Running Tests?** Go to [Running Evaluations](../running-evaluations.md)
