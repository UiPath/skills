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

- `bpmn:serviceTask` wrapper with the wrapper shell that matches the agent deployment style (`Orchestrator.StartAgentJob` for folder-deployed coded or low-code agents; `A2A.AgentExecution` for external A2A; `Intsvc.*AgentExecution` for Integration Service external agents) — see [../../task-recipes/agent-job.md](../../task-recipes/agent-job.md) for the decision table.
- For `Orchestrator.StartAgentJob`, the required binding pair (`name` + `folderPath`, same `resourceKey`, `resource="process"`, `resourceSubType="Agent"`) and the matching context inputs `=bindings.<bindingId>`.
- Input/output mappings, boundary timeout/error paths, and gateways.
- Public-safe resource placeholders.

## Stop conditions

Stop before Operate when agent identity, version, input schema, output schema, or resource binding is unresolved.
