---
paths:
  - "skills/uipath-planner/**"
  - "skills/uipath-genome/**"
  - "skill-flavors/studioweb/uipath-planner/**"
  - "skill-flavors/studioweb/uipath-genome/**"
  - "tests/tasks/uipath-planner/**"
  - "tests/tasks/uipath-genome/**"
---

# Genome Skills — Subject Homes

`uipath-planner` writes, checks and keeps current genomes and SDDs; `uipath-genome` builds genomes. Each subject is stated in full in one file per skill; a fact both skills need is written in each and listed under § Copies kept in both skills; every other mention points to it. Edit the home, leave the pointers.

## Home per subject

Paths are relative to the skill folder.

### uipath-planner

| Subject | Home |
|---|---|
| Genome format: levels, section rules, stubs, population matrix, `*[Inferred]*`, write-then-offer-edits, provenance, Design Links | `references/shared/genome-format-guide.md` |
| Source Map, source values, source defects | `references/shared/extracted-genome-guide.md` |
| Transactional Shape, the `Decided:` line and its project chain | `references/shared/transactional-shape-guide.md` |
| Extraction pipeline, its questions (the refactor questions Retire, Fold and Target: § Step 6c), sizing, reading plan | `references/extract/extract-guide.md`; UiPath source facts: `references/extract/uipath-source-guide.md` with `uipath-rpa-signals-guide.md` and `uipath-non-rpa-signals-guide.md`; framework pack resolution: `references/extract/source-frameworks-guide.md`; extraction in parts: `references/shared/extraction-parts-guide.md` |
| Defect verification | `references/shared/defect-verification-guide.md` |
| `author`: genome from an idea, PDD, TO-BE or SDD; scenario proposals | `references/author/author-guide.md`; from an agreed SDD: `references/author/genome-from-sdd-guide.md`; scenarios: `references/author/scenario-proposal-guide.md` |
| `edit`: edit requests and what each updates, partial re-extraction | `references/edit/edit-guide.md` |
| Skill mapping: Build With names, Decision Tree, target choice (a refactor's targets included), operate-only skills, common combinations | `references/shared/skill-mapping-guide.md` |
| `design`: SDD phases, products, packages, solution composition, caller requests | `references/design/design-guide.md`; Phase 3: `references/design/sdd-writing-guide.md`; the rest of `references/design/` per subject |
| SDD fingerprint | `scripts/sdd-fingerprint.mjs` |
| `check` and the strict check after `author`, `extract` and `edit`; genome checker: what it checks | `SKILL.md`; checker: `scripts/check-genome.mjs` header comment |
| `decompose`: dated plan and tasks | `references/decompose/decompose-guide.md`; format: `references/shared/plan-and-tasks-format.md` |
| Verb choice, chaining, Critical Rules | `SKILL.md`; each verb's reads: its guide's § Read Plan |

### uipath-genome

| Subject | Home |
|---|---|
| Verb choice | `SKILL.md` |
| `build` start, verb rules, read plan | `references/build-guide.md` (§ Start, § Verb Rules, § Read Plan) |
| What each genome section means at build | `references/genome-reading-guide.md` |
| Execution: phases, target project resolution, skill groups, owning-skill contract, acceptance verdicts | `references/execution-guide.md` |
| Configuration and scaffolding questions, autonomous runs | `references/configuration-questions-guide.md` |
| A build in parts: lead agent, brief, ledgers, resuming | `references/execution-parts-guide.md` |
| Transactional shape at build: split questions, the projects a `Decided:` chain names, REFramework surfaces | `references/transactional-execution-guide.md` |
| Migration: preflight, catalogs, credentials, source steps | `references/source-migration-guide.md`; source and pack resolution: `references/source-frameworks-guide.md` |
| UI target migration: three phases, target spec, Object Repository, verification labels | `references/ui-target-migration-guide.md`; composite interaction patterns: `references/composite-interactions-guide.md` |
| UiPath selector facts: tag chains, tiers, rules 1–16 | `references/selector-translation-guide.md`; matching semantics and checking a definition: `references/selector-matching-guide.md`; per technology: `selector-translation-web-guide.md`, `selector-translation-sap-guide.md`, `selector-translation-desktop-guide.md` |
| Live application: exploration, live healing pass | `references/live-application-guide.md` |
| Where a UI check goes, in every build | `references/ui-verification-guide.md` |
| Test components at build | `references/test-execution-guide.md` |
| Refactor of a UiPath source: contract, build questions, plan, run modes, cutover | `references/refactor-guide.md` |
| Open items for the target environment | `references/open-items-guide.md` |
| Completion report and hand-off folder | `references/completion-report-guide.md` |
| Package doc and tool errata (temporary) | `references/package-doc-errata-guide.md` |
| Offline definition workarounds (temporary) | `references/offline-definition-workarounds-guide.md` |

Framework facts (detection, inventory, locators, per-field translation, pitfalls, scripts, examples) live in the framework migration pack, never in either skill. What a pack contains: the pack's `CONTRACT.md`.

## Rules

1. **The two skills never read or link each other's files.** Naming the other skill and its verbs is allowed. A fact both need is written in both and listed under § Copies kept in both skills.
2. **Generic first, framework second, never application-only.** A rule that holds for any source lives in a generic guide; a framework's guide keeps only what is specific to it. Application material survives only as a worked example inside the generic rule, when it shows what the generic wording cannot. Values from the run that prompted an edit are not examples.
3. **A procedure lives in the guide of the verb that runs it**, even when two verbs run the same script.
4. **SKILL.md is a router.** A Critical Rule names its subject and home in one or two sentences; conditions, numbers and examples stay in the home.
5. **No meta-commentary.** No sentences about a document's own editing or reconciling two files in prose; when two files disagree, fix one.
6. **What another skill, a CLI or a package doc owns is named, never restated.** Name the artefact or capability; the build reads details from the owner. `uip rpa uia` syntax routes to the UI Automation package guide; generic `uip rpa` commands are stable and allowed. `offline-definition-workarounds-guide.md` is the labelled temporary exception.
7. **UiPath behaviour is written as the latest version shows it**, with no per-version conditions. `package-doc-errata-guide.md` is the labelled temporary exception.
8. **The builder ships no selector checker and no target tool.** A run writes its own script where it needs one (`selector-matching-guide.md` § Checking a definition).
9. **The framework migration pack cites rules by subject**, in the skill's words (a heading or bold rule head), never by file name or number. Renaming a subject the pack quotes updates the pack in a paired PR.
10. **Every reference file has its row in its verb's § Read Plan**, keyed by a condition decidable at that phase, written in the same change as the file.
11. **Temporary guides are deleted on their conditions:**
    - `offline-definition-workarounds-guide.md`: once the UIA CLI creates a first definition offline and registers a number attribute bound to a selector variable.
    - `package-doc-errata-guide.md`: a package's section once that package's shipped docs carry the corrected text; a tool's row once the tool behaves as its docs say; the file once no section is left.
12. **Keep the external contracts** unchanged unless the change is the point: each skill's frontmatter `description`, the verbs and entry points other skills and hosts call, the pack resolution steps and the pack's README § Frameworks table shape, the Source Map contract rows, the planner's script names and flags.
13. **A file's boundary is its audience: verb × condition.** A rule sits in the file every session that needs it reads, and in no file a session reads without needing it. A file every session of a verb reads holds no conditional block above about 5 KB; a block under about 5 KB whose condition is common stays where it is.
14. **Check each added sentence against what its reader reads in that verb** (the verb's § Read Plan and the skill's source frameworks guide), and cut it when those reads already give it. At build the pack's source guide is read only in the sections the builder points to, so a pack fact a build needs reaches it through one pointer in a file the build reads. What the owning skill's routing already opens for the work being built needs no pointer. A step that says where its output goes is not listed again among the run brief's contents or a read plan's reads.

## Copies kept in both skills

Each row is one fact written in both skills. A change to either side changes the other in the same PR.

| Subject | uipath-planner | uipath-genome |
|---|---|---|
| Options A, B and C, the item store, per-item state a queue cannot hold, a source's coordination stores and owned database | `references/shared/transactional-shape-guide.md` § Rules rule 3 | `references/transactional-execution-guide.md` § Shape Rules rule 2 |
| The REFramework and the behaviour owed whatever the split | `references/shared/transactional-shape-guide.md` opening paragraph | `references/transactional-execution-guide.md` § Shape Rules opening paragraph |
| `Decided:` line form and its project chain | `references/shared/transactional-shape-guide.md` § Rules rule 8 | `references/transactional-execution-guide.md` § Shape Rules rule 4 |
| Split-option signals table, different-component producer and consumer | `references/shared/transactional-shape-guide.md` § Rules rule 8 derivation table | `references/transactional-execution-guide.md` § Shape Rules rule 5 |
| Several levels of items are one unit of work | `references/shared/transactional-shape-guide.md` § Rules rule 11 | `references/transactional-execution-guide.md` § Shape Rules rule 7 |
| Chains: the upstream reference, creating the downstream item | `references/shared/transactional-shape-guide.md` § Rules rule 13 | `references/transactional-execution-guide.md` § Shape Rules rule 8 |
| UiPath Test Data table | `references/extract/uipath-source-guide.md` § Test Data | `references/source-migration-guide.md` § Test Data |
| Source Map contract and its example | `references/shared/extracted-genome-guide.md` § Source Map | `references/genome-reading-guide.md` § Source Map |
| Source values | `references/shared/extracted-genome-guide.md` § Source values | `references/genome-reading-guide.md` § Source values |
| Secrets and attached applications across component boundaries | `references/shared/genome-format-guide.md` § Platform Dependencies, § Interface (component) | `references/genome-reading-guide.md` § Platform Dependencies, § Interface |
| Genome file name slug | `references/shared/genome-format-guide.md` § File Naming and Location | `references/genome-reading-guide.md` § File Naming and Location |
| Framework migration pack resolution | `references/extract/source-frameworks-guide.md` § Other frameworks — the framework migration pack | `references/source-frameworks-guide.md` § Other frameworks — the framework migration pack |
| Running in parts: brief, ownership, ledgers, waits, resuming | `references/shared/extraction-parts-guide.md` § Running in Parts | `references/execution-parts-guide.md` § Running in Parts |

## Paired edits

One change, every file in its row, same PR.

| Change | uipath-planner | uipath-genome | Tests |
|---|---|---|---|
| Genome format change | `references/shared/genome-format-guide.md` (or `extracted-genome-guide.md` / `transactional-shape-guide.md` for its subject); `assets/templates/component-genome-template.md`; `assets/templates/process-genome-template.md`; `scripts/check-genome.mjs` | the subject's § Copies kept in both skills file; `references/genome-reading-guide.md` when the build's consequence changes | `tests/tasks/uipath-planner/_shared/test_genome_contract.py`; the example genomes strict runs over, `tests/tasks/uipath-planner/_shared/genome-examples/` |
| New UiPath file kind or product | `SKILL.md` description; `references/extract/source-frameworks-guide.md` and `references/extract/uipath-source-guide.md` detection tables; `references/decompose/decompose-guide.md` scan list; `references/shared/skill-mapping-guide.md` § Decision Tree for Ambiguous Steps and § Refactor Targets; `scripts/check-genome.mjs` skill lists | `references/source-frameworks-guide.md`; `references/execution-guide.md` § 1.4 reuse list | — |
| New building skill | `references/shared/skill-mapping-guide.md`; `scripts/check-genome.mjs` `VALID_SKILLS` / `OPERATE_SKILLS` | — | `tests/tasks/uipath-planner/_shared/test_genome_check.py` asserts both |
| A subject of § Copies kept in both skills | its planner file | its builder file | — |
| SDD fingerprint change | `scripts/sdd-fingerprint.mjs` (`check-genome.mjs` imports it) | — | `tests/tasks/uipath-planner/_shared/test_sdd_fingerprint.py` |
| `Decided:` line form (option, unit, source, project chain) | `references/shared/transactional-shape-guide.md`; `assets/templates/component-genome-template.md`; `assets/templates/process-genome-template.md`; `scripts/check-genome.mjs` | `references/transactional-execution-guide.md` | `tests/tasks/uipath-planner/_shared/test_genome_check_findings.py` |

## Where to put new content

| New content | Home |
|---|---|
| New genome section or content rule | planner `genome-format-guide.md` (+ both templates); Transactional Shape rule: `transactional-shape-guide.md`; Source Map, source-value or source-defect rule: `extracted-genome-guide.md`. Its build consequence: builder `genome-reading-guide.md` |
| New edit request or edit rule | planner `edit-guide.md` |
| Rule for verifying suspected source defects | planner `defect-verification-guide.md` |
| Rule for extraction in parts | planner `extraction-parts-guide.md` |
| Fact about reading a UiPath source or its deployed state | planner `uipath-source-guide.md` (or its RPA / non-RPA signals guide); what the build re-reads of the source: builder `source-migration-guide.md` |
| New scaffolding question | builder `configuration-questions-guide.md` |
| New report line | builder `completion-report-guide.md` |
| Rule for a build in parts | builder `execution-parts-guide.md` |
| UiPath selector fact | the builder's selector guide of its technology; `selector-translation-guide.md` when it holds for every technology; matching quirk: `selector-matching-guide.md` |
| Build pattern for a composite interaction across technologies | builder `composite-interactions-guide.md` |
| Where a UI check goes | builder `ui-verification-guide.md` |
| Exploring, checking or healing against a reachable application | builder `live-application-guide.md`; what every UI migration owes the application, reachable or not: `ui-target-migration-guide.md` § Verifying targets |
| Building test components or migrating their data | builder `test-execution-guide.md` |
| Refactor target, retire or fold question | planner `extract-guide.md` § Step 6c; the target rules: `skill-mapping-guide.md` |
| What a refactor keeps, asks at build, plans, tests or hands over for cutover | builder `refactor-guide.md` |
| A framework's transactional construct | UiPath: planner `uipath-source-guide.md`; any other framework: its source guide in the framework migration pack |
| A framework's new action, locator format or pitfall | that framework's guides in the framework migration pack |
| New framework | a `<framework>/` pack in the framework migration pack plus its README § Frameworks row; nothing in either skill |
