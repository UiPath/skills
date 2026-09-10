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

<!-- RULE:case.action.both-outcomes -->
- A boolean decision from an action has TWO outcomes, and downstream routing has
  to express both. Gating only the affirmative arm (`approved === true`) leaves
  the rejection path implicit: nothing runs, the stage never completes for that
  reader, and the plan validates anyway because an unreferenced value is not an
  error. Write the complementary condition explicitly, even when the negative
  arm only routes to a close-out.

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

<!-- RULE:case.sla.escalation-absent -->
- An ABSENT `escalation` is the persisted representation of Breached — not a
  missing field. So when a plan carries a dangling escalation reference (a
  hand-written `"any"` sentinel, or an id no escalation defines), the repair is
  to drop the reference and leave a plain breach rule on the SLA. Do not invent
  an escalation to make the reference resolve: that silently converts a breach
  response into an at-risk one, which fires at a different time. Only an at-risk
  response needs a concrete escalation, and it must be one declared on that same
  SLA.

<!-- RULE:case.sla.lane-exit -->
- A secondary lane's exit type is a routing decision, and the two shapes are not
  interchangeable. A lane that hands the case BACK to the work it interrupted
  exits `return-to-origin`, which lets the origin stage's own conditions carry
  the case onward — no lane needs a duplicated exit rule per possible origin. A
  lane that ends the case instead exits `exit-only`, and then the case needs a
  matching `caseExitRules` row, or the case can reach the lane and never leave
  it. Read the SDD's own words for which: "returns to", "resumes", "rework"
  means the first; "closed", "terminated", "escalated out" means the second.

<!-- RULE:case.skip.live -->
- Whether a skipped task satisfies a completion rule is runtime behavior. For a
  critical bypass, use a separate expression-gated exit or prove the path live.

## Completion and optionality

<!-- RULE:case.exit.non-completing -->
- `marksCaseComplete` distinguishes two different outcomes, and a case usually
  needs both. At least one `completeWhen(...)` rule must carry `true`, or the
  case can never close. An outcome that ENDS the case without closing it
  normally — an escalated close-out, a rejection, a withdrawal — is a separate
  rule with `marksCaseComplete: false`. It is added ALONGSIDE the positive rule
  and never replaces it: folding both readings into one `true` rule ("Case
  resolved or escalated") loses the distinction the plan was asked to make.

<!-- RULE:case.optionality.explicit -->
- Declare optionality when something consumes it. `.required(false)` and
  omitting `.required()` are different statements in the emitted plan — the
  builder writes `isRequired` only when you call it — and a
  `required-stages-completed` exit reads that flag to decide which stages gate
  completion. When a stage or task is deliberately optional, say so explicitly
  rather than relying on a default the schema leaves unstated. Secondary lanes
  are the common case: an `exceptionStage(...)` that gates normal completion is
  almost never what was meant.

## Design fidelity

<!-- RULE:case.sdd.declared-shapes -->
- When the request supplies an SDD, its declared task TYPES are part of the
  contract, not a hint. A task the SDD calls `process` stays a process even when
  an agent looks like a better fit for the described work, and a
  `wait-for-timer` stays a timer even when its duration reads like a connector
  poll. Substituting the type silently answers a different question, and no
  static check can see it because both spellings validate. Where the SDD is
  genuinely unresolvable, use `.unresolved('<kind>')` — which preserves the
  declared kind — rather than picking a different one.

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

<!-- RULE:case.brownfield.recompile -->
- Repair by recompiling from source, not by editing the emitted JSON. The
  compiler owns everything synthetic in the plan — a formal argument's slot `id`
  is minted from its name rather than copied from it, task and condition ids are
  derived, and companions are wired to match. A hand-edit fixes the field you
  looked at and leaves the derived ones carrying whatever the broken input had,
  which is a class of defect `uip maestro case validate` does not report: it
  checks the contract, not whether an id was supposed to be distinct from the
  name beside it. Round-tripping the whole plan re-derives all of them at once.

## Product boundary

<!-- RULE:case.validation.layers -->
- TypeScript checks call shape, `case check` checks source semantics, and
  `uip maestro case validate` checks the compiled product contract. Run all
  applicable layers; use live debug only when execution is part of the task.
