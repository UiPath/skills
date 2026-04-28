---
name: uipath-solution-design
description: "[PREVIEW] PDD→SDD: analyze PDDs (PDF/docx/md), pick scope (single product or multi-project Solution: RPA/Flow/Case/Agents/Apps/API Workflows), generate implementation-ready SDD. For project setup→uipath-platform."
---

# UiPath Solution Design

Transform a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) that a coding agent can build from. Select the right UiPath scope — either a single product (RPA Process/Library/Test Auto, Maestro Flow, Case Management, Agents, Coded Apps, or API Workflows) or a multi-project Solution composing several of them — based on PDD signals.

## Critical Rules

1. **The SDD is implementation-oriented, not a PDD mirror.** Reorganize the PDD content into a structure a coding agent can execute against. Do not copy PDD sections verbatim.
2. **Never invent selectors, UI targets, or element identifiers.** The SDD covers architecture only — selectors require application inspection at development time.
3. **Follow the phased interaction model.** Read the full PDD first, recommend a product, present a summary with clarifying questions, get architecture approval, then generate the complete SDD. See [SDD Generation Guide](references/sdd-generation-guide.md).
4. **Fill gaps with `[DEFAULT]` or `[SME REVIEW]`.** Use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts). Use `[SME REVIEW]` for gaps requiring business knowledge. Never silently invent business rules.
5. **The Project Structure section is the most important section.** It must list every workflow file (or node / stage / tool / page / step) with its responsibility, inputs, outputs, and which PDD steps it covers. Run Level 2.5 (Project Decomposition) from the Product Selection Guide BEFORE designing project structure — it produces the unified project list that drives structure for every scope, including Solutions (multi-product) and RPA Master Projects (queue-connected sub-projects using REFramework).
6. **RPA data definitions follow the implementation mode.** For Coded C# or Hybrid mode: use C# `record` (immutable) or `class` (mutable). No inheritance. Max 15 properties per type. Default to `string` unless the PDD specifies numeric, date, or boolean operations. For XAML mode: use dictionary keys or DataTable columns.
7. **Non-RPA products use their native type system.** For Agents, Coded Apps, Flow, Case Management, and API Workflows: use the JSON schema or type definition appropriate to that product's template.
8. **Always generate the Implementation Plan.** Write it as the final SDD section AND create live tasks via TaskCreate with dependencies. Do not ask the user — generate it automatically. If TaskCreate is unavailable or fails, the plan section in the SDD file is sufficient — do not block SDD completion.
9. **Select the primary scope BEFORE designing architecture.** The scope (single product or Solution) determines the template(s) and project structure. Use the [Product Selection Guide](references/product-selection-guide.md) Level 1 → Level 1.5 (RPA sub-type) → Level 1.75 (Solution composition) → Level 2.5 (project decomposition). Present the recommended scope first with single-product alternatives and "Solution (customize)" below. The skill that builds the workflows/nodes/tasks owns the final detailed decisions.
10. **Write the SDD to the current working directory.** For single-product scope, one file at `<PROCESS_NAME_KEBAB_CASE>-sdd.md`. For Solution scope, a `<SOLUTION_NAME_KEBAB>-solution-sdd.md` overview plus one `<PROJECT_NAME_KEBAB>-sdd.md` per project in the unified project list. If the user specifies a path, use that instead.
11. **If the user's intent implies implementation, execute the plan after SDD approval.** When the user asks to "create", "build", "implement", "set up", "make", "prepare", or "scaffold" a project from a PDD, proceed to work through the implementation tasks in dependency order — the agent will activate the appropriate skills for each task. When the user asks to "design", "architect", or "generate an SDD", stop after writing the SDD. If intent is ambiguous, use `AskUserQuestion` to clarify.
12. **Use AskUserQuestion for Agent/Coded App gaps.** If the primary product is Agents or Coded Apps and the PDD lacks required details (framework, tools, pages, flows), use `AskUserQuestion` to ask if the user wants to proceed with gap-filling or use a different product. Never auto-fallback.
13. **All user questions use numbered-choice format by default; use `multiSelect: true` only for Solution composition.** Every `AskUserQuestion` uses a blockquote with numbered options and a `*(recommended)*` tag on the default choice. This applies to execution mode, language, product gap-filling, fallback selection, SME review resolution, RPA sub-type, and scope confirmation. The **one exception** is Level 1.75 Pass A (Solution composition), which uses paired `multiSelect: true` questions (4 options each, two questions in one call) to let the user check every product the Solution should include.

