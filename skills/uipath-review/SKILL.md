---
name: uipath-review
description: "UiPath read-only reviewer — audit structure, quality, best practices for RPA (.xaml/.cs), agents (.py/agent.json), flows (.flow), BPMN (.bpmn), coded apps, solutions (.uipx). Does NOT edit files. For building/editing→domain skills."
allowed-tools: Bash, Read, Glob, Grep, WebFetch, AskUserQuestion
user-invocable: true
---

# UiPath Solution & Artifact Reviewer

Review UiPath solutions and artifacts for structural validity, quality, best practices, optimization, correctness, and business alignment. Produce a structured review report with findings and recommendations.

## When to Use

Use for requests to review, audit, check, evaluate, improve, quality-gate, or understand the business value or architecture of a UiPath project, solution, or artifact; artifact-type best-practice reviews; and inheritance of an existing solution.

## Critical Rules

1. **Read-only.** Never manually modify files. The sole exceptions are the CLI-owned writes of an agent review, `uip agent refresh` and `uip agent review-history add` ([agent-review-guide.md](references/agents/agent-review-guide.md)); they are mandatory; never restore or clean up what they change. Report fixes and route them to `uipath-rpa`, `uipath-agents`, `uipath-maestro-flow`, `uipath-maestro-bpmn`, `uipath-api-workflow`, `uipath-coded-apps`, `uipath-platform`, or `uipath-solution`.
2. **Validate first.** Every RPA entry point requires `uip rpa validate`, plus a project-level `uip rpa build` — `build` compiles the whole project, including entry points `validate` was never pointed at, so a clean per-file `validate` can still fail `build`. Use `uip maestro flow validate`, `uip maestro bpmn validate`, and `uip api-workflow validate` as applicable. Every CLI validation command uses `--output json`. Report each command's Error, Warning, and Info counts; detail every Error and Warning, but add no detail lines for clean results. A review without both RPA `validate` and `build` is incomplete.
3. Discover and classify every project before reviewing any project.
4. Classify findings as **Critical** (blocks deployment), **Warning** (should fix), or **Info** (improvement opportunity).
5. Establish or infer business context before optimization; queues and additional components are not automatically better.
6. Do not duplicate validation findings. Reference the output rule ID and message rather than restating checks or passes. Counts include all results; Errors and Warnings also receive detail lines.
7. Limit analysis to 30 minutes. For solutions with 10+ projects, provide a summary and deep dives for the three highest-risk projects, offering the remainder separately.
8. **Agent projects follow [agent-review-guide.md](references/agents/agent-review-guide.md).** Once Step 1 classifies a project as Agent (Low-Code) or Agent (Coded), read that guide and run its Critical Rules and Steps 2–6 for that project; the steps below apply to it only where the guide points back to them.
9. Put intended but unapplied rules in **Rules Skipped**, including missing tooling/files, unavailable review CLI, and `status: deferred`. Do not list non-applicable rules.

## Review Workflow

### Step 0 — Discover, Scope, and Locate the PDD

#### 0a. Probe the Filesystem

Run from the user-specified directory or current working directory, excluding managed build directories:

```bash
find . -maxdepth 3 \( -type d \( -name ".agent-builder" -o -path "*/.local/build" \) \) -prune -o \( -name "*.uipx" -o -name "project.json" -o -name "project.uiproj" -o -name "agent.json" -o -name "*.flow" -o -name "*.bpmn" -o -name "app.config.json" -o -name ".uipath" -o -name "pyproject.toml" -o -name "langgraph.json" -o -name "llama_index.json" -o -name "openai_agents.json" -o -name "uipath.json" -o -name "main.py" \) -print 2>/dev/null
find . -maxdepth 3 \( -type d \( -name ".agent-builder" -o -path "*/.local/build" \) \) -prune -o \( -name "*PDD*" -o -name "*pdd*" -o -name "*Process_Design*" -o -name "*process_design*" -o -name "*Process-Design*" -o -name "*ProcessDesign*" -o -name "*SDD*" -o -name "*Solution_Design*" -o -name "*design_document*" -o -name "*DesignDocument*" -o -name "*requirements*" -o -name "*specification*" \) -print 2>/dev/null
```

#### 0b. Locate and Use the PDD

