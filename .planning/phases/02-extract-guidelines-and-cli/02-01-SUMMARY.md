---
phase: 02-extract-guidelines-and-cli
plan: 01
subsystem: documentation
tags: [validation, iteration-loop, smoke-test, fix-one-thing]

requires:
  - phase: 01-extract-shared-uia-content
    provides: shared file pattern and paradigm-neutral conventions
provides:
  - shared validation-loop.md with fix-one-thing rule, iteration loop, and smoke test
affects: [02-02, 03-integrate-and-trim]

tech-stack:
  added: []
  patterns: [non-UIA shared file naming (no prefix)]

key-files:
  created: [skills/shared/validation-loop.md]
  modified: []

key-decisions:
  - "Listed DO NOT rules as numbered items under a Rules heading for scannability"
  - "Used generic <FILE> placeholder in all commands instead of extension-specific examples"

patterns-established:
  - "Non-UIA shared files use plain names (no uia- prefix)"

requirements-completed: [GUIDE-01, GUIDE-02]

duration: 1min
completed: 2026-03-31
---

# Phase 02 Plan 01: Shared Validation Loop Summary

**Paradigm-neutral validation-loop.md with fix-one-thing rule, 5-attempt iteration loop with DO NOT rules, and smoke test with when-to/when-not-to guidance**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-31T08:29:39Z
- **Completed:** 2026-03-31T08:30:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created shared validation-loop.md merging best elements from both skills
- Fix-one-thing rule stated generically without UIA-specific examples
- Unified iteration loop with validate command, 5 fix attempt cap, and all 5 DO NOT rules
- Smoke test procedure with when-to-run and when-not-to-run guidance
- GUIDE-02 confirmed as already satisfied by Phase 1's uia-debug-workflow.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shared validation-loop.md** - `4107dcf` (feat)

## Files Created/Modified
- `skills/shared/validation-loop.md` - Fix-one-thing rule, validation iteration loop, smoke test procedure

## Decisions Made
- Listed DO NOT rules as numbered items under a Rules heading for scannability (source had them as inline code block comments)
- Used generic `<FILE>` placeholder in all commands instead of `.xaml` or `.cs` examples
- Cross-reference to cli-reference.md included as a single line after the Rules section

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- validation-loop.md ready for cross-referencing from cli-reference.md (plan 02)
- Phase 3 can trim iteration loop and smoke test from both skill files

---
*Phase: 02-extract-guidelines-and-cli*
*Completed: 2026-03-31*