## Workflow

The SDD generation follows 3 phases. Before starting, ask the user for their preferred execution mode (Autonomous or Interactive). See [SDD Generation Guide](references/sdd-generation-guide.md) for detailed steps. All user questions use numbered-choice format.

1. **Phase 1 — PDD Analysis & Scope Selection.** Ask execution mode. Read the full PDD, extract structured information, run Level 1 (primary scope) → Level 1.5 (RPA sub-type if applicable) → Level 1.75 (Solution composition if applicable) → Level 2.5 (project decomposition). In Interactive mode, present a summary with the recommended scope (single product or Solution) at the top and single-product alternatives + "Solution (customize)" below. In Autonomous mode, proceed without pausing. For Agent/Coded App products with missing info, use `AskUserQuestion` for gap-filling or fallback (both modes).
2. **Phase 2 — Architecture Review.** Load the product-specific template. Generate the architectural core. In Interactive mode, present for review. In Autonomous mode, proceed without pausing.
3. **Phase 3 — Full SDD Generation.** Generate all remaining sections. Resolve `[SME REVIEW]` items by asking the user before writing (both modes). Write the SDD to disk and create the implementation plan. If the user's intent implies implementation (see Critical Rule 11), proceed to execute the tasks in dependency order.

## Reference Navigation

| File | Purpose |
|------|---------|
| [SDD Generation Guide](references/sdd-generation-guide.md) | Detailed instructions for each phase of SDD generation |
| [PDD Analysis Guide](references/pdd-analysis-guide.md) | How to extract structured data from PDDs in any format |
| [Product Selection Guide](references/product-selection-guide.md) | Level 1 scope selection (single product vs Solution), Solution composition (Level 1.75), cross-product project-list merge (Level 2.5 Part B), capability add-ons, template mapping |
| [RPA Product Guide](references/rpa-product-guide.md) | RPA-only: sub-type signals, Level 1.5 sub-type confirmation, Level 2 authoring mode, Level 2.5 Part A decomposition patterns, REFramework guidance. Load when Level 1 = RPA or a Solution includes RPA. |
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
11. **Putting everything in a single RPA project when the PDD has distinct processing stages.** If the PDD describes email ingestion + data extraction + output generation + reporting, these are separate projects connected by Orchestrator queues — not one monolithic process. Run Level 2.5 (Project Decomposition) from the Product Selection Guide to decide. A single project is only appropriate for simple linear processes with no independent failure/retry per stage.
11.5. **Forcing a single-product scope when the PDD describes multiple coordinated projects.** If the PDD needs (for example) 2 RPA Libraries + 1 Test Automation project, or a Flow plus callable API Workflows, the correct scope is **Solution** — not a single-product SDD that buries the rest as "integrated components". Watch the Level 1 Solution Signals and offer Solution (customize) as an alternative on the recommendation screen so the user can check every product the design needs.
12. **Ignoring REFramework for queue-based transactional processing.** REFramework is the standard UiPath framework for Performer projects that consume from Orchestrator queues. It provides built-in transaction retry, state management, and exception routing. Using a custom framework for this pattern leads to fragile, non-standard implementations.
13. **Omitting NuGet package dependencies.** Developers need to know which packages to install. Infer packages from the Application Inventory (DU → IntelligentOCR, email → Mail.Activities or MicrosoftOffice365.Activities, etc.) and list them in §14 Packages.

