# Phase 1: Extract UiAutomation Content - Research

**Researched:** 2026-03-31
**Domain:** Markdown content extraction and deduplication
**Confidence:** HIGH

## Summary

This phase extracts duplicated UiAutomation content from two `ui-automation-guide.md` files (coded-workflows and rpa-workflows) into five shared files under `skills/shared/`. The work is pure content surgery: identify shared passages, extract them, and flag near-identical variants for human review.

Both source files were read and compared line-by-line. The overlap is high (~70% as estimated in PROJECT.md), with most shared content being verbatim-identical. Differences concentrate in paradigm-specific framing (C# `Descriptors` vs XAML snippets, `using` blocks vs Application Cards, `uiAutomation` service vs activities). The extraction is mechanical but requires precision to satisfy the zero-logic-loss constraint.

**Primary recommendation:** Extract shared content by working through each of the 5 target files sequentially, pulling verbatim-identical text first, then flagging divergent passages in the review document. Do not attempt to "merge" differing content — preserve both variants in the flag document.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Shared files live at `skills/shared/`
- Single shared folder for all phases (UiAutomation in Phase 1, guidelines + CLI in Phase 2)
- Both SKILL.md files will use explicit relative paths (`../shared/uia-prerequisites.md`) -- no glob patterns
- Pure shared core: shared files contain ONLY truly shared content, no C#/XAML specifics
- Each section ends with a generic bridge sentence so shared content reads standalone
- Paradigm-specific details stay in each skill's trimmed `ui-automation-guide.md`
- Sections unique to one skill stay untouched in their skill's guide -- Phase 1 only extracts duplicated content
- Comparison table in a markdown file: columns for Section, Coded Version, RPA Version, Difference Summary
- Review document lives at `.planning/phases/01-extract-uiautomation-content/` as a planning artifact
- 5 shared files: `uia-prerequisites.md`, `uia-servo-workflows.md`, `uia-debug-workflow.md`, `uia-selector-recovery.md`, `uia-multi-step-flows.md`
- Shared files include CLI command examples (uip rpa, servo) since these are identical across both skills

### Claude's Discretion
- Exact section headings and ordering within shared files
- How to word generic bridge sentences at paradigm divergence points
- Whether to include cross-references between shared files

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SHARED-01 | Extract UiAutomation prerequisites (package version, servo setup) into shared file | Prerequisites section is verbatim-identical in both files (lines 10-23 coded, lines 9-23 rpa); see Content Map below |
| SHARED-02 | Extract servo/indication tool workflows into shared file | uia-configure-target intro, indication fallback commands, and discovery glob are identical; framing paragraphs differ slightly |
| SHARED-03 | Extract debug-first workflow procedure into shared file | "Running UI Automation Workflows" section in coded (lines 177-203) has no equivalent section in RPA file -- this is coded-only content that needs careful handling |
| SHARED-04 | Extract runtime selector failure recovery procedure into shared file | "Runtime Selector Failures" section in coded (lines 207-219) has no equivalent in RPA file -- same concern as SHARED-03 |
| SHARED-05 | Extract multi-step UI flow patterns into shared file | Multi-step flows section is verbatim-identical in both files; only the final sentence differs ("build the full workflow code" vs "build the full workflow XAML") |
| FLAG-01 | Near-identical content flagged in review document | Multiple divergence points identified; see Divergence Inventory below |
</phase_requirements>

## Content Map: Source Files Compared

### Verbatim-Identical Sections (safe to extract as-is)

| Topic | Coded Lines | RPA Lines | Notes |
|-------|-------------|-----------|-------|
| Prerequisites (package version check, upgrade commands) | 10-23 | 9-23 | Identical including code blocks; only fallback link text differs ("Fallback: Raw Indication Commands" vs "Low-Level Indication Tools") |
| uia-configure-target intro paragraph | 83-89 | 48-54 | Identical: skill description, glob pattern, disclaimer |
| uia-configure-target invocation | 91-94 | 56-59 | Identical: window+element, window-only |
| Multi-step UI flows: complete-then-advance rule | 101-128 | 68-95 | Verbatim-identical warnings, servo workflow steps 1-4, "Do NOT use run-file" warning; only last sentence differs |
| Indication fallback: CLI commands | 132-150 | 101-121 | Core commands identical; post-indication retrieval differs (coded mentions ObjectRepository.cs, RPA focuses on XAML snippets) |
| servo refs vs UIA refs warning | 109 | 76 | Identical warning block |

### Sections That Differ (paradigm-specific, stay in skill files)

| Topic | Coded | RPA | Nature of Difference |
|-------|-------|-----|---------------------|
| Opening framing | "using the `uiAutomation` service" + IUiAutomationAppService | "using UiPath UIAutomation activities" | Paradigm identity |
| API reference path | `coded/` subfolder | `activities/` subfolder | Different doc sets |
| Workflow Pattern (coded) | Open/Attach returns UiTargetApp, IDisposable | N/A | Coded-only; C# API pattern |
| Screen Handle Affinity (coded) | UiTargetApp handle binding, C# code example | N/A | Coded-only |
| Target Resolution (coded) | string, IElementDescriptor, TargetAnchorableModel, RuntimeTarget | N/A | Coded-only; C# types |
| Finding Descriptors (coded) | 4-step decision tree, ObjectRepository.cs | N/A | Coded-only; C# descriptor system |
| Application Card (RPA) | N/A | NApplicationCard, Use Application/Browser | RPA-only |
| Target Configuration (RPA) | N/A | Selector, Anchor, CV, Fuzzy selector | RPA-only |
| Object Repository (RPA) | N/A | .objects/ directory, reference strings | RPA-only |
| Common Activities table (RPA) | N/A | Activity reference table | RPA-only |
| Common Pitfalls | C# SelectItem workaround, Screen Handle Mismatch | Missing xmlns, wrong OR refs, SelectItem, ScreenPlay overuse | Partially overlapping |
| Running workflows / debug | Full procedure with servo targets baseline | N/A in current file | See SHARED-03 concern below |
| Selector failure recovery | Full 6-step procedure | N/A in current file | See SHARED-04 concern below |

## Architecture Patterns

### Extraction Strategy

The extraction follows a consistent pattern for each shared file:

1. **Identify the verbatim-identical core** from both source files
2. **Strip paradigm-specific framing** (C# types, XAML snippets, coded-only API references)
3. **End with a generic bridge sentence** where the shared content meets paradigm-specific territory
4. **Log every divergence** in the review document (FLAG-01)

### Recommended Shared File Structure

```
skills/
  shared/
    uia-prerequisites.md
    uia-servo-workflows.md
    uia-debug-workflow.md
    uia-selector-recovery.md
    uia-multi-step-flows.md
```

Each shared file should be self-contained with a clear title, no assumptions about which skill is consuming it, and bridge sentences at paradigm boundaries.

### Cross-References Between Shared Files

Recommended: yes, include them. The debug workflow references selector recovery ("follow the Running UI Automation Workflows procedure"), and multi-step flows reference the servo workflow. Use relative links: `[see uia-debug-workflow.md](uia-debug-workflow.md)`.

## Critical Finding: SHARED-03 and SHARED-04

The debug-first workflow procedure (SHARED-03) and runtime selector failure recovery (SHARED-04) exist **only in the coded-workflows guide**. The RPA guide has no equivalent sections.

This raises a question: is this content truly shared, or is it coded-only?

**Analysis:** The procedures themselves are paradigm-agnostic. They use `uip rpa run-file --command StartDebugging` (same CLI for both), `servo targets` (same tool), and `uia-improve-selector` (same skill). The only coded-specific detail in SHARED-03 is that it references `ObjectRepository.cs` in step 3 of selector recovery. The RPA equivalent would reference `.objects/` metadata files.

**Conclusion:** These procedures SHOULD be shared -- they're currently missing from the RPA guide (likely an oversight during original authoring). Extracting them as shared files makes both skills benefit. The review document should flag this as "content present in coded only, believed to be applicable to both, needs human confirmation."

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Content diffing | Manual side-by-side comparison | Systematic section-by-section mapping (done in this research) | The files have different structures; naive diff produces noise |
| Merge decisions | Auto-merging near-identical text | FLAG-01 review document for human decision | Zero-logic-loss constraint requires human review of any non-identical merge |

## Common Pitfalls

### Pitfall 1: Silently Dropping Content
**What goes wrong:** During extraction, a sentence or edge case present in only one variant gets lost.
**Why it happens:** Extracting "shared" content by copying from one file and ignoring the other.
**How to avoid:** For each shared file, verify every sentence against BOTH source files. Any sentence present in one but not the other must either stay in the skill-specific file or be flagged in the review document.
**Warning signs:** Shared file is shorter than the longest source section.

### Pitfall 2: Leaking Paradigm-Specific Content into Shared Files
**What goes wrong:** Shared file mentions `ObjectRepository.cs`, `Descriptors`, `using` blocks, XAML snippets, or activity names.
**Why it happens:** Copying verbatim from one source without stripping paradigm-specific terms.
**How to avoid:** After writing each shared file, grep for: `ObjectRepository.cs`, `Descriptors.`, `using `, `.xaml`, `NApplicationCard`, `IDisposable`, `UiTargetApp`, `TargetAnchorable`, `xmlns:`.
**Warning signs:** Any C# or XAML syntax in a shared file.

### Pitfall 3: Broken Internal Links After Extraction
**What goes wrong:** Source files have internal anchor links (e.g., `#fallback-raw-indication-commands`) that break after content moves.
**Why it happens:** Extracting sections without updating cross-references.
**How to avoid:** After extraction, verify all internal links in both trimmed source files and all shared files.

### Pitfall 4: Inconsistent Fallback Section Naming
**What goes wrong:** Coded calls it "Fallback: Raw Indication Commands", RPA calls it "Low-Level Indication Tools (Alternative)". The shared version needs one name.
**Why it happens:** Original authors used different headings for the same content.
**How to avoid:** Pick a neutral name for the shared file, flag the naming difference in the review document.

## Divergence Inventory (Input for FLAG-01)

These are the near-identical content pairs that need flagging:

| # | Section | Coded Version | RPA Version | Difference |
|---|---------|---------------|-------------|------------|
| 1 | Prerequisites fallback link | "see Fallback: Raw Indication Commands" | "see Low-Level Indication Tools" | Different heading name |
| 2 | uia-configure-target result | "re-read ObjectRepository.cs to get the descriptor paths" | "return the XAML snippet to use directly" | Different post-configuration action |
| 3 | Multi-step flows final sentence | "build the full workflow code in one pass" | "build the full workflow XAML in one pass" | "code" vs "XAML" |
| 4 | Indication fallback: post-indication | "re-reading ObjectRepository.cs, or retrieve the ready-to-use XAML snippets" | "retrieve the ready-to-use XAML snippets" (only XAML) | Coded mentions both paths |
| 5 | Indication fallback heading | "Fallback: Raw Indication Commands" | "Low-Level Indication Tools (Alternative)" | Different heading |
| 6 | Common Pitfalls: SelectItem | C# code example with TypeInto workaround | Brief mention: "may fail on custom select elements" | Different detail level |
| 7 | Debug workflow | Full procedure (lines 177-203) | Not present | Coded-only, believed applicable to both |
| 8 | Selector recovery | Full 6-step procedure (lines 207-219) | Not present | Coded-only, believed applicable to both |
| 9 | Indication: "Capturing New UI Targets" | Not present as separate section | Separate section (lines 125-141) with additional examples | RPA has extra examples for indicate-application with --parent-id |
| 10 | Step 3 "Do NOT" warnings | Two warnings: don't call low-level CLI directly, don't launch app before configuring | Not present as explicit warnings | Coded has explicit anti-pattern warnings |

## Extraction Plan per Shared File

### uia-prerequisites.md (SHARED-01)
**Source:** Both files, "Prerequisites" section
**Content:** Package version requirement, version check command, upgrade command, fallback warning
**Bridge sentence:** "If the user declines, warn that `uip rpa uia` commands will fail and fall back to the indication tools."
**Divergence:** Link text for fallback differs (flag #1) -- use generic wording in shared file

### uia-servo-workflows.md (SHARED-02)
**Source:** Both files, "uia-configure-target" intro + skill invocation + indication fallback
**Content:** Skill description, glob discovery, invocation syntax (window+element, window-only), skill search behavior, "Do NOT" warnings (from coded), indication fallback commands
**Bridge sentence:** "After configuration, retrieve the target references for your workflow." (generic -- coded reads ObjectRepository.cs, RPA gets XAML)
**Divergences:** Flags #2, #4, #5, #9, #10 -- the "Do NOT" warnings from coded should be included in shared (they're good guidance for both); the RPA extra examples for indicate-application with --parent-id should be flagged

### uia-debug-workflow.md (SHARED-03)
**Source:** Coded file only, "Running UI Automation Workflows" section
**Content:** StartDebugging requirement, window baseline procedure (servo targets before/after), Stop command, window cleanup
**Bridge sentence:** None needed -- procedure is self-contained
**Divergence:** Flag #7 -- content exists only in coded, needs human confirmation it applies to RPA too. The procedure uses only shared tools (uip rpa run-file, servo) so it should apply.

### uia-selector-recovery.md (SHARED-04)
**Source:** Coded file only, "Runtime Selector Failures" section
**Content:** Error recognition, 6-step recovery procedure, uia-improve-selector skill reference
**Bridge sentence:** Needs generic wording at step 3 where coded mentions "ObjectRepository.cs or OR .metadata files"
**Divergence:** Flag #8 -- coded mentions ObjectRepository.cs specifically; shared version should say "Object Repository files" generically

### uia-multi-step-flows.md (SHARED-05)
**Source:** Both files, "Multi-Step UI Flows" section
**Content:** Complete-then-advance rule, servo warnings, 4-step capture-advance cycle, "Do NOT use run-file" warning
**Bridge sentence:** "After all targets are captured, build the full workflow using all the collected OR references." (drops "code"/"XAML")
**Divergence:** Flag #3 -- trivial word difference in final sentence

## Open Questions

1. **SHARED-03 and SHARED-04: applicable to RPA?**
   - What we know: The procedures use CLI tools (uip rpa, servo) that work identically for both paradigms. No XAML or C# specifics in the procedure steps themselves.
   - What's unclear: Whether the RPA guide intentionally omitted these or it was an oversight.
   - Recommendation: Extract as shared, flag in review document for human confirmation. The content is objectively useful for both.

2. **RPA "Capturing New UI Targets" section (lines 125-141)**
   - What we know: This section has additional indicate-application examples (with --parent-id) not in the coded guide. It partially overlaps with the indication fallback section.
   - What's unclear: Whether this extra content should be folded into the shared indication file or stay RPA-specific.
   - Recommendation: Flag in review document. The --parent-id example is useful for both paradigms.

## Sources

### Primary (HIGH confidence)
- `skills/uipath-coded-workflows/references/ui-automation-guide.md` -- full file read, 228 lines
- `skills/uipath-rpa-workflows/references/ui-automation-guide.md` -- full file read, 178 lines
- `.planning/phases/01-extract-uiautomation-content/01-CONTEXT.md` -- user decisions
- `.planning/REQUIREMENTS.md` -- requirement definitions
- `.planning/PROJECT.md` -- zero-logic-loss constraint

## Metadata

**Confidence breakdown:**
- Content mapping: HIGH -- both source files fully read and compared
- Extraction strategy: HIGH -- straightforward content surgery on known inputs
- Divergence inventory: HIGH -- systematic comparison completed
- SHARED-03/04 applicability: MEDIUM -- logical analysis says yes, but human confirmation needed

**Research date:** 2026-03-31
**Valid until:** Indefinite (source files are the ground truth; re-research only if source files change)
