---
name: uipath-genome-builder
description: "UiPath genome builder: EXECUTE an existing automation genome (`*-genome.md`) — build, implement, or run the migration or refactor it describes. Write, draft, author, edit, extract or document a genome, or turn an idea/SOP/PDD/SDD into one→uipath-planner (it writes every genome; never write or change one here). Builds a component or process genome — the coding-agent spec uipath-planner writes — through the owning skills, invoked before any skill it names: configuration questions, build, a verdict per acceptance criterion, open items and cutover. A genome extracted from a UiPath project or another framework's export builds as a refactor or migration: UI targets and test data migrated, characterization tests, run modes, comparison. Triggers: 'build/execute/implement this genome', 'build from the blueprint', 'run the migration from this genome', 'execute the refactor'. Build without a genome→that artifact's skill. Legacy activity upgrade→uipath-activity-migrator. Quality review→uipath-review."
when_to_use: "User points at an existing *-genome.md file (or one whose first line is `<!-- UIPATH-AUTOMATION-GENOME`) and asks to build, execute, implement or follow it, or uipath-planner hands over a genome it wrote for a build, a migration or a refactor. Not for writing, drafting or editing a genome — that is uipath-planner."
---

# UiPath Genome Builder — build automations from their genome

Genome: markdown specification an AI agent consumes to build or rebuild an automation — what it does, business rules, data moving between parts, platform resources, its transactional shape, verification, and which UiPath skill builds each part. **`uipath-planner` writes every genome** (Author, Extract, Edit); this skill **builds** from it (Execute), verifies it and hands it off. Genomes stay thin: build skills carry UiPath know-how; a genome describes *what*, skills know *how*.

> **Execute reads by plan, never from memory.** Its first read is [read-plan-guide.md](references/read-plan-guide.md), whole: it names every other guide, the phase and condition that open it, and how each is read. This file only routes.

## When to Use This Skill

- `*-genome.md` file to build from — authored from an idea, a PDD, a TO-BE or an SDD, or extracted from an existing automation
- A genome extracted from a UiPath source to execute as a refactor, or from another framework's export as a migration
- A genome `uipath-planner` hands over once it is written

## Mode Detection

Rows are checked in order; the first that matches decides.

1. **A request that writes or changes a genome → invoke `uipath-planner` with the request, then stop.** Writing or changing a genome is `uipath-planner`'s, never this skill's: authoring one from an idea, a description, an SOP, a PDD, a TO-BE or an SDD; proposing scenarios for a goal; extracting one from a UiPath project or solution or another framework's export (documentation, estate assessment, the first step of a refactor or migration); editing one, partial re-extraction included. This holds even when the request asks for the file to be edited directly or names the exact change: make no change to the genome file here, and read no guide of this skill for it. Once `uipath-planner` has written the genome, a build of it is row 2. When `uipath-planner` is not installed, say that writing the genome needs it and stop.
2. **`*-genome.md` path plus build intent** ("build", "execute", "implement", "follow") → **Execute**. Read [read-plan-guide.md](references/read-plan-guide.md) whole, then the start reads it names. Executing a genome extracted from a UiPath source is a refactor, and so is executing one from another framework when the request asks for a refactor.
3. **A request to refactor or migrate an automation with no genome yet** → `uipath-planner` extracts first (row 1), then Execute here. An upgrade of a Windows-Legacy project's activities in place stays `uipath-activity-migrator`'s.

A request to design a solution and derive tasks, or any input this list assigns to another skill, is that skill's job. Say so and stop.

## Critical Rules

Each rule names its subject and the one guide that states it in full; the guide's wording is the rule.

1. **Execution never edits the genome and never skips the configuration questions** — waived only by an explicit "take the defaults" in the current request — then advances group by group without pausing, assesses every acceptance criterion, and writes the open-items files when the target environment needs setup — [execution-guide.md](references/execution-guide.md) § 1.3, § 2.2, § 3; [open-items-guide.md](references/open-items-guide.md). A spec fix is a `uipath-planner` edit, followed by re-execution.
2. **What the genome's SDD already decided is answered, not asked**: the split and queue design, the implementation mode, the package pins, the refactor answers — [execution-guide.md § 1.1](references/execution-guide.md).
3. **A genome missing a required section, or failing the checker, is malformed**: report it and send it back to `uipath-planner` — [execution-guide.md § 1.1](references/execution-guide.md); `scripts/check-genome.py`.
4. **Execution on an extracted genome is a migration by default**: catalogs derived from the export at preflight, UI targets and test data migrated from them, no secret ever copied — [source-migration-guide.md](references/source-migration-guide.md).
5. **Build through the owning skill, verifiably**: its mandatory reads, and for every activity kind the default XAML and the package's per-activity doc before the first file using it is written; workflows authored as files, never generated — [execution-guide.md § 2.2](references/execution-guide.md).
6. **Composite source actions are contracts in the genome and patterns at build** — [genome-reading-guide.md](references/genome-reading-guide.md) § Sections, Workflow; [ui-target-migration-guide.md § Composite interactions](references/ui-target-migration-guide.md).
7. **UiPath selector truth lives in one guide** — [selector-translation-guide.md](references/selector-translation-guide.md) rules 1–16, with what its technology guides add to them. **Verification is a property of the acting activity**, except a test project's checkpoints — [ui-verification-guide.md](references/ui-verification-guide.md).
8. **A migrated target carries a verdict — `verified`, `shape-verified` or `offline-unverified` —** and a reachable application is a windfall, never a precondition for finishing the run — [ui-target-migration-guide.md § Verifying targets](references/ui-target-migration-guide.md).
9. **Most source steps are not UI activities**, and linking is the last thing done to a workflow file — [source-migration-guide.md § Source steps that are not UI actions](references/source-migration-guide.md); [ui-target-migration-guide.md § UI targets](references/ui-target-migration-guide.md).
10. **The transactional shape is described in the genome and split at build**: execution asks the split questions per flow, unless the SDD recorded the split, and the behaviour is owed whatever the choice — [genome-reading-guide.md](references/genome-reading-guide.md) § Transactional Shape; [transactional-execution-guide.md](references/transactional-execution-guide.md).
11. **Source values are read from the source, not from its rendering**, and execution follows the source where it and the genome disagree — [genome-reading-guide.md](references/genome-reading-guide.md) § Source Map, source values.
12. **Executing a genome extracted from a UiPath source is a refactor**, and so is a migration whose request asks for one: every component re-authored on the target its shape fits, the genome the contract, every changed output a plan row with its reason, characterization tests before the logic — [refactor-guide.md](references/refactor-guide.md). **A UiPath source's deployed state is source**: the binding a process overrides is the value that runs — [genome-reading-guide.md](references/genome-reading-guide.md) § UiPath Source.
13. **Nothing reaches a tenant unasked**: the build stops at the pack dry run, never writes to a tenant the user did not name, and a build that replaces a running automation ends its open items with the cutover — [open-items-guide.md](references/open-items-guide.md); [refactor-guide.md § Done](references/refactor-guide.md).

## Anti-patterns

1. **Writing, extracting or editing a genome here — including a direct edit the user names.** That is `uipath-planner`'s Author, Extract and Edit lanes (§ Mode Detection row 1); an in-place activity upgrade of a Legacy project is `uipath-activity-migrator`'s.
2. **Editing the genome to make a build pass.** The genome is read-only at execution; the gap goes into the report and back to `uipath-planner` (Critical Rule 1).
