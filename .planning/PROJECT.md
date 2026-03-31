# UiPath Skills Reference Refactor

## What This Is

A collection of Claude Code skills that guide AI-assisted creation of UiPath automation workflows. Two skills — `uipath-coded-workflows` (C# coded automations) and `uipath-rpa-workflows` (XAML/RPA automations) — share significant UiAutomation reference content that is currently duplicated across both.

## Core Value

Eliminate duplicated UiAutomation reference content so changes are made once and reflected everywhere, without losing any logic from either skill.

## Requirements

### Validated

- SHARED-01 through SHARED-05: 5 shared files created in `skills/shared/` — Validated in Phase 1: Extract UiAutomation Content
- FLAG-01: Near-duplicate review document with 10 divergence items — Validated in Phase 1
- GUIDE-01: Fix-one-thing rule in `shared/validation-loop.md` with unified iteration loop — Validated in Phase 2: Extract Guidelines and CLI
- GUIDE-02: Debug-first execution guidance already satisfied by Phase 1's `shared/uia-debug-workflow.md` — Validated in Phase 2
- CLI-01: Common CLI commands in `shared/cli-reference.md` (8 commands, global options, activity docs) — Validated in Phase 2
- CLI-02: Shared CLI file created; skill file trimming deferred to Phase 3 — Partially validated in Phase 2
- INTEG-01: Both SKILL.md files reference shared/ for UiAutomation content — Validated in Phase 3: Integrate Skills
- INTEG-02: Domain-specific ui-automation-guide.md trimmed to paradigm-specific content with shared/ pointers — Validated in Phase 3
- INTEG-03: Zero logic loss verified via 119-section checklist across 8 files — Validated in Phase 3
- CLI-02: Skill CLI files trimmed to domain-specific commands only — Fully validated in Phase 3

### Active

None — all v1.0 requirements validated

### Out of Scope

- Refactoring domain-specific content (C# API patterns, XAML activity patterns) — these stay in their respective skills
- Changing skill triggering logic or SKILL.md descriptions
- Adding new features or documentation beyond what exists today

## Context

- Both skills target UiPath Studio automation but differ in paradigm: coded (C#) vs low-code (XAML)
- `ui-automation-guide.md` has ~70% overlap between the two skills (prerequisites, servo tools, indication, debug workflow, selector recovery)
- `uip-guide.md` (coded) and `cli-reference.md` (rpa) share CLI command documentation with different scope
- `coding-guidelines.md` and `validation-and-fixing.md` share the "fix one thing at a time" and debug-first patterns
- The repo has 7 skills total; only these 2 have significant duplication
- Near-identical content must be flagged for review, not silently merged

## Constraints

- **Zero logic loss**: Every instruction, example, and edge case must survive the refactor — flag near-duplicates for human review
- **Shared folder structure**: Common files live in a shared location referenced by both skills
- **Split by concern**: Shared files organized by topic so Claude loads only what's relevant at each step

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Multiple shared files by concern | Claude loads only relevant file at each step, not a monolith | Validated (Phase 1) |
| Domain-specific files stay in skill folders | C# vs XAML examples are not shareable | Validated (Phase 1) |
| Shared folder at `skills/shared/` | Parallel to skill folders, short relative paths | Validated (Phase 1) |
| Pure shared core with bridge sentences | No C#/XAML specifics in shared files; generic bridge text at paradigm boundaries | Validated (Phase 1) |
| Standardize on `validate` over `get-errors` | `validate` forces re-analysis; `get-errors` returns stale cached state | Validated (Phase 2) |
| Unified iteration loop (best of both) | RPA's DO NOT rules + coded's attempt caps merged into one loop | Validated (Phase 2) |
| GUIDE-02 satisfied by Phase 1 | `uia-debug-workflow.md` already covers StartDebugging guidance | Validated (Phase 2) |
| Section-heading + pointer trimming | Keep heading, replace content with one-line pointer to shared file | Validated (Phase 3) |
| Direct shared/ refs in SKILL.md | Claude loads SKILL.md first, so shared content is discoverable faster | Validated (Phase 3) |
| Trim all overlaps, not just Phase 2 deferrals | Single source of truth everywhere — any section in shared/ gets a pointer | Validated (Phase 3) |

---
*Last updated: 2026-03-31 after Phase 3 completion — all v1.0 phases complete*
