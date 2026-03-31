# Phase 3: Integrate Skills - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Update both SKILL.md files and domain-specific guides to reference shared files; trim duplicated content from domain files to section-heading pointers; verify zero logic loss across all files. This is the final wiring phase — no new shared files are created, only references added and duplicated content removed.

</domain>

<decisions>
## Implementation Decisions

### SKILL.md referencing strategy
- Replace existing UIA sections/pointers in both SKILL.md files to point to shared/ files instead of only the domain-specific guide
- Coded SKILL.md: update "UI Automation References" section to list all 5 shared UIA files with explicit paths, then point to domain guide for C#-specific content
- RPA SKILL.md: update "UI Automation References" and inline UIA mentions to point to shared/ files, then point to domain guide for XAML-specific content
- Also reference shared/validation-loop.md and shared/cli-reference.md from relevant SKILL.md sections (Critical Rule #14 for validation, CLI Quick Reference for CLI) — Claude loads SKILL.md first, so it finds shared content faster
- Coded SKILL.md Rule #15: trim to one line + pointer to shared files (lose the hierarchy overview, shared files have the procedure)
- RPA SKILL.md "Target Configuration Gate" section: trim to concise policy + pointer to shared files (same treatment as coded Rule #15)

### Guide trimming depth
- Section heading + pointer pattern everywhere: keep the section heading so readers know the topic exists, replace content with a one-line pointer to the shared file
- Example: `## Prerequisites\n\nSee [shared/uia-prerequisites.md](../shared/uia-prerequisites.md).`
- Same pattern for all trimmed content across all files (UIA guides, CLI files, guideline files) — consistent approach everywhere
- Paradigm-specific content stays unchanged in its section

### Overlap trimming scope
- Trim ALL overlaps with shared files, not just what Phase 2 deferred
- RPA's validation-and-fixing.md "Running UI Automation Workflows" section → pointer to shared/uia-debug-workflow.md
- Any section whose content now exists in a shared file gets trimmed to a pointer, regardless of which domain file it's in
- Single source of truth everywhere

### Files to trim (comprehensive list)
- `skills/uipath-coded-workflows/references/ui-automation-guide.md` — extracted UIA sections → pointers to shared/uia-*.md files
- `skills/uipath-rpa-workflows/references/ui-automation-guide.md` — extracted UIA sections → pointers to shared/uia-*.md files
- `skills/uipath-coded-workflows/references/coding-guidelines.md` — fix-one-thing rule, iteration loop → pointer to shared/validation-loop.md
- `skills/uipath-rpa-workflows/references/validation-and-fixing.md` — iteration loop, smoke test, Running UI Automation Workflows → pointers to shared/validation-loop.md and shared/uia-debug-workflow.md
- `skills/uipath-coded-workflows/references/uip-guide.md` — common CLI commands → pointer to shared/cli-reference.md
- `skills/uipath-rpa-workflows/references/cli-reference.md` — common CLI commands → pointer to shared/cli-reference.md

### Verification approach
- Section-level checklist: for each original file, list every section heading and note where it ended up (shared file path, stays in domain file, or pointer added)
- Standalone artifact: VERIFICATION-CHECKLIST.md in the phase directory, reviewable independently, archived after review
- Matches Phase 1's pattern with the divergence review doc

### Plan structure
- Two plans matching previous phases' pattern:
  - Plan 1: All integration work (trim 6 domain files + update 2 SKILL.md files)
  - Plan 2: Verification checklist (build section-level checklist, verify every section accounted for, produce VERIFICATION-CHECKLIST.md)

### Claude's Discretion
- Exact wording of pointer sentences in trimmed sections
- Order of file modifications within Plan 1
- How to handle any minor content that doesn't cleanly map to a shared file (edge cases during trimming)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source files to modify
- `skills/uipath-coded-workflows/SKILL.md` — Coded skill entry point; update UI Automation References, Rule #15, Critical Rule #14, CLI references
- `skills/uipath-rpa-workflows/SKILL.md` — RPA skill entry point; update UI Automation References, Target Configuration Gate, CLI Quick Reference
- `skills/uipath-coded-workflows/references/ui-automation-guide.md` — Coded UIA guide to trim
- `skills/uipath-rpa-workflows/references/ui-automation-guide.md` — RPA UIA guide to trim
- `skills/uipath-coded-workflows/references/coding-guidelines.md` — Fix-one-thing rule and iteration loop to trim
- `skills/uipath-rpa-workflows/references/validation-and-fixing.md` — Iteration loop, smoke test, Running UI Automation Workflows to trim
- `skills/uipath-coded-workflows/references/uip-guide.md` — Common CLI commands to trim
- `skills/uipath-rpa-workflows/references/cli-reference.md` — Common CLI commands to trim

### Shared files (targets for pointers)
- `skills/shared/uia-prerequisites.md` — UiAutomation prerequisites (Phase 1)
- `skills/shared/uia-configure-target-workflows.md` — Servo/indication workflows (Phase 1)
- `skills/shared/uia-debug-workflow.md` — Debug-first workflow procedure (Phase 1)
- `skills/shared/uia-selector-recovery.md` — Runtime selector failure recovery (Phase 1)
- `skills/shared/uia-multi-step-flows.md` — Multi-step UI flow patterns (Phase 1)
- `skills/shared/validation-loop.md` — Fix-one-thing rule, iteration loop, smoke test (Phase 2)
- `skills/shared/cli-reference.md` — Common CLI commands, global options, activity docs (Phase 2)

### Requirements
- `.planning/REQUIREMENTS.md` — INTEG-01, INTEG-02, INTEG-03 acceptance criteria

### Prior context
- `.planning/phases/01-extract-uiautomation-content/01-CONTEXT.md` — Phase 1 decisions (pure shared core, bridge sentences, file granularity)
- `.planning/phases/02-extract-guidelines-and-cli/02-CONTEXT.md` — Phase 2 decisions (what to trim, validate over get-errors, deferred trimming)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 7 shared files in `skills/shared/` ready to be referenced (5 UIA from Phase 1, 2 from Phase 2)
- Phase 1 divergence review doc at `.planning/phases/01-extract-uiautomation-content/` for reference on what was extracted

### Established Patterns
- Phase 1 convention: explicit relative paths (`../shared/...`) for cross-references
- Phase 1 convention: pure shared core with generic bridge sentences at paradigm boundaries
- Both SKILL.md files already use `[reference-name](references/file.md)` link format
- Section-per-topic structure in both UIA guides and CLI files

### Integration Points
- Both SKILL.md files are the entry points Claude loads first — shared refs here improve discovery speed
- Domain-specific guides are loaded on-demand when Claude needs detailed procedures
- Shared files are the single source of truth; domain files become thin wrappers for paradigm-specific content

</code_context>

<specifics>
## Specific Ideas

- Trim-to-pointer pattern should be consistent: section heading preserved, content replaced with single-line pointer using relative path
- SKILL.md changes should be minimal structural changes — update existing sections, don't reorganize

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-integrate-skills*
*Context gathered: 2026-03-31*