The PDD is the source of truth for process behavior, business context, inputs/outputs, exceptions, SLAs, transactions, queues, applications, credentials, and success criteria. Search in order: `./docs/`, `./documentation/`, `./Design/`, project root; names containing `PDD.*`, `Process_Design_Document.*`, `SDD.*`, `Solution_Design_Document.*`, or `Requirements.*`; root `AGENTS.md` or `README.md`; then `project.json.description` and metadata. Read supported documents with appropriate tools and extract review criteria.

If none is found, use the `AskUserQuestion` tool to ask interactively (do not print the question as prose):

```text
Question: I could not find a Process Design Document (PDD) in this project. Do you have one I can use as the source of truth for this review?
Header: PDD
Options:
  1. Yes, I have a file — provide a path, URL, or Confluence/SharePoint link.
  2. I'll paste the content — provide the PDD or relevant sections.
  3. No, proceed without — review technical quality and best practices only; business-logic alignment cannot be verified.
```

Read supplied or pasted content; if declined, record the limitation. Use the PDD as the primary benchmark.

#### 0c. Determine Scope

Internal labels such as “Path A”, “Path B”, and “Step 3a” must not appear in the final report. Use the user-facing Review Scope vocabulary from Step 5.

**Solution/multi-project scope:** a root `.uipx`, or at least two executable project markers in different subdirectories. Executable markers are `project.json` with `outputType` Process/Tests/unspecified, low-code `agent.json`, coded-agent Python (`pyproject.toml` plus framework or `uipath.json` configuration), `.flow`, or `project.uiproj` with `ProjectType` Flow/ProcessOrchestration/Api. Libraries (`outputType: Library`) do not trigger this scope. Windows-Legacy executables do not trigger `.uipx` scope; do not flag missing `.uipx`, and recommend Modern migration only when solution bundling is desired.

For solution scope, read `.uipx`; find orphan executables; classify all projects; check `config.json`, versions, dependencies, circular dependencies, and cross-project relationships; build a project map; cross-reference the PDD; read [references/solution-review-guide.md](references/solution-review-guide.md); then review each project.

**Single-project scope:** one root project marker, no `.uipx`, and no executable siblings. Classify it, cross-reference the PDD, skip solution checks, and proceed. If given a file, walk upward to its enclosing project and review the full project.

### Step 1 — Classify Project Type and Language

For every project, read `project.json.expressionLanguage` for RPA (`VisualBasic` or `CSharp`) and adapt expression, null/type, string, LINQ, naming, and Unit of Work checks; never assume VB.

| Signal | Type | Checklist/catalog |
|---|---|---|
| `project.json` + `.cs` with `[Workflow]` | RPA (Coded) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| `project.json` + `.xaml` | RPA (XAML) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| absent `targetFramework` or `Legacy` | RPA (Windows-Legacy) | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) §10; recommend `uipath-rpa` Legacy mode |
| both `.cs` and `.xaml` | RPA (Hybrid) | RPA checklist |
| DU packages `UiPath.IntelligentOCR.Activities` or `UiPath.DocumentUnderstanding.ML.Activities` | RPA + Document Understanding | RPA + [du-review-checklist.md](references/document-understanding/du-review-checklist.md) |
| `agent.json.type == lowCode` | Agent (Low-Code) | [agent-review-guide.md](references/agents/agent-review-guide.md) |
| Python coded-agent signals, including `agent.json.type == coded` | Agent (Coded) | [agent-review-guide.md](references/agents/agent-review-guide.md) |
| `*.flow` + `project.uiproj.ProjectType == Flow` | Flow | [flow-review-checklist.md](references/flows/flow-review-checklist.md) |
| `*.bpmn` + `ProjectType == ProcessOrchestration` | Maestro BPMN | [bpmn-review-checklist.md](references/bpmn/bpmn-review-checklist.md) |
| `Workflow.json` with `document.dsl` and `do[]` + `ProjectType == Api` | API Workflow | [api-workflow-review-checklist.md](references/api-workflows/api-workflow-review-checklist.md) |
| `.uipath/` or `app.config.json` | Coded App | [coded-app-review-checklist.md](references/coded-apps/coded-app-review-checklist.md) |

For solutions, record path, type, language, and entry points. Inventory authored files, excluding managed/build/dependency directories:

```bash
find "<PROJECT_DIR>" \( -type d \( -name ".agent-builder" -o -path "*/.local/build" -o -name "node_modules" -o -name ".venv" -o -name "obj" -o -name "bin" \) \) -prune -o -type f -print 2>/dev/null | sort
```

