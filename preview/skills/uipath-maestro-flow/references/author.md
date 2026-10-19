# Author — build and edit a flow with the builder SDK

Everything that happens on disk before a flow touches the cloud: scaffold the
project, choose each node, write `<Name>.flow.ts`, and run the loop in
[`CLI-LOOP.md`](CLI-LOOP.md) until the emitted `.flow` validates. Authoring ends
at a valid artifact; publishing, running and debugging are
[`operate.md`](operate.md), and a failed run is [`diagnose.md`](diagnose.md).

The builder owns the `.flow` JSON. `compile` emits every node definition, the
`variables.nodes[]` entries that make `$vars.<step>.output` resolve, the
resource bindings, the connector `inputs.detail`, and the error flags, so none
of that is hand-authored here. What stays with you is judgment the compiler
cannot make: which node, which topology, what an output means, and what to ask.

## Critical rules

1. **Choose the node before writing it, from a search, never from a brand
   name.** For an external service run `uip maestro registry search
   '<service>'` and prefer, in order: a curated connector, managed HTTP in
   connector mode, manual HTTP for an API with no connector, and an RPA
   workflow only when there is no API at all (a desktop app, a terminal). For a
   tenant resource (agent, process, API workflow, IxP model) run the family's
   `uip maestro flow registry search`; it only returns published resources, so
   `uip maestro flow registry pull --force` first, and check the solution's own
   projects with `uip maestro flow registry list --local` before concluding a
   resource is missing. `mock()` marks a capability both searches proved
   absent; it is never a stand-in for one they found.
