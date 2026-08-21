# Classification Details — uipath-maestro-flow

**Classification: Partial**

---

## What the Skill Teaches

Build, edit, validate, operate, diagnose, and evaluate UiPath Flow (`.flow`) projects — covering four capabilities (Author, Operate, Diagnose, Evaluate) with node authoring as the primary focus.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| **1** | **Greenfield 3-turn execution map** | **Yes — TRANSFORM-PIPELINE** | Rule 10 / greenfield.md: fixed T1→T2→T3 sequence (scaffold + registry pull + CLI node add → Read + Edit/Write → configure + validate + format) |
| **2** | **Resource discovery order (search before create)** | **Yes — DETECT** | Rule 3: pull → search tenant registry → search local → create; explicit priority order with defined fallback |
| **3** | **Node ownership classification (CLI-owned vs user-owned)** | **Yes — DETECT** | Rule 9: connector/connector-trigger/managed-HTTP → CLI; all others → user; explicit binary rule |
| **4** | **Post-build validation** | **Yes — VALIDATE/CHECK** | `uip maestro flow validate <file> --output json`; also `flow format` for diagram generation |
| 5 | Flow design (which nodes to add, how to structure the process, conditional logic) | No | Core authoring judgment — selecting node types, designing the flow structure, choosing gateway conditions |
| 6 | Connector disambiguation (multiple connectors for same intent) | No | Requires consulting the Disambiguation ladder and IS rules; domain judgment |
| 7 | Failure diagnosis (incidents, runtime variables, known failure modes) | No | Investigation requires interpreting error context, matching failure modes, and determining root cause |
| 8 | Evaluation design (evaluators, eval sets, data points, comparison) | No | Requires judgment on what to test, which evaluator type fits, and how to interpret comparison results |
| 9 | Operate lifecycle (upload, publish, deploy, debug, manage instances) | Marginal | CLI-driven pipeline but every cloud action requires explicit user consent gate; not automatable end-to-end |

---

## Codifiable Procedures (not yet scripted)

### 1. Greenfield 3-Turn Execution Map — TRANSFORM-PIPELINE

**Source:** `skills/uipath-maestro-flow/SKILL.md` §Critical rules, Rule 10

**What it does:** For new flow builds, the skill mandates a fixed 3-turn batching pattern to minimize round-trips: T1 chains scaffold + registry pull + CLI-owned `node add` in parallel with `registry get` and discovery reads; T2 reads the scaffolded `.flow` and applies `Edit`/`Write` for user-owned nodes and edge wiring; T3 chains `node configure && validate && format`. Each turn's tool calls are parallelized where data dependencies allow. Line 97: "A typical greenfield build is 3 turns, not 10+: (T1) one chained Bash for scaffold + registry pull + CLI-owned `node add`, in parallel with `registry get` and `Read` calls for any extra discovery; (T2) one `Read` of the scaffolded `.flow` in parallel with the `Edit`/`Write` calls that add the End node and wire edges; (T3) one chained Bash for `node configure && validate && format`."

**Why it's mechanical:** The turn structure and batching rules are explicit and order-dependent; the only judgment within each turn is which specific nodes and edges to add, not how to batch the tool calls.

**Turn savings:** Without following this map, agents spend 10+ turns on sequential commands; enforcing the map as a default collapses scaffolding overhead by 70%.

---

### 2. Resource Discovery — DETECT

**Source:** `skills/uipath-maestro-flow/SKILL.md` §Critical rules, Rule 3

**What it does:** Before choosing a node type for any named external service or resource, the skill mandates a fixed priority search: (1) `uip maestro flow registry pull --force && registry search "<name>"` against the tenant registry; (2) `registry list --local` for in-solution resources; (3) only then scaffold or create. The connector-discovery variant additionally requires `uip is connections list --all-folders` for any connector key found. Line 76: "Resource discovery order — search before creating. When the prompt references an existing resource by name, follow this order strictly before deciding the resource doesn't exist: 1. Pull, then search the tenant registry… 2. In-solution local discovery… 3. Only then create/scaffold."

**Why it's mechanical:** The three-step priority order is explicit; the decision tree (found in step 1 → use; found in step 2 → use; not found → create) is fully deterministic.

**Turn savings:** Without a script, agents skip to creation directly (a known anti-pattern the skill calls out), wasting turns on scaffolding resources that already exist.

---

### 3. Node Ownership Classification — DETECT

**Source:** `skills/uipath-maestro-flow/SKILL.md` §Critical rules, Rule 9

**What it does:** Every node in a `.flow` file has exactly one author — either the CLI (`uip maestro flow node add` + `configure`) or the user (Edit/Write). The classification rule is binary: connector activities, connector triggers, wait-for-events, and managed HTTP (`core.action.http.v2`) are CLI-owned; all other node types are user-owned. Mixing authoring methods on a CLI-owned node corrupts `inputs.detail`. Line 96: "Every node has exactly one author — Edit/Write or CLI, never both. Connector activities…, connector triggers…, wait for events…, and managed HTTP (`core.action.http.v2`) are CLI-owned — use `uip maestro flow node add` + `uip maestro flow node configure`. Every other node type… is user-owned."

**Why it's mechanical:** The classification uses an explicit enumeration of CLI-owned types; any type not on the list is user-owned; no gray areas remain once the type is known.

**Turn savings:** Without upfront classification, agents frequently apply the wrong authoring tool, which corrupts `bindings[]` or `inputs.detail` and requires re-runs; a pre-check script prevents the class of errors entirely.

---

### 4. Post-Build Validation — VALIDATE/CHECK

**Source:** `skills/uipath-maestro-flow/SKILL.md` §Anti-patterns (universal)

**What it does:** After every edit session the skill requires running `uip maestro flow validate <file> --output json` and reading every warning, not just errors. A green exit with unresolved warnings (especially connector-keyword warnings) is not "done." The format step (`uip maestro flow format`) generates the diagram. Line 105: "Never run `flow debug` as a validation step — debug executes the flow with real side effects (rule #2). Use `flow validate` for checking correctness."

**Why it's mechanical:** The command is fixed; success requires exit 0 and no unresolved warnings; the connector-keyword warning has an explicit resolution path.

**Turn savings:** Without a script, agents run validate, partially read JSON output, and miss warnings in 1–2 turns; a structured wrapper returning error/warning counts collapses to one actionable result.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** Flow design — selecting which nodes to add, designing the flow structure, choosing gateway conditions, wiring business logic — is the skill's primary purpose and is entirely judgment-based. The Author capability's core value (what process to build, how to connect it) cannot be codified. Additionally, three of the four capabilities (Operate, Diagnose, Evaluate) are heavily judgment-dependent: diagnosing failures requires contextual interpretation, evaluation design requires deciding what to test, and operate gates on user consent at every cloud step.

**Why not None:** The 3-turn execution map (TRANSFORM-PIPELINE), resource discovery priority order (DETECT), node ownership classification (DETECT), and post-build validation (VALIDATE/CHECK) are all explicitly codifiable, CLI-driven procedures with fixed rules and no judgment required.

**Evidence locations:**
- 3-turn map: `skills/uipath-maestro-flow/SKILL.md` §Critical rules, Rule 10 (line 97)
- Resource discovery order: `skills/uipath-maestro-flow/SKILL.md` §Critical rules, Rule 3 (line 76)
- Node ownership rule: `skills/uipath-maestro-flow/SKILL.md` §Critical rules, Rule 9 (line 96)
- Judgment for flow design: `skills/uipath-maestro-flow/SKILL.md` §When to use this skill — Author section
