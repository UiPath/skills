# Proposal: Merge `uipath-maestro-flow` + `uipath-lattice-flow` into `uipath-flow`

> Status: Draft
> Date: 2026-04-09
> Deprecates: `uipath-maestro-flow`, `uipath-lattice-flow`

---

## 1. Problem Statement

Two skills exist that teach agents to work with UiPath `.flow` files:

- **`uipath-maestro-flow`** — CRUD via CLI commands (`uip flow node add`, `uip flow edge add`, etc.). 46 files, plugin system with `planning.md` + `impl.md` per node type.
- **`uipath-lattice-flow`** — CRUD via direct `.flow` JSON editing (Read/Write/Edit tools). 40 files, bundled node schemas in `references/nodes/`, starter templates in `assets/templates/`.

Both teach the same conceptual model (same `.flow` JSON format, same node types, same ports, same variables, same expressions, same validation rules). The only difference is **how operations are executed**.

**Goal**: One self-contained skill, `uipath-flow`, that covers both approaches with a clean two-layer architecture — shared abstraction, swappable implementation.

---

## 2. Architecture

```
                       ┌──────────────────────────────────────────┐
                       │         ABSTRACTION LAYER (shared)        │
                       │                                          │
                       │  Strategy & Planning                     │
                       │    Two-phase planning methodology        │
                       │    Node selection catalog & heuristics   │
                       │    Topology patterns (7 named patterns)  │
                       │    Mermaid diagram conventions            │
                       │                                          │
                       │  Node Knowledge                          │
                       │    Semantics, ports, inputs, outputs     │
                       │    Definition blocks (canonical schemas) │
                       │    Instance templates                    │
                       │    Common mistakes                       │
                       │                                          │
                       │  Flow Mechanics                          │
                       │    .flow JSON schema                     │
                       │    Variables (globals/nodes/updates)     │
                       │    Expressions (=js:, {{ }}, $vars)      │
                       │    Edge wiring rules & port reference    │
                       │    Validation checklist (17 items)       │
                       │    Subflow scope isolation               │
                       │    Binding system (connectors + resources)│
                       ├──────────────────┬───────────────────────┤
                       │    CLI Mode      │  JSON Authoring Mode  │
                       │                  │                       │
                       │  uip flow        │  Read/Write/Edit      │
                       │  node add/       │  .flow JSON directly  │
                       │  edge add/       │                       │
                       │  node configure  │  Bundled schemas as   │
                       │                  │  copy-paste source    │
                       │  registry get    │                       │
                       │  for definitions │  ID generation        │
                       │                  │  algorithms           │
                       │  Auto-maintains  │                       │
                       │  variables.nodes │  Manual regeneration  │
                       │                  │  of variables.nodes   │
                       │  uip flow        │                       │
                       │  validate        │  Manual checklist +   │
                       │  (primary)       │  optional CLI validate│
                       └──────────────────┴───────────────────────┘

                       Converge: publish (uip solution bundle/upload)
                                 debug   (uip flow debug)
```

### Mode Selection

The agent does NOT auto-select. Mode is determined by:

| Signal | Mode |
|--------|------|
| User says "use CLI" or references `uip` commands | CLI |
| User says "edit the JSON" or "author directly" | JSON Authoring |
| No explicit preference stated | Ask the user |
| Flow needs dynamic resource or connector nodes | Either mode works; both need CLI for registry/IS discovery |
| Publishing or debugging | Always CLI (both modes converge) |

Default recommendation when asked: **JSON Authoring** for OOTB-only flows (no external dependencies), **CLI** when the user is already working with `uip` commands.

---

## 3. Node Documentation Strategy: How Plugins and Node Refs Merge

This is the core design decision. The existing skills organize node documentation differently:

| Skill | Structure | Content per node |
|-------|-----------|-----------------|
| maestro-flow | 2 files per node: `planning.md` + `impl.md` | Planning: selection heuristics, ports, topology. Impl: registry validation, CLI commands, JSON from registry, debug table |
| lattice-flow | 1 file per node | Identity, ports, inputs, outputs, full definition JSON, instance example, common mistakes |

Both contain three **distinct kinds** of content per node, even though they organize them differently:

1. **Strategy content** — When to select this node, selection heuristics, how it fits topology patterns, planning annotations. This is pure abstraction. It never changes regardless of whether you use CLI or JSON.

