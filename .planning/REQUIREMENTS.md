# Requirements: UiPath Skills Reference Refactor

**Defined:** 2026-03-31
**Core Value:** Eliminate duplicated UiAutomation reference content so changes are made once and reflected everywhere

## v1.0 Requirements

### Shared UiAutomation Content

- [x] **SHARED-01**: Extract UiAutomation prerequisites (package version, servo setup) into shared file
- [x] **SHARED-02**: Extract servo/indication tool workflows (uia-configure-target, indicate-application, indicate-element) into shared file
- [x] **SHARED-03**: Extract debug-first workflow procedure (StartDebugging, window baseline, cleanup) into shared file
- [x] **SHARED-04**: Extract runtime selector failure recovery procedure into shared file
- [x] **SHARED-05**: Extract multi-step UI flow patterns into shared file

### Shared Guidelines

- [x] **GUIDE-01**: Extract "fix one thing at a time" / single-fix-per-iteration rule into shared file
- [x] **GUIDE-02**: Extract debug-first execution guidance (StartDebugging over StartExecution) into shared file

### Shared CLI

- [x] **CLI-01**: Extract common `uip rpa` commands (validate, run-file, get-errors) into shared reference
- [x] **CLI-02**: Each skill retains only domain-specific CLI usage examples

### Skill Integration

- [x] **INTEG-01**: Both SKILL.md files updated to reference shared folder for UiAutomation content
- [x] **INTEG-02**: Each skill's domain-specific ui-automation-guide.md trimmed to only C#/XAML-specific content with pointers to shared files
- [x] **INTEG-03**: Verify zero logic loss — every instruction in current files accounted for in either shared or domain-specific location

### Flagging

- [x] **FLAG-01**: Near-identical content with minor differences flagged in a review document for human decision on which version to keep or how to merge

## Out of Scope

| Feature | Reason |
|---------|--------|
| Refactoring domain-specific content (C# API, XAML activities) | These are inherently different per skill paradigm |
| Changing SKILL.md triggering logic or descriptions | Out of scope — structural refactor only |
| Adding new documentation or features | Refactor preserves existing content, doesn't expand it |
| Refactoring skills beyond coded-workflows and rpa-workflows | Only these two have significant duplication |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SHARED-01 | Phase 1 | Complete |
| SHARED-02 | Phase 1 | Complete |
| SHARED-03 | Phase 1 | Complete |
| SHARED-04 | Phase 1 | Complete |
| SHARED-05 | Phase 1 | Complete |
| FLAG-01 | Phase 1 | Complete |
| GUIDE-01 | Phase 2 | Complete |
| GUIDE-02 | Phase 2 | Complete |
| CLI-01 | Phase 2 | Complete |
| CLI-02 | Phase 2 | Complete |
| INTEG-01 | Phase 3 | Complete |
| INTEG-02 | Phase 3 | Complete |
| INTEG-03 | Phase 3 | Complete |

**Coverage:**
- v1.0 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-27 after roadmap creation*
