# Author — build and edit a flow with the builder SDK

Everything before a flow touches the cloud—scaffolding, node selection, `<Name>.flow.ts`, and [`CLI-LOOP.md`](CLI-LOOP.md)—ends when the emitted `.flow` validates. Publishing, running, and debugging are [`operate.md`](operate.md) and [`diagnose.md`](diagnose.md).

The builder owns `.flow` JSON: `compile` emits node definitions, `variables.nodes[]` entries resolving `$vars.<step>.output`, resource bindings, connector `inputs.detail`, and error flags. Authoring supplies node choice, topology, output meaning, and questions.

## Critical rules

1. **Choose the node before writing it, from a search, never from a brand name.** For an external service run `uip maestro registry search '<service>'`; prefer, in order: a curated connector, managed HTTP in connector mode, a connector built with `uip is connectors builder` for an authenticated REST+JSON API without a connector, manual HTTP otherwise (it keeps the credential in the flow, outside `uip is connections list`), and RPA only when no API exists (desktop app or terminal). For a tenant resource (agent, process, API workflow, IxP model), run the family's `uip maestro flow registry search`; it returns only published resources, so run `uip maestro flow registry pull --force` first and check solution projects with `uip maestro flow registry list --local` before declaring it missing. `mock()` means both searches proved the capability absent; never use it for a found capability.
2. **Read the node's reference before writing the step.** [SKILL.md](../SKILL.md#supported-node-types) maps each node to one reference and example. Copy tenant identity fields (keys, model names, folder keys); never construct them.
3. **Read the Integration Service contract before any `uip is` call.** Both are in [/uipath:uipath-platform](/uipath:uipath-platform), under `references/integration-service/`. `connections.md` covers selection, folder scoping, BYOA filtering, and empty-result recovery; after recovery, stop and report an open question if no healthy connection exists. `resources.md` covers reference lookups; finish pagination before reporting "not found".
4. **Edit the source, not the artifact.** Change `<Name>.flow.ts` and re-emit with `compile -o` for a new flow. Re-emit a pre-existing non-empty `.flow` with decompile and merge ([`brownfield.md`](brownfield.md)). Never hand-edit `.flow`, `content/*.bpmn`, `bindings_v2.json`, `entry-points.json`, `operate.json`, or `package-descriptor.json`; the CLI regenerates them. Route brownfield JSON through `decompile` ([`brownfield.md`](brownfield.md)). Non-interactive runs take the same route: nobody can approve a script over the `.flow`, so write a large node definition into the source. A node the builder cannot express is an SDK gap to report, not JSON to splice, unless its reference names a CLI route.
5. **Run the loop once the source is complete.** Use `check --source` while writing; on finished source and after the last edit run `check`, `compile`, and `validate`. `compile` does not run `check`, so clean `check` precedes every `compile`; brownfield edits use `--baseline <original.flow>` ([`brownfield.md`](brownfield.md#check-only-what-you-changed-check---baseline)). Ignore an error only when its message says to do so and the case applies (for example, false-positive `INLINE_AGENT_PROMPT_JSON_TEXT` when JSON is mentioned only as data). In emit-only mode, `check` refuses and `validate` is the gate. Treat every `validate` warning as failure unless the loop reference names it reviewed.
6. **Bind every declared output on every path.** Each `.return({...})` must name every key in `.output({...})`. `check` misses omissions; `compile` binds them to `$vars.<name>`, `validate` only warns (`EXPRESSION_DIAGNOSTIC`), and the run returns `undefined`.
7. **Handle an error only when the request says what should happen.** Add `.onError(...)` only for a stated failure ("if the call fails…", "return X for invalid input", "handle timeouts"); an unhandled failure must fault the run. A handler must recover genuinely or reach a caller-distinguishable terminal: a distinct `.return` or `.terminate`. Add `hitl` only when the request says the run waits for a person; post-run review (such as reviewing a drafted reply) is not `hitl`. This overrides `uipath-human-in-the-loop` Step 2b and its pattern guide; unstated signals go under Open questions.
8. **Never invent the business meaning of a named output or uncovered input case—ask.** If an output (`caseKey`, `severity`, `ticketId`) lacks derivation, ask or state and confirm an assumption; never guess pass-through or formatting. Check coverage across valid values of inputs read by stated rules: `High` over $500 and `Low` under $50 leaves $50 to $500; `Expedite` for an overdue Gold order leaves other tiers uncovered. List every uncovered case and ask; never fold it into a stated value or unstated default. Invalid input remains under rule 7. When the request says no one will answer (headless, CI), the no-folding rule lifts: map each uncovered case to the most defensible stated value rather than stopping, and list each under Open questions as **[REQUIRED]**.
9. **Present a finite decision as a list of options, with "Something else" last.** For solution, connector, trigger, or resource choices, ask with the enumerated choices, never as an open question; without a structured-question tool, use a numbered chat list. Headless/CI uses the recommended option and records it prominently in the final report; with no recommendation, stop and report the open decision, except rule-8 uncovered cases, which you still decide. Never auto-answer consent gates (destructive operations, tenant writes).
<!--skill-flavor:solution-lookup:start-->
10. **Look for an existing solution before `uip solution init`.** Run `find . -maxdepth 2 -name '*.uipx'`. If one exists, ask which to use with one option per solution, "Create a new solution", then "Something else"; do not silently adopt, re-initialize, or repair it. The scaffold is in [SKILL.md](../SKILL.md#project-layout).
<!--skill-flavor:solution-lookup:end-->
11. **Never invoke another skill on your own.** If an RPA process, agent, or nonexistent app is needed, name the gap and give the user what they need to switch skills.
12. **Batch independent calls; chain dependent ones.** Scaffold, install, and registry search go in one turn. In the next, chain `check`, each named `prepare`, re-`check`, `compile`, and `validate`; split only when a later step needs earlier output.

## Journeys

| Journey | Read |
| --- | --- |
| Create a new flow | [SKILL.md — Project layout](../SKILL.md#project-layout), then [SKILL.md — Lifecycle](../SKILL.md#lifecycle) (local gates alone: [`CLI-LOOP.md`](CLI-LOOP.md#local-authoring-hard-gates)) |
| Edit an existing flow (`.flow.ts` or raw `.flow`) | [`brownfield.md`](brownfield.md) |
| Add or change one node | The node row in [SKILL.md — Supported node types](../SKILL.md#supported-node-types) |
| Connector with tenant-specific fields | [`connector-params.md`](connector-params.md) + [`bindings.md`](bindings.md) |

### Count what the request names before building

Count named services, systems, documents, decisions, approvals, schedules, and computations. A domain/outcome ("shipment tracking", "our onboarding") and project name are not steps.

- **Zero steps: scaffold only.** Scaffold, compile the stub, and validate; do not invent a pipeline. Report requested behavior as open questions.
- **One or more steps: build all.** An adjacent outcome does not cancel a step; "Check the weather for the Bellevue office and tell me if it's a nice day" names a lookup and threshold decision.

### Plan first only when the flow is complex

Plan before building for five or more nodes with branching/parallel paths, connector/resource discovery, or ambiguity. Build directly for a single-node edit, linear pipeline, or stated topology. Skipping the plan never skips node choice. Two outcomes are `.branch`, not a script ternary; three or more are `.switch`; named external services follow rule 1.

A plan contains a one-line summary; node table (step, node, why); wiring; inputs/outputs; connectors and connections; and open questions. Get approval before building (rule 9, with "proceed" recommended).

**Is Maestro the right home?** Prefer it for several waits, branching/parallel paths, SLAs, cross-product composition, or per-case visibility. A single-wait, mostly linear process may be simpler as queue plus Action Center; say so before designing topology.

### Patterns

For a new flow or edit matching one of these shapes, or finishing one inserted by the canvas ([`brownfield.md`](brownfield.md)), read its guide before choosing nodes. For two or more, also read [composing-guide.md](patterns/composing-guide.md).

| Pattern | Reach for it when | Guide |
| --- | --- | --- |
| `ai-decision-human-review` | An agent decides/proposes an action and a person reviews/approves before action | [guide](patterns/ai-decision-human-review-guide.md) |
| `routing-triage` | Emails, tickets, or claims are classified/routed, with a person catching low-confidence or unmatched items | [guide](patterns/routing-triage-guide.md) |
| `batch-ai` | An agent handles each list item and one bad item must not stop the rest | [guide](patterns/batch-ai-guide.md) |
| `conversational-intake` | Chat gathers or answers a request over several turns | [guide](patterns/conversational-intake-guide.md) |
| `parallel-agents` | Several agents work one input and one merges them | [guide](patterns/parallel-agents-guide.md) |
| `voice-agents` | A phone call or call line is handled by voice agents | [guide](patterns/voice-agents-guide.md) |

These are not patterns for a linear pipeline, single node, human approval without an agent deciding, an agent classification without a person in the request (`inlineAgent()` plus `.branch()` or `.switch()`), a field switch, or an edit adding none of them. `summarize()` and `batchTransform()` are single nodes.

1. Adapt counts and branches to the request, preserve what the guide's "Why it works" names, or say you are building something else.
2. Shape tables mark each step **Entry**, **Mechanism**, or **Placeholder**. Entry is the pattern's start/end: drop Entry start when the flow already has one; drop Entry End when steps follow, wiring its inbound edge to them. Keep every Mechanism step. Choose Placeholder like any node (rule 1), or skip it when existing work covers it.
3. An agent step is a published agent found by search, otherwise `inlineAgent()`; never `mock()`. Write its prompt; never decide its runtime answer while authoring.
4. An omitted threshold is an open question (rule 8): ask, or headless, use the guide's value and list it as **[REQUIRED]**.

## Variable types

Inputs, outputs, and vars use the six Flow CLI/Workbench types: `types.string`, `types.number`, `types.boolean`, `types.object`, `types.array`, `types.file`.

- `float`, `double`, `date`, `datetime`, and `jsonSchema` are Case-only. The Flow builder refuses them with a TypeScript error and `DECLARATION_TYPE_NOT_FLOW` at build. Use `types.string` for dates, `types.number` for decimals, and `types.object` or `types.array` for `jsonSchema`, with shape in `{ schema }`, e.g. `{ type: types.object, schema: { type: 'object', properties: { id: { type: 'string' } } } }`. For an existing decompiled `.flow`, see [brownfield](brownfield.md#a-case-only-variable-type): `date`/`datetime` return as `types.string`; other types stop merge until retyped.
- `types.integer` builds and packs as integer but Workbench does not offer it; prefer `types.number`.
- `types.any` is untyped; use it only when the value has no fixed type.

## Anti-patterns

- **Never replace a registered connector with `mock()` or a script because it cannot be configured yet.** Write `connector(...)`, run the `prepare` named by `check`, and if no live connection exists report "prepare pending" as an open question. Reviewers and Studio Web need the real connector.
- **Never reuse a reference id from another flow or session** (mailbox folder, Slack channel, Jira project). IDs are connection-account scoped; resolve again with a `lookup()` token and the `prepare` named by `check`.
- **Never write an unresolvable reference field.** On lookup failure (401/403 expired grant or 5xx), do not substitute display name, alias, or remembered value; stop and report the failed resolve.
- **Never reference a parent's values inside a subflow.** Pass through `subflow(child, {...})` inputs and read with `input(...)`; `check` misses `$vars.start.output.*` reads in child scripts, which compile and resolve to nothing.
- **Never use `console.log` in a script.** The script runtime has no `console`, and `check` does not flag it. Return the value to inspect: `return { debug: value }`.
- **Never put every `$vars` reference of an expression inside double quotes.**
  An End-node `=js:` expression like `'No results for "' + $vars.start.output.topic + '".'`
  evaluates to null, with no warning. Keep at least one reference outside the
  quotes.
- **Never rely on a dotted JSON key surviving `$vars`.** Read through `$vars`,
  `{"5.3.0":"x"}` becomes `{"5":{"3":{"0":"x"}}}`. Pass the JSON as a string and
  `JSON.parse` it in a script.
- **Never treat green `validate` as business-correctness proof.** It checks structure; named outputs, reference IDs, and connector field values require evidence from [`CLI-LOOP.md`](CLI-LOOP.md#bounded-completion).

## Completion output

When authoring ends, report:

1. **File paths** — `.flow.ts` source and emitted `.flow`.
2. **What was built** — steps, branches, and outputs in one or two sentences.
3. **Loop status** — final `check`, `compile`, and `validate` results, including each accepted warning and why.
4. **Placeholders** — every `mock()` and its capability.
5. **Connections** — per connector, the `connection: <Name> (<id>)` line printed by `prepare` and its folder (candidate line or `uip is connections list <connector-key> --all-folders --output json`), or what is missing/still to prepare. A guessed connection ([bindings.md](bindings.md#where-both-values-come-from)) also goes under Open questions as **[REQUIRED]**.
6. **Open questions** — every unresolved decision marked **[REQUIRED]** or **[OPTIONAL]**.
<!--skill-flavor:completion-next:start-->
7. **What's next** — if not already specified, ask via rule 9: upload to Studio Web, debug the flow, deploy to Orchestrator, or "Something else". Each hands off to [`operate.md`](operate.md). If the request named the next step ("publish it", "debug it"), select and act on it.
<!--skill-flavor:completion-next:end-->

## Narration and progress

Be silent by default except for decisions, failures, consent gates, and the final result. Narrate each logical step in one plain-English line and maintain a step-level progress list only when requested (verbose, show steps, track progress) or when the user has a standing preference. A logical step is the smallest user-relevant outcome ("added the Slack step"), not its commands.

## API index lookups

The installed `@uipath/maestro-builder-sdk` package contains `dist/api-members.md` and `dist/api-index.md`. Rows use package-root-relative paths, for example:

```
| `outcomePorts` | property | `HitlInputs` | `dist/core/actions.d.ts:583-597` |
```

Each file header identifies its source repo/generator and says not to edit it there; builds regenerate rows from declarations. Match one name, then read the span — it is the whole declaration including its doc comment, so one read answers the question, with the types and the `@remarks` and `@example` bodies in full. No searching and no shell, so it works the same on Windows. Field/method names are usual because references have one row per field; `api-members.md` is usually the target. Both cover all three entry points, including `/case` and `/bpmn`.

The indexes live with the package rather than SKILL.md because spans are build-specific: declaration changes move lines, while the skill ships independently. Read `.d.ts`, never `dist/*.js`; JavaScript has no types/comments. A name in neither index is probably a RUNTIME output key (for example a human task's `Action` or error-envelope fields), found in node references. Runtime-only decisions for sibling surfaces belong to `uipath-maestro-case` and `uipath-maestro-bpmn`; neither is needed to build a Flow.
