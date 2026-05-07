# Signal Planning

Use this reference when planning BPMN signal throw/catch behavior.

## When to use

- Broadcasting an event to one or more waiting process paths.
- Starting or resuming a path from a signal.
- Coordinating between event subprocesses or independent processes.
- Modeling public-safe cross-process notification without connector metadata.

## Planning steps

1. Decide whether the signal is local modeling intent or an executable runtime contract.
2. Define signal name, payload variables, catch locations, and throw locations.
3. Plan correlation and idempotency behavior if multiple instances can catch the signal.
4. Add timeout or fallback paths for waits.
5. Use signal events where broadcast semantics are intended; use message events for directed correlation.

## Model may draft

- `bpmn:signal` definitions.
- Signal start, catch, throw, boundary, and end events.
- Mappings and diagram geometry.
- Public-safe signal names and payload variables.

## Stop conditions

Stop before Operate when runtime signal subscription, correlation, payload schema, or cross-process contract is unresolved.
