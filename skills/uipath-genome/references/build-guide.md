# Build Guide — the `build` and `prepare` verbs

`build` turns a genome into the automation it specifies: it asks the configuration questions, builds every component through its owning skill, wires them, gives each acceptance criterion a verdict and ends with the hand-off folder. Building a genome extracted from a UiPath source is a **refactor**; one extracted from another framework's export is a **migration**. The procedure is [execution-guide.md](execution-guide.md); this guide holds the verb's rules and its read plan.

## Start

The genome facts of [SKILL.md § Setup](../SKILL.md) decide the rows of § Read Plan below. An extracted genome whose Source Map names no framework opens neither the migration row nor the refactor row until the user's answer names it.

**A file without the genome marker** is not a genome: say `uipath-planner` writes genomes, and stop.

**A Build With or Components skill the host lacks** (found when the start row of § Read Plan invokes each named skill), other than a retired name ([genome-reading-guide.md § Build With and Components](genome-reading-guide.md)): name the skill and the components that need it, say the build needs it installed, and stop.

**A component genome the Components table links is missing on disk:** ask the user for its path — the one question about the source the build asks. When the user supplies none, report the missing path as an edit for `uipath-planner`, and stop.

## Prepare

`prepare` runs the start of a build on the machine that will build, and stops before anything is built, so that every question is answered ahead in the genome's readiness file.

1. **Start as a build starts:** § Start, the § Read Plan rows of the phase "start, before any question", and [execution-guide.md](execution-guide.md) § 1.1, then its § 1.2, the preflight discovery the options are built from.
2. **Read the readiness file** beside the genome as the user's file of answers ([configuration-questions-guide.md](configuration-questions-guide.md) rule 4), its unapplied business answers going to `uipath-planner` first, as at build. No readiness file beside the genome: say that `uipath-planner` writes it ("Write the readiness file"), and stop.
3. **Select every question this build would ask** — the genome, refactor, split and scaffolding questions and the run-level ones ([configuration-questions-guide.md](configuration-questions-guide.md)) — and drop each one the request or the decided-values table answers, and each one the file already holds as an item, answered or not: a Configuration Question, a project to build into, a system's reachability.
4. **Ask each owning skill how it builds each capability the genome uses** — mail, documents and PDFs, spreadsheets, databases, files and shares, web and desktop applications, SAP, APIs and connectors, AI and document understanding, people in the loop — through the skill invoked for preflight discovery: its recommended activity package, connector or API, and the alternatives it supports. Never from memory.
5. **Write the Architecture decisions section**, in place of its "Not prepared yet" line, as § The Architecture decisions section states.
6. **Write the Build setup section**, in place of its line: every other selected question, grouped by topic (rule 1). A first line names the date and the machine's facts the options rest on: the host, the installed packages, the template feed, the source export found — never a signed-in account, a user name or a tenant URL, since the file travels with the genome.
7. **Every question** in both sections is worded as rules 2–2b state, in the readiness file's item form, a block of labelled lines: the question in bold; the `Context:` lines rule 2a gives; `Recommended:` the Recommended option with what it gives; `Instead:` each other option with what it gives; `Change:`. A question with no option the build can recommend (a path only the user knows) ends instead on `Until answered:` — what the build does while it stays open — and `Answer:`. Each section opens with a `Confirmed:` line. These two sections, and the counts the file's header and Contents give for them, are the only parts of the file `prepare` writes.
8. **Build nothing:** no project, no install, no tenant write, no question asked. End by naming the file, how many decisions and questions the two sections hold, and how many of them are needed.

A later `build` reads both sections with the rest of the file: a question with an answer or a change, or under a filled `Confirmed:` line, is not asked. Its own preflight runs again; a question whose options no longer hold there (another machine, other packages installed) is asked again.

### The Architecture decisions section

The decisions that shape what gets built, each with the build's proposal: the Recommended option, from the preflight and each owning skill's way for its capability. What the genome already shows — its Process Map and Components, Platform Dependencies, the Transactional Shape, Deployment, the Source Map — is named by section where a decision rests on it, never redrawn. Four groups, in this order, a group with no decision left out:

1. **Processes and their work items** — for each flow of the Transactional Shape without a `Decided:` line, its split questions ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)), each `Context:` naming the flow and the facts of its As-is the answer rests on.
2. **Libraries and reusable parts** — the Library layout question, its `Context:` naming the libraries and the source units each is built from, as the Source Map names them.
3. **Technology per capability** — one decision per capability the automation uses, in the order step 4 lists them: `Today:` how the source does it (the application, the client, the protocol), as the genome states it; `Recommended:` the owning skill's way — the activity package, connector or API by name; `Instead:` each alternative with when it fits (for mail: Microsoft 365 activities over Graph, the desktop Outlook activities, IMAP and SMTP). A migration keeps the source's technology unless an option names a gain the source never had and what it requires (a connection, a licence, an app registration); a choice a Configuration Question already asks is named there, never asked twice.
4. **Other decisions** — Target framework, Settings store, Workflow type, Source fidelity, Log target and, in a refactor, the refactor questions.

