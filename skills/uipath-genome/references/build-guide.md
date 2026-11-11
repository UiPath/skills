# Build Guide — the `build` verb

`build` turns a genome into the automation it specifies: it asks the configuration questions, builds every component through its owning skill, wires them, gives each acceptance criterion a verdict and ends with the hand-off folder. Building a genome extracted from a UiPath source is a **refactor**; one extracted from another framework's export is a **migration**. The procedure is [execution-guide.md](execution-guide.md); this guide holds the verb's rules and its read plan.

## Start

The genome facts of [SKILL.md § Setup](../SKILL.md) decide the rows of § Read Plan below. An extracted genome whose Source Map names no framework opens neither the migration row nor the refactor row until the user's answer names it.

**A file without the genome marker** is not a genome: say `uipath-planner` writes genomes, and stop.

**A Build With or Components skill the host lacks** (found when the start row of § Read Plan invokes each named skill): name the skill and the components that need it, say the build needs it installed, and stop.

**A component genome the Components table links is missing on disk:** ask the user for its path — the one question about the source the build asks. When the user supplies none, report the missing path as an edit for `uipath-planner`, and stop.

## Verb Rules

These add to the Critical Rules in [SKILL.md](../SKILL.md). Each rule names its subject and the one guide that states it in full; the guide's wording is the rule.

1. **The build never skips the configuration questions** — waived only by the build request ([configuration-questions-guide.md](configuration-questions-guide.md) rule 3, autonomous runs) — then advances group by group without pausing, assesses every acceptance criterion, and ends with the hand-off folder: the completion report as its README, and the open-items files when the target environment needs setup — [execution-guide.md](execution-guide.md) § 2.2, § 3; [configuration-questions-guide.md](configuration-questions-guide.md); [completion-report-guide.md](completion-report-guide.md); [open-items-guide.md](open-items-guide.md). A spec fix: [SKILL.md](../SKILL.md) Critical Rule 2.
2. **What the genome records as decided is answered, not asked**: a designed genome's split and queue design (`Decided:` lines), implementation mode, package pins and refactor answers — [execution-guide.md § 1.1](execution-guide.md).
3. **A build on an extracted genome is a migration by default**: catalogs derived from the export at preflight, UI targets and test data migrated from them, no secret ever copied — [source-migration-guide.md](source-migration-guide.md).
4. **Build through the owning skill, verifiably**, never by writing a project outside its journey: its mandatory reads, and for every activity kind the default XAML and the package's per-activity doc before the first file using it is written; workflows authored as files, never generated — [execution-guide.md § 2.2](execution-guide.md).
5. **Composite source actions are contracts in the genome and patterns at build** — [genome-reading-guide.md § Workflow](genome-reading-guide.md); [composite-interactions-guide.md](composite-interactions-guide.md).
6. **UiPath selector truth lives in one guide** — [selector-translation-guide.md](selector-translation-guide.md) rules 1–16, with what its technology guides add to them. **Verification is a property of the acting activity**, except a test project's checkpoints — [ui-verification-guide.md](ui-verification-guide.md).
7. **A migration's UI targets go through exploration, the offline migration and the live healing pass, in that order**; a migrated target carries a verdict — `verified`, `shape-verified` or `offline-unverified` — and the live checks it still owes, and a reachable application is a windfall, never a precondition for finishing the run — [ui-target-migration-guide.md](ui-target-migration-guide.md) rule 4 and § Verifying targets; [live-application-guide.md](live-application-guide.md).
8. **Most source steps are not UI activities**, and linking is the last thing done to a workflow file — [source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md); [ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md).
9. **The transactional shape is split at build**: the genome decides no split except on a flow's `Decided:` line, the build asks the split questions for every other flow, and the behaviour is owed whatever the choice — [transactional-execution-guide.md](transactional-execution-guide.md), its § Shape Rules stating what the genome's section says.
10. **Source values are read from the source, not from its rendering**: an empty rendering is "not shown", never "not set", and the build follows the source where it and the genome disagree — [genome-reading-guide.md § Source values](genome-reading-guide.md).
11. **Building a genome extracted from a UiPath source is a refactor**, and so is a migration whose request asks for one: every component re-authored on the target the genome names, the genome the contract, every changed output a plan row with its reason, characterization tests before the logic — [refactor-guide.md](refactor-guide.md). **A UiPath source's deployed state is source**: the binding a process overrides is the value that runs — [refactor-guide.md § Deployed State](refactor-guide.md).
12. **Nothing reaches a tenant that no answer allowed**: the build stops at the last local gate, and the only tenant write is the one an answer allows — the default an autonomous run takes counts as the answer; publishing, deploying, queues, assets and triggers stay open items; a build that replaces a running automation ends its open items with the cutover — [open-items-guide.md](open-items-guide.md); [refactor-guide.md § Done](refactor-guide.md).

