# Sequence Flow Planning

Use this reference when planning control-flow edges between BPMN nodes in the same scope.

## When to use

- Connecting tasks, events, gateways, and subprocesses.
- Adding branch conditions or default routes.
- Re-routing existing process paths.
- Adding diagram waypoints for Studio Web rendering.

## Planning steps

1. Identify source and target elements and confirm they are in the same BPMN scope.
2. Decide whether the flow is unconditional, conditional, or a gateway default.
3. Name flows only when the label helps reviewers understand a branch.
4. Plan expressions from declared variables and mappings.
5. Update diagram waypoints with readable routing.
6. Check downstream joins and end states after every route change.

## Model may draft

- `bpmn:sequenceFlow` elements.
- Conditional expressions and default-route labels.
- Incoming and outgoing references on connected nodes.
- BPMN DI edges and waypoints.

## Stop conditions

Stop when a requested route crosses subprocess, event subprocess, or participant boundaries; use message flow, call activity, or subprocess modeling instead.
