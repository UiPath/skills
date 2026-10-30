---
paths:
  - "skills/uipath-planner/**"
  - "skill-flavors/*/uipath-planner/**"
  - "tests/tasks/uipath-planner/**"
---

# uipath-planner — Verbs and Subject Homes

Governs editing `skills/uipath-planner/`; it lives here, not in the skill folder, so it never ships and never loads in a run. Paths below are relative to the skill folder. The skill is one entry point with seven verbs, on the pattern of a command-line tool (`uipath-genome-builder` carries `build` on the same pattern): `SKILL.md` routes, each verb's guide holds its procedure, its own rules and its read plan. Every subject is stated in full in exactly one file; every other mention is a one-line pointer to that file and section. Edit the home; leave the pointers. A change touching more than the home plus its pointers is putting content in the wrong file.

## Verbs and their homes

| Verb | Entry guide | Former name |
|---|---|---|
| `design` | `references/design-guide.md`; Case Management: `references/case/case-design-guide.md` | Phase D (with the Case Design Lane); `sdd-generation-guide.md`, `case-design-lane-guide.md` |
| `plan` | `references/plan-guide.md` | Lane A — PDD-driven; `pdd-driven-lane-guide.md` |
| `decompose` | `references/decompose-guide.md` | Lane B — Non-PDD; `non-pdd-lane-guide.md` |
| `author` | `references/author-guide.md` | `uipath-genome` Author mode; `authoring-guide.md` |
| `extract` | `references/extract-guide.md` | `uipath-genome` Extract mode; `extraction-guide.md` |
| `edit` | `references/edit-guide.md` | `uipath-genome` Edit mode; `editing-guide.md` |
| *build* | `uipath-genome-builder` — `references/build-guide.md`, then `references/execution-guide.md` | `uipath-genome` Execute mode |
| `check` | `SKILL.md` § Check; `scripts/check-genome.mjs` | `scripts/check-genome.py` |

1. **A new verb** gets a row in `SKILL.md` § Verbs, a line in § Choosing the Verb, its edges in § Chaining, an entry guide with § Verb Rules and § Read Plan, and a row here.
2. **A rule every verb obeys** goes in `SKILL.md` § Critical Rules; **a rule one verb obeys** goes in that verb guide's § Verb Rules; **a rule every genome write obeys** goes in `genome-format-guide.md` § Writing Rules. Never state one in two of these.
3. **Scripts are Node** (`node`, built-ins only, Node >= 20): users install the skills through the Node-based `uip` CLI, so `node` is present where `python3`, `bash` or `pwsh` may not be. Repository tests and graders may stay Python.
4. **The genome owners own** the genome verbs (`author`, `extract`, `edit`), their guides, the genome core, the checker and the genome tests, and `uipath-genome-builder`; the planner owners own `design`, `plan`, `decompose` and their guides (`CODEOWNERS`).

## Genome core — shared with `uipath-genome-builder`

`references/genome-format-guide.md`, `extracted-genome-guide.md`, `transactional-shape-guide.md`, `skill-mapping-guide.md`, `uipath-source-guide.md`, `parts-guide.md`, `source-frameworks-guide.md`, `assets/templates/component-genome-template.md`, `assets/templates/process-genome-template.md` and `scripts/check-genome.mjs` are the genome core. Both skills ship them byte-identical, because each is installed on its own and may not read the other's files; the canonical copies are here.

1. **Edit the core here**, then run `node scripts/check-genome-core.mjs --fix` from the repository root to copy it to `uipath-genome-builder`; CI (`uipath-genome checker unit tests`) fails while a copy differs.
2. **A core file links only to core files and to `SKILL.md`** (both skills have one). A guide outside the core is named by its skill and file name — "`uipath-genome-builder`'s execution-guide.md § 2.2" — never linked, so every link resolves in both skills; the check fails on a link that breaks this.
3. **A core file names a verb with its skill** — `uipath-planner`'s `author`, `extract`, `edit`; `uipath-genome-builder`'s `build` — so it reads correctly from either skill.
4. **Never restate the core** in either skill: point into it by section.

## Home per subject — `design`, `plan`, `decompose`

