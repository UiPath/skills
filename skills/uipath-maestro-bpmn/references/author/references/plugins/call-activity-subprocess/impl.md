# Call Activity and Subprocess Implementation

This document defines the implementation boundary for call activities and subprocesses. For agentic or case-management process calls, see [task-recipes/call-activity.md](../../task-recipes/call-activity.md).

## Model-owned implementation

The model may edit:

- `bpmn:subProcess`, event subprocess, and `bpmn:callActivity`.
- Nested events, tasks, gateways, flows, and diagram planes.
- Scoped variables and `uipath:mapping` for boundary data.
- Boundary events, retries, and error mappings.
- Placeholder-safe called element references when documented.

## Subprocess rules

- Use inline `bpmn:subProcess` when the work stays in the local BPMN source and
  needs local tasks, gateways, variables, or boundary handlers.
- Keep sequence flows inside the subprocess scope. Do not connect a nested node
  directly to a root-level node.
- Put subprocess-local variables in the subprocess extension elements only when
  they should not be root state.
- Use root variables for data that must leave the subprocess.
- Expanded subprocesses need visible child shapes and edges in the diagram.
- Collapsed subprocesses may show only the wrapper shape, but nested content
  still needs a product-supported diagram strategy before upload.

## Event subprocess rules

- Use event subprocesses for scoped error or message handling, not as generic
  containers.
- Set `triggeredByEvent="true"`.
- Give the event subprocess exactly one start event.
- For error event subprocesses, use a supported error start definition and the
  shapes from [error-handling.md](../../../../shared/error-handling.md).
- Prefer a boundary error event when one activity owns the failure branch.
  Prefer an event subprocess when the scope needs a shared fallback handler.

## Call activity rules

- Use `bpmn:callActivity` when execution leaves the local BPMN scope for an
  agentic, case-management, or other called process contract.
- Keep called-resource identity placeholder-safe until the CLI or operator
  resolves the actual resource.
- Put call inputs and outputs in the same mapping pattern as other activities:
  payload inputs read `=vars.<variableId>` and outputs target declared mutable
  variable ids.
- Add boundary events and retry/error mapping only when the called process
  contract makes the error behavior explicit.
- Do not inline a called process into a subprocess unless the user explicitly
  wants a local copy of the child workflow.

## CLI or operator-owned implementation

The CLI or operator must resolve:

- Real called process, package, API workflow, agent, or solution resource identity.
- Generated bindings and package metadata.
- Dynamic input/output schemas for called resources.

## Validation expectations

- Sequence flows stay within subprocess scope.
- Event subprocess start rules are satisfied.
- Call activity inputs and outputs match declared contracts.
- Nested visible elements have diagrams.
- Called-resource bindings are resolved before upload/run.