Only this authored-file set is in scope for reading, citation, and metrics.

### Step 2 — Run Automated Validation and Workflow Analyzer

Run commands yourself before manual review, for every project and every RPA entry point. Record all results.

#### 2a. RPA

Read `entryPoints` from `project.json` and run each:

```bash
uip rpa validate --file-path "<ENTRY_FILE>" --project-dir "<PROJECT_DIR>" --output json
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

Any entry-point validation error or project build failure means the project is not deployable. Do not validate only `Main.xaml`.

#### 2b. Workflow Analyzer

```bash
uip rpa analyze --project-dir "<PROJECT_DIR>" --output json
```

If unavailable, use Analyzer results included by `uip rpa validate`. Report every violation: Error as Critical, Warning as Warning, and Info as Info, preserving rule ID, file, and description. Examples include ST-SEC-007, ST-ANA-005, ST-DBP-003, ST-MRD-011, ST-NMG-001, ST-ANA-003, and ST-ANA-009 when emitted.

#### 2c. Other Types

| Type | Command |
|---|---|
| Flow | `uip maestro flow validate "<PROJECT_NAME>.flow" --output json` |
| Maestro BPMN | `uip maestro bpmn validate "<FILE>.bpmn" --output json` |
| API Workflow | `uip api-workflow validate "<WORKFLOW_JSON>" --output json` |
| Coded App | `uip codedapp pack dist --dry-run --output json` |
| Solution | `uip solution pack "<SOLUTION_DIR>" "<OUTPUT_DIR>" --output json` |

Report all severities. API workflow validation is offline; never run `uip api-workflow run`. If older CLI versions lack BPMN or API validation, record unavailable rules under Rules Skipped and use the relevant checklist.

#### 2d. Validation Results

Every report includes:

```markdown
### Automated Validation Results

| Project | Command | Errors | Warnings | Info |
|---|---|---:|---:|---:|
| ... | ... | ... | ... | ... |

