# Scope Recommendation Guide

How `design` presents the product-selection outcome and maps it to SDD templates — read only by `design` (its § Read Plan names the sections). The selection logic itself: [product-selection-guide.md](../shared/product-selection-guide.md), [solution-composition-guide.md](solution-composition-guide.md).

## Template Mapping

### Single-product scope

Based on the Level 1 primary, select one template:

| Primary Product | Template |
|---|---|
| RPA Process, Library, Test Automation | `../assets/templates/rpa-sdd-template.md` |
| Maestro Flow | `../assets/templates/flow-sdd-template.md` |
| Maestro BPMN | `../assets/templates/bpmn-sdd-template.md` |
| Case Management | `../assets/templates/case-sdd-template.md` (task detail blocks: `../assets/templates/case-sdd-task-details-template.md`) |
| Agents | `../assets/templates/agent-sdd-template.md` |
| Coded Apps | `../assets/templates/coded-app-sdd-template.md` |
| API Workflows | `../assets/templates/api-workflow-sdd-template.md` |

> **Coded Functions are never a Level 1 primary and have no standalone template.** A Function's contract is the host template's `### Coded Functions` table (Flow / BPMN / Case / Agent templates carry it). In a Solution it is a project-list row with a build task routed to `uipath-functions`, but NO per-project SDD file. A request that is *only* a Function is a `decompose` single-skill deferral to `uipath-functions`.

### Solution scope (Level 1 = Solution or user picked Solution (customize))

A Solution produces **one SDD file per project in the Level 2.5 unified project list** plus a **solution overview SDD** that ties them together. Use the kebab-case project name from the unified list as the filename.

| Output file | Template | How many |
|---|---|---|
| `<SOLUTION_NAME_KEBAB>-solution-sdd.md` | Solution overview (see structure below) | Exactly 1 |
| `<PROJECT_NAME_KEBAB>-sdd.md` | Per-project — pick the template matching that project's product | One per project in the unified list |

For RPA projects in the Solution, use the RPA template once per RPA *group* — if the Level 2.5 Part A decomposition produced a Master Project (e.g., Dispatcher + Performer + Reporting), those sub-projects share one RPA SDD file (§10/§11 cover the sub-projects). If two RPA projects are unrelated (e.g., a Library not called by the Performer), they each get their own RPA SDD file.

**Component rows get no SDD file.** Project-list rows whose product is a component (Coded Function, IXP model, custom connector) do NOT get a per-project SDD file — their contract is the host SDD's table (`### Coded Functions`, `### IXP / Document Understanding Models`, connector rows) plus their row in the solution overview's Project Inventory. `plan` derives their build tasks from those rows, ordered before their consumers.

### Solution overview SDD structure

The solution overview SDD includes:

1. Solution Overview (objective, business context)
2. Planner Handoff — solution-level handoff header with `Project SDD role: root`, `Solution ID: <SOLUTION_NAME_KEBAB>`, `Solution root SDD: <its own filename>`, and the canonical `Tasks file: <SOLUTION_NAME_KEBAB>-tasks.md` (the ONE tasks file every child also names), plus cross-project ordering notes (integrated components built before their consumers) for `plan` to consume. Position 2 keeps the header inside the first ~50 lines § Choosing the Verb reads — do not move it lower. Do not include a task list here — `plan` owns task generation.
3. Project Inventory — the unified project list from Level 2.5 Part B
4. Cross-Project Data Flow — how projects call each other (Flow → RPA, Agent tool → API Workflow, RPA Performer → Library)
5. Shared Assets & Queues — assets, credentials, and queues referenced by more than one project
6. Per-Project SDD Index — filename + one-line scope per project

## Gap Handling for Agent / Coded App

When the primary product is Agents or Coded Apps and the PDD is missing required information ([product-selection-guide.md](../shared/product-selection-guide.md) § Signals per product):

1. Ask a structured question with the numbered-choice format:

> The PDD describes <PRODUCT>-specific capabilities, but requirements are missing for: <LIST_GAPS>.
>
> 1. **Proceed with <PRODUCT>** *(recommended)* — I will ask follow-up questions to fill the gaps
> 2. **Use a different product** — I will ask which product to use instead

2. If user chooses **option 1** → ask again with a batch of product-specific gap-filling structured questions (numbered, with defaults where possible) — keep a prompt to at most 4 questions, so split into two batched prompts when more than 4 gaps remain

