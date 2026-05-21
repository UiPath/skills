# Agent Invocation End-to-End Fixture

Synthetic public-safe BPMN project exercising the full path from a process input through a UiPath-deployed agent and back into a downstream decision. This fixture implements the recommended RPA-wrapper indirection from [`../../../references/author/references/task-recipes/python-coded-agent.md`](../../../references/author/references/task-recipes/python-coded-agent.md), not the draft direct `Orchestrator.StartAgentJob` path.

## What this fixture proves

- **Mirror-variable idiom.** A read-only `uipath:input` entry variable (`Var_RequestId`) is re-projected into a mutable `uipath:inputOutput` mirror (`Var_RequestId_Mirror`) by a start-event `BPMN.Variables` mapping. Downstream nodes target the mirror, never the entry input.
- **`Orchestrator.StartJob` agent invocation.** A `bpmn:serviceTask` invokes the deployed agent's RPA wrapper through `Orchestrator.StartJob`, passing the mirror variable as `JobArguments` JSON and capturing both job state and the agent's structured result.
- **JSON output consumption pattern.** The agent's structured result lands in `Var_AgentResult` (`type="json"`) and a downstream exclusive gateway reads one field (`=vars.Var_AgentResult.outcome == "approved"`) to route to one of two end events.

## Limitations

This fixture is a static contract-shape fixture. It demonstrates how the XML should look but does not exercise a real Orchestrator/Agent deployment. Before treating this fixture as runtime-authoritative, pack and run it against a real Maestro CI tenant — local `.maintenance/check-validation-fixtures.py` only validates XML shape, not deploy-time `uip solution pack` behavior or runtime job lifecycle.

The accompanying XAML RPA wrapper that this fixture's `Binding_AgentWrapperProcess` points at is not part of this skill; see the `uipath-rpa` skill for XAML authoring.

## Files

- `agent-invocation-e2e.bpmn` - the BPMN model.
- `bindings_v2.json` - generated bindings manifest with the agent-wrapper process resource.
- `entry-points.json` - declared entry input/output schemas.
- `operate.json`, `package-descriptor.json`, `project.uiproj` - package metadata.
