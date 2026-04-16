---
name: uipath-review
description: "[PREVIEW] Read-only UiPath reviewer — audit structure, quality, best practices for RPA (.xaml/.cs), agents (.py/agent.json), flows (.flow), coded apps, solutions (.uipx). Does NOT edit files. For building/editing→domain skills."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Solution & Artifact Reviewer

Review UiPath solutions and individual artifacts for structural validity, quality, best practices, optimization, and correctness. Produces a structured review report with findings and recommendations.

## When to Use This Skill

- User asks to "review", "audit", "check quality of", or "evaluate" a UiPath project or solution
- User asks "is this solution good?" or "what can be improved?"
- User wants a pre-deployment quality gate check
- User wants to understand the business value and architecture of an existing solution
- User asks about best practices for a specific artifact type
- User has inherited a UiPath project and wants to understand its quality

## Critical Rules

1. **NEVER modify any files.** This skill is read-only. If fixes are needed, identify them in the report and tell the user which skill to use (uipath-rpa, uipath-agents, uipath-maestro-flow, uipath-coded-apps, uipath-platform).
2. **ALWAYS run validation and Workflow Analyzer before manual review.** Run `uip rpa get-errors` on every RPA entry point, `uip agent validate` on agents, `uip flow validate` on flows. Report every Error, Warning, and Info result. A review without automated validation is incomplete.
3. **ALWAYS discover and classify before reviewing.** For solutions: classify every project before reviewing any individual one. For single projects: identify the project type and find the enclosing project directory before reviewing individual files.
4. **Report severity for every finding.** Use: **Critical** (blocks deployment), **Warning** (should fix), **Info** (improvement opportunity).
5. **Understand business context first.** Before evaluating optimization, ask or infer what the solution is trying to accomplish. A queue-based architecture is not "better" if the use case processes 5 items/day.
6. **Use `--output json`** on all CLI validation commands for programmatic parsing.
7. **Do not duplicate what validation commands catch.** Reference the validation output by rule ID and message — do not manually re-describe the same issue. But DO include every validation result (Error, Warning, Info) in the report.
8. **Cap the review at 30 minutes of analysis.** For very large solutions (10+ projects), provide a summary review with deep dives on the 3 highest-risk projects. Offer to review remaining projects if the user wants.

## Review Workflow

### Step 0 — Discover, Scope, and Locate the PDD

#### 0a. Probe the Filesystem

Run this from the directory the user specified (or the current working directory):

```bash
# Discover solution files, project markers, and documentation
find . -maxdepth 3 \( -name "*.uipx" -o -name "project.json" -o -name "agent.json" -o -name "*.flow" -o -name "app.config.json" -o -name ".uipath" -o -name "langgraph.json" -o -name "llama_index.json" -o -name "openai_agents.json" -o -name "uipath.json" -o -name "main.py" \) 2>/dev/null

# Search for PDD or design documents
find . -maxdepth 3 \( -name "*PDD*" -o -name "*pdd*" -o -name "*Process_Design*" -o -name "*process_design*" -o -name "*Process-Design*" -o -name "*ProcessDesign*" -o -name "*SDD*" -o -name "*Solution_Design*" -o -name "*design_document*" -o -name "*DesignDocument*" -o -name "*requirements*" -o -name "*specification*" \) 2>/dev/null
```

#### 0b. Locate the PDD (Process Design Document)

The PDD is the **source of truth** for the review. It defines what the automation should do, its business context, expected inputs/outputs, exception handling requirements, and success criteria. The review evaluates whether the implementation matches the PDD.

**Search for PDD in this order:**

1. **Check common locations:** `./docs/`, `./documentation/`, `./Design/`, project root
2. **Check common names:** `PDD.docx`, `PDD.pdf`, `PDD.md`, `Process_Design_Document.*`, `SDD.*`, `Solution_Design_Document.*`, `Requirements.*`
3. **Check AGENTS.md or README.md** at project root — may contain or reference the PDD
4. **Check project.json** `description` field or any metadata pointing to documentation

**If PDD is found:**
- Read it (supports .md, .pdf, .docx via appropriate tools)
- Extract the key review criteria: business process description, expected inputs/outputs, exception handling requirements, SLAs, transaction definitions, queue specifications, application list, credential requirements
- Use it as the **primary benchmark** for all subsequent review steps

**If PDD is NOT found:**

