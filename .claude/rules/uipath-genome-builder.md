---
paths:
  - "skills/uipath-genome-builder/**"
  - "skill-flavors/*/uipath-genome-builder/**"
  - "tests/tasks/uipath-genome-builder/**"
---

# uipath-genome-builder — Subject Homes

Governs editing `skills/uipath-genome-builder/`; it lives here, not in the skill folder, so it never ships and never loads in a run. Paths below are relative to the skill folder. The skill builds automations from genomes with two verbs, on the pattern of a command-line tool: `SKILL.md` routes and holds the rules every verb shares; `references/build-guide.md` holds `build`'s own rules and read plan, and `references/execution-guide.md` its procedure. `uipath-planner` writes and changes every genome; this skill never does. Every subject is stated in full in exactly one file; every other mention is a one-line pointer to that file and section.

## Genome core — shared with `uipath-planner`, canonical there

`references/genome-format-guide.md`, `extracted-genome-guide.md`, `transactional-shape-guide.md`, `skill-mapping-guide.md`, `uipath-source-guide.md`, `parts-guide.md`, `source-frameworks-guide.md`, `assets/templates/*-genome-template.md` and `scripts/check-genome.mjs` are copies of `uipath-planner`'s genome core. **Never edit them here**: edit the planner's copy, then run `node scripts/check-genome-core.mjs --fix` from the repository root. The rules for core files (links, verb names) are in [uipath-planner.md](uipath-planner.md) § Genome core.

## Home per subject

| Subject | Home |
|---|---|
| Choosing between `build` and `check`, and the hand-back to `uipath-planner` for any genome write | `SKILL.md` § Choosing the Verb |
| What `build` reads at each phase and the condition that opens each guide; its own rules | `references/build-guide.md` |
| Credential asset per login account, Secret asset per secret with no account, a secret crossing no component boundary; secrets never in genome, data file or report; values the platform keeps per environment as assets | `genome-format-guide.md` § Platform Dependencies; at build: `execution-guide.md` § 2.2, credentials |
| Configuration and scaffolding questions (the source-fidelity question, the Live application and Healing pass questions among them), project/solution resolution, library gating, skill groups, owning-skill contract, what the names and texts a build writes say and never cite (run records, source ids), acceptance verdicts, the hand-off folder (its files and where each is written) and its README, the completion report with its split line | `references/execution-guide.md` |
| Applying or declining the transactional shape at build: split questions and their answer line, autonomous split defaults, projects a split materialises, REFramework template creation, groups and surfaces, the REFramework build items (the record store's writes and fetch, children kept in it), alternative unit of work, four-exit verification | `references/transactional-execution-guide.md` |
| What a build's parts add: the project owner and its shared operations, the project ledger contract and progress file, planning parts, per-activity discovery in the read plan, one host per project, linking order, solution mutations, the run brief's contents, the part report and its mechanical checks | `references/execution-parts-guide.md` |
| Open-items files: target-environment setup steps for the engineer (per project and per solution, in the hand-off folder) | `references/open-items-guide.md` |
| Migration preflight (including the secret scrub and what the build follows when the genome and the source disagree), credentials from the source's accounts, what each **kind** of source step becomes at build time, the source's names and shape kept in the rebuild and the correspondence table, executor records | `references/source-migration-guide.md` |
| UI target migration: the migrated-target rules, the three phases (exploration, the offline migration, the live healing pass) and that no part drives the application between them, the target spec, link ordering and idempotency, Object Repository identity, composite **patterns** (build), Element Scope, the three verification labels, the live checks every UI migration writes | `references/ui-target-migration-guide.md` |
| The two live phases of a migration, with a reachable application: driving it read-only and probes, exploration with its application notes, the verdict per interaction family, the seeds and the contract probe, the live healing pass (the read-only check of every target once linked, then the runs on the user's yes) | `references/live-application-guide.md` |
| Where a UI check goes in every build (`VerifyOptions` on the acting activity, a Check activity only for a branch, a test project's checkpoints), failure handling and logging once | `references/ui-verification-guide.md` |
| Test components at build: test-case shape, the test-data rules and pipeline (store → entity, files → variations), result parity, checkpoint titles and the checkpoint map per component | `references/test-execution-guide.md` |
| Every technology-neutral UiPath-side selector fact: tag chain per technology, attribute tiers and roles, `wnd`, matching semantics, rules 1–16 (criteria, purpose, `aaname`, captions and `<nav>` paths, position, tables, scope, identifiers, description, confidence, no-selector, one tag one node, driver verification, widget roles), § Checking a definition | `references/selector-translation-guide.md` |
| A technology's tags and its part of rules 4–16: web (`html`, `webctrl`, the `aaname` test, web grids and scopes, web widget anatomy) | `references/selector-translation-web-guide.md` |
| SAP GUI (`wnd` session attributes, `sap`, SAP tables and session windows) | `references/selector-translation-sap-guide.md` |
| Desktop (`uia`, `ctrl`, `java`, other tags) | `references/selector-translation-desktop-guide.md` |
| The definitions the offline migration builds from the target spec: seeds, shapes, the order of commands, what offline authoring cannot know; the workaround for a number attribute bound to a selector variable (temporary: the file is deleted once the UIA CLI creates a first definition offline and registers a number attribute bound to a selector variable) | `references/offline-definition-workarounds-guide.md` |
| Corrections to an installed package's per-activity docs until the corrected package ships, and tool defects met in builds with what the build does instead, until fixed (temporary: a package's section is deleted once that package's shipped docs carry the corrected text, a tool's row once the tool behaves as its docs say, the file once no section is left) | `references/package-doc-errata-guide.md` |
| A refactor (executing a genome extracted from a UiPath source, or from another framework when the request asks for one): the contract (kept, changed with a reason, carried over), the refactor questions (retire, fold, target, rulings on source defects, run modes, run record, connections) and their answer line, choosing the target (steps typed by the mapping guide's decision tree, one host, coordination replaced by the target's means, capabilities confirmed without a tenant, shape-deciding probes), the refactor plan, characterization tests, shadow and write-test modes and the comparison, the Cutover section of the open items, done and its report line | `references/refactor-guide.md` |
| `build`'s own rules and read plan | `references/build-guide.md` |
| What a genome section means, how it is written | the genome core (`genome-format-guide.md` and its siblings) |

## Rules

1. **A build-side rule lives in this skill's guides**, a writing rule in the core or in `uipath-planner`. A guide here names a `uipath-planner` guide by skill and file name, never by a link.
2. **Scripts are Node** (`node`, built-ins only, Node >= 20); repository tests and graders may stay Python.
3. The remaining editing rules for the genome guides — generic first, procedures in the verb that runs them, catalogs read by section, owners named not restated — are [uipath-planner.md](uipath-planner.md) § Rules for the genome guides; they hold here unchanged.
