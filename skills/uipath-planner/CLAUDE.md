# uipath-planner — Subject Homes of the Genome Lanes

Governs editing this skill; never read in a run. Every subject is stated in full in exactly one file; every other mention is a one-line pointer to that file and section. The SDD lanes (Phase D, case design, Lanes A and B) keep their homes in the guides `SKILL.md` § Reference Navigation lists.

## Home per subject

| Subject | Home |
|---|---|
| The planner's output rule (genome, SDD, SDD → genome, never a PDD); one writer, one builder, one handoff | `SKILL.md` Critical Rule 14 |
| Which lane a request lands in; the lanes' read plans; framework pack resolution for extraction | `SKILL.md` § Entry Guard, § Read Plans, § Source Frameworks |
| Author: inputs (idea, SOP, PDD, TO-BE, agreed SDD), scenario proposals for a goal, level, complexity signals, product selection for an authored genome, bounded follow-ups, write and check, hand to the build | `references/authoring-guide.md` |
| Extract: estate assessment, the pipeline from detection to the checked Source Map, evidence policy, Map seeding and divergence check through the Cartographer MCP, the handoff to the build | `references/extraction-guide.md` |
| Verifying a suspected source defect: the two passes, the classification table, verdicts from subagents | `references/defect-verification-guide.md` |
| What extraction's parts add to the shared parts guide | `references/extraction-parts-guide.md` |
| Edit requests and what each updates, regeneration of a Map-bound genome's Map and SDD parts, the check after every edit, partial re-extraction | `references/editing-guide.md` |
| The SDD-only design of a migration or refactor (genome and Map in, no PDD) | `references/sdd-generation-guide.md` § SDD-only design |
| Building from a genome in a plan | `references/multi-skill-patterns-guide.md` § Pattern 7 |
| Genome templates and worked examples | `assets/templates/*-genome-template.md`, `assets/examples/` — every example passes `scripts/check-genome.py --profile strict` |
| Genome levels (component / process), the test-project exception, section rules, stubs, population matrix, `*[Inferred]*`, write-then-offer-edits, complexity inference, design links, the composite UI interaction contract, one credential asset per login account | `references/genome-format-guide.md` |
| Source Map contract rows and the step table, source values, the source-defect marker and the defect index | `references/extracted-genome-guide.md` |
| Transactional Shape: unit of work, flows and levels, roles, options A/B/C, outcomes, step groups, the derivation table, stub | `references/transactional-shape-guide.md` |
| Build With skill names, decision tree, operate-only skills, common combinations | `references/skill-mapping-guide.md` |
| Work in parts in either lane: orchestrator, brief, ledgers, read plans, forks, returns, one owner | `references/parts-guide.md` |
| UiPath source facts: reading order, detection, inventory, signals per artifact type, deployed state, UI target locators, test data, provenance, pitfalls | `references/uipath-source-guide.md` |
| What `scripts/check-genome.py` checks (its docstring) | the script, canonical here |
| The Map of Work schema, its records and its changesets | the Cartographer MCP — never encoded in this skill |
| Building, verifying and handing off a genome | `uipath-genome-builder` — never this skill |

## Genome format and the shared checker

`references/genome-format-guide.md`, `references/extracted-genome-guide.md`, `references/transactional-shape-guide.md`, `references/skill-mapping-guide.md`, `references/parts-guide.md` and `references/uipath-source-guide.md` hold the genome format and exist only in this skill. `scripts/check-genome.py` is the one file shared with `uipath-genome-builder`, byte-identical and canonical here.

1. **Edit the checker here**, then run `python3 scripts/check-genome-core.py --fix` from the repository root to copy it to `uipath-genome-builder`; CI fails while the copies differ.
2. **A change to what a genome section means** is mirrored in `skills/uipath-genome-builder/references/genome-reading-guide.md` in the same PR — the builder's restatement of the parts of the format a build acts on. A writing-only rule (how to word, extract or size a section) needs no mirror.
3. **The format guides name build-side rules by their subject** ("`uipath-genome-builder`'s split questions"), never by a `uipath-genome-builder` file, so this skill keeps working when `uipath-genome-builder` is absent.
4. **The genome owners own** the genome lanes, the format guides, the checker and the genome-writing tests; the planner owners own the SDD lanes (`CODEOWNERS`).
