# Review Workflow Guide

Detailed reference for the end-to-end review process. The SKILL.md provides the quick workflow; this guide covers edge cases, decision criteria, and the optimization evaluation framework.

## PDD as Source of Truth

The **Process Design Document (PDD)** — also called Process Definition Document, Solution Design Document (SDD), or Requirements Specification — is the primary benchmark for the review. When available, the PDD defines:

- **Business process description** — what the automation should do, step by step
- **Expected inputs and outputs** — data types, formats, sources, destinations
- **Exception handling requirements** — which errors are business exceptions vs system exceptions, retry counts, escalation paths
- **Applications and systems involved** — which apps are automated, login requirements
- **Transaction definition** — what constitutes one transaction, queue item structure
- **Queue specifications** — queue names, retry config, SLAs, priority rules
- **Credential requirements** — which credentials are needed, storage requirements
- **SLAs and performance targets** — throughput, processing time, availability windows
- **Happy path and exception scenarios** — all documented paths through the process
- **Out of scope items** — what the automation should NOT do

### How PDD Drives Each Review Step

| Review Step | Without PDD | With PDD |
|---|---|---|
| **Classification** | Classify by filesystem signals only | Verify project type matches PDD design |
| **Validation** | Run CLI tools, report all findings | Same + verify entry points match PDD process list |
| **Manual Review** | Technical checklist only | Technical checklist + PDD alignment verification |
| **Optimization** | Evaluate patterns against general best practices | Evaluate patterns against PDD's volume/SLA/business requirements |
| **Report** | Technical quality report | Technical quality + business alignment report |

### PDD Formats

PDDs come in many formats. The review skill can read:
- **Markdown (.md)** — read directly
- **PDF (.pdf)** — read via Read tool (supports PDF)
- **Text (.txt)** — read directly
- **Word (.docx)** — ask the user to provide a plain-text or PDF version, or summarize the key sections

### PDD Traceability Matrix

When a PDD is available, build a traceability matrix that maps every PDD requirement to its implementation artifact. Include this in the review report under the PDD Alignment section.

```markdown
| # | PDD Requirement | Project | File / Element | Status | Finding |
|---|---|---|---|---|---|
| 1 | Extract invoice data from PDF | InvoiceProcessor | ExtractData.xaml → ML Extractor | Implemented | — |
| 2 | Validate amount against threshold | InvoiceProcessor | ValidateInvoice.xaml → If branch | Implemented | — |
| 3 | Send rejection email | InvoiceProcessor | — | **Missing** | [P-001] |
| 4 | Log to audit database | InvoiceProcessor | Process.xaml → SQL Insert | Implemented | Schema differs from PDD |
| 5 | Retry 3x on app failure | InvoiceProcessor | Config.xlsx → MaxRetryNumber=2 | **Mismatch** | [P-002] PDD says 3 |
```

**Status values:** Implemented, Missing, Mismatch, Partial.

Every "Missing" or "Mismatch" becomes a numbered finding in the report. This matrix makes gaps visible at a glance — a project can pass every technical check and still fail to deliver what was designed.

### When PDD Is Missing

If no PDD exists and the user cannot provide one:
1. Note this limitation prominently in the report
2. Focus on technical quality, best practices, and structural correctness
3. Cannot verify: business logic alignment, exception scenario coverage, SLA feasibility, correct transaction definition
4. Flag as **Info**: "No PDD available — business logic alignment not verified"

## Review Scope Determination

### Filesystem Probes

Run these commands to detect what exists in the target directory:

```bash
# Detect solution files
find . -maxdepth 1 -name "*.uipx" 2>/dev/null

# Detect all project types
find . -maxdepth 3 -name "project.json" -o -name "agent.json" -o -name "*.flow" -o -name "app.config.json" -o -name "project.uiproj" 2>/dev/null

# Detect coded agent markers
find . -maxdepth 2 \( -name "langgraph.json" -o -name "llama_index.json" -o -name "openai_agents.json" -o -name "uipath.json" \) 2>/dev/null
```

### Scope Decision Tree

