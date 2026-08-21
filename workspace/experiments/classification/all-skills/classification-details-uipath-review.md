# Classification Details — uipath-review

**Classification: Strong**

---

## What the Skill Teaches

Read-only reviewer of UiPath artifacts (RPA, agents, flows, BPMN, coded apps, solutions) covering filesystem discovery, project type classification, automated validation, agent-specific CLI review, unit-of-work analysis, PDD alignment, technical quality review, agent grading, and report generation.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Filesystem discovery** | **Yes — EXTRACT** | Step 0a: two deterministic `find` commands to locate markers and PDD candidates |
| 2 | **Project type classification** | **Yes — DETECT** | Step 1b: detection table maps filesystem signals to project types and checklists |
| 3 | **expressionLanguage capture** | **Yes — PARSE** | Step 1a: read `project.json` → extract `expressionLanguage` field |
| 4 | **Automated validation** | **Yes — VALIDATE/CHECK** | Step 2: mandatory `validate`/`build`/`analyze` commands per project type |
| 5 | Review CLI + deterministic findings | No (CLI is scripted) | `uip agent review` / `uip codedagent review` already scripted; output carried verbatim |
| 6 | **Unit-of-work transaction shape classification** | **Yes — DETECT** | Step 3a.3: matrix classifies one-to-one / one-to-many / unclear from grep patterns |
| 7 | Judgment catalog application | No | Requires reading agent source and reasoning about design quality |
| 8 | PDD alignment review | No | Comparing implementation to PDD requires semantic judgment |
| 9 | **Agent grade computation** | **Yes — COMPUTE/FORMULA** | Step 4.5: `G_jud = 100 − (15 × Criticals) − (4 × Warnings) − (1 × Infos)`; `Final = min(G_det, G_jud)` |
| 10 | **Structured report generation** | **Yes — FORMAT-CONVERT** | Step 5: fixed report schema (Summary, Validation, Findings, Per-Project, Next Steps) |

---

## Codifiable Procedures (not yet scripted)

### 1. Project Type Detection — DETECT

**Source:** `skills/uipath-review/SKILL.md` §Step 1b — Determine project type

**What it does:** Maps filesystem signals to project types and corresponding review checklists using a deterministic detection table. Inputs: file listing from Step 1c `find` command. Outputs: project type label and checklist file path. Line 131: `"| Filesystem Signal | Project Type | Review Checklist |"` opens a 9-row detection table where signals like "`project.json` + `.cs` files with `[Workflow]` attributes" → "RPA (Coded)" and "`agent.json` with `"type": "lowCode"`" → "Agent (Low-Code)".

**Why it's mechanical:** Each filesystem signal set maps to exactly one project type; no ambiguous overlap. The detection table enumerates all cases.

**Turn savings:** Agents currently scan file listings and match signals manually; a detection script takes a file-list input and returns the project type and checklist path in one call.

---

### 2. Automated Validation Pipeline — VALIDATE/CHECK

**Source:** `skills/uipath-review/SKILL.md` §Step 2 — Run Automated Validation and Workflow Analyzer

**What it does:** Runs the correct validation commands per project type. For RPA: `uip rpa validate` on every entry point + `uip rpa build` (to catch what validate misses) + `uip rpa analyze`. For agents: `uip agent refresh` → `uip agent validate`. For flows/BPMN/API workflows/coded apps: the corresponding type-specific validate command. Line 167: `"This step is mandatory and non-negotiable. You MUST run validation commands yourself (via Bash) before doing any manual review."` Output is error/warning/info counts per command per project.

**Why it's mechanical:** The command selection table (Step 2c) maps project type to validate command; all commands are specified with exact flags and output parsing.

**Turn savings:** Without a scripted validation step, agents execute commands one by one; a validation runner takes a project-type + project-dir and executes the full validation battery in one pass.

---

### 3. Unit-of-Work Transaction Shape Classification — DETECT

**Source:** `skills/uipath-review/SKILL.md` §Step 3a.2–3a.4

**What it does:** Classifies the transaction shape of a project's execution body using two `grep` commands and a classification matrix. Step 3a.2 greps for `ForEach|While` (iteration) and `HttpRequest|Add Queue Item|InvokeWorkflowFile|Write Range|Write Line|SqlCommand` (external effects). Step 3a.3 maps the grep results to one of three shapes: one-to-one / one-to-many / unclear. Line 336: `"| Actual execution pattern | Transaction Shape |"` opens the classification matrix. Step 3a.4 then maps shape + remediation posture to finding severity.

**Why it's mechanical:** The grep patterns and the classification matrix are fully specified; the severity mapping table is explicit (one-to-many + splittable + no guards + MaxRetryNumber < 2 → Critical).

**Turn savings:** Agents currently inspect execution files manually for iteration and external effects across 2–4 turns; a classification script runs the greps and returns shape + severity in one call.

---

### 4. Agent Grade Computation — COMPUTE/FORMULA

**Source:** `skills/uipath-review/SKILL.md` §Step 4.5 — Compute the Agent Letter Grade

**What it does:** Computes `G_jud` from judgment findings using the formula `100 − (15 × Criticals) − (4 × Warnings) − (1 × Infos)`, floored at 0, then maps to a grade band (85–100→A, 65–84→B, 45–64→C, 25–44→D, 0–24→F). Applies caps: any unmitigated judgment Critical → at most D; security/data-integrity Critical → F. Final grade is `min(G_det, G_jud)` where `G_det` comes from the review CLI's `Data.Grade`. Line 483: `"G_jud score — 100 − (15 × Criticals) − (4 × Warnings) − (1 × Infos) over the judgment findings, floored at 0."` 

**Why it's mechanical:** The formula, grade bands, and cap rules are all specified constants; no judgment on the formula itself.

**Turn savings:** Agents currently compute grades manually by tallying findings and looking up the band table; a grade script takes finding counts and returns the grade letter with binding constraint in one call.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Six of ten teaching areas are codifiable: filesystem discovery (EXTRACT), project type detection (DETECT), expressionLanguage capture (PARSE), automated validation (VALIDATE/CHECK), transaction shape classification (DETECT), grade computation (COMPUTE/FORMULA), and report generation (FORMAT-CONVERT). The non-codifiable areas — judgment catalog application and PDD alignment — require semantic reasoning but are explicitly bounded by the structured review workflow. The skill's most distinctive teaching (the grading formula, the detection table, the validation battery, the transaction shape matrix) is almost entirely codifiable.

**Why not None:** Four independent codifiable procedures exist: project type detection, automated validation, transaction shape classification, and grade computation.

**Evidence locations:**
- DETECT project type: `SKILL.md` §Step 1b (lines 130–144, detection table)
- VALIDATE/CHECK validation battery: `SKILL.md` §Step 2 (lines 167–249)
- DETECT transaction shape: `SKILL.md` §Step 3a.2–3a.4 (lines 324–401, grep patterns + matrix)
- COMPUTE/FORMULA grade: `SKILL.md` §Step 4.5 (lines 469–488, formula + grade bands)
- FORMAT-CONVERT report: `SKILL.md` §Step 5 (lines 491–633, required report structure)