2. **Schema content** — The canonical definition block, instance template, handle configuration, input/output schemas. This is shared reference data. Both modes need it. CLI mode gets it from `registry get`; JSON mode copies it from the reference file. The data itself is identical.

3. **How-to content** — The CLI commands to add/configure/validate the node, OR the JSON editing steps to insert into arrays and regenerate variables. This is purely implementation-specific.

### Where Each Kind Lives in the Merged Skill

```
Strategy content:
  ├── planning-guide.md          Condensed node catalog with selection
  │                              heuristics, topology patterns, and
  │                              planning annotation format. Read during
  │                              Phase 1. Replaces all planning.md files.
  │
  └── nodes/*.md (top sections)  Detailed semantics, ports, inputs,
                                 outputs per node. Read during Phase 2.

Schema content:
  └── nodes/*.md (bottom sections)  Definition block + instance template.
                                    Mode-neutral. JSON mode copies directly.
                                    CLI mode uses for verification.

How-to content:
  ├── cli/workflow-guide.md      Generic CLI patterns (node add, edge add,
  │                              registry get, node configure). Covers all
  │                              node types via parameterized instructions.
  │                              Replaces all impl.md files.
  │
  └── json/workflow-guide.md     Generic JSON patterns (insert into arrays,
                                 copy definition, generate IDs, regenerate
                                 variables.nodes). Replaces lattice-flow's
                                 inline procedures.
```

### Node Reference File Structure (Unified)

Each `nodes/*.md` file is mode-neutral and contains:

```
# Node Name (core.action.script)

## When to Use                             ← from planning.md
Selection criteria, decision heuristics.

## Ports                                   ← from both (shared)
| Direction | Port ID   | Notes                          |
|-----------|-----------|--------------------------------|
| target    | input     |                                |
| source    | success   | NOT "output" — #1 wiring mistake |
| source    | error     | Only when errorHandlingEnabled  |

## Inputs                                  ← from both (shared)
| Field  | Type   | Required | Notes              |
|--------|--------|----------|--------------------|
| script | string | yes      | Must return {}     |

## Outputs                                 ← from both (shared)
| Key    | Type   | Source Expression  |
|--------|--------|--------------------|
| output | object | =result.response   |
| error  | object | =result.Error      |

## Definition                              ← from lattice-flow (bundled)
<complete JSON block — copy verbatim>      CLI mode: verify against registry get
                                           JSON mode: copy into definitions[]

## Instance Example                        ← from lattice-flow
<complete JSON instance>

## Common Mistakes                         ← merged from both
1. Using "output" as source port instead of "success"
2. Returning bare scalar instead of object
3. Using console.log (Jint has no console)
```

### Why This Works for Both Modes

**JSON Authoring agent reads a node file and sees:**
> "Copy the Definition block into `workflow.definitions[]`. Copy the Instance Example as a starting point for my node in `workflow.nodes[]`. Adjust inputs. Follow `json/workflow-guide.md` for the generic insert+regenerate pattern."

**CLI agent reads the same node file and sees:**
> "Run `uip flow registry get core.action.script --output json` to get the definition. Verify it matches the structure shown here. Use `uip flow node add` with flags from `cli/workflow-guide.md`."

The node file itself doesn't say "do it this way." It provides the knowledge. The mode-specific workflow guide provides the method.

### How the Plugin System Content Redistributes

| Plugin content (maestro-flow) | Destination (merged skill) |
|-------------------------------|---------------------------|
| `planning.md` → selection heuristics | `planning-guide.md` node catalog |
| `planning.md` → port summary | `nodes/*.md` Ports section |
| `planning.md` → topology considerations | `planning-guide.md` topology patterns |
| `planning.md` → planning annotation | `planning-guide.md` output format |
| `impl.md` → registry validation | `cli/workflow-guide.md` generic pattern |
| `impl.md` → CLI commands | `cli/workflow-guide.md` parameterized |
| `impl.md` → JSON structure | `nodes/*.md` Definition + Instance sections |
| `impl.md` → debug table | `nodes/*.md` Common Mistakes section |

### How the Lattice-Flow Node Content Redistributes

