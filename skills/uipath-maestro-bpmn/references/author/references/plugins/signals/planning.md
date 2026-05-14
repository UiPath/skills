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

## Executable boundary

Standard BPMN signal XML is the only confirmed model-owned signal contract. Treat executable cross-process signaling as unresolved unless the operator or CLI provides the runtime subscription contract.

- Model-owned: `bpmn:signal` definitions, signal event references, local throw/catch topology, public-safe labels, variables, mappings, and diagram geometry.
- Operator or CLI-owned: runtime subscription registration, cross-process correlation, payload schema versioning, tenant/folder/resource/channel identifiers, and any non-BPMN binding needed for deployed execution.
- Brownfield rule: preserve imported signal extension payloads or annotations that appear to carry runtime contracts. Do not rewrite them into generated guidance without a fixture-backed validator.

## Model may draft

- `bpmn:signal` definitions.
- Signal start, catch, throw, boundary, and end events.
- Mappings and diagram geometry.
- Public-safe signal names and payload variables.

## Stop conditions

Stop before Operate when runtime signal subscription, correlation, payload schema, or cross-process contract is unresolved.
