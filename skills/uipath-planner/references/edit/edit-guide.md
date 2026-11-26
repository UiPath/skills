# Editing Guide — change a genome in place

Content rules for what an edit writes: [genome-format-guide.md](../shared/genome-format-guide.md), and for an extracted genome [extracted-genome-guide.md](../shared/extracted-genome-guide.md). Only `edit` changes a genome; `uipath-genome` reads it and never edits it, so a deviation the build reports comes back here and the build re-runs. A request from `uipath-genome` quotes the user's yes to its offer and is applied without offering the edits again; one without it offers them first. Every edit ends with the strict check (§ Review after every edit). Edits are targeted and in place, never a regeneration ([genome-format-guide.md § Write, Then Offer Edits](../shared/genome-format-guide.md)).

## Read Plan

The writing rules of [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) apply to every edit.

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole; [genome-format-guide.md](../shared/genome-format-guide.md) every section before § Design Links, plus § Design Links when the genome has a `Designed in:` or `Preferences:` line; [genome-questions-guide.md](../shared/genome-questions-guide.md) whole; [process-genome-sections-guide.md](../shared/process-genome-sections-guide.md) for a process genome (the level in the genome's first-line marker); [extracted-genome-guide.md](../shared/extracted-genome-guide.md) when the genome has a Source Map with a step table; [transactional-shape-guide.md](../shared/transactional-shape-guide.md) when the edit touches the Transactional Shape, or a step, rule or handler of a genome whose Transactional Shape is not the stub; [open-questions-guide.md](../shared/open-questions-guide.md) whole; [sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md) whole when an SDD is beside the genome or the request asks for one |
| a related resource is given | the genome is extracted and the user hands over a PDD, SOP, runbook or other resource beside the source | [extract-guide.md](../extract/extract-guide.md) Step 1 (the related-resources question) and Step 3's **Related resources** paragraph |
| "The SDD was revised: update the genome" | — | [genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md) whole, plus the rows of its own Read Plan |
| "Findings from `uipath-genome`" | a finding names a Build With skill (a retired name) | [skill-mapping-guide.md](../shared/skill-mapping-guide.md) |
| partial re-extraction | — | [extract-guide.md](../extract/extract-guide.md), [defect-verification-guide.md](../shared/defect-verification-guide.md) and the source guide, as for `extract`; [extraction-parts-guide.md](../shared/extraction-parts-guide.md) when the list runs in parts |
| a refactor review | the genome is extracted and the user asks for its refactoring opportunities | [refactor-hotspots-guide.md](../shared/refactor-hotspots-guide.md) whole; [extract-guide.md](../extract/extract-guide.md) § Step 6b and § Step 6c; [skill-mapping-guide.md](../shared/skill-mapping-guide.md) whole; [product-selection-guide.md](../shared/product-selection-guide.md) § Constraint Gate when a decision changes a target; [transactional-shape-guide.md](../shared/transactional-shape-guide.md) when a decision touches a flow; [extraction-parts-guide.md](../shared/extraction-parts-guide.md) when the edit spans more components than one context holds |
| bringing the genome to the build | the genome is extracted and a refactor or migration build has written its hand-off folder | the reads of a partial re-extraction (row above), with [uipath-source-guide.md](../extract/uipath-source-guide.md) as the source guide; [extraction-parts-guide.md](../shared/extraction-parts-guide.md) § Reconciliation |

Each phase's reads go out in at most three turns: turn 1 every file read whole and the heading list of every file read by section; turn 2 the sections chosen; turn 3 only what turn 2 routed to.

## Edits

### Any genome

On a genome with a `Designed in:` line, a change to what the SDD holds — products, projects, components and their skills, and the decisions the SDD records (the split and queue design, the implementation mode, the package pins, the refactor answers) — goes to `design` to revise the linked SDD, and the same run then applies "The SDD was revised" to update the genome ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current). Every other row (complexity, inferred flags, wording, step detail, a finding from `uipath-genome`) applies as written.

