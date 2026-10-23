---
name: uipath-genome
description: "UiPath automation genome builder (`*-genome.md`): always invoke to build, execute or implement a genome file, before any skill it names. EXECUTE a component or process genome — the coding-agent spec uipath-planner writes — through the owning skills: configuration questions, build, a verdict per acceptance criterion, open items and cutover. A genome extracted from a UiPath project or another framework's export builds as a refactor or migration: UI targets and test data migrated, characterization tests, run modes, comparison. Triggers: 'build/execute/implement this genome', 'build from the blueprint', 'run the migration from this genome', 'execute the refactor'. Write, extract, document or edit a genome, or design from an idea/SOP/PDD/SDD→uipath-planner. Build without a genome→that artifact's skill. Legacy activity upgrade→uipath-activity-migrator. Quality review→uipath-review."
when_to_use: "User points at a *-genome.md file (or one whose first line is `<!-- UIPATH-AUTOMATION-GENOME`) and asks to build, execute, implement or follow it. uipath-planner hands over a genome it authored or extracted for a build, a migration or a refactor."
---

# UiPath Genome — build automations from their genome

Genome: markdown specification an AI agent consumes to build or rebuild an automation — what it does, business rules, data moving between parts, platform resources, its transactional shape, verification, and which UiPath skill builds each part. **`uipath-planner` writes every genome** (Author, Extract, Edit); this skill **builds** from it (Execute), verifies it and hands it off. Genomes stay thin: build skills carry UiPath know-how; a genome describes *what*, skills know *how*.

> **Read by the read plan (§ Read Plans), never from memory.** This file routes; guides carry the rules, each subject in exactly one guide. A file the plan reads whole is read whole — not grepped or skimmed; a pointer that names a section (`guide.md § Section`) is a section read, that section in full; a guide no condition of the plan has reached stays closed, and the `CLAUDE.md` beside this file, which governs editing the skill, is not read in a run. A framework selectors guide's per-technology tables are a **catalog**, read by section: list its headings, then read the sections for the technologies the source recorded; the rules around them are read whole.

## When to Use This Skill

- `*-genome.md` file to build from — authored from an idea, a PDD, a TO-BE or an SDD, or extracted from an existing automation
- A genome extracted from a UiPath source to execute as a refactor, or from another framework's export as a migration
- A genome `uipath-planner` hands over once it is written

## Mode Detection

1. **`*-genome.md` path plus build intent** ("build", "execute", "implement", "follow") → **Execute**. Read [execution-guide.md](references/execution-guide.md). Executing a genome extracted from a UiPath source is a refactor, and so is executing one from another framework when the request asks for a refactor ([refactor-guide.md](references/refactor-guide.md)).
2. **Everything that writes or changes a genome is `uipath-planner`'s**: authoring one from an idea, a description, an SOP, a PDD, a TO-BE or an SDD; proposing scenarios for a goal; extracting one from a UiPath project or solution or another framework's export (documentation, estate assessment, the first step of a refactor or migration); editing one, partial re-extraction included. Hand the request to `uipath-planner`; once it has written the genome, Execute here. When `uipath-planner` is not installed, say that writing the genome needs it and stop.
3. **A request to refactor or migrate an automation with no genome yet** → `uipath-planner` extracts first (row 2), then Execute here. An upgrade of a Windows-Legacy project's activities in place stays `uipath-activity-migrator`'s.

A request to design a solution and derive tasks, or any input this list assigns to another skill, is that skill's job. Say so and stop.

## Read Plans

Every turn resends the whole context: a reference read early is paid again on every later turn, and one a later answer rules out is paid for nothing. Execute reads, at each phase, only what this table names for the conditions that hold:

