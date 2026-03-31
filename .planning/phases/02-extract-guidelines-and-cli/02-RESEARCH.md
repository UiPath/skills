# Phase 2: Extract Guidelines and CLI - Research

**Researched:** 2026-03-31
**Domain:** Content extraction and deduplication (markdown reference files)
**Confidence:** HIGH

## Summary

This phase creates two new shared files (`shared/validation-loop.md` and `shared/cli-reference.md`) by extracting content duplicated across both skills. The work is straightforward text surgery — no code, no libraries, no APIs. The primary risk is incomplete extraction or accidental loss of domain-specific content that should remain in skill files.

All decisions are locked by CONTEXT.md. The source files are well-understood from direct reading. Phase 1 established the shared file pattern (topic-focused markdown in `skills/shared/`, paradigm-neutral language, relative-path cross-references).

**Primary recommendation:** Execute as two independent plans — one per shared file — since the files have no interdependencies.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- GUIDE-02 already satisfied by Phase 1's `shared/uia-debug-workflow.md` — no new file needed
- Shared guideline file named `shared/validation-loop.md` containing: fix-one-thing rule (generic, no UIA examples), unified iteration loop (merge RPA DO-NOT rules with coded attempt caps), standardize on `validate` over `get-errors`, smoke test section, skip focus-activity (RPA-only)
- Shared CLI file named `shared/cli-reference.md` with section-per-command format
- CLI commands included in shared: list-instances, start-studio, create-project, open-project, validate, run-file, get-errors, install-or-update-packages
- CLI commands excluded from shared: indicate-application, indicate-element (Phase 1 shared), inspect-package (coded-only), get-manual-test-cases/get-manual-test-steps (coded-only), find-activities/get-default-activity-xaml/list-workflow-examples/get-workflow-example/focus-activity (RPA-only)
- Global options and STUDIO_DIR/PROJECT_DIR resolution in shared CLI
- run-file documents both StartExecution and StartDebugging inline (no cross-reference to uia-debug-workflow.md)
- Activity docs discovery section included in shared CLI
- No example JSON responses in shared CLI — commands only
- Phase 2 does NOT trim skill files — trimming is Phase 3 (INTEG-02)

### Claude's Discretion
- Exact section ordering within shared files
- How to word the generic fix-one-thing rule without UIA-specific examples
- Whether to include cross-references between shared files

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GUIDE-01 | Extract "fix one thing at a time" / single-fix-per-iteration rule into shared file | Goes into `shared/validation-loop.md` — source content identified in coding-guidelines.md lines 114 and 174 |
| GUIDE-02 | Extract debug-first execution guidance (StartDebugging over StartExecution) into shared file | Already satisfied by Phase 1's `shared/uia-debug-workflow.md` — mark complete, no work needed |
| CLI-01 | Extract common `uip rpa` commands into shared reference | Goes into `shared/cli-reference.md` — 8 commands + global options + activity docs section |
| CLI-02 | Each skill retains only domain-specific CLI usage examples | Achieved by Phase 3 trimming; Phase 2 only creates the shared file. Both skill CLI files remain untouched in Phase 2 |
</phase_requirements>

## Architecture Patterns

### Established Shared File Pattern (from Phase 1)
```
skills/
  shared/
    uia-prerequisites.md          # Phase 1
    uia-configure-target-workflows.md  # Phase 1
    uia-debug-workflow.md         # Phase 1
    uia-multi-step-flows.md       # Phase 1
    uia-selector-recovery.md      # Phase 1
    validation-loop.md            # Phase 2 NEW
    cli-reference.md              # Phase 2 NEW
```

