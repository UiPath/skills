# Editing Guide — change a genome in place

Content rules for what an edit writes: [genome-format-guide.md](genome-format-guide.md), and for an extracted genome [extracted-genome-guide.md](extracted-genome-guide.md). Only `edit` changes a genome; `uipath-genome-builder` reads it and never edits it, so a fix found during a build comes back here and the build re-runs. Edits are targeted and in place, never a regeneration ([genome-format-guide.md § Write, Then Offer Edits](genome-format-guide.md)).


## Read Plan

The writing rules of [genome-format-guide.md § Writing Rules](genome-format-guide.md) apply to every edit.

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide and [genome-format-guide.md](genome-format-guide.md) whole; [extracted-genome-guide.md](extracted-genome-guide.md) when `context` reports `extracted`; [transactional-shape-guide.md](transactional-shape-guide.md) when the edit touches the Transactional Shape, or a step, rule or handler of a genome whose `transactional` is true |
| partial re-extraction | — | [extract-guide.md](extract-guide.md), [defect-verification-guide.md](defect-verification-guide.md) and the source guide, as for `extract`; [parts-guide.md](parts-guide.md) and [extraction-parts-guide.md](extraction-parts-guide.md) when the list runs in parts |

Each phase's reads go out in at most three turns: turn 1 every file read whole and the heading list of every file read by section; turn 2 the sections chosen; turn 3 only what turn 2 routed to.

## Edits

### Any genome

| Request | Update |
|---|---|
| "Add detail to step X" | Workflow step X; add acceptance criteria if detail is testable |
| "Change complexity" / "complexity should be higher or lower" | Complexity section, then section depth per population matrix |
| "Add/remove an application" | Target Applications, Workflow, Build With, Acceptance Criteria |
| "Use a different skill for step X" | Build With row and rationale, validated against mapping guide |
| "Split this into components" | Promote to process genome: create process file, move component content into component files, add Handoffs |
| "Merge these two components" / "split this one" | Adjust Components, Handoffs, component files; re-check Interface agreement |
| "Scenario X signs in as persona Y" | Platform Dependencies (credential asset for Y), test component's row schema (asset name per row), Configuration Questions |
| "Remove the inferred flags" | Delete every `*[Inferred]*` — user confirmed the content |
| "The Map says X" / "the process owner confirmed rule Y" / a changeset on the change proposal | A genome with a `Map binding:` line: regenerate the parts the Map and the SDD hold from the record, through the Cartographer MCP, keyed by step number and record id; the genome's own content is kept. A person's edit to a Map-held part is not made here — it goes back as a comment or a changeset on the change proposal ([genome-format-guide.md § Design Links](genome-format-guide.md)) |
| "Make it transactional" / "drop the transactional shape" | Transactional Shape (unit of work, As-is, outcomes, split options, evidence) or its stub; Platform Dependencies (the store the As-is names); Configuration Questions (retry counts) |
| "Step X should be a business exception" | Transactional Shape outcomes table; the rule under Business Rules for step X; an acceptance criterion for the recorded reason |
| "One row per transaction instead of one file" (change the unit of work) | Transactional Shape (Unit of work, Alternative units of work, As-is, outcomes, split options); Interface; Handoffs data passed; Platform Dependencies (store); Acceptance Criteria (duplicate and retry cases) |
| "Split the dispatcher into its own component" / "use one queue" / "apply the REFramework" / "drop the ledger" | Not a genome edit: the split, the store, the template and the fate of the source's coordination stores are execution's configuration answers, chosen from the Split options by `uipath-genome-builder`'s split questions (`uipath-genome-builder`'s transactional-execution-guide.md § Split questions). Edit the Transactional Shape only when what it describes changes: in an authored genome the described process itself — a new source, a new item kind, items that must now be shared — and then the As-is, the Evidence and the options; in an extracted genome its As-is or Evidence, when wrong or incomplete |

### Extracted genomes

| Request | Update |
|---|---|
| "This step is wrong / missing" | Workflow, then Build With, Acceptance Criteria, Source Map |
| "Rename / reorder / remove steps" | Workflow and Source Map together, so every step still names its source objects |
| "Drop the Source Map" | Remove section from every file — genome is being shared as a blueprint; say target and data migration will no longer be possible from it |
| "Here is the PDD too" | [extract-guide.md](extract-guide.md) Step 3, **Related resources** |
| "Is this really a defect?" / "check it against the source" | Rerun both passes of [defect-verification-guide.md](defect-verification-guide.md) for that finding, and re-mark it in the body and its Source Map row by what the passes show |
| "Fix this defect in the rebuild" / "keep the source's behaviour" | A ruling: written at the step after the source fact, cited in the defect index's Rebuild follows cell, and carried into the step's Workflow lines, criteria and Source Map row ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md)) |
| "Also translate what is not covered", or an unused part | § Partial Re-extraction with the objects of the Source Map's `Not covered` or `Unused` row the user names |
| "The source changed" / "finish the unread parts" | § Partial Re-extraction with the changed or unread objects. Rerun extraction from its Step 1 ([extract-guide.md](extract-guide.md)) only when the components themselves changed (projects or root processes added, removed or regrouped); preserve user edits the source does not contradict and say which were kept |

## Check after every edit

After every edit, run the check again before answering:

```bash
python3 "<SKILL_DIR>/scripts/check-genome.py" <process|component> "<GENOME_MD>" --profile strict
```

Use `python` on Windows. A process genome takes the checker to every component genome it links. An extracted genome takes the checks [extract-guide.md](extract-guide.md) Step 6b runs against its source. Fix every `FAIL` line and run it again, at most three rounds, then name what is left.

## Partial Re-extraction

Rewrites only the steps whose source objects changed or were never read: finishing a run cut short, translating what the Source Map leaves not covered, and bringing a genome back in line with a source that changed after extraction.

1. **The object list.** For a run cut short: the objects of the `Not read (run cut short)` rows. For what is not covered: the objects of the `Not covered` row the user names. For a changed source: the objects that differ from the source identity the Source Map records — `git diff --name-status <COMMIT>..HEAD` for a source in a repository; `diff -rq "<OLD_EXPORT>" "<NEW_EXPORT>"` over the object files for a new export, leaving out the source guide's Exclusions. When the old export is gone, compare the new inventory with the Source Map's step tables: an object no row names is new, a row whose object is missing is gone, and every other object is re-read, since nothing shows what changed.
2. **Map objects to steps** through the Source Map's step tables. A new object is placed by the call graph ([extract-guide.md](extract-guide.md) Step 4), and its caller's step changes too. An object nothing in the genome calls becomes new steps, numbered after the last one, in the component the user names — the library that holds the shared workflows, or a component of its own. A row whose object is gone loses its step.
3. **Read** the listed objects whole with the source guide, plus each caller's bindings to them, and verify every finding they raise or that rests on them ([defect-verification-guide.md](defect-verification-guide.md)).
4. **Rewrite only the mapped steps** — with their substeps, Business Rules, Error Handling entries, Acceptance Criteria and Source Map rows — add the new steps, and remove the gone ones with their criteria. Every other line stays as written, user edits included. A renumbering updates every reference to the moved steps, Handoffs and pointers included. A new finding takes an id no row of its component's Source Map uses.
5. **Close.** Update the Source Map's source identity (commit, or export identity and inventory counts), remove the `Not read` rows and the `Not covered` entries the pass completed, then run [extraction-parts-guide.md § Reconciliation](extraction-parts-guide.md), the extraction guide's Step 6b check and its Step 7.

A list above one part's budget runs in parts ([extraction-parts-guide.md](extraction-parts-guide.md)), the parts taking the listed objects.
