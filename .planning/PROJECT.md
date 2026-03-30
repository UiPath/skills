# UiPath Skills Reference Refactor

## What This Is

A collection of Claude Code skills that guide AI-assisted creation of UiPath automation workflows. Two skills — `uipath-coded-workflows` (C# coded automations) and `uipath-rpa-workflows` (XAML/RPA automations) — share significant UiAutomation reference content that is currently duplicated across both.

## Core Value

Eliminate duplicated UiAutomation reference content so changes are made once and reflected everywhere, without losing any logic from either skill.

## Requirements

### Validated

(None yet — ship to validate)

### Active

(Defined in REQUIREMENTS.md)

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
| Multiple shared files by concern | Claude loads only relevant file at each step, not a monolith | -- Pending |
| Domain-specific files stay in skill folders | C# vs XAML examples are not shareable | -- Pending |

---
*Last updated: 2026-03-31 after milestone v1.0 start*
