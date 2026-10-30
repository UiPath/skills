# Build Guide — the `build` verb

`build` turns a genome into the automation it specifies: it asks the configuration questions, builds every component through its owning skill, wires them, gives each acceptance criterion a verdict and ends with the hand-off folder. Building a genome extracted from a UiPath source is a **refactor**; one extracted from another framework's export is a **migration**. The genome is read-only throughout. The procedure is [execution-guide.md](execution-guide.md); this guide holds the verb's rules and its read plan.

## Start

The `context` call of [SKILL.md § Setup](../SKILL.md) has run; its fields decide the rows of § Read Plan below. `extracted` is true when the genome has a `## Source Map` that is not the stub; `transactional` is true when its Transactional Shape is not the stub, false for the stub, and null when the section is absent — null opens no transactional read and is a report item like the other findings below. `build_mode` `unknown` opens neither the migration row nor the refactor row until the Source Map's `Source framework` row, or the user's answer, names the framework ([SKILL.md § Setup](../SKILL.md)).

**A component genome the Components table links is missing on disk:** ask the user for its path — the one question about the source the build asks. When the user supplies none, report the missing path as an edit for `uipath-planner`, and stop.

When `check.ok` is false, each `FAIL` line is sorted into one of two classes:

1. **Blocking — the genome is malformed:** the genome carries no `<!-- UIPATH-AUTOMATION-GENOME: component|process` marker; a section the build requires is missing (the required sections per level: [execution-guide.md § 1.1](execution-guide.md)); the Source Map has no `### Steps` table, or its rows do not pair one-to-one with the Workflow steps; in an extracted genome, Workflow steps not in the numbered form, because the Source Map's rows pair with the steps by number. Report each such `FAIL` as an edit for `uipath-planner`, and stop. A missing component genome follows the paragraph above.
2. **Report items — the build continues:** every other `FAIL` — every other missing section, wording (a code-level token in the body, a heading or blockquote not written as the template has it), numbering (acceptance criteria not in the numbered form; Workflow steps in a genome that is not extracted), counts, and the format of a Transactional Shape, Configuration Question or step-table cell. Each goes into the completion report as an edit for `uipath-planner`; the build never fixes it in the genome.

## Verb Rules

These add to the Critical Rules in [SKILL.md](../SKILL.md). Each rule names its subject and the one guide that states it in full; the guide's wording is the rule.

1. **The build never edits the genome and never skips the configuration questions** — waived only by an explicit "take the defaults" request: the user's current request, or `Execution autonomy: autonomous` in the Planner Handoff of the `Designed in:` SDD or in the build task prompt `uipath-planner`'s `plan` hands over ([execution-guide.md § 1.3](execution-guide.md), autonomous runs) — then advances group by group without pausing, assesses every acceptance criterion, and ends with the hand-off folder: the completion report as its README, and the open-items files when the target environment needs setup — [execution-guide.md](execution-guide.md) § 1.3, § 2.2, § 3; [open-items-guide.md](open-items-guide.md). A spec fix is a `uipath-planner` edit, then the build runs again.
2. **What the genome's SDD already decided is answered, not asked**: the split and queue design, the implementation mode, the package pins, the refactor answers — [execution-guide.md § 1.1](execution-guide.md).
3. **A build on an extracted genome is a migration by default**: catalogs derived from the export at preflight, UI targets and test data migrated from them, no secret ever copied — [source-migration-guide.md](source-migration-guide.md).
4. **Build through the owning skill, verifiably**, never by writing a project outside its journey: its mandatory reads, and for every activity kind the default XAML and the package's per-activity doc before the first file using it is written; workflows authored as files, never generated — [execution-guide.md § 2.2](execution-guide.md).
5. **Composite source actions are contracts in the genome and patterns at build** — [genome-format-guide.md § Workflow](genome-format-guide.md); [ui-target-migration-guide.md § Composite interactions](ui-target-migration-guide.md).
6. **UiPath selector truth lives in one guide** — [selector-translation-guide.md](selector-translation-guide.md) rules 1–16, with what its technology guides add to them. **Verification is a property of the acting activity**, except a test project's checkpoints — [ui-verification-guide.md](ui-verification-guide.md).
7. **A migration's UI targets go through exploration, the offline migration and the live healing pass, in that order**; a migrated target carries a verdict — `verified`, `shape-verified` or `offline-unverified` — and the live checks it still owes, and a reachable application is a windfall, never a precondition for finishing the run — [ui-target-migration-guide.md](ui-target-migration-guide.md) rule 4 and § Verifying targets; [live-application-guide.md](live-application-guide.md).
8. **Most source steps are not UI activities**, and linking is the last thing done to a workflow file — [source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md); [ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md).
9. **The transactional shape is split at build**: the genome describes and never decides, the build asks the split questions per flow unless the SDD recorded the split, and the behaviour is owed whatever the choice — [transactional-shape-guide.md](transactional-shape-guide.md); [transactional-execution-guide.md](transactional-execution-guide.md).
10. **Source values are read from the source, not from its rendering**: an empty rendering is "not shown", never "not set", and the build follows the source where it and the genome disagree — [extracted-genome-guide.md § Source values](extracted-genome-guide.md).
11. **Building a genome extracted from a UiPath source is a refactor**, and so is a migration whose request asks for one: every component re-authored on the target its shape fits, the genome the contract, every changed output a plan row with its reason, characterization tests before the logic — [refactor-guide.md](refactor-guide.md). **A UiPath source's deployed state is source**: the binding a process overrides is the value that runs — [uipath-source-guide.md § Deployed State](uipath-source-guide.md).
12. **Nothing reaches a tenant unasked**: the build stops at the pack dry run, never writes to a tenant the user did not name, and a build that replaces a running automation ends its open items with the cutover — [open-items-guide.md](open-items-guide.md); [refactor-guide.md § Done](refactor-guide.md).

