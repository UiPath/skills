# Agent Planning

Use this reference when planning agent execution from BPMN.

## When to use

- Starting a UiPath agent job.
- Calling an A2A or external agent execution shell.
- Routing based on agent status, answer, or structured output.
- Combining agent work with HITL validation, RPA jobs, or business rules.

## Planning steps

1. Identify agent type, invocation style, input contract, output contract, and timeout behavior.
2. Decide whether the agent resource already exists or must be created by a sibling workflow outside this skill.
3. Plan variables for prompt/input, structured output, status, and errors.
4. Add validation or HITL review if agent output affects high-impact decisions.
5. Use placeholder-safe bindings for agent resources.
6. Plan fallback paths for timeout, no answer, or invalid output.

## Model may draft

- Service task wrapper with documented `Orchestrator.StartAgentJob` or `A2A.AgentExecution` shell.
- Input/output mappings, boundary timeout/error paths, and gateways.
- Public-safe resource placeholders.

## Stop conditions

Stop before Operate when agent identity, version, input schema, output schema, or resource binding is unresolved.