Use the `AskUserQuestion` tool to ask interactively:

```
Question: "I could not find a Process Design Document (PDD) in this project. Do you have one I can use as the source of truth for this review?"
Header: "PDD"
Options:
  1. Label: "Yes, I have a file"
     Description: "I'll provide a file path, URL, or Confluence/SharePoint link to the PDD, SDD, or requirements document"
  2. Label: "I'll paste the content"
     Description: "I'll copy/paste the PDD content (or key sections) directly into the chat"
  3. Label: "No, proceed without"
     Description: "Skip PDD alignment — review will cover technical quality and best practices only, not business logic verification"
```

- **If user selects "Yes, I have a file":** they will provide the path in their response. Read the document and proceed with PDD-informed review.
- **If user selects "I'll paste the content":** they will paste the PDD text (or relevant sections) in their next message. Use that content as the PDD for the review.
- **If user selects "No, proceed without":** proceed without it — the review will focus on technical quality, best practices, and structural correctness, but cannot verify business logic alignment. Note this limitation in the report.

#### 0c. Determine Review Scope

> **Workflow labels like "Path A / Path B / Step 3a" are internal to this skill. NEVER use them in the final review report.** The report must use user-facing language — see Step 5 for the required **Review Scope** vocabulary.

Classify the scope internally using these rules:

**Scope: Solution or Multi-project** — `.uipx` exists at root, OR 2+ **executable** project markers exist in different subdirectories.

- Executable project = `project.json` with `outputType` of `Process`/`Tests`/unspecified, OR `agent.json`, OR `.flow`
- Library projects (`outputType: "Library"`) co-located with consumers do NOT trigger this scope — that is the normal library+consumer pattern
- **Windows-Legacy executables do NOT trigger this scope for `.uipx` purposes**: `.uipx` solutions are not supported for Legacy projects. If any detected executable is Legacy, do not flag missing `.uipx` — recommend migration to Modern compatibility if solution bundling is desired. Review each Legacy project independently.

Steps for Solution / Multi-project scope:
1. Read the `.uipx` file (if present) to enumerate all projects
2. Scan subdirectories for project markers not listed in `.uipx` (orphan executables)
3. Classify each project using the detection table in Step 1
4. Run solution-level checks: missing config.json, version mismatches, cross-project dependencies, circular dependencies
5. Build a solution map: every project with its type, path, and relationship to others
6. Cross-reference with PDD (if available)
7. Read [references/solution-review-guide.md](references/solution-review-guide.md) for the full procedure
8. Proceed to Step 1 for each project individually

**Scope: Single Project** — one `project.json` / `agent.json` / `.flow` / coded-app marker at root, no `.uipx`, no executable siblings.

1. Classify the project using the detection table in Step 1
2. Cross-reference with PDD (if available)
3. Skip solution-level checks; go directly to Step 1

If the user pointed to a specific file (e.g., `Main.xaml`), walk up to the enclosing project directory and review the full project.

---

### Step 1 — Classify the Project Type and Capture Language

For **each** project discovered (one for single-project scope, multiple for solution/multi-project scope), determine its type AND capture its expression language.

**Step 1a — Read `expressionLanguage` from `project.json` for every RPA project.** This is mandatory. The value (`VisualBasic` or `CSharp`) affects everything downstream: expression syntax in If/Switch conditions, null checks, type checks (`TypeOf x Is T` in VB vs `x is T` in C#), string operations, LINQ syntax, and naming conventions. All subsequent inspection steps (especially Step 3a Unit of Work grep and expression-dependent checks) MUST adapt patterns to the project's language. Do not assume VB.

Record the language per project alongside the type (see solution table below).

**Step 1b — Determine project type** using the detection table:

| Filesystem Signal | Project Type | Review Checklist |
|---|---|---|
| `project.json` + `.cs` files with `[Workflow]` attributes | RPA (Coded) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| `project.json` + `.xaml` workflow files | RPA (XAML) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| `project.json` with `expressionLanguage: "VisualBasic"` and no/Legacy `targetFramework` | RPA (Windows-Legacy) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) §10. Also recommend the user invoke the dedicated `uipath-rpa-legacy` skill for Legacy-specific deep validation. Legacy is supported indefinitely in Studio LTS — do NOT flag as Critical. |
| `project.json` + both `.cs` and `.xaml` | RPA (Hybrid) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| `project.json` + `.xaml` + DU packages in dependencies (`UiPath.IntelligentOCR.Activities`, `UiPath.DocumentUnderstanding.ML.Activities`) | RPA + Document Understanding | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) + [du-review-checklist.md](references/document-understanding/du-review-checklist.md) |
| `agent.json` (no `main.py`) | Agent (Low-Code) | [agent-review-checklist.md](references/agents/agent-review-checklist.md) |
| `main.py` + `langgraph.json` / `llama_index.json` / `openai_agents.json` / `uipath.json` | Agent (Coded) | [agent-review-checklist.md](references/agents/agent-review-checklist.md) |
| `*.flow` + `project.uiproj` with `"ProjectType": "Flow"` | Flow | [flow-review-checklist.md](references/flows/flow-review-checklist.md) |
| `.uipath/` directory or `app.config.json` | Coded App | [coded-app-review-checklist.md](references/coded-apps/coded-app-review-checklist.md) |

