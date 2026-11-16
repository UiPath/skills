# Editing Guide — change a genome in place

Content rules for what an edit writes: [genome-format-guide.md](../shared/genome-format-guide.md), and for an extracted genome [extracted-genome-guide.md](../shared/extracted-genome-guide.md). Only `edit` changes a genome; `uipath-genome` reads it and never edits it, so a deviation the build reports comes back here and the build re-runs. Every edit ends with the strict check (§ Review after every edit). Edits are targeted and in place, never a regeneration ([genome-format-guide.md § Write, Then Offer Edits](../shared/genome-format-guide.md)).

## Read Plan

The writing rules of [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) apply to every edit.

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole; [genome-format-guide.md](../shared/genome-format-guide.md) every section before § Design Links for a process genome and every section before § Process Genome Sections for a component genome (the level in the genome's first-line marker), plus § Design Links when the genome has a `Designed in:` or `Preferences:` line; [extracted-genome-guide.md](../shared/extracted-genome-guide.md) when the genome has a Source Map with a step table; [transactional-shape-guide.md](../shared/transactional-shape-guide.md) when the edit touches the Transactional Shape, or a step, rule or handler of a genome whose Transactional Shape is not the stub; [sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md) and [open-questions-guide.md](../shared/open-questions-guide.md) whole |
| a related resource is given | the genome is extracted and the user hands over a PDD, SOP, runbook or other resource beside the source | [extract-guide.md](../extract/extract-guide.md) Step 1 (the related-resources question) and Step 3's **Related resources** paragraph |
| "The SDD was revised: update the genome" | — | [genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md) whole, plus the rows of its own Read Plan |
| "Findings from `uipath-genome`" | a finding names a Build With skill (a retired name) | [skill-mapping-guide.md](../shared/skill-mapping-guide.md) |
| partial re-extraction | — | [extract-guide.md](../extract/extract-guide.md), [defect-verification-guide.md](../shared/defect-verification-guide.md) and the source guide, as for `extract`; [extraction-parts-guide.md](../shared/extraction-parts-guide.md) when the list runs in parts |

Each phase's reads go out in at most three turns: turn 1 every file read whole and the heading list of every file read by section; turn 2 the sections chosen; turn 3 only what turn 2 routed to.

## Edits

### Any genome

On a genome with a `Designed in:` line, a change to what the SDD holds — products, projects, components and their skills, and the decisions the SDD records (the split and queue design, the implementation mode, the package pins, the refactor answers) — goes to `design` to revise the linked SDD, and the same run then applies "The SDD was revised" to update the genome ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current). Every other row (complexity, inferred flags, wording, step detail, a finding from `uipath-genome`) applies as written.

