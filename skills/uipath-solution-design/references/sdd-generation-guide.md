# SDD Generation Guide

Step-by-step instructions for transforming a PDD into an SDD. Follow the 3-phase interaction model described in SKILL.md.

## Phase 1 — PDD Analysis & Product Selection

### Step 1: Read the PDD

1. Determine the input format (PDF, docx, markdown, pasted text).
2. **Size-based reading strategy** for PDFs:
   - **Under 10 pages:** read the entire document in one pass. Skip ToC lookup.
   - **10-50 pages:** read the ToC first, then read sections in priority order (overview → steps → exceptions → applications → credentials).
   - **Over 50 pages:** read ToC, then read high-priority sections (overview, process steps, exceptions) first, extract as you go, then read remaining sections.
3. For pasted text over 3000 words, ask the user to paste in sections.
4. **Docx handling:** if the .docx file renders as raw XML or binary content, tell the user: "The Word document could not be parsed as readable text. Please export it as PDF or paste the content directly." Do not attempt to extract data from garbled output.
5. **Error cases:** if the document cannot be read (corrupt PDF, password-protected, unsupported format), tell the user and ask them to provide it in a different format. If the document does not appear to be a PDD (no process steps, no application details, no exception handling), tell the user and stop.
6. **Language handling:** if the PDD is not in English, ask the user: "The PDD appears to be in [LANGUAGE]. Should I generate the SDD in English or [LANGUAGE]?" Generate the SDD in the requested language, but keep section headings and structural identifiers (BR-01, B1, E1) in English for tool compatibility.

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

### Step 3: Detect Gaps

Scan for missing or vague information. Use the Gap Detection Checklist in the [PDD Analysis Guide](pdd-analysis-guide.md) to classify each gap as `[DEFAULT]` or `[SME REVIEW]`.

### Step 4: Select the Product

Apply the [Product Selection Guide](product-selection-guide.md) decision tree. Produce:

- **Primary product** (one of: RPA Process, RPA Library, RPA Test Automation, Maestro Flow, Case Management, Agents, Coded Apps, API Workflows)
- **Integrated components** (any of: RPA processes, Agents, API Workflows, Integration Service connectors, HITL, Coded Apps)
- **Reasoning** — bullet points mapping PDD signals to the chosen product
- **Alternatives considered** — rejected products and why

### Step 5: Check for Agent/Coded App Gaps

If the primary product is **Agents** or **Coded Apps** AND required product-specific information is missing from the PDD:

1. Use `AskUserQuestion` with a single prompt:
   > "The PDD describes [product]-specific capabilities, but requirements are missing for [list gaps]. Should I proceed with [product] and ask follow-up questions, or use a different product?"
   > Options: "Proceed with [product]" / "Use a different product"

2. If user chooses **Proceed**:
   - Use `AskUserQuestion` again with a batch of 4-6 product-specific gap-filling questions
   - For Agents: framework choice, tools, memory/RAG, evaluation criteria, bindings
   - For Coded Apps: framework, app type (Web/Action), pages/routes, state management, caller

3. If user chooses **Use a different product**:
   - Use `AskUserQuestion` to pick the fallback:
     > "Which fallback product?" Options: "RPA Process", "Maestro Flow", "Case Management", "Stop"
   - Re-run Step 4 with the fallback as the primary
   - If "Stop" is chosen, end the session with a message

Never auto-fallback. The user must choose explicitly.

### Step 6: Present Summary + Product Recommendation

Present to the user:

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

## Recommended Product

**Primary:** <PRIMARY_PRODUCT>
**Integrated components:** <INTEGRATED_PRODUCTS_OR_NONE>

**Reasoning:**
- <PDD_SIGNAL_1> → <PRODUCT_MAPPING>
- <PDD_SIGNAL_2> → <PRODUCT_MAPPING>

**Alternatives considered:**
- <REJECTED_PRODUCT> — rejected because <REASON>

