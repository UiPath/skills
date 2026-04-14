---
name: uipath-solution-design
description: "[PREVIEW] PDD→SDD: analyze Process Design Documents (PDF/docx/md), generate implementation-ready Solution Design Documents. Project structure, workflows, data models, testing. For project setup→uipath-platform, for workflows→uipath-rpa."
---

# UiPath Solution Design

Transform a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) that a coding agent can build from.

## Critical Rules

1. **The SDD is implementation-oriented, not a PDD mirror.** Reorganize the PDD content into a structure a coding agent can execute against. Do not copy PDD sections verbatim.
2. **Never invent selectors, UI targets, or element identifiers.** The SDD covers architecture only — selectors require application inspection at development time.
3. **Follow the 3-phase interaction model.** Read the full PDD first, present a summary with clarifying questions, get architecture approval, then generate the complete SDD. See [SDD Generation Guide](references/sdd-generation-guide.md).
4. **Fill gaps with `[DEFAULT]` or `[SME REVIEW]`.** Use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts). Use `[SME REVIEW]` for gaps requiring business knowledge. Never silently invent business rules.
5. **The Project Structure section is the most important section.** It must list every workflow file with its responsibility, inputs, outputs, and which PDD steps it covers.
6. **Express data definitions as C# types when recommending Coded or Hybrid mode.** Use classes, structs, and enums. For pure XAML, use dictionary keys or DataTable column definitions.
7. **Always generate the Implementation Plan.** Write it as the final SDD section AND create live tasks via TaskCreate with dependencies. Do not ask the user — generate it automatically.
8. **Implementation mode recommendation is lightweight.** Provide a brief justification based on process characteristics. The `uipath-rpa` skill owns the final decision. See [Implementation Mode Guide](references/implementation-mode-guide.md).
9. **Write the SDD to the current working directory** with filename `<process-name-kebab-case>-sdd.md`. If the user specifies a path, use that instead.
10. **If the user's intent implies implementation, execute the plan after SDD approval.** When the user asks to "create", "build", or "implement" a project from a PDD, proceed to work through the implementation tasks: use `uipath-platform` to create the project, then `uipath-rpa` to build the workflows. When the user asks to "design", "architect", or "generate an SDD", stop after writing the SDD.

## Workflow

The SDD generation follows 3 phases. Only interrupt the user when genuinely necessary.

### Phase 1 — PDD Analysis

1. Read the full PDD. For large PDFs, read in chunks (max 20 pages per request).
2. Extract structured information following the [PDD Analysis Guide](references/pdd-analysis-guide.md).
3. Present a summary to the user:
   - Process name and objective
   - Number of applications involved (with roles)
   - Number of process steps identified
   - Key business rules found
   - Gaps or ambiguities detected
4. Ask clarifying questions ONLY for genuine ambiguities that affect architecture decisions. Do not ask about details that can be filled with `[DEFAULT]` or resolved during implementation.

### Phase 2 — Architecture Review

1. Generate the architectural core of the SDD:
   - Implementation mode recommendation (XAML / Coded / Hybrid) with justification
   - Project structure with full workflow inventory table
   - Data model definitions (C# types or dictionary keys)
   - Application inventory with roles and scope boundaries
2. Present this to the user for review.
3. Incorporate feedback before proceeding.

### Phase 3 — Full SDD Generation

1. Generate all remaining sections using the [SDD Template](assets/templates/sdd-template.md).
2. Write the complete SDD to disk.
3. Generate the Implementation Plan:
   - Write it as the final section of the SDD (persistent)
   - Create live tasks via TaskCreate with proper dependencies (actionable)

### Phase 4 — Execution (when user intent implies implementation)

If the user's request implies building the solution (e.g., "create a project from this PDD"), proceed to execute the implementation plan:

1. Use `uipath-platform` for project scaffolding (task 1)
2. Use `uipath-rpa` for workflow implementation (remaining tasks)
3. Work through tasks in dependency order, marking each complete as you go

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
6. **Making the final implementation mode decision.** The SDD recommends; `uipath-rpa` decides. Keep the recommendation lightweight with a brief justification.
7. **Generating overly abstract workflow descriptions.** Each workflow in the inventory must have a concrete responsibility, specific PDD step references, and defined inputs/outputs.
