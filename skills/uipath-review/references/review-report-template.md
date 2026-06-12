# Review Report Template

Required output format for the Step 5 review report. Produce the report in chat — do NOT create a file.

## Report Rules — Do Not Violate

1. NEVER use internal workflow labels in the output. Forbidden terms: "Path A", "Path B", "Step 3a", "Step 0c", "Mismatch"/"Aligned" (use "one-to-one" / "one-to-many" / "unclear"), "disqualifying criteria", "verdict". The report is for the user, not a trace of the skill's internal workflow.
2. Do NOT create a separate "Unit of Work Analysis" section. The shape observation is a one-liner in the Summary. If the shape analysis produces a concern, it becomes a normal numbered finding.
3. Size metrics per file type use **activity / variable / node counts**, not "lines". Lines are meaningless for XAML and misleading for any file. See "Structural Metrics" table below.
4. Validation Status for Legacy projects says "Use `uipath-rpa` (Legacy mode) for Legacy-specific validation" — it does NOT say "Could not run" or "Failed". Legacy is supported indefinitely in Studio LTS; the `uip rpa` CLI targets Modern projects (Legacy mode uses the `uip rpa-legacy` CLI internally).

## Structural Metrics (never "lines")

| File type | Metrics to use |
|---|---|
| `.xaml` | Activity count, max nesting depth, root-scope variable count, argument count, invoke-workflow count |
| `.cs` (coded workflow) | Method count, statement count (LOC excluding blank/comment), class count |
| `.flow` | Node count, gateway count, longest path depth, subflow count |
| `.py` (coded agent) | Function count, statement count, import count |
| Config (JSON/XLSX) | Entry count, nesting depth |

## Required Report Structure

```markdown
## Review Report: <Project or Solution Name>

### Summary
- **Overall Quality:** Good / Needs Improvement / Critical Issues
- **Business Value:** <1-2 sentence description of what this automation does>
- **Review Scope:** Single project / Solution (N projects) / Multi-project repo (N executables + M libraries)
- **Project Types Found:** <list with type and language, e.g., "RPA (XAML, VisualBasic)", "Agent (Coded, Python)">
- **Validation Status:** <per project: pass with counts, or "Validation via uipath-rpa (Legacy mode)" for Legacy>
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

> For Legacy projects, note: "Validation CLI (`uip rpa validate`, `uip rpa analyze`) targets Modern projects. Legacy validation runs through `uipath-rpa` Legacy mode (using the `uip rpa-legacy` CLI)."

### Rule Findings

| Project | Source | Errors | Warnings | Info | Skipped |
|---|---|---|---|---|---|
| ClassifierAgent | `uip agent review` + judgment catalog | 2 | 5 | 3 | 1 |
| TriageAgent | `uip codedagent review` + judgment catalog | 1 | 4 | 2 | 1 |

**From the review CLI (deterministic):**
- [C-D-001] `LOWCODE_MESSAGES_NO_USER` — `ClassifierAgent/agent.json` — messages[] has no role="user" entry. Fix: Add a `{"role": "user", "content": "..."}` message.
- [C-D-003] `FRAMEWORK_DEP_MISSING` — `TriageAgent/pyproject.toml` — langgraph.json present but uipath-langchain missing from [project] dependencies. Fix: Add `"uipath-langchain"` to [project] dependencies in pyproject.toml.

**From the judgment catalog (reasoning):**
- [W-D-002] `LC_PROMPT_ROLE_DEFINITION` — `ClassifierAgent/agent.json` — System prompt opens with task instructions before establishing the agent's role. Fix: Add an opening sentence: "You are an X that does Y."
- [W-D-004] `CODED_ERROR_HANDLING` — `TriageAgent/main.py` — `llm.ainvoke(...)` call has no try/except, fallback, or retry. Fix: Wrap the call in try/except with a fallback path or surface the error in the agent's output state.
- ...

**Rules Skipped (and why):**
- `uip codedagent review` — CLI not available in environment (deterministic checks not run)
- `LC_GUARDRAIL_EVALS_CONSISTENCY` — no eval set present to assess against

> The Rule Findings section is required for every agent project (low-code or coded). It is omitted for project types whose catalog has not yet been authored (RPA, flows, coded apps as of phase 1).

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
| ProjectC | RPA (XAML) | VisualBasic | 84 activities, 50 vars, depth 12 | Via uipath-rpa (Legacy mode) | Needs Improvement | C-002, W-003 |

### Recommended Next Steps

Route each fix to the appropriate skill:

| Fix needed | Use skill |
|---|---|
| Fix RPA workflow / coded workflow / XAML / project.json | `uipath-rpa` |
| Fix RPA Windows-Legacy project | `uipath-rpa` (Legacy mode) |
| Fix agent (coded or low-code) | `uipath-agents` |
| Fix flow (.flow) | `uipath-maestro-flow` |
| Fix coded app | `uipath-coded-apps` |
| Fix Orchestrator resources (assets, queues, folders) | `uipath-platform` |
| Fix `.uipx` solution / pack / publish / deploy lifecycle | `uipath-solution` |

1. Fix [C-001] using `uipath-rpa` — change argument type to SecureString
2. ...

### Optimization Notes
- <queue usage, bulk operations, retry/idempotency observations — e.g., partial-failure handling for one-to-many shapes>
```

## Finding Severity Labels (never "Mismatch"/"Aligned")

- Overall Quality: `Good` / `Needs Improvement` / `Critical Issues`
- Transaction Shape: `one-to-one` / `one-to-many` / `unclear`
- Findings: `Critical` / `Warning` / `Info`

## Quality Determination Thresholds

- **Good** — 0 Critical, 0-3 Warnings
- **Needs Improvement** — 0 Critical, 4+ Warnings OR 1 Critical with clear fix
- **Critical Issues** — 2+ Critical OR 1 Critical with security/data-integrity implications
