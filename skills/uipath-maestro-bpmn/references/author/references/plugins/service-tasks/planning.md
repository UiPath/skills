# Service Task Planning

Use this reference when planning BPMN service tasks and service-like work.

## When to use

- System work represented by `bpmn:serviceTask`.
- UiPath extension-backed service shells.
- Draft placeholders for connector, queue, agent, RPA, API workflow, or business rule calls.
- Service work that needs retry, error mapping, input mapping, or output mapping.

## Planning steps

1. Identify the service owner: model-authored shell, CLI-enriched connector, Orchestrator resource, or external dependency.
2. Decide whether the task can be implemented now or must remain a draft placeholder.
3. List required inputs, outputs, bindings, retry behavior, and boundary error paths.
4. Declare variables before mapping task outputs.
5. Plan resource bindings with placeholder-safe IDs only.
6. Add diagram geometry and surrounding flows.

## Model may draft

- Standard `bpmn:serviceTask` wrappers.
- Public-safe IDs, labels, mappings, retries, and boundary errors.
- Documented non-Integration-Service `uipath:activity` shells.
- Placeholders for CLI-owned service details.

## Stop conditions

Stop before upload/run when required service type metadata, resource binding, input schema, output schema, or executable context is missing.