2. **Read the node's reference before writing the step.** The router table in
   [SKILL.md](../SKILL.md#supported-node-types) names one reference and one
   example per node. Copy identity fields (keys, model names, folder keys)
   from the tenant; never construct them.
3. **Read the Integration Service contract before any `uip is` call.** Both
   live in [/uipath:uipath-platform](/uipath:uipath-platform), under
   `references/integration-service/`. `connections.md` covers selection,
   folder scoping, BYOA filtering and empty-result recovery; if no healthy
   connection exists after its recovery flow, stop and report it as an open
   question. `resources.md` covers reference-field lookups; finish its
   pagination loop before reporting "not found".
4. **Edit the source, not the artifact.** Change `<Name>.flow.ts` and re-emit
   with `compile -o`. Never hand-edit the emitted `.flow`, `content/*.bpmn`,
   `bindings_v2.json`, `entry-points.json`, `operate.json` or
   `package-descriptor.json` — the CLI regenerates them, and the next compile
   silently undoes a hand edit. Brownfield JSON goes through `decompile`
   ([`brownfield.md`](brownfield.md)).
5. **Run the loop once the source is complete.** `check --source` is cheap, so
   use it freely while writing; `compile` and `validate` run on the finished
   source, and again after the last edit. Treat every `validate` warning as a
   failure unless the loop reference names it as reviewed.
6. **Bind every declared output on every path.** Each `.return({...})` must
   name every key in `.output({...})`. `check` does not catch a missing one:
   `compile` binds it to `$vars.<name>`, `validate` only warns
   (`EXPRESSION_DIAGNOSTIC`), and the run returns `undefined` for it.
7. **Handle an error only when the request says what should happen.** Add
   `.onError(...)` only for a stated failure ("if the call fails…", "return X
   for invalid input", "handle timeouts"); an unhandled failure must fault the
   run. A handler either genuinely recovers or reaches a terminal the caller
   can tell apart from success — a distinct `.return`, or `.terminate`.
8. **Never invent the business meaning of a named output — ask.** When a
   request names an output (`caseKey`, `severity`, `ticketId`) without saying
   how to derive it, whether it passes through or is reformatted is the
   user's rule. Ask, or state the assumption and confirm it. A guessed format
   compiles and validates and returns the wrong value.
9. **Present a finite decision as a list of options, with "Something else"
   last.** Which solution, which connector, which trigger, which resource to
   bind: ask with the enumerated choices, never as an open question. Without a
   structured-question tool, ask in chat as a numbered list. With nobody to ask
   (CI, headless), take the recommended option and record it prominently in
   the final report; if none is recommended, stop and report the open
   decision. Consent gates — destructive operations, tenant writes — are never
   auto-answered.
10. **Look for an existing solution before `uip solution init`.** Run
    `find . -maxdepth 2 -name '*.uipx'`. If one exists, ask which to use (one
    option per solution, "Create a new solution", then "Something else"); do
    not silently adopt, re-initialize, or repair it. The scaffold itself is in
    [SKILL.md](../SKILL.md#project-layout).
11. **Never invoke another skill on your own.** When the flow needs an RPA
    process, an agent, or an app that does not exist, name the gap and hand
    the user what they need to switch skills.
12. **Batch independent calls; chain dependent ones.** Scaffold, install and
    the registry search go in one turn; `check`, each `prepare` it names, the
    re-`check`, `compile` and `validate` chain in the next. Split only where a
    later step needs an earlier step's output.

## Journeys

| Journey | Read |
| --- | --- |
| Create a new flow | [SKILL.md — Project layout](../SKILL.md#project-layout), then [`CLI-LOOP.md`](CLI-LOOP.md) |
| Edit an existing flow (`.flow.ts` or raw `.flow`) | [`brownfield.md`](brownfield.md) |
| Add or change one node | the node's row in [SKILL.md — Supported node types](../SKILL.md#supported-node-types) |
| Connector with tenant-specific fields | [`connector-params.md`](connector-params.md) + [`bindings.md`](bindings.md) |

### Count what the request names before building

Count the steps the request names: services, systems, documents, decisions,
approvals, schedules, computations. A domain or an outcome ("shipment
tracking", "our onboarding") is not a step, and neither is the project name.

- **Zero steps: scaffold only.** Scaffold the project, compile the stub, and
  validate. Do not invent a pipeline from the domain word. Report what the flow
  should do as open questions; that is the finished deliverable.
- **One or more steps: build all of them.** An outcome next to a step does not
  cancel the step. "Check the weather for the Bellevue office and tell me if
  it's a nice day" names a lookup and a threshold decision; build both.

### Plan first only when the flow is complex

Plan before building when the flow has five or more nodes with branching or
parallel paths, needs connector or resource discovery, or the requirements are
ambiguous. Build directly for a single-node edit, a linear pipeline, or a
topology the user already spelled out.

Skipping the plan never skips the node choice. Two outcomes ("if … otherwise
…") are a `.branch`, never a script ternary; three or more are a `.switch`; a
named external service goes through rule 1.

A plan states: a one-line summary, the node table (step name, node, why), the
wiring, the inputs and outputs, every connector and its connection, and open
questions. Get it approved before building (rule 9, with "proceed"
recommended).

**Is Maestro the right home?** A flow earns its place with several waits,
branching or parallel paths, SLAs, cross-product composition, or per-case
visibility. A single-wait, mostly linear process may be simpler as a queue plus
Action Center; say so before designing topology.

## Anti-patterns

- **Never replace a registered connector with `mock()` or a script because it
  cannot be configured yet.** Write the `connector(...)` step, run the
  `prepare` that `check` names, and if there is no live connection, report
  "prepare pending" as an open question. Reviewers and Studio Web need the real
  connector in the artifact.
- **Never reuse a reference id from another flow or session** — a mailbox
  folder, a Slack channel, a Jira project. Ids are scoped to the account behind
  the connection: a reused one compiles, validates, and faults at run time.
  Resolve it again with a `lookup()` token and the `prepare` that `check`
  names.
- **Never write a reference field you could not resolve.** If the lookup fails
  (401/403 on an expired grant, 5xx), you have no id: do not substitute the
  display name, an alias, or a remembered value. Stop and report the failed
  resolve.
- **Never reference a parent's values inside a subflow.** A child flow has its
  own scope; pass values through the `subflow(child, {...})` inputs and read
  them with `input(...)`. `check` does not flag a child script that reads
  `$vars.start.output.*` from the parent — it compiles and resolves to nothing.
- **Never use `console.log` in a script.** The script runtime has no
  `console`, and `check` does not flag it. Return the value to inspect:
  `return { debug: value }`.
- **Never treat a green `validate` as proof of business correctness.** It
  checks structure. Named outputs, reference ids and connector field values
  are only proven by the evidence in [`CLI-LOOP.md`](CLI-LOOP.md#bounded-completion).

## Completion output

When authoring is done, report:

1. **File paths** — the `.flow.ts` source and the emitted `.flow`.
2. **What was built** — steps, branches and outputs, in a sentence or two.
3. **Loop status** — the last `check`, `compile` and `validate` results,
   including any warning you judged acceptable and why.
4. **Placeholders** — each `mock()` and the capability it stands for.
5. **Missing connections or pending prepares** — per connector.
6. **Open questions** — every decision the request left open, each marked
   **[REQUIRED]** or **[OPTIONAL]**.
7. **What's next** — when the request did not already say, ask with rule 9:
   upload to Studio Web, debug the flow, deploy to Orchestrator, or "Something
   else". Each hands off to [`operate.md`](operate.md). A request that already
   named the next step ("publish it", "debug it") is the selection; act on it.

## Narration and progress

Silent by default: surface decisions, failures, consent gates and the final
result. Narrate each logical step in one plain-English line, and keep a
step-level progress list, only when the user asks for it (verbose, show steps,
track progress) or has a standing preference for it. A logical step is the
smallest outcome the user cares about — "added the Slack step", not the three
commands behind it.
