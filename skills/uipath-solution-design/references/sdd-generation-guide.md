# SDD Generation Guide

Step-by-step instructions for transforming a PDD into an SDD. Follow the 3-phase interaction model described in SKILL.md.

## Phase 1 — PDD Analysis

### Step 1: Read the PDD

1. Determine the input format (PDF, docx, markdown, pasted text).
2. For PDFs, read in chunks of up to 20 pages per request. Start with pages 1-20, then continue.
3. For large documents, read the Table of Contents first (usually page 2-3) to understand the structure before reading detail sections.

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

Scan for missing or vague information. Classify each gap:

1. **`[DEFAULT]` — Fill with industry-standard patterns.** Apply when:
   - Retry counts not specified → default to 3 retries with exponential backoff
   - Timeouts not specified → default to 30s for page loads, 10s for element waits
   - Error notification not specified → default to logging + continue pattern
   - Max items per run not specified → default to 50 items as a safety cap

2. **`[SME REVIEW]` — Flag for business knowledge.** Apply when:
   - Amount thresholds or approval limits are not stated
   - Business rules depend on domain knowledge not in the PDD
   - Process scheduling conflicts with other processes
   - Data retention or compliance requirements are unclear
   - Exception handling requires a business decision (retry vs. skip vs. escalate)

### Step 4: Present Summary

Present to the user:

```
## PDD Analysis Summary

**Process:** <process name>
**Objective:** <1-2 sentence summary>
**Applications:** <count> — <app1 (role)>, <app2 (role)>, ...
**Process Steps:** <count> steps identified across <count> applications
**Business Rules:** <count> extracted
**Business Exceptions:** <count> defined in PDD
**System Errors:** <count> defined in PDD
**Gaps Detected:** <count> [DEFAULT], <count> [SME REVIEW]

### Clarifying Questions
<only if genuinely ambiguous — list numbered questions>
```

Wait for user confirmation before proceeding to Phase 2.

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

## Phase 3 — Full SDD Generation

### Step 1: Generate Remaining Sections

Using the [SDD Template](../assets/templates/sdd-template.md), generate all sections not yet covered:

1. Business rules — extract and number from PDD prose and exception tables
2. Value mappings — any data transformations between systems
3. Exception handling table — from the PDD's exception handling section, enriched with `[DEFAULT]` actions where missing
4. Error handling table — from the PDD's error handling section, enriched with `[DEFAULT]` retry/escalation logic
5. Credentials and assets table — from the PDD's credentials and asset management section
6. Testing strategy — canonical test case, happy path assertions, exception test cases
7. Implementation plan — task breakdown with SDD section references

### Step 2: Write the SDD File

1. Assemble all sections into the template structure.
2. Write to `<process-name-kebab-case>-sdd.md` in the current working directory.
3. Confirm the file path to the user.

### Step 3: Create Live Tasks

Create tasks via TaskCreate that map to the Implementation Plan section. Each task must:

1. Have a clear, actionable subject in imperative form
2. Reference exact SDD sections in the description
3. Include the anti-hallucination rule: "Use values, mappings, and structure exactly as documented in the SDD. Do not infer or guess."
4. Have proper dependencies set via `addBlockedBy`

Standard task sequence:

| Order | Task | Blocked By | Description |
|---|---|---|---|
| 1 | Create project scaffolding | — | Create UiPath project per SDD §Project Structure and §Implementation Mode (via `uipath-platform`) |
| 2 | Define data models | — | Create types/variables per SDD §Data Definitions |
| 3 | Configure assets and credentials | — | Set up assets per SDD §Credentials & Assets |
| 4 | Implement `<workflow-name>` | 1, 2 | One task per workflow in the inventory table, referencing its PDD steps |
| ... | *(repeat for each workflow)* | Previous workflow tasks as needed | |
| N-1 | Implement exception and error handling | All workflow tasks | Wire up exceptions per SDD §Exception Handling and §Error Handling |
| N | Implement test suite | All workflow tasks | Build tests per SDD §Testing Strategy |

### Step 4: Execute the Implementation Plan

After writing the SDD and creating tasks, proceed to execute the plan. Do not wait for the user to manually invoke other skills — work through the tasks in dependency order:

1. **Task 1 — Project scaffolding:** Use `uipath-platform` to create the UiPath project based on the SDD's §Project Structure and §Implementation Mode sections.
2. **Task 2 — Data models:** Use `uipath-rpa` to create the data types/variables per §Data Definitions.
3. **Task 3 — Assets and credentials:** Use `uipath-platform` to configure assets per §Credentials & Assets.
4. **Tasks 4..N-2 — Workflows:** Use `uipath-rpa` to implement each workflow from the inventory table, in dependency order.
5. **Task N-1 — Exception/error handling:** Use `uipath-rpa` to wire up handlers per §Exception Handling and §Error Handling.
6. **Task N — Test suite:** Use `uipath-rpa` to build tests per §Testing Strategy.

Mark each task as `completed` via TaskUpdate as you finish it. If a task fails or is blocked, keep it `in_progress` and diagnose the issue before moving on.
