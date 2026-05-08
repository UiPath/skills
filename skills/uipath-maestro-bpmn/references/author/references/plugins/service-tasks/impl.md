# Service Task Implementation

This document defines the implementation boundary for `bpmn:serviceTask`. Resource-backed task choices live in [task-recipes/](../../task-recipes/).

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` elements, flow references, and diagram shapes.
- `uipath:mapping` for declared variables.
- `uipath:retry`, `uipath:errorMapping`, and tags when explicitly requested.
- Documented non-Integration-Service `uipath:activity` shells with public-safe context.
- Boundary error or timeout events attached to the task.

Use service tasks for `Orchestrator.StartJob`, `Orchestrator.StartAgentJob`, `A2A.AgentExecution`, `Orchestrator.ExecuteApiWorkflowAsync`, `Orchestrator.CreateAndWaitForQueueItem`, and supported `Intsvc.*` service executions. Do not use a service task for new queue-create, HITL, business-rule, script, or call-activity XML.

## CLI-owned implementation

The CLI must enrich or validate:

- Integration Service payloads.
- Dynamic schemas and generated outputs.
- Binding resources in generated package files.
- Real resource identifiers for cloud-side execution.

## Validation expectations

- Required service context fields exist for the selected type.
- Inputs reference declared variables or literals.
- Outputs map to declared writable variables.
- Binding expressions resolve to root `uipath:bindings` or generated bindings.
- Boundary events use valid event definitions and stay in scope.
