---
when: "you are producing the Step 5 review report and need the full report template, structural-metrics table, example rows, or the exact severity/grade thresholds"
---

# Review Report Format (Step 5 detail)

The body's Step 5 keeps the hard report rules and section order; this file carries the full template, the structural-metrics table, worked example rows, and the severity/grade lookup tables.

## Structural metrics to report (never "lines")

| File type | Metrics to use |
|---|---|
| `.xaml` | Activity count, max nesting depth, root-scope variable count, argument count, invoke-workflow count |
| `.cs` (coded workflow) | Method count, statement count (LOC excluding blank/comment), class count |
| `.flow` | Node count, gateway count, longest path depth, subflow count |
| `.py` (coded agent) | Function count, statement count, import count |
| Config (JSON/XLSX) | Entry count, nesting depth |

## Required report structure

```markdown
## Review Report: <Project or Solution Name>

### Summary
- **Overall Quality:** Good / Needs Improvement / Critical Issues
- **Agent Grade:** <A–F> — <verdict label> (<binding constraint, e.g. "gated by G_det = CLI Data.Grade B; judgment clean (G_jud A)">) — *agent projects only; omit this line if the review has no agent projects*
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

**Validation Details:** *(Errors and Warnings only — omit the heading entirely when there are none)*
- [V-E-001] <project>/<file>: **<rule-id>** — <message>
- [V-W-001] <project>/<file>: **<rule-id>** — <message>

> For Legacy projects, note: "Validation CLI (`uip rpa validate`, `uip rpa analyze`) targets Modern projects. Legacy validation runs through `uipath-rpa` Legacy mode (using the `uip rpa-legacy` CLI)."

### Rules Skipped

| Rule / Command | Why |
|---|---|
| `uip codedagent review` | CLI not available in environment (deterministic checks not run) |
| `LC_GUARDRAIL_ACTION_INEFFECTIVE`, `LC_GUARDRAIL_MISAPPLIED` | Guardrails catalog unavailable (agent declares 2 guardrails, effectiveness unverified) |

> Only rules that were intended but could not be applied (Critical Rule 11). Group skips sharing one cause into a single row.

### Critical Findings (block deployment)

| ID | Rule | Recommendation |
|---|---|---|
| C-D-001 | `LOWCODE_SYSTEM_MESSAGE_MISSING` | `ClassifierAgent/agent.json`: `messages[0]` (system role) has empty content. Set `messages[0].content` to a non-empty system prompt. |
| C-001 | — | `ProjectA/Helper.cs`: Password argument uses `String`. Change the argument type to `SecureString`. |

### Warnings (should fix before production)

| ID | Rule | Recommendation |
|---|---|---|
| W-D-002 | `LC_PROMPT_ROLE_DEFINITION` | `ClassifierAgent/agent.json`: System prompt starts with task instructions before defining the agent's role. Open with: "You are an X that does Y." |

### Improvement Opportunities

| ID | Rule | Recommendation |
|---|---|---|
| I-D-001 | `LC_GUARDRAIL_RECOMMENDED` | `ClassifierAgent/agent.json`: `inputSchema.properties` contains `customer_email` and `ssn` without a PII guardrail. Add an Agent-scope PII guardrail with a block action. |

> One row per finding. Format each recommendation as `<file>: <issue>. <fix>.` Use the CLI's `File`, `Description`, and `SuggestedFix` verbatim; keep judgment and manual findings concise. Review-CLI, judgment-catalog, and manual-checklist findings all go in these three tables — do not split them into separate sections by source, and never list a finding in more than one table. `Rule` is `—` for a finding with no `rule_id` (Critical Rule 12).

### Per-Project Summary
| Project | Type | Language | Size | Validation | Quality | Grade | Key Findings |
|---|---|---|---|---|---|---|---|
| ClassifierAgent | Agent (Coded) | Python | 14 functions, 220 statements | Pass | Good | B | W-D-002 |
| ProjectA | RPA (Coded) | CSharp | 42 methods, 1,300 statements | 1 error, 2 warnings | Needs Improvement | — | V-E-001, W-001 |
| ProjectB | Flow | — | 18 nodes, 3 gateways, depth 5 | Pass | Good | — | I-001 |
| ProjectC | RPA (XAML) | VisualBasic | 84 activities, 50 vars, depth 12 | Via uipath-rpa (Legacy mode) | Needs Improvement | — | C-002, W-003 |

> The **Grade** column is the per-agent `min(G_det, G_jud)` from Step 4.5 — **agent projects only** (`—` for other types, phase 1). Append the review CLI's `Data.Grade` when it differs, e.g. `B (CLI: A)`. The **Quality** column (Good / Needs Improvement / Critical Issues) applies to every project type.

### Recommended Next Steps

Route each fix to the appropriate skill:

| Fix needed | Use skill |
|---|---|
| Fix RPA workflow / coded workflow / XAML / project.json | `uipath-rpa` |
| Fix RPA Windows-Legacy project | `uipath-rpa` (Legacy mode) |
| Fix agent (coded or low-code) | `uipath-agents` |
| Fix flow (.flow) | `uipath-maestro-flow` |
| Fix Maestro BPMN (.bpmn) | `uipath-maestro-bpmn` |
| Fix API workflow (Workflow.json) | `uipath-api-workflow` |
| Fix coded app | `uipath-coded-apps` |
| Fix Orchestrator resources (assets, queues, folders) | `uipath-platform` |
| Fix `.uipx` solution / pack / publish / deploy lifecycle | `uipath-solution` |

1. Fix [C-001] using `uipath-rpa` — change argument type to SecureString
2. ...

### Optimization Notes
- <queue usage, bulk operations, retry/idempotency observations — e.g., partial-failure handling for one-to-many shapes. Only print section when optimization is relevant and applicable to the project or solution.>

**Final grade: <A–F>**
```

> **`Final grade:` is the report's last line — nothing follows it.** No notes, caveats, or commentary, inside the report or after it. It restates the Summary's `Agent Grade` letter so the grade stays visible at the tail of a long report; the two must always match. Letter only. Only print for agent projects.

## Severity / grade lookup

**Finding severity labels (never "Mismatch"/"Aligned"):**
- Overall Quality: `Good` / `Needs Improvement` / `Critical Issues` (all project types)
- Agent Grade: `A` / `B` / `C` / `D` / `F` (no `+`/`-`) — agent projects only; see Step 4.5 and [agent-grading-rubric.md](agents/agent-grading-rubric.md)
- Transaction Shape: `one-to-one` / `one-to-many` / `unclear`
- Findings: `Critical` / `Warning` / `Info`

**Overall Quality thresholds** (all project types):
- **Good** — 0 Critical, 0–3 Warnings
- **Needs Improvement** — 0 Critical, 4+ Warnings OR 1 Critical with clear fix
- **Critical Issues** — 2+ Critical OR 1 Critical with security/data-integrity implications

**Agent Grade → verdict label** (agent projects only; the line reads "B — Good"):

| Grade | Verdict label |
|---|---|
| **A** / **B** | Good |
| **C** / **D** | Needs Improvement |
| **F** | Critical Issues |

This maps the letter to the verdict word only. The agent grade is `min(G_det, G_jud)` from Step 4.5, where **G_det is the review CLI's `Data.Grade`** and the G_jud band lives in Step 4.5.
