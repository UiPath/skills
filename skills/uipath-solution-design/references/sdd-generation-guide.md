# SDD Generation Guide

Step-by-step instructions for transforming a PDD into an SDD. Follow the 3-phase interaction model described in SKILL.md.

## Phase 1 — PDD Analysis & Scope Selection

### Step 0: Determine Execution Mode

Before reading the PDD, ask the user how they want the interaction to work. Use `AskUserQuestion` with the numbered-choice format:

> How should I handle this SDD generation?
>
> 1. **Autonomous** *(recommended)* — I will read the PDD, make all decisions, and generate the full SDD. I will only interrupt for hard blockers (PDD unreadable, Agent/Coded App missing critical info, unresolved `[SME REVIEW]` items before finalizing).
> 2. **Interactive** — I will pause at each phase checkpoint (summary, architecture, final SDD) for your review before proceeding.

Remember the execution mode for the rest of this session — reference it before each checkpoint to decide whether to pause or proceed. In **Autonomous** mode:
- Skip Phase 1 summary presentation (generate internally, do not wait for confirmation)
- Skip Phase 2 architecture review (generate, do not wait)
- Still ask the SME Review resolution question before writing (Step 1.5) — this is a hard blocker
- Still ask the Agent/Coded App gap-filling question if triggered — this is a hard blocker

In **Interactive** mode:
- Present and wait at every checkpoint as described in the steps below

### Step 0.5: Create Progress Tasks

After getting the execution mode, create progress-tracking tasks via `TaskCreate`. These give the user a real-time checklist of where the SDD generation stands.

```
TaskCreate: subject="Read PDD and extract data",        activeForm="Reading PDD…"
TaskCreate: subject="Select product",                    activeForm="Selecting product…"
TaskCreate: subject="Generate architecture (Phase 2)",   activeForm="Generating architecture…"
TaskCreate: subject="Generate full SDD (Phase 3)",       activeForm="Generating SDD sections…"
TaskCreate: subject="Resolve SME review items",          activeForm="Resolving SME review items…"
TaskCreate: subject="Write SDD to disk",                 activeForm="Writing SDD…"
TaskCreate: subject="Create implementation tasks",       activeForm="Creating implementation tasks…"
```

Mark each task `in_progress` when starting and `completed` when done.

**Rule G-8 — Task creation is best-effort and never blocks SDD output.** If any `TaskCreate` or `TaskUpdate` call fails at any point (tool unavailable, runtime error, timeout), log a single warning to the user, continue the SDD generation without progress tasks, and do not retry. The SDD file itself — and, in Phase 3, the Implementation Plan section inside it — is the authoritative deliverable. Progress tasks are a UX convenience only. This rule applies to both the progress tasks created here and the implementation tasks created in Phase 3 Step 3.

These are **separate from** the Implementation Plan tasks created in Phase 3 Step 3. These track the SDD generation process itself; those track the downstream implementation work.

### Step 1: Read the PDD

> **Progress:** Mark "Read PDD and extract data" as `in_progress`.

1. Determine the input format (PDF, docx, markdown, pasted text).
2. **Size-based reading strategy** for PDFs:
   - **Under 10 pages:** read the entire document in one pass. Skip ToC lookup.
   - **10-50 pages:** read the ToC first, then read sections in priority order (overview → steps → exceptions → applications → credentials).
   - **Over 50 pages:** read ToC, then read high-priority sections (overview, process steps, exceptions) first, extract as you go, then read remaining sections.
3. For pasted text over 3000 words, ask the user to paste in sections.
4. **Docx handling:** if the .docx file renders as raw XML or binary content, tell the user: "The Word document could not be parsed as readable text. Please export it as PDF or paste the content directly." Do not attempt to extract data from garbled output.
5. **Error cases:** if the document cannot be read (corrupt PDF, password-protected, unsupported format), tell the user and ask them to provide it in a different format. If the document does not appear to be a PDD (no process steps, no application details, no exception handling), tell the user and stop.
6. **Language handling:** if the PDD is not in English, use `AskUserQuestion` with the numbered-choice format:

   > The PDD appears to be in <LANGUAGE>. Which language should the SDD use?
   >
   > 1. **English** *(recommended)* — SDD in English for broadest tool compatibility
   > 2. **<LANGUAGE>** — SDD in the same language as the PDD

   Regardless of choice, keep section headings and structural identifiers (BR-01, B1, E1) in English for tool compatibility.