3. If user chooses **option 2** → ask a structured question for the fallback:

> Which product should I use instead?
>
> 1. **RPA Process** — standard UI/data automation
> 2. **Maestro Flow** — orchestrate multiple automations
> 3. **Case Management** — staged lifecycle with SLA
> 4. **Stop** — do not generate an SDD

4. Re-run product selection with the fallback as primary

Do not auto-fallback. The user must choose explicitly.

## Presenting the Recommendation

The recommendation screen always puts the **recommended scope at the top** and offers **single-product alternatives plus "Solution (customize)"** below. The recommended scope is determined by Level 1:

- If Level 1 produced a single product → the recommendation is that single product (with its Level 1.5 sub-type if RPA).
- If Level 1 produced Solution (one or more Solution Signals matched) → the recommendation is the **pre-composed Solution**, with the pre-checked product list from Pass A of Level 1.75.

### Summary block

Emit this block as the Phase 1 summary content:

```markdown
## Recommended Scope
**Recommendation:** <SINGLE_PRODUCT | SOLUTION(<PRODUCT_1>, <PRODUCT_2>, ...)>
**Delivery model:** <cloud | automation-suite <version-if-known> | standalone | unspecified — assumed cloud [SME REVIEW]>
**Blocked by platform:** <PRODUCT → ALTERNATIVE_APPLIED (matrix | user exclusion), ... | none>
**Need profile:** <ONE_LINE_CORE_NEED_AND_TARGET_KPI — from design-guide.md Step 3.5>
**Reasoning:**
- <NEED_FACTOR — determinism / input structure / integration surface / coordination shape / volume / risk / trigger> → <PRODUCT>
- ...
**Alternatives considered:**
- <REJECTED_OPTION> — rejected because <REASON>
- ...

## Project List
<UNIFIED_PROJECT_LIST_FROM_LEVEL_2.5_PART_B — include Product, Sub-type, Role, Framework, Input/Output Queue columns>

## Queue Architecture (RPA Master Project rows only)
<QUEUE_TABLE_OR_N/A>
**Boundaries named:** <BOUNDARY_PER_SPLIT_PER_RPA_PROCESS_PROJECT_OR_N/A>
```

**Durable home.** This block is conversation output at the Phase 1 checkpoint, but the `## Recommended Scope` lines (`Recommendation:`, `Delivery model:`, `Blocked by platform:`) must also survive into the SDD — every template hosts a `## Recommended Scope` section between `## Decisions Made` and `## Action Required`, emitted in BOTH execution modes ([sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 3). Autonomous mode skips the checkpoint presentation, so the SDD copy is the only durable record of the Constraint Gate outcome.

### Confirmation question

Right after emitting the summary, confirm the scope via a structured question with the numbered-choice format. **The recommended option is always item 1.**

> I recommend the following scope for this SDD. Which should I use?
>
> 1. **<RECOMMENDED_SCOPE>** *(recommended)* — <ONE_LINE_REASON>
> 2. **<STRONGEST_SINGLE_PRODUCT_ALTERNATIVE>** — <ONE_LINE_REASON_OR_TRADEOFF>
> 3. **<SECOND_SINGLE_PRODUCT_ALTERNATIVE_OR_OMIT_IF_NONE>** — <ONE_LINE_REASON>
> 4. **Solution (customize)** — I will ask you to check every product the Solution should include

When the recommendation is already a Solution, still include **Solution (customize)** as an option so the user can adjust the composition. When the recommendation is a single product, **Solution (customize)** lets the user upgrade to a multi-project design.

### Customize branch

If the user picks **Solution (customize)**:

1. Run Level 1.75 Pass A (paired multi-select) — pre-check the recommended products from the default composition (or from the signals if the default was single-product).
2. Run Level 1.75 Pass B — resolve quantities per product.
3. Run Level 1.75 Pass C — sub-type per RPA project.
4. Run Level 2.5 to produce the unified project list.
5. Re-emit the summary block with the customized project list, then re-run the confirmation question. The customized composition replaces option 1 (still marked *recommended*) so the user can confirm or customize again (max 3 revisions — after that, proceed with the latest composition and tag disagreements as `[SME REVIEW]`).

### If the user disagrees with a single-product recommendation

Re-run Level 1 (and Level 1.5 if the chosen fallback is RPA) with the user's preference as the forced primary, then re-present.
