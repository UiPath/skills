# Script → Source Text Map — uipath-maestro-flow

One row per rule, table, or constant a script would implement, mapped to the exact file and line span that supplies it. Paths are relative to `skills/uipath-maestro-flow/`. Line spans were read from the files at classification time — re-check them after any edit to the skill.

Twelve scripts (S1–S12) correspond 1:1 to the twelve procedures in `classification-details-uipath-maestro-flow.md`.

---

## S1 — `validate-mermaid-plan`

**In:** the mermaid block from the arch plan (+ optionally the plan's node/edge tables). **Out:** pass/fail + per-violation line and rule id.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | 12 syntax rules (graph LR not flowchart, ID charset, reserved words, plain labels, allowed shapes, edge-label form, no empty labels, unique subgraph ids, closed subgraphs, no semicolons, no blank lines) | `references/author/references/planning-arch.md` §Mermaid Validation Rules → Syntax Rules | 506–523 |
| 2 | Reserved-word list (`end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`) | same → Syntax Rules #3 | 510 |
| 3 | Forbidden label characters (`> < : ; ? & " ( ) [ ] { }`) | same → Syntax Rules #5 | 512–516 |
| 4 | Allowed shape set (`(text)`, `[text]`, `{text}` only) | same → Syntax Rules #6 | 517 |
| 5 | 6 structural rules (no orphans, both decision branches, all switch cases, loopBack shown, parallel fork/merge) | same → Structural Rules | 525–532 |
| 6 | The 11-step check order + "fix before outputting" gate | same → Validation Procedure | 534–548 |
| 7 | Shape-per-node-category mapping used when generating the diagram | same → §2 Flow Diagram (Mermaid), Requirements | 397–416 |
| 8 | Diagram↔table cross-check (every node/edge in the tables appears in the diagram) | same → §3 Node Table, §4 Edge Table (Rules) | 444–458, 472–476 |

---

## S2 — `route-node-ownership`

**In:** node type string(s) or a `.flow` file. **Out:** per node, `edit` | `cli`, plus a blocking warning when a full-file `Write` is planned over a flow containing CLI-owned nodes.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | User-owned type table (triggers, control flow, logic, HITL, patterns, agents, resource nodes, IxP, queue) | `references/author/CAPABILITY.md` §Node ownership | 26–38 |
| 2 | CLI-owned type table + the four prefixes (`uipath.connector.<key>.<op>`, `uipath.connector.trigger.*`, `uipath.connector.event.*`, `core.action.http.v2`) | same | 40–47 |
| 3 | Per-family rules (`node add` then `node configure`; re-configure is CLI-only; never full-file `Write`; label/edges/layout remain editable) | same | 49–57 |
| 4 | Canonical statement of the invariant | `SKILL.md` rule #9 | 96 |
| 5 | Tool Selection Ladder rungs 1–4 (incl. scripting-is-approval-gated) | `references/author/references/editing-operations.md` §Tool Selection Ladder | 5–12 |
| 6 | Per-operation default/alternative matrix (19 operations) | same §Strategy Selection Matrix | 33–59 |
| 7 | Ownership recap at build time | `references/author/references/greenfield.md` §Node ownership recap | 304–316 |

---

## S3 — `flow-mutate` (structural mutation engine)

**In:** `.flow` path, operation, operands, and a `registry get` payload when a new type is introduced. **Out:** mutated `.flow` (2-space indent preserved).

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | What the caller owns when not using CLI (definitions, node variables, edge cleanup, orphan cleanup, `targetPort`, `bindings_v2.json`) | `references/author/references/editing-operations-json.md` §Key Differences from CLI | 11–23 |
| 2 | 7-item pre-flight checklist (locate canonical `.flow` next to `project.uiproj`; definitions + `typeVersion` string match; unique camelCase id; both ports; End/Terminate outputs; `variables.nodes[]`; delete cascade) | same §Pre-flight Checklist | 26–41 |
| 3 | Add-a-node payload shape | same §Add a node | 99–187 |
| 4 | Delete-a-node payload + sweep | same §Delete a node | 188–198 |
| 5 | Add/delete-an-edge payload | same §Add an edge, §Delete an edge | 199–232 |
| 6 | Update-node-inputs semantics (in place; preserve node id) | same §Update node inputs | 233–252 |
| 7 | Variable operations (workflow variable, End-node output mapping, variable update) | same §Variable Operations | 253–325 |
| 8 | Node-instance schema (`id`, `type`, `typeVersion`, `display`, `inputs`, `outputs`; no `model` block) | `references/shared/file-format.md` §Node instance | 65–136 |
| 9 | `variables.nodes[]` entry shape `{id:"<nodeId>.<outputId>", type, binding{nodeId,outputId}}` and the one-entry-per-declared-output rule | same §Node outputs | 137–191 |
| 10 | Placeholder `layout.nodes` entry shape + format ownership | same §Layout | 192–227 |
| 11 | Edge schema + both-ports requirement + id-must-start-with-a-letter | same §Edge — both ports required | 228–245 |
| 12 | `definitions[]` rule (verbatim from registry, one per unique `type:typeVersion`) | same §Definition entry | 246–255 |
| 13 | Action-node standard `outputs` skeleton (`=result.response` / `=Error`) | `references/shared/action-nodes.md` §Standard JSON skeleton | 41–72 |
| 14 | Shared rules the mutation must honour (definitions, layout, edge rules, validate-once) | `references/author/references/editing-operations.md` §Shared Rules | 66–95 |
| 15 | The anchoring discipline the script makes obsolete (per-array anchor table, disjointness, uniqueness pre-flight) | `references/author/references/greenfield.md` §Anchoring parallel `.flow` Edits | 279–302 |
| 16 | Same, cross-referenced form | `references/author/references/editing-operations.md` §Parallel same-file Edits | 96–105 |
| 17 | 2-space indent on write | `references/author/references/editing-operations-json.md` §Canonical heredoc recipe | 74 |

---

## S4 — `flow-compose` (composite graph edits)

**In:** `.flow` path, recipe name, target node ids. **Out:** mutated `.flow`. Built on S3 primitives.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | Insert a node between two existing nodes (`Edit × 3`) | `references/author/references/editing-operations-json.md` §Insert a node between two existing nodes | 329–338 |
| 2 | Insert a decision branch (`Edit × 3`, true/false ports) | same §Insert a decision branch | 339–349 |
| 3 | Remove a node and reconnect (`Edit × 4`, incl. orphan-definition prune) | same §Remove a node and reconnect | 350–359 |
| 4 | Replace a mock with a real resource node (10 ordered steps, incl. `bindings[]`) | same §Replace a mock with a real resource node | 360–385 |
| 5 | Replace manual trigger with scheduled trigger (in-place type swap + definition swap) | same §Replace manual trigger with scheduled trigger | 386–405 |
| 6 | Create a subflow (parent node + `subflows.<id>` with own nodes/edges/variables/layout) | same §Create a subflow | 406–467 |
| 7 | Delete cascade order (nodes → edges → definitions → `bindings_v2.json`, with the shared-connector exception) | same §Pre-flight Checklist item 7 | 38 |
| 8 | Brownfield edit→recipe routing table | `references/author/references/brownfield.md` §Common edits | 30–52 |
| 9 | Subflow scope isolation (no parent `$vars` inside a subflow) | `references/shared/variables-and-expressions.md` §Subflow Scope | 563–568 |

---

## S5 — `check-topology`

**In:** `.flow` file (or plan node+edge tables). **Out:** list of illegal-wiring findings.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | Port table — 31 node types → input/output port names, incl. dynamic ports (`case-{id}`, `branch-{id}`, `loopBack`) | `references/author/references/planning-arch.md` §Standard Port Reference | 214–251 |
| 2 | `error` is implicit and off by default | same, note under the table | 252 |
| 3 | 12 wiring rules (trigger never a target; End/Terminate never a source; every non-trigger has an incoming edge; every non-terminal has an outgoing edge; decision exactly 2; switch one per case; loopBack; merge multi-in; no cycles except loopBack; no dangling nodes; error-port rule) | same §Wiring Rules | 256–271 |
| 4 | Port names by node type, second copy (registry is authoritative) | `references/shared/file-format.md` §Standard ports by node type | 282–305 |
| 5 | `error` edge ⇒ source node must carry `inputs.errorHandlingEnabled: true` | `references/shared/file-format.md` §Wiring the error port | 350–373 |
| 6 | Generic action-node port naming (`output` / `default` / `success` varies by plugin) | `references/shared/action-nodes.md` §Standard ports | 73–82 |
| 7 | Edge-table legality rules (every node a target once except trigger; a source once except End/Terminate) | `references/author/references/planning-arch.md` §4 Edge Table → Rules | 472–476 |
| 8 | Dynamic-port list restated | `references/author/references/editing-operations.md` §Edge rules | 83–88 |

> **Conflict to encode:** the HITL QuickForm output port is `completed` in `planning-arch.md` line 249 and in `diagnose/references/failure-modes.md` §HITL (132–148), but `outcome-completed` in `author/references/plugins/hitl/impl.md` lines 79 and 204. Accept both spellings and report the mismatch rather than picking one.

---

## S6 — `audit-expressions`

**In:** `.flow` file. **Out:** per-field findings with node id + JSON path.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | The rule: any `$vars.*` / `$metadata.*` / `$self.*` in a value field must start with `=js:` | `references/shared/node-output-wiring.md` §The Rule | 9–11 |
| 2 | Three observed bad forms and what each ships to runtime (incl. the invented `nodes.X.output.Y`) | same §What Goes Wrong Without `=js:` | 15–27 |
| 3 | Canonical pattern + accepted expression forms (whole object, field, array index, template literal, `$metadata`) | same §The Canonical Pattern / Examples | 31–52 |
| 4 | Per-node-type field matrix — 14 rows of required-YES vs required-NO fields (connector body/query/path params, managed HTTP, HTTP branches, decision, switch, End `outputs.<varId>.source`, variable updates, loop `collection`, subflow `inputs.<id>.source`, script body, inline-agent tokens) | same §Where the Rule Applies | 55–76 |
| 5 | Connector-input wiring reference (static vs variable vs mixed) | same §Connector Node Wiring — Quick Reference | 80–110 |
| 6 | 5 anti-patterns to detect, incl. `{ }` interpolation in connector/HTTP inputs and a quoted `=js:` | same §Anti-Patterns | 113–120 |
| 7 | Transform `inputs.collection` exception — path string, no `=js:` | same, note after the quick reference | 109 |
| 8 | The manual remedy the script replaces (`grep '"vars\.'` → patch → re-validate) | same §Validation Tip | 131–138 |
| 9 | Value-vs-condition split, second copy | `references/author/references/editing-operations.md` §Expression prefix rules | 107–112 |
| 10 | Symptom/cause/fix framing + the field list to sweep | `references/diagnose/references/failure-modes.md` §MST-9107 | 25–56 |
| 11 | Which half of this the CLI validator already catches (scope the script to the remainder) | same §`flow validate` passes… → **Caught** | 329–336 |

---

## S7 — `lint-jint`

**In:** `.flow` file. **Out:** per script node / expression, banned-construct findings.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | Supported construct list (operators, string/array/object/Math/JSON methods, template literals, destructuring, spread, arrow functions) | `references/shared/variables-and-expressions.md` §Jint Engine Constraints → Supported | 514–528 |
| 2 | Banned construct list (`fetch`, `XMLHttpRequest`, `setTimeout`, `setInterval`, `document`, `window`, `console`, `require`, `import`, `eval`, `Function`, `async`/`await`, `Promise`, bare `Date`) | same → Not Supported | 530–537 |
| 3 | Script body must `return` an object | `references/author/CAPABILITY.md` critical rule #7 | 69 |
| 4 | `console.log` unavailable | same, anti-patterns | 137 |
| 5 | 8 script-node rules — no `function main()` wrapper, `return` object, `$vars` global, ES2020/Jint, no `console.log`, no external calls, 30-second timeout, never name a variable `aggregate` | `references/author/references/plugins/script/impl.md` §Script rules | 31–42 |
| 6 | Expression contexts to lint besides script bodies (decision, switch, HTTP branch, variable updates, loop collection) | `references/shared/variables-and-expressions.md` §Expression Contexts | 434–509 |

---

## S8 — `build-resource-bindings`

**In:** `.flow` file (+ definitions already present). **Out:** emitted/verified top-level `bindings[]` pairs and a findings list.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | Which node families need bindings (`uipath.core.*`: rpa, agent, flow, agentic-process, api-workflow, hitl) | `references/shared/file-format.md` §Bindings — Orchestrator resource bindings | 513–518 |
| 2 | Entry shape (`id`, `name`, `type`, `resource`, `resourceKey`, `default`, `propertyAttribute`, `resourceSubType`) | same, JSON block | 519–542 |
| 3 | 6 rules — two entries per node, share on `(resourceKey, name)`, unique ids, no instance `model` block, `resourceKey` verbatim from the definition, `resourceSubType` per resource kind | same → Rules | 544–551 |
| 4 | Placeholder-resolution mechanics (`<bindings.{name}>` → `=bindings.<id>`) and the exact debug-time failure when absent | same → Why this is required | 553–555 |
| 5 | Definitions stay verbatim — do not rewrite placeholders inside `definitions[]` | same | 555–557 |
| 6 | Symptom → cause → fix for the missing-pair case; explicit statement that `flow validate` does not check it | `references/diagnose/references/failure-modes.md` §Missing `bindings[]` on resource node | 291–315 |
| 7 | Per-node-type concrete pair (worked example: RPA, `resourceSubType: Process`) | `references/author/references/plugins/rpa/impl.md` §Top-level `bindings[]` entries | 77–106 |
| 8 | Instance must not carry `model.context[]` | `references/author/CAPABILITY.md` anti-patterns | 133 |
| 9 | Connector-side binding surface, kept distinct from resource bindings | `references/author/references/plugins/connector/impl.md` §Bindings — top-level `.flow` `bindings[]` | 545–702 |

---

## S9 — `encode-parameter-values`

**In:** parent-field name/value pairs (from the api-type action's `{token}`s). **Out:** `parameterValues` tuple array + the raw-keyed copy for `bodyParameters`/`queryParameters`.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | When the activity has a parent-field-driven schema at all (both metadata locations: top-level `objectActions[]` with `ActionType: "Api"`, and `connectorMethodInfo.design.actions[]` with `actionType: "api"`) | `references/author/references/plugins/connector/impl.md` §Step 6c | 363–371 |
| 2 | Rule source selection (`source: field` vs `source: method`) | same | 372–376 |
| 3 | Substitution table applied longest-first: `:::`→`_sub_`, `[*]`→`_array`, `::`→`_sub_`, `.`→`_sub_` | same → Token encoding rule | 400–408 |
| 4 | Worked outputs (`fields.project.key`→`fields_sub_project_sub_key`, `items[*]`→`items_array`, `tenantEntityName` unchanged) | same | 409 |
| 5 | Complementary-copy rule — raw keys in `bodyParameters`/`queryParameters`, encoded keys in `parameterValues`; dropping the runtime copy yields `DAP-DT-_2003 refField with name <X> not found` | same | 411–418 |
| 6 | On-wire tuple shape `[[key, value], …]`, not an object map; inner keys camelCase | `SKILL.md` anti-patterns | 108 |
| 7 | Verified full payload shape | `references/author/references/plugins/connector/impl.md` §Step 6c → Shape | 420–517 |
| 8 | Re-configure is a full rebuild — the script must emit the complete `--detail`, never a patch | same §Step 6 note | 221–229 |
| 9 | Related key transform for connector params: strip `[*]` from a `requestFields[].name` and pass a `=js:` array expression | `references/author/CAPABILITY.md` anti-patterns | 145 |

---

## S10 — `wire-agent-inputs`

**In:** list of `$vars.<node>.output.<field>` sources. **Out:** `agentInputVariables[]`, `inputSchema.properties`, prompt tokens; plus a three-way alignment report.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | The three artifacts are hand-authored; CLI derives none of them; flatten rule `$vars.<trigger>.output.<var>` → `<trigger>__output__<var>` | `references/author/references/plugins/inline-agent/impl.md` §Wiring Flow Variables into Agent Prompts | 50 |
| 2 | Which mismatch `flow validate` catches vs which passes and faults at debug | same | 52 |
| 3 | Prerequisite — every bound trigger field must exist in `variables.globals[]` with `direction:"in"` + `triggerNodeId` | same | 54–60 |
| 4 | The four-row artifact table with exact shapes (`binding`, `inputSchema` key, `{{input.<key>}}`, `contentTokens` entry) | same | 62–67 |
| 5 | `content` ↔ `contentTokens` mirror invariant — regenerated by `uip agent refresh`, never hand-fixed (script must not emit it) | same §The `content` ↔ `contentTokens` mirror invariant | 71–83 |
| 6 | End-to-end worked example to test against | same §Worked example | 85–116 |
| 7 | 6 anti-patterns (never `{{ $vars.X }}`, brace-free `rawString`, keep node prompts as placeholders, declared type must match real output shape, `required` only when never empty, `binding` not `value`) | same §Anti-patterns | 124–131 |
| 8 | Token form in the shared wiring matrix (spaced-brace `{{ … }}`, not `=js:`) | `references/shared/node-output-wiring.md` §Where the Rule Applies, inline-agent row | 74 |

---

## S11 — `diagnose-run`

**In:** job key or instance id (+ folder key), path to the local `.flow`. **Out:** one consolidated report (incident, faulting element, variable state, correlated node with its inputs and upstream edges).

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | The fixed ladder order + stop condition | `references/diagnose/references/troubleshooting-guide.md` §Diagnostic priority | 7–14 |
| 2 | Step 1 — resolve instance id + folder key from `job status` | same §Step 1 | 16–24 |
| 3 | Step 2 — `instance incidents`, then `incident get`, optional `incident summary` | same §Step 2 | 26–44 |
| 4 | Step 3 — `instance variables`, optionally scoped by `--parent-element-id` | same §Step 3 | 46–58 |
| 5 | Step 4 — correlation: element id → `.flow` node, its `inputs`, upstream edges, inbound variable values; `instance asset` when local may differ | same §Step 4 | 60–75 |
| 6 | Step 5 — traces only as last resort | same §Step 5 | 77–85 |
| 7 | Exact subcommand surface and flag forms | same §CLI command reference | 87–115 |
| 8 | `--folder-key` mandatory on `instance` / `incident get`; never call APIs directly; fetch deployed asset when in doubt | `references/diagnose/CAPABILITY.md` §Critical rules | 20–25 |
| 9 | How to obtain FOLDER_KEY when absent | `references/shared/cli-conventions.md` §6 `--folder-key` requirement | 149–160 |
| 10 | Report contract — Studio Web URL and instance id as the first two lines, `<not returned by CLI>` when missing | `references/operate/references/run.md` §Reporting debug runs to the user | 44–55 |
| 11 | `--output json` + `--output-filter` extraction mechanics and the `Data`-shape traps the parsing must avoid | `references/shared/cli-conventions.md` §2, §3, §4 | 41–123 |

---

## S12 — `audit-flow-predebug`

**In:** `.flow` file. **Out:** findings for the conditions the skill says `flow validate` misses.

| # | What the script needs | Source | Lines |
|---|---|---|---|
| 1 | The authoritative not-caught list (reused reference ids; missing resource `bindings[]`; HITL completed port unwired; stale `layout`; open-schema output-path walks; wrong-direction reads) | `references/diagnose/references/failure-modes.md` §`flow validate` passes, `flow debug` faults → **Not caught** | 338–345 |
| 2 | The caught list — scope boundary, so the script does not duplicate the CLI | same → **Caught** | 329–336 |
| 3 | Missing `bindings[]` check (shares S8's rule set) | same §Missing `bindings[]` on resource node | 291–315 |
| 4 | HITL unwired-port check (symptom: flow blocks indefinitely) | same §HITL `completed` port unwired | 132–148 |
| 5 | Layout-size check thresholds: inline agents 288×96, containers 560×320, everything else 96×96; sticky notes exempt | same §MST-9061 → Fix | 111–125 |
| 6 | Same thresholds, authoring-side statement | `references/shared/file-format.md` §Layout → What format does | 220–224 |
| 7 | `errorHandlingEnabled` shape 1 (flag, no `error` edge) and shape 2 (error path rejoins happy path / shares the success terminal) | same catalog §Run reports `Completed` but the work never happened → Cause | 158–166 |
| 8 | Reference implementation of that check — already published as a copy-paste heredoc, port it verbatim | same → Fix | 172–201 |
| 9 | How to act on each finding line | same → Fix, bullet list | 204–210 |
| 10 | Error-path legality matrix (which targets are ✗ / ✓) | `references/shared/file-format.md` §Do not swallow the failure | 321–338 |
| 11 | Default-off policy — do not flag a node that handles no stated failure | same §Default: off | 312–320 |
| 12 | `variables.nodes[]` presence check (one per declared output; trigger `output` only, action `output`+`error`, End/terminate none) | `references/diagnose/references/failure-modes.md` §MST-9972 | 60–98 |
| 13 | Reused-reference-id heuristic + the re-resolve command to recommend | same §Reused reference ID | 219–246 |
| 14 | Warnings-are-defects gate (a zero exit with warnings is not "done"), incl. the connector-keyword warning | `SKILL.md` anti-patterns | 109 |

---

## Files carrying no scriptable procedure

Listed so the mapping is complete — every skill file is accounted for above or here.

| Area | Files | Why not scriptable |
|---|---|---|
| Capability routing, question/consent/narration protocol | `SKILL.md` 12–90, `references/shared/ux-narration-and-todos.md` (all) | Conversational policy and intent classification |
| Planning judgment | `references/author/references/planning-arch.md` 12–55, 275–384, 552–630; `references/author/references/planning-impl.md` (all) | Requirements interpretation, live discovery, approval gate |
| Per-node-type semantics | `references/author/references/plugins/**` (56 files) except the spans cited in S7/S8/S9/S10 | Selection criteria and input meaning per node type |
| Connector configuration workflow | `references/author/references/plugins/connector/impl.md` 54–360, 518–544, 703–738 | Live-tenant calls, field elicitation, filter semantics |
| Operate lifecycle | `references/operate/**` except `run.md` 44–55 | CLI calls, already chainable in one `Bash`; consent decisions |
| Evaluate | `references/evaluate/**` | CLI CRUD + run surface; `--only-failed` already implements the failure rules (`running-guide.md` 204–213) |
| CLI conventions | `references/shared/cli-conventions.md` 1–40, 124–177 | Binary/version probe already given as an inline snippet |
| Variables semantics | `references/shared/variables-and-expressions.md` 35–509, 543–727 | Schema teaching; `variables.nodes[]` regeneration is `flow format` |
| Skill-doc maintenance | `.maintenance/**` | Already fully scripted (`check-all.sh` orchestrates all 9 checkers); "Not loaded by agents during normal use" (`.maintenance/README.md` 3) |
