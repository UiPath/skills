# Case runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in [the generated API](api.md).

## Triggers and live payloads

<!-- RULE:case.trigger.event-resolution -->
- A connector event without a subscription is a placeholder. A resolved event
  needs a generated descriptor or connector key/event plus symbolic connection
  and folder bindings. For an unresolved placeholder, preserve the requested
  source system, object, and event verbatim in the trigger name or description;
  the service-type-only runtime bag cannot carry that intent. Do not fabricate
  a connector descriptor or node type. For example,
  `eventTrigger({ name: 'aged_invoice_cases record created' })` preserves the
  unresolved source while remaining a valid placeholder. Only a live
  subscription proves the payload shape.

## Human and on-demand work

<!-- RULE:case.select-next-stage.live -->
- `wait-for-user` and select-next-stage behavior depends on a live Case runtime.
  Static validation proves the contract, not the human selection outcome.

## Connections and external work

<!-- RULE:case.connector.bindings -->
- Source connection and folder ids from `bindings.json`; TypeScript uses symbolic
  names. Compiling into a scaffolded project regenerates its existing
  `bindings_v2.json`; then run `uip solution resources refresh --solution-folder
  {solution} --output json`. A live run is the evidence that those environment
  resources resolve.

<!-- RULE:case.resources.live -->
- Published process, agent, RPA, API workflow, sub-case, connector, and folder
  references are tenant facts. Static validation cannot prove they exist.

- Resource refresh is additive. After removing or repointing a resource-bound
  task, list local solution resources and remove each orphaned process or app by
  its listed key with `uip solution resources remove {key} --solution-folder
  {solution} --output json`, then refresh again. Never remove the Case project's
  own process/package pair, and never target package entries directly.

## SLA and runtime semantics

<!-- RULE:case.sla.calendar -->
- SLA `d`, `w`, and `m` are calendar units. A business-day requirement needs an
  explicit product decision or live calendar service; do not invent a conversion.

- An `sla-status-change` breach response uses only `{ sla }`; an at-risk response
  also names `{ escalation }`. Put an enter-stage response on an
  `exceptionStage(...)` and call `.required(false)` so the secondary stage does
  not gate `required-stages-completed`.

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
  `__UNRESOLVED_*` marker before checking or compiling the repair. Removing or
  repointing a bound task also requires the orphan cleanup under
  [Connections and external work](#connections-and-external-work); compilation
  and resource refresh do not remove solution declarations.

## Product boundary

<!-- RULE:case.validation.layers -->
- TypeScript checks call shape, `case check` checks source semantics, and
  `uip maestro case validate` checks the compiled product contract. Run all
  applicable layers; use live debug only when execution is part of the task.