| Node ref content (lattice-flow) | Destination (merged skill) |
|--------------------------------|---------------------------|
| Identity, BPMN model | `nodes/*.md` header |
| Ports table | `nodes/*.md` Ports section |
| Inputs/outputs schema | `nodes/*.md` Inputs/Outputs sections |
| Definition block | `nodes/*.md` Definition section (kept) |
| Instance example | `nodes/*.md` Instance Example section (kept) |
| Common mistakes | `nodes/*.md` Common Mistakes section |
| ID generation algorithms | `json/authoring-guide.md` |
| variables.nodes regeneration | `json/workflow-guide.md` |
| Validation checklist | `validation-guide.md` (shared) |

### Dynamic Resource Nodes

Dynamic resource nodes (RPA workflow, agent, API workflow, agentic process) follow the same three-kind split, with one difference: **both modes require CLI for registry discovery**. The registry interaction (`registry pull`, `registry search`, `registry get`) is not mode-specific — it's required to discover tenant-specific node types regardless of how you apply the result.

```
dynamic-nodes/
├── resource-node-guide.md     Shared structure: handles, bindings pattern,
│                              registry workflow (used by both modes),
│                              mock placeholder pattern, error schema
├── rpa-workflow-guide.md      Type-specific: serviceType, input/output
│                              patterns, .NET naming, complete examples,
│                              definition + instance templates
├── agent-guide.md             Type-specific + personal workspace agents
├── api-workflow-guide.md      Type-specific
└── agentic-process-guide.md   Type-specific + Flow type distinction
```

The `resource-node-guide.md` documents the 12-step add-resource-node procedure with mode branching:

| Step | Shared or Mode-Specific |
|------|------------------------|
| 1. Registry pull | Shared (CLI required) |
| 2. Registry search | Shared (CLI required) |
| 3. Registry get | Shared (CLI required) |
| 4-5. Extract definition + inputs | Shared (from registry output) |
| 6. Add node to flow | **CLI**: `uip flow node add` / **JSON**: insert into arrays |
| 7. Add definition | **CLI**: auto / **JSON**: copy from registry output |
| 8. Generate bindings | **CLI**: auto / **JSON**: manual, follow template |
| 9. Wire edges | **CLI**: `uip flow edge add` / **JSON**: insert into edges[] |
| 10. Set inputs | **CLI**: via `--input` flags / **JSON**: edit `inputs` directly |
| 11. Regenerate variables.nodes | **CLI**: auto / **JSON**: manual |
| 12. Validate | Both: `uip flow validate` |

### Connector Nodes

Connector nodes are the most complex. They always require CLI for IS interaction (connection discovery, resource description, reference resolution) regardless of mode. The mode difference is only in the final wiring step.

```
connectors/
└── connector-guide.md         Full lifecycle:
                               - 4-tier decision ladder (planning)
                               - 6-step configuration workflow
                               - bindings_v2.json schema
                               - Mode branching at Step 6 only
                               - Debug/common errors table
```

**Connector workflow with mode branching:**

| Step | Content | Mode |
|------|---------|------|
| Tier selection (planning) | 4-tier decision ladder | Shared |
| Step 1: Fetch connection | `uip is connections list` + ping | Shared (CLI) |
| Step 2: Enriched registry get | `uip flow registry get --connection-id` | Shared (CLI) |
| Step 3: Describe resource | `uip is resources describe` + read metadataFile | Shared (CLI) |
| Step 4: Resolve references | `uip is resources execute list` | Shared (CLI) |
| Step 5: Validate required fields | Check metadataFile, ask user if missing | Shared |
| Step 6: Configure node | **CLI**: `uip flow node configure --detail` / **JSON**: edit `inputs.detail` directly | Mode-specific |
| Write bindings_v2.json | **CLI**: auto (node configure writes it) / **JSON**: manual edit | Mode-specific |

---

## 4. File Structure