#### Validation Details
- [V-E-001] <file>: <rule ID> — <message>
- [V-W-001] <file>: <rule ID> — <message>
```

Include counts for every command. Detail Errors and Warnings only. Do not narrate clean results, passes, zero issues, drift status, scores, regeneration counts, or schema status; the table is sufficient.

### Step 3 — Manual Quality Review

For each project, load its type-specific checklist and inspect only authored files.

#### 3a. Unit of Work Discovery

Derive both the declared contract unit and actual execution unit; do not ask the user. A mismatch is Critical-to-Warning regardless of type.

| Type | Declared unit location |
|---|---|
| RPA with queue | Queue schema or fields used by `Add Queue Item`/`Get Transaction Item` |
| RPA without queue | `Main.xaml` input arguments |
| Flow | `.flow.variables.globals` entries with `in`/`inout` direction |
| Maestro BPMN | Start-event payload/process inputs |
| API workflow | `Workflow.json` request schema |
| Coded app | Entry-point schema in `operate.json`/`entry-points.json` |

Find the core execution body and inspect iteration and effects:

```bash
grep -n 'ForEach\|While' <EXECUTION_FILE>
grep -n 'HttpRequest\|Add Queue Item\|InvokeWorkflowFile\|Write Range\|Write Line\|SqlCommand' <EXECUTION_FILE>
```

For coded projects inspect `for`, `foreach`, `while`, and external I/O. Classify:

| Pattern | Shape |
|---|---|
| One invocation causes one atomic external state change | one-to-one |
| Loop over an input collection with external effects in the loop | one-to-many |
| Retry/UI enumeration/in-memory-only loop | one-to-one |
| No loop | one-to-one |
| Contract or execution cannot be mapped deterministically | unclear |

Side effects making a loop one-to-many include invoked side-effect workflows, HTTP/connectors, queue operations (`Add Queue Item`, `Set Transaction Progress`), database writes (`Execute Non Query`, `Insert Data Table`, `Bulk Insert`), non-temporary file writes (`Write Range`, `Write CSV`, `Append to File`), state-changing UI actions (Click submit/save, persistent Type Into, SAP `Call Transaction`), and email sends. Session scope, shared credentials, one portal, PDD wording, idempotency, or queue size do not reclassify the shape.

For one-to-many, determine whether sub-units can be independently queued. If yes, recommend dispatcher/performer splitting. If no, use the 10-point hardening checklist in [rpa-common-issues.md](references/rpa/rpa-common-issues.md) under “When it cannot be split — hardening checklist”; report each missing safeguard separately. Check read-before-write, conditional skips, `UniqueReference`, SQL `MERGE`/`ON CONFLICT`/`UPSERT`/`WHERE NOT EXISTS`, HTTP idempotency headers, status filters, pre-check workflows, and per-sub-item progress.

Severity: splittable with no guards and `MaxRetryNumber < 2` is Critical; splittable with guards but weak progress/output is Warning; unsplittable missing safeguards is Warning–Critical; splittable with guards, retry, and per-item output is Info; unclear mapping is Info. Report one Transaction Shape summary line per project and never create a separate Unit of Work Analysis section.

#### 3b. PDD Alignment

When available, compare business process, inputs/outputs, exceptions/retries, applications, transaction definition, queues, credentials, SLAs/performance, happy-path and exception scenarios, and out-of-scope items. Mismatches are generally Warning; hardcoded credentials are Critical; SLA/performance and out-of-scope concerns are Info. Use a dedicated PDD Alignment section. Without a PDD, state: “No PDD was available for this review. Business logic alignment could not be verified. This review covers technical quality and best practices only.”

#### 3c. Technical Review

Load the applicable checklist. For solutions also read [solution-review-guide.md](references/solution-review-guide.md) for `.uipx`, `config.json`, orphan, dependency, consistency, and architecture checks. Skip `.uipx` checks for Windows-Legacy executables and recommend migration instead.

Consult as applicable: [rpa-advanced-checklist.md](references/rpa/rpa-advanced-checklist.md); [long-running-workflow-issues.md](references/rpa/long-running-workflow-issues.md) for persistence activities or Orchestration Process; [modern-studio-issues.md](references/rpa/modern-studio-issues.md) for Studio 2024.10+; [du-review-checklist.md](references/document-understanding/du-review-checklist.md) when DU packages are present; [rpa-common-issues.md](references/rpa/rpa-common-issues.md); and [flow-common-issues.md](references/flows/flow-common-issues.md).

### Step 4 — Evaluate Optimization

Only after validation and manual review, assess business suitability, architecture, dependencies, queue usage, bulk operations, transaction/error recovery, redundant calls, logging, selectors, files, data handling, configuration consistency, environment separation, and performance. For solutions assess cross-project architecture, pinned libraries, circular dependencies, dispatcher/performer suitability, and shared configuration. For single projects assess queues for more than 50 independent items, batching, REFramework/equivalent retry, resource efficiency, and selector/data patterns. Read [review-workflow-guide.md](references/review-workflow-guide.md) and [architecture-assessment-guide.md](references/architecture-assessment-guide.md).

### Step 5 — Produce the Review Report

Write the report in chat; **and when the task asks you to save it to a path (e.g. `./_review_report.md`), also write it to that exact path** (≥500 bytes). The read-only rule forbids creating or editing files **inside the project under review** — it does NOT forbid writing the requested report file. Do not use internal labels such as “Path A”, “Path B”, “Step 3a”, or “Step 0c”; do not use “Mismatch”, “Aligned”, “disqualifying criteria”, or “verdict”. Use one-to-one, one-to-many, or unclear. Do not create a Unit of Work Analysis section.

Required sections, in order:

1. `## Review Report: <name>`
2. `### Summary` — render as a **bullet list, not a table**. Bullets: Overall Quality; Business Value; Review Scope; Project Types Found; Validation Status; PDD Available; Transaction Shape per project.
3. `### PDD Alignment` — only when a PDD is available.
4. `### Automated Validation Results` — counts table and Error/Warning details only.
5. `### Rules Skipped` — intended but unapplied rules only.
6. `### Critical Findings`, `### Warnings`, `### Improvement Opportunities` — one row per finding: `| <id> | <rule> | <file>: <issue>. <fix>. |`; use `—` when no `rule_id`; never duplicate or split findings by source.
7. `### Per-Project Summary` — Quality per project. Report size as structural counts, never lines: `.xaml` activity/nesting/variable/argument counts, `.cs` method/statement counts, `.flow` node/gateway/depth counts, `.py` function/statement/import counts, config entry/nesting counts.
8. `### Recommended Next Steps` — route fixes to the appropriate skill.
9. `### Optimization Notes` — only when relevant.