| Phase | Condition | Read |
|---|---|---|
| start, before any question | — | [execution-guide.md](references/execution-guide.md); [genome-reading-guide.md](references/genome-reading-guide.md) by section — § Levels and Files, § Design Links and § Sections, and § Transactional Shape when it is not the stub; each skill named in Build With / Components, invoked once for preflight discovery and the scaffolding options — its SKILL.md only, its mandatory reads wait for the build; [transactional-execution-guide.md](references/transactional-execution-guide.md) when the Transactional Shape is not the stub, before the split questions |
| start, before any question | a refactor: the Source Map names a UiPath source, or the request asks for a refactor | [refactor-guide.md](references/refactor-guide.md) whole and genome-reading-guide.md § Build Skills; the SKILL.md of every product § Choosing the target there offers a component, invoked once for its capability check — its mandatory reads wait for the build |
| build, once the configuration answers exist | — | the owning skill's mandatory reads, through its own journey |
| build | the genome has a Source Map | genome-reading-guide.md § Source Map |
| build | an export was resolved | the migration reads of § Source Frameworks |
| build | a group builds UI activities, extracted genome or not | [ui-verification-guide.md](references/ui-verification-guide.md) |
| build | the genome has test components, extracted or not | [test-execution-guide.md](references/test-execution-guide.md) |
| build | a group is planned in parts, runs through subagents or forks, or resumes after a pause or a compaction | [execution-parts-guide.md](references/execution-parts-guide.md) whole |
| build | no application is reachable | [offline-definition-workarounds-guide.md](references/offline-definition-workarounds-guide.md) |
| build | a group uses a doc or a tool [package-doc-errata-guide.md](references/package-doc-errata-guide.md) corrects | that doc's row, read with the doc, and the § Tools rows for the tools a group builds with |
| build | a Build With row names a retired skill or one the host lacks | genome-reading-guide.md § Build Skills |
| build | an execution guide points into a section | that section of genome-reading-guide.md |
| build | a UiPath source's UI targets, test data or deployed state are read | genome-reading-guide.md § UiPath Source |
| end | the target environment needs setup | [open-items-guide.md](references/open-items-guide.md) |

Each phase's reads go out in at most three turns, never file by file as each file names the next:

1. **Turn 1**, one message: every file the phase reads whole, and the heading list (a search for `^#` lines) of every file it reads by section.
2. **Turn 2**, one message: the sections chosen from those lists, and the owning skill's discovery for the activity kinds in play.
3. **Turn 3**, only what turn 2 routed to.

A plan never narrows an owning skill's contract: a read that skill mandates is performed even when no plan names it, a read that misses (a wrong path) is retried the next turn, and neither is dropped to stay within three turns.

## Source Frameworks

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read at execution with [genome-reading-guide.md](references/genome-reading-guide.md) § UiPath Source, with [source-migration-guide.md](references/source-migration-guide.md) § Migration preflight step 4, [ui-target-migration-guide.md](references/ui-target-migration-guide.md) § UI targets and [ui-verification-guide.md](references/ui-verification-guide.md): its UI targets are carried over, not translated. Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run:

1. **Ask for its location.** Ask "Where is the framework migration guide?" unless the request, or the execution scaffolding answer ([execution-guide.md § 1.3](references/execution-guide.md)), already gave it. Accept a folder path (`<PACK_DIR>`); a git URL is cloned into a scratch folder first. Never search the disk for it, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks: the framework the Source Map names. An extracted genome names its framework in the Source Map; that name selects the row and makes the execution a **migration**.
3. **Run, then read.** Read [source-migration-guide.md](references/source-migration-guide.md) whole and derive the catalogs with the row's script (its § Migration preflight). A build with UI activities also reads [ui-target-migration-guide.md](references/ui-target-migration-guide.md), the source guide's § Composite actions and `<PACK_DIR>/<framework>/selectors-guide.md` by technology section together with [selector-translation-guide.md](references/selector-translation-guide.md) and its guide for each technology the target catalog holds — [web](references/selector-translation-web-guide.md), [SAP GUI](references/selector-translation-sap-guide.md), [desktop](references/selector-translation-desktop-guide.md); a build with test components reads [test-execution-guide.md](references/test-execution-guide.md).

No row matches → say which framework the Source Map names and that the pack has no guide for it. Pack not available → Execute continues without the migration part — live capture or placeholders, stated in the report ([source-migration-guide.md § Migration preflight](references/source-migration-guide.md) step 1).

## The Genome and the Checker

`uipath-planner` writes every genome with its format guides, which this skill does not hold: what a build needs from a genome is restated in [genome-reading-guide.md](references/genome-reading-guide.md), read by section. The one file both skills hold is `scripts/check-genome.py`, byte-identical, canonical in `uipath-planner`; execution runs it before anything is asked ([execution-guide.md § 1.1](references/execution-guide.md)). CI fails when the copies differ ([CLAUDE.md](CLAUDE.md)).

