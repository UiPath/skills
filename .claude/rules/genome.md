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

`uipath-planner` writes, checks and keeps current genomes and SDDs; `uipath-genome` builds genomes. Each subject is stated in full in one file; every other mention points to it. Edit the home, leave the pointers.

## Home per subject

Paths are relative to the skill folder.

### uipath-planner

| Subject | Home |
|---|---|
| Genome format: levels, section rules, stubs, population matrix, `*[Inferred]*`, write-then-offer-edits, provenance, Design Links | `references/shared/genome-format-guide.md` |
| Source Map, source values, source defects | `references/shared/extracted-genome-guide.md` |
| Transactional Shape | `references/shared/transactional-shape-guide.md` |
| Extraction pipeline, its questions, sizing, reading plan | `references/extract/extract-guide.md`; UiPath source facts: `references/extract/uipath-source-guide.md` with `uipath-rpa-signals-guide.md` and `uipath-non-rpa-signals-guide.md`; framework pack resolution: `references/extract/source-frameworks-guide.md`; extraction in parts: `references/shared/extraction-parts-guide.md` |
| Defect verification | `references/shared/defect-verification-guide.md` |
| `author`: genome from an idea, PDD, TO-BE or SDD; scenario proposals | `references/author/author-guide.md`; from an agreed SDD: `references/author/genome-from-sdd-guide.md`; scenarios: `references/author/scenario-proposal-guide.md` |
| `edit`: edit requests and what each updates, partial re-extraction | `references/edit/edit-guide.md` |
| Skill mapping: Build With names, Decision Tree, operate-only skills, common combinations | `references/shared/skill-mapping-guide.md` |
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
| Transactional shape at build: split questions, REFramework surfaces | `references/transactional-execution-guide.md` |
| Migration: preflight, catalogs, credentials, source steps | `references/source-migration-guide.md`; source and pack resolution: `references/source-frameworks-guide.md` |
| UI target migration: three phases, target spec, Object Repository, verification labels | `references/ui-target-migration-guide.md`; composite interaction patterns: `references/composite-interactions-guide.md` |
| UiPath selector facts: tag chains, tiers, rules 1–16 | `references/selector-translation-guide.md`; matching semantics and checking a definition: `references/selector-matching-guide.md`; per technology: `selector-translation-web-guide.md`, `selector-translation-sap-guide.md`, `selector-translation-desktop-guide.md` |
| Live application: exploration, live healing pass | `references/live-application-guide.md` |
| Where a UI check goes, in every build | `references/ui-verification-guide.md` |
| Test components at build | `references/test-execution-guide.md` |
| Refactor of a UiPath source: contract, questions, target, plan, run modes, cutover | `references/refactor-guide.md` |
| Open items for the target environment | `references/open-items-guide.md` |
| Completion report and hand-off folder | `references/completion-report-guide.md` |
| Package doc and tool errata (temporary) | `references/package-doc-errata-guide.md` |
| Offline definition workarounds (temporary) | `references/offline-definition-workarounds-guide.md` |

Framework facts (detection, inventory, locators, per-field translation, pitfalls, scripts, examples) live in the framework migration pack, never in either skill. What a pack contains: the pack's `CONTRACT.md`.

## Rules

1. **The two skills never read or link each other's files.** Naming the other skill and its verbs is allowed. A fact both need is written in both.
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

## Paired edits

One change, every file in its row, same PR.

| Change | uipath-planner | uipath-genome | Tests |
|---|---|---|---|
| Genome format change | `references/shared/genome-format-guide.md` (or `extracted-genome-guide.md` / `transactional-shape-guide.md` for its subject); `assets/templates/component-genome-template.md`; `assets/templates/process-genome-template.md`; `scripts/check-genome.mjs` | `references/genome-reading-guide.md`, only when the build's consequence changes | `tests/tasks/uipath-planner/_shared/test_genome_contract.py` |
| New UiPath file kind or product | `SKILL.md` description; `references/extract/source-frameworks-guide.md` and `references/extract/uipath-source-guide.md` detection tables; `references/decompose/decompose-guide.md` scan list; `references/shared/skill-mapping-guide.md` § Decision Tree for Ambiguous Steps; `scripts/check-genome.mjs` skill lists | `references/source-frameworks-guide.md`; `references/execution-guide.md` § 1.4 reuse list | — |
| New building skill | `references/shared/skill-mapping-guide.md`; `scripts/check-genome.mjs` `VALID_SKILLS` / `OPERATE_SKILLS` | — | `tests/tasks/uipath-planner/_shared/test_genome_check.py` asserts both |
| SDD fingerprint change | `scripts/sdd-fingerprint.mjs`; `scripts/check-genome.mjs` | — | `tests/tasks/uipath-planner/_shared/test_sdd_fingerprint.py` |

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
| What a refactor keeps, asks, plans, tests or hands over for cutover | builder `refactor-guide.md` |
| A framework's transactional construct | UiPath: planner `uipath-source-guide.md`; any other framework: its source guide in the framework migration pack |
| A framework's new action, locator format or pitfall | that framework's guides in the framework migration pack |
| New framework | a `<framework>/` pack in the framework migration pack plus its README § Frameworks row; nothing in either skill |
