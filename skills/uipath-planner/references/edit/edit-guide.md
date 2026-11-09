# Editing Guide — change a genome in place

Content rules for what an edit writes: [genome-format-guide.md](../shared/genome-format-guide.md), and for an extracted genome [extracted-genome-guide.md](../shared/extracted-genome-guide.md). Only `edit` changes a genome; `uipath-genome` reads it and never edits it, so a fix found during a build comes back here and the build re-runs. Edits are targeted and in place, never a regeneration ([genome-format-guide.md § Write, Then Offer Edits](../shared/genome-format-guide.md)).

## Read Plan

The writing rules of [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) apply to every edit.

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole; [genome-format-guide.md](../shared/genome-format-guide.md) every section before § Design Links for a process genome and every section before § Process Genome Sections for a component genome (the level in the genome's first-line marker), plus § Design Links when the genome has a `Designed in:` line; [extracted-genome-guide.md](../shared/extracted-genome-guide.md) when the genome has a Source Map with a step table; [transactional-shape-guide.md](../shared/transactional-shape-guide.md) when the edit touches the Transactional Shape, or a step, rule or handler of a genome whose Transactional Shape is not the stub |
| a related resource is given | the genome is extracted and the user hands over a PDD, SOP, runbook or other resource beside the source | [extract-guide.md](../extract/extract-guide.md) Step 1 (the related-resources question) and Step 3's **Related resources** paragraph |
| partial re-extraction | — | [extract-guide.md](../extract/extract-guide.md), [defect-verification-guide.md](../shared/defect-verification-guide.md) and the source guide, as for `extract`; [extraction-parts-guide.md](../shared/extraction-parts-guide.md) when the list runs in parts |

Each phase's reads go out in at most three turns: turn 1 every file read whole and the heading list of every file read by section; turn 2 the sections chosen; turn 3 only what turn 2 routed to.

## Edits

### Any genome

| Request | Update |
|---|---|
| "The SDD was revised: update the genome" (from `uipath-genome`, or the user) | Read the SDD the `Designed in:` line links whole and redo [genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md) items 3–6 against it: every section whose SDD content changed is rewritten, nothing else is. Then take the SDD's fingerprint again and rewrite the `Designed in:` line ([genome-format-guide.md § Design Links](../shared/genome-format-guide.md)). An unattended build's request applies the edit without offering it; the closing summary names the sections changed |
| "Findings from `uipath-genome`" (from the build, or the user forwarding its report) | Apply each finding where it points: a checker `FAIL` → the section and rule it names ([genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md)); a genome deviation → the step the source contradicts, written as the build followed it unless the user rules otherwise; a retired skill name → the Build With row, from [skill-mapping-guide.md](../shared/skill-mapping-guide.md); a `Not covered` object to build → [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md). A build's request applies the edits without offering them |
| "Add detail to step X" | Workflow step X; add acceptance criteria if detail is testable |
| "Change complexity" / "complexity should be higher or lower" | Complexity section, then section depth per population matrix |
| "Add/remove an application" | Target Applications, Workflow, Build With, Acceptance Criteria |
| "Use a different skill for step X" | Build With row and rationale, validated against mapping guide |
| "Split this into components" | Promote to process genome: create process file, move component content into component files, add Handoffs |
| "Merge these two components" / "split this one" | Adjust Components, Handoffs, component files; re-check Interface agreement |
| "Scenario X signs in as persona Y" | Platform Dependencies (credential asset for Y), test component's row schema (asset name per row), Configuration Questions |
| "Remove the inferred flags" | Delete every `*[Inferred]*` — user confirmed the content |
| "Make it transactional" / "drop the transactional shape" | Transactional Shape (unit of work, As-is, outcomes, split options, evidence) or its stub; Platform Dependencies (the store the As-is names); Configuration Questions (retry counts) |
| "Step X should be a business exception" | Transactional Shape outcomes table; the rule under Business Rules for step X; an acceptance criterion for the recorded reason |
| "One row per transaction instead of one file" (change the unit of work) | Transactional Shape (Unit of work, Alternative units of work, As-is, outcomes, split options); Interface; Handoffs data passed; Platform Dependencies (store); Acceptance Criteria (duplicate and retry cases) |
| "Split the dispatcher into its own component" / "use one queue" / "apply the REFramework" / "drop the ledger" | A decision for the build, not a rewrite of what the genome describes: record it as the flow's `Decided:` line ([transactional-shape-guide.md](../shared/transactional-shape-guide.md) rule 8), and nowhere else. Edit the Transactional Shape itself only when what it describes changes — a new source, a new item kind, items that must now be shared |

### Extracted genomes

| Request | Update |
|---|---|
| "This step is wrong / missing" | Workflow, then Build With, Acceptance Criteria, Source Map |
| "Rename / reorder / remove steps" | Workflow and Source Map together, so every step still names its source objects |
| "Drop the Source Map" | Remove section from every file — genome is being shared as a blueprint; say target and data migration will no longer be possible from it |
| "Here is the PDD too" (any related resource) | A related resource of [extract-guide.md](../extract/extract-guide.md) Step 1: read it and write what it settles as Step 3's **Related resources** paragraph states |
| "Is this really a defect?" / "check it against the source" | Rerun both passes of [defect-verification-guide.md](../shared/defect-verification-guide.md) for that finding, and re-mark it in the body and its Source Map row by what the passes show |
| "Fix this defect in the rebuild" / "keep the source's behaviour" | A ruling: written at the step after the source fact, cited in the defect index's Rebuild follows cell, and carried into the step's Workflow lines, criteria and Source Map row ([extracted-genome-guide.md § Source Defects](../shared/extracted-genome-guide.md)) |
| "Also translate what is not covered", or an unused part | [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) with the objects of the Source Map's `Not covered` or `Unused` row the user names |
| "The source changed" / "finish the unread parts" | [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) with the changed or unread objects. Rerun extraction from its Step 1 ([extract-guide.md](../extract/extract-guide.md)) only when the components themselves changed (projects or root processes added, removed or regrouped); preserve user edits the source does not contradict and say which were kept |

## Review after every edit

After every edit, review what changed, and every component genome a process genome links that the edit touched, against [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) before answering. An extracted genome also takes the Source Map checks [extract-guide.md](../extract/extract-guide.md) Step 6b runs against its source. Fix what breaks a rule, then name what is left.

## Back to the Build

An edit `uipath-genome` requested, or a request that also asks to build, ends by invoking `uipath-genome` with `build "<GENOME_MD>"` and the user's build request quoted verbatim, after § Review after every edit. A finding the edit could not apply is named in that hand-off; the build reports it instead of handing it back again. `uipath-genome` not installed → end at the summary and say the build needs it. Any other edit ends at its summary.
