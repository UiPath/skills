---
name: uipath-solution-design
description: "[PREVIEW] PDD→SDD: analyze Process Design Documents (PDF/docx/md), select UiPath product (RPA/Flow/Case/Agents/Coded Apps/API Workflows), generate implementation-ready SDD. For project setup→uipath-platform."
---

# UiPath Solution Design

Transform a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) that a coding agent can build from. Select the right UiPath product (RPA Process/Library/Test Auto, Maestro Flow, Case Management, Agents, Coded Apps, or API Workflows) based on PDD signals.

## Critical Rules

1. **The SDD is implementation-oriented, not a PDD mirror.** Reorganize the PDD content into a structure a coding agent can execute against. Do not copy PDD sections verbatim.
2. **Never invent selectors, UI targets, or element identifiers.** The SDD covers architecture only — selectors require application inspection at development time.
3. **Follow the phased interaction model.** Read the full PDD first, recommend a product, present a summary with clarifying questions, get architecture approval, then generate the complete SDD. See [SDD Generation Guide](references/sdd-generation-guide.md).
4. **Fill gaps with `[DEFAULT]` or `[SME REVIEW]`.** Use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts). Use `[SME REVIEW]` for gaps requiring business knowledge. Never silently invent business rules.
5. **The Project Structure section is the most important section.** It must list every workflow file (or node / stage / tool / page / step) with its responsibility, inputs, outputs, and which PDD steps it covers.
6. **Express data definitions as C# records when the primary is RPA in Coded or Hybrid mode.** Use records for immutable data, classes for mutable. No inheritance. Max 15 properties per type. Default to `string` unless the PDD specifies numeric, date, or boolean operations. For XAML mode, use dictionary keys or DataTable columns. For Agents/Coded Apps/Flow/Case/API Workflows, use the JSON schema or type definition appropriate to that product.
7. **Always generate the Implementation Plan.** Write it as the final SDD section AND create live tasks via TaskCreate with dependencies. Do not ask the user — generate it automatically. If TaskCreate is unavailable or fails, the plan section in the SDD file is sufficient — do not block SDD completion.
8. **Select the primary product BEFORE designing architecture.** The product determines the template and the project structure. Use the [Product Selection Guide](references/product-selection-guide.md) to recommend a primary product + integrated components based on PDD signals. The skill that builds the workflows/nodes/tasks owns the final detailed decisions.
9. **Write the SDD to the current working directory** with filename `<PROCESS_NAME_KEBAB_CASE>-sdd.md`. If the user specifies a path, use that instead.
10. **If the user's intent implies implementation, execute the plan after SDD approval.** When the user asks to "create", "build", "implement", "set up", or "make" a project from a PDD, proceed to work through the implementation tasks in dependency order — the agent will activate the appropriate skills for each task. When the user asks to "design", "architect", or "generate an SDD", stop after writing the SDD.
11. **Use AskUserQuestion for Agent/Coded App gaps.** If the primary product is Agents or Coded Apps and the PDD lacks required details (framework, tools, pages, flows), use `AskUserQuestion` to ask if the user wants to proceed with gap-filling or use a different product. Never auto-fallback.

## Workflow

The SDD generation follows 3 phases. Only interrupt the user when genuinely necessary. See [SDD Generation Guide](references/sdd-generation-guide.md) for detailed steps.

1. **Phase 1 — PDD Analysis & Product Selection.** Read the full PDD, extract structured information, run product selection, present a summary with the recommended product (primary + integrated) and detected gaps. For Agent/Coded App products with missing info, use `AskUserQuestion` for gap-filling or fallback.
2. **Phase 2 — Architecture Review.** Load the product-specific template. Generate the architectural core for that product (project structure, workflow/node/stage/tool inventory, data models). Present to the user for review. Incorporate feedback before proceeding.
3. **Phase 3 — Full SDD Generation.** Generate all remaining sections, write the SDD to disk, and create the implementation plan. If the user's intent implies implementation (see Critical Rule 10), proceed to execute the tasks in dependency order.

## Reference Navigation

| File | Purpose |
|------|---------|
| [SDD Generation Guide](references/sdd-generation-guide.md) | Detailed instructions for each phase of SDD generation |
| [PDD Analysis Guide](references/pdd-analysis-guide.md) | How to extract structured data from PDDs in any format |
| [Product Selection Guide](references/product-selection-guide.md) | Decision tree for selecting primary product + integrated components |
| [RPA Template](assets/templates/rpa-sdd-template.md) | SDD template for RPA Process / Library / Test Automation |
| [Flow Template](assets/templates/flow-sdd-template.md) | SDD template for Maestro Flow |
| [Case Management Template](assets/templates/case-sdd-template.md) | SDD template for Case Management |
| [Agent Template](assets/templates/agent-sdd-template.md) | SDD template for UiPath Agents |
| [Coded App Template](assets/templates/coded-app-sdd-template.md) | SDD template for Coded Apps (web) |
| [API Workflow Template](assets/templates/api-workflow-sdd-template.md) | SDD template for API Workflows |

## Anti-patterns

1. **Copying the PDD structure into the SDD.** The SDD must reorganize content for implementation, not mirror the PDD's document flow.
2. **Defaulting to RPA Process when the PDD describes something else.** Use the Product Selection Guide's decision tree. A PDD with AI reasoning signals should go to Agents; a PDD with stages/SLA/approval should go to Case Management; etc.
3. **Inventing selectors from screenshots.** Screenshots help understand the UI flow but cannot produce reliable selectors. Leave selector work for development time.
4. **Generating the full SDD without user checkpoint.** Always present the product recommendation (end of Phase 1) AND the architecture (Phase 2) before generating the rest. The product choice and project structure are the hardest to fix later.
5. **Asking the user about every gap.** Use `[DEFAULT]` for standard patterns. Only escalate with `[SME REVIEW]` for business-knowledge gaps. Use `AskUserQuestion` only for Agent/Coded App gap-filling.
6. **Skipping the Implementation Plan.** The task breakdown is a required output, not optional. It bridges the SDD to actual development work.
7. **Making the final implementation decision.** The SDD recommends product, mode, and structure; the specialized skills decide the details. Keep recommendations lightweight with brief justifications.
8. **Generating overly abstract workflow/node/task descriptions.** Each item in the inventory must have a concrete responsibility, specific PDD step references, and defined inputs/outputs.
9. **Auto-falling-back from Agents/Coded Apps to another product without asking.** If the PDD is missing product-specific details, use `AskUserQuestion` — the user chooses whether to proceed with gap-filling or pick a different product.
10. **Inlining HITL schema for Flow/Maestro/Agent products.** HITL for those products is owned by the `uipath-human-in-the-loop` skill. Flag touchpoints only. Case Management is the exception — it handles HITL tasks inline.

## Future Work

<!-- TODO: Add SDD diffing capability for multi-phase processes.
     When a process has phases (e.g., Phase 1 classic RPA, Phase 2
     semantic selectors), the skill should be able to generate a
     diff-SDD that only describes what changes between phases,
     referencing the base SDD for unchanged sections. -->

<!-- TODO: When the dedicated API Workflow skill is built, the
     api-workflow-sdd-template.md may need updates to match that
     skill's expected inputs. -->