1. `.uipx` file found at root → **Solution review** (includes all contained projects)
2. Multiple `project.json` / `agent.json` / `.flow` files in subdirectories, no `.uipx` → **Multi-project review** (treat as informal solution)
3. Single `project.json` / `agent.json` / `.flow` at root → **Single project review**
4. User specifies a single file path → **Single file review** (still check project context)
5. None of the above → Ask the user to specify the target directory

## Project Type Detection — Edge Cases

### Hybrid RPA Projects

A project with both `.cs` and `.xaml` files is hybrid. To determine the primary mode:

1. Read `project.json` → check `expressionLanguage` field
2. Count `.cs` files with `[Workflow]` attribute vs `.xaml` workflow files
3. Check `main` field in `project.json` — if it points to `.xaml`, XAML is primary
4. The minority mode is supplementary (coded utilities in a XAML project, or XAML UI automation in a coded project)

### Mono-Repo Structures

Some teams place multiple unrelated projects in a single repository without a `.uipx` solution file:

1. Each subdirectory with a `project.json` or `agent.json` is an independent project
2. Review each independently
3. Note the lack of solution packaging as an **Info** finding — suggest creating a `.uipx` if projects are related

### Nested Solutions

Rarely, a directory may contain nested `.uipx` files:

1. Identify the top-level `.uipx` as the primary solution
2. Flag nested `.uipx` as a **Warning** — nested solutions cause packaging conflicts

## Validation Command Reference

> **You MUST run these commands yourself via Bash.** Do not just list them — execute them, parse the output, and include every Error, Warning, and Info result in the review report.

### RPA Validation and Workflow Analyzer

The `uip rpa get-errors` command performs both structural validation AND Workflow Analyzer rule checks. Run it on **every entry point file**, not just Main.xaml.

**Step 1 — Discover all entry points:**

```bash
# Read project.json to get all entry points
cat "<PROJECT_DIR>/project.json" | python3 -c "import json,sys; d=json.load(sys.stdin); [print(e['filePath']) for e in d.get('entryPoints',[])]"
```

**Step 2 — Validate each entry point:**

```bash
# Run for EACH entry point file discovered above
uip rpa get-errors --file-path "<ENTRY_FILE>" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

**Step 3 — Report ALL results:**

Every result must appear in the review report, categorized by severity:
- `"severity": "Error"` → report as **Critical** (blocks deployment)
- `"severity": "Warning"` → report as **Warning** (should fix)
- `"severity": "Info"` → report as **Info** (improvement opportunity)

Include the Workflow Analyzer rule ID (e.g., ST-NMG-001, ST-DBP-003, ST-SEC-007) when present.

**Expected output (success):**
```json
{
  "errors": []
}
```

**Expected output (failures):**
```json
{
  "errors": [
    {
      "filePath": "Main.xaml",
      "activityId": "ActivityId",
      "message": "Error description",
      "severity": "Error"
    }
  ]
}
```

**Interpret results:**
- `severity: "Error"` → maps to **Critical** in review report
- `severity: "Warning"` → maps to **Warning** in review report
- 0 errors does not mean the project is correct — runtime testing (`run-file`) catches logic errors

### Agent Validation

```bash
# Low-code agent
uip agent validate ./agent-directory --output json

