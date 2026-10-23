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
| The Map of Work schema, its records and its changesets | the Cartographer MCP — never encoded in this skill |
| Building, verifying and handing off a genome | `uipath-genome` — never this skill |

## Shared core

`references/genome-format-guide.md`, `references/extracted-genome-guide.md`, `references/transactional-shape-guide.md`, `references/skill-mapping-guide.md`, `references/parts-guide.md`, `references/uipath-source-guide.md` and `scripts/check-genome.py` are byte-identical copies of the canonical files in `skills/uipath-genome/`, at the same relative paths. Their subject homes are listed in `skills/uipath-genome/CLAUDE.md`.

1. **Never edit a core file here first.** Edit the canonical copy in `uipath-genome`, copy it across, then run `python3 scripts/check-genome-core.py` from the repository root. CI fails while a copy differs.
2. **Links inside the core** point only to other core files and to the SKILL.md sections both skills keep (§ Read Plans, § Source Frameworks). Everything else is named by its subject — what execution asks, what extraction reads — so the same text holds in both skills.
3. **A lane guide here may link into the core**, never into a `uipath-genome` file: a build-side rule is named by its subject ("`uipath-genome`'s split questions").
4. **The genome owners own** the genome lanes, the core copies and the genome-writing tests; the planner owners own the SDD lanes (`CODEOWNERS`).
