# Case runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in [the generated API](api.md).

## Triggers and live payloads

<!-- RULE:case.trigger.event-resolution -->
- A connector event without a subscription is a placeholder. A resolved event
  needs a generated descriptor or connector key/event plus symbolic connection
  and folder bindings. Only a live subscription proves the payload shape.

## Human and on-demand work

<!-- RULE:case.select-next-stage.live -->
- `wait-for-user` and select-next-stage behavior depends on a live Case runtime.
  Static validation proves the contract, not the human selection outcome.

## Connections and external work

<!-- RULE:case.connector.bindings -->
- Source connection and folder ids from `bindings.json`; TypeScript uses symbolic
  names. A live run is the evidence that those environment resources resolve.

<!-- RULE:case.resources.live -->
- Published process, agent, RPA, API workflow, sub-case, connector, and folder
  references are tenant facts. Static validation cannot prove they exist.

## SLA and runtime semantics

<!-- RULE:case.sla.calendar -->
- SLA `d`, `w`, and `m` are calendar units. A business-day requirement needs an
  explicit product decision or live calendar service; do not invent a conversion.

<!-- RULE:case.skip.live -->
- Whether a skipped task satisfies a completion rule is runtime behavior. For a
  critical bypass, use a separate expression-gated exit or prove the path live.

## Brownfield editing

<!-- RULE:case.brownfield.pipeline -->
- Start with `uip maestro case decompile`. Edit the generated `.case.ts`, retain
  `preserveCaseJson(...)`, and run the generated pipeline to keep foreign
  metadata and bindings that the typed surface does not own. Strict decompile
  fails closed on unresolved references. For an explicitly broken input, rerun
  with `--best-effort`, inspect every reported diagnostic, and replace every
  `__UNRESOLVED_*` marker before checking or compiling the repair.

## Product boundary

<!-- RULE:case.validation.layers -->
- TypeScript checks call shape, `case check` checks source semantics, and
  `uip maestro case validate` checks the compiled product contract. Run all
  applicable layers; use live debug only when execution is part of the task.