| Subject | Home |
|---|---|
| The three phases of `design`, its checkpoints, the skeleton write, SME resolution, the superset check and the `ready` flip; the SDD-only design of a migration or refactor | `references/design-guide.md` |
| The case design conversation, its one confirmation and its write; the case model and its defaults | `references/case/case-design-guide.md`; `references/case/case-design-layers-guide.md` |
| PDD extraction in any format | `references/pdd-analysis-guide.md` |
| Product scope, the Constraint Gate and the levels; platform availability | `references/product-selection-guide.md`; `references/platform-availability-guide.md` |
| Task derivation from an SDD, Pattern 7 (build from a genome) | `references/plan-guide.md`; `references/multi-skill-patterns-guide.md` |
| A plan without an SDD | `references/decompose-guide.md` |
| Plan and tasks file format | `references/plan-and-tasks-format.md` |
| Which specialist owns what (for plans) | `references/skill-mapping-guide.md` § Skill Capability Map |

## Home per subject — genome verbs

| Subject | Home |
|---|---|
| Genome levels (component / process), test-components-are-one-test-project exception, section rules, stubs, population matrix, `*[Inferred]*`, write-then-offer-edits, complexity inference | `references/genome-format-guide.md` |
| Composite UI interaction **contract** (what a substep must carry) | `genome-format-guide.md` § Workflow |
| Source Map contract rows and the step table (its columns and rules), how extracted unused parts are written and where those left out go; "genome files are the only output" (locators and rows stay in export) | `references/extracted-genome-guide.md` § Source Map |
| The kinds of source fact read from the source, never from its rendering (literals and case rules, counts, lengths, waits and budgets, set or typed, control-flow flags, formats, built-ins, parameter documentation, log texts, file kinds and the field a filter uses) | `extracted-genome-guide.md` § Source values |
| The source-defect marker, the evident intent, which behaviour the rebuild follows, user rulings, the defect index | `extracted-genome-guide.md` § Source Defects |
| What `scripts/check-genome.mjs` checks (its header comment), which the genome tasks also grade with; when each verb runs it; the `context` facts the read plans branch on | the script; `SKILL.md` § Check and § Setup; extract-guide Step 6b, author-guide Step 8, edit-guide § Check after every edit, source-migration-guide § Migration preflight |
| Transactional Shape: the unit-of-work test and its granularity (alternative unit of work), flows versus nested levels (the two tests of rule 12), producer and consumer roles and the Type-cell role word, queue-vs-direct choice, per-item state a queue cannot hold and the record store beside it, the three outcomes and the conditional Postponed row, step groups, two-level sources folded into one unit of work, configuration split, traceability, one Recommendation verdict, stub | `references/transactional-shape-guide.md` |
| Extraction pipeline, the questions of its first message (related resources, unused parts, subagents), sizing and the reading plan with what unused parts are, evidence policy for blanket screen captures, completing and checking Source Map | `references/extract-guide.md` |
| Verifying a suspected source defect: the two passes, the classification table, vendor-settled semantics, verdicts from subagents, writing while verdicts are out | `references/defect-verification-guide.md` |
| Authoring steps, scenario proposals for a goal, platform-capability suggestions, bounded follow-ups | `references/author-guide.md` |
| Edit requests and what each updates, for any genome and for extracted genomes; the check after every edit; partial re-extraction | `references/edit-guide.md` |
| Build With skill names, decision tree, operate-only skills, common combinations by shape | `references/skill-mapping-guide.md` |
| Work in parts in `extract` or `build`: the orchestrator, shared decisions before fan-out, the brief and its rulings, a ledger per part with its Resume block, resuming, per-part read plans, forks (when, fork or fresh subagent, what a fork does, review), returns as verdicts checked against the disk, one owner per shared artifact, the Subagents question with its defaults (the parts' model per mode, the cap of four at once) | `references/parts-guide.md` |
| What extraction's parts add: one part per component, who writes, the shared-decision list, the extraction fork's shared reads, the part's read plan, own defect verification, the return contract, reconciliation | `references/extraction-parts-guide.md` |
| UiPath source facts: reading order and designer-noise filter with the connector schema caches and the compressed connector configuration (no inventory script), detection, inventory, signals per artifact type (project settings, test projects), platform resources, the deployed state (processes, versions, binding overrides, connection identities, triggers, job history, the other processes sharing its resources) and its Source Map rows, provenance, pitfalls, which REFramework file feeds which Transactional Shape row | `references/uipath-source-guide.md` — the reference implementation of a source guide, with the sections the pack's `CONTRACT.md` gives every source guide |
| What a framework pack must contain | `CONTRACT.md` in the framework migration pack — ask the user for its location |
| Framework facts only: detection, inventory, signals, composite-action wording, locator formats, per-field translation tables, framework pitfalls, inventory scripts, worked examples | `<PACK_DIR>/<framework>/source-guide.md`, `selectors-guide.md`, `scripts/`, `examples/` in the framework migration pack — never in this skill |
| Choosing the verb, chaining verbs, the boundaries with sibling skills (activity-migrator, maestro-case), the rules every verb shares | `SKILL.md` |
| What a verb reads at each phase and the condition that opens each guide, the three-turn reading rule | each verb guide's § Read Plan (`author-guide`, `extract-guide`, `edit-guide`; `uipath-genome-builder`'s `build-guide`) |
| Framework pack resolution (ask for location, select row, run then read), how each verb reads a source, the pack-missing behaviour per verb | `references/source-frameworks-guide.md` |
| The rules every genome write obeys | `genome-format-guide.md` § Writing Rules |

