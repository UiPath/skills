# Decision graph support for `uipath-rules`

Plan to let the `uipath-rules` skill author a decision requirements graph: several decisions in one `.dmn`, linked by `informationRequirement`.

Repos read for this plan: `skills`, `cli`, `business-rules`, `PO.Frontend`, `Autopilot`.

## Current state

| Repo | State for a `.dmn` with several decisions |
|---|---|
| business-rules | Works. With no decision named, the engine evaluates the whole graph and returns one result per decision. |
| cli | `refresh` writes one whole-file entry point plus one per decision (`/<file>.dmn#<id>`). `debug` returns every decision. `validate` passes the file but skips the graph checks. No `rules format` command exists. |
| PO.Frontend | The diagram is behind the flag `canvas-enableBusinessRulesV2Drd`, default off. With the flag off, the file opens in Source view. `formatDrdXml` is on `develop` (#8326, MST-15586). |
| Autopilot | Hard-codes nothing about one decision. It pins `@uipath/skills-studioweb` and `@uipath/cli-browser`. |
| skills | Critical Rule 3 in `skills/uipath-rules/SKILL.md` forbids several decisions. The grader in `tests/tasks/uipath-rules/_shared/rules_check.py` rejects them too. |

### What a new rule holds today

One decision table, in every path:

- `uip rules init` seeds one decision with the marker `surface="decision-table"`.
- Autopilot's `CreateProjects` calls Unified Build, which takes its seed from `getStartDmnDiagram` in `PO.Frontend/src/utils/DmnDocumentTemplates.ts`. That function returns the same seed as `uip rules init`.
- Exception: with the start-screen flag on, `getStartDmnDiagram` returns an empty `definitions` element in an "uninitialized" namespace. The designer then shows a table-or-diagram start screen.

The designer picks its view from the file structure, not from the marker. A file with two decisions opens as a diagram even with a `decision-table` marker, and the designer rewrites the marker on the next save.

## Decisions

1. **No table-or-graph choice in the skill.** The agent models what the request needs. The init template and the marker stay as they are.
2. **Scope version 1 to decision tables.** Literal expressions and business knowledge models have their own designer flags, both off.
3. **Restrictions go in `validate`.** The skill carries a rule only when an eval proves it necessary.
4. **The agent writes no layout.** `uip rules format` places nodes, as `uip maestro bpmn format` did for the BPMN skill before the builder SDK.
5. **Keep direct XML editing.** No builder layer unless evals show agents damaging the diagram section.
6. **The skill ships before the designer flag turns on.** A graph opens in Source view until then.
7. **The Studio Web flavor gets the same rule.** Rule 3 sits outside the flavor blocks, so the flavor inherits the change with no override.

## Phase 1. Evals and grader (skills)

1. Generalize `tests/tasks/uipath-rules/_shared/rules_check.py`. `load_rule` fails on more than one decision. Add chain evaluation and unit tests.
2. Add a preservation check to the grader: shapes present before the edit are unchanged.
3. Add seven tasks:

| # | Task | Grades |
|---|---|---|
| 1 | Greenfield chain of two decisions | Each decision's output on test cases |
| 2 | Plain single-table request | Stays one decision |
| 3 | Add a decision to an existing table | Ids and entry points survive |
| 4 | Add a decision to a user-arranged graph | Existing shapes unchanged, no shape written by hand |
| 5 | Large policy, eight to ten decisions | Outputs, and `validate` passes |
| 6 | Repair a dangling requirement and a cycle | `validate` passes after the fix |
| 7 | Business knowledge model request | Whatever `validate` enforces |

### Phase 1 status

Written, not yet run with `coder-eval`. Every checker passes on a correct solution and fails on the untouched fixture, with `refresh` and `validate` run from CLI source.

| # | Task folder under `tests/tasks/uipath-rules/` |
|---|---|
| 1 | `smoke/graph_chain_author` |
| 2 | `smoke/greenfield_author`, which exists and already fails a rule with more than one decision |
| 3 | `smoke/graph_extend_table` |
| 4 | `smoke/graph_extend_arranged` |
| 5 | `integration/graph_large_policy` |
| 6 | `smoke/graph_repair` |
| 7 | `smoke/graph_unsupported_bkm` |

Grader: `_shared/graph_check.py` evaluates the tables in dependency order and compares shape positions with the fixture. `_shared/rules_check.py` gained `load_graph`, quoted lists, `not()`, and null handling in unary tests.

Tasks 1, 3, 4, and 5 fail by design against the current skill, because Rule 3 refuses several decisions. That run is the baseline for phase 2.

## Phase 2. Minimal skill change (skills)

1. Remove the refusal from Critical Rule 3 in `skills/uipath-rules/SKILL.md`. Keep it for business knowledge models, knowledge sources, decision services, and imports until `validate` rejects them.
2. Run the evals with `/skill-compare` against the current skill.
3. Sort each failure into a `validate` rule or one skill line.

## Phase 3. Validation (cli, PO.Frontend)

Details are deferred. Known gaps:

- **cli.** `packages/rules-tool/src/services/rules-validate-service.ts` calls `validateDmnDocument` without `allowDrdDocuments`, so the graph naming checks do not run.
- **PO.Frontend.** No rule exists for a cycle or for duplicate decision names. The publish gate does not validate decision logic inside a graph.
- **Unsupported elements.** Nothing rejects a business knowledge model, knowledge source, decision service, or import.
- **cli test.** `packages/rules-tool/tests/rules-debug.e2e.test.ts` asserts one decision.

## Phase 4. Layout (cli, PO.Frontend)

1. **cli.** Bump `@uipath/dmn-editor-utils` from 0.1246.8 to a version with the `/layout` export.
2. **cli.** Add `uip rules format <PROJECT_DIR>` over `formatDrdXml`. Default mode keeps placed nodes and places only nodes without a shape. A `--relayout` flag covers a user's explicit request to tidy the diagram.
3. **PO.Frontend, later.** Wrap wide rows and reduce edge crossings in `packages/dmn-editor/src/dmn/DrdLayout.ts`.

### Layout measurements

`formatDrdXml` run on ten test graphs:

| Scenario | Nodes | Result |
|---|---|---|
| Small, no shapes | 4 | Clean tree, 552 wide, no crossings |
| Init seed plus 2 added nodes | 4 | Seed nodes stay, new ones land beside them |
| User-arranged plus 1 added decision | 4 | User positions unchanged, new node above its input |
| Agent-written 200 by 120 grid | 4 | Kept as written, 1 overlap |
| 1 decision, 25 inputs | 26 | One row, 8,280 wide |
| 3 by 4 decisions, 6 inputs | 18 | 1,968 wide, 34 crossings |
| 5 by 8 decisions, 20 inputs | 60 | 6,600 wide, 1,264 crossings |
| 10 by 20 decisions, 60 inputs | 260 | 20,040 wide, 20,566 crossings |
| 60 placed plus 5 added | 65 | Existing nodes unchanged, no overlap |

The large graphs are random with three requirements per decision, so real policies cross less.

Findings:

- Every node that `format` placed had zero overlaps.
- `format` keeps a placed node even when it overlaps another. Only `--relayout` moves it, and that discards the user's arrangement.
- The designer draws a decision 288 by 96 and an input 216 by 96, whatever width and height the file holds.
- The layout puts each level in one row, with no wrap and no crossing reduction.

## Phase 5. Finish the skill (skills)

1. Add one line: never write `DMNDI`, and run `format` after the last edit. The loop becomes `format`, `refresh`, `validate`.
2. Add only the lines the evals proved necessary. Create `references/decision-graph-guide.md` only if they do not fit in `SKILL.md`.
3. Extend the review step to show the graph, then one table per decision.
4. Extend "Editing an Existing Rule": every decision id is an entry point.
5. Update the description and add rows to `tests/tasks/activation/uipath-rules.jsonl`.
6. Check `skill-flavors/studioweb/uipath-rules/SKILL.md` against the changed blocks.
7. Check the decision-keyed output text in `skills/uipath-maestro-bpmn/references/bpmn-runtime.md` and in the case skill.

## Phase 6. Autopilot

1. Bump the `@uipath/skills-studioweb` and `@uipath/cli-browser` pins.
2. Confirm the browser CLI bundle includes `rules format`.

## Open items

1. **Agent-written shapes.** Nothing catches a shape the agent writes against the skill line. Eval 4 measures how often it happens.
2. **Uninitialized seed.** The start-screen flag will be on. The seeded file in Studio Web is then an empty `definitions` element with `id="business-rule-uninitialized"`, `name=""`, and an "uninitialized" namespace, not a decision table. Undecided:
   - The Studio Web flavor tells the agent to keep the seeded root element. An agent that does so keeps the sentinel id, the empty name, and the sentinel namespace. The engine registers models by namespace and name, so two such rules can collide.
   - Who writes the real root: the agent, `uip rules refresh`, or a CLI command that Studio Web can run in place of `init`.
   - Which marker the file gets, because no author chose a table or a diagram on the start screen.
   - Whether `validate` rejects the sentinel namespace once the file holds a decision.

## Order

Phases 1 and 2 need nothing from other repos. Phase 5 step 1 waits on the `format` command from phase 4. Phases 3 and 4 run in parallel with the evals.