Agent projects add the Summary grade bullet, Grade column, and final-grade line from [agent-review-guide.md § Step 5](references/agents/agent-review-guide.md#step-5--report-additions).

Legacy validation status must say: `Use uipath-rpa (Legacy mode) for Legacy-specific validation`. Do not say “Could not run” or “Failed”. Legacy is supported indefinitely in Studio LTS and is not a Critical deployment blocker. Recommend migration based on actual needs. Overall Quality is **Good** for 0 Critical and 0–3 Warnings; **Needs Improvement** for 0 Critical and 4+ Warnings or 1 Critical with a clear fix; **Critical Issues** for 2+ Critical or 1 security/data-integrity Critical. Never use “Mismatch” or “Aligned”.

## Task Navigation

| Need | Reference |
|---|---|
| Agent review workflow | [agent-review-guide.md](references/agents/agent-review-guide.md) |
| Agent grade | [agent-grading-rubric.md](references/agents/agent-grading-rubric.md) |
| Rule schema | [rule-format.md](references/rule-format.md) |
| Review CLI/catalog workflow | [rule-catalog-workflow.md](references/rule-catalog-workflow.md) |
| Low-code catalog | [agents-lowcode-rules.md](references/agents/agents-lowcode-rules.md) |
| Coded catalog | [agents-coded-rules.md](references/agents/agents-coded-rules.md) |
| Full workflow | [review-workflow-guide.md](references/review-workflow-guide.md) |
| Solution | [solution-review-guide.md](references/solution-review-guide.md) |
| RPA | [rpa-review-checklist.md](references/rpa/rpa-review-checklist.md) |
| RPA common issues | [rpa-common-issues.md](references/rpa/rpa-common-issues.md) |
| Flow | [flow-review-checklist.md](references/flows/flow-review-checklist.md) |
| Flow common issues | [flow-common-issues.md](references/flows/flow-common-issues.md) |
| BPMN | [bpmn-review-checklist.md](references/bpmn/bpmn-review-checklist.md) |
| API workflow | [api-workflow-review-checklist.md](references/api-workflows/api-workflow-review-checklist.md) |
| Coded app | [coded-app-review-checklist.md](references/coded-apps/coded-app-review-checklist.md) |
| Platform resources | [platform-resources-checklist.md](references/platform/platform-resources-checklist.md) |
| RPA deep dive | [rpa-advanced-checklist.md](references/rpa/rpa-advanced-checklist.md) |
| Long-running workflow | [long-running-workflow-issues.md](references/rpa/long-running-workflow-issues.md) |
| Modern Studio | [modern-studio-issues.md](references/rpa/modern-studio-issues.md) |
| Document Understanding | [du-review-checklist.md](references/document-understanding/du-review-checklist.md) |
| Architecture | [architecture-assessment-guide.md](references/architecture-assessment-guide.md) |
| DevOps readiness | [devops-readiness-checklist.md](references/devops-readiness-checklist.md) |

## Anti-Patterns

1. **Never flag Windows-Legacy (absent or `Legacy` `targetFramework`) as a Critical issue** — the Legacy targetFramework itself is never a Critical finding or deployment blocker; it is supported indefinitely in Studio LTS. Flag Warning only when relevant capabilities are missing; otherwise Info. Recommend migration based on actual needs, especially Healing Agent, Unified Target/Modern UIA, Object Repository, ScreenPlay, coded test cases, Autopilot, or Agents/Maestro. Route deep validation to `uipath-rpa` Legacy mode. **On a clean Legacy project, do not let Overall Quality read as "Critical Issues" on account of the Legacy runtime, an incomplete/stubbed integration, or a design gap — those are Warnings unless you have concrete evidence of a shipped security or data-integrity defect. If you do cite a genuine Critical, its recommendation must state plainly that it is unrelated to the Windows-Legacy targetFramework** (never place the Legacy label and a Critical rating together without that disclaimer).
2. Do not recommend removing a dependency until usages have been searched and no consumers remain.
3. Do not flag `-preview` package versions; address stability through activity-owner channels rather than the user-facing report.
4. Do not run scripts or install Python packages. Deterministic checks belong in the review CLI; the skill ships no executable code.
