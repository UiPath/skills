# SDD Generation Guide

Step-by-step instructions for transforming a PDD into an SDD. Follow the 3-phase interaction model described in SKILL.md.

## Phase 1 — PDD Analysis

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

Follow the [PDD Analysis Guide](pdd-analysis-guide.md) to extract data from each PDD section. Build an internal model with these components:

| Component | PDD Topic to Look For | Required |
|---|---|---|
| Process name and objective | Introduction | Yes |
| Key contacts | Process key contacts | No |
| Process overview (schedule, volumes, FTEs) | Process overview | Yes |
| In-scope activities | In scope for RPA | Yes |
| Out-of-scope activities | Out of scope for RPA | Yes |
| Process steps | Detailed process map / Detailed process steps | Yes |
| Business exceptions | Exceptions handling | Yes |
| System errors | Error mapping and handling | Yes |
| Application inventory | In-scope application details | Yes |
| Development prerequisites | Prerequisites for development | No |
| Credentials and assets | Credentials and asset management | Yes |
| Test data | Appendix | No |

### Step 3: Detect Gaps

Scan for missing or vague information. Use the Gap Detection Checklist in the [PDD Analysis Guide](pdd-analysis-guide.md) to classify each gap as `[DEFAULT]` (fill with industry-standard pattern) or `[SME REVIEW]` (flag for business knowledge).

### Step 4: Present Summary

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

