# uipath-genome — Subject Homes

Every subject is stated in full in exactly one file; every other mention is a one-line pointer to that file and section. Edit the home; leave the pointers. A change touching more than the home plus its pointers is putting content in the wrong file.

## Home per subject

| Subject | Home |
|---|---|
| Genome levels (component / process), test-components-are-one-test-project exception, section rules, stubs, population matrix, `*[Inferred]*`, write-then-offer-edits, complexity inference | `references/genome-format-guide.md` |
| Composite UI interaction **contract** (what a substep must carry) | `genome-format-guide.md` § Workflow |
| Credential asset per login account; secrets never in genome, data file or report | `genome-format-guide.md` § Platform Dependencies |
| Source Map contract rows; "genome files are the only output" (locators and rows stay in export) | `genome-format-guide.md` § Source Map |
| Extraction pipeline, evidence policy for blanket screen captures, completing and checking Source Map | `references/extraction-guide.md` |
| Authoring steps, platform-capability suggestions, bounded follow-ups, authored edit table | `references/authoring-guide.md` |
| Build With skill names, decision tree, operate-only skills | `references/skill-mapping-guide.md` |
| Configuration and scaffolding questions, project/solution resolution, library gating, skill groups, owning-skill contract, subagents, acceptance verdicts, completion report | `references/execution-guide.md` |
| Migration preflight, Object Repository identity, composite **patterns** (build), verification on acting activity, Element Scope, live verification per family, result parity, test-data pipeline, executor records | `references/source-migration-guide.md` |
| Every UiPath-side selector fact: tag chain per technology, attribute catalog and tiers, matching semantics, rules 1–16 (criteria, purpose, `aaname`, anchors, position, tables, scope, identifiers, description, confidence, no-selector, one tag one node, driver verification, widget anatomy), § Checking a definition | `references/selector-translation-guide.md` |
| Definition and anchor shapes when no application reachable (temporary) | `references/offline-definition-workarounds-guide.md` |
| What a source guide must contain | `references/sources/source-framework-contract.md` |
| Framework facts only: detection, inventory, signals, composite-action wording, locator formats, per-field translation tables, framework pitfalls | `references/sources/<framework>-source-guide.md`, `<framework>-selectors-guide.md` |
| Mode detection, Source Frameworks table, one- or two-sentence rules naming subject and home, task navigation | `SKILL.md` |

## Rules

1. **Generic first, framework second, never application-only.** A rule that holds for any source lives in a generic guide; a source guide keeps only what is specific to its framework and points to the generic rule. Application material (Workday, SAP, …) survives only as a worked example inside the generic rule it illustrates or in that framework's guides.
2. **A procedure lives in the guide of the mode that runs it.** Extraction-time steps in the extraction guide, execution-time steps in the execution or migration guide, even when both run the same script.
3. **SKILL.md is a router.** A Critical Rule names the subject and its home in one or two sentences; it never restates conditions, numbers or examples. Anti-patterns in SKILL.md route; the prohibition in full lives with the subject.
4. **Anti-pattern lists hold only the file's own subjects.** Everything else is a pointer, or is deleted when the home already states the prohibition.
5. **A pointer may add detail only when that detail exists nowhere else.** Prefer adding it to the home.
6. **Catalog files are read by section, rule files in full.** The attribute catalog in the selector guide and the per-technology tables in a selectors guide are catalogs: list headings, read the sections for the technologies in play. Rules, procedures and contracts are read whole. Say which kind a file is at its top.
7. **Keep the external contracts** unchanged unless the change is the point: frontmatter `description`, the Source Frameworks table shape, the Source Map contract rows, script names and flags.
8. **No meta-commentary.** Do not write sentences about the document's own editorial behaviour or reconcile differences between files in prose; if two files disagree, fix one.
9. **No UIA CLI syntax outside the offline guide.** `uip rpa uia` subcommands, their flags and artifact filenames are co-versioned with `UiPath.UIAutomation.Activities` and drift. Name the capability (driver default, attribute listing, selector evaluator, snapshot reload, the OR CLI's listing / replace / create commands, element-interaction probes) and route syntax to the package guide `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Documentation. The vocabulary is defined once in selector-translation-guide rule 15. Generic `uip rpa` commands (`validate`, `activities get-default-xaml`, …) are stable and allowed. `offline-definition-workarounds-guide.md` is the labelled temporary exception.
10. **Conflicts resolve toward the most recently verified statement** (a live driver pass beats a first-pass inference beats a vendor document), and the resolution is recorded in the PR.

## Where to put new content

| New content | Home |
|---|---|
| UiPath selector fact (new attribute, tier, matching quirk, node rule) | selector-translation-guide — then reference from framework guide |
| New build pattern for a composite interaction | source-migration-guide § Composite interactions (+ source guide's wording row) |
| Framework's new action, locator format or pitfall | that framework's source or selectors guide |
| New genome section or content rule | genome-format-guide (+ templates) |
| New scaffolding question or report line | execution-guide |
| New framework | `sources/<framework>-source-guide.md`, `-selectors-guide.md`, row in SKILL.md § Source Frameworks — in one change |
