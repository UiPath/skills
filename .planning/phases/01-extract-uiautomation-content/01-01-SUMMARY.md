---
phase: 01-extract-uiautomation-content
plan: 01
subsystem: docs
tags: [markdown, deduplication, uiautomation, shared-content]

requires:
  - phase: none
    provides: n/a
provides:
  - "Shared prerequisites file (uia-prerequisites.md) with package version check and upgrade commands"
  - "Shared servo workflows file (uia-servo-workflows.md) with uia-configure-target usage and indication fallback"
  - "Shared multi-step flows file (uia-multi-step-flows.md) with complete-then-advance rule and servo workflow"
affects: [01-extract-uiautomation-content, 02-rewire-skill-guides]

tech-stack:
  added: []
  patterns: ["shared content extraction with generic bridge sentences at paradigm boundaries"]

key-files:
  created:
    - skills/shared/uia-prerequisites.md
    - skills/shared/uia-servo-workflows.md
    - skills/shared/uia-multi-step-flows.md
  modified: []

key-decisions:
  - "Used 'Indication Fallback Commands' as neutral heading (replacing coded's 'Fallback: Raw Indication Commands' and RPA's 'Low-Level Indication Tools')"
  - "Included coded-only 'Do NOT' warnings in shared servo file since they apply to both paradigms"
  - "Generic bridge sentences replace paradigm-specific post-configuration actions (ObjectRepository.cs vs XAML snippets)"

patterns-established:
  - "Shared file convention: paradigm-neutral content under skills/shared/ with relative cross-references"
  - "Bridge sentence pattern: end shared sections with generic action replacing coded/RPA-specific instructions"

requirements-completed: [SHARED-01, SHARED-02, SHARED-05]

duration: 2min
completed: 2026-03-31
---

# Phase 01 Plan 01: Extract Shared UiAutomation Content Summary

**Three shared reference files for prerequisites, servo/indication workflows, and multi-step UI flows extracted from both ui-automation-guide.md files**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T07:44:20Z
- **Completed:** 2026-03-31T07:46:20Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Created paradigm-neutral prerequisites file with package version check and upgrade commands
- Created servo workflows file with uia-configure-target usage, Do-NOT warnings, and indication fallback
- Created multi-step flows file with complete-then-advance rule, servo capture-advance cycle, and run-file warning
- All three files verified clean of paradigm-specific terms (ObjectRepository.cs, Descriptors., XAML, etc.)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shared prerequisites file** - `91c641e` (feat)
2. **Task 2: Create shared servo workflows file** - `3599524` (feat)
3. **Task 3: Create shared multi-step flows file** - `d7d87ec` (feat)

## Files Created/Modified
- `skills/shared/uia-prerequisites.md` - Package version requirement, check/upgrade commands, fallback reference
- `skills/shared/uia-servo-workflows.md` - uia-configure-target usage, glob discovery, Do-NOT warnings, indication fallback commands
- `skills/shared/uia-multi-step-flows.md` - Complete-then-advance rule, servo workflow steps, run-file warning, cross-reference to servo workflows

## Decisions Made
- Used "Indication Fallback Commands" as neutral heading replacing the differing section names in coded/RPA guides
- Included the two "Do NOT" warnings from coded guide in the shared servo file since they are universally applicable
- Bridge sentences use "retrieve the target references for your workflow" and "build the full workflow" to avoid "code"/"XAML" paradigm words

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Three shared files ready for consumption by both skill guides
- Plan 01-02 (review document / remaining shared files) can proceed
- Future phase will rewire SKILL.md files to reference these shared files via relative paths

## Self-Check: PASSED

All 3 created files verified on disk. All 3 task commits verified in git log.

---
*Phase: 01-extract-uiautomation-content*
*Completed: 2026-03-31*
