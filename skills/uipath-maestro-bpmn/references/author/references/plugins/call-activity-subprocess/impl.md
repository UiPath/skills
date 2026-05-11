# Call Activity and Subprocess Implementation

This document defines the implementation boundary for call activities and subprocesses. For agentic or case-management process calls, see [task-recipes/call-activity.md](../../task-recipes/call-activity.md).

## Model-owned implementation

The model may edit:

- `bpmn:subProcess`, event subprocess, and `bpmn:callActivity`.
- Nested events, tasks, gateways, flows, and diagram planes.
- Scoped variables and `uipath:mapping` for boundary data.
- Boundary events, retries, and error mappings.
- Placeholder-safe called element references when documented.

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