# Coded agent — check if eval sets exist first
ls evaluations/eval-sets/*.json 2>/dev/null
# If eval sets exist:
uip codedagent eval main evaluations/eval-sets/smoke-test.json --no-report
```

### Flow Validation

```bash
uip flow validate <ProjectName>.flow --output json
```

**Checks performed by the CLI:**
- JSON schema compliance
- Node/edge reference integrity (all nodeIds must exist)
- Unique IDs (node and edge IDs)
- Port validation (every edge must have targetPort)
- Definition completeness (every node type must have a matching definitions entry)

### Coded App Validation

```bash
# Check build output exists
ls dist/ 2>/dev/null

# Dry-run pack to verify packaging
uip codedapp pack dist --dry-run
```

### Solution Validation

```bash
uip solution pack <SOLUTION_DIR> <OUTPUT_DIR> --output json
```

## Quality Dimensions

Every review evaluates five dimensions. Not all dimensions apply equally to every artifact type.

### 1. Structural Validity

Are all required files present, correctly formatted, and schema-compliant?

| Artifact | Required Files | Schema Validation |
|---|---|---|
| RPA | `project.json`, entry point file (.xaml or .cs) | `uip rpa get-errors` |
| Agent (Low-Code) | `agent.json` | `uip agent validate` |
| Agent (Coded) | `main.py`, framework config, `pyproject.toml` | Import check + eval |
| Flow | `.flow`, `project.uiproj` | `uip flow validate` |
| Coded App | `package.json`, `.uipath/`, build output | `uip codedapp pack --dry-run` |
| Solution | `.uipx`, project subdirectories | `uip solution pack` |

### 2. Best Practices Adherence

Does the project follow established patterns and conventions?

- Naming conventions (files, variables, arguments)
- Code organization (separation of concerns, modularity)
- Error handling patterns (retry, try-catch, transaction)
- Testing coverage (test cases, evaluation sets)
- Documentation (comments where non-obvious, README)

### 3. Performance and Optimization

Is the project efficient for its intended scale?

- File sizes (XAML <500KB, >5MB is critical)
- API call patterns (batching vs. per-item)
- Queue usage for distributed work
- Selector efficiency (stable selectors, no wildcards)
- Logging volume (sufficient for debugging, not excessive)

### 4. Maintainability

Can another developer understand and modify this project?

- Code complexity (nesting depth, method length)
- Modularity (reusable components, clear interfaces)
- Consistency (naming, patterns, style)
- Test coverage (are changes verifiable?)
- Documentation (sufficient for onboarding)

### 5. Deployment Readiness

Is the project ready for production deployment?

- Dependencies pinned to specific versions
- Configuration externalized (no hardcoded URLs, credentials)
- Entry points correctly defined
- Packaging succeeds (`pack` commands work)
- Environment-specific configuration separated from logic

## Severity Classification Rules

### Critical (blocks deployment)

Use when the issue will cause the solution to **fail in production** or has **security implications**:

- Validation errors (CLI reports errors)
- Missing required files (project.json, agent.json, .flow entry)
- Hardcoded credentials or secrets
- Broken dependencies (missing packages, version conflicts)
- Security vulnerabilities (plaintext passwords, SQL injection, command injection)
- Circular dependencies between projects

### Warning (should fix before production)

Use when the issue **degrades quality** or will cause **maintenance problems**:

- Missing test cases or evaluation sets
- Oversized files (XAML >500KB but <5MB)
- Inconsistent naming conventions
- Missing error handling on external calls
- Outdated dependencies (not broken, but old)
- No retry logic for transient failures
- Hardcoded values that should be assets or configuration

### Info (improvement opportunity)

Use when the issue is a **missed optimization** or **minor convention deviation**:

- Unused variables or imports
- Suboptimal patterns (could use queues but works without them)
- Missing documentation or comments
- Minor naming inconsistencies
- Could benefit from subflows or code extraction
- Test coverage could be expanded

## Report Format Specification

The review report follows a fixed markdown structure. Produce it in chat — do NOT write it to a file.

```markdown
## Review Report: <Solution/Project Name>

### Summary
- **Overall Quality:** Good / Needs Improvement / Critical Issues
- **Business Value:** <1-2 sentence description of what this solution does>
- **Project Types Found:** <list with counts>
- **Validation Status:** <pass/fail per project>

### Automated Validation & Workflow Analyzer Results

> This section is MANDATORY. Every review must include the output of `uip rpa get-errors` (for RPA), `uip agent validate` (for agents), `uip flow validate` (for flows), etc. Report ALL Errors, Warnings, and Info.

| Project | File | Command | Errors | Warnings | Info |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

**Validation Details:**
- [V-E-001] Project/File: **ST-RULE-ID** — Description
- [V-W-001] Project/File: **ST-RULE-ID** — Description
- [V-I-001] Project/File: **ST-RULE-ID** — Description

### Critical Findings (blocks deployment)
1. [C-001] <finding title> — `<project/file path>` — <recommendation>
2. [C-002] ...

### Warnings (should fix before production)
1. [W-001] <finding title> — `<project/file path>` — <recommendation>
2. [W-002] ...

### Improvement Opportunities
1. [I-001] <finding title> — `<project/file path>` — <recommendation>
2. [I-002] ...

### Per-Project Summary
| Project | Type | Validation | Quality | Key Findings |
|---|---|---|---|---|
| ProjectA | RPA (Coded) | Pass | Good | W-001 |
| ProjectB | Flow | 2 errors | Needs Work | C-001, W-002 |

### Recommended Next Steps
1. Fix [C-001] using `uipath-rpa` skill
2. Add test cases using `uipath-rpa` skill
3. ...

### Optimization Notes
- Queue usage: <observation and recommendation>
- Bulk operations: <observation and recommendation>
- Transaction handling: <observation and recommendation>
```

**Overall Quality determination:**
- **Good** — 0 Critical findings, 0-3 Warnings
- **Needs Improvement** — 0 Critical findings, 4+ Warnings OR 1 Critical with clear fix
- **Critical Issues** — 2+ Critical findings OR 1 Critical with security implications

## Optimization Evaluation Framework

### When to Recommend Queues

Recommend queue-based processing when **all** of these apply:
1. The solution processes a collection of independent work items (invoices, orders, records)
2. Volume exceeds ~50 items per run OR items arrive continuously
3. Items can be processed independently (no ordering dependency)
4. Retry and audit trail per item are valuable

Do NOT recommend queues when:
- Volume is <20 items per run and runs are infrequent
- Items have ordering dependencies
- The entire batch must succeed or fail atomically
- The added complexity outweighs the reliability benefit

### When to Recommend Bulk Operations

Recommend bulk APIs when:
1. A loop makes individual API calls (e.g., creating queue items one by one)
2. The loop processes >10 items
3. A bulk/batch API exists for the operation

Detection pattern — look for:
- `ForEach` loops containing HTTP Request or Orchestrator API calls
- Script nodes inside `core.logic.loop` making individual API calls
- Python loops with individual `uipath.client` calls

### When to Recommend Transactions

Recommend transaction patterns (REFramework or equivalent) when:
1. Each work item must be tracked individually (success/failure/retry)
2. Partial failures should not block remaining items
3. Items need retry with exponential backoff or max-retry limits
4. Audit trail per item is required for compliance

### When to Flag Resource Inefficiency

Flag these patterns:
- **Redundant API calls:** Same data fetched multiple times without caching
- **Excessive logging:** `Log` calls inside tight loops or for every iteration
- **Oversized payloads:** Large DataTables or JSON objects passed between workflows when only a subset is needed
- **Unnecessary file I/O:** Reading/writing files in loops when in-memory processing suffices
- **Missing connection reuse:** Opening/closing application scopes repeatedly instead of wrapping loops

## Automation Type Assessment

When reviewing a solution, assess whether the right automation approach was chosen for each component:

### Automation Spectrum

| Type | Characteristics | When Appropriate | Flag If Misused |
|---|---|---|---|
| **Deterministic RPA** | Fixed rules, static paths, same input → same output | Structured data, predictable UI, high-volume batch | Used for ambiguous/unstructured tasks |
| **Rules-Based** | If-then-else, business rules engine, enumerable conditions | Known business rules, classification, routing | Rules are too complex to enumerate (should use agent) |
| **Non-Deterministic (Agent)** | LLM reasoning, dynamic planning, probabilistic | Ambiguous input, natural language, reasoning required | Used for simple deterministic tasks (overkill) |
| **Hybrid (Agentic Workflow)** | Agent reasons at decision layer, RPA executes actions | Complex processes mixing ambiguous and structured steps | All steps are deterministic (use pure RPA) |

### Project Variant Selection

Before reviewing implementation details, verify the project is using the right structural template. A project using the wrong variant creates friction throughout.

| Signal | Expected Variant | Flag If Wrong |
|---|---|---|
| Reads data from source, creates queue items, does NOT process them | **Dispatcher** (linear, no REFramework needed) | Warning if using REFramework — dispatcher is simple sequential |
| Reads queue items, processes one per invocation, retries on failure | **Performer** (REFramework) | Warning if linear without retry |
| Reads data AND processes each item in the same project | **Dispatcher + Performer combined** or **Single REFramework project** | Info — consider splitting for scalability |
| One-shot execution, no iteration, no queue | **Linear Sequence** | Warning if forced into REFramework (adds complexity for no benefit) |
| Long-running, multi-actor, human approvals needed | **Maestro flow** (or long-running workflow with Suspend) | Warning if using REFramework for HITL |
| Processes independent items from Excel/DataTable/API, needs retry | **REFramework (non-queue)** | Warning if custom retry logic instead of REFramework |

### Complexity Assessment

For each project, estimate complexity to calibrate review depth. Count these indicators and sum the score:

| Indicator | Score | How to Count |
|---|---|---|
| UI interactions (Click, Type Into, Get Text, etc.) | +0.5 each | Grep XAML for `NClick`, `NTypeInto`, `NGetText`, `Click`, `TypeInto`, `GetText` |
| Conditional branches (If, Switch, Flowchart Decision) | +1 each | Grep XAML for `<If `, `<Switch `, `<FlowDecision ` |
| Distinct target applications/systems | +1 each | Count unique `Use Application/Browser` targets + API endpoints |
| Error handling complexity (Try-Catch blocks, Retry Scopes) | +1-2 total | Count Try-Catch and Retry Scope activities |
| Data transformation complexity (LINQ, DataTable ops, JSON parsing) | +1-3 total | Assess data manipulation activities |

| Total Score | Complexity | Review Calibration |
|---|---|---|
| 1-5 | Low | Quick review — focus on structural correctness |
| 6-15 | Medium | Standard review — all checklist sections |
| 16-30 | High | Deep review — load advanced checklist, trace all execution paths |
| 30+ | Very High | Flag as Warning — consider decomposition. Projects this complex often have hidden bugs. |

### REFramework Assessment

For RPA projects processing multiple independent items, assess whether REFramework (or equivalent) should be used:

| Signal | Recommendation | Severity |
|---|---|---|
| Processes >20 independent items per run | Should use REFramework or queue-based pattern | Warning if not |
| Has retry requirements for transient failures | Should use REFramework's built-in retry | Warning if custom retry |
| Needs per-item audit trail | Should use Orchestrator queues | Info |
| Simple linear process (<10 items) | REFramework may be overkill | Info |
| Long-running with human interventions | Consider Maestro instead of REFramework | Info |

### Maestro vs REFramework Assessment

| Criterion | Use Maestro | Use REFramework | Use Both |
|---|---|---|---|
| Process type | Long-running, multi-actor | Transactional, queue-based | Maestro orchestrates, REFramework performs |
| Actors involved | RPA + agents + humans + APIs | RPA only (single performer) | Mix of actor types |
| Duration | Hours to weeks | Minutes to hours per batch | Varies by component |
| Error handling | BPMN error events, compensation | Built-in retry, state recovery | Each handles its layer |
| Visibility | Real-time process monitoring | Job/queue monitoring | Both dashboards |

## Advanced Review Considerations

### Library Dependencies

For projects that consume UiPath Libraries:

| Check | Severity |
|---|---|
| Library versions pinned (not floating) | Warning |
| No circular library dependencies | Critical |
| Library `outputType` is "Library" in project.json | Critical |
| Consuming project's library version matches published version | Warning |
| No transitive dependency conflicts | Warning |

### Object Repository Assessment

| Check | Severity |
|---|---|
| Object Repository used consistently (not mixed with hardcoded selectors) | Warning |
| UI Library version managed (not auto-incremented incorrectly) | Warning |
| No duplicate descriptors for the same element | Info |
| Cross-platform projects don't use Object Repository (not supported) | Critical |

### CI/CD and DevOps Readiness

| Check | Severity |
|---|---|
| Source control configured (Git, TFS, SVN) | Warning |
| CI/CD pipeline exists for automated publish | Info |
| Tests included in pipeline | Info |
| Environment promotion path defined (dev → staging → prod) | Info |
| Solution packaging used for deployment | Warning |
| Workflow Analyzer enforced before publish (via Automation Ops policy) | Info |

> For a comprehensive architecture-level assessment including process suitability scoring, complexity classification, and environment separation review, see [architecture-assessment-guide.md](architecture-assessment-guide.md).