### Clarifying Questions
<NUMBERED_QUESTIONS_IF_ANY>
```

Wait for user confirmation. Ask at most 5 clarifying questions total, in a single round. If the user cannot answer some, tag those items as `[SME REVIEW]` and proceed. If the user disagrees with the product recommendation, re-run Step 4 with their preference.

## Phase 2 — Architecture Review

### Step 1: Load the Product-Specific Template

Based on the primary product selected in Phase 1, load the matching template:

| Primary Product | Template File |
|---|---|
| RPA Process, Library, Test Automation | `../assets/templates/rpa-sdd-template.md` |
| Maestro Flow | `../assets/templates/flow-sdd-template.md` |
| Case Management | `../assets/templates/case-sdd-template.md` |
| Agents | `../assets/templates/agent-sdd-template.md` |
| Coded Apps | `../assets/templates/coded-app-sdd-template.md` |
| API Workflows | `../assets/templates/api-workflow-sdd-template.md` |

### Step 2: Generate the Architectural Core

The architectural core sections differ per template. For each product, generate these sections in Phase 2:

**RPA (Process / Library / Test Automation):**
- §5 Data Definitions (C# records or dictionary tables per §12 Implementation Mode)
- §9 Application Inventory (flag Integration Service connectors)
- §11 Project Structure (project type, folder layout, workflow inventory)
- §12 Implementation Mode (XAML / Coded / Hybrid — apply Level 2 from product-selection-guide)

**Maestro Flow:**
- §3 Nodes Inventory (with node type per node)
- §4 Variables (direction, type)
- §5 Subflows (if any)
- §7 Integrated Components (RPA, Agents, API Workflows, Connectors, HITL touchpoints)
- §9 Project Structure

**Case Management:**
- §3 Stages
- §4 Tasks Grid (per stage, lanes × index)
- §8 Task Type Registry (RPA / AGENT / API_WORKFLOW / CONNECTOR / HITL)
- §9 Integrated Components
- §10 Project Structure

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
| RPA | Workflow Inventory | `.xaml` or `.cs` workflow files |
| Flow | Nodes Inventory | Flow nodes |
| Case | Tasks Grid | Tasks per lane/index |
| Agents | Tools | Python functions, RPA/API workflow bindings |
| Coded Apps | Pages + Components | Routes and React/Angular/Vue components |
| API Workflows | Execution Flow steps | Activities (HTTP, Connector, Script) |

Each unit must have: **a concrete responsibility, specific PDD step references, and defined inputs/outputs.**

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
- Exception / Error Handling
- Credentials & Assets (RPA)
- Triggers (Flow)
- SLA Rules & Escalations (Case)
- Evaluation Criteria (Agents)
- Error Handling (all)
- Testing Strategy
- Implementation Plan (final section — task breakdown)

### Step 2: Write the SDD File

1. Assemble all sections in template order.
2. **Target SDD length: 300-800 lines of markdown.** For processes with more than 20 steps, group related steps into sub-processes and summarize at the parent level. For processes with more than 10 business rules, prioritize the 10 most impactful and list the rest in an "Additional Rules" subsection.
3. Write to `<PROCESS_NAME_KEBAB_CASE>-sdd.md` in the current working directory.
4. Confirm the file path to the user.

### Step 3: Create Live Tasks

Create tasks via TaskCreate that map to the Implementation Plan section. If TaskCreate is unavailable or fails, the implementation plan in the SDD file is sufficient — do not block SDD completion on task creation failures.

Each task must:

1. Have a clear, actionable subject in imperative form
2. Reference exact SDD sections in the description
3. Include the anti-hallucination rule: "Use values, mappings, and structure exactly as documented in the SDD. Do not infer or guess."
4. Have proper dependencies set via `addBlockedBy`

Task ordering follows the Implementation Plan section of the selected template. Integrated component tasks come BEFORE tasks that use them (e.g., create the RPA process before building the Flow node that calls it).

### Step 4: Execute the Implementation Plan (conditional)

Only proceed if the user's intent implies implementation — they asked to "create", "build", "implement", "set up", or "make" a project from a PDD. If the user asked to "design", "architect", or "generate an SDD", stop here. The SDD and task list are the deliverables.

When proceeding, work through the tasks in dependency order. The agent will activate the appropriate skills for each task automatically based on the task description.

Mark each task as `completed` via TaskUpdate as you finish it. If a task fails or is blocked, keep it `in_progress` and diagnose the issue before moving on.
