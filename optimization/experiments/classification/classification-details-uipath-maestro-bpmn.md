# Classification Details — uipath-maestro-bpmn

**Classification: Partial**

---

## What the Skill Teaches

The skill covers five distinct work areas: authoring, validation, metadata management, operate (packaging / lifecycle), and diagnose. Below is a breakdown of each area and whether its procedures are codifiable.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Registry discovery (pull / list / search / get, IS connections list) | No | CLI calls requiring user confirmation and intent mapping |
| 2 | Connector enrichment (`registry get --connection-id --object-name`) | No | CLI call; resource identifiers come from discovery or user |
| 3 | Template placeholder filling (`{id}`, `{name}`, `{incomingEdge}`, etc.) | No | Requires agent judgment for process structure and content |
| 4 | Structural BPMN authoring (process scaffold, sequence flows, gateways, events, boundary events, subprocesses, multi-instance markers) | No | Generative/creative; process shape comes from requirements |
| 5 | **Diagram generation (`bpmndi:BPMNDiagram`)** | **Yes — BUILD-MODEL** | Fixed sizes (tasks 100×80, events 36×36, gateways 50×50), left-to-right layout; fully deterministic given the process graph |
| 6 | **BPMN validation** | **Already scripted** | `validator/validate-bpmn.mjs` — runs all 19 PO.Frontend rules offline; this is an existing skill script, excluded per instructions |
| 7 | Expression authoring (`=vars.X`, `=bindings.X`, `=js:`, scoping rules) | Marginal | Rules are explicit but application is part of authoring; a post-hoc syntax checker is a VALIDATE, but minor value |
| 8 | **Package metadata scaffolding** (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) | **Yes — FORMAT-CONVERT / BUILD-MODEL** | `local-metadata-regeneration-guide.md` gives exact JSON shapes and derivation rules from BPMN root elements |
| 9 | **Package metadata drift check** | **Yes — VALIDATE** | `local-metadata-regeneration-guide.md` §Drift Handling gives explicit rules: `entry-points.json` ids must match root `uipath:entryPointId`s; `bindings_v2.json` version must be `"2.0"`; `operate.json` must point at the correct BPMN file |
| 10 | Packaging (`uip maestro bpmn pack`) | No | CLI call |
| 11 | Upload / publish / deploy | No | CLI calls; require explicit user consent |
| 12 | Run / debug / manage instances | No | CLI calls; require explicit user consent and post-run judgment |
| 13 | Diagnose priority ladder (incidents → variables → deployed asset → element executions → package files → traces) | No | CLI reads requiring interpretation and analysis at each step |
| 14 | Agent wrapper selection (processType → extension type) | No (marginal) | A 4-row lookup table; too small to warrant a standalone script |

---

## Codifiable Procedures (not yet scripted)

### 1. Diagram auto-layout — BUILD-MODEL

**Source:** `references/structural-bpmn.md` §Diagram interchange (`bpmndi:BPMNDiagram`)

**What it does:** Given a BPMN file with `<bpmn:process>` content but no `<bpmndi:BPMNDiagram>`, parse all flow nodes and sequence flows, assign left-to-right positions using fixed node dimensions (tasks 100×80, events 36×36, gateways 50×50), and emit `BPMNShape` + `BPMNEdge` XML to complete the file.

**Why it's mechanical:** The layout rule is fully specified: left-to-right ordering by process topology, non-overlapping bounds, fixed per-type dimensions. No content judgment involved.

**Turn savings:** The agent currently calculates x/y coordinates by hand for every node and flow — typically 4-8 turns for a medium process.

---

### 2. Package metadata scaffolding — FORMAT-CONVERT / BUILD-MODEL

**Source:** `references/shared/local-metadata-regeneration-guide.md` §Minimal Local Metadata Shape and §Entry Point Rules and §Binding Rules

**What it does:** Given a `.bpmn` file (and its basename/project name), parse:
- Root `bpmn:startEvent` elements with `uipath:entryPointId` → generate `entry-points.json` entries
- Root `uipath:variables` with `elementId` → generate `inputSchema` / `outputSchema`
- Root `uipath:bindings` → generate `bindings_v2.json` resources array (empty for no-dependency projects)
- Produce `operate.json`, `project.uiproj`, `package-descriptor.json` from the project name and BPMN filename

**Why it's mechanical:** Every field derivation rule is stated explicitly: `id` = `uipath:entryPointId` value; `filePath` = `/content/<bpmn-file>#<start-event-id>`; `bindings_v2.json.version` = `"2.0"`; `package-descriptor.json.content` = list of generated files under `content/`.

**Turn savings:** The agent currently writes all 5 JSON files manually across multiple turns.

---

### 3. Package metadata drift check — VALIDATE

**Source:** `references/shared/local-metadata-regeneration-guide.md` §Drift Handling + §Entry Point Rules + §Binding Rules

**What it does:** Given a `.bpmn` file plus existing `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json`, verify:
- Each root start event with `uipath:entryPointId` has a matching entry in `entry-points.json` with correct `id` and `filePath`
- `bindings_v2.json` has `"version": "2.0"` and a `resources` array
- `operate.json` `main` matches the BPMN filename
- `package-descriptor.json` `content` lists the BPMN and all generated JSON files

Exit 0 if clean, exit 1 with specific drift findings.

**Why it's mechanical:** All validation rules are explicit comparisons with no judgment.

**Turn savings:** The agent currently reads and compares these files textually — typically 2-3 turns per drift check.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The majority of the skill is judgment-intensive and not codifiable:
- Registry discovery and template retrieval require user confirmation and intent mapping (which node type best matches the requirement)
- Structural BPMN authoring — gateway topology, event/boundary event design, subprocess decomposition — is generative design work
- Operate and diagnose steps are CLI calls interleaved with analysis and consent gates

These three areas (discovery/authoring, operate, diagnose) represent roughly 75% of the skill's content by reference volume and by the cognitive work they demand.

**Why not None:** Three distinct procedures are codifiable and not yet scripted (diagram layout, metadata scaffolding, drift check), and the existing validator is already a complete script for the validation step. New scripts for the three procedures would meaningfully reduce agent turns in the metadata management sub-workflow.

**Evidence locations:**
- Diagram layout rules: `references/structural-bpmn.md` §Diagram interchange
- Package metadata shapes and derivation rules: `references/shared/local-metadata-regeneration-guide.md` §Minimal Local Metadata Shape, §Entry Point Rules, §Binding Rules, §Drift Handling
- Already-scripted validator: `validator/validate-bpmn.mjs`, `validator/README.md`
- Non-codifiable authoring: `references/registry-workflow.md`, `references/structural-bpmn.md` (authoring sections)
- Non-codifiable operate/diagnose: `references/operate/CAPABILITY.md`, `references/diagnose/CAPABILITY.md`, `references/diagnose/references/troubleshooting-guide.md`
