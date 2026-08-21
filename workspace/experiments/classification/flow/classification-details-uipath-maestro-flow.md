# Classification Details — uipath-maestro-flow

**Classification: Partial**

---

## What the Skill Teaches

Build, edit, publish, run, diagnose, and evaluate UiPath Maestro Flow (`.flow`) projects through the `uip maestro flow` CLI plus direct `.flow` JSON authoring, organized as four capabilities (Author, Operate, Diagnose, Evaluate) with a 28-plugin per-node-type catalog.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Capability routing — map a request to Author / Operate / Diagnose / Evaluate | No | Intent classification; no fixed input→output mapping |
| 2 | User-interaction protocol — dropdown + "Something else", consent gates, narration and todo opt-in | No | Conversational policy, not a transform |
| 3 | "Is Maestro the right home?" gate and when-to-plan judgment | No | Requirements judgment |
| 4 | Node selection heuristics (connector → managed HTTP → RPA ladder, branch/transform/wait/human/agent choices) | No | Requires reading intent; ladder input is a live registry search |
| 5 | Topology pattern catalog (linear, branch, parallel+merge, loop, error, orchestration, scheduled, RPA bridge) | No | Design menu, chosen by judgment |
| 6 | Plan document structure (summary, node table, edge table, I/O table, connector summary, open questions) | Marginal | Table emission is mechanical once nodes/edges are decided, but content is generative |
| 7 | **Mermaid plan diagram — syntax + structural validation** | **Yes — VALIDATE/CHECK** | 12 syntax rules, reserved-word list, forbidden-character list, 11-step check procedure |
| 8 | Solution/project scaffold sequence + registration/layout verification | Marginal | Already a single chained `Bash`; the layout check is one `ls` |
| 9 | **Node ownership routing — node type → Edit/Write vs CLI** | **Yes — LOOKUP/REFERENCE-TABLE** | Two closed tables in `author/CAPABILITY.md`; wrong route silently corrupts `bindings[]` |
| 10 | **`.flow` structural mutation primitives (nodes, edges, definitions, variables, layout)** | **Yes — TRANSFORM-PIPELINE** | Fixed multi-array splice with a documented anchor-uniqueness discipline |
| 11 | **Composite graph edits (insert-between, decision branch, remove+reconnect, replace mock/trigger, subflow)** | **Yes — TRANSFORM-PIPELINE** | Each is an ordered `Edit × 3–4` recipe over the same JSON arrays, including the delete cascade |
| 12 | **Port + wiring legality (Standard Port Reference + 12 wiring rules)** | **Yes — VALIDATE/CHECK** | Port names are a closed table; rules are graph invariants |
| 13 | **Expression prefix contract (`=js:` per field/node type, forbidden forms)** | **Yes — DETECT** | Per-field required/forbidden table; `flow validate` covers only part of it |
| 14 | **Jint runtime constraints for script bodies and `=js:` expressions** | **Yes — DETECT** | Explicit supported/not-supported construct lists |
| 15 | Variables system semantics (directions, `globals`/`nodes`/`variableUpdates` schemas, subflow and loop scope) | No | Schema teaching; `variables.nodes[]` regeneration is already `flow format` |
| 16 | **Resource-node top-level `bindings[]` construction + presence audit** | **Yes — BUILD-MODEL/MATRIX** | Two entries per resource node, all fields derived from the registry definition |
| 17 | Connector configuration workflow (connection bind → describe → reference resolution → `--detail`) | No | Live-tenant calls, field selection, and user elicitation |
| 18 | **Connector `customFieldsRequestDetails` key encoding + `parameterValues` tuple shape** | **Yes — COMPUTE/FORMULA** | Fixed longest-first substitution table plus a fixed serialization shape |
| 19 | Connector filter trees / CEQL authoring | No | Query semantics from user intent |
| 20 | **Inline-agent input wiring triple + flatten rule** | **Yes — BUILD-MODEL/MATRIX** | Stated flatten rule and three aligned artifacts derived from one binding list |
| 21 | Inline-agent project lifecycle (`agent init/refresh/validate`, `resource.json`) | No | CLI calls |
| 22 | IxP node semantics (discovery, `fileRef` wiring, output field taxonomy) | No | Model-specific, registry-driven |
| 23 | HITL / trigger / control-flow / pattern node semantics (remaining plugin families) | No | Per-node-type domain knowledge |
| 24 | Error-handling design policy (default-off flag, do-not-swallow matrix) | Marginal | Audit already ships as a copy-paste heredoc in `failure-modes.md` |
| 25 | Ship — `resources refresh` → Studio Web upload vs `pack` + `publish` | No | CLI chain plus a consent decision |
| 26 | Debug run + mandatory reporting contract (Studio Web URL / instance ID first) | No | Consent-gated CLI call |
| 27 | Process run + job status/traces | No | CLI calls |
| 28 | Instance lifecycle (pause / resume / cancel / retry) | No | CLI calls, gated on prior diagnosis |
| 29 | **Diagnostic priority ladder + faulting-element→node correlation** | **Yes — TRANSFORM-PIPELINE** | Fixed 5-step chain where each call's arguments come from the previous call's JSON |
| 30 | **Pre-debug audit of the documented "not caught by `flow validate`" set** | **Yes — DETECT** | The skill enumerates exactly what validate misses |
| 31 | Failure-mode catalog reading (symptom → cause → fix) | Marginal | Lookup table, but symptom matching is fuzzy free text |
| 32 | Evaluate — evaluator types, JSON shapes, custom prompts | No | CLI CRUD + prompt authoring |
| 33 | Evaluate — eval sets, data points, `--criteria`, attachments, simulations | No | CLI CRUD |
| 34 | Evaluate — run start/status/results, compare, failure detection | Marginal | `--only-failed` already implements the failure rules |

---

## Codifiable Procedures (not yet scripted)

Each procedure below carries a **source-text map**: one entry per rule, table, or constant the script would implement, quoted verbatim from the skill with its line numbers. Paths are relative to `skills/uipath-maestro-flow/`. Quotes are reproduced exactly; `…` marks a gap between non-adjacent lines and ` […]` marks a line cut at 900 characters. Line numbers were read at classification time — re-verify after any edit to the skill.

### 1. Mermaid plan-diagram validator — VALIDATE/CHECK

**Source:** `references/author/references/planning-arch.md` §Mermaid Validation Rules

**What it does:** Takes the generated mermaid block from the architectural plan and returns pass/fail plus per-violation locations. Checks the first line is `graph LR`, node IDs match `[a-zA-Z0-9_]`, no ID starts with or equals a mermaid reserved word (`end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`), labels contain none of `> < : ; ? & ( ) [ ] { } "`, only `(text)` / `[text]` / `{text}` shapes appear, every edge uses `-->` or `-->|label|`, every `subgraph` is closed, no blank lines inside the block, and every node/edge in the plan's node and edge tables appears in the diagram. Line 504: "LLM-generated mermaid frequently contains syntax errors. After generating the diagram, **check every rule below** before presenting it to the user. Fix violations before outputting."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **The rule list the checker walks (12 syntax rules)** — `references/author/references/planning-arch.md` lines 506–523

   ```text
   506: ### Syntax Rules
   …
   508: 1. **First line must be `graph LR`** (horizontal — matches the Flow canvas) — use `graph` not `flowchart` (the `flowchart` keyword is not supported by all renderers).
   …
   523: 12. **No blank lines inside the mermaid block** — blank lines between node definitions and edges can prevent rendering in some mermaid implementations. Keep all lines contiguous.
   ```

2. **Reserved-word list** — `references/author/references/planning-arch.md` lines 510

   ```text
   510: 3. **Node IDs must not start with or equal a reserved word** — mermaid reserves these as keywords: `end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`. IDs that start with these (e.g., `endWarm`, `defaultPath`, `styleNode`) break the parser. Use alternatives like `warmEnd`, `pathDefault`, `nodeStyle` — or use a prefix like `done_warm`, `finish_warm`.
   ```

