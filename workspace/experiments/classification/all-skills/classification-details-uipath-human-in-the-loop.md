# Classification Details — uipath-human-in-the-loop

**Classification: Partial**

---

## What the Skill Teaches

Design and wire HITL nodes (QuickForm, new Coded Action App, existing deployed app) across Flow, Low-Code Agent, and Maestro surfaces — from schema design through node insertion, edge wiring, and validation.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Business pattern recognition (proactive HITL recommendation) | No | Requires judgment about whether a process needs a human checkpoint and which pattern applies |
| 2 | Surface detection (Flow / Low-Code Agent / Maestro) | Marginal | Three `find` commands with a lookup table; trivial to script but very low value as standalone |
| 3 | Task type selection (QuickForm / New Coded App / Existing Deployed App) | No | Context-dependent judgment; skill explicitly says "do not choose on their behalf" |
| 4 | Schema design — field direction, types, labels, inOut semantics | No | Requires understanding upstream data, downstream needs, and field semantics for the specific business process |
| 5 | Writing node JSON and edge wiring | No | Requires knowing upstream node IDs, correct handle names, and output variable paths |
| **6** | **`variables.nodes` regeneration after insertion** | **Yes — BUILD-MODEL/MATRIX** | Rule 4 mandates full-array replacement; the algorithm is in a reference doc and takes node list as input |
| **7** | **Post-change validation with `uip maestro flow validate`** | **Yes — VALIDATE/CHECK** | Rule 5: run validate after every write; pass/fail is deterministic |
| 8 | Fallback routing on blockers (app not found, no dist/, expired auth) | No | Judgment on which alternative to propose based on user context |
| 9 | Post-wiring report to user | No | Judgment on summarizing schema, edges, runtime variable paths for this specific flow |

---

## Codifiable Procedures (not yet scripted)

### 1. `variables.nodes` Regeneration — BUILD-MODEL/MATRIX

**Source:** `skills/uipath-human-in-the-loop/SKILL.md` §Critical Rules

**What it does:** After inserting a HITL node into `workflow.nodes`, the entire `workflow.variables.nodes` array must be rebuilt from scratch using the node list as input — partial appending is forbidden. The construction algorithm is deterministic given the current set of nodes and is documented in a reference. Line 38: "Regenerate `variables.nodes` after adding the node. Replace the entire `workflow.variables.nodes` array — do not append. See the reference docs for the algorithm."

**Why it's mechanical:** Given the node list from the `.flow` file, the algorithm produces a fixed output structure with no judgment; the replacement rule (full overwrite, never append) is an explicit invariant.

**Turn savings:** Currently the agent reads the reference, applies the algorithm manually across 1–2 turns, and edits the array; a script accepting the `.flow` path collapses this to one call.

---

### 2. Post-Change Validation — VALIDATE/CHECK

**Source:** `skills/uipath-human-in-the-loop/SKILL.md` §Critical Rules

**What it does:** After every node write or edge change, the skill requires running `uip maestro flow validate <file> --output json` and confirming no error-severity findings remain before reporting completion. If validation fails, the agent must diagnose from the JSON and fix before reporting. Line 39: "Validate after every change. Run `uip maestro flow validate <file> --output json` after writing the node and edges."

**Why it's mechanical:** The command is fixed; success is exit 0 with no error-severity findings; the pass/fail check requires no judgment.

**Turn savings:** Without a script the agent runs the command and parses JSON output in 1–2 turns; a validation wrapper returning structured pass/fail collapses to a single call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The dominant work — business pattern recognition, task type selection, schema field design, node JSON authoring, and edge wiring — all require understanding the user's specific business process, upstream node outputs, and downstream data needs. These judgment-heavy areas account for more than half of what the skill teaches.

**Why not None:** Rules 4 and 5 describe explicit deterministic procedures: full-array replacement for `variables.nodes` (BUILD-MODEL/MATRIX) and a fixed post-change validate command (VALIDATE/CHECK). Both are independent of the process being designed.

**Evidence locations:**
- `variables.nodes` full-replacement rule: `skills/uipath-human-in-the-loop/SKILL.md` §Critical Rules (line 38)
- Mandatory post-change validation: `skills/uipath-human-in-the-loop/SKILL.md` §Critical Rules (line 39)
- Judgment-dominant schema design: `skills/uipath-human-in-the-loop/SKILL.md` §Step 4b — Schema Design Rules