For **Solution / Multi-project scope**, record all projects in a table:

```markdown
| # | Project Path | Type | Language | Entry Points |
|---|---|---|---|---|
| 1 | ./InvoiceProcessor/ | RPA (XAML) | VisualBasic | Main.xaml, Helper.xaml |
| 2 | ./Dispatcher/ | RPA (Coded) | CSharp | Main.cs |
| 3 | ./ClassifierAgent/ | Agent (Coded) | Python | main.py |
| 4 | ./Orchestration.flow | Flow | — | — |
```

### Step 2 — Run Automated Validation and Workflow Analyzer

This step is **mandatory** and **non-negotiable**. You MUST run validation commands yourself (via Bash) before doing any manual review.

- **Solution / Multi-project scope:** Run validation on **every project** in the solution. For each RPA project, validate **every entry point file**.
- **Single Project scope:** Run validation on the single project. For RPA projects, validate **every entry point file**.

Report **all** results — Errors, Warnings, and Info — in the final review report.

#### 2a. RPA Projects — Validate Every Entry Point

1. Read `project.json` → extract the `entryPoints` array
2. For **each** entry point file, run validation yourself:

```bash
uip rpa get-errors --file-path "<ENTRY_FILE>" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

3. Collect **all** results — Errors, Warnings, and Info-level messages
4. If any entry point has validation errors, the project is **not deployable**

> Do NOT validate only Main.xaml — validate every file listed in `entryPoints`. A project can have multiple entry points and errors in any of them block deployment.

#### 2b. RPA Projects — Run Workflow Analyzer

The Workflow Analyzer checks code quality rules (ST-NMG naming, ST-DBP design, ST-MRD maintainability, ST-USG usage, ST-SEC security, ST-REL reliability). Run it explicitly:

```bash
uip rpa analyze --project-dir "<PROJECT_DIR>" --output json --use-studio
```

If `uip rpa analyze` is not available, `uip rpa get-errors` includes Workflow Analyzer results. Check the output for all rule violations:

- **Error-level violations** → report as **Critical** findings (e.g., ST-SEC-007 SecureString, ST-ANA-005 missing project.json)
- **Warning-level violations** → report as **Warning** findings (e.g., ST-DBP-003 empty Catch, ST-MRD-011 Write Line usage, ST-NMG-001 naming)
- **Info-level violations** → report as **Info** findings (e.g., ST-ANA-003 workflow count, ST-ANA-009 file activity stats)

> Every Workflow Analyzer violation must appear in the review report with its rule ID, affected file, and description. Do not silently skip any severity level.

#### 2c. Other Project Types

| Project Type | Validation Command | Report All Severities |
|---|---|---|
| Agent (Low-Code) | `uip agent validate ./path --output json` | Yes — errors, warnings, info |
| Agent (Coded) | `uip codedagent eval main evaluations/eval-sets/smoke-test.json --no-report` (if eval sets exist) | Yes — pass/fail per test case |
| Flow | `uip flow validate <ProjectName>.flow --output json` | Yes — schema errors, reference errors, warnings |
| Coded App | `uip codedapp pack dist --dry-run` | Yes — build errors, pack warnings |
| Solution | `uip solution pack <SolutionDir> <OutputDir> --output json` | Yes — per-project pack results |

#### 2d. Record All Results

For the review report, create a validation summary:

```markdown
### Validation Results