```
skills/uipath-flow/
├── SKILL.md                                    # Unified skill definition
│
├── references/
│   │
│   │  ── Shared Abstraction Layer ──
│   │
│   ├── flow-schema.md                          # .flow JSON format, entity schemas
│   ├── variables-guide.md                      # Variables, expressions, $vars, Jint
│   ├── edge-wiring-guide.md                    # Port reference table, wiring patterns
│   ├── validation-guide.md                     # 17-item checklist + optional CLI validate
│   ├── planning-guide.md                       # Two-phase methodology, node catalog,
│   │                                           # topology patterns, mermaid rules,
│   │                                           # .arch.plan.md + .impl.plan.md formats
│   ├── bindings-guide.md                       # bindings_v2.json + workflow.bindings
│   ├── subflow-guide.md                        # Scope isolation, loop subflows
│   ├── project-setup-guide.md                  # Project scaffolding (both paths)
│   ├── publish-debug-guide.md                  # Always CLI: bundle/upload/debug
│   │
│   │  ── Implementation Layer ──
│   │
│   ├── cli/
│   │   ├── commands-reference.md               # All uip flow|solution|is commands
│   │   └── workflow-guide.md                   # CLI step-by-step patterns
│   │
│   ├── json/
│   │   ├── authoring-guide.md                  # ID generation, JSON editing patterns
│   │   └── workflow-guide.md                   # JSON step-by-step patterns
│   │
│   │  ── Node Knowledge (mode-neutral) ──
│   │
│   ├── nodes/                                  # 19 OOTB node types
│   │   ├── trigger-manual.md
│   │   ├── trigger-scheduled.md
│   │   ├── action-script.md
│   │   ├── action-http.md
│   │   ├── action-transform.md
│   │   ├── action-transform-filter.md
│   │   ├── logic-decision.md
│   │   ├── logic-switch.md
│   │   ├── logic-loop.md
│   │   ├── logic-foreach.md
│   │   ├── logic-while.md
│   │   ├── logic-merge.md
│   │   ├── logic-delay.md
│   │   ├── logic-mock.md
│   │   ├── control-end.md
│   │   ├── control-terminate.md
│   │   ├── hitl.md
│   │   ├── mock-blank.md
│   │   └── mock-node.md
│   │
│   ├── dynamic-nodes/                          # Tenant resource nodes
│   │   ├── resource-node-guide.md              # Shared pattern + registry workflow
│   │   ├── rpa-workflow-guide.md
│   │   ├── agent-guide.md
│   │   ├── api-workflow-guide.md
│   │   └── agentic-process-guide.md
│   │
│   └── connectors/                             # IS connector nodes
│       └── connector-guide.md                  # Full lifecycle + bindings_v2.json
│
└── assets/
    └── templates/                              # Starter templates (both modes)
        ├── minimal-flow-template.json
        ├── decision-flow-template.json
        ├── loop-flow-template.json
        ├── http-flow-template.json
        ├── scheduled-trigger-template.json
        ├── connector-flow-template.json
        ├── multi-agent-template.json
        └── project-scaffold-template.json
```

**File count: ~38** (vs 86 combined from both existing skills)

### File-Level Content Sources

| Merged file | Primary source | Secondary source |
|-------------|---------------|-----------------|
| `SKILL.md` | New (unified) | Rules from both |
| `flow-schema.md` | lattice `flow-schema-guide.md` | maestro `flow-file-format.md` |
| `variables-guide.md` | lattice `variables-guide.md` | maestro `variables-and-expressions.md` |
| `edge-wiring-guide.md` | lattice `edge-wiring-guide.md` | maestro port tables from plugins |
| `validation-guide.md` | lattice `validation-checklist.md` | maestro validation loop rule |
| `planning-guide.md` | maestro `planning-arch.md` + `planning-impl.md` | lattice quick-start structure |
| `bindings-guide.md` | lattice `bindings-guide.md` | maestro connector bindings |
| `subflow-guide.md` | lattice `subflow-guide.md` | maestro subflow plugin |
| `project-setup-guide.md` | lattice `project-scaffolding-guide.md` | maestro create-solution workflow |
| `publish-debug-guide.md` | maestro SKILL.md steps 7-8 | New |
| `cli/commands-reference.md` | maestro `flow-commands.md` | — |
| `cli/workflow-guide.md` | maestro impl.md files (generic patterns extracted) | — |
| `json/authoring-guide.md` | lattice `project-scaffolding-guide.md` (ID algorithms) | — |
| `json/workflow-guide.md` | lattice SKILL.md common edits | — |
| `nodes/*.md` (19 files) | lattice `references/nodes/*.md` | maestro `plugins/*/planning.md` heuristics |
| `dynamic-nodes/*.md` (5 files) | lattice `references/dynamic-nodes/*.md` | maestro `plugins/*/impl.md` registry steps |
| `connectors/connector-guide.md` | maestro `plugins/connector/*.md` | lattice connector template |
| `assets/templates/*.json` (8 files) | lattice `assets/templates/` | — |

---

## 5. SKILL.md Design

### Frontmatter

```yaml
---
name: uipath-flow
description: "Create, edit, validate UiPath Flow projects (.flow). Two modes: CLI (uip flow) or direct JSON authoring. OOTB + dynamic resource + connector nodes. For XAML->uipath-rpa."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---
```

