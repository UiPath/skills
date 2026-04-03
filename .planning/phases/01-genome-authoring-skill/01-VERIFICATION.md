---
phase: 01-genome-authoring-skill
verified: 2026-04-02T16:30:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 01: Genome Authoring Skill Verification Report

**Phase Goal:** Users can describe an automation idea and get a complete, well-structured genome markdown file back
**Verified:** 2026-04-02T16:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User describes an automation idea and receives a genome markdown file following TEMPLATE.md format | VERIFIED | SKILL.md 8-step workflow (Steps 1–7) drives free-form intake to written `{slug}-genome.md`; genome-template.md mirrors `.genome_spec/TEMPLATE.md` plus Build With |
| 2 | Agent asks fewer questions for simple genomes and conducts a full interview for complex ones | VERIFIED | Critical Rule 3 sets hard follow-up limits (Simple: 0-1, Medium: 1-2, Complex: 2-3); Step 5 enforces batching; Step 2 complexity signal table and 5 additional heuristics govern inference |
| 3 | Generated genome includes testable acceptance criteria derived from the workflow | VERIFIED | Critical Rule 6 bans generic criteria and mandates `Given [input], the automation [observable outcome]` pattern; Step 6 explicitly derives each criterion from a workflow step or business rule |
| 4 | All three complexity levels (simple, medium, complex) produce valid genome output with appropriate sections populated | VERIFIED | Step 6 population matrix maps all 10 template sections across Simple/Medium/Complex with explicit stub vs. full rules; every section is required at all levels |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `skills/uipath-genome-authoring/SKILL.md` | Complete skill definition, min 150 lines, name in frontmatter | VERIFIED | 161 lines; `name: uipath-genome-authoring` confirmed; TRIGGER/DO NOT TRIGGER present; 8 critical rules, 8 workflow steps, reference navigation, 7 anti-patterns |
| `skills/uipath-genome-authoring/references/genome-template.md` | All template sections from spec plus `## Build With` | VERIFIED | 66 lines; 10 sections confirmed (Overview through Tags); `## Build With` inserted between Acceptance Criteria and Complexity; header comment references `.genome_spec/TEMPLATE.md` as source of truth; links to `skill-mapping-guide.md` |
| `skills/uipath-genome-authoring/references/skill-mapping-guide.md` | All 5 build skills with selection criteria | VERIFIED | 43 lines; mapping table with all 5 skills; 7-rule decision tree; Common Combinations section with 4 examples |
| `CODEOWNERS` | Entry for `/skills/uipath-genome-authoring/` | VERIFIED | Line 28: `/skills/uipath-genome-authoring/ @DragosUnguru` — correct comment + path pattern |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `SKILL.md` | `references/genome-template.md` | Relative link in Reference Navigation (line 150) and Step 6 (line 100) | WIRED | `[genome-template.md](./references/genome-template.md)` resolves to existing file |
| `SKILL.md` | `references/skill-mapping-guide.md` | Relative links in Critical Rule 8 (line 27), Step 6 (line 120), Step 8 (line 146), Reference Navigation (line 151) | WIRED | `[skill-mapping-guide.md](./references/skill-mapping-guide.md)` resolves to existing file; 4 reference points |
| `genome-template.md` | `skill-mapping-guide.md` | Relative link in Build With section (line 54) | WIRED | `[skill-mapping-guide.md](./skill-mapping-guide.md)` — both files in same `references/` directory |
| `genome-template.md` | `.genome_spec/TEMPLATE.md` | Content derivation noted in header comment | VERIFIED | Section order matches spec exactly; Build With is the only addition; header comment documents the relationship |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUTH-01 | 01-02-PLAN | User can describe an automation idea and receive a complete genome markdown file | SATISFIED | SKILL.md Step 1 (receive description) through Step 7 (write file) provides the complete path; Critical Rule 7 mandates immediate file write |
| AUTH-02 | 01-02-PLAN | Agent asks configuration questions adapted to genome complexity | SATISFIED | Critical Rule 3 and Step 5 enforce follow-up limits by complexity level; Step 2 complexity inference prevents the agent from ever asking the user to self-classify |
| AUTH-03 | 01-01-PLAN, 01-02-PLAN | Genome output follows TEMPLATE.md format with all applicable sections populated | SATISFIED | `genome-template.md` is a verified derivation of `.genome_spec/TEMPLATE.md`; Critical Rule 5 mandates all sections present; population matrix in Step 6 specifies full vs. stub per complexity |
| AUTH-04 | 01-02-PLAN | Agent generates testable acceptance criteria derived from the described workflow | SATISFIED | Critical Rule 6 defines the testability contract; Step 6 Acceptance Criteria subsection mandates derivation from workflow steps; three specific patterns given; vague criteria explicitly banned |
| AUTH-05 | 01-01-PLAN, 01-02-PLAN | Agent handles all three complexity levels (simple, medium, complex) | SATISFIED | Complexity signal table (Step 2) + 5 additional heuristics cover all three levels; population matrix in Step 6 specifies behavior at each level; stub patterns defined for all simple-level sections |

