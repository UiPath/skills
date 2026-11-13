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

## Script tasks

<!-- RULE:case.script.positional-rename -->
- The function form's parameters are positional: first parameter becomes
  `vars`, second becomes `metadata`. The mapping is by position, not by
  name. Any names work, except `metadata` first or `vars` second, which
  compile refuses. A function-local `const` is fine;
  a module-scope constant or an `import` is refused at compile.
  Compile also refuses destructured parameters (`({ amount }) =>`),
  aliasing (`const v = vars`), bracket access (`vars['x']`), optional
  chaining on `vars`, and passing `vars` to another function.

<!-- RULE:case.script.body-and-refs -->
- A string body compiles as authored. Declare every `vars.x` read
  with `.var()` or `.input()` before referencing it.

<!-- RULE:case.script.outputs -->
- `.outputs({ scriptResult: '=result.response' })` maps the whole return value
  to a case variable. Compile refuses any source except `=result.response` and
  `=Error` (code `SCRIPT_OUTPUT`). To reach a single field, read
  `vars.scriptResult.<field>` downstream. The compiled output row is named
  `scriptResponse`.

## Connections and external work

<!-- RULE:case.connector.bindings -->
- Source connection and folder ids from `bindings.json`; TypeScript uses symbolic
  names. Compiling into a scaffolded project regenerates its existing
<!--skill-flavor:bindings-refresh:start-->
  `bindings_v2.json`; then run `uip solution resources refresh --solution-folder
  {solution} --output json`.
<!--skill-flavor:bindings-refresh:end-->
  A live run is the evidence that those environment
  resources resolve. A `CONNECTION_STUB` warning from `case check` or `case
  compile` means a connection or folder label compiles to a value that is not
  a real id; it still compiles (fine for an offline or validate-only task), but
  bind it with the `registry prepare` command the warning prints before a live
  run.

<!-- RULE:case.resources.live -->
- Published process, agent, RPA, API workflow, sub-case, connector, and folder
  references are tenant facts. Static validation cannot prove they exist.

<!--skill-flavor:orphan-cleanup:start-->
- Resource refresh is additive. After removing or repointing a resource-bound
  task, prune orphans before refreshing:

  1. Recompile. `compile` (SDK 6.86.23+) emits `ORPHANED_SOLUTION_RESOURCE`
     for each process or app declaration no binding still references. An
     older SDK emits nothing, so step 2 removes nothing and the orphan ships.
  2. For each reported orphan:
     `uip solution resources remove {key} --solution-folder {solution} --output json`
  3. Connection declarations are not covered by the warning. Remove one
     only when no project in the solution still binds it. Search both
     binding files, because a coded agent binds a connection in
     `bindings.json`, not `bindings_v2.json`:
     `grep -rl --include=bindings_v2.json --include=bindings.json --exclude-dir=resources --exclude-dir=.venv '<connection-key>' {solution}`
     No match means safe to remove with `resources remove`.
  4. Never remove the Case project's own process/package pair, and never
     target package entries directly.
  5. `uip solution resources refresh --solution-folder {solution} --output json`
<!--skill-flavor:orphan-cleanup:end-->

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
  missing field. A reference to an at-risk escalation, or the Case Designer's
  `escalationId: "any"` wildcard, makes the rule at-risk; one to an
  `sla-breached` escalation is Breached. The wildcard is valid and fires on
  every at-risk escalation of that SLA (in SDK source,
  `escalation: ANY_ESCALATION`). Do not author it; name the escalation the
  requirement means. Repair an existing rule by the requirement's status, never
  by what the plan already carries: a breach response drops the reference and
  leaves a plain breach rule on the SLA; repointing it at an at-risk escalation
  keeps it at-risk, which fires at a different time. Only an at-risk response
  needs a concrete escalation, and it must be one declared on that same SLA.

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

  Three-exit pattern (completing + rejected + withdrawn):

  ```ts
  .completeWhen(rule('required-stages-completed'), { marksCaseComplete: true })
  .completeWhen(rule('selected-stage-completed', { stage: 'Rejection' }), { marksCaseComplete: false })
  .completeWhen(rule('selected-stage-completed', { stage: 'Withdrawal' }), { marksCaseComplete: false })
  ```

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

<!-- RULE:case.sdd.output-contract -->
- The SDD's Out-variable table is a three-part contract:

  1. **Declaration.** Every SDD Out-variable needs a case-level `.output()`
     that reserves the variable.
  2. **Production.** At least one task must write the variable. For a
     non-action task, use `.outputs({ name: <source> })`. For an action
     task, map a form field to the case variable through the field's
     `value` in `.action({ outputs: [{ name, value }] })` — do not add a
     custom `.outputs()` entry, which creates a duplicate row that
     `validate --sdd` reports.
  3. **Casing and paths.** Output keys and extract paths must match the
     SDD's field names character-for-character, including casing. When
     the SDD declares a sub-property dereference, extract it from the
     producing task's own output root: `=response.<field>` on a connector
     or wait-for-connector task, `=<OutputName>.<field>` on other types.
     When the SDD dereferences in place (e.g. inside a `$xref`
     expression), keep the SDD's casing and null-guard it:
     `vars.analysisResult?.unusualClauses`.

