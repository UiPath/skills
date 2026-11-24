# Author — build and edit a flow with the builder SDK

<!--skill-flavor:author-scope:start-->
Everything on disk before a flow touches the cloud—scaffolding, node choice, `<Name>.flow.ts`, and the loop in [`CLI-LOOP.md`](CLI-LOOP.md)—ends when the emitted `.flow` validates. Publishing, running, and debugging are [`operate.md`](operate.md); a failed run is [`diagnose.md`](diagnose.md).
<!--skill-flavor:author-scope:end-->

The builder owns `.flow` JSON: `compile` emits node definitions, `variables.nodes[]` entries for `$vars.<step>.output`, resource bindings, the connector `inputs.detail`, and error flags. Author judgment remains: node, topology, output meaning, and questions.

## Critical rules

1. **Choose the node before writing it, from a search, never from a brand name.** For an external service run `uip maestro registry search '<service>'`; prefer, in order: a curated connector, managed HTTP in connector mode, a connector built with `uip is connectors builder` for an authenticated REST+JSON API without a connector, manual HTTP otherwise (its credential stays in the flow, outside `uip is connections list`), and RPA only when no API exists (desktop app or terminal). For a tenant resource (agent, process, API workflow, IxP model), run the family's `uip maestro flow registry search`; it returns only published resources. Before calling it missing, run `uip maestro flow registry list --local`; if still missing, run `uip maestro flow registry pull --force` once and search again (registry reads cache for 30 minutes). `mock()` marks a capability both searches proved absent, never one they found.
2. **Read the node's reference before writing the step.** The router in [SKILL.md](../SKILL.md#supported-node-types) gives one reference and example per node. Copy tenant identity fields (keys, model names, folder keys); never construct them.
3. **Read the Integration Service contract before any `uip is` call.** Both are in [/uipath:uipath-platform](/uipath:uipath-platform), under `references/integration-service/`. `connections.md` covers selection, folder scope, BYOA filtering, and empty-result recovery; if no healthy connection remains after recovery, stop and report an open question. `resources.md` covers reference-field lookups; complete pagination before reporting "not found".
<!--skill-flavor:source-not-artifact:start-->
4. **Edit the source, not the artifact.** Change `<Name>.flow.ts` and re-emit with `compile -o` for a new flow; for a non-empty `.flow` that existed before this turn, use decompile and merge ([`brownfield.md`](brownfield.md)).
<!--skill-flavor:source-not-artifact:end-->
   Never hand-edit emitted `.flow`, `content/*.bpmn`, `bindings_v2.json`, `entry-points.json`, `operate.json`, or `package-descriptor.json`; the CLI regenerates them and compile undoes edits. Route brownfield JSON through `decompile` ([`brownfield.md`](brownfield.md)). Non-interactive runs take the same route (nobody can approve a script over the `.flow`): write large node definitions into source; an inexpressible node is an SDK gap to report, not JSON to splice, unless its reference names a CLI route.
