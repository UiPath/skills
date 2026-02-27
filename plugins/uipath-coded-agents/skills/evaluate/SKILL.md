---
description: Test and evaluate UiPath coded agents
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Evaluating UiPath Agents

Design and run comprehensive tests for your UiPath coded agents using the evaluation framework.

## Overview

The evaluation framework provides:
- Multiple evaluator types (output-based and trajectory-based)
- Test case organization and schema validation
- Mocking capabilities for external dependencies
- Performance analysis and metrics

## Documentation

### Framework Overview
- **[Evaluations Overview](references/evaluations.md)** - Framework introduction
  - Output-based evaluators for result validation
  - Trajectory-based evaluators for execution flow analysis
  - Test case organization
  - Mocking external dependencies

### Creating Tests
- **[Creating Evaluations](references/evaluations/creating-evaluations.md)** - Design test cases
  - Define evaluation scenarios
  - Collect test inputs and expected outputs
  - Organize by scenario type
  - Schema validation

### Evaluator Types
- **[Evaluators Guide](references/evaluations/evaluators/README.md)** - Understand evaluator types
  - Output-based evaluators: ExactMatch, JsonSimilarity, LLMJudgeOutput, Contains
  - Trajectory-based evaluators: Trajectory
  - Custom evaluators
  - Evaluator selection guide

### Test Organization
- **[Evaluation Sets](references/evaluations/evaluation-sets.md)** - Structure your tests
  - Evaluation set file format
  - Test case schema
  - Mocking strategies
  - Complete examples

### Execution & Analysis
- **[Running Evaluations](references/evaluations/running-evaluations.md)** - Execute and analyze
  - Running test suites
  - Understanding results
  - Performance analysis
  - Troubleshooting

### Best Practices
- **[Evaluation Best Practices](references/evaluations/best-practices.md)** - Patterns and optimization
  - Best practices for evaluation design
  - Common patterns by agent type:
    - Calculator/Deterministic agents
    - Natural language agents
    - Multi-step orchestration agents
    - API integration agents
  - Test organization strategies
  - Performance optimization


## Workflow

1. Build your agent with [Building Agents](/uipath-coded-agents:build) — review [Agent Patterns](/uipath-coded-agents:build#agent-patterns) for your use case
2. Test it manually with [Running Agents](/uipath-coded-agents:execute)
3. Design evaluation test cases with [Creating Evaluations](references/evaluations/creating-evaluations.md)
4. Select appropriate evaluators from [Evaluators Guide](references/evaluations/evaluators/README.md)
5. Run evaluations and analyze results with [Running Evaluations](references/evaluations/running-evaluations.md)

## Next Steps

1. **Getting started with evaluation?**
   - Start with [Creating Evaluations](references/evaluations/creating-evaluations.md)
   - Review [Best Practices](references/evaluations/best-practices.md) for your agent type

2. **Ready to run tests?**
   - Use [Running Evaluations](references/evaluations/running-evaluations.md)

3. **Need to understand evaluators?**
   - See [Evaluators Guide](references/evaluations/evaluators/README.md)

## Additional Instructions
- For project setup and agent patterns, see [Building Agents](/uipath-coded-agents:build)
- If you are unsure about usage, read the linked authentication reference before making assumptions.