## Critical Rules

Each rule names its subject and the one guide that states it in full; the guide's wording is the rule.

1. **Execution never edits the genome and never skips the configuration questions** — waived only by an explicit "take the defaults" in the current request — then advances group by group without pausing, assesses every acceptance criterion, and writes the open-items files when the target environment needs setup — [execution-guide.md](references/execution-guide.md) § 1.3, § 2.2, § 3; [open-items-guide.md](references/open-items-guide.md). A spec fix is a `uipath-planner` edit, followed by re-execution.
2. **What the genome's SDD already decided is answered, not asked**: the split and queue design, the implementation mode, the package pins, the refactor answers — [execution-guide.md § 1.1](references/execution-guide.md).
3. **A genome missing a required section, or failing the checker, is malformed**: report it and send it back to `uipath-planner` — [execution-guide.md § 1.1](references/execution-guide.md); `scripts/check-genome.py`.
4. **Execution on an extracted genome is a migration by default**: catalogs derived from the export at preflight, UI targets and test data migrated from them, no secret ever copied — [source-migration-guide.md](references/source-migration-guide.md).
5. **Build through the owning skill, verifiably**: its mandatory reads, and for every activity kind the default XAML and the package's per-activity doc before the first file using it is written; workflows authored as files, never generated — [execution-guide.md § 2.2](references/execution-guide.md).
6. **Composite source actions are contracts in the genome and patterns at build** — [genome-reading-guide.md](references/genome-reading-guide.md) § Sections, Workflow; [ui-target-migration-guide.md § Composite interactions](references/ui-target-migration-guide.md).
7. **UiPath selector truth lives in one guide** — [selector-translation-guide.md](references/selector-translation-guide.md) rules 1–16, with what its technology guides add to them. **Verification is a property of the acting activity**, except a test project's checkpoints — [ui-verification-guide.md](references/ui-verification-guide.md).
8. **A migrated target carries a verdict — `verified`, `shape-verified` or `offline-unverified` —** and a reachable application is a windfall, never a precondition for finishing the run — [ui-target-migration-guide.md § Verifying targets](references/ui-target-migration-guide.md).
9. **Most source steps are not UI activities**, and linking is the last thing done to a workflow file — [source-migration-guide.md § Source steps that are not UI actions](references/source-migration-guide.md); [ui-target-migration-guide.md § UI targets](references/ui-target-migration-guide.md).
10. **The transactional shape is described in the genome and split at build**: execution asks the split questions per flow, unless the SDD recorded the split, and the behaviour is owed whatever the choice — [genome-reading-guide.md](references/genome-reading-guide.md) § Transactional Shape; [transactional-execution-guide.md](references/transactional-execution-guide.md).
11. **Source values are read from the source, not from its rendering**, and execution follows the source where it and the genome disagree — [genome-reading-guide.md](references/genome-reading-guide.md) § Source Map, source values.
12. **Executing a genome extracted from a UiPath source is a refactor**, and so is a migration whose request asks for one: every component re-authored on the target its shape fits, the genome the contract, every changed output a plan row with its reason, characterization tests before the logic — [refactor-guide.md](references/refactor-guide.md). **A UiPath source's deployed state is source**: the binding a process overrides is the value that runs — [genome-reading-guide.md](references/genome-reading-guide.md) § UiPath Source.
13. **Nothing reaches a tenant unasked**: the build stops at the pack dry run, never writes to a tenant the user did not name, and a build that replaces a running automation ends its open items with the cutover — [open-items-guide.md](references/open-items-guide.md); [refactor-guide.md § Done](references/refactor-guide.md).

## Anti-patterns

1. **Writing, extracting or editing a genome here.** That is `uipath-planner`'s Author, Extract and Edit lanes (§ Mode Detection); an in-place activity upgrade of a Legacy project is `uipath-activity-migrator`'s.
2. **Editing the genome to make a build pass.** The genome is read-only at execution; the gap goes into the report and back to `uipath-planner` (Critical Rule 1).