## Read Plan

**How a read is done.** A file the plan reads whole is read whole — never grepped or skimmed. A pointer that names a section (`guide.md § Section`) is a section read: that section in full, opened by its heading without listing the file's headings first. A guide no condition of the plan has reached stays closed. A framework selectors guide's per-technology tables are a **catalog**, read by section: list its headings, then read the sections for the technologies the source recorded; the rules around them are read whole.

Every turn resends the whole context: a reference read early is paid again on every later turn, and one a later answer rules out is paid for nothing. `build` reads, at each phase, only what this table names for the conditions that hold; `context` answers the conditions about the genome.

| Phase | Condition | Read |
|---|---|---|
| start, before any question | — | [execution-guide.md](execution-guide.md); [genome-format-guide.md § Design Links](genome-format-guide.md) when `designed_in` is set (another section of it is read when an execution guide points into it, row below); each skill named in Build With / Components, invoked once for preflight discovery and the scaffolding options — its SKILL.md only, its mandatory reads wait for the build; [transactional-execution-guide.md](transactional-execution-guide.md) and [transactional-shape-guide.md](transactional-shape-guide.md) when `transactional` is true, before the split questions |
| start, before any question | `build_mode` is `migration` (the Source Map names a framework other than UiPath) | [source-frameworks-guide.md](source-frameworks-guide.md) whole — it resolves the framework migration pack and names the migration reads |
| start, before any question | `build_mode` is `refactor`, or the request asks for a refactor | [refactor-guide.md](refactor-guide.md) and [skill-mapping-guide.md](skill-mapping-guide.md) whole; the SKILL.md of every product § Choosing the target there offers a component, unless `designed_in` is set and the SDD is on disk — then only for a component the SDD leaves unplaced ([refactor-guide.md](refactor-guide.md) rule 7) — invoked once for its capability check; its mandatory reads wait for the build |
| build, once the configuration answers exist | — | the owning skill's mandatory reads, through its own journey |
| build | `extracted` is true | [extracted-genome-guide.md](extracted-genome-guide.md); [source-frameworks-guide.md](source-frameworks-guide.md) |
| build | an export was resolved | the build reads of [source-frameworks-guide.md](source-frameworks-guide.md) for the Source Map's framework — § UiPath sources ([uipath-source-guide.md § UI Target Locators](uipath-source-guide.md) and § Test Data, [source-migration-guide.md § Migration preflight](source-migration-guide.md) step 4, [ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md), [ui-verification-guide.md](ui-verification-guide.md)) or § Other frameworks — the framework migration pack |
| build | a group builds UI activities, extracted genome or not | [ui-verification-guide.md](ui-verification-guide.md) |
| build | the genome has test components, extracted or not — `context`'s `test_components` when it emits it, otherwise the Components table's Type cells and the Deployment section | [test-execution-guide.md](test-execution-guide.md) |
| build | a group is planned in parts, runs through subagents or forks, or resumes after a pause or a compaction | [parts-guide.md](parts-guide.md) and [execution-parts-guide.md](execution-parts-guide.md) |
| build | the Live application answer names a reachable application | [live-application-guide.md](live-application-guide.md), before the target spec is written |
| build | a group uses a doc or a tool [package-doc-errata-guide.md](package-doc-errata-guide.md) corrects | that doc's row, read with the doc, and the § Tools rows for the tools a group builds with |
| build | a Build With row names a retired skill or one the host lacks | [skill-mapping-guide.md](skill-mapping-guide.md) |
| build | an execution guide points into a section | that section of genome-format-guide.md, transactional-shape-guide.md or extracted-genome-guide.md |
| end | the target environment needs setup | [open-items-guide.md](open-items-guide.md) |

Each phase's reads go out in at most three turns, never file by file as each file names the next:

1. **Turn 1**, one message: every file the phase reads whole, the sections the plan names by heading, and the heading list (a search for `^#` lines) of every catalog or file it reads by sections the plan does not name.
2. **Turn 2**, one message: the sections chosen from those lists, and the owning skill's discovery for the activity kinds in play.
3. **Turn 3**, only what turn 2 routed to.

A plan never narrows an owning skill's contract: a read that skill mandates is performed even when no plan names it, a read that misses (a wrong path) is retried the next turn, and neither is dropped to stay within three turns.
