# Sequence Flow Implementation

This document defines the implementation boundary for BPMN sequence flows.

## Model-owned implementation

The model may edit:

- `bpmn:sequenceFlow` with `id`, `sourceRef`, `targetRef`, and optional `name`.
- `bpmn:conditionExpression` bodies.
- `incoming` and `outgoing` child references on flow nodes.
- Gateway `default` attributes that reference sequence flows.
- `bpmndi:BPMNEdge` waypoints.

## Implementation rules

- Keep sequence flows inside one process or subprocess scope.
- Use `xsi:type="bpmn:tFormalExpression"` for condition expressions when the file uses that convention.
- Use a leading `=` for UiPath runtime expressions.
- Do not attach conditions to outgoing flows from parallel gateways.
- Update both XML references and diagram edges together.

## Validation expectations

- Every sequence flow source and target exists.
- Connected elements reference the sequence flow consistently.
- Conditional expressions parse and use declared variables.
- Default flows are not also treated as mandatory conditional branches.
- Every visible sequence flow has a BPMN DI edge.