| Project | Command | Errors | Warnings | Info |
|---|---|---|---|---|
| InvoiceProcessor | uip rpa get-errors (Main.xaml) | 0 | 3 | 1 |
| InvoiceProcessor | uip rpa get-errors (Helper.cs) | 1 | 0 | 0 |
| InvoiceDispatcher | uip flow validate | 0 | 0 | 0 |
| ClassifierAgent | uip agent validate | 0 | 1 | 0 |

#### Validation Details
- [E-001] InvoiceProcessor/Helper.cs: ST-SEC-007 — Password argument uses String instead of SecureString
- [W-001] InvoiceProcessor/Main.xaml: ST-MRD-011 — Write Line activity used (use Log Message instead)
- [W-002] InvoiceProcessor/Main.xaml: ST-DBP-003 — Empty Catch block in TryCatch_1
- [W-003] InvoiceProcessor/Main.xaml: ST-NMG-001 — Variable 'temp_val' does not match naming convention
- [I-001] InvoiceProcessor: ST-ANA-009 — 12 file activities detected
- [W-004] ClassifierAgent: Missing tool description for 'lookup_customer'
```

> The validation results section is **required** in every review report. A review without automated validation is incomplete.

### Step 3 — Manual Quality Review

For **each** project (one for single-project, all for solution/multi-project), load the relevant checklist from `references/` based on the type classified in Step 1. Read project files, check patterns, evaluate design.

#### 3a. Unit of Work Discovery (mandatory, generic)

Every project has two units of work: what the **contract** declares one invocation represents, and what the **execution body** actually does. A mismatch is a Critical-to-Warning finding regardless of project type. Do not ask the user — derive both mechanically from the project.

**Step 3a.1 — Discover the declared unit of work** (per project type):

| Project type | Where the declared unit lives |
|---|---|
| RPA + queue | Queue item schema (`Data/*.json`, `JSON Schema/`, or the SpecificContent fields used by `Add Queue Item` / `Get Transaction Item`) |
| RPA without queue | `Main.xaml` input arguments |
| Flow | `.flow` file → `variables.globals` → entries with `direction: "in"` or `"inout"` |
| Agent (low-code) | `agent.json` → `inputSchema` |
| Agent (coded) | `Input` class in `main.py` (Pydantic `BaseModel`) |
| API workflow | Request schema defined in the workflow |
| Coded app | Entry point input schema in `operate.json` / `entry-points.json` |

**Step 3a.2 — Discover the actual unit of work** (core execution body):

Identify the core execution file (`ProcessTransaction.xaml`, `Process.xaml`, `Main.xaml`, `main.py`, flow body, API handler) then run these mechanical checks:

```bash
# Detect iteration inside the execution body
grep -n 'ForEach\|While' <EXECUTION_FILE>

# Detect external-effect activities (writes, API calls, queue pushes, workflow invocations)
grep -n 'HttpRequest\|Add Queue Item\|InvokeWorkflowFile\|Write Range\|Write Line\|SqlCommand' <EXECUTION_FILE>
```

For coded projects, look for `for` / `foreach` / `while` statements and external I/O calls.

**Step 3a.3 — Classify using this matrix:**

Classify the **Transaction Shape** using this matrix. Shape is a neutral description of the relationship between input and external effects — it is NOT a pass/fail verdict.

| Actual execution pattern | Transaction Shape |
|---|---|
| One invocation → one atomic external state change (one write, one submission, one workflow call) | **One-to-one** |
| Execution iterates over an array/collection field of the declared input, and the loop body contains external effects (see list below) | **One-to-many** |
| Iteration only over retry counters, UI element enumeration, or pure in-memory transformations (no external effects in loop body) | **One-to-one** (in-memory iteration is intra-unit; not a sub-unit of work) |
| No iteration at all | **One-to-one** |
| Contract or execution cannot be deterministically mapped (schema missing/unclear, dynamic dispatch) | **Unclear** |

**External effects inside a loop body that make it one-to-many** (none of these are defeated by session scope, shared credentials, single portal, or business-model arguments):

- `InvokeWorkflowFile` / `Invoke Method` to workflows with external side effects
- HTTP activities (`HTTP Request`, connector activities, REST calls)
- Queue operations (`Add Queue Item`, `Set Transaction Progress`, `Set Transaction Status`)
- Database writes (`Execute Non Query`, `Insert Data Table`, `Bulk Insert`)
- File writes outside `Temp/` directories (`Write Range`, `Write CSV`, `Append to File`)
- UI activities that modify target-system state (Click on submit/save, Type Into fields that persist, SAP `Call Transaction`)
- Email send activities

Classification is mechanical. It does not change based on:
- "The portal models this as one transaction" (UX framing ≠ atomicity)
- "One browser session" (session ≠ transaction)
- "Idempotency guards exist so it's fine" (guards are a remediation signal, not a reclassifier)
- "The PDD calls it one transaction" (declared intent ≠ execution reality)
- "The queue only has one item" (queue is the declared unit; actual unit is what gets written)

**Step 3a.4 — Record shape, then separately assess remediation.**

The shape itself is reported neutrally. Whether it becomes a finding — and at what severity — depends on remediation posture:

**For One-to-one:** No finding. Report the shape observation in Summary, move on.

**For One-to-many:** Assess two separate questions.

*Question A — Can the sub-units be independently queued / split?*
- Yes: the proper fix is dispatcher/performer — split the queue so each sub-unit is an atomic transaction. Use this when sub-units are independent (one invoice, one employee record, one order, one file).
- No: the domain forces a sequential session-bound submission (SAP new-plan enrollment, carrier portal group application, bank multi-step wire). Queue splitting is infeasible. The fix is not architectural — it is operational: verify atomicity, error handling, crash recovery, and progress tracking using the **10-point hardening checklist** in [rpa-common-issues.md](references/rpa/rpa-common-issues.md) → "When it cannot be split — hardening checklist." Each missing safeguard is a separate finding.

*Question B — What partial-failure recovery exists today?*

Look for any of these patterns (semantically, not by filename):

| Pattern | Detection |
|---|---|
| Read-check-before-write before each sub-unit write | Inspect activity sequence in the loop body |
| Conditional skip based on "already exists/processed" state | Inspect If/Switch branches wrapping writes |
| Orchestrator queue dedup via `UniqueReference` | Check `Add Queue Item` properties |
| SQL idempotent writes (`MERGE`, `ON CONFLICT`, `UPSERT`, `WHERE NOT EXISTS`) | Grep SQL statements |
| HTTP idempotency (`Idempotency-Key` header, ETag `If-Match` / `If-None-Match`) | Check HTTP Request headers |
| Status-column filters (`WHERE Status != 'Processed'`) | Grep queries |
| Pre-check workflow invocation (names often contain `check`/`verify`/`exists`/`processed`/`already`/`skip`/`idempoten` — one of many forms, not the only signal) | Inspect invoked workflow names and bodies |
| Per-sub-item progress written to queue `Output` / Data Service / external state | Inspect what's persisted during the loop |

**Severity and finding framing:**

| Scenario | Severity | Finding framing |
|---|---|---|
| One-to-many + sub-units splittable + no idempotency guards + `MaxRetryNumber` < 2 | **Critical** | "Transaction granularity: split into dispatcher/performer. Current architecture risks partial-state corruption on transient failure." |
| One-to-many + sub-units splittable + idempotency guards exist but progress/output fidelity weak | **Warning** | "Transaction granularity: consider dispatcher/performer split for better analytics and retry isolation." |
| One-to-many + sub-units NOT splittable (domain constraint) + missing safeguards | **Warning–Critical** | "Cannot be split — run the 10-point hardening checklist in [rpa-common-issues.md](references/rpa/rpa-common-issues.md) → 'When it cannot be split.' Report each missing safeguard as a separate finding." |
| One-to-many + splittable + guards + retry + per-sub-item output | Info (tech debt) | "Transaction granularity: working with compensation; consider dispatcher/performer if volume grows." |
| Unclear | Info | "Unit of work ambiguous — schema/code documentation gap." |

The shape observation belongs in the **Executive Summary** of the report as a one-liner (see Step 5). Any finding generated from the shape analysis becomes a normal numbered finding in the Critical/Warning/Info sections — not a separate "Unit of Work Analysis" block.

#### 3b. PDD Alignment Review (if PDD is available)

If a PDD was found or provided in Step 0, use it as the **primary benchmark** for the manual review. For each project, verify:

| PDD Section | What to Check | Severity if Mismatched |
|---|---|---|
| Business process description | Does the implementation match the described process flow? | Warning |
| Expected inputs/outputs | Do workflow arguments match PDD-defined inputs and outputs? | Warning |
| Exception handling requirements | Are Business Exceptions thrown for the cases the PDD defines? Are retries configured per PDD specs? | Warning |
| Application list | Are all applications from the PDD automated? Any missing? Any extras not in PDD? | Warning |
| Transaction definition | Does the transaction item structure match the PDD? | Warning |
| Queue specifications | Queue names, retry counts, SLAs match PDD? | Warning |
| Credential requirements | Are all credentials from PDD stored securely (assets/vault)? | Critical if hardcoded |
| SLAs and performance targets | Does the automation design support PDD-defined throughput/timing? | Info |
| Happy path + exception scenarios | Are all PDD-documented scenarios handled? | Warning |
| Out of scope items | Does the automation stay within PDD-defined scope? | Info |

**Report PDD mismatches** as a dedicated section in the review report. A technically sound automation that doesn't match its PDD is still a problem.

If no PDD is available, skip this sub-step and note in the report:
> **Note:** No PDD was available for this review. Business logic alignment could not be verified. This review covers technical quality and best practices only.

#### 3c. Technical Quality Review

For **each** project, load the type-specific checklist:

For **Solution / Multi-project scope**, also perform solution-level checks from [references/solution-review-guide.md](references/solution-review-guide.md):
- Solution structure validation (.uipx, config.json, orphan projects) — **skip `.uipx` checks if any detected executable is Windows-Legacy; recommend migration instead**
- Cross-project dependency checks
- Configuration consistency across projects
- Multi-project architecture pattern assessment

For deep-dive RPA reviews, also consult:
- RPA (advanced): [rpa-advanced-checklist.md](references/rpa/rpa-advanced-checklist.md) — project organization, selector robustness, variable hygiene, data patterns, error handling depth, testing maturity, idempotency
- RPA (long-running): [long-running-workflow-issues.md](references/rpa/long-running-workflow-issues.md) — load when project uses persistence activities (`Suspend`, `Wait and Resume`, `Create Form Task`, Orchestration Process type)
- RPA (Modern Studio): [modern-studio-issues.md](references/rpa/modern-studio-issues.md) — load for Studio 2024.10+ projects (Modern vs Classic mixing, coded/XAML interop, Object Repository, Data Manager, Healing Agent)
- Document Understanding: [du-review-checklist.md](references/document-understanding/du-review-checklist.md) — load when DU packages detected in `project.json` dependencies

For common antipatterns per project type, also consult:
- RPA: [rpa-common-issues.md](references/rpa/rpa-common-issues.md)
- Agents: [agent-common-issues.md](references/agents/agent-common-issues.md)
- Flows: [flow-common-issues.md](references/flows/flow-common-issues.md)

### Step 4 — Evaluate Optimization

Only after validation (Step 2) and manual review (Step 3) are complete, evaluate optimization.

**Solution / Multi-project scope** — evaluate cross-project concerns:
- **Architecture:** Is the multi-project design appropriate (dispatcher/performer, main + libraries, flow + resources)?
- **Cross-project dependencies:** Are library versions pinned? Any circular dependencies?
- **Queue usage:** Should this solution use queues for work distribution?
- **Bulk operations:** Are there loops that could use bulk APIs?
- **Transaction handling:** Is error recovery and retry properly implemented across projects?
- **Resource efficiency:** Are there redundant API calls, excessive logging, or unnecessarily large files?
- **Configuration consistency:** Do all projects use the same pattern for configuration (assets, config.json)?

**Single Project scope** — evaluate within-project optimization:
- **Queue usage:** If processing >50 independent items, should this use queues?
- **Bulk operations:** Are there loops with individual API calls that could be batched?
- **Transaction handling:** Is REFramework or equivalent retry logic needed?
- **Resource efficiency:** File sizes, logging volume, selector efficiency, data handling patterns

Read [references/review-workflow-guide.md](references/review-workflow-guide.md) for the full optimization evaluation criteria.

Read [references/architecture-assessment-guide.md](references/architecture-assessment-guide.md) for the architecture-level evaluation framework — process suitability, complexity classification, environment separation, and architecture principles scoring.

### Step 5 — Produce the Review Report

Output a structured report in chat (do NOT create a file):

**Report rules — do not violate:**

1. NEVER use internal workflow labels in the output. Forbidden terms: "Path A", "Path B", "Step 3a", "Step 0c", "Mismatch"/"Aligned" (use "one-to-one" / "one-to-many" / "unclear"), "disqualifying criteria", "verdict". The report is for the user, not a trace of the skill's internal workflow.
2. Do NOT create a separate "Unit of Work Analysis" section. The shape observation is a one-liner in the Summary. If the shape analysis produces a concern, it becomes a normal numbered finding.
3. Size metrics per file type use **activity / variable / node counts**, not "lines". Lines are meaningless for XAML and misleading for any file. See "Structural Metrics" table below.
4. Validation Status for Legacy projects says "Use `uipath-rpa-legacy` skill for Legacy-specific validation" — it does NOT say "Could not run" or "Failed". Legacy is supported indefinitely in Studio LTS; the `uip rpa` CLI targets Modern projects.

**Structural metrics to report (never "lines"):**

| File type | Metrics to use |
|---|---|
| `.xaml` | Activity count, max nesting depth, root-scope variable count, argument count, invoke-workflow count |
| `.cs` (coded workflow) | Method count, statement count (LOC excluding blank/comment), class count |
| `.flow` | Node count, gateway count, longest path depth, subflow count |
| `.py` (coded agent) | Function count, statement count, import count |
| Config (JSON/XLSX) | Entry count, nesting depth |

**Required report structure:**

```markdown
## Review Report: <Project or Solution Name>

### Summary
- **Overall Quality:** Good / Needs Improvement / Critical Issues
- **Business Value:** <1-2 sentence description of what this automation does>
- **Review Scope:** Single project / Solution (N projects) / Multi-project repo (N executables + M libraries)
- **Project Types Found:** <list with type and language, e.g., "RPA (XAML, VisualBasic)", "Agent (Coded, Python)">
- **Validation Status:** <per project: pass with counts, or "Validation via uipath-rpa-legacy skill" for Legacy>
- **PDD Available:** Yes (path) / No — business logic alignment not verified
- **Transaction Shape:** <one line per project, e.g., "Processes 1 invoice per invocation (one-to-one)." or "Processes 1 company per invocation; internally writes N employee enrollments (one-to-many) — see [W-002].">

### PDD Alignment (only if PDD was available)

| PDD Requirement | Implementation Status | Finding |
|---|---|---|
| ... | ... | ... |

> If no PDD: "No PDD was available for this review. Business logic alignment could not be verified."

### Automated Validation Results

| Project | File | Command | Errors | Warnings | Info |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

**Validation Details:**
- [V-E-001] <project>/<file>: **<rule-id>** — <message>
- ...

> For Legacy projects, note: "Validation CLI (`uip rpa get-errors`, `uip rpa analyze`) targets Modern projects. Legacy validation is available via the dedicated `uipath-rpa-legacy` skill."

### Critical Findings (block deployment)
1. [C-001] <concise title> — `<project/file>` — <what to check + recommended fix>

### Warnings (should fix before production)
1. [W-001] <concise title> — `<project/file>` — <what to check + recommended fix>

### Improvement Opportunities
1. [I-001] <concise title> — `<project/file>` — <what to improve>

### Per-Project Summary
| Project | Type | Language | Size | Validation | Quality | Key Findings |
|---|---|---|---|---|---|---|
| ProjectA | RPA (Coded) | CSharp | 42 methods, 1,300 statements | 1 error, 2 warnings | Needs Work | V-E-001, W-001 |
| ProjectB | Flow | — | 18 nodes, 3 gateways, depth 5 | Pass | Good | I-001 |
| ProjectC | RPA (XAML) | VisualBasic | 84 activities, 50 vars, depth 12 | Via uipath-rpa-legacy | Needs Improvement | C-002, W-003 |

### Recommended Next Steps

Route each fix to the appropriate skill:

| Fix needed | Use skill |
|---|---|
| Fix RPA workflow / coded workflow / XAML / project.json | `uipath-rpa` |
| Fix RPA Windows-Legacy project | `uipath-rpa-legacy` |
| Fix agent (coded or low-code) | `uipath-agents` |
| Fix flow (.flow) | `uipath-maestro-flow` |
| Fix coded app | `uipath-coded-apps` |
| Fix Orchestrator resources (assets, queues, folders, deploy) | `uipath-platform` |

1. Fix [C-001] using `uipath-rpa` — change argument type to SecureString
2. ...

### Optimization Notes
- <queue usage, bulk operations, retry/idempotency observations — e.g., partial-failure handling for one-to-many shapes>
```

**Finding severity labels (never "Mismatch"/"Aligned"):**
- Overall Quality: `Good` / `Needs Improvement` / `Critical Issues`
- Transaction Shape: `one-to-one` / `one-to-many` / `unclear`
- Findings: `Critical` / `Warning` / `Info`

**Quality determination thresholds:**
- **Good** — 0 Critical, 0-3 Warnings
- **Needs Improvement** — 0 Critical, 4+ Warnings OR 1 Critical with clear fix
- **Critical Issues** — 2+ Critical OR 1 Critical with security/data-integrity implications

## Task Navigation

| I need to... | Read this |
|---|---|
| Understand the full review workflow in detail | [review-workflow-guide.md](references/review-workflow-guide.md) |
| Review a solution structure (.uipx) | [solution-review-guide.md](references/solution-review-guide.md) |
| Review an RPA project (coded or XAML) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| Find common RPA issues | [rpa-common-issues.md](references/rpa/rpa-common-issues.md) |
| Review an agent project | [agent-review-checklist.md](references/agents/agent-review-checklist.md) |
| Find common agent issues | [agent-common-issues.md](references/agents/agent-common-issues.md) |
| Review a flow project | [flow-review-checklist.md](references/flows/flow-review-checklist.md) |
| Find common flow issues | [flow-common-issues.md](references/flows/flow-common-issues.md) |
| Review a coded app | [coded-app-review-checklist.md](references/coded-apps/coded-app-review-checklist.md) |
| Review Orchestrator resources | [platform-resources-checklist.md](references/platform/platform-resources-checklist.md) |
| Deep-dive an RPA project | [rpa-advanced-checklist.md](references/rpa/rpa-advanced-checklist.md) |
| Review a long-running / Orchestration Process (persistence, Wait/Resume, Suspend) | [long-running-workflow-issues.md](references/rpa/long-running-workflow-issues.md) |
| Review Modern Studio (2024.10+) specific concerns (Modern vs Classic, coded/XAML interop, Object Repo, Healing Agent) | [modern-studio-issues.md](references/rpa/modern-studio-issues.md) |
| Review a Document Understanding project | [du-review-checklist.md](references/document-understanding/du-review-checklist.md) |
| Assess architecture and process suitability | [architecture-assessment-guide.md](references/architecture-assessment-guide.md) |
| Review source control / CI-CD / DevOps readiness (any project type) | [devops-readiness-checklist.md](references/devops-readiness-checklist.md) |

## Anti-Patterns — What NOT to Do

1. **Do not modify files.** This is a review skill, not a builder. Identify issues, recommend fixes, and tell the user which skill to use.
2. **Do not review without running automated validation first.** Manual review alone misses structural issues that CLI tools catch instantly.
3. **Do not skip solution-level discovery.** Reviewing a single project without understanding the solution context leads to wrong optimization recommendations (e.g., suggesting queues when the solution already has a dispatcher/performer pattern).
4. **Do not report validation errors as manual findings.** Reference the validation output — do not re-describe what the CLI already reported.
5. **Do not provide a review without severity ratings.** Every finding must be Critical, Warning, or Info. An undifferentiated list of issues is not actionable.
6. **Do not recommend architecture changes without understanding business context.** Ask about volume, frequency, SLA, and error tolerance before suggesting queue-based processing, parallel execution, or other architectural patterns.
7. **Do not attempt to fix issues yourself.** Report the issue, suggest the fix, name the skill that can apply it. Stop there.
8. **Do not flag Windows-Legacy compatibility as Critical.** Legacy is supported **indefinitely** in Studio LTS — 2024.10, 2025.10, 2026.10, and all future LTS releases continue to support creating, opening, editing, running, and deploying Legacy projects. It is NOT a deployment blocker and NOT a mid-term support risk. Deprecation means "no new features added to Legacy," not "Legacy will be removed." Flag as **Warning** (if the project would benefit from capabilities Legacy lacks — see [rpa-review-checklist.md §10](references/rpa/rpa-review-checklist.md) for ranked feature list) or **Info** (if Studio LTS is the organizational standard or SOAP web services are required). When recommending migration, lead with the 2-3 features most relevant to the project's actual pain (typically **Healing Agent**, **Unified Target / Modern UIA**, **Object Repository**, **ScreenPlay**, **coded test cases**, **Autopilot**, **Agents/Maestro**). Route Legacy-specific deep validation to the dedicated `uipath-rpa-legacy` skill.