| Request | Update |
|---|---|
| "The SDD was revised: update the genome" (after a `design` revise, or from the user) | Read the SDD the `Designed in:` line links whole and redo [genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md) items 3–6 against it: every section whose SDD content changed is rewritten, nothing else is. Then take the fingerprint again, over the root and every child SDD it lists for a solution, and rewrite the `Designed in:` line ([genome-format-guide.md § Design Links](../shared/genome-format-guide.md)). A run that follows a `design` revise, or an unattended request, applies the edit without offering it; the closing summary names the sections changed |
| "Findings from `uipath-genome`" (from the build's completion report, or the user forwarding it) | Apply each finding where it points: a genome deviation → the step the source contradicts, written as the build followed it unless the user rules otherwise; a retired skill name → the Build With row, from [skill-mapping-guide.md](../shared/skill-mapping-guide.md); a `Not covered` object to build → [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md). A build's request applies the edits without offering them |
| "Write the SDD" (a genome written before it had one, or one whose SDD the user wants written again) | The SDD from the genome ([sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md)). A genome with no Open Decisions section gets it first, every point left to a person entered and its marks naming their entries ([genome-format-guide.md § Open Decisions](../shared/genome-format-guide.md)); nothing else in the genome changes |
| "Apply the answers" (the user filled in the SDD's Action Required or the readiness file, answered in a reply or an interview (§ Interview), or `uipath-genome` sent them back) | Each item answered, changed or under a filled `Confirmed:` line whose answer alters the genome, matched by its id. A reply's id is checked against what its item asks, and two answers to one id go to the user with both. The items are those of the SDD's Business decisions, Material to supply and Preferences; of the readiness file's Architecture decisions whose `Recorded in:` line names a genome section; each line of its Edits for `uipath-planner`; and the SDD items the readiness file lists as still open. Each is applied as the row of this guide it is:<br>- a ruling, a defect named under Defects the rebuild fixes, and a confirmed recommendation the genome does not build yet, as "Fix this defect in the rebuild" / "keep the source's behaviour";<br>- a confirmed reading loses its marker; a changed one, or a discrepancy the owner rules for the resource, as "This step is wrong / missing";<br>- an export given, or an object to translate, as a partial re-extraction;<br>- a resource as "Here is the PDD too";<br>- a preferences file as the `Preferences:` line, the genome then brought in line with it ([genome-format-guide.md § Design Links](../shared/genome-format-guide.md));<br>- a split as the flow's `Decided:` line, its source `the request` with the answer quoted;<br>- any other Architecture decision in the section its `Recorded in:` line names, as the row of that section's subject (a technology: "Add/remove an application");<br>- a line of Edits for `uipath-planner` as the row of what it finds wrong, once the genome and the source confirm it, otherwise marked `Not applied:` with what they show.<br><br>On a genome with a `Designed in:` line, an item taken from the SDD's own design goes to `design` first (§ Any genome). An answer that leaves the genome as it stands (an object left out, the source kept, a business outcome confirmed as built) changes no step. Every entry an answer settles reads decided ([genome-format-guide.md § Open Decisions](../shared/genome-format-guide.md)). The readiness file's applied items are marked `Applied <YYYY-MM-DD>: <what it wrote>` (`the Recommended option` for an accepted one); configuration values stay as answered, for the build. A request from `uipath-genome` applies the edits without offering them |
| "The SDD was edited: update the genome" (the user changed a section other than Action Required, of an SDD written from the genome) | Read each changed section against the genome, and apply each change as the row of this guide it is (a step, a rule, an application, a component). In a migration, a change that departs from the source goes to the user first. The SDD is then written again from the genome |
| "Add detail to step X" | Workflow step X; add acceptance criteria if detail is testable |
| "Change complexity" / "complexity should be higher or lower" | Complexity section, then section depth per population matrix |
| "Add/remove an application" | Target Applications, Workflow, Build With, Acceptance Criteria |
| "Use a different skill for step X" | Build With row and rationale, validated against mapping guide |
| "Split this into components" | Promote to process genome: create process file, move component content into component files, add Handoffs |
| "Merge these two components" / "split this one" | Adjust Components, Handoffs, component files; re-check Interface agreement |
| "Scenario X signs in as persona Y" | Platform Dependencies (credential asset for Y), test component's row schema (asset name per row), Configuration Questions |
| "Remove the inferred flags" | Delete every `*[Inferred: …]*` mark, since the user confirmed the content; each reading entry the marks named reads decided |
| "Make it transactional" / "drop the transactional shape" | Transactional Shape (unit of work, As-is, outcomes, split options, evidence) or its stub; Platform Dependencies (the store the As-is names); Configuration Questions (retry counts) |
| "Step X should be a business exception" | Transactional Shape outcomes table; the rule under Business Rules for step X; an acceptance criterion for the recorded reason |
| "One row per transaction instead of one file" (change the unit of work) | Transactional Shape (Unit of work, Alternative units of work, As-is, outcomes, split options); Interface; Handoffs data passed; Platform Dependencies (store); Acceptance Criteria (duplicate and retry cases) |
| "Split the dispatcher into its own component" / "use one queue" / "apply the REFramework" / "drop the ledger" | A decision for the build, not a rewrite of what the genome describes: record it as the flow's `Decided:` line ([transactional-shape-guide.md](../shared/transactional-shape-guide.md) rule 8). Edit the Transactional Shape itself only when what it describes changes — a new source, a new item kind, items that must now be shared. A split that drops a store of the flow's Coordination row rewrites the genome as that guide's rule 3 states |

### Extracted genomes

| Request | Update |
|---|---|
| "This step is wrong / missing" | Workflow, then Build With, Acceptance Criteria, Source Map |
| "Rename / reorder / remove steps" | Workflow and Source Map together, so every step still names its source objects |
| "Retire / fold / rebuild `<component>` on `<product>`" (a refactor or migration target) | The refactor answer, as [extract-guide.md](../extract/extract-guide.md) Step 6c records it: the component's Build With / Components row and the `Requested change` row; a split it decides → the flow's `Decided:` line |
| "Drop the Source Map" | Remove section from every file — genome is being shared as a blueprint; say target and data migration will no longer be possible from it |
| "Here is the PDD too" (any related resource) | A related resource of [extract-guide.md](../extract/extract-guide.md) Step 1: read it and write what it settles as Step 3's **Related resources** paragraph states |
| "Is this really a defect?" / "check it against the source" | Rerun both passes of [defect-verification-guide.md](../shared/defect-verification-guide.md) for that finding, and re-mark it in the body and its Source Map row by what the passes show |
| "Fix this defect in the rebuild" / "keep the source's behaviour" | A ruling: written at the step after the source fact, cited in the defect index's Rebuild follows cell, and carried into the step's Workflow lines, criteria and Source Map row; an evident intent the ruling confirms loses its marker, and the defect's entry reads decided ([extracted-genome-guide.md § Source Defects](../shared/extracted-genome-guide.md)) |
| "Also translate what is not covered", or an unused part | [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) with the objects of the Source Map's `Not covered` or `Unused` row the user names |
| "The source changed" / "finish the unread parts" | [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) with the changed or unread objects. Rerun extraction from its Step 1 ([extract-guide.md](../extract/extract-guide.md)) only when the components themselves changed (projects or root processes added, removed or regrouped); preserve user edits the source does not contradict and say which were kept |

## Interview

`interview` asks the open items of the SDD's Action Required, and of the readiness file when one exists beside the genome, then applies the answers. It asks only what nothing else answers: an item the request, an answers file, the preferences file or a filled `Confirmed:` line already settles is never asked.

1. **How to answer.** One structured question comes first, skipped when the request already says. Its options:
   - every item, a batch at a time (Recommended when an item has no default);
   - only what needs a decision: the items with no default and the business outcomes, the rest keeping their defaults;
   - the defaults: every item takes its default;
   - the defaults, with the overrides the user names.
2. **Roles.** When the items name more than one answerer and the request names none, one multi-select question asks which roles the user answers for. Only their items are asked; the others stay open for their own answerers.
3. **Order.** Items with no default come first. Then the business outcomes, run behaviours, readings, material and configuration values, each group in step order.
4. **Batches** of at most four structured questions, one per item:
   - the options come from the item's `Builds now:`, `Recommended:`, `Default:`, `Reading:` and `Instead:` lines, the recommended one first and marked, the default named;
   - every batch also offers "use the defaults for the rest of this group".
5. **Stop** when the user says so, takes the defaults for what is left, or no item of the user's roles remains.
6. **Write, then apply.** Each answer goes under its item, as its `Change:` or `Answer:`. Defaults taken for a whole heading go on its `Confirmed:` line, as "the user, <YYYY-MM-DD>, in an interview". Then apply them as "Apply the answers" does.
7. **What remains.** The closing summary lists the items still open by role. With them it names the document to send to each: the SDD, or the readiness file for the build's own questions.

## Review after every edit

After every edit, review what changed, and every component genome a process genome links that the edit touched, against [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) before answering. An extracted genome also takes the Source Map checks [extract-guide.md](../extract/extract-guide.md) Step 6b runs against its source. Fix what breaks a rule.

Then write the SDD again ([sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md) item 5; for a genome with a `Designed in:` line, its Action Required section, item 6). Then run the strict check on the edited genome ([SKILL.md](../../SKILL.md) § Check) — `node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict`, adding `--processes` and `--recordsets` when a partial re-extraction wrote the inventory files. The check also checks the SDD's fingerprint. Fix every `FAIL` and run it again, at most three rounds; a fix to the genome writes the SDD's fingerprint again. When answering, name every `FAIL` left, and how many questions the SDD's Action Required still holds and how many are needed before the build.

## Back to the Build

An edit `uipath-genome` requested, or a request that also asks to build or to prepare the build, ends by invoking `uipath-genome` with `build "<GENOME_MD>"`, or `prepare "<GENOME_MD>"` for a request to prepare, and the user's request quoted verbatim, after § Review after every edit. A finding or answer the edit could not apply is named in that hand-off; the build reports it instead of handing it back again. `uipath-genome` not installed → end at the summary and say the build needs it. Any other edit ends at its summary.