Description: 195 characters (under 250 limit). Front-loads identity (".flow"), signals both modes, includes redirect.

### Body Structure

```
# UiPath Flow

## Mode Selection
<table of signals → mode, default recommendation>

## Critical Rules
<15 unified rules, mode-tagged where they differ>

## Quick Start: New Flow
<10-step procedure with CLI/JSON branching per step>

## Common Edits
<Add node, remove node, add edge, add variable —
 each with "CLI:" and "JSON:" sub-steps>

## Reference Navigation
<table: "I want to..." → file to read>

## Node Catalog
<OOTB types table (19) + dynamic resource types table (4+)>

## Anti-Patterns
<merged from both skills, deduplicated>

## Completion Output
<6 items to report when done>
```

### Critical Rules (Unified, 15 Rules)

| # | Rule | Applies to |
|---|------|-----------|
| 1 | Every edge must have both `targetPort` and `sourcePort`. | Both |
| 2 | Every node type needs a definitions entry. **CLI**: copy from `registry get`. **JSON**: copy from the node's reference file. Never hand-write. | Both (mode-tagged) |
| 3 | For multi-node flows, complete both planning phases with user approval gates before building. | Both |
| 4 | Phase 1: `registry search`/`list` only. Phase 2: `registry get` required for all node types. | Both |
| 5 | Script nodes must `return {}` — never a bare scalar. | Both |
| 6 | Use `=js:` prefix for all expressions. | Both |
| 7 | Every `out` variable must be mapped on every reachable End node. | Both |
| 8 | Only edit `<ProjectName>.flow` and optionally `bindings_v2.json`. | Both |
| 9 | Node and edge IDs must be unique. | Both |
| 10 | Regenerate `variables.nodes` after every node add/remove. **CLI**: automatic. **JSON**: manual — follow the regeneration algorithm. | Both (mode-tagged) |
| 11 | Validate after every structural change. **CLI**: `uip flow validate`. **JSON**: run the 17-item checklist, optionally also CLI validate. | Both (mode-tagged) |
| 12 | Use `core.logic.mock` as placeholder for missing dynamic resource nodes. | Both |
| 13 | Do not run `uip flow debug` without explicit user consent. | Both |
| 14 | Dynamic resource and connector nodes require CLI for registry/IS discovery, regardless of mode. | Both |
| 15 | Always use `--output json` on all `uip` commands when parsing output. Never invoke other skills automatically — provide handoff instructions. | Both |

### Quick Start with Mode Branching

```
Step 1 — Determine mode
  Ask user or detect from context.

Step 2 — Project setup
  CLI: uip solution new → uip flow init → uip solution project add
  JSON: mkdir, create project.uiproj, copy template from assets/templates/

Step 3 — Plan (multi-node flows)
  Phase 1: Read planning-guide.md, design topology, produce .arch.plan.md
  GATE: user approval
  Phase 2: Read planning-guide.md, resolve implementations, produce .impl.plan.md
  GATE: user approval

Step 4 — Build
  For each node in the plan:
    Read nodes/<type>.md for ports, inputs, definition
    CLI: uip flow node add + uip flow edge add
    JSON: Insert into nodes[], definitions[], edges[]. Regenerate variables.nodes.

Step 5 — Configure complex nodes
  Dynamic resources: Read dynamic-nodes/<type>-guide.md. Both modes use registry.
  Connectors: Read connectors/connector-guide.md. Both modes use IS CLI for discovery.

Step 6 — Variables
  Edit .flow JSON directly (both modes — CLI has no variable commands).

Step 7 — Validate
  CLI: uip flow validate <file> --output json
  JSON: Run 17-item checklist (validation-guide.md). Optionally also CLI validate.

Step 8 — Debug (requires explicit user consent)
  Both modes: uip flow debug <project-dir>

Step 9 — Publish
  Both modes: uip solution bundle + uip solution upload (Studio Web default)
  Orchestrator path only on explicit request: uip flow pack
```

---

## 6. Planning Methodology (Preserved from maestro-flow)

The two-phase planning methodology is kept intact as a shared abstraction. It works identically regardless of implementation mode because planning operates at the topology level — it determines WHAT nodes to use and HOW they connect, not HOW to add them to the file.

### Phase 1: Discovery & Architecture

