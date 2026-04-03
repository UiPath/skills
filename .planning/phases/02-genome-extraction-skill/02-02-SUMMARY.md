---
phase: 02-genome-extraction-skill
plan: 02
subsystem: genome-extraction
tags: [genome, extraction, skill-definition, uipath, reverse-engineering]

# Dependency graph
requires:
  - phase: 01-genome-authoring-skill
    provides: "Genome template, skill-mapping-guide, population matrix, authoring patterns"
  - phase: 02-genome-extraction-skill/plan-01
    provides: "project-analysis-guide.md, extraction-mapping-guide.md, CODEOWNERS entry"
provides:
  - "Complete extraction SKILL.md for plugin discovery and agent activation"
  - "6-step extraction workflow (receive path, analyze files, infer complexity, map signals, write genome, offer edits)"
  - "9 critical rules for autonomous project analysis"
affects: [uipath-genome-extraction]

# Tech tracking
tech-stack:
  added: []
  patterns: [autonomous-extraction-pipeline, signal-to-genome-mapping, ambiguity-flagging]

key-files:
  created:
    - skills/uipath-genome-extraction/SKILL.md
  modified: []

key-decisions:
  - "Mirrored authoring skill structure exactly (9 rules, population matrix, anti-patterns) for consistency"
  - "Used ambiguity marker format *[Inferred from project signals]* as recommended in research"
  - "Referenced skill-mapping-guide.md from authoring skill rather than inlining Build With decision tree"

patterns-established:
  - "Extraction workflow: 6-step pipeline replacing authoring skill's 8-step interview"
  - "Ambiguity flagging: *[Inferred from project signals]* appended to uncertain content"
  - "Generalization pattern: hardcoded values become Configuration Questions with original as default"

requirements-completed: [EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05]

# Metrics
duration: 2min
completed: 2026-04-02
---

# Phase 2 Plan 2: Extraction SKILL.md Summary

**Complete extraction skill definition with 6-step analysis pipeline, 9 critical rules, population matrix, and 7 anti-patterns for reverse-engineering UiPath projects into genomes**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-02T17:25:56Z
- **Completed:** 2026-04-02T17:27:52Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created SKILL.md with valid YAML frontmatter (name matching folder, description with TRIGGER/DO NOT TRIGGER)
- Defined 9 critical rules parallel to the authoring skill: agent reads first, generalize don't transcribe, complexity from signals, behavioral descriptions, every section present, flag ambiguity, write immediately, one skill per step, blueprint preamble
- Defined 6-step extraction workflow replacing the authoring skill's 8-step interview: receive path, analyze files, infer complexity, map signals, write genome, offer edits
- Included population matrix (10 sections x 3 complexity levels) matching authoring skill exactly
- Linked all 4 reference files: genome-template.md, project-analysis-guide.md, extraction-mapping-guide.md, skill-mapping-guide.md
- Defined 7 anti-patterns including Integration Service misclassification and code-level acceptance criteria

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SKILL.md with extraction workflow and critical rules** - `2720fe6` (feat)

## Files Created/Modified
- `skills/uipath-genome-extraction/SKILL.md` - Complete extraction skill definition (128 lines) with frontmatter, critical rules, workflow, population matrix, reference navigation, and anti-patterns

## Decisions Made
- Mirrored authoring skill structure exactly (same section ordering, same number of critical rules, same population matrix values) to maintain consistency across genome-related skills
- Used `*[Inferred from project signals]*` as the ambiguity marker format, following the research recommendation for lightweight, searchable, removable flags
- Referenced skill-mapping-guide.md from the authoring skill directory rather than duplicating content, consistent with Plan 01's approach

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Extraction skill is complete: SKILL.md + 2 reference files + CODEOWNERS entry
- Plugin system can discover the skill via YAML frontmatter
- An agent can follow the skill to analyze any UiPath project and produce a genome

## Self-Check: PASSED

All files exist and all commits verified.

---
*Phase: 02-genome-extraction-skill*
*Completed: 2026-04-02*
