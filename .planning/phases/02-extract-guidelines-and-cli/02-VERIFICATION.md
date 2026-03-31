---
phase: 02-extract-guidelines-and-cli
verified: 2026-03-31T00:00:00Z
status: passed
score: 9/9 must-haves verified
---

# Phase 02: Extract Guidelines and CLI — Verification Report

**Phase Goal:** Shared files exist for the fix-one-thing rule, debug-first execution guidance, and common CLI commands; each skill's CLI file retains only its domain-specific content
**Verified:** 2026-03-31
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A shared file contains the fix-one-thing rule stated generically without UIA-specific examples | VERIFIED | `skills/shared/validation-loop.md` line 5: "Fix One Thing at a Time"; no TypeInto/KeyboardShortcut/ObjectRepository/Descriptors terms (grep returns 0) |
| 2 | A shared file contains the unified validation iteration loop with validate command, 5 fix attempt cap, and all 4 DO NOT rules | VERIFIED | `validate --file-path` present; "Cap at 5 fix attempts" present; 5 DO NOT rules listed (rule 5 is fix-one-thing; plan specifies 4+1) |
| 3 | A shared file contains the smoke test procedure with when-to-run and when-not-to-run guidance | VERIFIED | "Smoke Test" heading present; "When to run" (3 items) and "When NOT to run" (3 items) both present; `run-file --file-path` documented |
| 4 | GUIDE-02 is marked complete without a new file (already satisfied by uia-debug-workflow.md) | VERIFIED | `skills/shared/uia-debug-workflow.md` exists with 2 occurrences of StartDebugging; no new debug-first file created in Phase 2 |
| 5 | A shared CLI file contains all 8 common commands in section-per-command format | VERIFIED | All 8 present: list-instances, start-studio, create-project, open-project, validate, run-file, get-errors, install-or-update-packages |
| 6 | Global options and STUDIO_DIR/PROJECT_DIR resolution logic are in the shared CLI file | VERIFIED | Global options table present; STUDIO_DIR 3-step waterfall present; PROJECT_DIR resolution subsection present |
| 7 | run-file documents both StartExecution and StartDebugging inline | VERIFIED | Both present in run-file section with inline code examples |
| 8 | Activity docs discovery section is in the shared CLI file | VERIFIED | "Installed Package Activity Documentation" section present with 5-action table including .local/docs/packages/ path |
| 9 | No domain-specific commands in the shared CLI file | VERIFIED | grep returns 0 for: indicate-application, indicate-element, inspect-package, find-activities, focus-activity, get-manual-test-cases |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `skills/shared/validation-loop.md` | Fix-one-thing rule, validation iteration loop, smoke test procedure | VERIFIED | 81 lines; substantive content; cross-references cli-reference.md |
| `skills/shared/cli-reference.md` | Common CLI reference for both skills | VERIFIED | 199 lines; all 8 commands; global options; activity docs section |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `skills/shared/validation-loop.md` | `skills/shared/cli-reference.md` | Cross-reference link after Rules section | WIRED | Line 40: "See [cli-reference.md](cli-reference.md) for full `validate` and `run-file` command documentation." |
| `skills/shared/cli-reference.md` | `skills/shared/uia-configure-target-workflows.md` | indicate commands NOT duplicated in shared CLI | WIRED | grep for "indicate" and "uia-configure-target" in cli-reference.md returns 0 matches — indicate-* commands correctly excluded |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GUIDE-01 | 02-01-PLAN.md | Extract "fix one thing at a time" / single-fix-per-iteration rule into shared file | SATISFIED | `validation-loop.md` section 1 is the generic fix-one-thing rule; no UIA-specific examples present |
| GUIDE-02 | 02-01-PLAN.md | Extract debug-first execution guidance (StartDebugging over StartExecution) into shared file | SATISFIED | Already satisfied by Phase 1's `uia-debug-workflow.md`; plan correctly noted no new work needed; REQUIREMENTS.md marks it complete |
| CLI-01 | 02-02-PLAN.md | Extract common `uip rpa` commands (validate, run-file, get-errors) into shared reference | SATISFIED | `cli-reference.md` contains all 8 common commands including validate, run-file, and get-errors with full documentation |
| CLI-02 | 02-02-PLAN.md | Each skill retains only domain-specific CLI usage examples | SATISFIED (Phase 2 scope) | Both skill CLI files unchanged and present: `uipath-coded-workflows/references/uip-guide.md` and `uipath-rpa-workflows/references/cli-reference.md`; per plan, trimming to domain-specific is Phase 3 (INTEG-02) work |

No orphaned requirements — all 4 Phase 2 requirement IDs (GUIDE-01, GUIDE-02, CLI-01, CLI-02) are claimed by plans and verified in the codebase.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No anti-patterns found |

No TODOs, FIXMEs, placeholder comments, empty implementations, or UIA-specific terms detected in either shared file.

---

### Human Verification Required

None. All phase outputs are documentation files with verifiable content — no runtime behavior, visual rendering, or external service dependencies.

---

### Gaps Summary

None. All must-haves are satisfied. Both shared files exist, are substantive, and are properly cross-referenced. All four requirement IDs (GUIDE-01, GUIDE-02, CLI-01, CLI-02) are accounted for and verified. CLI-02's domain-specific trimming is correctly deferred to Phase 3 per plan scope.

---

_Verified: 2026-03-31_
_Verifier: Claude (gsd-verifier)_
