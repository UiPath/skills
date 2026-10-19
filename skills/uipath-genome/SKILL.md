---
name: uipath-genome
description: "UiPath automation genome (`*-genome.md`): always invoke to build, execute or edit a genome file, before any skill it names. Portable markdown blueprint of an automation at process and component level: steps, business rules, handoffs, platform resources, acceptance criteria, and the UiPath skill that builds each part. EXTRACT a genome from a UiPath project or solution (`.xaml`/`.cs`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.case`/`.json`, `.uipx`) or another automation or test framework's export, for documentation, a refactor or migration to UiPath; AUTHOR one from an idea; EXECUTE one to build it. Triggers: 'genome', 'blueprint', 'document this automation/solution/process', 'reverse-engineer this project', 'build/implement this genome'. PDD/SDD, SOP or idea to design without a genome→uipath-planner. Build without a genome→that artifact's skill. Legacy activity upgrade→uipath-activity-migrator. Quality review→uipath-review. Finding what to automate→uipath-automation-discovery."
when_to_use: "User points at a *-genome.md file (or one whose first line is `<!-- UIPATH-AUTOMATION-GENOME`) and asks to build, execute, implement, follow or edit it. User says 'genome', 'blueprint', 'document what this automation does', 'extract a spec from this project/solution', 'reverse-engineer this process', 'describe this solution at high and low level', 'propose a workshop or demo scenario to build'. User asks to refactor a UiPath automation ('refactor this process', 'rebuild it on Maestro or Portable')."
---

# UiPath Genome — document, author, and execute automation blueprints

Genome: markdown specification an AI agent consumes to rebuild an automation — what it does, business rules, data moving between parts, platform resources, its transactional shape, verification, and which UiPath skill builds each part. Genomes stay thin: build skills carry UiPath know-how; a genome describes *what*, skills know *how*.

> **Read by the mode's read plan (§ Read Plans), never from memory.** This file routes; guides carry the rules, each subject in exactly one guide. A file the plan reads whole is read whole — not grepped or skimmed; a pointer that names a section (`guide.md § Section`) is a section read, that section in full; a guide no condition of the plan has reached stays closed, and the `CLAUDE.md` beside this file, which governs editing the skill, is not read in a run. A framework selectors guide's per-technology tables are a **catalog**, read by section: list its headings, then read the sections for the technologies the source recorded; the rules around them are read whole.

## When to Use This Skill

- Existing UiPath project or solution to document, understand, or prepare for migration ("what does this solution do", "extract a genome", "document this process at high and low level")
- Existing UiPath automation to refactor: rebuilt on another UiPath product, framework or architecture, its behaviour kept; or another framework's automation migrated with a refactor, when asked
- Described automation idea needing a specification before building, or a goal (a self-paced workshop, a demo, trying a product) needing a scenario proposed first
- `*-genome.md` file to build from
- Existing genome to update, split into components, or re-extract after source changed

## Mode Detection

Determine mode from input, in this order:

1. **`*-genome.md` path plus build intent** ("build", "execute", "implement", "follow") → **Execute**. Read [execution-guide.md](references/execution-guide.md).
2. **A UiPath project or solution, or another framework's export, plus refactor intent** ("refactor", "re-platform", "rebuild it on Maestro, API workflows or Portable", "move it off the Windows robot", "migrate and modernize it") → **Extract** its genome first; once it is written and the user's edits are in (an unattended run goes straight on), **Execute** that genome: executing a genome extracted from a UiPath source is a refactor, and so is executing one from another framework when the request asks for a refactor ([refactor-guide.md](references/refactor-guide.md)). An upgrade of a Windows-Legacy project's activities in place stays `uipath-activity-migrator`'s.
3. **Directory, project file, solution manifest, or another framework's export** (`project.json`, `project.uiproj`, `.uipx`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.case`, `caseplan.json`, `uipath.json`; or a folder with none of these holding another automation or test framework's export) → **Extract**. Read [extraction-guide.md](references/extraction-guide.md) and the framework's guides (§ Source Frameworks). A `.bpmn` here is an existing process project to document; a BPMN model handed over as the design to build from is `uipath-planner`'s. A Windows-Legacy UiPath project whose activities are to be upgraded in place is `uipath-activity-migrator`'s; documenting it, or blueprinting it for a rebuild, is an extraction.
4. **Description, idea, SOP, transcript or other process document with no source project, when the user asks for a genome or blueprint; or a goal to propose a scenario for** (a self-paced workshop, a demo, trying a product) → **Author**. Read [authoring-guide.md](references/authoring-guide.md). The same input without a genome or blueprint asked for — designing or building from an SOP, a transcript, a process spec or an idea — is `uipath-planner`'s.
5. **`*-genome.md` path plus edit intent** ("update", "add a step", "split", "remove the inferred flags") → **Edit**. Read [editing-guide.md](references/editing-guide.md): its edit table, and — when the source changed or the extraction was cut short — its § Partial Re-extraction, which re-extracts only the changed or unread objects.

