# Extracted Genome Guide

What a genome extracted from an existing automation carries beyond the sections every genome has ([genome-format-guide.md](genome-format-guide.md)): the Source Map, the source values it is written from, and the source's defects.

## Source Map

Where every part of the genome came from: a table of contract rows — one row per component in a process genome — and, in each component genome, the step table below. Names files and source objects, never activity names or variables. Also records dead code found, unresolved invocations, and steps whose intent was inferred, plus `Related resources` and `Resource discrepancies` rows when the user gave resources ([extraction-guide.md](extraction-guide.md) Step 3). Authored genomes have no Source Map. Remove the section on request when the genome is redistributed as a reusable blueprint.

**The step table.** Every extracted component genome carries, under a `### Steps` heading in its Source Map, one table pairing each Workflow step with what it was built from:

| Step | Source objects | Data sets | Captures | Notes |
|---|---|---|---|---|
| 3 | `Submit_Order` (482113, lines 29–40) | `Order_Rows` (1207) | 2 | The confirmation is sent by `Send_Confirmation` (529077), a step of its own; called by the run's root `Order_Main` (310045) |

1. **One row per Workflow step**, keyed by its number exactly as the Workflow numbers it — never `Step 3`, a name or a range. A test component's steps are its test cases. A step built from the same objects as another repeats them.
2. **Source objects** lists only the objects whose behaviour the step implements, separated by `; `, the step's primary object first: the one whose name a rebuild that keeps the source's names gives the step's file or workflow. A framework source writes each as `` `Name` (id) `` or `` `Name` (id, {locator}) ``: names repeat across folders in most frameworks, so the id is what identifies the copy, and the locator is the position inside the object that the source guide's § Provenance names (lines, a page, nodes, test steps), backticked names allowed. A UiPath source writes the workflow's project-relative path, `` `Folder/Workflow.xaml` ``, a test case with its `testCaseId` in the parentheses ([uipath-source-guide.md § Provenance](uipath-source-guide.md)). A caller, and a callee that is a step of its own, go to Notes; a window or a control never appears here — it is the target catalog's.
3. **Data sets** lists the data sets the step's own objects read, written like a source object, or `none`: a test case's own data set, and one it borrows from another case or a shared set (login rows, interface data). A library step's cell is `none` unless the library reads a data set itself: what its callers pass is their data, on their own steps. The column gives the kind, so a root and its data set that share a name, or a data set whose id equals a process id, are never mistaken for one another.
4. **Captures** is the number of screen captures the source takes inside the step, `0` when it takes none; execution checks the rebuild's evidence against it.
5. **Notes** is free text — callers, callees, lines, findings, quirks — and the only cell no check reads.

**Unused parts** — enabled objects no entry point reaches ([extraction-guide.md](extraction-guide.md) Step 2b) — are written as the Unused parts answer says. Extracted, each is written like any other part: an uncalled library workflow is a public workflow of its library, an uncalled entry point or test case a step of its component, and a workflow nothing invokes a step of its component, after the steps the entry points reach, whose first sentence says that no step invokes it today; its step-table row's Notes say `no caller in the export`. Left out, the live surface goes to the `Not covered` row and the rest to an `Unused` row, each by name and id with what it does in a few words, so a partial re-extraction can add it later ([editing-guide.md § Partial Re-extraction](editing-guide.md)).

**For a genome extracted from another framework the Source Map is also the migration contract.** Execution regenerates every catalog it needs — UI target locators, data rows, process inventory — from the export, and the Source Map is the only place that says where the export is and which source objects each step came from. It must therefore carry, in the process genome (or the single component genome):

| Row | Content |
|---|---|
| Source framework | the framework name exactly as [SKILL.md § Source Frameworks](../SKILL.md) spells it, and the framework version the export states |
| Source export | the export's root path as extraction read it, plus its identity (database or tenant, export date, process count) so a moved copy can be recognised |
| Steps | the step table above, in every component genome |
| Checkpoints | for every workflow step of a test component, and of a library a test component calls, the source's checkpoints inside it: source step id, what is asserted, the expected value (or the data column it comes from; for a library step, the Interface argument), and whether the source captured a screenshot there; a library step with no checkpoint has no row. Execution builds one assertion and one evidence artifact per checkpoint and produces the result parity table from them ([test-execution-guide.md § Result parity](test-execution-guide.md)). One row, or one per step as `Checkpoints, step N` |
| Not covered | live behaviour the extracted projects or folders hold that no step is built from — an entry point, public workflow or test case nothing in the genome reaches, or one the request or the Unused parts answer left out — by name and id, each with what it does in a few words; [extraction-guide.md](extraction-guide.md) Step 7 offers to translate them. Unused parts that are no live surface belong to the `Unused` row; dead code, superseded copies and objects reached only through disabled calls to the dead-code row |
| Inventory counts | what the export holds and the genome covers, as counts: processes, windows, controls (and how many have no locator), recordsets, rows, credential accounts, and the objects left out, which their own rows name (`Not covered`, `Unused`, excluded, dead code) |
| Other rows as needed | excluded objects, dead code, unresolved references, steps whose intent was inferred, data files that are outputs rather than inputs, source-only constructs with no counterpart, findings — any label |

