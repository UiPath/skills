---
name: uipath-genome
description: "UiPath genome builder: always invoke FIRST to build, execute, implement or follow an EXISTING `*-genome.md`, or run the migration or refactor it describes — before reading the file or loading any skill it names — through the owning skills. Configuration questions, a build per component through its skill, a verdict per acceptance criterion, open items and cutover; a genome extracted from a UiPath project is a refactor, one from another framework's export a migration (UI targets and test data migrated, characterization tests, run modes, comparison). Write, draft, author, edit, extract or document a genome, or turn an idea, SOP, PDD or SDD into one→uipath-planner (it writes every genome; never write or change one here); check or validate a genome→uipath-planner. Build without a genome→that artifact's skill. Legacy activity upgrade in place→uipath-activity-migrator. Quality review→uipath-review."
when_to_use: "User points at an existing *-genome.md (or a file whose first line is `<!-- UIPATH-AUTOMATION-GENOME`) and asks to build, execute, implement or follow it; or uipath-planner hands over a genome it wrote for a build, a migration or a refactor. Not for writing, drafting, editing, checking or validating a genome — that is uipath-planner."
argument-hint: "[build] <genome.md>"
user-invocable: true
---

# UiPath Genome — build automations from their genome

One verb. A genome is the markdown specification of an automation — what it does, its business rules, the data between its parts, platform resources, transactional shape, verification, and the skill that builds each part. `uipath-planner` writes every genome; this skill builds it. The genome says *what*; the owning skills know *how*.

## Setup

1. **Read the genome whole** and take from it the facts the read plans branch on. Each guide names a fact as written here:
   - **Level** — the first-line marker `<!-- UIPATH-AUTOMATION-GENOME: component|process`. A file without the marker is not a genome: say `uipath-planner` writes genomes, and stop.
   - **Component genomes** — a process genome's Components table links; a library component is the one whose Type cell says library.
   - **Extracted** — the genome has a `## Source Map` that is not the stub. **Source framework** — the Source Map's `Source framework` row; a component genome with a `Part of:` line takes it from its process genome. **Build mode** — not extracted: a build; extracted from a UiPath source: a refactor; from another framework: a migration. An extracted genome whose row names no framework: ask the user which framework the source is.
   - **Transactional** — the Transactional Shape is not the stub.
   - **Test components** — a Components Type cell reading "Test-case group…", or `Test case:` steps.
   - **Packaging** — the process genome's Deployment Packaging line.
   - **Designed** — the genome carries a `Designed in:` line; the build reads no SDD for it.
2. **Open the verb's guide** and read it whole; its § Read Plan names every other file the verb reads and when. Never work from memory of a guide.

## Verbs

| Verb | Input | Output | Guide |
|---|---|---|---|
| `build` | A `*-genome.md` | The projects, built through their owning skills, and the hand-off folder | [build-guide.md](references/build-guide.md) |

## Choosing the Verb

Checked in order; the first match decides.

1. **A request that writes or changes a genome → invoke `uipath-planner` with the request, then stop.** Authoring one from an idea, a description, an SOP, a PDD, a TO-BE or an SDD; proposing scenarios for a goal; extracting one from a UiPath project or solution or another framework's export; editing one, partial re-extraction and applying the answers of its pre-build file included — even when the request names the exact change. Make no change to the genome file here. When `uipath-planner` is not installed, say that writing or changing the genome needs it and stop.
2. **The user named a verb** → that verb.
3. **A genome plus build intent** ("build", "execute", "implement", "follow", "run the migration", "execute the refactor") → `build`. A genome extracted from a UiPath source builds as a refactor; one from another framework as a migration, or a refactor when the request asks for one.
4. **Check or validate a genome → invoke `uipath-planner` with the request, then stop.**
5. **A refactor or migration with no genome yet** → `uipath-planner` extracts it first (item 1), then `build` here. An upgrade of a Windows-Legacy project's activities in place is `uipath-activity-migrator`'s.

Any other input is another skill's job: say which, and stop.

## Critical Rules

Each rule names its subject and the guide that states it in full; [build-guide.md § Verb Rules](references/build-guide.md) holds the rest.

1. **Choose the verb first** (§ Choosing the Verb) and run § Setup before anything else.
2. **The build never edits the genome** — not even a one-line fix the user names. A gap in the genome goes into the report and back to `uipath-planner` as an edit, then the build runs again.
3. **Never skip the configuration questions** — [build-guide.md](references/build-guide.md) rules 1–2.
4. **Build through the owning skill, verifiably** — [build-guide.md](references/build-guide.md) rule 4.
5. **Nothing reaches a tenant that no answer allowed** — [build-guide.md](references/build-guide.md) rule 12.

## Anti-patterns

1. **Writing, extracting or editing a genome here — including a direct edit the user names.** That is `uipath-planner` (§ Choosing the Verb item 1).
2. **Editing the genome to make a build pass** (Critical Rule 2).