## Read Plan

**How a read is done.** A file the plan reads whole is read whole — never grepped or skimmed. A pointer that names a section (`guide.md § Section`) is a section read: that section in full, opened by its heading without listing the file's headings first. A guide no condition of the plan has reached stays closed. A framework selectors guide's per-technology tables are a **catalog**, read by section: list its headings, then read the sections for the technologies the source recorded; the rules around them are read whole.

Every turn resends the whole context: a reference read early is paid again on every later turn, and one a later answer rules out is paid for nothing. `build` reads, at each phase, only what this table names for the conditions that hold; the genome facts of [SKILL.md § Setup](../SKILL.md) answer the conditions about the genome.

| Phase | Condition | Read |
|---|---|---|
| start, before any question | — | [execution-guide.md](execution-guide.md); [configuration-questions-guide.md](configuration-questions-guide.md); [genome-reading-guide.md § Design Links](genome-reading-guide.md) when the genome is designed (another section of it is read when an execution guide points into it, row below); each skill named in Build With / Components, invoked once for preflight discovery and the scaffolding options — its SKILL.md only, its mandatory reads wait for the build; [transactional-execution-guide.md](transactional-execution-guide.md) when the genome is transactional, before the split questions |
| start, before any question | the build is a migration (the Source Map names a framework other than UiPath) | [source-frameworks-guide.md](source-frameworks-guide.md) whole — it resolves the framework migration pack and names the migration reads |
| start, before any question | the build is a refactor, or the request asks for a refactor | [refactor-guide.md](refactor-guide.md) whole |
| build, once the configuration answers exist | — | the owning skill's mandatory reads, through its own journey; [completion-report-guide.md](completion-report-guide.md), before the answers go into the hand-off's README |
| build | the genome is extracted | [genome-reading-guide.md](genome-reading-guide.md) § Source Map, § Source values and § Source Defects; [source-frameworks-guide.md](source-frameworks-guide.md) |
| build | an export was resolved | the build reads of [source-frameworks-guide.md](source-frameworks-guide.md) for the Source Map's framework — § UiPath sources ([source-migration-guide.md § UI Target Locators](source-migration-guide.md) and § Test Data, [source-migration-guide.md § Migration preflight](source-migration-guide.md) step 4, [ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md), [ui-verification-guide.md](ui-verification-guide.md)) or § Other frameworks — the framework migration pack |
| build | a group builds UI activities, extracted genome or not | [ui-verification-guide.md](ui-verification-guide.md) |
| build | the genome has test components, extracted or not | [test-execution-guide.md](test-execution-guide.md) |
| build | a group is planned in parts, runs through subagents, or resumes after a pause or a compaction | [execution-parts-guide.md](execution-parts-guide.md) |
| build | the Live application answer names a reachable application | [live-application-guide.md](live-application-guide.md), before the target spec is written, or before the first UI group of an authored genome |
| build | a group uses a doc or a tool [package-doc-errata-guide.md](package-doc-errata-guide.md) corrects | that doc's row, read with the doc, and the § Tools rows for the tools a group builds with |
| build | a Build With row names a retired skill | [genome-reading-guide.md § Build With and Components](genome-reading-guide.md) |
| build | an execution guide points into a section | that section of [genome-reading-guide.md](genome-reading-guide.md) |
| end | the target environment needs setup | [open-items-guide.md](open-items-guide.md) |

Each phase's reads go out in at most three turns, never file by file as each file names the next:

1. **Turn 1**, one message: every file the phase reads whole, the sections the plan names by heading, and the heading list (a search for `^#` lines) of every catalog or file it reads by sections the plan does not name.
2. **Turn 2**, one message: the sections chosen from those lists, and the owning skill's discovery for the activity kinds in play.
3. **Turn 3**, only what turn 2 routed to.

A plan never narrows an owning skill's contract: a read that skill mandates is performed even when no plan names it, a read that misses (a wrong path) is retried the next turn, and neither is dropped to stay within three turns.
