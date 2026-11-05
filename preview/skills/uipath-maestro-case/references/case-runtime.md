# Case runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in the generated API.

## Triggers and live payloads

<!-- RULE:case.trigger.event-resolution -->
- A connector event without a subscription is a placeholder. A resolved event
  needs a generated descriptor or connector key/event plus symbolic connection
  and folder bindings. For an unresolved placeholder, put the watched object
  in `object` (`@uipath/maestro-builder-sdk` 6.32.6 or later) and keep the
  source system and event verbatim in the name or description. Do not fabricate a
  connector descriptor or node type. This example keeps the source object
  while remaining a valid placeholder:

  ```ts
  eventTrigger({ name: 'T02', object: 'aged_invoice_cases', description: 'record created' })
  ```

  `object` and `subscription` are mutually exclusive. Only a live
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
  resources resolve. A `CONNECTION_STUB` warning from `case check` or `case
  compile` means a connection or folder label compiles to a value that is not
  a real id; it still compiles (fine for an offline or validate-only task), but
  bind it with the `registry prepare` command the warning prints before a live
  run.

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

## Task exit rules

<!-- RULE:case.task-exit.semantics -->
- A `task-exited` rule reacts to a task of its own stage that ended without
  completing: `failed` (the task failed on its own, after its retries) or
  `userExited` (a person ended the running task through the exit API). A task
  the case itself cancelled (an interrupting stage) is neither and fires no
  rule. The rule fires once EVERY task it names has exited; for "any one of
  them", write one rule per task. An exited task does not satisfy
  `required-tasks-completed`: the stage stays open until a rule moves the case
  on, or an operator re-runs the task.

<!-- RULE:case.task-exit.placement -->
- Put the rule on the entry of the task that should start (a manual fallback),
  or on an exit of the failing task's stage with `{ marksStageComplete: false }`
  and enter the next stage with `rule('selected-stage-exited', { stage })`. The
  platform compiles it nowhere else: at a stage entry, on an exit that marks
  the stage complete (unless `type: 'wait-for-user'`), or at case completion
  the rule is written and never fires (`check`: `TASK_EXITED_PLACEMENT`;
  `validate`: `CASE_MGMT_CASE_CONDITION_RULE_TASK_EXITED_NOT_HERE`). Name only
  tasks of the rule's own stage (`TASK_EXITED_TASK_OUTSIDE_STAGE`), and never
  the task whose entry holds the rule: that re-runs it after every failure
  until the case guardrail stops the loop (`TASK_EXITED_SELF_RERUN`).

  ```ts
  .exitWhen(rule('task-exited', { tasks: ['Fetch Policy'], exitReasons: ['failed'], errorCategories: ['Deployment'] }),
    { displayName: 'Fetch failed to deploy', marksStageComplete: false })
  .task('Enter Policy By Hand', t => t.action({ title: 'Enter the policy' }).required(false)
    .entryWhen(rule('task-exited', { tasks: ['Fetch Policy'] })))
  ```

<!-- RULE:case.task-exit.filters -->
- `exitReasons` narrows the rule to `failed`, `userExited`, or both; omit it
  for either. `errorCategories` (`User`, `System`, `Deployment`) applies only
  to a failures-only rule (`exitReasons: ['failed']`): only a failure carries an
  error, and the platform ignores the filter on any other rule
  (`TASK_EXITED_FILTER_IGNORED`). Anything finer than the category, such as the
  error code or message, is an `expression` over the task's error, not a
  filter.

<!-- RULE:case.task-exit.flags -->
- A plan with a `task-exited` rule compiles with both case flags on,
  `caseExecutionExitsOnTaskFailure` (a failing task exits and the case keeps
  running instead of faulting) and `caseExecutionUsesTaskExitRules` (the rules
  react to exits). Call `.exitOnTaskFailure()` alone for a case that wants the
  exit behaviour without a rule; call either with `false` only to keep the old
  behaviour, which makes every `task-exited` rule a no-op
  (`TASK_EXITED_IGNORED`). A decompiled plan carries the calls explicitly, so
  keep them.

<!-- RULE:case.task-exit.cli -->
- `uip maestro case validate` knows the rule from case-schema 0.1212 on;
  `uip maestro case rule-types list --output json` lists `task-exited` under
  `task-entry` and `stage-exit` when it does. An older `uip` rejects the rule
  as an invalid discriminator: upgrade before compiling, do not remove the rule
  to pass.

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
- Start with `uip maestro case decompile <plan> -o <Name>.case.ts --no-pipeline`.
  Edit the generated `.case.ts` and retain `preserveCaseJson(...)`: it keeps
  the foreign metadata the typed surface does not own. Compile back into the
  same plan: `uip maestro case compile <Name>.case.ts -o <plan>`. Needs
  `@uipath/maestro-builder-sdk` 6.50.1 or later, which resolves the decompiled
  labels (for example `bOC1`) against that plan's own `bindings` array; an
  older SDK writes the label in as the key, so upgrade first. Do not pass
  `--bindings <plan>`: it replaces `bindings.json`, so a connector the edit
  adds loses its mapping. Do not run `<Name>.pipeline.mjs`: it writes a plan
  pack and debug never read. Strict decompile fails closed on unresolved
  references. For an explicitly broken input, rerun
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
  which plain `uip maestro case validate` does not report. `--strict` rejects a
  slot id copied from its name (`STRICT_FORMAL_ARG_ID`), but neither profile
  checks that task and condition ids match their derived form, so `Valid` from
  either does not prove a hand-edit is complete. Round-tripping the whole plan
  re-derives all of them at once.

## Product boundary

<!-- RULE:case.validation.layers -->
- TypeScript checks call shape, `case check` checks source semantics, and
  `uip maestro case validate` checks the compiled product contract. Run all
  applicable layers; use live debug only when execution is part of the task.
