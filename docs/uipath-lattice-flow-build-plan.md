# Build Plan: `uipath-lattice-flow` Skill — Phase 1 (OOTB Nodes)

## Context

Building a new skill that teaches AI agents to read, create, edit, and validate `.flow` files as pure JSON — no CLI dependency for OOTB flows. Replaces `uipath-maestro-flow` long-term. Proposal: `docs/uipath-lattice-flow-proposal.md`.

## Key Discovery: 19 Node Types (Not 14)

The proposal anticipated 14-15 OOTB nodes. Exploration found **19**:

| # | nodeType | Source | Category |
|---|---|---|---|
| 1 | `core.trigger.manual` | registration.json | trigger |
| 2 | `core.trigger.scheduled` | sales-pipeline-hygiene definition | trigger |
| 3 | `core.action.script` | registration.json | data-operations |
| 4 | `core.action.http` | registration.json | data-operations |
| 5 | `core.action.transform` | release-notes-generator definition | data-operations |
| 6 | `core.action.transform.filter` | release-notes-generator definition | data-operations |
| 7 | `core.logic.decision` | registration.json | control-flow |
| 8 | `core.logic.switch` | registration.json | control-flow |
| 9 | `core.logic.loop` | registration.json | control-flow |
| 10 | `core.logic.foreach` | registration.json | control-flow |
| 11 | `core.logic.while` | registration.json | control-flow |
| 12 | `core.logic.merge` | registration.json | control-flow |
| 13 | `core.logic.delay` | hr-onboarding definition | control-flow |
| 14 | `core.logic.mock` | hr-onboarding definition | control-flow |
| 15 | `core.logic.terminate` | registration.json | control-flow |
| 16 | `core.control.end` | registration.json | control-flow |
| 17 | `uipath.human-in-the-loop` | registration.json | human-task |
| 18 | `core.mock.blank` | registration.json | mock |
| 19 | `core.mock.node` | registration.json | mock |

**Proposal type-name corrections:**
- `core.event.end` → `core.control.end`
- `core.event.terminate` → `core.logic.terminate`
- `core.action.hitl` → `uipath.human-in-the-loop`
- `core.action.blank` → `core.mock.blank`

## Design Decisions

1. **Definition blocks from reference flows** — Registration files are minimal; reference flow definitions are richer (constraints, icons, descriptions). Use reference flow definitions as canonical where available. Fall back to registration files otherwise.

2. **Template distillation** — Replace dynamic nodes with `core.logic.mock` placeholders to preserve wiring topology. Include `display.description` noting what the mock replaces.

3. **Three mock node types** — Document all three: `core.logic.mock` (recommended prototyping placeholder), `core.mock.node` (supports error handling), `core.mock.blank` (simplest pass-through).

4. **`variables.nodes` regeneration** — Document in both project-scaffolding-guide and validation-checklist.

## File Manifest (37 files)

### Batch 1: Foundation (5 files)

| File | Source |
|---|---|
| `SKILL.md` | Proposal draft + maestro-flow conventions |
| `references/flow-schema-guide.md` | Proposal entity inventory (lines 232-407) |
| `references/project-scaffolding-guide.md` | Proposal CLI analysis (lines 92-192) |
| `references/validation-checklist.md` | Proposal validation rules |
| `assets/templates/minimal-flow-template.json` | dice-roller/reference.flow verbatim |

### Batch 2: Node Reference Docs (19 files)

All in `references/nodes/`. Each follows: Type/Category/BPMN → Ports table → Inputs table → Outputs table → Definition Block (verbatim JSON) → Node Instance Example → Common Mistakes.

| File | Source |
|---|---|
| `trigger-manual.md` | manual-trigger.registration.json + dice-roller definition |
| `trigger-scheduled.md` | sales-pipeline-hygiene definition (line 3042) |
| `action-script.md` | script-task.registration.json + dice-roller definition |
| `action-http.md` | http-request.registration.json (498 lines — most complex) |
| `action-transform.md` | release-notes-generator definition |
| `action-transform-filter.md` | release-notes-generator definition |
| `logic-decision.md` | decision.registration.json |
| `logic-switch.md` | switch.registration.json |
| `logic-loop.md` | loop.registration.json |
| `logic-foreach.md` | foreach.registration.json |
| `logic-while.md` | while.registration.json |
| `logic-merge.md` | merge.registration.json |
| `logic-delay.md` | hr-onboarding definition |
| `logic-mock.md` | hr-onboarding definition (core.logic.mock) |
| `control-end.md` | end.registration.json |
| `control-terminate.md` | terminate.registration.json |
| `hitl.md` | hitl.registration.json |
| `mock-blank.md` | blank-node.registration.json |
| `mock-node.md` | mock-node.registration.json |

### Batch 3: Guides + Template (4 files)

| File | Source |
|---|---|
| `references/edge-wiring-guide.md` | Synthesized from all 19 node port tables |
| `references/variables-guide.md` | Proposal schema + maestro-flow variables-and-expressions.md |
| `references/subflow-guide.md` | Proposal SubflowEntry schema + reference flows |
| `assets/templates/project-scaffold-template.json` | calculator-multiply/reference.flow verbatim |

### Batch 4: Bindings + Remaining Templates (7 files)

| File | Source |
|---|---|
| `references/bindings-guide.md` | Minimal — empty for OOTB flows |
| `assets/templates/decision-flow-template.json` | devconnect-email → OOTB subset |
| `assets/templates/loop-flow-template.json` | sales-pipeline-cleanup → OOTB subset |
| `assets/templates/http-flow-template.json` | hr-onboarding → OOTB subset |
| `assets/templates/scheduled-trigger-template.json` | sales-pipeline-hygiene → OOTB subset |
| `assets/templates/connector-flow-template.json` | send-date-email → keep as-is |
| `assets/templates/multi-agent-template.json` | release-notes-generator → OOTB subset |

### Batch 5: Integration (2 edits)

| File | Change |
|---|---|
| `CODEOWNERS` | Add `/skills/uipath-lattice-flow/` entry |
| `README.md` | Add to skill catalog table |

## Execution Strategy

Use parallel sub-agents heavily:
- **Batch 1**: 2-3 agents writing foundation docs in parallel
- **Batch 2**: 3-4 agents each handling 5-6 node docs (read .registration.json → write markdown)
- **Batch 3-4**: 2-3 agents for guides and template extraction
- **Batch 5**: Direct edits in main context

Each agent gets:
- The node doc template (consistent structure)
- The source .registration.json or reference flow definition path + line numbers
- The correct nodeType from the inventory table

## Verification

After all files are created:
1. Validate SKILL.md frontmatter (name matches folder, description < 250 chars)
2. Validate all relative links in SKILL.md resolve to existing files
3. Validate both template JSON files parse correctly
4. Validate all node docs have the required sections
5. Run `hooks/validate-skill-descriptions.sh` if available