5. **Run the loop once the source is complete.** Use `check --source` while writing; run `compile` and `validate` on finished source and again after the last edit. `compile` does not run `check`: run a clean `check` before every `compile`; for brownfield edits use `--baseline <original.flow>` ([`brownfield.md`](brownfield.md#check-only-what-you-changed-check---baseline)). Ignore an error only when its message says to do so and that case applies (for example, false-positive `INLINE_AGENT_PROMPT_JSON_TEXT` when JSON is mentioned only as data). In emit-only mode `check` refuses and `validate` is the gate. Treat every `validate` warning as failure unless the loop reference names it reviewed.
6. **Bind every declared output on every path.** An output that only `.return()` sets (no `default`, `{ updates }` or shared input) comes back `null` from every `.return({...})` that leaves it out. `check` reports that as `RETURN_OUTPUT_MISSING` on `@uipath/maestro-builder-sdk` 6.100.0 or later; an older SDK misses it. Write `lit(null)` when null is the answer. `check` still misses an output set with `{ updates }` on only some paths: a `.return()` on a path that skipped the update returns its default, or `null`. Name the output in that `.return()`, or set it before the paths split.
7. **Handle errors only when requested.** Add `.onError(...)` only for stated failure behavior ("if the call fails…", invalid-input return, or timeout handling); otherwise let failure fault the run. A handler must recover genuinely or reach a terminal the caller can tell apart from success: a distinct `.return` or `.terminate`. Add `hitl` only when the request says the run waits for a person; post-run review of output, such as a drafted reply, is not hitl. This overrides `uipath-human-in-the-loop` Step 2b and its pattern guide; put unstated signals under Open questions.
8. **Never invent a named output's meaning or an uncovered input case—ask.** If derivation, pass-through, or reformatting of a named output (`caseKey`, `severity`, `ticketId`) is unspecified, ask or state and confirm an assumption; a guessed format compiles and validates and returns the wrong value. Check coverage over the valid values, ranges, and combinations of the inputs the stated rules read (`High` for refunds over $500 and `Low` under $50 leave $50 to $500 unassigned; `Expedite` for an overdue order from a Gold customer leaves overdue orders from every other tier unassigned); list each uncovered case and ask—never fold it into a stated value or an unprovided default. Invalid input remains under rule 7. When the request says no one will answer (headless, CI), the no-folding rule lifts: map each uncovered case to the most defensible stated value rather than stopping and list each under Open questions as **[REQUIRED]**.
9. **Present finite decisions as options, with "Something else" last.** For solution, connector, trigger, or resource choices, ask with enumerated options, never open-ended; without a structured-question tool, use a numbered chat list. If nobody can answer (CI, headless), choose the recommended option and record it prominently; without a recommendation, stop and report the open decision, except an uncovered rule-8 case, which you still decide. Never auto-answer consent gates (destructive operations or tenant writes).
<!--skill-flavor:solution-lookup:start-->
10. **Look for an existing solution before `uip solution init`.** Run `find . -maxdepth 2 -name '*.uipx'`. If one exists, ask which to use—one option per solution, "Create a new solution", then "Something else"—and do not silently adopt, re-initialize, or repair it. The scaffold is in [SKILL.md](../SKILL.md#project-layout).
<!--skill-flavor:solution-lookup:end-->
11. **Never invoke another skill on your own.** When the flow needs an RPA process, an agent, or an app that does not exist, name the gap and hand the user what they need to switch skills.
12. **Batch independent calls; chain dependent ones.** Put scaffold, install, and registry search in one turn. In the next, chain `check`, each named `prepare`, re-`check`, `compile`, and `validate`; split only when a later step needs earlier output.

## Journeys

| Journey | Read |
| --- | --- |
| Create a new flow | [SKILL.md — Project layout](../SKILL.md#project-layout), then [SKILL.md — Lifecycle](../SKILL.md#lifecycle) (local gates: [`CLI-LOOP.md`](CLI-LOOP.md#local-authoring-hard-gates)) |
| Edit an existing flow (`.flow.ts` or raw `.flow`) | [`brownfield.md`](brownfield.md) |
| Add or change one node | Its row in [SKILL.md — Supported node types](../SKILL.md#supported-node-types) |
| Connector with tenant-specific fields | [`connector-params.md`](connector-params.md) + [`bindings.md`](bindings.md) |

### Count what the request names before building

Count named services, systems, documents, decisions, approvals, schedules, and computations. A domain/outcome and the project name are not steps. With zero steps, scaffold, compile the stub, validate, and report desired behavior as open questions; that is the finished deliverable. Do not invent a pipeline. With one or more, build all named steps; an adjacent outcome does not cancel one: "Check the weather for the Bellevue office and tell me if it's a nice day" names a lookup and a threshold decision; build both.

### Plan first only when the flow is complex

Plan before building when the flow has five or more nodes with branching/parallel paths, needs connector/resource discovery, or is ambiguous. Build directly for a single-node edit, linear pipeline, or specified topology; skipping a plan does not skip node choice. Use `.branch` for two outcomes, never a script ternary, and `.switch` for three or more; named external services follow rule 1.

A plan gives a one-line summary; node table (step, node, why); wiring; inputs/outputs; each connector and connection; and open questions. Get approval before building (rule 9, with "proceed" recommended).

A flow earns Maestro when it has several waits, branching/parallel paths, SLAs, cross-product composition, or per-case visibility. Say so before designing if a single-wait mostly linear process may be better as a queue plus Action Center.

### Patterns

Read its guide before choosing nodes when a new or edited flow has one of these shapes, including one inserted by the canvas ([`brownfield.md`](brownfield.md)); with two or more, also read [composing-guide.md](patterns/composing-guide.md).

| Pattern | Reach for it when | Guide |
| --- | --- | --- |
| `ai-decision-human-review` | An agent decides/proposes and a person reviews/approves before action | [guide](patterns/ai-decision-human-review-guide.md) |
| `routing-triage` | Emails, tickets, or claims are classified/routed, with human handling of low-confidence/unmatched items | [guide](patterns/routing-triage-guide.md) |
| `batch-ai` | An agent handles each list item and one bad item must not stop the rest | [guide](patterns/batch-ai-guide.md) |
| `conversational-intake` | Chat gathers or answers a request over several turns | [guide](patterns/conversational-intake-guide.md) |
| `parallel-agents` | Several AI agents work one input concurrently and one merges them | [guide](patterns/parallel-agents-guide.md) |
| `voice-agents` | A phone call or call line is handled by voice agents | [guide](patterns/voice-agents-guide.md) |

Do not use these for a linear pipeline, single node, human approval without an agent decision, agent classification without a requested person (`inlineAgent()` plus `.branch()` or `.switch()`), a field switch, or an edit adding none of them. `summarize()` and `batchTransform()` are single nodes, not patterns.

1. Adapt counts and branches to the request while retaining the guide's "Why it works", or state that you are building something else.
2. Shape tables mark steps **Entry**, **Mechanism**, or **Placeholder**. Entry is the pattern start/end: drop an Entry start if the flow already has one; drop an Entry End when steps follow and wire its inbound edge to them. Keep every Mechanism step. Choose a Placeholder by rule 1 or skip it when existing work covers it.
3. An agent is a published agent found by search, otherwise `inlineAgent()`; never `mock()`. Write its prompt; never decide its runtime answer while authoring.
4. An omitted threshold is an open question (rule 8): ask, or headless, use the guide's value and list it as **[REQUIRED]**.

## Variable types

Inputs, outputs, and vars take one of the six types the Flow CLI and Workbench offer: `types.string`, `types.number`, `types.boolean`, `types.object`, `types.array`, `types.file`.

- `float`, `double`, `date`, `datetime`, and `jsonSchema` are Case-only. The Flow builder rejects them with a TypeScript error and `DECLARATION_TYPE_NOT_FLOW` at build. Use `types.string` for dates, `types.number` for decimals, and `types.object` or `types.array` for `jsonSchema`, with shape in `{ schema }`, e.g. `{ type: types.object, schema: { type: 'object', properties: { id: { type: 'string' } } } }`. For an existing decompiled `.flow`, see [brownfield](brownfield.md#a-case-only-variable-type).
- `types.integer` builds and packs as integer but is unavailable in Workbench; prefer `types.number`.
- `types.any` is untyped; use only when no fixed type exists.
- A `types.file` value is a file reference `{ ID, FullName, MimeType, Metadata }`, never the content. Its file name is `.FullName`, not `.name`: `$vars.<triggerNodeId>.output.<inputName>.FullName`.

## Anti-patterns

- **Never replace a registered connector with `mock()` or a script because it is not configured.** Write `connector(...)`, run the `prepare` named by `check`, and if no live connection exists, report "prepare pending" as an open question. Reviewers and Studio Web need the real connector.
- **Never reuse a reference id from another flow/session** (mailbox folder, Slack channel, Jira project). IDs are scoped to the account behind the connection: a reused one compiles, validates, and faults at runtime. Resolve again with a `lookup()` token and the `prepare` named by `check`.
- **Never write an unresolved reference field.** On lookup failure (401/403 expired grant or 5xx), do not substitute display name, alias, or remembered value; stop and report the failed resolve.
- **Never reference parent values inside a subflow.** Pass them through `subflow(child, {...})` and read with `input(...)`. On `@uipath/maestro-builder-sdk` 6.100.0 or later, `check` on the calling flow reports a child's `$vars.start.output.<name>` or `input('<name>')` for any `<name>` the child does not declare, the parent's inputs included, as `SUBFLOW_PARENT_SCOPE_READ`; an older SDK compiles it, and it resolves to nothing.
- **Never debug a script with `console.log`.** `console.log` and its
  siblings exist but do nothing, so the output goes nowhere
  ([script runtime](script.md#the-javascript-runtime)). Return the value to
  inspect: `return { debug: value }`.
- **Never put every `$vars` reference in an End output or `{ updates }` expression inside double quotes.** `'No results for "' + $vars.start.output.topic + '".'` evaluates to null without warning (also inside `'…'` or a template literal); Decision and Switch conditions and an HTTP `url` are unaffected. Write the quote as `String.fromCharCode(34)`, or keep one reference outside the quoted text (`$vars.start.output.topic + ' "no results"'`).
- **Never rely on dotted JSON keys surviving `$vars`.** `{"5.3.0":"x"}` becomes `{"5":{"3":{"0":"x"}}}`; see [script.md](script.md#dotted-keys-in-values).
- **Never treat green `validate` as business-correctness proof.** It checks structure. Named outputs, reference IDs, and connector values require evidence from [`CLI-LOOP.md`](CLI-LOOP.md#bounded-completion).

## Completion output

When authoring ends, report:

1. **File paths** — `.flow.ts` source and emitted `.flow`.
2. **What was built** — steps, branches, and outputs in one or two sentences.
3. **Loop status** — last `check`, `compile`, and `validate` results, including each accepted warning and why.
4. **Placeholders** — every `mock()` and its capability.
5. **Connections** — for each connector, the `connection: <Name> (<id>)` line printed by `prepare` and its folder (candidate line or `uip is connections list <connector-key> --all-folders --output json`), or what is missing/still to prepare. A guessed connection ([bindings.md](bindings.md#where-both-values-come-from)) also goes under Open questions as **[REQUIRED]**.
6. **Open questions** — every decision the request left open, marked **[REQUIRED]** or **[OPTIONAL]**.
<!--skill-flavor:completion-next:start-->
7. **What's next** — if not specified, ask by rule 9: upload to Studio Web, debug, deploy to Orchestrator, or "Something else". Each hands off to [`operate.md`](operate.md). If specified ("publish it", "debug it"), select and act on it.
<!--skill-flavor:completion-next:end-->

## Narration and progress

Be silent by default; surface decisions, failures, consent gates, and the final result. Narrate each logical step in one plain-English line, and keep a step-level progress list, only when requested (verbose, show steps, track progress) or required by standing preference. A logical step is the smallest user-valued outcome, not its commands.

## API index lookups

The installed `@uipath/maestro-builder-sdk` package contains `dist/api-members.md` and `dist/api-index.md`. Rows look like:

```
| `outcomePorts` | property | `HitlInputs` | `dist/core/actions.d.ts:583-597` |
```

The path is package-root-relative. Each file header names its source repo/generator and says not to edit it; rows regenerate from declarations on every build.

Match one name, then read its full span—the declaration, doc comment, types, `@remarks`, and `@example`—to answer the question. Reading the span needs no search and no shell, so it works the same on Windows. Field/method names usually belong in `api-members.md` because it has one row per field. Both indexes cover all three entry points, including `/case` and `/bpmn`.

They live in the package, not `SKILL.md`, because spans are build-specific: declaration changes move lines, while the skill ships independently. An index beside the `.d.ts` files it points into cannot disagree with them. Read `.d.ts`, never `dist/*.js`; JavaScript has no types/comments and causes extra tool calls. A name absent from both indexes is probably a runtime output key (such as a human task's `Action` or error-envelope fields), documented in node references. Runtime-only decisions for sibling surfaces belong to `uipath-maestro-case` and `uipath-maestro-bpmn`; neither is needed to build a Flow.
