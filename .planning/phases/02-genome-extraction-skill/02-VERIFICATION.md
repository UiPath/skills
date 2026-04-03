---
phase: 02-genome-extraction-skill
verified: 2026-04-02T17:31:20Z
status: gaps_found
score: 5/6 must-haves verified
re_verification: false
gaps:
  - truth: "Output genome is indistinguishable from one created by the authoring skill"
    status: partial
    reason: "SKILL.md references skill-mapping-guide.md from the uipath-genome-authoring skill directory via a relative path (../uipath-genome-authoring/references/skill-mapping-guide.md). This is a direct cross-skill file dependency, which CONTRIBUTING.md and CLAUDE.md both prohibit: 'Skills cannot reference or depend on other skills.' The extraction skill is not self-contained. If uipath-genome-authoring is absent, the extraction skill's Build With step breaks."
    artifacts:
      - path: "skills/uipath-genome-extraction/SKILL.md"
        issue: "Lines 33, 66, 118 link to ../uipath-genome-authoring/references/skill-mapping-guide.md"
      - path: "skills/uipath-genome-extraction/references/extraction-mapping-guide.md"
        issue: "Line 174 links to ../../uipath-genome-authoring/references/skill-mapping-guide.md"
    missing:
      - "Copy skill-mapping-guide.md into skills/uipath-genome-extraction/references/ (or inline its decision tree in extraction-mapping-guide.md) and update all 4 references to use the local path ./references/skill-mapping-guide.md"
human_verification:
  - test: "Point the agent at a real UiPath project directory and run the extraction workflow end-to-end"
    expected: "Agent reads project files without prompting, produces a genome.md file in the CWD named from project.json, genome contains all 10 sections populated per the complexity level inferred from the project, no code-level syntax in business rules or acceptance criteria, no extraction markers in output"
    why_human: "End-to-end agent behavior and genome output quality cannot be verified by static grep"
  - test: "Check that the genome output is visually indistinguishable from one created by the authoring skill on the same automation concept"
    expected: "Both genomes read as if authored from scratch -- no extraction markers, no source file references, same section order and formatting"
    why_human: "Requires comparing two LLM-generated documents for parity -- not automatable"
---

# Phase 2: Genome Extraction Skill Verification Report

**Phase Goal:** Users can point the agent at an existing UiPath Studio solution and get a genome spec that captures what the solution does
**Verified:** 2026-04-02T17:31:20Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Agent reads UiPath project files (project.json, .xaml, .cs, .cs.json, .flow) to understand the solution | VERIFIED | project-analysis-guide.md covers all 5 file types with specific signal tables. SKILL.md Step 2 instructs the agent to read all relevant files with no file count limit. Exclusion rules for auto-generated dirs present. |
| 2 | Agent identifies target applications, workflow steps, and business rules from project files | VERIFIED | extraction-mapping-guide.md has 16-row package-to-target-app table, business rule extraction section with XAML/C# translation patterns. project-analysis-guide.md extracts call graph for workflow step ordering. |
| 3 | Agent detects platform features (Document Understanding, Integration Service, Orchestrator queues) | VERIFIED | extraction-mapping-guide.md Platform Feature Detection table covers 8 signals including DU, IS, queues, attended, Maestro, global handler, multi-entry-point. |
| 4 | Agent extracts error handling patterns and maps them to behavioral descriptions | VERIFIED | extraction-mapping-guide.md Error Handling Pattern Mapping table has 6 patterns with XAML signal, .cs signal, and behavioral genome description columns. Rule enforces behavioral language. |
| 5 | Agent generalizes hardcoded values into Configuration Questions with original values as defaults | VERIFIED | extraction-mapping-guide.md Generalization Rules section has 9 categories of values to generalize, with prescribed format "N. {Question}? (source project used: {original value})". SKILL.md Critical Rule 2 enforces this. |
| 6 | Output genome is indistinguishable from one created by the authoring skill | PARTIAL | SKILL.md mirrors authoring skill structure (9 critical rules, 6-step workflow replacing 8-step interview, same population matrix, 7 anti-patterns). Blueprint preamble rule present. However: SKILL.md and extraction-mapping-guide.md both link to skill-mapping-guide.md from the uipath-genome-authoring skill directory -- a cross-skill dependency prohibited by project rules. |