3. **Forbidden label characters** — `references/author/references/planning-arch.md` lines 512–516

   ```text
   512: 5. **No special characters in labels** — these break mermaid parsing even when quoted:
   513:    - `>` and `<` (interpreted as shape operators or HTML) — replace with words like "over" or "under"
   514:    - `(`, `)`, `[`, `]`, `{`, `}` (conflict with shape delimiters)
   515:    - `:`, `;`, `?`, `&`, `"` (unreliable across renderers)
   516:    - Use plain alphanumeric text and spaces only
   ```

4. **Allowed shape set** — `references/author/references/planning-arch.md` lines 517

   ```text
   517: 6. **Use only universally supported shapes** — `(text)` for rounded rectangle, `[text]` for rectangle, `{text}` for diamond. Do NOT use `([text])` (stadium), `{{text}}` (hexagon), or other extended shapes — they are not supported by all renderers.
   ```

5. **Structural rules** — `references/author/references/planning-arch.md` lines 525–532

   ```text
   525: ### Structural Rules
   …
   527: 1. **Every node defined must be connected** — no orphan nodes floating in the diagram
   …
   529: 3. **Decision nodes must show both branches** — `true` and `false` edges, each labeled
   …
   531: 5. **Loop structures**: show the loop body and the loopBack edge returning to the loop node
   ```

6. **The check order and the fix-before-output gate** — `references/author/references/planning-arch.md` lines 534–548

   ```text
   536: After generating the mermaid block:
   …
   538: 1. First line is `graph LR` — not `flowchart`
   539: 2. Check each node ID contains only `[a-zA-Z0-9_]`
   540: 3. Check no node ID starts with or equals a reserved word (`end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`)
   …
   547: 10. Check for blank lines inside the mermaid block — remove any empty lines between statements
   548: 11. If any rule is violated, fix it before outputting
   ```

7. **Shape per node category, used when emitting the diagram** — `references/author/references/planning-arch.md` lines 397–416

   ```text
   399: - Use `graph LR` (left-right) for all flows — Flow uses a horizontal canvas. Do NOT use `graph TD` (top-down) — it produces vertical diagrams that conflict with the horizontal node layout. Do NOT use `flowchart` — it is not supported by all mermaid renderers.
   …
   409: - Use only these universally supported node shapes:
   410:   - Triggers: rounded rectangle `(Trigger Name)`
   411:   - Actions: rectangle `[Action Name]`
   412:   - Control flow: diamond `{Decision Name}` for Decision/Switch
   413:   - End/Terminate: rounded rectangle `(Done)`
   414:   - Connectors: rectangle `[Connector Service Operation]`
   415:   - Placeholders: rectangle `[Mock Description]`
   ```

8. **Diagram↔table cross-check** — `references/author/references/planning-arch.md` lines 544–546

   ```text
   545: 8. Verify every node in the node table appears in the diagram
   546: 9. Verify every edge in the edge table appears in the diagram
   ```

**Why it's mechanical:** Every rule is a lexical or set-membership test over the diagram text, with the reserved words and forbidden characters enumerated in the doc; no interpretation of what the diagram means is required.

**Turn savings:** The agent currently re-reads its own diagram against 12 syntax rules and an 11-step procedure, then patches and re-checks — typically 1–3 turns, plus a rendering-failure round trip when a violation slips through. One script call replaces it.

---

### 2. Node ownership router — LOOKUP/REFERENCE-TABLE

**Source:** `references/author/CAPABILITY.md` §Node ownership — who authors the node

**What it does:** Takes one or more node types (or a whole `.flow` file) and returns, per node, the authoring tool: `Edit`/`Write` for user-owned types, `uip maestro flow node add` + `node configure` for the four CLI-owned families (`uipath.connector.<key>.<op>`, `uipath.connector.trigger.<key>.<trigger>`, `uipath.connector.event.<key>.<event>`, `core.action.http.v2`). Run over an existing file it also flags the dangerous case — a full-file `Write` planned against a flow containing CLI-owned nodes. Line 24: "Every node in a `.flow` file has exactly one author. The validator enforces this."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **User-owned type table** — `references/author/CAPABILITY.md` lines 26–38

   ```text
   24: Every node in a `.flow` file has exactly one author. The validator enforces this.
   …
   26: **User-owned nodes (Edit / Write directly):**
   …
   28: | Category | Node types |
   …
   30: | Triggers | `core.trigger.manual`, `core.trigger.scheduled` |
   …
   36: | Resource nodes | `uipath.core.rpa-workflow.*`, `uipath.core.agent.*`, `uipath.core.flow.*`, `uipath.core.agentic-process.*`, `uipath.core.api-workflow.*`, `uipath.core.human-task.*` |
   …
   38: | Queue | `core.action.queue.create`, `core.action.queue.create-and-wait` |
   ```

2. **CLI-owned type table and the four families** — `references/author/CAPABILITY.md` lines 40–47

   ```text
   40: **CLI-owned nodes (`uip maestro flow node add` + `uip maestro flow node configure`):**
   …
   42: | Category | Node types | Why |
   …
   44: | Connector activities | `uipath.connector.<key>.<op>` | `inputs.detail` is a `=jsonString:essentialConfiguration` envelope. Validate rejects hand-authored shapes. |
   45: | Connector triggers | `uipath.connector.trigger.<key>.<trigger>` | Same envelope + product-managed `bindings_v2.json` derivation. |
   46: | Wait for events (mid-flow) | `uipath.connector.event.<key>.<event>` | Same envelope and event metadata as a trigger, but placed mid-flow (has an `input` port) instead of as the start node. See [connector-trigger/impl.md — Wait for events](references/plugins/connector-trigger/impl.md#wait-for-events-uipathconnectoreventkeyevent). |
   47: | Managed HTTP | `core.action.http.v2` | Same envelope. |
   ```

3. **Per-family rules the router must state** — `references/author/CAPABILITY.md` lines 49–57

   ```text
   49: For CLI-owned nodes:
   …
   51: - Use `uip maestro flow node add` to insert the node and copy the definition into `definitions[]`.
   52: - Use `uip maestro flow node configure --detail '{...}'` to populate `inputs.detail` and `bindings[]`.
   53: - Subsequent edits to `inputs.detail` are also CLI-only — re-run `node configure` (it's a full rebuild; see [connector/impl.md](references/plugins/connector/impl.md)).
   54: - **Never `Write` (full-file rewrite) a flow that contains CLI-owned nodes** — it silently clobbers their `bindings[]` / `inputs.detail`, leaving a corrupted connection binding that `flow validate` passes but `flow debug` fails on. `Edit` user-owned nodes in place; if a `Write` is unavoidable, re-run `node configure` for every CLI-owned node as the **last** write to touch `inputs.detail` / `bindings[]` (a later `Write` re-clobbers what `configure` just fixed).
   55: - You may still `Edit` the node's `display.label`, edges, layout, and outputs — those are not part of the envelope.
   ```

4. **Canonical statement of the invariant** — `SKILL.md` lines 96

   ```text
   96: 9. **Every node has exactly one author — Edit/Write or CLI, never both.** Connector activities (`uipath.connector.<key>.<op>`), connector triggers (`uipath.connector.trigger.<key>.<trigger>`), wait for events (`uipath.connector.event.<key>.<event>` — a mid-flow event wait, configured exactly like a trigger), and managed HTTP (`core.action.http.v2`) are CLI-owned — use `uip maestro flow node add` + `uip maestro flow node configure`. Every other node type — triggers, control flow, logic, HITL, patterns, agents, resource nodes, queue — is user-owned: author the `.flow` JSON directly with `Edit` — or `Write`, but never a full-file `Write` on a flow that *also* contains CLI-owned nodes (it clobbers their CLI-set `bindings[]`/`inputs.detail`; `Edit` in place, or re-run `node configure` as the last step). `inputs.detail` on CLI-owned nodes is a `=jsonString:essentialConfiguration` envelope […]
   ```

5. **Tool Selection Ladder rungs** — `references/author/references/editing-operations.md` lines 5–12

   ```text
   7: > **Pick the lowest-numbered tool that fits the operation.** If no rung fits, stop and ask the user. Scripting languages (`python`, `node`, `jq`, `sed`, `awk`, shell heredocs) are a last resort and require explicit user approval — see rung 4.
   …
   10: > 2. **Any structural `.flow` mutation** (add/delete OOTB nodes, add/delete edges, add/edit variables, in-place value tweaks, output mapping, subflows, scheduled triggers, non-connector resources, inline-agent node/wiring) → `Edit`.
   11: > 3. **Wholesale file rewrite** (only when ≥70% of nodes change, e.g., scaffolding from a template) → `Write` — but never on a flow that already contains CLI-owned nodes (connector, connector-trigger, managed HTTP): the rewrite clobbers their CLI-owned `bindings[]` / `inputs.detail` and `flow validate` won't catch it. Use `Edit` (rung 2); if you do `Write`, re-run `node configure` **as the last write** to touch `inputs.detail` / `bindings[]` (a later `Write` re-clobbers it). See [CAPABILITY.md — Node ownership](../CAPABILITY.md#node-ownership--who-authors-the-node).
   12: > 4. **Anything else** → STOP and ask the user. A scripting language is a last resort: surface the trade-offs (state bypass, opaque diff, no interruption point) and present finite options — typically **Use `Edit` instead** / **Use `Write` (full rewrite)** / **Approve the script for this change** / **Cancel** / **Something else**. Only proceed after the user explicitly approves that path for this specific change. See the dropdown question rule in [SKILL.md](../../../SKILL.md).
   ```

6. **Per-operation default/alternative matrix** — `references/author/references/editing-operations.md` lines 33–59

   ```text
   39: | Add a node | **Edit / Write** | — | Flow CLI is not an option for non-carve-out node CRUD. |
   …
   45: | Update node inputs | **Edit** | — | In-place edit; preserves node ID and `$vars`. **Exception:** managed HTTP `inputs.branches` / `timeout` / `retryCount` must be set at `node add --input` time — to change them, `uip maestro flow node remove` and re-add with new `--input`. |
   46: | Add/edit workflow variable | **Edit** | — | Edit-only; CLI does not support. |
   …
   55: | **Configure a connector node** | **CLI** (carve-out) | — | `uip maestro flow node configure --detail` auto-populates `inputs.detail` + `bindings_v2.json`. Hand-authored `inputs.detail` skips `essentialConfiguration` and fails at runtime — no Edit fallback. |
   ```

7. **Ownership recap at build time** — `references/author/references/greenfield.md` lines 304–316

   ```text
   306: > **Before each node, classify it as user-owned or CLI-owned (see [CAPABILITY.md — Node ownership](../CAPABILITY.md#node-ownership--who-authors-the-node)). Connector activities, connector triggers, and `core.action.http.v2` are CLI-only — use `uip maestro flow node add` + `uip maestro flow node configure`, never Edit. Hand-writing these will fail `flow validate`.**
   ```

**Why it's mechanical:** The mapping is two closed tables plus four type-prefix patterns; the classification depends only on the node type string.

**Turn savings:** Today the agent re-reads the ownership tables (and the `Write`-clobbers-`bindings[]` warnings scattered across `CAPABILITY.md`, `greenfield.md`, and `editing-operations.md`) before each build, and pays a full repair cycle when it hand-authors `inputs.detail` — a validate failure plus a `node configure` recovery, 2+ turns.

---

### 3. `.flow` structural mutation engine — TRANSFORM-PIPELINE

**Source:** `references/author/references/editing-operations-json.md` §Primitive Operations, §Pre-flight Checklist; `references/author/references/greenfield.md` §Anchoring parallel `.flow` Edits

**What it does:** Applies one primitive mutation (add node, delete node, add edge, delete edge, update node inputs, add variable, add output mapping, add variable update) to the `.flow` JSON, touching every array the operation implies in one pass: `nodes[]`, `edges[]` (with `sourcePort`/`targetPort` set), `definitions[]` (pasted verbatim from a `registry get` payload, one entry per unique `type:typeVersion`), `variables.nodes[]` (one `{id, type, binding{nodeId,outputId}}` entry per output), and a placeholder `layout.nodes` entry. Line 97: "Several recipes below touch more than one top-level array at once (Add a node hits `nodes[]`, `definitions[]`, `variables.nodes`, and `layout.nodes`)."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **What the caller owns when not using the CLI** — `references/author/references/editing-operations-json.md` lines 11–23

   ```text
   13: When editing the `.flow` file with `Edit` / `Write`, **you** are responsible for everything the CLI normally handles:
   …
   17: | Definitions | Auto-copied from registry cache | Copy the returned node definition object from `uip maestro flow registry get` into `definitions` array |
   18: | Node variables | Auto-added to `variables.nodes` | Add output variable entries manually (or accept that `variables.nodes` may need regeneration) |
   19: | Edge cleanup on delete | Auto-removes connected edges | Find and remove all edges referencing the deleted node |
   20: | Orphan cleanup | Auto-removes unused definitions and orphaned bindings | Remove definitions no longer referenced by any node; remove connector bindings only when no remaining node uses that connector |
   21: | `targetPort` | Auto-set | Set `targetPort` on every edge (validate rejects without it) |
   ```

2. **Pre-flight checklist items 2–7** — `references/author/references/editing-operations-json.md` lines 26–41

   ```text
   33: 2. **Definitions and versions.** For every new node type, run `uip maestro flow registry get <type> --output json`. Copy the returned node definition object **verbatim** into `definitions[]` — one entry per unique `type:typeVersion`. Depending on CLI/plugin version, the node definition may appear as `Data.Node` or as the top-level object containing fields such as `nodeType`, `version`, and `handleConfiguration`; copy that node object, not the surrounding `Result` / `Code` envelope. Then set each node instance's `typeVersion` to match the copied definition's `version` exactly — string match, no normalization. Never hand-write or paraphrase definitions (see "Every node type needs a `definitions` entry" in [the Author capability index](../CAPABILITY.md)). For node types with a documented `uip maestro flow node add` carve-out (managed HTTP, connector activities, connector triggers), use the […]
   34: 3. **Unique node ID.** Pick a camelCase ID that does not collide with existing node IDs. Prefer meaningful names (`fetchUsers`, `filterActive`) since they become part of every `$vars.<nodeId>.*` expression.
   35: 4. **`sourcePort` and `targetPort` on every edge.** Omitting `targetPort` is the #1 validation error (see "`targetPort` is required on every edge" in [the Author capability index](../CAPABILITY.md)). Use `sourcePort`, never `sourceHandle`; `sourceHandle` is not part of the `.flow` edge schema and produces a precise schema error such as `[error] [edges[N].sourcePort] Invalid input: expected string, received undefined` (the path tells you exactly which edge entry is missing the `sourcePort` key). Look up ports in the relevant plugin's `planning.md` or in [file-format.md — Standard ports](../../shared/file-format.md). If an edge uses `sourcePort: "error"`, the source node must also have `inputs.errorHandlingEnabled: true`; `uip maestro flow format` self-heals this, but direct JSON edits must set it. Only those nodes — setting the flag on a node with no `error` edge swallows its failures […]
   …
   37: 6. **`variables.nodes[]` (REQUIRED for every data-producing node — this is what powers `$vars.X.output`).** For each data-producing node, add an entry per output (`output` for action / trigger nodes, plus `error` for action nodes). The BPMN emitter walks `variables.nodes[]` to write the process-level `<uipath:inputOutput id="<nodeId>.<outputId>">` declarations the runtime needs; without them, downstream `$vars.<sourceNodeId>.output` resolves to `undefined` even though `flow validate` passes (MST-9972). The shape per entry: `{ "id": "<nodeId>.<outputId>", "type": "object", "binding": { "nodeId": "<nodeId>", "outputId": "<outputId>" } }`. After your edits, **`uip maestro flow format` regenerates this block from `nodes[]` + `definitions[]`** — running format makes any direct-authored omission self-healing.
   38: 7. **On delete — cascade manually.** Remove the node from `nodes`. Then sweep `edges[]` for any with matching `sourceNodeId`/`targetNodeId`. Then prune `definitions[]` if this was the last user of the type. Then check `bindings_v2.json` — but only remove a connector binding if no remaining node uses the same connector (bindings are shared at the connector level).
   ```

3. **Add a node — arrays touched and the definition copy step** — `references/author/references/editing-operations-json.md` lines 99–187

   ```text
   101: **Tool:** `Edit` (insert into `nodes[]` + `definitions[]` + `variables.nodes` + `layout.nodes`)
   …
   103: 1. Run `uip maestro flow registry get <node-type> --output json` and copy the returned node definition object (`Data.Node` or the top-level node object, depending on CLI/plugin version)
   104: 2. Use `Edit` to add a node entry to the `nodes` array:
   ```

4. **Delete a node — full cascade** — `references/author/references/editing-operations-json.md` lines 188–198

   ```text
   190: **Tool:** `Edit` (remove from `nodes[]` + dependent edges + orphaned definitions + `variables.nodes` + `variableUpdates`)
   …
   192: 1. Use `Edit` to remove the node object from `nodes`
   193: 2. Remove **all edges** where `sourceNodeId` or `targetNodeId` equals the node's `id`
   194: 3. If no other node uses the same `type`, remove the definition from `definitions`
   195: 4. Remove the node's entry from `variables.nodes`
   196: 5. Remove any `variableUpdates` entries keyed by the node's `id`
   197: 6. If the node is a connector node, remove its binding from `bindings_v2.json` **only if no other node in the flow uses the same connector**. Bindings are shared at the connector level (keyed by `metadata.Connector`), not per node.
   ```

5. **Add an edge — id pattern and the four criticals** — `references/author/references/editing-operations-json.md` lines 199–226

   ```text
   201: **Tool:** `Edit` (insert into `edges[]` with `targetPort`)
   …
   207:   "id": "edge_<SOURCE_NODE_ID>_<SOURCE_PORT>_<TARGET_NODE_ID>_<TARGET_PORT>",
   …
   215: **Critical:** the edge `id` MUST match the pattern above — never a bare UUID or any id starting with a digit.
   …
   217: **Critical:** `targetPort` is required on every edge. Omitting it produces a validation error.
   …
   219: **Critical:** the outgoing port field is named `sourcePort`, not `sourceHandle`. `sourceHandle` is a UI/runtime term, not valid `.flow` JSON.
   …
   221: **Critical:** for `sourcePort: "error"`, also set `inputs.errorHandlingEnabled: true` on the source node. Without the flag, Studio Web hides the source handle and `uip maestro flow validate` fails. The converse is equally strict: **never set the flag on a node that has no `error` edge** — it suppresses the node's fault and the run reports success while the work failed. See [file-format.md — Default: off](../../shared/file-format.md#default-off--enable-only-for-a-failure-the-flow-actually-handles).
   ```

6. **Update node inputs — in place, id preserved** — `references/author/references/editing-operations-json.md` lines 233–252

   ```text
   235: **Tool:** `Edit` (in-place value tweak — preserves node ID and `$vars`)
   …
   237: Use `Edit` to modify the `inputs` object of the target node in-place. No need to delete and re-add.
   …
   249: This is a key advantage of `Edit` — input updates are a single field edit, not the delete + re-add pattern required by the CLI.
   ```

7. **Variable operations — Edit-only, no CLI fallback** — `references/author/references/editing-operations-json.md` lines 253–325

   ```text
   255: These are `Edit`-only — the CLI does not support variable management. There is no fallback strategy.
   …
   283: Use `Edit` to map every `out` variable in `variables.globals` on every reachable End node:
   …
   306: Use `Edit` to add an entry to `variables.variableUpdates.<NODE_ID>`:
   ```

8. **Node-instance schema** — `references/shared/file-format.md` lines 65–136

   ```text
   65: ## Node instance
   …
   69:   "id": "rollDice",
   70:   "type": "core.action.script",
   71:   "typeVersion": "1.0",
   72:   "display": { "label": "Roll Dice" },
   ```

9. **`variables.nodes[]` recipe and why it is the runtime contract** — `references/shared/file-format.md` lines 137–191

   ```text
   141: The canonical recipe for a data-producing node is therefore:
   …
   143: - `definitions[]` entry copied verbatim from `uip maestro flow registry get` (carries the manifest `outputDefinition`).
   144: - `variables.nodes[]` entry per output: `{ "id": "<nodeId>.<outputId>", "type": "object", "binding": { "nodeId": "<nodeId>", "outputId": "<outputId>" } }`.
   …
   147: Skipping `variables.nodes[]` produces a flow that passes `flow validate` but resolves `$vars.<sourceNodeId>.output` to `undefined` at runtime (MST-9972). `uip maestro flow format` regenerates `variables.nodes[]` from `nodes[]` + `definitions[]`, so always run it after structural edits — the omission becomes self-healing.
   ```

10. **Layout is owned by `flow format`; placeholder is fine** — `references/shared/file-format.md` lines 192–227

   ```text
   194: Node positioning is stored in a **top-level `layout` object**, keyed by node `id`. The same shape applies inside each subflow as `subflows[<id>].layout`. Layout data is owned by `uip maestro flow format` (see [cli-commands.md](cli-commands.md#uip-maestro-flow-format)) — you should not need to hand-write it.
   …
   218: Each key in `layout.nodes` is a node `id`. `flow format` creates an entry for every node and populates `position` + `size`.
   ```

11. **Edge schema gotchas** — `references/shared/file-format.md` lines 228–245

   ```text
   240: > **Gotcha**: `targetPort` is required. Omitting it produces `[error] [edges[N].targetPort] Invalid input: expected string, received undefined` at validate time.
   …
   242: > **Gotcha**: the source field is `sourcePort`, not `sourceHandle`. If you write `sourceHandle`, validation fails with `[error] [edges[N].sourcePort] Invalid input: expected string, received undefined` — the path identifies the offending edge entry exactly.
   …
   244: > **Gotcha — edge `id` MUST start with a letter (XML NCName).** Never use a bare UUID or any id with a leading digit (`"12bd09dd-…"`, `"1edge-start"`). Edge ids become BPMN `<bpmn:incoming>/<bpmn:outgoing>` IDREFs; a leading digit makes the converter silently drop those references while still emitting the `sequenceFlow`, so `flow validate` passes and upload succeeds — but the engine cannot traverse: the run reports **Completed having executed only the start node**, every output null. Use descriptive ids (`e-<source>-<target>`, e.g. `e-start-agent`); prefixing a letter (`e12bd09dd-…`) also works. Same rule applies to node ids.
   ```

12. **Definitions come from the registry, one per unique type** — `references/shared/file-format.md` lines 246–255

   ```text
   248: Every node type appearing in `nodes` must have a matching entry in `definitions`. Get the correct definition from:
   …
   254: Copy the returned node definition object into your `definitions` array. Depending on CLI/plugin version, that object may appear at `Data.Node` or as the top-level object containing fields such as `nodeType`, `version`, and `handleConfiguration`. Do not write definitions by hand — always pull from the registry to ensure schema compliance.
   ```

13. **Action-node `outputs` skeleton** — `references/shared/action-nodes.md` lines 41–72

   ```text
   43: All action nodes share this base shape on the node instance:
   …
   69: `outputs.output` documents the success payload referenced downstream as `=js:$vars.{nodeId}.output`. `outputs.error` documents the failure shape; the runtime routes to the implicit `error` port when the action faults. See [Implicit error port on action nodes](file-format.md#implicit-error-port-on-action-nodes).
   ```

14. **Shared rules the mutation must honour** — `references/author/references/editing-operations.md` lines 66–95

   ```text
   72: - Every unique `type:typeVersion` pair in `nodes` must have a matching entry in `definitions`
   73: - Definitions come from `uip maestro flow registry get <node-type> --output json` — copy the returned node definition object (`Data.Node` or the top-level node object, depending on CLI/plugin version)
   74: - **Never hand-write definitions** — hand-written definitions cause validation failures
   …
   79: - Layout (`layout.nodes`, `subflows[<id>].layout`) is owned by `uip maestro flow format` — do not hand-compute coordinates
   80: - When authoring a node, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); format rewrites it on save
   …
   85: - `targetPort` is required on every edge — validate rejects edges without it
   …
   91: - Run `uip maestro flow validate <ProjectName>.flow --output json` **once** after all edits complete
   92: - Do not validate after each individual edit — intermediate states are expected to be invalid
   ```

15. **The anchoring discipline the script makes obsolete** — `references/author/references/greenfield.md` lines 279–302

   ```text
   281: > **Do not assume a top-level key order.** The CLI does not guarantee which keys are present or in what sequence — fixtures show `runtime` before `nodes` on one flow and absent on another, and `bindings` / `variables` / `solutionId` / `projectId` / `metadata` appear in varying positions. Any anchor of the form "closing `]` + the NEXT top-level key" is coupled to that ordering and will silently break across CLI versions or between flows. **Anchor on the target array's OWN key instead — you just `Read` the file at the top of T2, so anchor to text that read actually contains.**
   …
   283: Anchor each Edit using its target array's own opening key, located in the text you just Read — not adjacency to a neighbor key. The catch: `"nodes": [` and `"edges": [` are NOT unique in the file. They recur **inside inline `definitions[]`** (an HTTP v2 / agent / subprocess definition embeds its own nested `nodes`/`edges`) **and inside any `subflows.<id>` block** (each subflow holds its own `nodes`/`edges`) — so even a small flow can carry several copies. The reliable, version-independent discriminator is **indentation: the top-level array sits at 2-space indent; every nested one is deeper.** `"definitions": [` and the top-level `"layout": {` appear once each, so they need no disambiguation.
   …
   294: **Disjointness rule.** Two parallel Edits MUST anchor on DIFFERENT top-level arrays — nodes-Edit on the top-level `nodes[]`, edges-Edit on the top-level `edges[]`, definitions-Edit on `definitions[]`, layout-Edit on `layout.nodes`. Because each anchors on its own array (not a shared boundary), the parallel Edits never overlap — provided each anchor is unique first (see below).
   …
   296: **Pre-flight uniqueness check.** Before submitting an Edit, confirm your `old_string` appears **exactly once** in the file you Read. `"definitions": [` and the top-level `"layout": {` are reliably unique. `"nodes": [` and `"edges": [` are NOT — they recur inside inline definitions and subflows, so anchor on the **2-space-indented** occurrence and extend through the first element's opening (e.g. `"id": "start"`) until the match count is one. Never anchor on a bare bracket shape, and never assume the first textual occurrence is the top-level one.
   ```

16. **Same rules, cross-referenced form** — `references/author/references/editing-operations.md` lines 96–105

   ```text
   100: - **Same-file Edits serialize in execution order** — they do not race, but each later Edit runs against the text the earlier ones already changed. An `old_string` that overlaps text a prior Edit removed or shifted fails with "string not found."
   101: - **Anchor each Edit on its target array's OWN opening key** (`"nodes": [`, `"edges": [`, `"definitions": [`, or `layout.nodes`), located in the text you just `Read` — never on "the key that follows X." Top-level key order and presence are not guaranteed (see [file-format.md](../../shared/file-format.md#top-level-structure)).
   102: - **`"nodes": [` and `"edges": [` are NOT unique** — they recur inside inline `definitions[]` and inside any `subflows.<id>` block. Anchor on the 2-space-indented (top-level) occurrence and extend until the match is unique.
   103: - Insert at the array's head (right after `[`) so the `old_string` never spans the array's closing `]`.
   ```

17. **2-space indent on write** — `references/author/references/editing-operations-json.md` lines 74

   ```text
   74: `json.dump(..., indent=2)` matches the file's existing 2-space indent — `flow format` normalizes layout but does not re-indent unrelated structure, so preserve the canonical 2-space indent on writes.
   ```

**Why it's mechanical:** The target arrays, the entry shapes, and the field values are fully specified by the operation plus the registry payload; the whole anchor-uniqueness discipline exists only because the mutation is done by text substitution rather than by parsing JSON, and disappears once the file is loaded as a structure.

**Turn savings:** A single node addition is currently one `Read` plus up to four parallel anchored `Edit` calls (2 turns), with a documented failure mode — "confirm your `old_string` appears **exactly once** in the file you Read" (line 296) — whose recovery costs a re-`Read`, a re-derived anchor, and a re-submit; the doc's own advice is to spend an extra turn preemptively. One script call per mutation removes both the turns and the failure mode.

---

### 4. Composite graph-edit recipes — TRANSFORM-PIPELINE

**Source:** `references/author/references/editing-operations-json.md` §Composite Operations

**What it does:** Executes one named graph rewrite end-to-end: insert a node between two connected nodes (drop the connecting edge, add the node, add two edges), insert a decision branch (drop an edge, add the decision node, add `true`/`false`/incoming edges), remove a node and reconnect (record neighbours, remove node, sweep edges, prune orphan definitions, add the bypass edge), replace a `core.logic.mock` with a real resource node, replace a manual trigger with a scheduled trigger, or create a subflow. Line 331: "**Tool:** `Edit` × 3 (delete old edge, add new node, add 2 new edges)"; line 352: "**Tool:** `Edit` × 4 (delete node, sweep edges, prune orphan definitions, add reconnect edge)"; the delete cascade is spelled out at line 38: "**On delete — cascade manually.** Remove the node from `nodes`. Then sweep `edges[]` for any with matching `sourceNodeId`/`targetNodeId`. Then prune `definitions[]` if this was the last user of the type."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **Insert a node between two existing nodes** — `references/author/references/editing-operations-json.md` lines 329–338

   ```text
   331: **Tool:** `Edit` × 3 (delete old edge, add new node, add 2 new edges)
   …
   333: 1. Use `Edit` to remove the edge connecting the two nodes from the `edges` array
   334: 2. Use `Edit` to add the new node to `nodes` (with definition in `definitions`)
   335: 3. Use `Edit` to add two new edges:
   ```

2. **Insert a decision branch** — `references/author/references/editing-operations-json.md` lines 339–349

   ```text
   341: **Tool:** `Edit` × 3 (delete old edge, add decision node, add 3 new edges)
   …
   343: 1. Use `Edit` to remove the edge where the branch should go
   344: 2. Use `Edit` to add the decision node to `nodes` with `inputs.expression`
   345: 3. Use `Edit` to add three edges:
   ```

3. **Remove a node and reconnect** — `references/author/references/editing-operations-json.md` lines 350–359

   ```text
   352: **Tool:** `Edit` × 4 (delete node, sweep edges, prune orphan definitions, add reconnect edge)
   …
   354: 1. Record the node's upstream and downstream connections from `edges`
   355: 2. Use `Edit` to remove the node from `nodes`
   356: 3. Use `Edit` to remove all edges referencing the node
   357: 4. Use `Edit` to clean up orphaned definitions
   358: 5. Use `Edit` to add a new edge connecting upstream directly to downstream
   ```

4. **Replace a mock with a real resource node** — `references/author/references/editing-operations-json.md` lines 360–385

   ```text
   362: **Tool:** `Edit` (multiple calls — replace node, edges, definitions, bindings, variables)
   …
   373: 3. Remove the mock node from `nodes`
   374: 4. Remove all edges referencing the mock
   375: 5. Add the real resource node to `nodes` with:
   …
   380: 6. Copy the definition from registry into `definitions`
   381: 7. Add entries to the top-level `bindings[]` array — two per resource (`name` + `folderPath`), with `resourceKey` matching the definition's `model.bindings.resourceKey`
   …
   383: 9. Add node variables to `variables.nodes`
   ```

5. **Replace manual trigger with scheduled trigger** — `references/author/references/editing-operations-json.md` lines 386–405

   ```text
   388: **Tool:** `Edit` × 2 (start node in-place, swap definition)
   …
   390: Use `Edit` to modify the start node in-place (no delete/re-add needed):
   …
   392: 1. Change `type` from `core.trigger.manual` to `core.trigger.scheduled`
   …
   402:    - Remove the `core.trigger.manual` definition
   403:    - Add the `core.trigger.scheduled` definition from `uip maestro flow registry get core.trigger.scheduled --output json` (the new definition carries the correct `model.type` and `model.eventDefinition`)
   ```

6. **Create a subflow** — `references/author/references/editing-operations-json.md` lines 406–467

   ```text
   408: **Tool:** `Edit` (or `Write` if scaffolding from template)
   …
   410: 1. Use `Edit` to add a `core.subflow` parent node to `nodes`:
   ```

7. **Delete cascade order** — `references/author/references/editing-operations-json.md` lines 38

   ```text
   38: 7. **On delete — cascade manually.** Remove the node from `nodes`. Then sweep `edges[]` for any with matching `sourceNodeId`/`targetNodeId`. Then prune `definitions[]` if this was the last user of the type. Then check `bindings_v2.json` — but only remove a connector binding if no remaining node uses the same connector (bindings are shared at the connector level).
   ```

8. **Brownfield edit→recipe routing** — `references/author/references/brownfield.md` lines 30–52

   ```text
   39: | **Add a node between two existing nodes** | Remove the connecting edge, add the new node, wire upstream → new → downstream. | [Edit/Write: Insert a node](editing-operations-json.md#insert-a-node-between-two-existing-nodes) |
   40: | **Add a branch (decision node)** | Remove an edge, add a decision node, wire true/false branches. | [Edit/Write: Insert a decision branch](editing-operations-json.md#insert-a-decision-branch) |
   41: | **Remove a node** | Remove the node, sweep edges/definitions/variables, reconnect upstream to downstream. | [Edit/Write: Remove a node](editing-operations-json.md#remove-a-node-and-reconnect) |
   ```

9. **Subflow scope isolation** — `references/shared/variables-and-expressions.md` lines 563–568

   ```text
   563: ### Subflow Scope
   …
   565: Subflows have their own variable scope. Parent variables are **not** automatically visible inside a subflow. Pass values explicitly via subflow `inputs` and receive results via subflow `outputs`.
   ```

**Why it's mechanical:** Each recipe is a fixed ordered sequence over the graph with no decision points once the target nodes and the new node's type are named; the edge sweep and orphan-definition prune are pure set operations on the parsed file.

**Turn savings:** Each composite is 3–5 serialized `Edit` calls today (the recipes state the counts), spread over 1–2 turns, and the delete cascade is the documented source of orphaned definitions and dangling edges when a sweep is missed. One script call per composite.

---

### 5. Topology and port legality checker — VALIDATE/CHECK

**Source:** `references/author/references/planning-arch.md` §Standard Port Reference, §Wiring Rules

**What it does:** Reads a `.flow` file (or the plan's node + edge tables) and reports illegal wiring: a `sourcePort`/`targetPort` that is not in the node type's port list, a trigger used as an edge target, an End/Terminate used as an edge source, a non-trigger node with no incoming edge, a non-terminal node with no outgoing edge, a decision node without exactly one `true` and one `false` edge, a switch missing a case edge, a cycle not routed through a loop's `loopBack`, a fully disconnected node, and an `error` edge whose source lacks `inputs.errorHandlingEnabled: true`. Line 216: "Use this when defining edges. Every edge requires a `sourcePort` and `targetPort`." Line 270: "**No dangling nodes** — every node must be connected by at least one edge. A node with no incoming and no outgoing edges is invalid. Verify every node in the node table appears in the edge table as either a source or target."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **Port table keyed by node type** — `references/author/references/planning-arch.md` lines 214–251

   ```text
   216: Use this when defining edges. Every edge requires a `sourcePort` and `targetPort`.
   …
   218: | Node Type | Input Port(s) | Output Port(s) |
   …
   220: | `core.trigger.manual` | — | `output` |
   …
   224: | `core.action.script` | `input` | `success`, `error` |
   225: | `core.action.http.v2` | `input` | `default`, `error`, `branch-{id}` (dynamic per `inputs.branches` entry) |
   …
   230: | `core.logic.decision` | `input` | `true`, `false` |
   …
   232: | `core.logic.loop` | `input`, `loopBack` | `success`, `output`, `error` |
   …
   249: | `uipath.human-in-the-loop.quick-form` | `input` | `completed` |
   ```

2. **`error` is implicit and off by default** — `references/author/references/planning-arch.md` lines 252

   ```text
   252: > **`error` is an implicit source port** on every action node (any node with `supportsErrorHandling: true`), and it is **off by default**. Wire it only when the requirements state what should happen if that node fails — a failed HTTP call, script exception, transform error, agent fault. With no error edge the node faults the flow, which is the correct default: a faulted run is visible, a swallowed failure is not. This is a **different mechanism** from content-based `inputs.branches` on HTTP. See [Implicit error port on action nodes](../../shared/file-format.md#implicit-error-port-on-action-nodes) for the default-off rule, wiring, when it fires, and the decision matrix vs branches/decision/switch.
   ```

3. **Wiring rules** — `references/author/references/planning-arch.md` lines 256–271

   ```text
   260: 1. Edges connect a **source port** (output) on one node to a **target port** (input) on another
   261: 2. Trigger nodes have no input port — they are always edge sources, never targets
   262: 3. End/Terminate nodes have no output port — they are always edge targets, never sources
   263: 4. Every non-trigger node must have at least one incoming edge
   264: 5. Every non-terminal node must have at least one outgoing edge
   265: 6. Decision nodes produce exactly two outgoing edges: one from `true`, one from `false`
   266: 7. Switch nodes produce one outgoing edge per case + optionally one from `default`
   267: 8. Loop nodes: the `loopBack` port receives the edge returning from the last node inside the loop body; `success` fires after all iterations
   268: 9. Merge nodes accept multiple incoming edges (one per parallel path being synchronized)
   269: 10. Do not create cycles except through Loop's `loopBack` mechanism
   270: 11. **No dangling nodes** — every node must be connected by at least one edge. A node with no incoming and no outgoing edges is invalid. Verify every node in the node table appears in the edge table as either a source or target.
   ```

4. **Ports by node type, second copy** — `references/shared/file-format.md` lines 282–305

   ```text
   282: ## Standard ports by node type
   …
   284: | Node type | Source ports (outgoing) | Target ports (incoming) |
   …
   286: | `core.trigger.manual` | `output` | — |
   287: | `core.action.script` | `success`, `error` | `input` |
   288: | `core.action.http.v2` | `default`, `error`, `branch-{id}` (dynamic) | `input` |
   …
   290: | `core.logic.decision` | `true`, `false` | `input` |
   291: | `core.logic.switch` | `case-{id}` (dynamic), `default` | `input` |
   292: | `core.logic.loop` | `success`, `output` | `input`, `loopBack` |
   ```

5. **An `error` edge requires the flag on the source node** — `references/shared/file-format.md` lines 350–373

   ```text
   361: `uip maestro flow edge add --source-port error` and `uip maestro flow format` set `inputs.errorHandlingEnabled: true` on the source node automatically — only for nodes that have an error edge. When editing `.flow` JSON directly, set the flag yourself **on those nodes only**:
   ```

6. **Generic action-node port naming** — `references/shared/action-nodes.md` lines 73–82

   ```text
   75: | Direction | Common name(s) | Notes |
   …
   77: | Input (target) | `input` | Every action node accepts a single input edge on `input`. |
   78: | Output (success, source) | `output`, `default`, or `success` | Name varies by plugin — `registry get` is authoritative. |
   79: | Output (error, source) | `error` | Implicit on every action node via `outputs.error`. |
   ```

7. **Edge-table legality rules** — `references/author/references/planning-arch.md` lines 472–476

   ```text
   474: - Source/target ports must match the [Standard Port Reference](#standard-port-reference)
   475: - Every node (except the trigger) must appear as a target at least once
   476: - Every node (except End/Terminate) must appear as a source at least once
   ```

8. **Dynamic ports restated** — `references/author/references/editing-operations.md` lines 83–88

   ```text
   87: - Dynamic ports: decision (`true`/`false`), switch (`case-{id}`/`default`), HTTP (`branch-{id}`/`default`), loop (`output`/`success`/`loopBack`)
   ```

9. **Conflicting HITL port name — planning table** — `references/author/references/planning-arch.md` lines 249

   ```text
   249: | `uipath.human-in-the-loop.quick-form` | `input` | `completed` |
   ```

10. **Conflicting HITL port name — plugin impl** — `references/author/references/plugins/hitl/impl.md` lines 79, 204

   ```text
   79: **Ports:** `input` (target) → `outcome-completed` (source, label: Completed)
   …
   204: | `outcome-completed` port unwired (Option 1) | Missing edge on output handle | Wire the `outcome-completed` output handle — an unwired `outcome-completed` blocks the flow indefinitely |
   ```

11. **Conflicting HITL port name — failure catalog** — `references/diagnose/references/failure-modes.md` lines 132–148

   ```text
   140: The HITL node's `completed` output handle has no outgoing edge — there is no consumer for the `completed` port event.
   …
   144: Add an edge from the HITL node's `completed` port to the next node in the flow. After running `uip maestro flow hitl add`, always wire the `completed` port before validating.
   ```

**Why it's mechanical:** Ports are a closed 31-row table keyed by node type, and the 12 wiring rules are graph predicates with no free parameters.

**Turn savings:** The agent currently eyeballs the port table per edge while authoring and discovers the rest at `flow validate`, which covers only schema-level edge errors (`targetPort` missing, unknown node ids) — dangling nodes, wrong port names for the type, and unbalanced decision branches surface later as a failed run. One pre-validate script call replaces the manual sweep and the debug round trip.

---

### 6. Expression prefix auditor — DETECT

**Source:** `references/shared/node-output-wiring.md` §Where the Rule Applies, §Anti-Patterns, §Validation Tip

**What it does:** Walks every string in the `.flow` JSON and flags four conditions using the doc's per-node-type field table: a `$vars`/`$metadata`/`$self` reference in a value field without the `=js:` prefix; an invented `nodes.<id>.output.<field>` reference; an `=js:` prefix wrongly applied to a condition field (decision `inputs.expression`, switch `inputs.cases[].expression`, HTTP `inputs.branches[].conditionExpression`) or a script body; and `{ }` template interpolation inside connector or HTTP activity inputs. Line 11: "**Any string that references `$vars.*`, `$metadata.*`, or `$self.*` MUST start with `=js:`. Otherwise it is a literal string at runtime.**"

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **The rule** — `references/shared/node-output-wiring.md` lines 9–11

   ```text
   11: **Any string that references `$vars.*`, `$metadata.*`, or `$self.*` MUST start with `=js:`. Otherwise it is a literal string at runtime.**
   ```

2. **Bad forms and what each ships to runtime** — `references/shared/node-output-wiring.md` lines 15–27

   ```text
   21: | What the agent wrote | What ships to runtime | Result |
   …
   23: | `"nodes.createEntityRecord1.output.Id"` | `"nodes.createEntityRecord1.output.Id"` | Literal string — invented `nodes.` prefix has no meaning. |
   24: | `"$vars.createEntityRecord1.output.Id"` | `"vars.createEntityRecord1.output.Id"` | Literal string — `$vars` rewritten to `vars` but no `=js:` so never evaluated. |
   25: | `"=js:$vars.createEntityRecord1.output.Id"` | `"=js:vars.createEntityRecord1.output.Id"` | Evaluates correctly. |
   …
   27: **There is no "nodes.X.output.Y" syntax.** Variable references always use `$vars.*`.
   ```

3. **Canonical pattern and accepted forms** — `references/shared/node-output-wiring.md` lines 31–52

   ```text
   34: "=js:$vars.<sourceNodeId>.output.<field>"
   …
   45: | The whole output object | `=js:$vars.fetchUser1.output` |
   46: | One field from a single-record output | `=js:$vars.createEntityRecord1.output.Id` |
   47: | A field from the first record of a query result (array) | `=js:$vars.queryEntityRecords1.output[0].Id` |
   ```

4. **Per-node-type field matrix** — `references/shared/node-output-wiring.md` lines 55–76

   ```text
   57: `=js:` is **required** in every field below when the value references `$vars`, `$metadata`, or `$self`:
   …
   61: | **Connector activity nodes** (`uipath.connector.<connector-key>.<activity>`) | `inputs.detail.bodyParameters.*` (all values) | **YES** |
   …
   64: | **Managed HTTP** (`core.action.http.v2`) | `inputs.detail.bodyParameters.url` / `headers` / `query` / `body` — both manual and connector mode store dynamic fields here in the `.flow` JSON, regardless of how the CLI's `--detail` flag accepts them at the top level | **YES** |
   …
   66: | **HTTP branches** | `inputs.branches[].conditionExpression` | **NO** — already JS, do not prefix |
   67: | **Decision** (`core.logic.decision`) | `inputs.expression` | **NO** — already JS, do not prefix |
   68: | **Switch** (`core.logic.switch`) | `inputs.cases[].expression` | **NO** — already JS, do not prefix |
   69: | **End nodes** (`core.control.end`) | `outputs.<varId>.source` | **YES** |
   70: | **Variable updates** | `variables.variableUpdates.<nodeId>[].expression` | **YES** (the CLI auto-prefixes if missing, but write it explicitly) |
   71: | **Loop nodes** (`core.logic.loop`) | `inputs.collection` | **YES** |
   72: | **Subflow nodes** (`core.subflow`) | `inputs.<inputId>.source` | **YES** |
   73: | **Script nodes** (`core.action.script`) | `inputs.script` body — `$vars.*` is read inside JS, no `=js:` wrapping | **NO** — the body is already JS |
   …
   76: **Rule of thumb:** If the field is *value-typed* (anything other than a hardcoded condition), `=js:` is required for `$vars`/`$metadata`/`$self` references. The two condition fields (Decision, Switch) and the script body are the only exceptions — they are always parsed as JS regardless.
   ```

5. **Static vs variable vs mixed in connector inputs** — `references/shared/node-output-wiring.md` lines 80–110

   ```text
   105: - **Static values** (`"HDFC Bank"`, `"3"`) — no prefix, written as plain JSON values.
   106: - **Variable references** (`$vars.X.output.Y`) — **always** wrap with `=js:`.
   107: - **Mixed strings** (template literals) — wrap the whole expression in `=js:` and use JS template literal syntax with `${ }`.
   ```

6. **Anti-patterns to detect** — `references/shared/node-output-wiring.md` lines 113–120

   ```text
   115: 1. **Never invent a `nodes.X.output.Y` syntax.** It does not exist. All variable references use `$vars`.
   116: 2. **Never write `$vars.X.output.Y` without `=js:`** in an expression value field. The `$vars→vars` rewrite happens regardless of prefix, leaving you with a literal string `"vars.X.output.Y"` at runtime — looks like an expression, isn't one. For plugin path fields such as Transform `inputs.collection`, use the plugin-specific path format instead.
   117: 3. **Never wrap conditions** (Decision, Switch, HTTP branch) in `=js:`. Those are parsed as JS automatically.
   118: 4. **Never use `{ }` template interpolation in connector or HTTP activity inputs.** The flow-layer template runner skips these fields. The `$` is stripped and `{vars.X}` ships literally to the IS runtime. Use `=js:` and JS template literals (`` `…${$vars.X}…` ``) instead.
   119: 5. **Never quote `=js:` itself in an expression.** `"=js:$vars.X"` is correct. `"\"=js:$vars.X\""` is a string containing the prefix.
   ```

7. **Transform `inputs.collection` exception** — `references/shared/node-output-wiring.md` lines 109

   ```text
   109: Plugin-specific path fields are not value fields. **Always** follow the plugin reference when it says a field stores a path string. Notable exception: Transform `inputs.collection` must be a path such as `"$vars.orders.output.items"`, without `=js:`.
   ```

8. **The manual remedy the script replaces** — `references/shared/node-output-wiring.md` lines 131–138

   ```text
   133: When debugging a flow whose output is the literal string `vars.X.output.Y` (or `nodes.X.output.Y`, or any other unevaluated expression) instead of the expected value:
   …
   135: 1. Open the `.flow` file
   136: 2. Search for the literal token in the failed field — `grep '"vars\.' <project>.flow` or `grep '"\$vars\.' <project>.flow`
   137: 3. For each match in `bodyParameters`, `queryParameters`, `pathParameters`, end-node `source`, or any value field, prepend `=js:`
   138: 4. Re-run `uip maestro flow validate` and re-debug
   ```

9. **Value-vs-condition split, second copy** — `references/author/references/editing-operations.md` lines 107–112

   ```text
   109: - Use `=js:` on **value expressions**: end node output `source`, variable updates, HTTP input fields, node `inputs` values
   110: - Do NOT use `=js:` on **condition expressions**: decision `expression`, switch case `expression`, HTTP branch `conditionExpression` — these are always evaluated as JS automatically
   ```

10. **MST-9107 cause and field list** — `references/diagnose/references/failure-modes.md` lines 25–56

   ```text
   37: The `=js:` prefix was omitted on a `$vars` / `$metadata` / `$self` reference inside a value field. The serializer rewrites `$vars` → `vars` whether or not the prefix is present, so a missing `=js:` yields a string that **looks like** an unevaluated expression but is actually a literal.
   …
   43: Add `=js:` to every `$vars`/`$metadata`/`$self` reference in:
   …
   52: Do **not** add `=js:` to condition expressions (decision `expression`, switch case `expression`, HTTP branch `conditionExpression`) — those are evaluated as JavaScript automatically.
   ```

11. **What the CLI validator already catches** — `references/diagnose/references/failure-modes.md` lines 329–336

   ```text
   329: **Caught** (validate exits non-zero, with a precise field path and remediation hint):
   …
   331: - Missing `=js:` prefix on `$vars`/`$metadata`/`$self` (MST-9107) — emitted by cli-side `expression-prefix-validator`
   332: - Invented `nodes.<id>.output.<...>` syntax (MST-9107 variant) — same validator, suggests `=js:$vars.<id>.output.<...>` as the fix
   ```

**Why it's mechanical:** Required vs forbidden is a table keyed by (node type, field path); the test is a prefix check on the string value.

**Turn savings:** The doc's own remedy is a manual loop — `grep '"vars\.'`, inspect each hit against the field table, prepend `=js:`, re-validate (§Validation Tip, lines 133–138) — which is 2–3 turns. The CLI's `expression-prefix-validator` catches the missing-prefix half only; the wrongly-prefixed conditions and the `{ }`-interpolation cases are not caught anywhere, so they cost a debug round trip instead.

---

### 7. Jint construct linter — DETECT

**Source:** `references/shared/variables-and-expressions.md` §Jint Engine Constraints; `references/author/CAPABILITY.md` §Critical rules, §Anti-patterns

**What it does:** Scans `core.action.script` bodies and every `=js:` expression for constructs the production runtime rejects and reports each with node id and offset: `fetch`, `XMLHttpRequest`, `setTimeout`, `setInterval`, `document`, `window`, `console`, `require`, `import`, `eval`, the `Function` constructor, `async`/`await`, `Promise`, and bare `Date` construction. It also flags a script node whose body has no object `return`. Line 530 opens the enumerated "### Not Supported" list; `author/CAPABILITY.md` line 69: "**Script nodes must `return` an object** — `return { key: value }`, not a bare scalar."; line 137: "**Never use `console.log` in script nodes** — `console` is not available in the Jint runtime."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **Supported constructs** — `references/shared/variables-and-expressions.md` lines 514–528

   ```text
   512: The production runtime uses **Jint** (a .NET JavaScript interpreter, ES2020 subset). Key constraints:
   …
   514: ### Supported
   …
   516: - Arithmetic: `+`, `-`, `*`, `/`, `%`
   …
   520: - String methods: `.toUpperCase()`, `.toLowerCase()`, `.trim()`, `.split()`, `.includes()`, `.startsWith()`, `.slice()`, `.substring()`
   521: - Array methods: `.filter()`, `.map()`, `.reduce()`, `.find()`, `.some()`, `.every()`, `.concat()`, `.length`
   ```

2. **Banned constructs** — `references/shared/variables-and-expressions.md` lines 530–537

   ```text
   530: ### Not Supported
   …
   532: - `fetch`, `XMLHttpRequest`, `setTimeout`, `setInterval` — no network or timers
   533: - `document`, `window`, `console` — no DOM or browser globals
   534: - `require`, `import` — no module system
   535: - `eval`, `Function` constructor — no dynamic code generation
   536: - `async`/`await`, `Promise` — no async operations
   537: - `Date` constructor may have limited support — prefer ISO 8601 strings
   ```

3. **Script body must return an object** — `references/author/CAPABILITY.md` lines 69

   ```text
   69: 7. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
   ```

4. **`console` unavailable** — `references/author/CAPABILITY.md` lines 137

   ```text
   137: - **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
   ```

5. **The eight script-node rules** — `references/author/references/plugins/script/impl.md` lines 31–42

   ```text
   31: ## Script rules
   …
   33: 1. **Top-level body — no `function main()` wrapper.** Node runs the `script` text directly (as a function body); a wrapper is never called → `output` null. Read workflow variables via `$vars.<variableId>` and upstream node outputs via `$vars.<nodeId>.output`; end with top-level `return {…}`. Not a coded Function: no `main`, no injected args.
   …
   36: 2. **Must `return` an object** — `return { key: value }`, not a bare scalar. The return value becomes `$vars.<nodeId>.output`.
   …
   39: 5. **No `console.log`** — `console` is not available. Use `return { debug: value }` to inspect values.
   40: 6. **No external calls** — use the HTTP node or a connector node for API calls.
   41: 7. **30-second timeout** — long-running computations will be killed.
   42: 8. **Never name a variable `aggregate`** — reserved host global. On any `Identifier 'X' has already been declared`, rename `X`.
   ```

6. **Other expression contexts to lint** — `references/shared/variables-and-expressions.md` lines 434–509

   ```text
   434: ## Expression Contexts
   …
   436: Expressions behave differently depending on where they appear.
   …
   454: ### Decision Node (`inputs.expression`)
   …
   464: ### Switch Node (`inputs.cases[].expression`)
   …
   480: ### HTTP Branch Condition (`inputs.branches[].conditionExpression`)
   …
   488: ### Variable Update Expressions
   …
   497: ### Loop Collection Expression
   ```

**Why it's mechanical:** The banned set is an explicit list in the skill, and the `return`-an-object requirement is a syntactic property of the body.

**Turn savings:** None of this is caught by `flow validate` — a `console.log` or an `await` in a script node surfaces as a faulted cloud run, so today it costs a `flow debug` plus the full diagnose ladder (4+ turns) to find. One lint call before validate.

---

### 8. Resource-node `bindings[]` builder and auditor — BUILD-MODEL/MATRIX

**Source:** `references/shared/file-format.md` §Bindings — Orchestrator resource bindings (top-level `bindings[]`); `references/diagnose/references/failure-modes.md` §Missing `bindings[]` on resource node

**What it does:** For every `uipath.core.*` resource node (rpa-workflow, agent, flow, agentic-process, api-workflow, human-task) in the file, emits or verifies the pair of top-level `bindings[]` entries — one with `name: "name"`, one with `name: "folderPath"` — copying `resourceKey` and `resourceSubType` from the node's definition `model.bindings`, sharing one pair across node instances that resolve to the same `(resourceKey, name)`, and reporting any resource node whose definition carries `<bindings.{name}>` placeholders with no matching entry. Line 546: "- Add **two entries** per resource node (one for `name`, one for `folderPath`)." Line 553: "Without matching entries in top-level `bindings[]`, `uip maestro flow debug` fails with \"Folder does not exist or the user does not have access to the folder\" even though `uip maestro flow validate` passes."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **Which node families need bindings** — `references/shared/file-format.md` lines 513–518

   ```text
   515: The top-level `bindings` array (a sibling of `nodes`, `edges`, `definitions`, `variables`, `layout`) holds resource-reference indirections for **Orchestrator resource nodes** — RPA workflows, agents, flows, agentic processes, API workflows, and HITL apps.
   ```

2. **Entry shape (first of the pair; second is identical but `folderPath`)** — `references/shared/file-format.md` lines 519–542

   ```text
   520: "bindings": [
   521:   {
   522:     "id": "<UNIQUE_ID>",
   523:     "name": "name",
   524:     "type": "string",
   525:     "resource": "process",
   526:     "resourceKey": "<FolderPath>.<ResourceName>",
   527:     "default": "<ResourceName>",
   528:     "propertyAttribute": "name",
   529:     "resourceSubType": "Process"
   530:   },
   ```

3. **The six rules** — `references/shared/file-format.md` lines 544–551

   ```text
   546: - Add **two entries** per resource node (one for `name`, one for `folderPath`).
   547: - **Share** entries across node instances that reference the same resource — do not duplicate. Matching is by `(resourceKey, name)`, so any node whose definition has the same `resourceKey` resolves to the same binding pair.
   548: - Entry IDs are unique strings within the file. Descriptive IDs (e.g. `bDepositRpaName`) are preferred over short random IDs.
   549: - The node instance has no `model` block — it carries only `inputs`, `outputs`, and `display`.
   550: - `resourceKey` must exactly match the definition's `model.bindings.resourceKey` (verbatim from the registry). The runtime uses this key to scope placeholder resolution so that binding names like `name` / `folderPath` (shared across resource kinds) don't cross-alias.
   551: - `resourceSubType` mirrors the definition's `model.bindings.resourceSubType`: `Process` (rpa), `Agent` (agent), `Flow` (flow), `ProcessOrchestration` (agentic-process), `Api` (api-workflow), or the app type for HITL.
   ```

4. **Why it is required and the exact debug-time failure** — `references/shared/file-format.md` lines 553

   ```text
   553: **Why this is required.** The definition's `model.context[].value` fields are placeholders of the form `<bindings.{name}>` — deliberately invalid as runtime expressions, so they can't be confused with one. Before the BPMN is emitted, the runtime rewrites each placeholder to `=bindings.<id>` by finding a workflow-level binding with `(resourceKey, name)` matching the node's manifest `model.bindings.resourceKey` + the placeholder name. Without matching entries in top-level `bindings[]`, `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder" even though `uip maestro flow validate` passes.
   ```

5. **Definitions stay verbatim** — `references/shared/file-format.md` lines 555

   ```text
   555: **Definitions stay verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — the definition is the authoring template. See "Every node type needs a `definitions` entry" in [author/CAPABILITY.md](../author/CAPABILITY.md).
   ```

6. **Symptom, cause, and the explicit statement that validate misses it** — `references/diagnose/references/failure-modes.md` lines 291–315

   ```text
   295: `uip maestro flow validate` passes locally. At `uip maestro flow debug` (or in deployed runs), the resource node faults with:
   …
   298: Folder does not exist or the user does not have access to the folder.
   …
   305: For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the registry definition carries `model.context[]` with `<bindings.{name}>` placeholders. The runtime rewrites these to `=bindings.{id}` at BPMN emit by matching `(resourceKey, name)` against the **top-level `bindings[]` array** in the `.flow` file. Without those entries, the placeholder never resolves and the runtime treats the binding as missing — surfacing as the folder-not-found error.
   …
   307: `flow validate` checks JSON schema and cross-references; it does not validate that resource-node `model.context[]` entries are matched by top-level `bindings[]` entries.
   …
   311: Add two entries to the top-level `bindings[]` array per resource node — `name` and `folderPath` — with `resourceKey` matching the definition's `model.bindings.resourceKey`. See the relevant resource plugin's `impl.md` for the exact shape ([rpa](../../author/references/plugins/rpa/impl.md), [agent](../../author/references/plugins/agent/impl.md), [flow](../../author/references/plugins/flow/impl.md), [agentic-process](../../author/references/plugins/agentic-process/impl.md), [api-workflow](../../author/references/plugins/api-workflow/impl.md), [hitl](../../author/references/plugins/hitl/impl.md)).
   ```

7. **Concrete pair for one resource kind (RPA)** — `references/author/references/plugins/rpa/impl.md` lines 77–106

   ```text
   77: ### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)
   …
   79: Add one entry per `(resourceKey, propertyAttribute)` pair. Share entries across node instances that reference the same RPA process — do NOT create duplicates.
   …
   84:     "id": "bProcessInvoicesName",
   85:     "name": "name",
   …
   88:     "resourceKey": "Finance/Automation.Invoice Processor",
   …
   90:     "propertyAttribute": "name",
   91:     "resourceSubType": "Process"
   ```

8. **Instance must not carry `model.context[]`** — `references/author/CAPABILITY.md` lines 133

   ```text
   133: - **Never author `model.context[]` on resource-node instances** — resource-node instances have no `model` block. For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the definition (from `registry get`) already carries `model.context[]` with `<bindings.{name}>` placeholders. Your job is to add matching entries to the top-level `bindings[]` array — two entries per resource node (`name` + `folderPath`) with `resourceKey` matching the definition's `model.bindings.resourceKey`. At BPMN emit, the runtime rewrites `<bindings.{name}>` → `=bindings.{id}` via `(resourceKey, name)` matching. Without the top-level `bindings[]` entries, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder." See the resource plugin's `impl.md`.
   ```

9. **Connector-side bindings, kept distinct** — `references/author/references/plugins/connector/impl.md` lines 545–702

   ```text
   545: ## Bindings — top-level `.flow` `bindings[]`
   …
   547: When a flow uses connector nodes, the runtime needs to know **which authenticated connection** to use for each connector. Bindings are authored in the flow's **top-level `bindings[]` array** (a sibling of `nodes`, `edges`, `definitions`). At `flow debug` / `flow pack` time the CLI regenerates `content/bindings_v2.json` from these entries.
   …
   549: > **Never edit `bindings_v2.json` directly.** Any manual edits are overwritten on the next debug/pack. All authoring flows through the `.flow` file's top-level `bindings[]`.
   …
   553: The connector node's **definition** (the manifest copied from `uip maestro flow registry get` into `definitions[]`) carries a `model.context[]` template like this. **Leave the definition exactly as the registry returns it** — do NOT rewrite `<bindings.*>` placeholders inside the definition, and do NOT author `model.context[]` on the instance:
   ```

**Why it's mechanical:** Entry count, field names, and every value are derived from the registry definition by a stated rule; the audit is a join between definition placeholders and `bindings[]` on `(resourceKey, name)`.

**Turn savings:** Today the agent reads the plugin `impl.md` for the shape, hand-writes two JSON objects per resource node inside a `bindings[]` Edit, and — because `flow validate` explicitly does not check this — discovers omissions as a folder-not-found fault at debug, then runs the diagnose ladder to trace it back. That is 2 authoring turns plus a 4-turn misdiagnosis risk.

---

### 9. Connector `parameterValues` key encoder — COMPUTE/FORMULA

**Source:** `references/author/references/plugins/connector/impl.md` §Step 6c — Populate custom fields (api-type ObjectActions)

**What it does:** Takes the parent-field names (the `{token}`s in the api-type action's `apiConfiguration.{url,body}`) plus their values and emits the `customFieldsRequestDetails.parameterValues` payload: each key encoded by applying the substitution table longest-first (`:::`→`_sub_`, `[*]`→`_array`, `::`→`_sub_`, `.`→`_sub_`), serialized as `[[key, value], ...]` tuples rather than an object map, with the raw-keyed copy retained for `bodyParameters`/`queryParameters`. Line 400: "**Token encoding rule.** Tokens are encoded via `NamingHelper.getValidIdentifier` (the IS-side identifier sanitizer) before being used as `parameterValues` keys, so they match design-property names at lookup time. Substitutions (applied longest-first):"

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **When the activity has a parent-field-driven schema** — `references/author/references/plugins/connector/impl.md` lines 363–371

   ```text
   363: A connector activity has a **parent-field-driven schema** when its valid input fields are not fixed in static metadata but are computed at design time by running an api-type ObjectAction against the IS Element Service. Examples: Jira's `Create Issue` schema depends on the project + issue type; Snowflake's `executeQuery` response columns depend on the SQL string; Dataservice V3's entity field set depends on `tenantEntityName`. The activity persists the parent-field values in `essentialConfiguration.customFieldsRequestDetails` so the runtime can replay the schema-fetch ObjectAction on each invocation. The CLI passes this through verbatim.
   …
   365: **How DAP determines support — check both metadata locations.** An api-type action may live at either:
   …
   367: - Top-level `objectActions[]` with PascalCase `ActionType: "Api"` (older shape, e.g. Jira `GenerateSchema`)
   368: - `connectorMethodInfo.design.actions[]` with lowercase `actionType: "api"` (newer shape, e.g. Dataservice V3 `FetchObjectMetadataTenant`)
   …
   370: The dispatcher matches `ObjectActionType.Api === 'api'` (case-sensitive lowercase string) — both shapes go through the same `_processCustomFieldsRequestAction` code path with no per-connector branching. Always inspect both locations from `registry get` output before deciding the connector has none.
   ```

2. **Rule source selection** — `references/author/references/plugins/connector/impl.md` lines 372–376

   ```text
   372: The matching action is then selected by one of two rule sources:
   …
   374: - **`source: field`** — the action's `rules[].refFieldName` are satisfied by user-supplied `-f, --field` values (typically SQL-style query connectors where the query string is the parent field).
   375: - **`source: method`** — the action is declared at the operation level and matched against the operation's HTTP method (typically CRUD activities).
   ```

3. **Substitution table** — `references/author/references/plugins/connector/impl.md` lines 400–408

   ```text
   400: **Token encoding rule.** Tokens are encoded via `NamingHelper.getValidIdentifier` (the IS-side identifier sanitizer) before being used as `parameterValues` keys, so they match design-property names at lookup time. Substitutions (applied longest-first):
   …
   402: | Match in token | Encoded as |
   403: |---|---|
   404: | `:::` | `_sub_` |
   405: | `[*]` | `_array` |
   406: | `::` | `_sub_` |
   407: | `.` | `_sub_` |
   408: 
   ```

4. **Worked outputs** — `references/author/references/plugins/connector/impl.md` lines 409

   ```text
   409: Examples: `fields.project.key` → `fields_sub_project_sub_key`; `items[*]` → `items_array`; `tenantEntityName` → `tenantEntityName` (unchanged). When in doubt, inspect a working `.flow` for the encoded form.
   ```

5. **Complementary-copy rule and the failure when dropped** — `references/author/references/plugins/connector/impl.md` lines 411–418

   ```text
   411: > **`customFieldsRequestDetails` is COMPLEMENTARY to `bodyParameters` / `queryParameters`, not a substitute.** Same parent-field values must appear in BOTH places, with different keys:
   …
   413: > | Location | Purpose | Key shape |
   …
   415: > | `bodyParameters` / `queryParameters` / `pathParameters` | Runtime input — what the connector actually sends to its API | **Raw** field names (e.g. `fields.project.key`, `tenantEntityName`) |
   416: > | `essentialConfiguration.customFieldsRequestDetails.parameterValues` | Design-time replay cache — drives the parent-field-driven schema fetch when the activity is re-opened or re-validated | **Encoded** keys (e.g. `fields_sub_project_sub_key`, `tenantEntityName`) |
   …
   418: > Concrete (Jira Create Issue): `bodyParameters.fields.project.key = "ENGCE"` AND `parameterValues = [["fields_sub_project_sub_key", "ENGCE"]]`. Concrete (Dataservice V3): `queryParameters.tenantEntityName = ""my-entity""` AND `parameterValues = [["tenantEntityName", ""my-entity""]]`. Dropping the runtime-input copy on the assumption that the cache covers it leaves the runtime with no field value to bind — manifests as `DAP-DT-_2003 refField with name <X> not found` at activity load.
   ```

6. **On-wire tuple shape** — `SKILL.md` lines 108

   ```text
   108: - **Never write `customFieldsRequestDetails.parameterValues` as a JSON object map** — Studio Web's TS port emits `Map<string,string|null>` via `Array.from(entries())`, so the on-wire shape is `[[key, value], ...]` tuples. Object-form `{key: value}` is rejected by the CLI at validate time. Inner keys are camelCase (`objectActionName`, `parameterValues`), not PascalCase. See [connector/impl.md Step 6c](references/author/references/plugins/connector/impl.md).
   ```

7. **Re-configure is a full rebuild** — `references/author/references/plugins/connector/impl.md` lines 221–229

   ```text
   221: > **Re-configure is full rebuild, not partial merge — every `--detail` field omitted gets dropped.** Each `node configure` call constructs a fresh `inputs.detail` object (`connector-service.ts:792-803`) and a fresh `essentialConfiguration` blob from `--detail` only. Anything not in this call's `--detail` is dropped from the rewritten flow:
   …
   229: > **Rule:** always re-pass the full intended `--detail` shape — connection plumbing + every parameter bucket + filter tree + customFieldsRequestDetails — even when changing one field. The CLI does not read the prior `inputs.detail` to fill gaps.
   ```

8. **Related `[*]` key transform** — `references/author/CAPABILITY.md` lines 145

   ```text
   145: - **Never include `[*]` literally in a connector `bodyParameters` / `queryParameters` / `pathParameters` key** — `[*]` in `requestFields[].name` is an array marker. Strip it and pass a `=js:` expression returning the array (e.g. `"fields.labels[*]"` → `"fields.labels": "=js:(['a', 'b'])"`). Never a literal JSON array — it validates but does not bind. Supported only when `[*]` is the name suffix; `[*]. See [connector/impl.md — Step 6b](references/plugins/connector/impl.md) for the full table including expression-value handling.
   ```

**Why it's mechanical:** A closed-form string transform with a fixed constant table, plus a fixed serialization shape — the doc even gives the worked outputs (`fields.project.key` → `fields_sub_project_sub_key`, `items[*]` → `items_array`).

**Turn savings:** The agent currently encodes each token by hand while composing `--detail`, and the two documented failure shapes — object-form `{key: value}` rejected at validate time, or a dropped raw-keyed copy producing `DAP-DT-_2003 refField with name <X> not found` at activity load — each cost a re-`configure` cycle of 1–2 turns.

---

### 10. Inline-agent input wiring builder/checker — BUILD-MODEL/MATRIX

**Source:** `references/author/references/plugins/inline-agent/impl.md` §Wiring Flow Variables into Agent Prompts

**What it does:** Given the list of upstream values to pass into an inline agent (`$vars.<node>.output.<field>`), emits all three aligned artifacts and verifies they stay aligned: the flow node's `inputs.agentInputVariables[]` entry (`id`, `type`, `binding: "=$vars…"` — never `value`), the `agent.json` `inputSchema.properties` key, and the `{{input.<key>}}` token in `messages[].content`, with keys produced by the stated flatten rule. It also reports a binding whose source is not a declared variable and a prompt token naming a key absent from `inputSchema`. Line 50: "**The CLI does not derive the input wiring** — `uip agent refresh` does **not** scan prompts, derive `inputSchema`, or populate `agentInputVariables`; you author all three, and packaging ships them as-authored. … Flatten rule: `$vars.<trigger>.output.<var>` → `<trigger>__output__<var>`."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **Three artifacts, CLI derives none, flatten rule** — `references/author/references/plugins/inline-agent/impl.md` lines 50

   ```text
   50: Passing flow data into an inline agent requires **three hand-authored, aligned** pieces. **The CLI does not derive the input wiring** — `uip agent refresh` does **not** scan prompts, derive `inputSchema`, or populate `agentInputVariables`; you author all three, and packaging ships them as-authored. (Refresh *does* regenerate `messages[].contentTokens` from `content` — that's the one derived part; see the invariant below.) The converter builds the runtime `JobArguments` from the **flow node's `inputs.agentInputVariables[]`** (not from `$vars` tokens in `agent.json`). Flatten rule: `$vars.<trigger>.output.<var>` → `<trigger>__output__<var>`.
   ```

2. **Which mismatch validate catches vs which faults at debug** — `references/author/references/plugins/inline-agent/impl.md` lines 52

   ```text
   52: The three pieces — **Delivery** (node `agentInputVariables[]`), **Contract** (`agent.json` `inputSchema`), and **Resolution** (`{{input.<key>}}` in `messages[].content`) — and their examples are in the table below. `flow validate` catches a Resolution↔Contract mismatch (a `{{input.K}}` that's malformed or names a key not in `inputSchema`), but a missing/wrong **Delivery** binding passes validate and only shows up as empty input at `flow debug`. Agent-side `inputSchema`/`contentTokens` mechanics: the `uipath-agents` skill's [inline-in-flow § Wiring Flow Inputs Into an Inline Agent](../../../../../../uipath-agents/references/lowcode/capabilities/inline-in-flow/inline-in-flow.md#wiring-flow-inputs-into-an-inline-agent-required).
   ```

3. **Prerequisite — the bound value must be a declared variable** — `references/author/references/plugins/inline-agent/impl.md` lines 54–60

   ```text
   54: > **Prerequisite — the bound value must actually exist as a variable.** A node binding `=$vars.X` resolves at runtime only if `$vars.X` is a declared variable. `flow validate` does **not** check that the path exists — a binding referencing an undeclared trigger field passes validate, then **faults at debug** with `JobArguments` empty. When the upstream node is a **trigger** (e.g. `core.trigger.manual`, id `start`), each field you bind must be declared in `variables.globals[]` as a trigger-associated input — `direction: "in"`, `triggerNodeId: "<triggerId>"` — and is then read as `$vars.<triggerId>.output.<id>`:
   …
   57: > { "id": "invoiceNumber", "direction": "in", "type": "string", "triggerNodeId": "start" }
   ```

4. **The artifact table with exact shapes** — `references/author/references/plugins/inline-agent/impl.md` lines 62–67

   ```text
   62: | Where | What | Example |
   …
   64: | Flow node `inputs.agentInputVariables[]` | One entry per input — the delivery binding the converter turns into `JobArguments`. | `{ "id": "start__output__invoiceNumber", "type": "string", "binding": "=$vars.start.output.invoiceNumber", "description": "Bound from $vars.start.output.invoiceNumber" }` |
   65: | `agent.json` `inputSchema.properties` | One `<trigger>__output__<var>` key per input — **mandatory**, binds `JobArguments` → the agent's `input`. | `"start__output__invoiceNumber": { "type": "string", "description": "Bound from $vars.start.output.invoiceNumber" }` |
   66: | `agent.json` `messages[].content` | `{{input.<trigger>__output__<var>}}` (the `input.` form — never `$vars`). | `"Invoice: {{input.start__output__invoiceNumber}}"` |
   67: | `agent.json` `messages[].contentTokens[]` | One `{ "type": "variable", "rawString": "input.<trigger>__output__<var>" }` per `{{ ... }}` token in `content` (brace-free `rawString`). | `{ "type": "variable", "rawString": "input.start__output__invoiceNumber" }` |
   ```

5. **`content` ↔ `contentTokens` mirror invariant** — `references/author/references/plugins/inline-agent/impl.md` lines 71–83

   ```text
   73: `content` is the source of truth. **`uip agent refresh` regenerates `messages[].contentTokens` from `content`** (correct `simpleText`/`variable` types, brace-free `rawString`). So: author the prompt in `content`, run `refresh`, and **don't hand-author or hand-fix `contentTokens`**. `uip agent validate` is read-only — if it flags a token mismatch (`Expected type "simpleText"…`, `Expected "input.X" but got "{{input.X}}"`, or `contentTokens has N entries but content requires M`), **re-run `refresh`** to regenerate; don't edit `rawString`.
   …
   75: What `refresh` produces, for `content` = `"Invoice Number: {{input.start__output__invoiceNumber}}\n"`:
   ```

6. **Worked example to test against** — `references/author/references/plugins/inline-agent/impl.md` lines 85–116

   ```text
   97: Matching `agent.json` — `inputSchema` keys mirror the bindings; the prompt uses the `input.` form, and `contentTokens` decompose `content` left-to-right (literals → `simpleText` verbatim incl. `\n`; each `{{ … }}` → brace-free `variable`):
   ```

7. **Anti-patterns** — `references/author/references/plugins/inline-agent/impl.md` lines 124–131

   ```text
   126: - **In `agent.json` prompts, use the `{{input.<trigger>__output__<var>}}` form** (the flattened key, `input.` prefix). Never use raw `{{ $vars.X }}` (the runtime can't resolve it — agent gets the literal token) or `{{plainName}}` (no prefix).
   127: - **The `variable` `rawString` is exactly what sits between the braces** — `input.<trigger>__output__<var>`, brace-free, no added spaces.
   128: - **Keep the flow-node `inputs.systemPrompt` / `inputs.userPrompt` as short generic placeholders** — the canonical prompt lives in `agent.json messages[]`, and delivery comes from `agentInputVariables[]`, not from tokens in the node prompts.
   129: - **Declared `type` must match the bound node's real output shape, in BOTH `agentInputVariables[].type` and `inputSchema`.** The runtime strict-validates `JobArguments` before the model runs: a list bound to an `object`-typed key faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` (incident `170002`, `"Input should be a valid dictionary … input_type=list"`), and both `flow validate` and `agent validate` still report `Valid`. **Data Service query-entity-records returns an array. A script-built value has the shape the script returns — `.map()` returns array, never object.** The registry won't settle it — connector nodes declare `output.type: "object"` with no schema — so bind the leaf (`=$vars.crmLookup1.output[0].accountTier`) or read the shape from one `flow debug` run.
   …
   131: - **Each `agentInputVariables[]` entry uses `binding` (not `value`).** The converter builds `JobArguments` from `binding`; a `value: "=js:$vars…"` entry (Studio Web's internal canvas form) is **ignored** — the agent gets empty input and faults at debug (`AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR`, "Template placeholders detected instead of actual values"). Write `{ "id": "<key>", "binding": "=$vars.<trigger>.output.<var>" }`. `binding` is what both the CLI converter and Studio Web's loader read.
   ```

8. **Token form in the shared wiring matrix** — `references/shared/node-output-wiring.md` lines 74

   ```text
   74: | **Inline-agent prompt** (`uipath.agent.autonomous` `agent.json` `messages[].content`) | Tokens reference upstream flow nodes directly: `{{ $vars.<flowNodeId>.output[.<field>] }}` (spaced braces). Mirror in `contentTokens[]` as `{ "type": "variable", "rawString": " $vars.<flowNodeId>.output[.<field>] " }` — `rawString` must include leading and trailing space. Never `{{input.<id>}}` and never bare `{{name}}`. | **NO** — `{{ ... }}` tokens, not `=js:`. See [author/references/plugins/inline-agent/impl.md § Wiring Flow Variables into Agent Prompts](../author/references/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts). |
   ```

**Why it's mechanical:** One binding list determines all three artifacts through a stated string rule; the alignment check is a three-way key-set comparison.

**Turn savings:** Today it is hand-authored across two files (a `.flow` Edit plus an `agent.json` Edit) per input, and the doc states a wrong or missing delivery binding passes both `flow validate` and `agent validate` — it shows up as empty agent input at debug, i.e. a full debug-plus-diagnose cycle. One script call emits and cross-checks the whole set.

---

### 11. Diagnostic ladder runner — TRANSFORM-PIPELINE

**Source:** `references/diagnose/references/troubleshooting-guide.md` §Diagnostic priority, Steps 1–5

**What it does:** Given a job key or instance id (plus folder key), runs the fixed ladder and returns one consolidated report: `job status` to resolve the instance id, `instance incidents` then `incident get` for error category, message, and faulting element, `instance variables` for data state at failure, then the correlation step — locate the faulting element id in the local `.flow`, print that node's `inputs`, its upstream edges, and the variable values flowing into it — escalating to `element-executions` / `instance asset` / `job traces` only when the earlier steps returned nothing. Line 9: "Investigate in this order — each step adds context, stop when you have enough to diagnose the root cause:" Line 62: "Use the incident's faulting element ID and the variable state to locate the failure point in the `.flow` file. Map the element ID to the corresponding node, check its `inputs`, upstream edges, and the variable values flowing into it."

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **The ladder order and stop condition** — `references/diagnose/references/troubleshooting-guide.md` lines 7–14

   ```text
   9: Investigate in this order — each step adds context, stop when you have enough to diagnose the root cause:
   …
   11: 1. Incidents (error message + faulting element)
   12: 2. Runtime variables (data state at failure)
   13: 3. Flow definition correlation (map element to `.flow` node)
   14: 4. Traces (last resort — verbose full timeline)
   ```

2. **Step 1 — resolve the instance id** — `references/diagnose/references/troubleshooting-guide.md` lines 16–24

   ```text
   18: The debug output (`Data.instanceId`) or `job status` response contains the instance ID. If you only have a job key:
   …
   21: uip maestro flow job status <JOB_KEY> --output json
   …
   24: Parse the instance ID and folder key from the response.
   ```

3. **Step 2 — incidents first** — `references/diagnose/references/troubleshooting-guide.md` lines 26–44

   ```text
   28: Failed flows always have an incident. Start here — incidents give you the error category, message, and the faulting element.
   …
   31: uip maestro flow instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
   …
   37: uip maestro flow incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
   …
   43: uip maestro flow incident summary --output json
   ```

4. **Step 3 — runtime variable state** — `references/diagnose/references/troubleshooting-guide.md` lines 46–58

   ```text
   48: Get the variable values at the time of failure to understand what data each node was working with:
   …
   51: uip maestro flow instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
   …
   57: uip maestro flow instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
   ```

5. **Step 4 — correlation, and the deployed-asset fallback** — `references/diagnose/references/troubleshooting-guide.md` lines 60–75

   ```text
   62: Use the incident's faulting element ID and the variable state to locate the failure point in the `.flow` file. Map the element ID to the corresponding node, check its `inputs`, upstream edges, and the variable values flowing into it.
   …
   64: If the local `.flow` file may differ from what was deployed, fetch the deployed BPMN definition:
   …
   67: uip maestro flow instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
   …
   73: uip maestro flow instance element-executions <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json  # per-element execution details
   74: uip maestro flow instance cursors <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json             # current execution cursor positions
   ```

6. **Step 5 — traces last** — `references/diagnose/references/troubleshooting-guide.md` lines 77–85

   ```text
   79: Traces are verbose but contain the full execution timeline. Use them only when incidents and variables are insufficient:
   …
   82: uip maestro flow job traces <JOB_KEY> --output json
   …
   85: > **Always use CLI commands for troubleshooting — never call the underlying APIs directly.**
   ```

7. **Subcommand surface** — `references/diagnose/references/troubleshooting-guide.md` lines 87–115

   ```text
   91: Inspect and manage Flow process instances. **Requires `uip login`.** All subcommands require `--folder-key <FOLDER_KEY>` (`-f` shorthand).
   …
   95: uip maestro flow instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json                           # get instance details
   96: uip maestro flow instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get incidents for a failed instance
   97: uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get runtime variable values
   …
   100: uip maestro flow instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json                         # get the deployed BPMN definition
   ```

8. **Diagnose-scoped critical rules** — `references/diagnose/CAPABILITY.md` lines 20–25

   ```text
   22: 1. **Investigate in priority order — incidents → variables → flow correlation → traces.** Each step adds context; stop when you have enough to identify the root cause. Skipping ahead to traces is the most common mistake — they are verbose and last-resort. See [troubleshooting-guide.md](references/troubleshooting-guide.md).
   23: 2. **Always include `--folder-key <FOLDER_KEY>` (`-f` shorthand) on `instance` and `incident get` commands.** Without it the command rejects the request before reaching the API. Get the folder key from `uip or folders list --output json` or from the job/process context. See [shared/cli-conventions.md](../shared/cli-conventions.md#6---folder-key-requirement).
   24: 3. **Never call the underlying APIs directly — always use `uip` CLI commands.** The `instance` and `incident` subcommands are the supported diagnostic surface; direct API calls are not.
   25: 4. **When the local `.flow` may differ from the deployed BPMN, fetch the deployed asset.** Use `uip maestro flow instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json` to see what actually ran. Do not assume your local file matches.
   ```

9. **How to obtain FOLDER_KEY** — `references/shared/cli-conventions.md` lines 149–160

   ```text
   151: All `uip maestro flow instance` and `uip maestro flow incident get` commands require `--folder-key <FOLDER_KEY>` (`-f` shorthand). Without it, the command rejects the request before reaching the API.
   ```

10. **Report contract** — `references/operate/references/run.md` lines 44–55

   ```text
   46: The CLI response includes a **Studio Web URL** (where the user inspects the run) and an **instanceId** (for log/trace correlation). Parse both from the JSON output — typically `Data.studioWebUrl` and `Data.instanceId` — and **always show them as the first two lines of the summary**:
   …
   48: ```text
   49: Studio Web URL: <url>
   50: Instance ID: <instanceId>
   …
   55: If either value is missing from the response, emit the label with `<not returned by CLI>` rather than dropping the line. Do not bury these values below the run summary — the user should see them immediately without scrolling.
   ```

11. **Extraction mechanics and the Data-shape traps** — `references/shared/cli-conventions.md` lines 41–123

   ```text
   43: All `uip` commands support structured JSON output. Use `--output json` whenever output is parsed programmatically — every reference doc and recipe in this skill assumes it.
   …
   57: When extracting one field or a projection from `uip --output json`, use `--output-filter '<jmespath>'`. The CLI exposes `--output-filter <expression>` as a global flag on every subcommand; it applies a [JMESPath](https://jmespath.org/) expression to the `Data` envelope **before** printing. Write expressions starting at `Data` — do **not** prefix them with `Data.`.
   …
   75: `registry search` returns `Data` as a **flat array of PascalCase objects** — `NodeType`, `Category`, `DisplayName`, `Description`, `Version`, `Tags`, `AvailableOnTenant`. Not `Data.Nodes`, not lowercase `type`/`category`; those shapes do not exist. Knowing the shape lets you write the right expression on call #1 — which is the actual protection. Do **not** rely on `--output-filter` to *catch* a wrong-shape guess: a syntactically valid expression that simply doesn't match (e.g. `--output-filter "Nodes"` or `"Nodes[*].NodeType"` against the flat array) returns `Data: []` with **exit 0** — the same silent trap as `python3`/`jq` (see the silent-`[]` note below). Only an *invalid* expression fails loudly with exit 3: a syntax error, or a type error such as `keys(@)` on an array.
   …
   94: - **Check whether `Data` is array or object first** — `--output-filter "type(@)"` returns `"array"` or `"object"`. `keys(@)` throws on arrays (`Filter 'keys(@)' failed to evaluate: Invalid type: keys() expected argument 1 to be type (object) but received type array instead`), so use `type(@)` as the first probe.
   …
   97: - **Watch for silent `[]`** — when the JMESPath path doesn't match anything, the CLI returns `Data: []` with `Result: "Success"`. That's the exact silent-failure mode the docs are designed to surface. If you got `Data: []` and were expecting a value, double-check field-name casing — **and note casing differs by command:**
   ```

**Why it's mechanical:** The order is fixed, every step's arguments are fields of the previous step's JSON envelope, the stop condition is "an incident with a faulting element was returned", and the correlation is a key lookup in the `.flow` graph.

**Turn savings:** Because each call's arguments come from the previous call's stdout, the agent cannot batch them — this is 4–6 sequential turns today (status → incidents → incident get → variables → read `.flow` → correlate). One script call collapses the chain and emits the correlated report.

---

### 12. Pre-debug audit of what `flow validate` does not catch — DETECT

**Source:** `references/diagnose/references/failure-modes.md` §`flow validate` passes, `flow debug` faults; §Index

**What it does:** Runs the checks the skill states the validator omits, against the local `.flow` before a debug or publish: missing top-level `bindings[]` entries on resource nodes, a HITL node whose `completed` source port has no outgoing edge, `layout` sizes that disagree with each node's shape (inline agents 288×96, containers 560×320, everything else 96×96), `inputs.errorHandlingEnabled: true` on a node with no `error` edge, an `error` edge that rejoins the happy path or shares the success End node, and reference-ID fields carrying values not re-resolved against the bound connection. Line 338: "**Not caught** — these still surface only at `flow debug` or in deployed runs:" followed by the enumerated list at lines 340–345.

**Source text — one entry per rule, table, or constant the script implements (verbatim, with line numbers):**

1. **The authoritative not-caught list** — `references/diagnose/references/failure-modes.md` lines 338–345

   ```text
   338: **Not caught** — these still surface only at `flow debug` or in deployed runs:
   …
   340: - Reused reference IDs → see [Reused reference ID](#reused-reference-id--cross-connection-id-leakage)
   341: - Missing top-level `bindings[]` entries on resource nodes → see [Missing `bindings[]` on resource node](#missing-bindings-on-resource-node)
   342: - HITL `completed` port unwired → see [HITL `completed` port unwired](#hitl-completed-port-unwired)
   343: - Stale `layout` data → see [MST-9061](#mst-9061--misshapen-rectangle-nodes-in-studio-web) (cosmetic, not faulting)
   344: - Output-path walks against **open** output schemas — HTTP response bodies, script returns, free-text agent output. The deep-path walker is permissive by design: it skips when the producer's schema doesn't authoritatively declare the field's structure, so e.g. `=js:$vars.fetchWeather.output.body.current_weather` against an HTTP node that declares only `output: { type: "object" }` passes validate and faults only when the runtime response doesn't have that path.
   345: - Wrong-direction reads (reading an `out`-only variable) — currently a runtime concern; the direction discriminator isn't yet threaded into the validator context.
   ```

2. **The caught list — scope boundary** — `references/diagnose/references/failure-modes.md` lines 329–336

   ```text
   329: **Caught** (validate exits non-zero, with a precise field path and remediation hint):
   …
   331: - Missing `=js:` prefix on `$vars`/`$metadata`/`$self` (MST-9107) — emitted by cli-side `expression-prefix-validator`
   …
   335: - Missing End-node output mappings for declared `out` variables (`MISSING_OUTPUT_MAPPING`, **warning** severity) — flow-schema `output-mapping` rule
   336: - Connector `inputs.detail.configuration` missing, empty, missing the `essentialConfiguration` envelope, or containing invalid JSON inside the `=jsonString:` prefix — emitted with a shape hint pointing at `uip maestro flow node configure`. Re-run that command rather than hand-editing.
   ```

3. **Missing `bindings[]` — symptom and validate gap** — `references/diagnose/references/failure-modes.md` lines 291–315

   ```text
   295: `uip maestro flow validate` passes locally. At `uip maestro flow debug` (or in deployed runs), the resource node faults with:
   …
   307: `flow validate` checks JSON schema and cross-references; it does not validate that resource-node `model.context[]` entries are matched by top-level `bindings[]` entries.
   ```

4. **HITL unwired port** — `references/diagnose/references/failure-modes.md` lines 132–148

   ```text
   136: Flow execution reaches a HITL QuickForm node, the human task is created and completed, but the flow blocks indefinitely afterward. No further nodes execute.
   …
   140: The HITL node's `completed` output handle has no outgoing edge — there is no consumer for the `completed` port event.
   …
   144: Add an edge from the HITL node's `completed` port to the next node in the flow. After running `uip maestro flow hitl add`, always wire the `completed` port before validating.
   ```

5. **Layout-size thresholds** — `references/diagnose/references/failure-modes.md` lines 111–125

   ```text
   121: - Sets each node's `size` by its canvas shape (inline agents → 288×96, containers → 560×320, everything else → 96×96)
   ```

6. **Same thresholds, authoring side** — `references/shared/file-format.md` lines 220–224

   ```text
   222: - Sets each node's `size` to match its canvas shape: inline agents (`uipath.agent.autonomous` / `uipath.agent.conversational`, `shape: rectangle`) → `{ "width": 288, "height": 96 }`; containers (loops/groups) → `{ "width": 560, "height": 320 }`; everything else — including referenced `uipath.core.agent.<guid>` nodes — → `{ "width": 96, "height": 96 }`. A size that disagrees with the node's shape renders misshapen in Studio Web.
   ```

7. **`errorHandlingEnabled` — the two failing shapes** — `references/diagnose/references/failure-modes.md` lines 158–166

   ```text
   160: The failing node has `inputs.errorHandlingEnabled: true`, which suppresses its fault instead of faulting the run. Two shapes:
   …
   162: 1. **Flag with no handler** — the flag is set on a node with no outgoing `sourcePort: "error"` edge. The node swallows the exception and execution continues down `default` with missing output.
   163: 2. **Error path rejoins the happy path** — an `error` edge targets the next happy-path node, or reaches the same End node the success path reaches. The failure then runs the success path's output mappings against the failed node's empty output.
   …
   165: Both pass `uip maestro flow validate` — it checks structure, never whether an error path is meaningful.
   ```

8. **Reference implementation already published as a heredoc** — `references/diagnose/references/failure-modes.md` lines 172–201

   ```text
   171: ```bash
   172: python3 - "<ProjectName>.flow" <<'PY'
   173: import json, sys
   174: d = json.load(open(sys.argv[1]))
   175: E = d.get("edges", []); N = {n["id"]: n for n in d.get("nodes", [])}
   …
   190: for nid, n in N.items():
   191:     if (n.get("inputs") or {}).get("errorHandlingEnabled") is not True: continue
   192:     err, ok = targets(nid, "error"), targets(nid, exclude="error")
   193:     if not err:
   194:         print(f"{nid}: flag set, NO error edge"); continue
   ```

9. **How to act on each finding line** — `references/diagnose/references/failure-modes.md` lines 204–210

   ```text
   206: - **`flag set, NO error edge`** (shape 1) — remove `inputs.errorHandlingEnabled` from that node. The failure then faults the run, which is the visible, correct outcome.
   207: - **`REJOINS the happy path`** / **`shares success terminal(s)`** (shape 2) — repoint the `error` edge at a terminal the caller can distinguish from success: a distinct End node mapping an error/status `out` variable, or `core.logic.terminate` when recovery is impossible.
   208: - **`distinct terminal(s) … - ok`** — this node's error handling is wired correctly; look elsewhere.
   ```

10. **Error-path legality matrix** — `references/shared/file-format.md` lines 321–338

   ```text
   323: An `error` edge must not rejoin the happy path. When it does, every failure walks the success route and the run reports `Completed` while the work never happened — the flow "always looks successful."
   …
   325: | | Error-path target | Result |
   …
   327: | ✗ | The next node on the happy path | Failure is invisible; downstream nodes run on missing data |
   328: | ✗ | The same End node the success path reaches | Success path's output mappings run against the failed node's empty output |
   329: | ✓ | A **distinct** End node mapping an error/status `out` variable | Caller can tell failure from success |
   330: | ✓ | `core.logic.terminate` | Aborts the flow when recovery is impossible — see [terminate/impl.md](../author/references/plugins/terminate/impl.md) |
   331: | ✓ | A recovery branch that rejoins **only after obtaining valid data** — a retry that succeeded, or a fallback source that returned data | Downstream runs on real data, not on the failed node's empty output |
   ```

11. **Default-off policy** — `references/shared/file-format.md` lines 312–320

   ```text
   314: `inputs.errorHandlingEnabled` is **opt-in, and stays off unless the requirements name a failure fallback.** Turning it on suppresses the node's fault: the node returns instead of faulting and execution continues. Enable it only when both hold:
   …
   316: 1. The requirements state what should happen when this node fails ("if the call fails, …", "return X for invalid input", "handle timeouts") — **and**
   317: 2. You wire the node's `error` port to a handler that produces an outcome distinguishable from success.
   …
   319: Never set the flag on a node that has no outgoing `error` edge — it suppresses the fault with nothing to catch it, converting a real failure into a run that reports success. Let the CLI own the flag: `uip maestro flow edge add --source-port error` and `uip maestro flow format` set it from the error edges actually present. If you find the flag on a node with no error edge, remove it.
   ```

12. **`variables.nodes[]` presence check** — `references/diagnose/references/failure-modes.md` lines 60–98

   ```text
   64: A downstream script or expression reads `$vars.<sourceNodeId>.output` and gets `undefined` at runtime. Common shapes: `Cannot read property 'output' of undefined`, `Cannot read properties of undefined (reading '<field>')`, or a connector activity receiving an empty / undefined input that an upstream node should have populated. `uip maestro flow validate` accepts the file without complaint. The upstream node's own incident shows it ran successfully.
   …
   68: The `.flow` file is missing `variables.nodes[]` entries for the upstream node. The BPMN emitter walks `variables.nodes[]` to write the process-level `<uipath:inputOutput id="<nodeId>.<outputId>">` declarations the runtime needs — without them, the activity's local `output` value has no process variable to flow into, and downstream `$vars` reads fail.
   …
   93: One entry per declared output (trigger nodes: `output` only; action nodes: `output` + `error`; end / terminate: none).
   ```

13. **Reused-reference-id heuristic and the re-resolve command** — `references/diagnose/references/failure-modes.md` lines 219–246

   ```text
   233: Reference IDs (mailbox folders, Slack channels, Jira projects, Google Sheets, etc.) are **scoped to the specific authenticated account behind the connection**. They are not portable across connections, even when the connection points to the same connector type.
   …
   237: Always re-resolve reference IDs against the connection bound to the current flow. Never paste a value you saw in another flow or session:
   …
   240: uip is resources run list <connector-key> <objectName> --connection-id <CURRENT_CONNECTION_ID> --output json
   ```

14. **Warnings-are-defects gate** — `SKILL.md` lines 109

   ```text
   109: - **Never treat a `flow validate` exit code of 0 as "done" when it printed warnings.** Warnings are build defects the validator chose not to hard-fail — read every one and resolve it before declaring the flow complete. The connector-keyword warning (`node "…" mentions the "<connector>" connector keyword but uses the generic Managed HTTP type core.action.http.v2 with no connection binding`) means you took the brand-name shortcut (rule #3) — fix it by binding the connector, do not ship past it. A green exit with an unresolved connector warning still fails downstream connector checks and runs against an undefined endpoint at debug time.
   ```

**Why it's mechanical:** The skill enumerates exactly which conditions the validator misses, each check is a structural predicate over the parsed `.flow`, and the layout thresholds are given as fixed numbers per shape.

**Turn savings:** Each of these currently surfaces only after a `flow debug` — a consent-gated run with real side effects — followed by the diagnose ladder to attribute it, so 5+ turns per occurrence. The one exception is the error-handling shape, for which the skill already ships a copy-paste heredoc; folding it into a single audit script covers the rest of the list at the same cost.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** 12 of the 34 teaching areas are codifiable — under half. The skill's bulk is domain semantics that no script can carry: a 28-plugin catalog of per-node-type selection criteria and input shapes (roughly half the skill's total line count), the planning judgment layer (Maestro-fit gate, node-type ladders, topology pattern selection), the user-interaction protocol (dropdown questions, consent gates, narration opt-in), and four capabilities' worth of CLI surface where the CLI itself is the implementation (`init`, `node add`/`configure`, `validate`, `format`, `migrate`, `solution upload`, `pack`, `debug`, `process`, `job`, `instance`, the entire `eval` subtree). Several checks a script would otherwise own are already inside `flow validate` and `flow format` — expression-prefix linting, unresolved-reference checks, output-mapping warnings, `variables.nodes[]` regeneration, layout normalization — which caps how much a new audit script can add. The codifiable set is concentrated in one region (mechanical `.flow` JSON manipulation and post-hoc auditing) rather than spread across the skill.

**Why not None:** The `.flow` file is plain JSON with a fully documented schema, and the skill specifies its mutations as fixed ordered array splices (`Edit × 3`, `Edit × 4`) executed by text anchoring — the single largest scriptable win, since parsing the file dissolves the entire anchor-uniqueness discipline. Beyond it, the skill hands over closed tables and stated formulas ready to codify: a 31-row port reference plus 12 graph invariants, a per-field `=js:` required/forbidden matrix, enumerated Jint-unsupported constructs, a longest-first token-encoding substitution table, a stated agent-input flatten rule, and an explicit list of what `flow validate` does not catch. The diagnose ladder is a fixed 5-step chain whose steps cannot be batched today because each consumes the previous step's JSON.

**Evidence locations:**
- Structural mutation is text-anchored, not parsed: `references/author/references/greenfield.md` §Anchoring parallel `.flow` Edits (line 296 pre-flight uniqueness check)
- Composite edits declare their own tool-call counts: `references/author/references/editing-operations-json.md` §Composite Operations (lines 331, 352)
- Closed port table + graph invariants: `references/author/references/planning-arch.md` §Standard Port Reference, §Wiring Rules (lines 216, 270)
- Per-field expression contract: `references/shared/node-output-wiring.md` §Where the Rule Applies (line 11 rule, line 74 table end)
- Enumerated unsupported runtime constructs: `references/shared/variables-and-expressions.md` §Jint Engine Constraints (line 530)
- Fixed substitution table: `references/author/references/plugins/connector/impl.md` §Step 6c (line 400)
- Stated flatten rule, CLI explicitly does not derive it: `references/author/references/plugins/inline-agent/impl.md` §Wiring Flow Variables into Agent Prompts (line 50)
- Fixed, non-batchable diagnostic chain: `references/diagnose/references/troubleshooting-guide.md` §Diagnostic priority (line 9), Step 4 (line 62)
- Explicit list of gaps in `flow validate`: `references/diagnose/references/failure-modes.md` §`flow validate` passes, `flow debug` faults (line 338)
- Non-codifiable bulk — 28 plugin planning/impl pairs: `references/author/references/plugins/` (56 files); CLI-owned lifecycle: `references/operate/references/` (ship.md, run.md, manage.md), `references/evaluate/references/commands-reference.md`
- Checks already owned by the CLI: `references/diagnose/references/failure-modes.md` §`flow validate` passes, `flow debug` faults — "**Caught**" list (lines 329–336)

---

## Appendix — Files Carrying No Scriptable Procedure

Listed so the source map is complete: every file in the skill is either cited by a procedure above or accounted for here.

| Area | Files | Why not scriptable |
|---|---|---|
| Capability routing, question/consent/narration protocol | `SKILL.md` 12–90, `references/shared/ux-narration-and-todos.md` (all) | Conversational policy and intent classification |
| Planning judgment | `references/author/references/planning-arch.md` 12–55, 275–384, 552–630; `references/author/references/planning-impl.md` (all) | Requirements interpretation, live discovery, approval gate |
| Per-node-type semantics | `references/author/references/plugins/**` (56 files) except the spans cited in procedures 7, 8, 9, 10 | Selection criteria and input meaning per node type |
| Connector configuration workflow | `references/author/references/plugins/connector/impl.md` 54–360, 518–544, 703–738 | Live-tenant calls, field elicitation, filter semantics |
| Operate lifecycle | `references/operate/**` except `run.md` 44–55 | CLI calls, already chainable in one `Bash`; consent decisions |
| Evaluate | `references/evaluate/**` | CLI CRUD + run surface; `--only-failed` already implements the failure rules (`running-guide.md` 204–213) |
| CLI conventions | `references/shared/cli-conventions.md` 1–40, 124–177 | Binary/version probe already given as an inline snippet |
| Variables semantics | `references/shared/variables-and-expressions.md` 35–509, 543–727 | Schema teaching; `variables.nodes[]` regeneration is `flow format` |
| Skill-doc maintenance | `.maintenance/**` | Already fully scripted (`check-all.sh` orchestrates all 9 checkers); "Not loaded by agents during normal use" (`.maintenance/README.md` 3) |
