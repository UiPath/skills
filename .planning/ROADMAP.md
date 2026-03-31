# Roadmap: UiPath Skills Reference Refactor

## Overview

Extract duplicated UiAutomation content from two skills into shared files, then update both skills to reference the shared location. Phase 1 creates shared UiAutomation files and flags near-duplicate content. Phase 2 extracts shared guidelines and CLI references. Phase 3 wires both skills to the shared files and verifies zero logic loss.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Extract UiAutomation Content** - Create shared files for UiAutomation prerequisites, servo tools, debug workflow, selector recovery, and multi-step UI patterns; flag near-duplicates (completed 2026-03-31)
- [x] **Phase 2: Extract Guidelines and CLI** - Create shared files for fix-one-thing rule, debug-first guidance, and common CLI commands; trim domain-specific CLI files (completed 2026-03-31)
- [x] **Phase 3: Integrate Skills** - Update both SKILL.md files and domain-specific guides to reference shared files; verify zero logic loss (completed 2026-03-31)

## Phase Details

### Phase 1: Extract UiAutomation Content
**Goal**: Shared UiAutomation reference files exist and contain all content currently duplicated across both skills, with near-identical variants flagged for human review
**Depends on**: Nothing (first phase)
**Requirements**: SHARED-01, SHARED-02, SHARED-03, SHARED-04, SHARED-05, FLAG-01
**Success Criteria** (what must be TRUE):
  1. A shared file exists for UiAutomation prerequisites (package version, servo setup) with content drawn from both skills
  2. A shared file exists for servo/indication tool workflows covering uia-configure-target, indicate-application, and indicate-element
  3. A shared file exists for the debug-first workflow procedure (StartDebugging, window baseline, cleanup)
  4. A shared file exists for runtime selector failure recovery procedure
  5. A shared file exists for multi-step UI flow patterns; a review document lists every near-identical content pair found with both variants preserved
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Extract shared files with content from both guides (prerequisites, servo workflows, multi-step flows)
- [x] 01-02-PLAN.md — Extract coded-only shared content (debug workflow, selector recovery) and create divergence review document

### Phase 2: Extract Guidelines and CLI
**Goal**: Shared files exist for the fix-one-thing rule, unified validation/iteration loop, smoke test, and common CLI commands
**Depends on**: Phase 1
**Requirements**: GUIDE-01, GUIDE-02, CLI-01, CLI-02
**Success Criteria** (what must be TRUE):
  1. A shared file contains the "fix one thing at a time" / single-fix-per-iteration rule with no duplication remaining in either skill's guidelines file
  2. A shared file contains the debug-first execution guidance (StartDebugging over StartExecution) with no duplication remaining in either skill's guidelines file
  3. A shared CLI reference file contains common `uip rpa` commands (validate, run-file, get-errors)
  4. Each skill's CLI file contains only the domain-specific usage examples not present in the shared CLI reference
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — Create shared validation-loop.md (fix-one-thing rule, iteration loop, smoke test)
- [x] 02-02-PLAN.md — Create shared cli-reference.md (8 common commands, global options, activity docs)

### Phase 3: Integrate Skills
**Goal**: Both skills load shared content via explicit references in SKILL.md; domain-specific guides are trimmed to only their paradigm-specific content; every instruction from the original files is accounted for
**Depends on**: Phase 2
**Requirements**: INTEG-01, INTEG-02, INTEG-03
**Success Criteria** (what must be TRUE):
  1. Both SKILL.md files reference the shared folder for UiAutomation content so Claude loads shared files at the relevant workflow steps
  2. Each skill's ui-automation-guide.md contains only C# or XAML-specific content respectively, with explicit pointers to the shared files for the extracted sections
  3. A verification pass confirms every instruction, example, and edge case from the original files is present in either a shared file or the trimmed domain-specific file — no content is lost
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md — Trim 6 domain reference files to pointers and update both SKILL.md files with shared/ references
- [ ] 03-02-PLAN.md — Build section-level verification checklist confirming zero logic loss

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Extract UiAutomation Content | 2/2 | Complete   | 2026-03-31 |
| 2. Extract Guidelines and CLI | 2/2 | Complete   | 2026-03-31 |
| 3. Integrate Skills | 2/2 | Complete   | 2026-03-31 |