**Allowed**: `registry search`, `registry list`, `is connections list`
**Forbidden**: `registry get`

Produces: `<SolutionName>.arch.plan.md` with:
- Summary
- Mermaid flow diagram (validated against 12-step rules)
- Node table (with `<PLACEHOLDER>` for unresolved values)
- Edge table
- Global variables (in/out/inout)
- Connector summary (if applicable)
- Open questions ([REQUIRED] / [OPTIONAL])

**Gate**: Explicit user approval before Phase 2.

### Phase 2: Implementation Resolution

**Required**: `registry get` for ALL node types (including OOTB in CLI mode)

Produces: `<SolutionName>.impl.plan.md` with:
- All Phase 1 sections, updated
- Connection IDs resolved and verified
- Placeholders replaced with real values
- Mock nodes replaced if resources now published
- Changes from architectural plan documented

**Gate**: Explicit user approval before build.

### Mode-Specific Nuance in Phase 2

| Phase 2 step | CLI mode | JSON mode |
|--------------|----------|-----------|
| Validate node types | `registry get` mandatory | `registry get` for dynamic/connector only; OOTB validated against bundled reference files |
| Resolve connectors | Full 6-step connector workflow | Same discovery steps; JSON wiring at Step 6 |
| Resolve resources | `registry get` + extract definition | `registry get` + extract definition (same — registry needed either way) |

---

## 7. Deprecation Plan

Once `uipath-flow` is implemented and validated:

1. Add deprecation notice to `uipath-maestro-flow/SKILL.md` frontmatter:
   ```yaml
   description: "[DEPRECATED] Use uipath-flow instead. ..."
   ```

2. Add deprecation notice to `uipath-lattice-flow/SKILL.md` frontmatter:
   ```yaml
   description: "[DEPRECATED] Use uipath-flow instead. ..."
   ```

3. After confirmation period, delete both deprecated skills entirely.

---

## 8. Implementation Phases

### Phase A: Shared Abstraction Layer

Create the mode-neutral foundation:

1. `SKILL.md` — unified definition with mode selection
2. `references/flow-schema.md` — merge both schema docs
3. `references/variables-guide.md` — merge, deduplicate
4. `references/edge-wiring-guide.md` — merge port tables
5. `references/validation-guide.md` — checklist + CLI validate
6. `references/planning-guide.md` — preserve two-phase methodology
7. `references/bindings-guide.md` — merge both binding docs
8. `references/subflow-guide.md` — from lattice-flow
9. `references/project-setup-guide.md` — both paths
10. `references/publish-debug-guide.md` — from maestro-flow

### Phase B: Node Knowledge (Mode-Neutral)

Create unified node reference files:

11. `references/nodes/*.md` (19 files) — merge planning heuristics from maestro-flow plugins with definition blocks from lattice-flow node refs
12. `references/dynamic-nodes/*.md` (5 files) — merge resource node guides
13. `references/connectors/connector-guide.md` — merge connector plugin

### Phase C: Implementation Layer

Create mode-specific workflow guides:

14. `references/cli/commands-reference.md` — from maestro-flow
15. `references/cli/workflow-guide.md` — extract generic CLI patterns from impl.md files
16. `references/json/authoring-guide.md` — ID generation, JSON editing patterns
17. `references/json/workflow-guide.md` — extract generic JSON patterns from lattice-flow

### Phase D: Templates

18. Copy `assets/templates/*.json` (8 files) from lattice-flow

### Phase E: Validation & Deprecation

19. Run skill structure validation (`hooks/validate-skill-descriptions.sh`)
20. Verify all internal links resolve
21. Test both modes against a real .flow creation scenario
22. Deprecate both source skills

---

## 9. Validation via coder_eval Tasks

33 existing tasks at `/home/tmatup/root/coder_eval/tasks/uipath_flow/` cover both CLI and JSON authoring scenarios. They serve as the validation suite for the merged skill.

### Task Inventory by Mode Coverage

