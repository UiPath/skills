# Genome From SDD Guide — the genome of an agreed SDD

`author` reads this guide when the input is an agreed SDD (`## Planner Handoff` with `Status: ready`): inside `design`, on the turn after the SDD is `ready` ([sdd-writing-guide.md](sdd-writing-guide.md) § Step 3), or when a request hands over an agreed SDD. The SDD decided the architecture; the genome restates it as the coding-agent spec and adds what only the genome holds (replication-grade substeps, composite UI contracts, the configuration questions, numbered acceptance criteria).

## Read Plan

These rows add to the rows of [author-guide.md § Read Plan](author-guide.md) that hold for every input.

| Phase | Condition | Read |
|---|---|---|
| the input is received | — | this guide whole; the SDD whole, with every child SDD a solution root lists; [skill-mapping-guide.md](skill-mapping-guide.md) § Rules, § Build Skills and § Platform Dependencies (not Build With) only — never § Decision Tree for Ambiguous Steps or § Common Combinations, because the SDD placed every project's skill. Nothing else: product-selection-guide.md, platform-availability-guide.md and pdd-analysis-guide.md stay closed, because the SDD decided what they decide |
| the input is received | the SDD has a queue or a per-item loop | [transactional-shape-guide.md](transactional-shape-guide.md) § Layout and, under § Rules, § Applicability and roles, § Item store, § Outcomes, step groups, configuration and traceability and § Split options and evidence; § Levels when the genome is a process genome; § Flows and levels of items when the SDD hands items on from one stage to the next or its items nest |
| the genome is written (item 7) | — | [genome-format-guide.md § Design Links](genome-format-guide.md) |

## Author from an agreed SDD

1. **Read the SDD whole**, with its Planner Handoff, and for a solution SDD (the root `*-solution-sdd.md`) every child SDD it lists. Then stop without writing when either holds:
   - **The SDD handed over is a Case Management SDD** — its Planner Handoff has a `Build handoff` row instead of `Tasks file`. It never becomes a genome: say that `uipath-maestro-case` builds from the SDD itself. A Case Management child of a solution SDD does not stop the genome; it is one component (item 3).
   - **A `draft` SDD** — `Status: draft`, with blocking SME items. Name the blocking items; the genome is written once the SDD is `ready`.
2. **Read `Execution autonomy` from the Planner Handoff.** It decides how the genome is finished:
   - **`autonomous`** — no follow-up rounds ([author-guide.md](author-guide.md) Step 6): every gap is written with `*[Inferred]*`, or carried as a Configuration Question with its default. After the check ([author-guide.md](author-guide.md) Step 8), the edits are offered in the closing summary, and the run does not wait for them.
   - **`interactive`, or no row** — [author-guide.md](author-guide.md) Steps 6 and 8 as written.
3. **The SDD's products and projects are the genome's.** Its project list sets the level ([author-guide.md](author-guide.md) Step 2) and the Build With / Components rows; Steps 3–5 never re-select a product the SDD placed. Its delivery model holds for every row. Two projects that are the producer and the consumer of one flow — a dispatcher that adds items to a queue and a performer that works them — are one `uipath-rpa` component: they are the split the SDD chose for that flow ([skill-mapping-guide.md](skill-mapping-guide.md) rule 3), recorded as item 4 states, never two components.
   - **A child SDD that is a Case Management SDD** (its handoff has `Build handoff` instead of `Tasks file`) is one component whose Build With is `uipath-maestro-case`. Its Interface names that child SDD's path, relative to the genome, as the component's build input: `uipath-genome-builder` hands that SDD to `uipath-maestro-case`, which builds the case from it. The component genome restates the case as the child SDD designed it and never redesigns it.
4. **The SDD's decisions are recorded, not reopened.** The split and queue design, the implementation mode, the package pins and, for a refactor, the refactor answers go into the sections that hold them (Transactional Shape evidence, Deployment, Configuration Questions defaults), so `uipath-genome-builder` reads them as answered.
5. **Gaps carry over, marker and all.** Every `[SME REVIEW]` or `[DEFAULT]` item of the SDD that touches a section is written in that section as `*[Inferred]*` followed by the item's text with its marker verbatim — `*[Inferred]* (SDD [SME REVIEW]: <note>)`, `*[Inferred]* (SDD [DEFAULT]: <note>)`. [author-guide.md](author-guide.md) Step 6 asks nothing the SDD already left to an SME.
6. **Apart from the `Genome` handoff row (item 7), the SDD is never edited.** A contradiction between the SDD and what the genome needs is named when edits are offered ([author-guide.md](author-guide.md) Step 8).
7. **Name the genome after the SDD and record it in one handoff.**
   - **A single-product SDD:** `<PROCESS_NAME_KEBAB>-genome.md` beside the SDD.
   - **A solution SDD** (a root `<SOLUTION_NAME_KEBAB>-solution-sdd.md` and its child SDDs): ONE genome for the whole solution, named after the root — `<SOLUTION_NAME_KEBAB>-genome.md` beside the root SDD. It is a process genome with its component genomes in `<SOLUTION_NAME_KEBAB>-genome/` when Step 2 counts two or more projects, and a component genome otherwise ([genome-format-guide.md § File Naming and Location](genome-format-guide.md)). Never write one genome per child SDD.

   Write the `Designed in:` line, linking the SDD the genome is named after ([genome-format-guide.md § Design Links](genome-format-guide.md)), and record the genome as `| **Genome** | <path> |` after `Tasks file` in that SDD's Planner Handoff — for a solution, the ROOT SDD's handoff only; the child SDDs are not edited.
8. **The genome write is a turn boundary.** What follows it: [sdd-writing-guide.md](sdd-writing-guide.md) § Step 3 item 4 when `design` ran; otherwise [SKILL.md](../SKILL.md) § Chaining.

Continue at [author-guide.md](author-guide.md) Step 2.
