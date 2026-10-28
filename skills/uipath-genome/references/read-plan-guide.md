# Read Plan — what Execute reads, and when

Read whole at the start of every Execute run, before any other guide of this skill. Rule file: every guide this skill reads is named here, with the phase and the condition that open it.

> **Read by the read plan (§ Read Plans below), never from memory.** `SKILL.md` routes; guides carry the rules, each subject in exactly one guide. A file the plan reads whole is read whole — not grepped or skimmed; a pointer that names a section (`guide.md § Section`) is a section read, that section in full; a guide no condition of the plan has reached stays closed, and the skill's `CLAUDE.md`, which governs editing the skill, is not read in a run. A framework selectors guide's per-technology tables are a **catalog**, read by section: list its headings, then read the sections for the technologies the source recorded; the rules around them are read whole.

## Read Plans

Every turn resends the whole context: a reference read early is paid again on every later turn, and one a later answer rules out is paid for nothing. Execute reads, at each phase, only what this table names for the conditions that hold:

| Phase | Condition | Read |
|---|---|---|
| start, before any question | — | [execution-guide.md](execution-guide.md); [genome-reading-guide.md](genome-reading-guide.md) by section — § Levels and Files, § Design Links and § Sections, and § Transactional Shape when it is not the stub; each skill named in Build With / Components, invoked once for preflight discovery and the scaffolding options — its SKILL.md only, its mandatory reads wait for the build; [transactional-execution-guide.md](transactional-execution-guide.md) when the Transactional Shape is not the stub, before the split questions |
| start, before any question | a refactor: the Source Map names a UiPath source, or the request asks for a refactor | [refactor-guide.md](refactor-guide.md) whole and genome-reading-guide.md § Build Skills; the SKILL.md of every product § Choosing the target there offers a component, invoked once for its capability check — its mandatory reads wait for the build |
| build, once the configuration answers exist | — | the owning skill's mandatory reads, through its own journey |
| build | the genome has a Source Map | genome-reading-guide.md § Source Map |
| build | an export was resolved | the migration reads of § Source Frameworks |
| build | a group builds UI activities, extracted genome or not | [ui-verification-guide.md](ui-verification-guide.md) |
| build | the genome has test components, extracted or not | [test-execution-guide.md](test-execution-guide.md) |
| build | a group is planned in parts, runs through subagents or forks, or resumes after a pause or a compaction | [execution-parts-guide.md](execution-parts-guide.md) whole |
| build | no application is reachable | [offline-definition-workarounds-guide.md](offline-definition-workarounds-guide.md) |
| build | a group uses a doc or a tool [package-doc-errata-guide.md](package-doc-errata-guide.md) corrects | that doc's row, read with the doc, and the § Tools rows for the tools a group builds with |
| build | a Build With row names a retired skill or one the host lacks | genome-reading-guide.md § Build Skills |
| build | an execution guide points into a section | that section of genome-reading-guide.md |
| build | a UiPath source's UI targets, test data or deployed state are read | genome-reading-guide.md § UiPath Source |
| end | the target environment needs setup | [open-items-guide.md](open-items-guide.md) |

Each phase's reads go out in at most three turns, never file by file as each file names the next:

1. **Turn 1**, one message: every file the phase reads whole, and the heading list (a search for `^#` lines) of every file it reads by section.
2. **Turn 2**, one message: the sections chosen from those lists, and the owning skill's discovery for the activity kinds in play.
3. **Turn 3**, only what turn 2 routed to.

A plan never narrows an owning skill's contract: a read that skill mandates is performed even when no plan names it, a read that misses (a wrong path) is retried the next turn, and neither is dropped to stay within three turns.

## Source Frameworks

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read at execution with [genome-reading-guide.md](genome-reading-guide.md) § UiPath Source, with [source-migration-guide.md](source-migration-guide.md) § Migration preflight step 4, [ui-target-migration-guide.md](ui-target-migration-guide.md) § UI targets and [ui-verification-guide.md](ui-verification-guide.md): its UI targets are carried over, not translated. Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run:

1. **Ask for its location.** Ask "Where is the framework migration guide?" unless the request, or the execution scaffolding answer ([execution-guide.md § 1.3](execution-guide.md)), already gave it. Accept a folder path (`<PACK_DIR>`); a git URL is cloned into a scratch folder first. Never search the disk for it, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks: the framework the Source Map names. An extracted genome names its framework in the Source Map; that name selects the row and makes the execution a **migration**.
3. **Run, then read.** Read [source-migration-guide.md](source-migration-guide.md) whole and derive the catalogs with the row's script (its § Migration preflight). A build with UI activities also reads [ui-target-migration-guide.md](ui-target-migration-guide.md), the source guide's § Composite actions and `<PACK_DIR>/<framework>/selectors-guide.md` by technology section together with [selector-translation-guide.md](selector-translation-guide.md) and its guide for each technology the target catalog holds — [web](selector-translation-web-guide.md), [SAP GUI](selector-translation-sap-guide.md), [desktop](selector-translation-desktop-guide.md); a build with test components reads [test-execution-guide.md](test-execution-guide.md).

No row matches → say which framework the Source Map names and that the pack has no guide for it. Pack not available → Execute continues without the migration part — live capture or placeholders, stated in the report ([source-migration-guide.md § Migration preflight](source-migration-guide.md) step 1).

## The Genome and the Checker

`uipath-planner` writes every genome with its format guides, which this skill does not hold: what a build needs from a genome is restated in [genome-reading-guide.md](genome-reading-guide.md), read by section. The one file both skills hold is `scripts/check-genome.py`, byte-identical, canonical in `uipath-planner`; execution runs it before anything is asked ([execution-guide.md § 1.1](execution-guide.md)). CI fails when the copies differ.