Each decision has a `Recorded in:` line naming the genome section that states its subject — the flow's `Decided:` line, the Target Applications row of the component that uses a capability, Deployment's Runtime and machines or Logging and retention bullet — or `the build` when no section does: `uipath-planner`'s "Apply the readiness answers" writes the answer there. Lines are one or two sentences, names in backticks, a split option's letter only beside its meaning. `prepare` run again keeps every change and the `Confirmed:` line, drops each decision the genome now records, and redraws a decision whose Recommended option rests on an answer since changed (a settings store that names the template a change removed), opening it with `New since confirmed`, which the `Confirmed:` line no longer covers.

````markdown
## 1. Architecture decisions

Usually answered by: the engineer, with the customer's architect.

Prepared <YYYY-MM-DD> by `uipath-genome` `prepare`. What gets built is the genome's Process Map and Components; what it replaces, the Source Map. Each decision carries the build's proposal: confirm it, or change it.

Confirmed:

### Processes and their work items

1. **<The split question in plain words>**
   - Context: <the flow, and the facts of its As-is the answer rests on>
   - Recommended: <the option, with what it gives and why it fits this genome>
   - Instead: <each alternative, with what it gives>
   - Recorded in: <the flow's `Decided:` line>
   - Change:

### Libraries and reusable parts

<n>. **<The Library layout question>**
   - Context: <the libraries, and the source units each is built from>
   - Recommended: …
   - Instead: …
   - Recorded in: the build
   - Change:

### Technology per capability

<n>. **<Capability>: how should the automation <do it>?**
   - Today: <how the source does it>
   - Recommended: <the owning skill's way>
   - Instead: <an alternative, with when it fits>
   - Recorded in: <the component's Target Applications row>
   - Change:

### Other decisions

<n>. **<The question in plain words>**
   - Context: <the facts the answer rests on>
   - Recommended: <the option, with what it gives>
   - Instead: <each alternative, with what it gives>
   - Recorded in: <the genome section, or the build>
   - Change:
````

## Verb Rules

These add to the Critical Rules in [SKILL.md](../SKILL.md). Each rule names its subject and the one guide that states it in full; the guide's wording is the rule.

1. **The build never skips the configuration questions** — waived only by the user: in the build request, or by the answer [configuration-questions-guide.md](configuration-questions-guide.md) rule 3 asks for (autonomous runs) — then advances group by group without pausing, assesses every acceptance criterion, and ends with the hand-off folder: the completion report as its README, and the open-items files when the target environment needs setup — [execution-guide.md](execution-guide.md) § 2.2, § 3; [configuration-questions-guide.md](configuration-questions-guide.md); [completion-report-guide.md](completion-report-guide.md); [open-items-guide.md](open-items-guide.md). A spec fix: [SKILL.md](../SKILL.md) Critical Rule 2.
2. **What the genome records as decided is answered, not asked**: a designed genome's split and queue design (`Decided:` lines), implementation mode, package pins and refactor answers, each recorded under its source's label — [configuration-questions-guide.md](configuration-questions-guide.md) rule 5 and the decided-values table.
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
| start, before any question | a Build With or Components row names a retired skill | [genome-reading-guide.md § Build With and Components](genome-reading-guide.md), before the named skills are invoked |
| build, once the configuration answers exist | — | the owning skill's mandatory reads, through its own journey; [completion-report-guide.md](completion-report-guide.md), before the answers go into the hand-off's README |
| build | the genome is extracted | [genome-reading-guide.md](genome-reading-guide.md) § Source Map, § Source values and § Source Defects; [source-frameworks-guide.md](source-frameworks-guide.md) |
| build | an export was resolved | the build reads of [source-frameworks-guide.md](source-frameworks-guide.md) for the Source Map's framework — § UiPath sources ([source-migration-guide.md § UI Target Locators](source-migration-guide.md) and § Test Data, [source-migration-guide.md § Migration preflight](source-migration-guide.md) step 4, [ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md), [ui-verification-guide.md](ui-verification-guide.md)) or § Other frameworks — the framework migration pack |
| build | a group builds UI activities, extracted genome or not | [ui-verification-guide.md](ui-verification-guide.md) |
| build | the genome has test components, extracted or not | [test-execution-guide.md](test-execution-guide.md) |
| build | a group is planned in parts, runs through subagents, or resumes after a pause or a compaction | [execution-parts-guide.md](execution-parts-guide.md) |
| build | the Live application answer names a reachable application | [live-application-guide.md](live-application-guide.md), before the target spec is written, or before the first UI group of an authored genome |
| build | a group uses a doc or a tool [package-doc-errata-guide.md](package-doc-errata-guide.md) corrects | that doc's row, read with the doc, and the § Tools rows for the tools a group builds with |
| build | an execution guide points into a section | that section of [genome-reading-guide.md](genome-reading-guide.md) |
| end | the target environment needs setup | [open-items-guide.md](open-items-guide.md) |

Each phase's reads go out in at most three turns, never file by file as each file names the next:

1. **Turn 1**, one message: every file the phase reads whole, the sections the plan names by heading, and the heading list (a search for `^#` lines) of every catalog or file it reads by sections the plan does not name.
2. **Turn 2**, one message: the sections chosen from those lists, and the owning skill's discovery for the activity kinds in play.
3. **Turn 3**, only what turn 2 routed to.

A plan never narrows an owning skill's contract: a read that skill mandates is performed even when no plan names it, a read that misses (a wrong path) is retried the next turn, and neither is dropped to stay within three turns.