| Request | Update |
|---|---|
| "The SDD was revised: update the genome" (after a `design` revise, or from the user) | Read the SDD the `Designed in:` line links whole and redo [genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md) items 3–6 against it: every section whose SDD content changed is rewritten, nothing else is. Then take the fingerprint again with `node "<SKILL_DIR>/scripts/sdd-fingerprint.mjs" "<SDD_PATH>"` (never `sha256sum`: the fingerprint leaves out the `Genome` row and covers every child SDD a solution lists), rewrite the `Designed in:` line ([genome-format-guide.md § Design Links](../shared/genome-format-guide.md)), and run `node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict` until it prints `OK` — the edit is not done before. A run that follows a `design` revise, or an unattended request, applies the edit without offering it; the closing summary names the sections changed |
| "Findings from `uipath-genome`" (from the build's completion report, or the user forwarding it) | Apply each finding where it points: a genome deviation → the step the source contradicts, written as the build followed it unless the user rules otherwise; a retired skill name → the Build With row, from [skill-mapping-guide.md](../shared/skill-mapping-guide.md); a `Not covered` object to build → [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) |
| "Write the SDD" (a genome with no SDD beside it, or one whose SDD the user wants written again) | The SDD from the genome ([sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md)); nothing in the genome changes |
| "Apply the answers" (the user filled in the SDD's Action Required or the readiness file, answered in a reply or an interview ([interview-guide.md](../interview/interview-guide.md)), or `uipath-genome` sent them back) | [§ Applying the Answers](#applying-the-answers) |
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
| "Split the dispatcher into its own component" / "use one queue" / "apply the REFramework" / "drop the ledger" | A decision for the build, not a rewrite of what the genome describes: the user's request made here is recorded as the flow's `Decided:` line, which a split answered for a build never is ([transactional-shape-guide.md](../shared/transactional-shape-guide.md) rule 8). Edit the Transactional Shape itself only when what it describes changes — a new source, a new item kind, items that must now be shared. A split that drops a store of the flow's Coordination row rewrites the genome as that guide's rule 3 states |

### Extracted genomes

| Request | Update |
|---|---|
| "This step is wrong / missing" | Workflow, then Build With, Acceptance Criteria, Source Map |
| "Rename / reorder / remove steps" | Workflow and Source Map together, so every step still names its source objects |
| "Retire / fold / rebuild `<component>` on `<product>`" (a refactor or migration target) | The refactor answer, as [extract-guide.md](../extract/extract-guide.md) Step 6c records it: the component's Build With / Components row and the `Requested change` row; a split it decides → the flow's `Decided:` line |
| "Check the refactoring opportunities" / "analyze the process and suggest refactors" / "what could be better here" | The refactor review of [refactor-hotspots-guide.md](../shared/refactor-hotspots-guide.md): the spots found discussed with the user in the session, and the design agreed applied as its § The review item 5 writes it; an input or output changed only on the user's word ([extract-guide.md](../extract/extract-guide.md) Step 6c). An edit spanning more components than one context holds runs in parts as [extraction-parts-guide.md § Running in Parts](../shared/extraction-parts-guide.md) states, each part editing the components it owns from one brief that holds the answers and the contracts between components |
| "Bring the genome to the build" (the user, once a refactor or migration rebuild is the one that will run, with the build's hand-off folder) | [§ Bringing the Genome to the Build](#bringing-the-genome-to-the-build) |
| "Drop the Source Map" | Remove section from every file — genome is being shared as a blueprint; say target and data migration will no longer be possible from it |
| "Here is the PDD too" (any related resource) | A related resource of [extract-guide.md](../extract/extract-guide.md) Step 1: read it and write what it settles as Step 3's **Related resources** paragraph states |
| "Is this really a defect?" / "check it against the source" | Rerun both passes of [defect-verification-guide.md](../shared/defect-verification-guide.md) for that finding, and re-mark it in the body and its Source Map row by what the passes show |
| "Fix this defect in the rebuild" / "keep the source's behaviour" | A ruling: written at the step after the source fact, cited in the defect index's Rebuild follows cell, and carried into the step's Workflow lines, criteria and Source Map row; an evident intent the ruling confirms loses its marker, as does a marked consequence the rebuild no longer rests on, which is then stated in words as unknown, and the defect's entry reads decided ([extracted-genome-guide.md § Source Defects](../shared/extracted-genome-guide.md)) |
| "Also translate what is not covered", or an unused part | [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) with the objects of the Source Map's `Not covered` or `Unused` row the user names |
| "The source changed" / "finish the unread parts" | [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) with the changed or unread objects. Rerun extraction from its Step 1 ([extract-guide.md](../extract/extract-guide.md)) only when the components themselves changed (projects or root processes added, removed or regrouped); preserve user edits the source does not contradict and say which were kept |

## Applying the Answers

"Apply the answers" takes each item answered whose answer alters the genome, matched by its id:
- the SDD's Business decisions, Material to supply and Preferences;
- the readiness file's Genome edits: each gap ruled on, and each line of its Edits for `uipath-planner`;
- the items the readiness file lists under Decisions still open, its configuration values excepted;
- on a genome with no SDD beside it, its open entries answered in a reply or an interview, matched by the genome's ids.

The readiness file's Architecture decisions and Build setup are the build's: none changes the genome.

A reply's id is checked against what its item asks. Two answers to one id go to the user with both, and so does a readiness answer whose `Context:` line no longer matches the genome section it rests on, since an edit changed that section after `prepare` wrote it. A readiness item of the build's that rests on a section this edit changes is named in the summary, for `prepare` to draw again.

Each is applied as the row of § Edits it is:
- a ruling, a defect named under Defects the rebuild fixes, and a recommended option chosen that the genome does not build yet, as "Fix this defect in the rebuild" / "keep the source's behaviour";
- a reading the answer keeps loses its marker; a changed one, or a discrepancy the owner rules for the resource, as "This step is wrong / missing";
- an export given, or an object to translate, as a partial re-extraction;
- a resource as "Here is the PDD too";
- a preferences file as the `Preferences:` line, the genome then brought in line with it ([genome-format-guide.md § Design Links](../shared/genome-format-guide.md));
- a gap ruled on in the sections its `See:` line names, as the row of what the option chosen changes;
- a line of Edits for `uipath-planner` as the row of what it finds wrong, once the genome and the source confirm it, otherwise marked `Not applied:` with what they show.

On a genome with a `Designed in:` line, an item taken from the SDD's own design goes to `design` first (§ Any genome). An answer that leaves the genome as it stands (an object left out, the source kept, a business outcome kept as built) changes no step. Every entry an answer settles reads decided ([genome-questions-guide.md § Open Decisions](../shared/genome-questions-guide.md)). The readiness file's applied items are marked `Applied <YYYY-MM-DD>: <what it wrote>` (`the recommended option` when that was chosen); configuration values stay as answered, for the build, and with no file to hold one the build asks it.

## Bringing the Genome to the Build

Once the rebuild is the one that will run, the genome is rewritten to describe it, read as a UiPath source ([uipath-source-guide.md](../extract/uipath-source-guide.md)):

1. **Read** the hand-off folder's README (its Decisions and Differences from the genome), and its refactor plan and correspondence tables where the build wrote them, then each built workflow they name and each one a `Requested change` decision touches.
2. **Re-point the Source Map** to the built solution, every row written as extraction writes it for a UiPath source: `Source framework`, `Source export` (its commit, in a repository), each step-table row naming the built workflow its step became — through the correspondence table where the build renamed, absorbed or merged it, and by reading the built projects where it wrote none — and the deployed-state, runtime, checkpoint, inventory, `Not covered` and `Unused` rows read again from it. A `Rebuilt from` row keeps the previous source's framework, export and `Requested change`; the `Requested change` row and the as-is process map then go.
3. **Rewrite what the build changed:** each difference, deviation and refactor decision the hand-off names, and each decision of the `Requested change` row, written where it acts as the built workflow does it, read there, never taken from the hand-off alone; a source defect the rebuild fixed is written as the built behaviour and leaves the defect index. A change the built workflow does not show is not written, and the summary names it.
4. **Remove what was not rebuilt:** a retired component, and a folded one whose steps now sit in the component it was folded into, leave the genome as "Merge these two components" updates it, each open entry they named withdrawn; a process genome left with one buildable project becomes a component genome ([genome-format-guide.md § Two Levels](../shared/genome-format-guide.md)).
5. **Close** as [extract-guide.md § Partial Re-extraction](../extract/extract-guide.md) item 5 closes, over the rewritten steps.

## Review after every edit

After every edit, review what changed, and every component genome a process genome links that the edit touched, against [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) before answering. An extracted genome also takes the Source Map checks [extract-guide.md](../extract/extract-guide.md) Step 6b runs against its source. Fix what breaks a rule.

Then write the SDD beside the genome again, when there is one ([sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md) item 5; for a genome with a `Designed in:` line, its Action Required section, item 6). Then run the strict check on the edited genome ([SKILL.md](../../SKILL.md) § Check) — `node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict`, adding `--processes` and `--recordsets` when a partial re-extraction wrote the inventory files. The check also checks an SDD's fingerprint. Fix every `FAIL` and run it again, at most three rounds; a fix to the genome writes again the SDD sections it changes, then the fingerprint. When answering, name every `FAIL` left, and how many questions are still open — the SDD's Action Required, or the genome's open entries when it has no SDD — and how many are needed before the build.

## Back to the Build

Bringing the genome to the build ends at its summary, since that build is done. Any other edit `uipath-genome` requested, or a request that also asks to build or to prepare the build, ends by invoking `uipath-genome` with `build "<GENOME_MD>"`, or `prepare "<GENOME_MD>"` for a request to prepare, and the user's request quoted verbatim, after § Review after every edit. A finding or answer the edit could not apply is named in that hand-off; the build reports it instead of handing it back again. The edit `prepare` asks for at its end ends at its summary, since that `prepare` has finished. `uipath-genome` not installed → end at the summary and say the build needs it. Any other edit ends at its summary.