**Conventions observed in Phase 1 files:**
- Paradigm-neutral language (no C#/XAML-specific terms unless universally applicable)
- Self-contained — each file covers one topic completely
- Cross-references use relative paths: `[uia-selector-recovery.md](uia-selector-recovery.md)`
- No `uia-` prefix for non-UIA shared files (new naming pattern for Phase 2)
- Concise, procedural style — numbered steps for workflows, code blocks for commands

### File 1: `shared/validation-loop.md`

**Purpose:** Single source of truth for the fix-one-thing rule, validation iteration loop, and smoke test procedure.

**Content mapping from source files:**

| Section | Source (coded) | Source (RPA) | Merge Strategy |
|---------|---------------|--------------|----------------|
| Fix-one-thing rule | coding-guidelines.md L114 + L174 (anti-pattern) | validation-and-fixing.md L59 (DO NOT bundle) | Generic version — state principle abstractly without TypeInto/KeyboardShortcut example |
| Iteration loop | coding-guidelines.md L98-108 (validate loop, 5 attempts, file-path targeting) | validation-and-fixing.md L46-60 (get-errors loop, DO NOT rules) | Merge: use `validate` as command, keep 5 fix attempts cap, keep all 4 DO NOT rules, keep 2 runtime retries |
| Smoke test | Not present | validation-and-fixing.md L64-91 (when to run, when not to run, examples) | Lift from RPA, generalize file extension references |

**Key merge decisions (locked):**
- Standardize on `validate` (forces re-analysis) instead of `get-errors` (cached state)
- 5 validation fix attempts (from coded), 2 runtime retries (from coded)
- All 4 DO NOT rules from RPA: don't skip validation, don't assume edits worked, don't obsess on one error, don't bundle fixes
- `focus-activity` stays RPA-only — do NOT include in shared loop
- Smoke test uses generic `--file-path` without specifying `.xaml` or `.cs` extension

**Suggested section ordering:**
1. Fix-one-thing rule (the principle)
2. Validation iteration loop (the procedure that applies the principle)
3. Smoke test (what to do after validation passes)

### File 2: `shared/cli-reference.md`

**Purpose:** Single source of truth for CLI commands common to both skills.

**Content mapping from source files:**

| Section | Source (coded: uip-guide.md) | Source (RPA: cli-reference.md) | Merge Strategy |
|---------|------------------------------|-------------------------------|----------------|
| Global options | L13-39 (table + STUDIO_DIR + PROJECT_DIR) | Not explicit (inline in commands) | Lift from coded — already well-structured |
| list-instances | L45-53 | L62 (table row) | Use coded's section-per-command format |
| start-studio | L57-67 | L63 (table row) | Use coded's format, includes resolution waterfall |
| create-project | L71-95 | L54 (table row, uses `new` alias) | Use coded's format. Note: RPA uses `uip rpa new`, coded uses `uip rpa create-project` — same command |
| open-project | L98-106 | L55 (table row) | Use coded's format |
| validate | L110-148 | Not present as separate command (embedded in iteration loop) | Use coded's format — already complete |
| run-file | L152-180 | L48 (table row) | Use coded's format; include both StartExecution and StartDebugging inline per decision |
| get-errors | Not present as separate command | L45 (table row) | Create section from RPA's description; note `validate` is preferred when files changed |
| install-or-update-packages | Not present as separate command | L47 (table row) | Create section from RPA's description + validation-and-fixing.md L8-17 for details |
| Activity docs discovery | Not present | L15-25 (full section) | Lift from RPA — already well-structured |

**Format decision (locked):** Section-per-command with heading, description, code example, parameter table. No JSON response examples.

**Suggested section ordering:**
1. Introduction (CLI is self-documenting, `--help` pattern)
2. Global options (table + STUDIO_DIR + PROJECT_DIR resolution)
3. Activity docs discovery (primary API discovery method)
4. Commands — grouped logically:
   - Studio management: list-instances, start-studio
   - Project lifecycle: create-project, open-project
   - Validation & execution: validate, run-file, get-errors
   - Package management: install-or-update-packages

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Merging iteration loops | Copy-paste one version and patch | Side-by-side diff of both, take best elements from each | Easy to lose a DO NOT rule or cap value |
| CLI command docs | Rewrite from memory | Directly lift from source files, strip response examples | Ensures no parameter or flag is lost |

## Common Pitfalls

### Pitfall 1: Losing content during merge
**What goes wrong:** A DO NOT rule, an attempt cap, or a CLI parameter gets dropped during extraction.
**Why it happens:** The two source files use different structures (prose vs. table, numbered list vs. code block).
**How to avoid:** After creating each shared file, verify every piece of source content is accounted for — either in the shared file or explicitly marked as domain-specific (kept in skill file).
**Warning signs:** Shared file is noticeably shorter than the combined source content.

### Pitfall 2: Including domain-specific content in shared files
**What goes wrong:** UIA-specific examples (TypeInto/KeyboardShortcut), RPA-only commands (focus-activity), or coded-only commands (inspect-package) end up in shared files.
**Why it happens:** Source files mix generic and domain-specific content in the same section.
**How to avoid:** Check every example and command against the inclusion/exclusion lists in CONTEXT.md decisions.
**Warning signs:** Shared file mentions `.xaml` or `.cs` file extensions, or references C#/XAML-specific concepts.

### Pitfall 3: Inconsistent terminology between shared files
**What goes wrong:** validation-loop.md says "run `validate`" but cli-reference.md documents the command differently.
**Why it happens:** Files written independently without cross-checking.
**How to avoid:** Use identical command syntax in both files. The validation loop should reference the exact same command format documented in cli-reference.md.

### Pitfall 4: Accidentally modifying skill files
**What goes wrong:** Phase 2 trims or modifies the skill-specific files (coding-guidelines.md, validation-and-fixing.md, uip-guide.md, cli-reference.md).
**Why it happens:** Natural instinct to "complete" the refactoring by updating references.
**How to avoid:** Phase 2 scope is CREATE only — two new shared files. All trimming is Phase 3 (INTEG-02).

## Detailed Source Content Analysis

### Fix-One-Thing Rule — Sources

**Coded (coding-guidelines.md L114):**
> Fix one thing at a time — When a runtime error occurs, identify the root cause, fix ONLY that, and re-run. Never bundle a speculative "improvement" (e.g., switching from TypeInto to KeyboardShortcut) with the actual fix (e.g., correcting a selector). Changing two things at once makes it impossible to verify which change resolved the issue — or whether the speculative change introduced a new one.

**Coded anti-pattern restatement (L174):**
> Never make unrelated changes during retry — identify the root cause, fix only that, re-run and verify. Never bundle a speculative "improvement" with the actual fix (e.g., fixing a broken selector AND switching from TypeInto to KeyboardShortcut in the same edit). One change, one re-run.

**RPA (validation-and-fixing.md L59):**
> DO NOT bundle multiple fixes in one iteration. Fix the root cause, re-run, verify. Never add a speculative change alongside the actual fix — changing two things at once makes it impossible to tell which one resolved the issue or whether the extra change introduced a new problem.

**Generic version guidance:** Drop the TypeInto/KeyboardShortcut and selector examples. Keep the core principle: one fix per iteration, never bundle speculative improvements with actual fixes, re-run to verify.

### Iteration Loop — Sources

**Coded (coding-guidelines.md L98-108):**
- Uses `validate --file-path` command
- Notes `validate` forces re-analysis vs `get-errors` cached state
- 5 fix attempt cap
- File-level targeting with `--file-path`

**RPA (validation-and-fixing.md L46-60):**
- Uses `get-errors --file-path` command (to be changed to `validate`)
- 4 DO NOT rules: don't stop until resolved, don't obsess on one error, don't skip validation, don't assume edits worked, don't bundle fixes
- No explicit attempt cap
- Mentions `focus-activity` as optional step (excluded from shared)

**Merged loop structure:**
1. Run `validate --file-path --format json`
2. If 0 errors -> exit to smoke test
3. Identify highest-priority error
4. Fix one thing (fix-one-thing rule)
5. Goto 1
- Cap at 5 validation fix attempts
- 2 runtime retry attempts after smoke test
- All 4 DO NOT rules included

### Smoke Test — Source (RPA only, validation-and-fixing.md L64-91)

Content to lift (generalized):
- Explanation of why smoke test matters (different validation paths)
- `run-file` command with `--format json`
- When to run (3 conditions)
- When NOT to run (3 conditions)
- Runtime error loop-back guidance

### CLI Commands — Overlap Analysis

| Command | In coded uip-guide.md | In RPA cli-reference.md | Shared? |
|---------|----------------------|------------------------|---------|
| list-instances | Yes (section) | Yes (table row) | YES |
| start-studio | Yes (section) | Yes (table row) | YES |
| create-project | Yes (section, `create-project`) | Yes (table row, `new`) | YES |
| open-project | Yes (section) | Yes (table row) | YES |
| validate | Yes (section) | Yes (embedded in loop) | YES |
| run-file | Yes (section) | Yes (table row) | YES |
| get-errors | No (mentioned inline) | Yes (table row) | YES (per decision) |
| install-or-update-packages | No (mentioned inline) | Yes (table row) | YES (per decision) |
| inspect-package | Yes (mentioned inline) | No | NO (coded-only) |
| get-manual-test-cases | Yes (section) | Yes (table row) | NO (coded-only per decision) |
| get-manual-test-steps | Yes (section) | Yes (table row) | NO (coded-only per decision) |
| indicate-application | Yes (section) | Yes (table row) | NO (Phase 1 shared) |
| indicate-element | Yes (section) | Yes (table row) | NO (Phase 1 shared) |
| find-activities | No | Yes (table row) | NO (RPA-only) |
| get-default-activity-xaml | No | Yes (table row) | NO (RPA-only) |
| list-workflow-examples | No | Yes (table row) | NO (RPA-only) |
| get-workflow-example | No | Yes (table row) | NO (RPA-only) |
| focus-activity | No | Yes (table row) | NO (RPA-only) |
| close-project | No | Yes (table row) | NO (not in decision list) |

**Note on get-errors and install-or-update-packages:** These are in the inclusion list per CONTEXT.md but coded's uip-guide.md doesn't have dedicated sections for them. Content will need to be assembled from inline mentions (coding-guidelines.md L108 for get-errors, validation-and-fixing.md L8-13 for install-or-update-packages) plus RPA's table descriptions.

**Note on get-manual-test-cases/get-manual-test-steps:** Present in both files but excluded per decision (coded-only). This is a scope decision, not a content overlap question.

## Open Questions

1. **Cross-references between the two new shared files**
   - What we know: validation-loop.md uses `validate` and `run-file` commands that are documented in cli-reference.md
   - What's unclear: Whether to add a cross-reference like "See [cli-reference.md](cli-reference.md) for full command documentation"
   - Recommendation: Add a brief cross-reference in validation-loop.md pointing to cli-reference.md for full command details. Keeps the loop file focused on procedure rather than duplicating command parameters.

2. **`close-project` command disposition**
   - What we know: Present in RPA's cli-reference.md but not in the CONTEXT.md inclusion list
   - What's unclear: Intentional omission or oversight
   - Recommendation: Exclude per CONTEXT.md — the inclusion list is explicit

## Sources

### Primary (HIGH confidence)
- Direct reading of `skills/uipath-coded-workflows/references/coding-guidelines.md` — fix-one-thing rule, validation loop, anti-patterns
- Direct reading of `skills/uipath-rpa-workflows/references/validation-and-fixing.md` — iteration loop, DO NOT rules, smoke test
- Direct reading of `skills/uipath-coded-workflows/references/uip-guide.md` — full CLI reference, section-per-command format
- Direct reading of `skills/uipath-rpa-workflows/references/cli-reference.md` — CLI table format, activity docs section
- Direct reading of Phase 1 shared files — established patterns and conventions
- CONTEXT.md — all locked decisions

## Metadata

**Confidence breakdown:**
- Content extraction: HIGH — all source files read directly, content mapped line-by-line
- Merge strategy: HIGH — decisions locked by CONTEXT.md, no ambiguity
- Section ordering: MEDIUM — Claude's discretion, recommendations provided but planner may adjust

**Research date:** 2026-03-31
**Valid until:** Indefinite (content extraction, not technology-dependent)