### Step 2: Extract Structured Information

Follow the [PDD Analysis Guide](pdd-analysis-guide.md) to extract data from the PDD. Build an internal model with these components:

| Component | PDD Topic to Look For | Required |
|---|---|---|
| Process name and objective | Introduction | Yes |
| Key contacts | Process key contacts | No |
| Process overview (schedule, volumes, FTEs) | Process overview | Yes |
| In-scope activities | In scope | Yes |
| Out-of-scope activities | Out of scope | Yes |
| Process steps | Detailed process map / steps | Yes |
| Business exceptions | Exceptions handling | Yes |
| System errors | Error mapping and handling | Yes |
| Application inventory | In-scope application details | Yes |
| Development prerequisites | Prerequisites for development | No |
| Credentials and assets | Credentials and asset management | Yes |
| Test data | Appendix | No |

**Key Contacts go into §1 Delivery Team.** The PDD's Key Contacts section (SA, BA, developers, PM, SME / Process Owner) populates the Delivery Team table in §1 of the RPA template. Include only roles the PDD explicitly names — do not invent or leave rows as `[SME REVIEW]`; omit silent rows instead.

### Step 2.5: Org Context Check

One piece of context cannot be inferred from any PDD — whether the organization maintains shared RPA libraries that every new project must reference (e.g., `CommonLibrary`, `<Company>.Activities`). Ask this question in BOTH Autonomous and Interactive modes — it is a hard blocker for correct §14 Packages content.

Use `AskUserQuestion` with the numbered-choice format:

> Does your organization maintain shared RPA libraries (e.g., `CommonLibrary`) that every new project must reference in its §14 Packages?
>
> 1. **No / none that apply here** *(recommended)* — I will not list any shared library in §14
> 2. **Yes — CommonLibrary** — I will include `CommonLibrary` in each sub-project's §14 Packages
> 3. **Yes — other** — you will name the libraries; I will include them in each sub-project's §14

Record the answer and propagate in Phase 2:
- Add the library names to each sub-project's §14 Packages table (one row per shared library, per sub-project).
- Add the same list to §16 Deployment Environment → "Shared libraries referenced".

Skip this step for non-RPA primaries (Agents, Coded Apps, Flow, Case, API Workflows) — shared RPA libraries do not apply to those products' package models.

### Step 3: Detect Gaps

Scan for missing or vague information. Use the Gap Detection Checklist in the [PDD Analysis Guide](pdd-analysis-guide.md) to classify each gap as `[DEFAULT]` or `[SME REVIEW]`.

### Step 4: Select the Primary Scope

> **Progress:** Mark "Read PDD and extract data" as `completed`. Mark "Select product" as `in_progress`.

Apply the [Product Selection Guide](product-selection-guide.md) Level 1 decision table. Produce:

- **Primary scope** — one of: Agents, Coded Apps, API Workflows, Case Management, Maestro Flow, **RPA** (sub-type next), **Solution** (composition next)
- **Solution signals** — note any that matched, even if Level 1 picked a single product (these become candidate additional projects if the user customizes)
- **Reasoning** — bullet points mapping PDD signals to the chosen scope
- **Alternatives considered** — rejected scopes and why

### Step 4.25: RPA Sub-type Selection (if RPA or Solution includes RPA)

