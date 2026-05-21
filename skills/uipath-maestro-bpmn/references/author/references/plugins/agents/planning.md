# Agent Planning

Use this reference when planning agent execution from BPMN. Agents are resource recipes for `bpmn:serviceTask`, not peer BPMN element types. See [task-recipes/agent-job.md](../../task-recipes/agent-job.md).

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

- `bpmn:serviceTask` wrapper with documented `Orchestrator.StartAgentJob` or `A2A.AgentExecution` shell.
- Input/output mappings, boundary timeout/error paths, and gateways.
- Public-safe resource placeholders.

## Stop conditions

Stop before Operate when agent identity, version, input schema, output schema, or resource binding is unresolved.

For invoking a deployed Python coded agent end-to-end (recommended RPA-wrapper path + draft direct path), see [`../../task-recipes/python-coded-agent.md`](../../task-recipes/python-coded-agent.md).
