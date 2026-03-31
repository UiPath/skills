# Phase 1: Extract UiAutomation Content - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Create shared files for UiAutomation content currently duplicated across `uipath-coded-workflows` and `uipath-rpa-workflows`. Extract prerequisites, servo/indication workflows, debug procedure, selector recovery, and multi-step UI patterns into `skills/shared/`. Flag every near-identical content pair in a review document for human decision.

</domain>

<decisions>
## Implementation Decisions

### Shared folder location
- Shared files live at `skills/shared/`
- Single shared folder for all phases (UiAutomation in Phase 1, guidelines + CLI in Phase 2)
- Both SKILL.md files will use explicit relative paths (`../shared/uia-prerequisites.md`) — no glob patterns

### Content merge strategy
- Pure shared core: shared files contain ONLY truly shared content, no C#/XAML specifics
- Each section ends with a generic bridge sentence (e.g., "retrieve the target references for your workflow") so shared content reads standalone
- Paradigm-specific details (e.g., "re-read ObjectRepository.cs" vs "retrieve XAML snippets") stay in each skill's trimmed `ui-automation-guide.md`
- Sections unique to one skill (e.g., "Screen Handle Affinity" in coded, "Application Card" in RPA) stay untouched in their skill's guide — Phase 1 only extracts duplicated content

### Flagging format
- Comparison table in a markdown file: columns for Section, Coded Version, RPA Version, Difference Summary
- Review document lives at `.planning/phases/01-extract-uiautomation-content/` as a planning artifact (not permanent)
- Archived after human review resolves the differences

### File granularity
- 5 shared files matching requirements SHARED-01 through SHARED-05:
  - `uia-prerequisites.md` — package version check, upgrade commands (SHARED-01)
  - `uia-servo-workflows.md` — uia-configure-target flow AND indication fallback commands (SHARED-02)
  - `uia-debug-workflow.md` — StartDebugging procedure, window baseline, cleanup (SHARED-03)
  - `uia-selector-recovery.md` — runtime selector failure recovery procedure (SHARED-04)
  - `uia-multi-step-flows.md` — complete-then-advance pattern, servo refs vs UIA refs warning (SHARED-05)
- Shared files include CLI command examples (uip rpa, servo) since these are identical across both skills

### Claude's Discretion
- Exact section headings and ordering within shared files
- How to word generic bridge sentences at paradigm divergence points
- Whether to include cross-references between shared files (e.g., "see also uia-debug-workflow.md")

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source files (both variants needed for extraction)
- `skills/uipath-coded-workflows/references/ui-automation-guide.md` — Coded workflow variant of all UiAutomation content
- `skills/uipath-rpa-workflows/references/ui-automation-guide.md` — RPA workflow variant of all UiAutomation content

### Requirements
- `.planning/REQUIREMENTS.md` — SHARED-01 through SHARED-05, FLAG-01 acceptance criteria

### Project constraints
- `.planning/PROJECT.md` — Zero logic loss constraint, split-by-concern decision, domain files stay in skill folders

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Both `ui-automation-guide.md` files are the primary extraction source — ~70% shared content
- `references/activity-docs/UiPath.UIAutomation.Activities/` contains skill docs referenced by both guides (uia-configure-target, uia-improve-selector)

### Established Patterns
- Both skills use `../../references/` relative paths to reference activity docs
- Shared files will use `../shared/` relative paths from each skill
- Both guides follow the same section ordering: prerequisites → workflow pattern → target configuration → fallback → pitfalls → running → failures

### Integration Points
- Each skill's `ui-automation-guide.md` will be trimmed to paradigm-specific content with pointers to `skills/shared/`
- Each skill's `SKILL.md` will reference shared files with explicit paths (Phase 3 work)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-extract-uiautomation-content*
*Context gathered: 2026-03-31*