If Level 1 selected **RPA**, run Level 1.5 from the [RPA Product Guide](rpa-product-guide.md#level-15--rpa-sub-type-selection) to confirm the sub-type (Process / Library / Test Automation). Always ask the user via `AskUserQuestion` even when only one signal set matches.

If Level 1 selected **Solution** and the composition includes RPA projects, defer Level 1.5 to Step 4.3 Pass C — sub-type runs once per RPA project in the composition.

### Step 4.3: Solution Composition (if Level 1 = Solution OR user customizes)

Run Level 1.75 from the [Product Selection Guide](product-selection-guide.md) when:

- Level 1 selected **Solution** (auto-proceed), OR
- The user picked "Solution (customize)" from the recommendation screen in Step 6

Execute the three passes:

1. **Pass A** — paired multi-select `AskUserQuestion` (two questions in one call, 4 options each, `multiSelect: true`) with the recommended products pre-checked.
2. **Pass B** — resolve counts per product using numbered-choice questions.
3. **Pass C** — per-RPA-project, run Level 1.5 from the [RPA Product Guide](rpa-product-guide.md#level-15--rpa-sub-type-selection) to pick sub-type.

Output: the Level 1.75 project list with Product, Sub-type, Source Signal columns.

### Step 4.5: Run Project Decomposition

Run Level 2.5 for every scope. The work is trivial for single-project scopes and substantive for RPA Process and Solutions.

**Part A — RPA decomposition signals** (per RPA Process project in the scope). See [RPA Product Guide → Level 2.5 Part A](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals).
1. Evaluate the 6 decomposition signals against the PDD data extracted in Step 2.
2. If 2+ signals match → **Master Project** for that RPA Process. Select the pattern (Dispatcher/Performer, Dispatcher/DU/Output, etc.).
3. If 0-1 signals match → **Single Project** for that RPA Process.

Skip Part A for RPA Library, RPA Test Automation, and non-RPA products.

**Part B — Merge into unified project list.** See [Product Selection Guide → Level 2.5 Part B](product-selection-guide.md#part-b--merge-into-the-final-project-list).
1. Combine every project produced by Part A with the non-RPA projects from Level 1 / Level 1.75.
2. Produce the unified project list with columns Product, Sub-type, Role, Framework, Input Queue, Output Queue.
3. For any Master Projects, include the queue schema table.
4. Note cross-product integration points (Flow → RPA, Agent tool → API Workflow, etc.).

This decision is critical — it determines the §10-§12 structure of the RPA template, the Project Inventory section of every non-RPA template, and the Solution overview SDD structure. Getting it wrong means rewriting the SDD.

### Step 5: Check for Agent/Coded App Gaps

If the primary product is **Agents** or **Coded Apps** AND required product-specific information is missing from the PDD, follow the Gap Handling flow in the [Product Selection Guide](product-selection-guide.md). All questions use the numbered-choice format.

Summary:
1. Ask the user: proceed with gap-filling or use a different product?
2. If proceed → batch 4-6 gap-filling questions (Agents: framework, tools, memory, evaluation, bindings. Coded Apps: framework, app type, pages, state, caller)
3. If different product → ask which fallback (RPA Process, Maestro Flow, Case Management, Stop)
4. Re-run Step 4 with fallback, or end if "Stop"

Never auto-fallback. The user must choose explicitly.

### Step 6: Present Summary + Scope Recommendation

Emit the summary block described in "Presenting the Recommendation" in the [Product Selection Guide](product-selection-guide.md). The **recommended scope appears first**; single-product alternatives and "Solution (customize)" follow as alternatives in the confirmation `AskUserQuestion` call.

```markdown
## PDD Analysis Summary

**Process:** <PROCESS_NAME>
**Objective:** <OBJECTIVE_SUMMARY>
**Applications:** <APP_COUNT> — <APP_NAME (ROLE)>, ...
**Process Steps:** <STEP_COUNT> steps identified across <APP_COUNT> applications
**Business Rules:** <RULE_COUNT> extracted
**Business Exceptions:** <EXCEPTION_COUNT> defined in PDD
**System Errors:** <ERROR_COUNT> defined in PDD
**Gaps Detected:** <DEFAULT_COUNT> [DEFAULT], <SME_REVIEW_COUNT> [SME REVIEW]

## Recommended Scope
**Recommendation:** <SINGLE_PRODUCT | SOLUTION(<PRODUCT_1>, <PRODUCT_2>, ...)>
**Reasoning:**
- <PDD_SIGNAL_1> → <PRODUCT_MAPPING>
- <PDD_SIGNAL_2> → <PRODUCT_MAPPING>

**Alternatives considered:**
- <REJECTED_OPTION> — rejected because <REASON>

## Project List
<UNIFIED_PROJECT_LIST_FROM_LEVEL_2.5_PART_B>

## Queue Architecture (RPA Master Project rows only)
<QUEUE_TABLE_OR_N/A>
**Decomposition signals matched:** <LIST_MATCHED_SIGNALS_PER_RPA_PROCESS_PROJECT_OR_N/A>

### Clarifying Questions
<NUMBERED_QUESTIONS_IF_ANY>
```

Then call `AskUserQuestion` with the confirmation question from the Product Selection Guide's "Presenting the Recommendation" section (recommendation as option 1, single-product alternatives, then "Solution (customize)").

**If the user picks "Solution (customize)":** re-run Level 1.75 per the customize branch in the guide, then re-emit this summary with the customized project list, then re-ask the confirmation question. Max 3 revisions — after that, proceed with the latest composition.

**If the user picks a single-product alternative:** re-run Step 4 (and Step 4.25 if RPA) with the user's choice as the forced primary.

Ask at most 5 clarifying questions total, in a single round. If the user cannot answer some, tag those items as `[SME REVIEW]` and proceed.

## Phase 2 — Architecture Review

> **Progress:** Mark "Select product" as `completed`. Mark "Generate architecture (Phase 2)" as `in_progress`.

### Step 1: Load the Template(s)

Load from the [Template Mapping table in the Product Selection Guide](product-selection-guide.md#template-mapping):

- **Single-product scope:** load the one template matching the Level 1 primary.
- **Solution scope:** load the solution overview structure PLUS one template per project in the Level 2.5 unified project list. RPA Master Projects share one RPA template file across their sub-projects; unrelated RPA projects each get their own file.

### Step 2: Generate the Architectural Core

The architectural core sections differ per template. For each product, generate these sections in Phase 2:

**RPA (Process / Library / Test Automation):**
- §5 Data Definitions (C# records or dictionary tables per §13 Implementation Mode)
- §9 Application Inventory (flag Integration Service connectors, specify email protocol)
- §10 Master Project Architecture (apply Level 2.5 Part A from [rpa-product-guide.md](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) — Single vs Master Project, sub-projects, queue schema)
- §11 Project Structure (per sub-project if Master Project: project type, framework, folder layout, workflow inventory)
- §12 Queue Architecture (Master Project only — queue definitions, item schemas, processing rules)
- §13 Implementation Mode (XAML / Coded / Hybrid — apply Level 2 from [rpa-product-guide.md](rpa-product-guide.md#level-2--authoring-mode))
- §14 Packages (infer NuGet packages from §9 Application Inventory and process steps)

**Maestro Flow:**
- §3 Nodes Inventory (with node type per node)
- §4 Variables (direction, type)
- §5 Subflows (if any)
- §7 Integrated Components (RPA, Agents, API Workflows, Connectors, HITL touchpoints)
- §9 Project Structure

**Case Management:**
- §3 Stages
- §4 Tasks Grid (per stage, lanes × index)
- §7 Data Definitions (case data objects, supporting objects, data flow)
- §13 Task Type Registry (RPA / AGENT / API_WORKFLOW / CONNECTOR / HITL)
- §14 Integrated Components
- §15 Project Structure

**Agents:**
- §2 Agent Framework (LangGraph / LlamaIndex / OpenAI Agents / Simple Function)
- §3 Tools
- §4 Memory / RAG
- §6 Orchestrator Bindings
- §9 Project Structure (Coded vs Low-code)

**Coded Apps:**
- §2 App Type & Tech Stack
- §3 Pages & Routes
- §4 Components
- §5 State Management
- §6 API Integration
- §10 Project Structure

**API Workflows:**
- §2 Input Schema
- §3 Output Schema
- §4 Execution Flow (high-level steps, no JavaScript)
- §5 Connectors & External Calls
- §10 Project Structure

### Step 3: Decompose Steps Into Implementation Units

Each template has a primary inventory table. Map PDD steps to units:

| Product | Primary Inventory | Unit Type |
|---|---|---|
| RPA (Single Project) | Workflow Inventory | `.xaml` or `.cs` workflow files |
| RPA (Master Project) | Workflow Inventory **per sub-project** | `.xaml` or `.cs` workflow files, grouped by sub-project |
| Flow | Nodes Inventory | Flow nodes |
| Case | Tasks Grid | Tasks per lane/index |
| Agents | Tools | Python functions, RPA/API workflow bindings |
| Coded Apps | Pages + Components | Routes and React/Angular/Vue components |
| API Workflows | Execution Flow steps | Activities (HTTP, Connector, Script) |

Each unit must have: **a concrete responsibility, specific PDD step references, and defined inputs/outputs.**

**For RPA Master Project:** decompose in two passes:
1. First, assign each PDD step to a sub-project based on the §10 sub-projects table (each sub-project lists its PDD steps).
2. Then, within each sub-project, decompose the assigned steps into workflow files.
3. For REFramework sub-projects, the main workflows (Init, GetTransactionData, Process, SetTransactionStatus) come from the framework — only the Process-specific workflows go in the inventory.

### Step 4: Flag Integrated Components

For each integrated component detected in Phase 1, flag it in the appropriate section of the template:

- **HITL** (Flow / Maestro / Agent only) → flag touchpoints in nodes/agent description; implementation task will route to `uipath-human-in-the-loop` skill
- **Integration Service connectors** → list in Application Inventory (RPA) or Connectors section (others); implementation task will route to `uipath-platform`
- **RPA processes called by Flow/Agent/Case** → list in Integrated Components section; implementation task will create the RPA project
- **API Workflows called by Flow/Agent/Case** → list in Integrated Components section; implementation task will create the API Workflow project

### Step 5: Present Architecture for Review

Present the architectural core to the user. Wait for approval or adjustments.

**Approval criteria:** any response without specific change requests. Responses like "looks good", "ok", "proceed", "yes", or a topic change all count as approval. If the user requests specific changes, incorporate them and re-present the architecture (max 3 revisions — after that, proceed with the latest version and tag disagreements as `[SME REVIEW]`).

## Phase 3 — Full SDD Generation

> **Progress:** Mark "Generate architecture (Phase 2)" as `completed`. Mark "Generate full SDD (Phase 3)" as `in_progress`.

### Step 1: Generate Remaining Sections

Fill in all sections of the chosen template not covered in Phase 1 or Phase 2. Section assignments per phase:

**Phase 1 produces (for all templates):**
- Header & Document History (process name, today's date, version 1.0)
- Overview section (§1)
- Process/Flow/Lifecycle diagram (§2 for most templates)
- Detailed steps / nodes description where applicable

**Phase 2 produces:** See Phase 2 Step 2 above (template-specific architectural core)

**Phase 3 produces:** All remaining sections — typically:
- Business Rules (RPA, Case)
- Value Mappings (RPA)
- Exception / Error Handling (all)
- Credentials & Assets (RPA)
- Deployment Environment (RPA — robot type, Studio/Robot versions, VM hosts, screen resolution, scalability). Fill `[SME REVIEW]` when the PDD does not specify — these fields typically come from the deployment team, not the PDD. Never invent VM names, version pins, or robot types.
- Triggers (Flow)
- SLA Rules & Escalations (Case)
- Compliance Constraints (Case)
- Roles & RACI Matrix (Case)
- Evaluation Criteria (Agents)
- Testing Strategy (including End-to-End Pipeline Test for RPA Master Projects)
- Implementation Plan (final section — task breakdown, using Master Project or Single Project plan per §10)

### Step 1.5: Resolve SME Review Items

> **Progress:** Mark "Generate full SDD (Phase 3)" as `completed`. Mark "Resolve SME review items" as `in_progress`.

Before writing the SDD, collect all `[SME REVIEW]` items. If there are any:

1. Batch them into a single `AskUserQuestion` using numbered-choice format:

> Before I finalize the SDD, these items need your input:
>
> 1. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
> 2. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
>
> You can answer each, accept all defaults by replying "use defaults", or skip specific items.

2. Update the SDD sections with the user's answers.
3. If the user partially answers or asks follow-ups, do one more round (max 2 rounds total). After 2 rounds, keep remaining unresolved items as `[SME REVIEW]` and proceed to Step 2.
4. Any items the user explicitly skips remain as `[SME REVIEW]` in the final file (should be rare).
5. If there are zero `[SME REVIEW]` items, skip this step entirely.

This step runs in BOTH Autonomous and Interactive modes — it is a hard blocker to producing a complete SDD.

### Step 2: Write the SDD File(s)

> **Progress:** Mark "Resolve SME review items" as `completed`. Mark "Write SDD to disk" as `in_progress`.

1. Assemble all sections in template order.
2. If any `[SME REVIEW]` items remain, add a consolidated warning section after Document History and before the Table of Contents:

```markdown
## Action Required — SME Review Items

| # | Section | Item | Question |
|---|---|---|---|
| 1 | <SECTION> | <ITEM> | <QUESTION> |

> These items are marked `[SME REVIEW]` in the document. The automation can be built with defaults, but these must be verified before production.
```

3. **Target SDD length: 300-800 lines of markdown** for single-project SDDs. **Master Project SDDs may reach 600-1200 lines** due to per-sub-project structure sections — this is expected. For processes with more than 20 steps, group related steps and summarize at the parent level. For processes with more than 10 business rules, prioritize the 10 most impactful.
4. Write the output file(s) to the current working directory:
   - **Single-product scope:** one file at `<PROCESS_NAME_KEBAB_CASE>-sdd.md`.
   - **Solution scope:** the solution overview at `<SOLUTION_NAME_KEBAB>-solution-sdd.md` PLUS one per-project SDD at `<PROJECT_NAME_KEBAB>-sdd.md` for each project in the unified project list. Put the `[SME REVIEW]` warning block in the solution overview AND in any per-project file where a review item lives in that project.
5. Output a summary in the conversation:

```markdown
## SDD Generated

<FILENAME_1> — <COUNT> sections, <LINE_COUNT> lines
<FILENAME_2> — <COUNT> sections, <LINE_COUNT> lines
...

<SME_REVIEW_COUNT> unresolved SME review items (if any — list them).
```

### Step 3: Create Live Tasks

> **Progress:** Mark "Write SDD to disk" as `completed`. Mark "Create implementation tasks" as `in_progress`.

Create tasks via TaskCreate that map to the Implementation Plan section. Apply rule G-8 (defined in Step 0.5): if any `TaskCreate` call fails, log a single warning, continue, and do not retry — the Implementation Plan section in the SDD file is the authoritative deliverable.

Each task must:

1. Have a clear, actionable subject in imperative form
2. Reference exact SDD sections in the description
3. Include the anti-hallucination rule: "Use values, mappings, and structure exactly as documented in the SDD. Do not infer or guess."
4. Have proper dependencies set via `addBlockedBy`

Task ordering follows the Implementation Plan section of the selected template. Integrated component tasks come BEFORE tasks that use them (e.g., create the RPA process before building the Flow node that calls it).

### Step 4: Execute the Implementation Plan (conditional)

> **Progress:** Mark "Create implementation tasks" as `completed`. All progress tasks are now done.

Only proceed if the user's intent implies implementation — they asked to "create", "build", "implement", "set up", or "make" a project from a PDD. If the user asked to "design", "architect", or "generate an SDD", stop here. The SDD and task list are the deliverables.

When proceeding, work through the tasks in dependency order. The agent will activate the appropriate skills for each task automatically based on the task description.

Mark each task as `completed` via TaskUpdate as you finish it. If a task fails or is blocked, keep it `in_progress` and diagnose the issue before moving on.

When all tasks are complete, output a final summary:

```markdown
## Implementation Complete

**Projects created:** <LIST_OF_PROJECT_NAMES_AND_TYPES>
**Tasks completed:** <COMPLETED_COUNT> / <TOTAL_COUNT>
**Skipped tasks:** <LIST_OR_NONE>
**Remaining `[SME REVIEW]` items:** <LIST_OR_NONE>
```