**Score:** 5/6 truths verified (1 partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `skills/uipath-genome-extraction/SKILL.md` | Complete skill definition with workflow, critical rules, population matrix, anti-patterns | VERIFIED | 128 lines. Valid YAML frontmatter. name=uipath-genome-extraction. Both TRIGGER/DO NOT TRIGGER clauses present. 5 required sections. 6 workflow steps. 9 critical rules. 7 anti-patterns. Population matrix table present. |
| `skills/uipath-genome-extraction/references/project-analysis-guide.md` | File-by-file extraction instructions for each UiPath file type | VERIFIED | Covers project.json (5 mentions), XAML (xmlns x5), .cs.json (x4), .flow (x3), Call Graph section. All 3 exclusion dirs present. InvokeWorkflowFile, ViewStateManager skip rule, red flag files (CodedWorkflow.cs, ConnectionsManager.cs) all present. Cross-ref to extraction-mapping-guide present. |
| `skills/uipath-genome-extraction/references/extraction-mapping-guide.md` | Signal-to-genome-section mapping tables | VERIFIED | 176 lines. Package table with 19 rows (16 UiPath packages). Complexity Inference table. Error Handling Pattern Mapping with Source Pattern/XAML Signal/.cs Signal/Genome Description columns. Generalization Rules. Business Rule Extraction. Acceptance Criteria Derivation with ban list. Cross-ref to project-analysis-guide present. |
| `CODEOWNERS` | Ownership entry for extraction skill | VERIFIED | Contains `/skills/uipath-genome-extraction/ @DragosUnguru` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| SKILL.md | genome-template.md | `../shared/genome/genome-template.md` | VERIFIED | File exists at skills/shared/genome/genome-template.md. Path resolves. Referenced in Step 5 and Reference Navigation. |
| SKILL.md | project-analysis-guide.md | `./references/project-analysis-guide.md` | VERIFIED | File exists. Referenced in Critical Rule 1, Step 2, Reference Navigation. |
| SKILL.md | extraction-mapping-guide.md | `./references/extraction-mapping-guide.md` | VERIFIED | File exists. Referenced in Critical Rule 3, Steps 3-4, Reference Navigation. |
| SKILL.md | skill-mapping-guide.md | `../uipath-genome-authoring/references/skill-mapping-guide.md` | WIRED BUT VIOLATES PROJECT RULES | File exists and path resolves. However this is a cross-skill reference. CONTRIBUTING.md states "Skills cannot reference or depend on other skills." |
| project-analysis-guide.md | extraction-mapping-guide.md | `extraction-mapping-guide.md` (relative) | VERIFIED | Cross-reference present at bottom of file. Path resolves (same directory). |
| extraction-mapping-guide.md | project-analysis-guide.md | `project-analysis-guide.md` (relative) | VERIFIED | Cross-reference present in opening line. Path resolves. |
| extraction-mapping-guide.md | skill-mapping-guide.md | `../../uipath-genome-authoring/references/skill-mapping-guide.md` | WIRED BUT VIOLATES PROJECT RULES | File exists and path resolves. Same cross-skill violation as above. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| EXTR-01 | 02-01-PLAN (partial), 02-02-PLAN | Agent reads UiPath project structure (project.json, .xaml, .cs, .flow files) | SATISFIED | project-analysis-guide.md covers all 5 file types with per-signal extraction tables. SKILL.md Step 2 implements the read-all-files workflow. |
| EXTR-02 | 02-02-PLAN | Agent identifies target applications, workflow steps, and business rules from project files | SATISFIED | extraction-mapping-guide.md Package-to-Target-Application, Business Rule Extraction sections. Call graph construction in project-analysis-guide.md. SKILL.md Step 4 maps signals to all genome sections. |
| EXTR-03 | 02-02-PLAN | Agent produces genome markdown following TEMPLATE.md format from analyzed solution | SATISFIED | SKILL.md Step 5 reads genome-template.md before writing. Population matrix enforces all 10 sections always present. File naming from project.json slug documented. |
| EXTR-04 | 02-01-PLAN, 02-02-PLAN | Agent detects platform features in use (Document Understanding, Integration Service, Orchestrator queues, etc.) | SATISFIED | extraction-mapping-guide.md Platform Feature Detection table with 8 signals. SKILL.md Critical Rule 3 and Step 4 reference this table. |
| EXTR-05 | 02-01-PLAN, 02-02-PLAN | Agent extracts error handling patterns and maps them to genome error handling section | SATISFIED | extraction-mapping-guide.md Error Handling Pattern Mapping table with 6 patterns. Behavioral translation rule enforced. SKILL.md Critical Rule 4. |

No orphaned requirements: all 5 EXTR IDs declared in plans are the only Phase 2 requirements in REQUIREMENTS.md.

### Anti-Patterns Found

| File | Line(s) | Pattern | Severity | Impact |
|------|---------|---------|----------|--------|
| `skills/uipath-genome-extraction/SKILL.md` | 33, 66, 118 | Cross-skill reference to `../uipath-genome-authoring/references/skill-mapping-guide.md` | Blocker | Skill is not self-contained. If uipath-genome-authoring directory is absent or renamed, Build With step has no decision tree. Violates explicit project rule. |
| `skills/uipath-genome-extraction/references/extraction-mapping-guide.md` | 174 | Cross-skill reference to `../../uipath-genome-authoring/references/skill-mapping-guide.md` | Blocker | Same violation, same impact. |

No TODO/FIXME/placeholder comments found. No empty return stubs. All implementations are substantive.

### Human Verification Required

#### 1. End-to-End Extraction Run

**Test:** Point the agent at a real UiPath project directory containing project.json, at least one .xaml file, and one .cs file. Ask it to extract a genome.
**Expected:** Agent reads all project files without asking what the project does, infers complexity from signal counts, writes a genome.md to CWD named from the project slug, all 10 sections present and populated per complexity, no code-level language in business rules or acceptance criteria, blueprint preamble present.
**Why human:** Static analysis cannot verify agent reading behavior, LLM output quality, or file-write behavior at runtime.

#### 2. Genome Parity Check

**Test:** Author a genome from scratch using uipath-genome-authoring on the same automation topic, then extract a genome from a project implementing that topic using uipath-genome-extraction.
**Expected:** Both documents have the same structure, tone, and format. The extracted genome has no provenance markers, no source file references, and reads as if authored from scratch.
**Why human:** Comparing LLM output documents for parity requires human judgment.

### Gaps Summary

One gap blocks the project rule requiring skills to be self-contained: `SKILL.md` and `extraction-mapping-guide.md` both link to `skill-mapping-guide.md` from the `uipath-genome-authoring` directory. This creates a hard runtime dependency between two skills. The fix is mechanical: copy `skill-mapping-guide.md` into `skills/uipath-genome-extraction/references/` and update the 4 references to use the local path. The content of the skill-mapping guide itself (decision tree for mapping automation types to skills) does not need to change.

Everything else in the phase is fully implemented: all 3 files are substantive, all intra-skill cross-references resolve, all 5 EXTR requirements are addressed, commit history matches summaries, and no placeholder content was found.

---

_Verified: 2026-04-02T17:31:20Z_
_Verifier: Claude (gsd-verifier)_
