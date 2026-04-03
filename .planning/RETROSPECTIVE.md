# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Genome Skills

**Shipped:** 2026-04-02
**Phases:** 2 | **Plans:** 4

### What Was Built
- Genome authoring skill: interview-based genome creation from user descriptions (8-step workflow, 3 complexity levels)
- Genome extraction skill: autonomous genome creation from existing UiPath projects (6-step analysis workflow, reads all file types)
- Shared genome infrastructure: template (10 sections), skill-mapping guide (5 skills, 7-rule decision tree)

### What Worked
- Authoring-before-extraction sequencing: Phase 1 established patterns (population matrix, critical rules, anti-patterns) that Phase 2 directly reused
- Deep reference material: extraction mapping guide with concrete tables (16 packages, 8 platform signals, 6 error patterns) gives agents specific lookup data instead of vague instructions
- Verification caught a real issue: cross-skill dependency on skill-mapping-guide.md was flagged and resolved by moving to shared/

### What Was Inefficient
- Phase 1 completion wasn't fully reflected in ROADMAP.md (Phase 1 checkbox still unchecked when Phase 2 started) — manual vs CLI state management gap
- Extraction executor placed skill-mapping-guide.md reference in authoring skill's directory despite CONTEXT.md noting it should be shared — the "reuse" framing was ambiguous

### Patterns Established
- `skills/shared/genome/` as the home for cross-skill genome assets (template, mapping guide)
- Autonomous "write first, offer edits" pattern for both genome skills
- Population matrix (10 sections x 3 complexity levels) as the canonical section depth guide

### Key Lessons
1. When CONTEXT.md says "reuse asset from skill X", the planner should proactively resolve the cross-skill reference issue (move to shared/) rather than creating the dependency and fixing it after verification
2. Markdown-only phases (no code, no tests) execute fast but still benefit from verification — the cross-skill violation wouldn't have been caught otherwise

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Key Pattern |
|-----------|--------|-------|-------------|
| v1.0 | 2 | 4 | Shared assets resolve cross-skill reuse |
