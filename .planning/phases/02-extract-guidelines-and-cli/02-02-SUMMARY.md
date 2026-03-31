---
phase: 02-extract-guidelines-and-cli
plan: 02
subsystem: docs
tags: [cli, uip, shared-reference]

requires:
  - phase: 01-extract-shared-uiautomation
    provides: shared file pattern and uia-configure-target-workflows.md (indicate commands excluded from CLI)
provides:
  - shared CLI reference with 8 common uip rpa commands
  - global options and STUDIO_DIR/PROJECT_DIR resolution docs
  - activity docs discovery section
affects: [03-integrate-shared-references]

tech-stack:
  added: []
  patterns: [section-per-command format for CLI docs]

key-files:
  created: [skills/shared/cli-reference.md]
  modified: []

key-decisions:
  - "Used coded uip-guide.md as structural template (section-per-command format)"
  - "No example JSON responses per context decisions"
  - "run-file documents both StartExecution and StartDebugging inline"

patterns-established:
  - "Non-UIA shared files use plain names (no uia- prefix)"
  - "Section-per-command: heading, description, code example, parameter table"

requirements-completed: [CLI-01, CLI-02]

duration: 1min
completed: 2026-03-31
---

# Phase 02 Plan 02: Shared CLI Reference Summary

**Shared CLI reference with 8 common uip rpa commands, global options, STUDIO_DIR/PROJECT_DIR resolution, and activity docs discovery**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-31T08:29:43Z
- **Completed:** 2026-03-31T08:31:04Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `skills/shared/cli-reference.md` with all 8 common commands in section-per-command format
- Included global options table with STUDIO_DIR 3-step resolution waterfall and PROJECT_DIR resolution
- Documented both StartExecution and StartDebugging variants inline in run-file section
- Included activity docs discovery section with .local/docs/packages/ access patterns
- Excluded all domain-specific commands (indicate-*, inspect-package, find-activities, focus-activity, test manager commands)

## Task Commits

1. **Task 1: Create shared cli-reference.md** - `dd63a0d` (feat)

## Files Created/Modified
- `skills/shared/cli-reference.md` - Shared CLI reference for both coded and RPA skills

## Decisions Made
- Used coded's uip-guide.md as structural template -- already had section-per-command format with parameter tables
- Merged RPA's progressive --help discovery pattern into the introduction
- Mentioned `uip rpa new` alias in create-project section per plan
- Excluded example JSON responses per context decisions -- commands only

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Shared CLI reference ready for Phase 3 integration (INTEG-02) where skill-specific CLI files will be trimmed to domain-specific content only
- Both skill CLI files remain untouched per Phase 2 scope

## Self-Check: PASSED

- FOUND: skills/shared/cli-reference.md
- FOUND: dd63a0d (task 1 commit)

---
*Phase: 02-extract-guidelines-and-cli*
*Completed: 2026-03-31*
