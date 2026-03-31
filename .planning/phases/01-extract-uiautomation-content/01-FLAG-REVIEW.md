# Near-Identical Content Review (FLAG-01)

This document flags every near-identical content pair found during Phase 1 extraction. Each row preserves both variants verbatim. A human decision is needed on which version to keep in the shared file, or how to merge them. After decisions are made, update the shared files accordingly and archive this document.

**Status:** Awaiting human review

## Comparison Table

| # | Section | Coded Version | RPA Version | Difference Summary |
|---|---------|---------------|-------------|-------------------|
| 1 | Prerequisites fallback link text | `see [Fallback: Raw Indication Commands](#fallback-raw-indication-commands)` | `see [Low-Level Indication Tools](#low-level-indication-tools-alternative)` | Different heading name for same section. Shared file uses neutral "indication tools" with link to uia-servo-workflows.md. |
| 2 | Post-uia-configure-target action | "re-read `ObjectRepository.cs` to get the descriptor paths" | "return the XAML snippet to use directly" | Different retrieval mechanism. Shared file uses generic bridge: "retrieve the target references for your workflow." |
| 3 | Multi-step flows final sentence | "build the full workflow code in one pass" | "build the full workflow XAML in one pass" | "code" vs "XAML". Shared file uses "build the full workflow in one pass". |
| 4 | Indication fallback post-indication | "re-reading `ObjectRepository.cs`, or retrieve the ready-to-use XAML snippets" | "retrieve the ready-to-use XAML snippets" | Coded mentions both retrieval paths; RPA mentions only XAML. Shared file uses generic bridge. |
| 5 | Indication fallback heading | `## Fallback: Raw Indication Commands` | `## Low-Level Indication Tools (Alternative)` | Different heading for same content. Shared file uses "## Indication Fallback Commands". |
| 6 | Common Pitfalls: SelectItem | Full C# code example with TypeInto workaround: `formScreen.TypeInto(Descriptors.MyApp.Form.Term, "12");` | Brief mention: "may fail on custom `<select>` elements; use Type Into as a workaround" | Coded has detailed C# workaround; RPA has brief mention. Both stay in respective skill files (paradigm-specific detail level). |
| 7 | Debug workflow procedure | Full procedure: StartDebugging, 5-step window baseline/cleanup (lines 177-203) | Not present | Coded-only content, believed paradigm-agnostic. Extracted as shared. **Needs human confirmation this applies to RPA workflows too.** |
| 8 | Selector recovery procedure | Full 6-step procedure with uia-improve-selector (lines 207-219) | Not present | Coded-only content, believed paradigm-agnostic. Extracted as shared. **Needs human confirmation this applies to RPA workflows too.** |
| 9 | "Capturing New UI Targets" section | Not present as separate section | Separate section (lines 125-141) with indicate-application examples including `--parent-id` | RPA has additional examples not in coded. **Decision needed: fold --parent-id examples into shared indication fallback, or keep RPA-specific?** |
| 10 | Step 3 "Do NOT" warnings | Two explicit warnings: don't call low-level CLI directly, don't launch app before configuring (lines 97-99) | Not present as explicit warnings | Coded has anti-pattern warnings absent from RPA. Extracted into shared file (good guidance for both). **Human should confirm.** |

## Decisions Needed

The following items require human input before proceeding:

1. **Item 7 -- Debug workflow as shared:** The StartDebugging + window baseline/cleanup procedure was extracted from coded-only into `skills/shared/uia-debug-workflow.md`. It uses only shared CLI tools (`uip rpa run-file`, `servo targets`, `servo window`). Confirm this applies to RPA workflows too.

2. **Item 8 -- Selector recovery as shared:** The 6-step runtime selector failure recovery was extracted from coded-only into `skills/shared/uia-selector-recovery.md`. It uses only shared tools (`uia-improve-selector`, `uip rpa`). Confirm this applies to RPA workflows too.

3. **Item 9 -- RPA "Capturing New UI Targets" section:** The RPA guide has a standalone section (lines 125-141) with `indicate-application` examples including `--parent-id` usage. The coded guide covers indication in its fallback section but lacks these additional examples. Decision: fold the `--parent-id` examples into the shared indication file, or keep them RPA-specific?

4. **Item 10 -- "Do NOT" anti-pattern warnings:** The coded guide has two explicit warnings at lines 97-99 (don't call low-level CLI directly, don't launch app before configuring). These are absent from the RPA guide. They were included in the shared content as generally useful. Confirm they apply to RPA workflows too.

## Resolution Instructions

For each row, mark the decision in a new "Resolution" column. Options:
- **keep coded** -- use the coded version in the shared file
- **keep RPA** -- use the RPA version in the shared file
- **merge as [description]** -- combine both, describe how
- **already handled in shared file** -- the shared extraction already resolved this
- **keep paradigm-specific** -- content stays in individual skill files, not shared

After all decisions, update shared files if needed and archive this document.