| Group | Tasks | Mode Tested | Skill Dependency | Changes Needed |
|-------|-------|-------------|-----------------|----------------|
| CLI exploration (registry, process, init/validate/pack, E2E) | 12 | CLI only | None — uses `allowed_tools: ["Skill", ...]` | None (picks up active plugin) |
| Complexity analysis (5/10/25/50/100 nodes) | 5 | CLI + JSON | None — uses `allowed_tools: ["Skill", ...]` | None |
| Older CLI tasks (dice_roller, add/remove terminate) | 3 | CLI + JSON | None — `uipath-flow-starter` template | None |
| Lattice-flow tasks (dice_roller, calculator, decision, loop, scheduled, add_decision, remove_node, rpa_node) | 8 | JSON authoring (rpa_node also CLI) | **Hardcoded path** to `uipath-lattice-flow` | Path update required |
| Reference flows (devconnect-email, hr-onboarding, sales-pipeline, weather-slack, output-filter-planning) | 5 | CLI + JSON | Plugin via `$UIPATH_PLUGIN_MARKETPLACE_DIR` | 1 stale `maestro-flow` mention |

### Required Path Changes (8 lattice_* tasks)

All 8 lattice tasks hardcode the skill path in `template_sources`:

```yaml
# Current
template_sources:
  - path: "../../../../skills/skills/uipath-lattice-flow"

# Updated
template_sources:
  - path: "../../../../skills/skills/uipath-flow"
```

Files to update:
- `lattice_dice_roller/dice_roller.yaml`
- `lattice_calculator/calculator.yaml`
- `lattice_decision_flow/decision_flow.yaml`
- `lattice_loop_flow/loop_flow.yaml`
- `lattice_scheduled_flow/scheduled_flow.yaml`
- `lattice_add_decision/add_decision.yaml`
- `lattice_remove_node/remove_node.yaml`
- `lattice_rpa_node/rpa_node.yaml`

Also update any `initial_prompt` text that says "uipath-lattice-flow" to "uipath-flow".

### Other Fixes

| File | Issue | Fix |
|------|-------|-----|
| `lattice_rpa_node/rpa_node.yaml` | Uses `uipcli` instead of `uip` in command patterns and prompt | Change to `uip` for consistency |
| `reference_flows/output-filter-planning/output_filter_planning.yaml` (line ~164) | LLM reviewer prompt references "maestro-flow template" | Update to "uipath-flow" |

### Validation Matrix

The merged skill must pass all existing tasks without regression. The matrix maps implementation phases to task groups:

| Phase | What It Validates | Tasks That Cover It |
|-------|------------------|---------------------|
| Phase A (shared abstraction) | Schema, variables, edges, validation | All lattice_* tasks (structural checks) |
| Phase B (node knowledge) | Definition blocks, ports, inputs | `lattice_dice_roller`, `lattice_calculator` (check_flow_structure.py scores) |
| Phase B (dynamic nodes) | Registry workflow, resource nodes | `lattice_rpa_node`, complexity 25/50/100 |
| Phase C (CLI implementation) | CLI commands, registry, debug | All 12 CLI exploration tasks, `dice_roller` (E2E debug) |
| Phase C (JSON implementation) | Direct JSON editing, ID generation | All 8 lattice_* tasks |
| Phase D (templates) | Template copy as starting point | `lattice_decision_flow`, `lattice_loop_flow`, `lattice_scheduled_flow` |
| Phase E (planning) | Two-phase methodology, plan docs | `output_filter_planning` |
| Full E2E | End-to-end flow creation + validation | `complexity_*`, `reference_flows/*` |

### Shared Test Infrastructure (No Changes Needed)

- `lattice_shared/check_flow_structure.py` — structural comparison scorer (Jaccard similarity on node types, edge counts, definitions, variables)
- `lattice_shared/references/*.flow` — ground-truth reference flows
- `lattice_add_decision/check_edit.py` — edit operation scorer
- `lattice_remove_node/check_edit.py` — remove operation scorer
- `dice_roller/check_dice_runs.py` — runtime execution validator

These scripts validate against `.flow` JSON structure, not skill names — they work unchanged with the merged skill.

---

## 10. Metrics

| Metric | maestro-flow | lattice-flow | uipath-flow (merged) |
|--------|-------------|-------------|---------------------|
| Total files | 46 | 40 | ~38 |
| Node doc files | 32 (16 types x 2) | 19 + 5 dynamic | 19 + 5 dynamic = 24 |
| Duplication | Moderate (planning.md repeats port info from impl.md) | Low | Minimal (each fact lives once) |
| Mode coverage | CLI only | JSON only | Both |
| Connector support | Full 6-step | Template only | Full 6-step, both modes |
| Planning methodology | Two-phase with gates | None (implicit) | Two-phase with gates |
| Templates | None | 8 | 8 |
| Self-contained | Yes | Yes | Yes |