## Brownfield editing

<!-- RULE:case.brownfield.pipeline -->
- Start with `uip maestro case decompile <plan> -o <Name>.case.ts --no-pipeline`.
  Edit the generated `.case.ts` and retain `preserveCaseJson(...)`: it keeps
  the foreign metadata the typed surface does not own. Compile back into the
  same plan: `uip maestro case compile <Name>.case.ts -o <plan>`.
<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.50.1 or later, which resolves the decompiled
  labels (for example `bOC1`) against that plan's own `bindings` array; an
  older SDK writes the label in as the key, so upgrade first.
<!--skill-flavor:sdk-upgrade:end-->
  Do not pass
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

### Check only what you changed: `check --baseline`

`check` judges the whole case. In an existing plan it also reports defects the
plan already had on stages and tasks you never touched, for example
`TASK_NO_ENTRY` on a task the Designer saved with no entry rule. Those would
fail every edit. Pass the original plan as `--baseline` and each finding says
whether your edit caused it.

The baseline must be the plan as it was before your first compile: compile
writes back into the same plan, so after it the file on disk is your edit.
Never pass that plan itself as `--baseline`: the edit compared with itself
reports every finding as pre-existing, so `check` passes with errors in it.
<!--skill-flavor:check-baseline-original:start-->
At the start of each editing session, before its first compile, copy it aside
and check against the copy. Overwrite any copy an earlier session left: an old
copy would count that session's changes as yours.

```bash
mkdir -p .flow-sdk/original && cp <project>/<plan> .flow-sdk/original/
uip maestro case check <Name>.case.ts --source --baseline .flow-sdk/original/<plan>
```
<!--skill-flavor:check-baseline-original:end-->

```text
✗ [TASK_NO_ENTRY] Task "Escalate" in stage "Intake" has no entry rule — ... (edited)
⚠ [TASK_NO_ENTRY] Task "Archive" in stage "Intake" has no entry rule — ... (pre-existing, not counted)
check: 1 error(s) in edited parts of the case, 0 pre-existing SDK defect(s), 1 pre-existing warning(s).
```

- **`(edited)`** (JSON `origin: "edited"`): fix it. The finding is on a stage,
  task or trigger you added or changed (a renamed task counts as changed), or
  it is new on one you did not touch, so your edit caused it. The exit code is
  1 only while one is left.
- **`(pre-existing, not counted)`**: the original reports the same code on the
  same unchanged stage, task or trigger. Leave it unless the user asked you to
  fix it. A finding that names no stage or task (a case-level rule) is
  pre-existing only when the original reports the same code and message.
- **`(pre-existing)` worded as a probable SDK defect** (JSON
  `class: "lowering"`): `compile` refuses that task even though you did not
  change it, so the compile stops on it. Do not edit the task to get around
  it. Stop, name the task and the code, and tell the user it is a probable SDK
  defect to report at <https://github.com/UiPath/builder-sdk/issues>.
- **`CHECK_INCOMPLETE`**: check stopped before it judged the whole case. Fix
  the error it names, even if the original has it too, then check again.
- **`--baseline ... is not the plan this source was decompiled from`** (exit
  2): the file you passed is not the original, most often the plan after a
  compile wrote your edit into it. Pass the copy you made before the first
  compile. If you no longer have it, decompile the current plan again and use
  that plan as the baseline from now on.

<!--skill-flavor:check-baseline-sdk-upgrade:start-->
Needs two releases: `@uipath/maestro-builder-sdk` 6.97.0 or later, and the
`uip` release that carries UiPath/cli#6081 (`uip` 1.205.0 does not).
- `unknown option '--baseline'` means `uip` is too old, whatever the SDK
  version. Upgrade `uip`. Upgrading the SDK alone gives the same error again.
- `--baseline on case check needs a @uipath/maestro-builder-sdk release that
  supports it` means `uip` is new enough and the SDK is not. Upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest`.

Until both are upgraded, run `check --source` without `--baseline`. In this
fallback only, fix only the errors on stages and tasks you changed, even
though the exit code stays non-zero.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->

## Product boundary

<!-- RULE:case.validation.layers -->
- TypeScript checks call shape, `case check` checks source semantics, and
  `uip maestro case validate` checks the compiled product contract. Run all
  applicable layers; use live debug only when execution is part of the task.