All 5 AUTH requirements satisfied. No orphaned requirements for this phase.

### Anti-Patterns Found

No anti-patterns detected. Scan of all three skill files (SKILL.md, genome-template.md, skill-mapping-guide.md) found:
- No TODO/FIXME/HACK/PLACEHOLDER comments
- No stub return values or empty implementations
- No placeholder text beyond intentional `{placeholder}` syntax in the template itself (correct by design)

### Human Verification Required

#### 1. Complexity inference accuracy

**Test:** Describe a borderline automation (e.g., "Read emails, classify by department, route to Outlook subfolder") and observe whether the agent infers Medium rather than Simple.
**Expected:** Agent infers Medium (multiple conditional paths, routing logic) without asking the user to declare complexity.
**Why human:** Inference accuracy depends on LLM reasoning over the signal table — cannot be verified by static grep.

#### 2. Follow-up question batching behavior

**Test:** Provide a sparse one-sentence automation description and observe how many separate messages the agent uses for follow-up questions.
**Expected:** All follow-up questions arrive in a single message, not one-at-a-time.
**Why human:** Runtime conversation behavior; not verifiable from static content.

#### 3. Acceptance criteria specificity

**Test:** Request a genome for a simple automation ("Download daily sales report from web portal and save to shared drive") and check that the acceptance criteria reference specific inputs and outputs.
**Expected:** Criteria reference concrete details like specific filenames, URLs, or observable outcomes — not "download completes successfully."
**Why human:** Quality of generated criteria depends on how the agent interprets Critical Rule 6 during generation.

#### 4. Proactive UiPath feature suggestions

**Test:** Describe an automation involving PDFs without mentioning Document Understanding. Check that the generated genome's Build With or Overview references Document Understanding.
**Expected:** Agent proactively includes Document Understanding in the genome even though the user did not mention it.
**Why human:** Feature suggestion behavior is a runtime output property; the instruction exists in Critical Rule 4 but adherence is not statically verifiable.

### Gaps Summary

No gaps. All automated checks passed.

The skill structure is complete and internally consistent:
- Folder name matches frontmatter `name` exactly (`uipath-genome-authoring`)
- SKILL.md is self-contained — skill names in the `description` field appear only in the DO NOT TRIGGER clause (correct use), not as structural imports
- All relative links resolve to existing files
- Section order in `genome-template.md` matches `.genome_spec/TEMPLATE.md` with a single insertion (Build With between Acceptance Criteria and Complexity)
- All 5 AUTH requirements are covered and traceable to specific rules, steps, and artifacts

The 4 items flagged for human verification are behavioral/runtime properties. They cannot be confirmed by static analysis but the static instructions governing them are sound and specific.

---

_Verified: 2026-04-02T16:30:00Z_
_Verifier: Claude (gsd-verifier)_