### Clarifying Questions
<NUMBERED_QUESTIONS_IF_ANY>
```

Wait for user confirmation before proceeding to Phase 2. Ask at most 5 clarifying questions total, in a single round. If the user cannot answer some questions, tag those items as `[SME REVIEW]` and proceed — do not re-ask.

## Phase 2 — Architecture Review

### Step 1: Determine Implementation Mode

Apply the [Implementation Mode Guide](implementation-mode-guide.md) to recommend XAML, Coded C#, or Hybrid. Write a 2-3 sentence justification.

### Step 2: Design Project Structure

1. **Choose a framework pattern:**
   - **REFramework** — when the process is transactional (queue-based, item-by-item processing with retry logic)
   - **Linear** — when the process is a simple sequential flow with no transaction concept
   - **Custom** — when neither fits (rare for PDD-described processes)

2. **Decompose into workflows.** Map PDD steps to workflow files:
   - Group related steps into a single workflow (e.g., all login steps = one workflow)
   - Separate orchestration from processing (main loop vs. per-item logic)
   - Extract reusable operations (e.g., "update status on dashboard" used by both success and error paths)
   - Each workflow should have a single, clear responsibility

3. **Build the workflow inventory table.** For each workflow:
   - File name (with extension: `.xaml` or `.cs`)
   - Responsibility (1-2 sentences)
   - PDD steps covered (exact step numbers)
   - Input arguments (name, type)
   - Output arguments (name, type)

### Step 3: Define Data Models

Based on the implementation mode:

- **Coded / Hybrid:** Define C# classes, structs, and enums for:
  - Transaction data (the item being processed)
  - Output data (results captured during processing)
  - Configuration data (if complex enough to warrant a type)
  - Enums for status values, category mappings, error types

- **Pure XAML:** Define:
  - Dictionary keys and value types for transaction data
  - DataTable column definitions
  - Variable naming conventions

### Step 4: Map Application Scopes

For each application in the inventory:

| Field | Description |
|---|---|
| Application name | From the PDD's application details section |
| Role | Data source, data target, processing tool, or lookup utility |
| Interaction pattern | Read-only, write-only, read-write, or transient |
| Session management | Stay logged in across transactions, or per-item login/logout |
| Owning workflow(s) | Which workflow(s) manage this application's scope |

### Step 5: Present Architecture for Review

Present the implementation mode, project structure, workflow inventory, data models, and application scope map to the user. Wait for approval or adjustments before proceeding.

**Approval criteria:** any response without specific change requests. Responses like "looks good", "ok", "proceed", "yes", or a topic change all count as approval. If the user requests specific changes, incorporate them and re-present the architecture (max 3 revisions — after that, proceed with the latest version and tag disagreements as `[SME REVIEW]`).

## Phase 3 — Full SDD Generation

### Step 1: Generate Remaining Sections

Using the [SDD Template](../assets/templates/sdd-template.md), generate every section not covered in Phase 2. Every template section must be assigned to a phase — nothing is orphaned.

**Generated in Phase 1 (from extracted PDD data):**
- Header & Document History (process name, current date, version 1.0)
- §1 Process Overview
- §2 Process Map — build from Phase 1 extracted steps using mermaid syntax. Do not invent steps.
- §3 Detailed Process Steps — reformat Phase 1 step extractions into the template structure

**Generated in Phase 2 (architecture core):**
- §5 Data Definitions
- §9 Application Inventory
- §11 Project Structure (the most important section)
- §12 Implementation Mode

**Generated in Phase 3 (this step):**
- §4 Business Rules — extract and number from PDD prose and exception tables
- §6 Value Mappings — any data transformations between systems
- §7 Exception Handling — from the PDD's exception handling section, enriched with `[DEFAULT]` actions where missing
- §8 Error Handling — from the PDD's error handling section, enriched with `[DEFAULT]` retry/escalation logic
- §10 Credentials & Assets — from the PDD's credentials and asset management section
- §13 Testing Strategy — canonical test case, happy path assertions, exception test cases
- §14 Implementation Plan — task breakdown with SDD section references

### Step 2: Write the SDD File

1. Assemble all sections in template order (header through §14), regardless of the phase in which they were generated.
2. **Target SDD length: 300-800 lines of markdown.** For processes with more than 20 steps, group related steps into sub-processes and summarize at the parent level in §3. For processes with more than 10 business rules, prioritize the 10 most impactful in §4 and list the rest in an "Additional Rules" subsection.
3. Write to `<PROCESS_NAME_KEBAB_CASE>-sdd.md` in the current working directory.
4. Confirm the file path to the user.

### Step 3: Create Live Tasks

Create tasks via TaskCreate that map to the Implementation Plan section. If TaskCreate is unavailable or fails, the implementation plan in the SDD file is sufficient — do not block SDD completion on task creation failures.

Each task must:

1. Have a clear, actionable subject in imperative form
2. Reference exact SDD sections in the description
3. Include the anti-hallucination rule: "Use values, mappings, and structure exactly as documented in the SDD. Do not infer or guess."
4. Have proper dependencies set via `addBlockedBy`

Standard task sequence:

| Order | Task | Blocked By | Description |
|---|---|---|---|
| 1 | Create project scaffolding | — | Create UiPath project per SDD §Project Structure and §Implementation Mode |
| 2 | Define data models | — | Create types/variables per SDD §Data Definitions |
| 3 | Configure assets and credentials | — | Set up assets per SDD §Credentials & Assets |
| 4 | Implement `<WORKFLOW_NAME>` | 1, 2 | One task per workflow in the inventory table, referencing its PDD steps |
| ... | *(repeat for each workflow)* | Previous workflow tasks as needed | |
| N-1 | Implement exception and error handling | All workflow tasks | Wire up exceptions per SDD §Exception Handling and §Error Handling |
| N | Implement test suite | All workflow tasks | Build tests per SDD §Testing Strategy |

### Step 4: Execute the Implementation Plan (conditional)

Only proceed if the user's intent implies implementation — they asked to "create", "build", "implement", "set up", or "make" a project from a PDD. If the user asked to "design", "architect", or "generate an SDD", stop here. The SDD and task list are the deliverables.

When proceeding, work through the tasks in dependency order:

1. **Task 1 — Project scaffolding:** Create the UiPath project per SDD §Project Structure and §Implementation Mode.
2. **Task 2 — Data models:** Create the data types/variables per §Data Definitions.
3. **Task 3 — Assets and credentials:** Configure assets per §Credentials & Assets.
4. **Tasks 4..N-2 — Workflows:** Implement each workflow from the inventory table, in dependency order.
5. **Task N-1 — Exception/error handling:** Wire up handlers per §Exception Handling and §Error Handling.
6. **Task N — Test suite:** Build tests per §Testing Strategy.

The agent will activate the appropriate skills for each task automatically.

Mark each task as `completed` via TaskUpdate as you finish it. If a task fails or is blocked, keep it `in_progress` and diagnose the issue before moving on.
