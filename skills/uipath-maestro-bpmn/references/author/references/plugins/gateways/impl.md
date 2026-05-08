# Gateway Implementation

This document defines the implementation boundary for BPMN gateways.

## Model-owned implementation

The model may edit:

- `bpmn:exclusiveGateway`, `bpmn:inclusiveGateway`, `bpmn:parallelGateway`, `bpmn:eventBasedGateway`, and `bpmn:complexGateway`.
- Incoming and outgoing `bpmn:sequenceFlow` references.
- `default` attributes for exclusive and inclusive split gateways.
- `bpmn:conditionExpression` on outgoing flows.
- Gateway shapes and sequence flow edges.

## Implementation rules

- Store branch logic on outgoing sequence flows, not on the gateway element.
- Use a leading `=` for runtime expressions where the frontend expects expressions.
- Do not use assignment expressions in gateway conditions.
- Prefer explicit default flows for fallthrough paths.
- Use parallel gateways only when every branch should run or rejoin.
- Use event-based gateways only when the next route is determined by the first event that occurs.

## Validation expectations

- Split gateways have the right number of outgoing flows.
- Join gateways have the right number of incoming flows.
- Defaults reference an outgoing flow from the same gateway.
- Conditional branches reference declared variables.
- Event-based gateway outgoing flows lead to valid catch events or receive tasks.