A PDD or SDD with no genome or blueprint asked for, a request to design a solution and derive tasks, or any input this list assigns to another skill is that skill's job, not a genome. Say so and stop.

## Read Plans

Every turn resends the whole context: a reference read early is paid again on every later turn, and one a later answer rules out is paid for nothing. Each mode reads, at each phase, only what this table names for the conditions that hold:

| Mode | Phase | Condition | Read |
|---|---|---|---|
| Author | start | — | [authoring-guide.md](references/authoring-guide.md), [genome-format-guide.md](references/genome-format-guide.md) and [skill-mapping-guide.md](references/skill-mapping-guide.md) whole; the template of the level chosen; one example to calibrate depth — for a process genome [invoice-processing-genome.md](assets/examples/invoice-processing-genome.md), for a component [classify-document-and-create-validation-genome.md](assets/examples/classify-document-and-create-validation-genome.md), or [purchase-requisition-entry-genome.md](assets/examples/purchase-requisition-entry-genome.md) when the description iterates over items |
| Author | the unit of work is assessed | the description iterates over items | [transactional-shape-guide.md](references/transactional-shape-guide.md) |
| Extract | start | — | [extraction-guide.md](references/extraction-guide.md), genome-format-guide.md, [extracted-genome-guide.md](references/extracted-genome-guide.md) and skill-mapping-guide.md whole; the template of the level chosen; the extracted example [salesforce-accounts-and-contacts-genome.md](assets/examples/salesforce-accounts-and-contacts-genome.md) by its § Source Map only, to calibrate the step table; the source guide as § Source Frameworks states |
| Extract | from the inventory on | the inventory or a signal shows per-item work: queue items fetched or added, a loop over rows, files or mails with a per-item catch, a work list read, a framework state machine | transactional-shape-guide.md, in the turn after the first such signal |
| Extract | the sizing plan is stated | the extraction runs in parts | [parts-guide.md](references/parts-guide.md) and [extraction-parts-guide.md](references/extraction-parts-guide.md) |
| Extract | the first suspected source defect | — | [defect-verification-guide.md](references/defect-verification-guide.md) |
| Edit | start | — | [editing-guide.md](references/editing-guide.md) and genome-format-guide.md whole; extracted-genome-guide.md when the genome has a Source Map; transactional-shape-guide.md when the edit touches the Transactional Shape, or a step, rule or handler of a genome whose shape is not the stub |
| Edit | partial re-extraction | — | extraction-guide.md, defect-verification-guide.md and the source guide, as for Extract; parts-guide.md and extraction-parts-guide.md when the list runs in parts |
| Execute | start, before any question | — | [execution-guide.md](references/execution-guide.md); each skill named in Build With / Components, invoked once for preflight discovery and the scaffolding options — its SKILL.md only, its mandatory reads wait for the build; [transactional-execution-guide.md](references/transactional-execution-guide.md) and transactional-shape-guide.md when the Transactional Shape is not the stub, before the split questions |
| Execute | start, before any question | a refactor: the Source Map names a UiPath source, or the request asks for a refactor | [refactor-guide.md](references/refactor-guide.md) and skill-mapping-guide.md whole; the SKILL.md of every product § Choosing the target there offers a component, invoked once for its capability check — its mandatory reads wait for the build |
| Execute | build, once the configuration answers exist | — | the owning skill's mandatory reads, through its own journey |
| Execute | build | the genome has a Source Map | extracted-genome-guide.md |
| Execute | build | an export was resolved | the migration reads of § Source Frameworks |
| Execute | build | a group builds UI activities, extracted genome or not | [ui-verification-guide.md](references/ui-verification-guide.md) |
| Execute | build | the genome has test components, extracted or not | [test-execution-guide.md](references/test-execution-guide.md) |
| Execute | build | a group is planned in parts, runs through subagents or forks, or resumes after a pause or a compaction | parts-guide.md and [execution-parts-guide.md](references/execution-parts-guide.md) |
| Execute | build | no application is reachable | [offline-definition-workarounds-guide.md](references/offline-definition-workarounds-guide.md) |
| Execute | build | a group uses a doc or a tool [package-doc-errata-guide.md](references/package-doc-errata-guide.md) corrects | that doc's row, read with the doc, and the § Tools rows for the tools a group builds with |
| Execute | build | a Build With row names a retired skill or one the host lacks | skill-mapping-guide.md |
| Execute | build | an execution guide points into a section | that section of genome-format-guide.md, transactional-shape-guide.md or extracted-genome-guide.md |
| Execute | end | the target environment needs setup | [open-items-guide.md](references/open-items-guide.md) |