**The genome files are the only output of extraction.** Recognition data (locators), data rows and process inventories never enter the genome body and are not written beside it either: they are the export's, a copy next to the genome goes stale and says nothing the export does not, and execution re-derives them from the export with the source guide's script into the build's working folder ([source-migration-guide.md § Migration preflight](source-migration-guide.md)). What the Source Map must record is everything execution needs to find them again — the rows above. A Source Map that names the export but not the per-step objects has lost the migration: execution cannot find the locators and rows the export carried and ships placeholders and invented data. A genome shared without its Source Map can be built but not migrated: the reader gets placeholders or a live capture, and the redistribution note says so.

## Source values

A genome is extracted through a rendering of the source — a framework's inventory output — and inherits every gap in it: a rendering can hide a typed value (a number, a flag stored as text, an option nested under another), and an extraction can paraphrase one. An empty value in a rendering is "not shown", never "not set". Every fact of these kinds that a step's wording or rules depend on is read from the source object and written as the source states it:

1. **Comparison literals, operators and case rules** — contains / equals / starts with, case-sensitive or not, line breaks ignored or not, whitespace normalised or not, a pattern that must match the whole text or one that searches it — spelled exactly, spacing and punctuation included: "contains `Wollen Sie wirklich`, case-insensitive", "reads exactly `Order placed!`, spacing aside", "matches `software|automation` anywhere, ignoring case".
2. **Counts, attempts and loop bounds**, and whether the loop tests before or after its body.
3. **Lengths, positions and occurrences** in text operations (a cut to 20 characters, the second `|`-field).
4. **Waits, pauses and timeouts** in the unit the source states, and a check's budget: its own timeout, or, for a check or an action with no timeout of its own, the framework's default budget the source guide names (a source check that waits its framework's default is not an activity waiting the activity's default).
5. **Set or typed:** whether a field is set (replaced) or typed into (appended, key by key).
6. **Flags that change control flow** (continue on error, a do-while, a skip switch, a failure the source tolerates or logs as a pass, a call made from a failure route). A step's own result handling is behaviour: a check whose failure the source logs as a pass or ignores is a decision or an optional wait, not a hard check, and a check that passes when its target is absent asserts absence.
7. **Formats** a date or number is typed or compared in (a mask, a pattern, one part of a date per segment): the format is part of the value.
8. **Values bound to a built-in** (the run date, the user's folder), computed at run time — never the stored default a same-named project variable carries.
9. **A parameter's unit, its default, and which of two filled parameters overrides the other**, read from the source's own documentation of that parameter (a framework export often carries it) before they are called unknown.
10. **Log texts** of each step, with their literal wording and variable substitutions.

Extraction writes them so ([extraction-guide.md](extraction-guide.md) Step 3); execution checks every one the genome cites before a group builds on it ([source-migration-guide.md § Migration preflight](source-migration-guide.md) step 4).

## Source Defects

An extracted genome carries a source's defect only once [defect-verification-guide.md](defect-verification-guide.md) has confirmed it in the full rendering and in the framework's source itself. It is written where the behaviour lives — the step, rule or handler — in this form:

`**Source defect:** {what the source does, stated as fact} … Evident intent: {what it was meant to do} {*[Inferred]* when only the step's purpose shows it}`

- The defect itself is a fact read in the source and never carries `*[Inferred]*`.
- The evident intent carries the marker only when the step's purpose is all that shows it. An intent the source states (a comment or log text at the defect, a sibling copy that does it — a disabled or unreached copy the author superseded included) is quoted and unmarked, and so is one a user ruling confirms. A step's or workflow's name shows only its purpose. Any consequence that depends on data, configuration, platform or package behaviour the export does not hold carries the marker.
- The genome says which behaviour the rebuild follows. It follows the evident intent when the source states that intent. When only the step's purpose shows it, the choice is the user's: the rebuild carries the source's behaviour unless the user rules otherwise, because a migration keeps the source's rules and an intent nobody wrote down is a guess. A ruling is written at the step after the source fact it departs from, as `User ruling ({date}): …`, and the index row's Rebuild follows cell cites it.
- A defect whose result only the source runtime's internals reproduce cannot be carried: an order left by a comparison that contradicts itself is whatever that runtime's sort makes of it, and a run the source platform refuses to start (a required setting left empty) has no behaviour to rebuild. The rebuild follows the evident intent.
- What an evident intent leaves open is put to the user as a ruling, its options listed at the step: where the rows a self-contradicting comparison cannot place go, a signal the step needs that the source never produced (an answer saying the input could not be read), a criterion the author's note names but never states (which records count as new). Until the user rules, the genome names the option the rebuild builds and marks it `*[Inferred]*`.
- A process genome indexes every component's defects under Error Handling and Recovery in one table, `Defect | Component step | Rebuild follows`: one row each, the defect named in a few words, stated in full only at its step.
- A defect's own Source Map row names the objects and lines that prove it.
- A behaviour the source's comments or design show as intended is a rule, not a defect.
- An AI step's instructions are source like any other step's: a rule that uses data the step is never given, or rules that contradict each other, is a source defect. Following its intent gives the step the data its instructions name, or rewords the rule, and the step's Business Rules state the instructions the rebuild uses.
- A behaviour that turns on semantics nobody documents is **unresolved**: state both readings and mark the chosen one `*[Inferred]*`.
- The word "suspected" never appears in a written genome: a finding is verified or not written as a defect.
