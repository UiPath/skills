# Phase 2: Extract Guidelines and CLI - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Create shared files for the fix-one-thing rule, unified validation/iteration loop, smoke test, and common CLI commands. Trim each skill's CLI and guideline files to retain only domain-specific content. Do NOT trim or modify UiAutomation content from skill files — that's Phase 3 work.

</domain>

<decisions>
## Implementation Decisions

### GUIDE-02 disposition
- Already satisfied by Phase 1's `shared/uia-debug-workflow.md` — no new file needed
- The StartDebugging-over-StartExecution principle is covered by the existing shared UIA debug workflow procedure
- Mark GUIDE-02 as complete without creating a new file

### Shared guideline file: `shared/validation-loop.md`
- **Fix-one-thing rule (GUIDE-01)**: Generic version without UiAutomation-specific examples (no TypeInto/KeyboardShortcut example). State the principle abstractly so it applies to any fix context
- **Unified iteration loop**: Merge best of both skills' loops — combine RPA's DO NOT rules (don't skip validation, don't assume edits worked, don't obsess on one error, don't bundle fixes) with coded's attempt caps (5 validation fix attempts, 2 runtime retries)
- **Standardize on `validate`**: Both skills should use `validate` (forces re-analysis) instead of `get-errors` (returns cached state). The shared loop uses `validate` as the validation command
- **Smoke test section**: Include the smoke test procedure (run-file after validation passes, when-to-run/when-not-to-run guidance). Extracted from both skills
- **Skip focus-activity**: `focus-activity` stays in RPA's domain-specific file only

### When Phase 3 trims skill files
- Both the positive "fix one thing" rule AND the anti-pattern restatement in coding-guidelines.md should point to the shared file — shared file is the single source of truth
- Do NOT trim already-extracted UIA sections (Running UI Automation Workflows, Runtime Selector Failures) during Phase 2 — that's Phase 3 (INTEG-02) work

### Shared CLI file: `shared/cli-reference.md`
- **Scope**: Only commands documented in BOTH uip-guide.md AND cli-reference.md go into the shared file
- **Commands included**: list-instances, start-studio, create-project, open-project, validate, run-file, get-errors, install-or-update-packages
- **Commands excluded from shared**: indicate-application and indicate-element (already covered by shared/uia-configure-target-workflows.md from Phase 1), inspect-package (coded-only), get-manual-test-cases/get-manual-test-steps (coded-only), find-activities/get-default-activity-xaml/list-workflow-examples/get-workflow-example/focus-activity (RPA-only)
- **Global options**: Include --project-dir, --studio-dir, --timeout, --verbose, --format and STUDIO_DIR/PROJECT_DIR resolution logic in the shared file
- **run-file**: Document both StartExecution and StartDebugging variants inline (self-contained, no cross-reference needed to uia-debug-workflow.md)
- **Activity docs discovery**: Include the "Installed Package Activity Documentation" section (browsing .local/docs/packages/) — identical across both skills
- **Format**: Section-per-command (heading, description, code example, parameter table). No example JSON responses — commands only
- **File naming**: `shared/cli-reference.md`

### Claude's Discretion
- Exact section ordering within shared files
- How to word the generic fix-one-thing rule without UIA-specific examples
- Whether to include cross-references between shared files

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source files for guideline extraction
- `skills/uipath-coded-workflows/references/coding-guidelines.md` — Fix-one-thing rule (line 114), anti-pattern restatement (line 174), validation loop (line 98-108)
- `skills/uipath-rpa-workflows/references/validation-and-fixing.md` — Iteration loop with DO NOT rules (lines 46-60), smoke test (lines 64-91)

### Source files for CLI extraction
- `skills/uipath-coded-workflows/references/uip-guide.md` — Full CLI reference, section-per-command format with global options
- `skills/uipath-rpa-workflows/references/cli-reference.md` — CLI reference in table format with activity docs discovery section

### Phase 1 shared files (already extracted — do not re-extract)
- `skills/shared/uia-debug-workflow.md` — StartDebugging procedure (satisfies GUIDE-02)
- `skills/shared/uia-configure-target-workflows.md` — Indicate commands (excluded from shared CLI)

### Requirements
- `.planning/REQUIREMENTS.md` — GUIDE-01, GUIDE-02, CLI-01, CLI-02 acceptance criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 1 shared files establish the pattern: topic-focused files in `skills/shared/` with paradigm-neutral language
- Both CLI files share global options section, STUDIO_DIR resolution, PROJECT_DIR resolution verbatim

### Established Patterns
- Phase 1 convention: pure shared core, generic bridge sentences at paradigm boundaries
- Shared file naming: `uia-*` prefix for UiAutomation, no prefix pattern established for non-UIA shared files yet
- Explicit relative paths (`../shared/...`) for cross-references

### Integration Points
- `coding-guidelines.md` will be trimmed to remove fix-one-thing rule and iteration loop (Phase 3)
- `validation-and-fixing.md` will be trimmed to remove iteration loop and smoke test (Phase 3)
- `uip-guide.md` will be trimmed to coded-specific commands only (Phase 3)
- `cli-reference.md` will be trimmed to RPA-specific commands only (Phase 3)

</code_context>

<specifics>
## Specific Ideas

- Iteration loops in both skills diverged through independent evolution, not because domains require different approaches — unify with best of both
- Standardize both skills on `validate` instead of `get-errors` for the iteration loop validation step

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-extract-guidelines-and-cli*
*Context gathered: 2026-03-31*
