# Multi-Instance Implementation

This document defines the implementation boundary for multi-instance activities.

## Model-owned implementation

The model may edit:

- `bpmn:multiInstanceLoopCharacteristics`.
- Sequential or parallel marker attributes.
- `uipath:loopCharacteristics` extension metadata.
- Input collection, item variable, and output mappings.
- Boundary error paths and completion-condition expressions.

## Implementation rules

- Declare collection and item variables before referencing them.
- Use sequential execution when item order or resource limits matter.
- Keep per-item outputs distinct from aggregate outputs.
- Do not hide service-call retries inside loop metadata; model retry or boundary behavior explicitly.

## Validation expectations

- Input collection exists and is iterable.
- Item variable is scoped and referenced consistently.
- Completion conditions use readable variables and no assignments.
- Output aggregation target exists.
- Parallel execution does not conflict with known resource constraints.