## Rules for the genome guides

1. **Generic first, framework second, never application-only.** A rule that holds for any source lives in a generic guide; a source guide keeps only what is specific to its framework and points to the generic rule. Application material (Workday, SAP, …) survives only as a worked example inside the generic rule it illustrates, and only when it shows what the generic wording cannot, or in that framework's guides. Values from the run that prompted an edit (hosts, project and asset names, counts) are not examples.
2. **A procedure lives in the guide of the verb that runs it.** Extraction-time steps in extract-guide, execution-time steps in the execution or migration guide, even when both run the same script.
3. **SKILL.md is a router.** It holds the verb table, § Choosing the Verb, § Chaining and the rules every verb shares; a verb's own rules sit in its guide's § Verb Rules. A genome rule names the subject and its home in one or two sentences; it never restates conditions, numbers or examples. Anti-patterns in SKILL.md route; the prohibition in full lives with the subject.
4. **Anti-pattern lists hold only the file's own subjects.** Everything else is a pointer, or is deleted when the home already states the prohibition.
5. **A pointer may add detail only when that detail exists nowhere else.** Prefer adding it to the home.
6. **Catalog files are read by section, rule files in full.** The per-technology tables in a framework selectors guide are a catalog: list headings, read the sections for the technologies in play. The UiPath side's tags live in one selector guide per technology, each read whole when its technology is in play. Rules, procedures and contracts are read whole. Say which kind a file is at its top.
7. **Keep the external contracts** unchanged unless the change is the point: frontmatter `description`, the pack resolution steps and the pack's README § Frameworks table shape, the Source Map contract rows, script names and flags.
8. **No meta-commentary.** Do not write sentences about the document's own editorial behaviour or reconcile differences between files in prose; if two files disagree, fix one.
9. **What another skill, a CLI or an activity package's docs own is named, never restated.** A file layout, schema, field or type list owned by another skill or a CLI changes with that owner, and so do an activity's settings, verbs and limits, which its package doc owns. Name the artefact or capability (the REFramework template's configuration file, the shape the entity-create command accepts, the driver default) and let the build read the details from the owner. UIA CLI syntax is the strictest case: `uip rpa uia` subcommands, their flags and artifact filenames are co-versioned with `UiPath.UIAutomation.Activities` and drift. Name the capability (driver default, attribute listing, selector evaluator, snapshot reload, the OR CLI's listing / replace / create commands, element-interaction probes) and route syntax to the package guide `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Documentation. The vocabulary is defined once in selector-translation-guide rule 15. Generic `uip rpa` commands (`validate`, `activities get-default-xaml`, …) are stable and allowed. `offline-definition-workarounds-guide.md` is the labelled temporary exception.
10. **Conflicts resolve toward the most recently verified statement** (a live driver pass beats a first-pass inference beats a vendor document), and the resolution is recorded in the PR.
11. **Name the subject, not the step.** Refer to another part of a procedure by what it is — "once every verdict on a suspected source defect is edited in", not "once every Step 4b verdict is edited in" — so the reader need not look the step up. Keep a step number only in a pointer the reader follows to that section.
12. **UiPath behaviour is written as the latest version shows it.** The newest package source and prerelease and the current CLI are the ground truth, with no per-version conditions; a rule that holds on every version carries the older versions' safety. `package-doc-errata-guide.md` is the labelled temporary exception: it bridges released packages until their corrected docs ship.
13. **The skill ships no selector checker and no target tool.** A structural selector check proves shape, not that anything matches the screen, and a maintained rule set drifts from the selector guide; the registration and linking commands follow the installed UI Automation package (rule 9). A run writes its own script where it needs one, as selector-translation-guide § Checking a definition and source-migration-guide § UI targets state.

14. **A file's boundary is its audience: verb × condition.** A rule sits in the file every session that needs it reads, and in no file a session reads without needing it. A file every session of a verb reads holds no conditional block above about 5 KB; a block under about 5 KB whose condition is common stays where it is.
15. **Every genome reference file has its row in a verb guide's § Read Plan,** keyed by a condition decidable at that phase, written in the same change as the file. Reads are named by the plan, never discovered by following pointers; a pointer into a section of a file the plan did not open is a section read.
16. **The framework migration pack cites this skill's rules by their subject**, in the skill's own words — a section heading or a bold rule head ("the skill's rule that one tag is one node", "the skill's Source Map contract") — never by file name or number, so files here move, split and renumber without touching the pack. Renaming a subject the pack quotes updates the pack in a paired pack PR.
17. **Check each added sentence against what its reader reads in that verb** (the verb guide's § Read Plan and § Source Frameworks), and cut it when those reads already give it. At `build` the pack's source guide is read only in the sections the skill points to, so a pack fact a build needs reaches it through one pointer in a file the build reads. What the owning skill's routing already opens for the work being built needs no pointer. A step that says where its output goes is not listed again among the run brief's contents or a read plan's reads.

## Where to put new genome content

| New content | Home |
|---|---|
| UiPath selector fact (new attribute, tier, matching quirk, node rule) | `uipath-genome-builder`'s selector guide of its technology — a new driver tag or attribute family with its tier source (package reference, or *derived*); `uipath-genome-builder`'s selector-translation-guide when it holds for every technology — then reference from framework guide |
| New build pattern for a composite interaction that holds across technologies | `uipath-genome-builder`'s ui-target-migration-guide § Composite interactions (+ source guide's wording row) |
| A rule for where a UI check goes, in any build | `uipath-genome-builder`'s ui-verification-guide |
| A rule for exploring, checking or healing against a reachable application in a migration | `uipath-genome-builder`'s live-application-guide; what every UI migration owes the live application, reachable or not: `uipath-genome-builder`'s ui-target-migration-guide § Verifying targets |
| A rule for building test components or migrating their data | `uipath-genome-builder`'s test-execution-guide |
| A build or selector fact for one technology (SAP GUI tables, a Java grid) | that technology's selector guide, read only when the technology is in play; a pointer where a package doc owns the detail |
| Framework's new action, locator format or pitfall | that framework's source or selectors guide |
| New genome section or content rule | genome-format-guide (+ templates); a Transactional Shape rule: transactional-shape-guide; a Source Map, source-value or source-defect rule: extracted-genome-guide |
| New edit request or a rule for edits | edit-guide |
| A rule for verifying suspected source defects | defect-verification-guide |
| A rule for parts, subagents, forks or resuming that holds in both `extract` and `build` | parts-guide; what one verb adds: extraction-parts-guide or `uipath-genome-builder`'s execution-parts-guide |
| New scaffolding question or report line | `uipath-genome-builder`'s execution-guide |
| A rule for rebuilding a UiPath automation — what a refactor keeps, asks, plans, tests, builds for verification or hands over for the cutover | `uipath-genome-builder`'s refactor-guide; a fact about reading a UiPath source or its deployed state: uipath-source-guide |
| A framework's transactional construct (queue, work list, per-item loop, framework template) | UiPath: uipath-source-guide § Signals — XAML › REFramework projects; any other framework: its source guide in the framework migration pack, pointing to genome-format-guide § Transactional Shape — nothing in this skill |
| New framework | A `<framework>/` pack in the framework migration pack (source guide, selectors guide, script, example, smoke task) plus its row in its README § Frameworks — in one change there; nothing in this skill |
