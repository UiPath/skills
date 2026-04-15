---
name: uipath-solution-design
description: "[PREVIEW] PDD→SDD: analyze Process Design Documents (PDF/docx/md), generate implementation-ready Solution Design Documents. Project structure, workflows, data models, testing. For project setup→uipath-platform, for workflows→uipath-rpa."
---

# UiPath Solution Design

Transform a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) that a coding agent can build from.

## Critical Rules

1. **The SDD is implementation-oriented, not a PDD mirror.** Reorganize the PDD content into a structure a coding agent can execute against. Do not copy PDD sections verbatim.
2. **Never invent selectors, UI targets, or element identifiers.** The SDD covers architecture only — selectors require application inspection at development time.
3. **Follow the phased interaction model.** Read the full PDD first, present a summary with clarifying questions, get architecture approval, then generate the complete SDD. See [SDD Generation Guide](references/sdd-generation-guide.md).
4. **Fill gaps with `[DEFAULT]` or `[SME REVIEW]`.** Use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts). Use `[SME REVIEW]` for gaps requiring business knowledge. Never silently invent business rules.
5. **The Project Structure section is the most important section.** It must list every workflow file with its responsibility, inputs, outputs, and which PDD steps it covers.
6. **Express data definitions as C# types when recommending Coded or Hybrid mode.** Use records for immutable data, classes for mutable. No inheritance. Max 15 properties per type — split into sub-types if larger. Default to `string` unless the PDD explicitly specifies numeric, date, or boolean operations. For pure XAML, use dictionary keys or DataTable column definitions.
7. **Always generate the Implementation Plan.** Write it as the final SDD section AND create live tasks via TaskCreate with dependencies. Do not ask the user — generate it automatically. If TaskCreate is unavailable or fails, the plan section in the SDD file is sufficient — do not block SDD completion.
8. **Implementation mode recommendation is lightweight.** Provide a brief justification based on process characteristics. The skill that builds the workflows owns the final decision. See [Implementation Mode Guide](references/implementation-mode-guide.md).
9. **Write the SDD to the current working directory** with filename `<PROCESS_NAME_KEBAB_CASE>-sdd.md`. If the user specifies a path, use that instead.
10. **If the user's intent implies implementation, execute the plan after SDD approval.** When the user asks to "create", "build", "implement", "set up", or "make" a project from a PDD, proceed to work through the implementation tasks in dependency order — the agent will activate the appropriate skills for each task. When the user asks to "design", "architect", or "generate an SDD", stop after writing the SDD.

## Workflow

The SDD generation follows 3 phases. Only interrupt the user when genuinely necessary. See [SDD Generation Guide](references/sdd-generation-guide.md) for detailed steps.

1. **Phase 1 — PDD Analysis.** Read the full PDD, extract structured information per the [PDD Analysis Guide](references/pdd-analysis-guide.md), present a summary with detected gaps. Ask clarifying questions only when the ambiguity would change the project structure, data model, or workflow inventory.
2. **Phase 2 — Architecture Review.** Generate the architectural core (implementation mode, project structure, workflow inventory, data models). Present to the user for review. Incorporate feedback before proceeding.
3. **Phase 3 — Full SDD Generation.** Generate all remaining sections using the [SDD Template](assets/templates/sdd-template.md), write the SDD to disk, and create the implementation plan (both as an SDD section and as live tasks via TaskCreate). If the user's intent implies implementation (see Critical Rule 10), proceed to execute the tasks in dependency order.

## Reference Navigation

| File | Purpose |
|------|---------|
| [SDD Generation Guide](references/sdd-generation-guide.md) | Detailed instructions for each phase of SDD generation |
| [PDD Analysis Guide](references/pdd-analysis-guide.md) | How to extract structured data from PDDs in any format |
| [Implementation Mode Guide](references/implementation-mode-guide.md) | Lightweight XAML vs Coded vs Hybrid decision guidelines |
| [SDD Template](assets/templates/sdd-template.md) | Canonical SDD markdown template with all sections |

## Anti-patterns

1. **Copying the PDD structure into the SDD.** The SDD must reorganize content for implementation, not mirror the PDD's document flow.
2. **Inventing selectors from screenshots.** Screenshots help understand the UI flow but cannot produce reliable selectors. Leave selector work for development time.
3. **Generating the full SDD without user checkpoint.** Always present the architecture (Phase 2) before generating the rest. The project structure and data models are the hardest to fix later.
4. **Asking the user about every gap.** Use `[DEFAULT]` for standard patterns. Only escalate with `[SME REVIEW]` for business-knowledge gaps.
5. **Skipping the Implementation Plan.** The task breakdown is a required output, not optional. It bridges the SDD to actual development work.
6. **Making the final implementation mode decision.** The SDD recommends; the skill that builds the workflows decides. Keep the recommendation lightweight with a brief justification.
7. **Generating overly abstract workflow descriptions.** Each workflow in the inventory must have a concrete responsibility, specific PDD step references, and defined inputs/outputs.