Each phase's reads go out in at most three turns, never file by file as each file names the next:

1. **Turn 1**, one message: every file the phase reads whole, and the heading list (a search for `^#` lines) of every file it reads by section.
2. **Turn 2**, one message: the sections chosen from those lists, and the owning skill's discovery for the activity kinds in play.
3. **Turn 3**, only what turn 2 routed to.

A plan never narrows an owning skill's contract: a read that skill mandates is performed even when no plan names it, a read that misses (a wrong path) is retried the next turn, and neither is dropped to stay within three turns.

## Source Frameworks

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read with [uipath-source-guide.md](references/uipath-source-guide.md) — whole at extraction; at execution only its § UI Target Locators and § Test Data, with [source-migration-guide.md](references/source-migration-guide.md) § Migration preflight step 4, [ui-target-migration-guide.md](references/ui-target-migration-guide.md) § UI targets and [ui-verification-guide.md](references/ui-verification-guide.md): its UI targets are carried over, not translated. Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run, in both modes:

1. **Ask for its location.** Ask "Where is the framework migration guide?" unless the request, or the execution scaffolding answer ([execution-guide.md § 1.3](references/execution-guide.md)), already gave it. Accept a folder path (`<PACK_DIR>`); a git URL is cloned into a scratch folder first. Never search the disk for it, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks: the row whose detection signals match the given files (Extract), or the framework the Source Map names (Execute). An extracted genome names its framework in the Source Map; that name selects the row and makes the execution a **migration**.
3. **Run, then read.** Run the row's script before reading any export file. Extract reads `<PACK_DIR>/<framework>/source-guide.md` in full and writes the genome and its Source Map. Execute reads [source-migration-guide.md](references/source-migration-guide.md) whole and derives the catalogs with the same script (its § Migration preflight). A build with UI activities also reads [ui-target-migration-guide.md](references/ui-target-migration-guide.md), the source guide's § Composite actions and `<PACK_DIR>/<framework>/selectors-guide.md` by technology section together with [selector-translation-guide.md](references/selector-translation-guide.md) and its guide for each technology the target catalog holds — [web](references/selector-translation-web-guide.md), [SAP GUI](references/selector-translation-sap-guide.md), [desktop](references/selector-translation-desktop-guide.md); a build with test components reads [test-execution-guide.md](references/test-execution-guide.md).

No row matches → say which framework the files appear to come from and that the pack has no guide for it; never improvise an extraction. Pack not available → Extract stops (no genome is extracted from a framework nobody has read); Execute continues without the migration part — live capture or placeholders, stated in the report ([source-migration-guide.md § Migration preflight](references/source-migration-guide.md) step 1).

## Critical Rules

Each rule names its subject and the one guide that states it in full; the guide's wording is the rule.

