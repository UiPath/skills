---
name: uipath-genome-builder
description: "UiPath genome builder (`*-genome.md`): always invoke to build a genome file, before any skill it names. BUILD, implement or run the migration or refactor a genome describes through the owning skills; CHECK or validate one (the same gate a build runs first). Configuration questions, a build per component through its skill, a verdict per acceptance criterion, open items and cutover; a genome extracted from a UiPath project is a refactor, one from another framework's export a migration (UI targets and test data migrated, characterization tests, run modes, comparison). Write, draft, author, edit, extract or document a genome, or turn an idea, SOP, PDD or SDD into one→uipath-planner (it writes every genome; never write or change one here). Build without a genome→that artifact's skill. Legacy activity upgrade in place→uipath-activity-migrator. Quality review→uipath-review."
when_to_use: "User points at an existing *-genome.md (or a file whose first line is `<!-- UIPATH-AUTOMATION-GENOME`) and asks to build, execute, implement or follow it, or to check or validate it; or uipath-planner hands over a genome it wrote for a build, a migration or a refactor. A genome whose preamble names `uipath-genome` (written before the skill split) builds here too. Not for writing, drafting or editing a genome — that is uipath-planner."
argument-hint: "[build | check] <genome.md>"
user-invocable: true
---

# UiPath Genome Builder — build automations from their genome

Two verbs. A genome is the markdown specification of an automation — what it does, its business rules, the data between its parts, platform resources, transactional shape, verification, and the skill that builds each part. `uipath-planner` writes every genome; this skill builds it and never changes it. The genome says *what*; the owning skills know *how*.

## Setup

1. **Read the genome's facts once:** `node "<SKILL_DIR>/scripts/check-genome.mjs" context "<GENOME_MD>"`. `<SKILL_DIR>` is the folder holding this file. Its JSON fields are: `level` (`component` | `process`, from the genome marker), `components` (a process genome's linked component genomes, each `{path, library}`), `test_components` and `independent_packages` (true, false or null, from the Deployment section's Packaging line), `extracted`, `source_framework`, `build_mode` (`build` | `refactor` | `migration` | `unknown` — `unknown` is an extracted genome whose framework was not found: read the Source Map's `Source framework` row, or ask the user which framework the source is when the row names none), `transactional`, `designed_in` (the path of the SDD the `Designed in:` line links) and `check` (the strict check: `ok` and `errors`). Never re-derive a field it emits from the genome's prose, and never run the checker again for them; a read-plan condition no field answers is read from the genome section the read plan names. A `check` that is not ok is a result for the verb to act on, not a failed call. When `node` is missing or the call fails, say "Context loading did not run; I'll read the genome directly", then read its first line and sections and continue.
2. **Open the verb's guide** and read it whole; its § Read Plan names every other file the verb reads and when. Never work from memory of a guide.

## Verbs

| Verb | Input | Output | Guide |
|---|---|---|---|
| `build` | A `*-genome.md` | The projects, built through their owning skills, and the hand-off folder | [build-guide.md](references/build-guide.md) |
| `check` | A `*-genome.md` | The checker's verdict | § Check |

## Choosing the Verb

Checked in order; the first match decides.

1. **A request that writes or changes a genome → invoke `uipath-planner` with the request, then stop.** Authoring one from an idea, a description, an SOP, a PDD, a TO-BE or an SDD; proposing scenarios for a goal; extracting one from a UiPath project or solution or another framework's export; editing one, partial re-extraction included — even when the request names the exact change. Make no change to the genome file here. When `uipath-planner` is not installed, say that writing or changing the genome needs it and stop.
2. **The user named a verb** → that verb.
3. **A genome plus build intent** ("build", "execute", "implement", "follow", "run the migration", "execute the refactor") → `build`. A genome extracted from a UiPath source builds as a refactor; one from another framework as a migration, or a refactor when the request asks for one.
4. **A genome to check or validate** → `check`.
5. **A refactor or migration with no genome yet** → `uipath-planner` extracts it first (item 1), then `build` here. An upgrade of a Windows-Legacy project's activities in place is `uipath-activity-migrator`'s.

Any other input is another skill's job: say which, and stop.

## Check

```bash
node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict
```

`build` runs it through `context` before it asks anything and sorts its findings into blocking ones and report items ([build-guide.md § Start](references/build-guide.md)). Exit 0 passes; exit 1 prints one `FAIL:` line per finding — `check` reports each finding as an edit for `uipath-planner` and stops, never fixing the genome; exit 2 is a usage error. A hand-run check whose level argument is not the level the first-line marker names reports the marker as missing: run it again with the marker's level — that `FAIL` is not a genome finding. What it checks: the script's header comment.

## Critical Rules

Each rule names its subject and the guide that states it in full; [build-guide.md § Verb Rules](references/build-guide.md) holds the rest.

1. **Choose the verb first** (§ Choosing the Verb) and run § Setup before anything else.
2. **The build never edits the genome** — not even a one-line fix the user names. A gap in the genome goes into the report and back to `uipath-planner` as an edit, then the build runs again.
3. **Never skip the configuration questions** — [build-guide.md](references/build-guide.md) rules 1–2.
4. **Build through the owning skill, verifiably** — [build-guide.md](references/build-guide.md) rule 4.
5. **Nothing reaches a tenant unasked** — [build-guide.md](references/build-guide.md) rule 12.

## Anti-patterns

1. **Writing, extracting or editing a genome here — including a direct edit the user names.** That is `uipath-planner` (§ Choosing the Verb item 1).
2. **Editing the genome to make a build pass.** The genome is read-only at build; the gap goes into the report and back to `uipath-planner`.
