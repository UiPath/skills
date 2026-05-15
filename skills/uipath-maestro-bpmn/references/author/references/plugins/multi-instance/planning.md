# Multi-Instance Planning

Use this reference when planning repeated execution over a collection.

## When to use

- Running an activity once per item.
- Parallel or sequential collection processing.
- Aggregating per-item outputs.
- Combining multi-instance with subprocess, service task, HITL, RPA, agent, or API workflow calls.

## Planning steps

1. Identify input collection, item variable, output collection, and completion condition.
2. Choose sequential or parallel execution based on side effects and ordering.
3. Decide how errors should affect the batch.
4. Plan aggregation and downstream gateway behavior.
5. Add UiPath loop metadata only after variables are declared.
6. Avoid parallel fan-out when called resources have rate limits or side effects that require ordering.

## Model may draft

- Standard BPMN loop characteristics.
- `uipath:loopCharacteristics` with input collection and input element metadata.
- Variables, mappings, boundary errors, and diagrams.

## Stop conditions

Stop when collection shape, item variable, ordering, aggregation, or failure behavior is not defined.