1. **Choose the genome level before writing**: one buildable project is a component genome, two or more a process genome with one component genome per project — [genome-format-guide.md § Two Levels](references/genome-format-guide.md).
2. **Read the source, do not ask about it**; ask only for the resources beside it, then read and link them — [extraction-guide.md](references/extraction-guide.md) Steps 1 and 3.
3. **Infer complexity, never ask for it** — [genome-format-guide.md § Complexity](references/genome-format-guide.md).
4. **Replication-grade detail in behavioural wording**, with no activity names, variable names, file paths or code syntax in the body — [genome-format-guide.md § Workflow](references/genome-format-guide.md) and § Provenance.
5. **Configuration Questions carry only the values left open** — [genome-format-guide.md § Configuration Questions](references/genome-format-guide.md).
6. **Every section present, always**, with a stub line where one does not apply — [genome-format-guide.md § Stub Lines](references/genome-format-guide.md).
7. **One skill per Build With row, from the mapping guide only**; operate-only skills belong under Platform Dependencies — [skill-mapping-guide.md](references/skill-mapping-guide.md).
8. **The preamble and the blueprint blockquote name `uipath-genome` as the skill that builds the genome**, and Build With (or Components) precedes Workflow (or Process Map) — [genome-format-guide.md § Two Levels](references/genome-format-guide.md) rule 5.
9. **Acceptance criteria are specific and testable** — [genome-format-guide.md § Acceptance Criteria](references/genome-format-guide.md).
10. **Flag ambiguity, never leave gaps**: the best interpretation plus `*[Inferred]*` — [genome-format-guide.md § Ambiguity Marker](references/genome-format-guide.md).
11. **Write immediately, offer edits after**; edits are in place, never a regeneration — [genome-format-guide.md § Write, Then Offer Edits](references/genome-format-guide.md); [editing-guide.md](references/editing-guide.md).
12. **Execution never edits the genome and never skips the configuration questions** — waived only by an explicit "take the defaults" in the current request — then advances group by group without pausing, assesses every acceptance criterion, and writes the open-items files when the target environment needs setup — [execution-guide.md](references/execution-guide.md) § 1.3, § 2.2, § 3; [open-items-guide.md](references/open-items-guide.md).
13. **Extraction writes genomes only, and the Source Map is the migration contract** — [extracted-genome-guide.md § Source Map](references/extracted-genome-guide.md).
14. **Execution on an extracted genome is a migration by default**: catalogs derived from the export at preflight, UI targets and test data migrated from them, no secret ever copied — [source-migration-guide.md](references/source-migration-guide.md).
15. **Build through the owning skill, verifiably**: its mandatory reads, and for every activity kind the default XAML and the package's per-activity doc before the first file using it is written; workflows authored as files, never generated — [execution-guide.md § 2.2](references/execution-guide.md).
16. **Composite source actions are contracts in the genome and patterns at build** — [genome-format-guide.md § Workflow](references/genome-format-guide.md); [ui-target-migration-guide.md § Composite interactions](references/ui-target-migration-guide.md).
17. **UiPath selector truth lives in one guide** — [selector-translation-guide.md](references/selector-translation-guide.md) rules 1–16, with what its technology guides add to them. **Verification is a property of the acting activity**, except a test project's checkpoints — [ui-verification-guide.md](references/ui-verification-guide.md).
18. **A migrated target carries a verdict — `verified`, `shape-verified` or `offline-unverified` —** and a reachable application is a windfall, never a precondition for finishing the run — [ui-target-migration-guide.md § Verifying targets](references/ui-target-migration-guide.md).
19. **Most source steps are not UI activities**, and linking is the last thing done to a workflow file — [source-migration-guide.md § Source steps that are not UI actions](references/source-migration-guide.md); [ui-target-migration-guide.md § UI targets](references/ui-target-migration-guide.md).
20. **The transactional shape is described in the genome and split at build**: the genome asserts no split, store, template or unit, execution asks the split questions per flow, and the behaviour is owed whatever the choice — [transactional-shape-guide.md](references/transactional-shape-guide.md); [transactional-execution-guide.md](references/transactional-execution-guide.md).
21. **Source values are read from the source, not from its rendering**: an empty rendering is "not shown", never "not set", and execution follows the source where it and the genome disagree — [extracted-genome-guide.md § Source values](references/extracted-genome-guide.md).
22. **A suspected source defect is verified in the full rendering and then in the framework's source before it is written**, and written by its classification — [defect-verification-guide.md](references/defect-verification-guide.md); marker: [extracted-genome-guide.md § Source Defects](references/extracted-genome-guide.md).
23. **Executing a genome extracted from a UiPath source is a refactor**, and so is a migration whose request asks for one: every component re-authored on the target its shape fits, the genome the contract, every changed output a plan row with its reason, characterization tests before the logic — [refactor-guide.md](references/refactor-guide.md). **A UiPath source's deployed state is source**: the binding a process overrides is the value that runs — [uipath-source-guide.md § Deployed State](references/uipath-source-guide.md).

## Anti-patterns

1. **Producing a genome when the user brought a PDD/SDD, SOP, transcript or idea without asking for a genome or blueprint, or asked for a solution design.** That is `uipath-planner`; an in-place activity upgrade of a Legacy project is `uipath-activity-migrator` (§ Mode Detection).
