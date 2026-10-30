---
name: uipath-planner
description: "UiPath solution planner, designer and genome writer. Always invoke for PDD / SDD files (`pdd.md`, `*-sdd.md`) and any `*-genome.md` to write or change. design: PDD or process source (SOP, transcript, .bpmn as design input)→SDD + genome. plan: SDD→per-skill tasks. decompose: multi-project request→plan. author / extract / edit: genome from an idea or SDD, from a UiPath project or solution (.xaml/.cs, .flow, .bpmn, agent.json, caseplan, .uipx) to document, refactor or migrate, or from another framework's export. Sole case-SDD author. Build from a genome→uipath-genome-builder. `.uipx` lifecycle→uipath-solution. Orchestrator/IS/auth→uipath-platform. Building .xaml/.cs→uipath-rpa; .flow→uipath-maestro-flow; .bpmn→uipath-maestro-bpmn; agent.json/.py→uipath-agents; caseplan.json→uipath-maestro-case. In-place Legacy activity upgrade→uipath-activity-migrator. Quality review→uipath-review."
when_to_use: "A PDD/SDD or another process source; 'generate an SDD', 'analyze this PDD', 'design/architect a UiPath solution'; 'propose a workshop/demo scenario'; document, reverse-engineer, extract a spec from, refactor or migrate an existing project (extract first); a request spanning separate buildable projects; ambiguous 'what should I build'. A PDD always routes here, even for one RPA process — never hand a raw PDD to a specialist. Skip only with no PDD, SDD, genome or existing automation to document, and one project (inline HITL/script/connector nodes count as one). Flow calling only deployed processes→uipath-maestro-flow."
argument-hint: "[design | plan | decompose | author | extract | edit | check] [target]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, AskUserQuestion, Agent, Skill, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# UiPath Planner — design, plan and genome-writing verbs

One skill, seven verbs. It writes the documents — the SDD, the plan and the genome; `uipath-genome-builder` builds from the genome. The user names a verb (`/uipath-planner author invoice-sdd.md`) or the request implies one (§ Choosing the Verb). This file routes and holds the rules every verb shares; each verb's guide holds its procedure, its own rules and its read plan, and opens only when the verb runs.

## Setup

1. **A genome is in play** (a path given, or one this run wrote) **and the verb is `author`, `extract`, `edit` or `check`**: run `node "<SKILL_DIR>/scripts/check-genome.mjs" context "<GENOME_MD>"` once. `<SKILL_DIR>` is the folder holding this file. Its JSON — `level`, `extracted`, `source_framework`, `build_mode` (`build` | `refactor` | `migration` | `unknown`), `transactional`, `designed_in` (resolved path), `components` (each `{path, library}`), `test_components`, `independent_packages`, `check` — answers every read-plan condition about the genome; never re-derive them from its prose. A `check` that is not ok is a result, not a failed call. When `node` is missing or the call fails, say "Context loading did not run; I'll read the genome directly", then read its first line and sections and continue. A genome handed on for a build skips this step: `uipath-genome-builder` runs it.
2. **Open the verb's guide** (§ Verbs) and read it whole. Its § Read Plan names every other file the verb reads, the phase that opens it and the condition that must hold; a file no condition reached stays closed. A file the plan reads whole is read whole — not grepped or skimmed; a pointer that names a section (`guide.md § Section`) is a read of that whole section; a catalog file (a framework selectors guide) is read by its heading list, then by the sections in play. Never work from memory of a guide.
3. **A Case Management design signal (§ Choosing the Verb item 3) opens [case-design-guide.md](references/case/case-design-guide.md) only** — never design-guide.md or sdd-writing-guide.md. A PDD whose Level 1 scope comes out as Case Management stays in design-guide.md, which states what that path reads.

## Verbs

| Verb | Input | Output | Guide |
|---|---|---|---|
| `design` | A PDD or any process-knowledge source, or "design / architect this" | SDD markdown (`*-sdd.md`) with the `## Planner Handoff` header, then the genome of the agreed design (`author`, [genome-from-sdd-guide.md](references/genome-from-sdd-guide.md)) | [design-guide.md](references/design-guide.md), then [sdd-writing-guide.md](references/sdd-writing-guide.md) for Phase 3 |
| `design` — Case Management | A case design request, a build handoff from `uipath-maestro-case`, or a case draft to finalize | Case SDD (`sdd.md`); never a genome | [case-design-guide.md](references/case/case-design-guide.md) |
<!--skill-flavor:plan-job:start-->
| `plan` | An SDD with the `## Planner Handoff` header or the `<!-- planner-handoff:v1 -->` marker | `<process>-tasks.md` and live `TaskCreate` tasks routed to the specialists | [plan-guide.md](references/plan-guide.md) |
| `decompose` | A request spanning separate buildable projects, with no SDD | A dated plan and live `TaskCreate` tasks | [decompose-guide.md](references/decompose-guide.md) |
<!--skill-flavor:plan-job:end-->
| `author` | An idea, description, SOP, transcript, PDD, TO-BE or agreed SDD, when a genome or blueprint is asked for; an agreed SDD `design` just wrote; a workshop or demo goal that needs a scenario | `*-genome.md` | [author-guide.md](references/author-guide.md) |
| `extract` | A UiPath project or solution with its deployed state, or another automation or test framework's export | `*-genome.md` with its Source Map | [extract-guide.md](references/extract-guide.md) |
| `edit` | A `*-genome.md` and a change: add, split, remove, re-extract what changed | The same genome, edited in place | [edit-guide.md](references/edit-guide.md) |
| *build* | A `*-genome.md` | Not this skill: hand the genome path to `uipath-genome-builder` | — |
| `check` | A `*-genome.md` | The checker's verdict | § Check |

## Choosing the Verb

Checked in order; the first match decides. Do not pattern-match on a filename or extension alone: the first-line genome marker, the `## Planner Handoff` heading and the `<!-- planner-handoff:v1 -->` marker are the load-bearing signals.

1. **The user named a verb** → that verb.
2. **A genome** — a `*-genome.md`, or a file whose first line is `<!-- UIPATH-AUTOMATION-GENOME` — to build, execute, implement or follow → `uipath-genome-builder`: invoke that skill with the genome path, then stop; to change, split or re-extract → `edit`; to check or validate → `uipath-genome-builder` when it is installed, otherwise `check`. This skill's own `check` runs after every genome write (§ Check).
3. **A Case Management design signal** — a build request `uipath-maestro-case` handed back because its design input is missing, a case design request with no PDD, or a case design draft to finalize → `design`, through [case-design-guide.md](references/case/case-design-guide.md).
4. **An existing automation** — a UiPath project or solution, or another framework's export — to document, reverse-engineer, size or blueprint → `extract`; to refactor or migrate → `extract`, then `uipath-genome-builder` (§ Chaining). A Windows-Legacy project whose activities are upgraded in place → `uipath-activity-migrator`.
5. **A genome or blueprint asked for** from a description, an SOP, a transcript, a PDD, a TO-BE or an SDD (not a Case Management SDD: `uipath-maestro-case` builds from it), or an explicit workshop, demo or scenario request ("propose a demo scenario with X") → `author`. An explicit genome request outranks Critical Rule 4's PDD → SDD default.
6. **A document path** → read its first ~50 lines. The `## Planner Handoff` heading or the `<!-- planner-handoff:v1 -->` marker (either alone suffices) → `plan`. A PDD or any process-knowledge source — steps, applications and exceptions in a PDD, Confluence page, BPMN model, meeting transcript, SOP or requirements doc, or a `.pdf` / `.docx` the user calls a PDD → `design`; a less structured source still goes to `design`, with heavier elicitation. Anything else → ask once with `AskUserQuestion`: *PDD → `design`*, *SDD → `plan`* (an SDD with no handoff header runs on the defaults [plan-guide.md](references/plan-guide.md) Step 1 states), *other context → `decompose`*, reading the document as its context.
7. **No document** → explicit design language ("design this", "architect this", "generate an SDD"), or a process described inline with enough detail to stand in for a PDD (process steps + applications + exceptions) → `design`. A design request thin on detail still goes to `design`, which elicits what is missing through `AskUserQuestion` in Phase 1 rather than degrading to a `decompose` plan. Otherwise → `decompose`: a request spanning separate buildable projects, or one still ambiguous after detection ("what should I build?", "automate our invoice handling, not sure with what") — its Step 2 exits single-project requests to the specialist.
8. **One project one specialist owns end to end, with no PDD, SDD or genome** → not this skill: load that specialist directly. A Flow with script nodes, an inline HITL step and its own solution wrapper is one `uipath-maestro-flow` project — inline nodes and solution scaffolding are steps the specialist performs, never separate skills to orchestrate. Counting them as skills and writing a plan is the most common mis-trigger.

## Chaining

A verb hands its output to the next one only along these edges:

- **`design` → `author` → `plan`.** `design` writes the SDD; the SDD write ends the turn. Once the SDD is `Status: ready`, the next turn runs `author` on it ([genome-from-sdd-guide.md](references/genome-from-sdd-guide.md)): the genome is written beside the SDD and the handoff gains its `Genome` row; that write ends the turn too. `plan` then runs on the next turn when the request's intent is to build ("create / build / implement / set up"); a request only to design stops after the genome. A `draft` SDD gets no genome until it flips to `ready`. Steps and exceptions: [sdd-writing-guide.md](references/sdd-writing-guide.md) Step 3.
- **A Case Management SDD never becomes a genome**: `uipath-maestro-case` builds from the SDD.
- **`extract` → `uipath-genome-builder`** for a refactor or migration request, in the same session, once the user's edits are in; an unattended run hands the genome over without asking.
- **`uipath-genome-builder` → `edit` → `uipath-genome-builder`.** A gap the build finds in the genome comes back here as an `edit`, then the build runs again; the builder never changes the genome.
- **`uipath-genome-builder` not installed** (it is absent from the session's list of available skills) → the genome verbs still write and check genomes, and `design` still writes the genome; say that the build needs `uipath-genome-builder`, and `plan` derives per-skill tasks from the SDD.

## Check

```bash
node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict
```

`author`, `extract` and `edit` run it after every write; `uipath-genome-builder` runs the same checker before it asks anything. Exit 0 passes; exit 1 prints one `FAIL:` line per finding — repair each with an `edit` and run it again; exit 2 is a usage error. What it checks: the script's header comment. Without `node`, review the genome against [genome-format-guide.md](references/genome-format-guide.md) by hand and say the check did not run.

## Critical Rules

Every verb obeys these; each verb's guide adds its own under § Verb Rules.

<!--skill-flavor:plan-design-only-outputs:start-->
1. **Plan, design and specify — never author automation code yourself.** `design`, `plan`, `decompose`, `author`, `extract` and `edit` write only SDD, plan/tasks and genome markdown, plus live `TaskCreate` calls; they NEVER write XAML, C#, Python, JSON, or project or scaffold files. Implementation always routes to a specialist, and every genome build to `uipath-genome-builder`.
<!--skill-flavor:plan-design-only-outputs:end-->
2. **Choose the verb first** (§ Choosing the Verb) and run § Setup, before anything else.
3. **One writer, one builder, one handoff.** `author`, `extract` and `edit` write and check every genome; `uipath-genome-builder` builds every genome and never changes one — not even a one-line fix the user names. The genome file is the only thing that passes between them.
4. **The output follows the input.** A PDD or process source gets an **SDD, then the genome of the agreed SDD** (§ Chaining); a Case Management design gets a case SDD and never a genome; a genome or blueprint request, a refactor or a migration gets a **genome**; a Word ASDD is the SDD converted ([sdd-writing-guide.md](references/sdd-writing-guide.md) Step 2.5); a **PDD** is never written — it is input only.
5. **Route — do not redescribe.** An SDD, a plan and a genome say WHICH skill builds each part and IN WHAT ORDER. They never describe a specialist's internal flow (target configuration, Object Repository registration, XAML pipelines, scaffolding, pack/publish, HITL field or outcome schema, auth, testing procedures). For a HITL step, pass business intent only ("manager approves or rejects an expense; can add a reason if rejected") — the HITL specialist chooses the schema.
6. **Fill gaps with markers — never silently invent business rules.** SDDs and plans use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts) and `[SME REVIEW]` for business-knowledge gaps; resolve `[SME REVIEW]` items with the user before finalizing — they gate the `Status: ready` flip, not the skeleton write. Genomes use the best interpretation plus `*[Inferred]*` ([genome-format-guide.md § Ambiguity Marker](references/genome-format-guide.md)). For an Agent or Coded App gap, ask with `AskUserQuestion` (proceed with gap filling, or a different product) — never fall back on your own.
    - **These tokens are the entire gap vocabulary, and their exact string is load-bearing.** The `Action Required — SME Review Items` block, the gap counts, the `Status: ready` flip, `plan`'s assumption carry-over and every reviewer grepping the file find the items by exact match on `[SME REVIEW]` / `[DEFAULT]`.
    - **Write the marker verbatim, with nothing else inside the brackets.** The note goes *after* the closing bracket: `| UiPath version | [SME REVIEW] not recorded in the PDD |`. Never fold the note inside (`[SME REVIEW — not recorded]`) and never substitute another word (`[PLACEHOLDER]`, `[TBD]`, `[TODO]`, `<fill in>`, `N/A`, prose like "to be confirmed"). A decorated or renamed marker is invisible to every consumer above — the gap silently disappears.
    - **When you map or copy content out of another document** (a source SDD into a client template, a PDD into an SDD, one SDD section into another), **carry its markers through byte-for-byte.** Re-wording a marker you did not author destroys a gap someone else recorded. Add new markers for the gaps *you* find; never edit the ones already there.
7. **Never invent selectors or UI targets.** Selectors need the application inspected at development time; an SDD, a plan and an authored genome leave them to the specialist. A target carried over from the source is not invented: `extract` records the source's targets in the Source Map, and `uipath-genome-builder` migrates them at build.
8. **Gate every product by the platform.** The delivery model (Automation Cloud, Automation Suite, standalone Orchestrator) blocks unavailable products through [platform-availability-guide.md](references/platform-availability-guide.md), in every verb that chooses a product (`design`, `decompose`, `author` without an SDD); a product the user excluded is never offered again in the session.
9. **Prompt budget.** `design` runs its own checkpoint model ([design-guide.md](references/design-guide.md)); `plan` and `decompose` each cap at **5 `AskUserQuestion` calls**. Ask execution autonomy **exactly once**, at `design` entry, and write it into the handoff header; `author` on an SDD and `plan` read it and never ask again. Scope and UI answers resolved in `design` flow forward through the SDD.
10. **Sole author of Case Management SDDs.** Every case design runs under [design-guide.md](references/design-guide.md) Verb Rule 7: a case design signal through [case-design-guide.md](references/case/case-design-guide.md) and its three-file reading set, opened with the Read tool, never `cat`; a PDD whose Level 1 scope is Case through design-guide.md's case rows.

## Reference Navigation

| Verb | Guides it may read (its § Read Plan decides when) |
|---|---|
| `design` | [design-guide.md](references/design-guide.md), [sdd-writing-guide.md](references/sdd-writing-guide.md), [pdd-analysis-guide.md](references/pdd-analysis-guide.md), [product-selection-guide.md](references/product-selection-guide.md), [platform-availability-guide.md](references/platform-availability-guide.md), [rpa-product-guide.md](references/rpa-product-guide.md), [business-rules-guide.md](references/business-rules-guide.md), [package-selection-guide.md](references/package-selection-guide.md), [tenant-library-search-guide.md](references/tenant-library-search-guide.md), [attended-reauth-pattern-guide.md](references/attended-reauth-pattern-guide.md), [asdd-crosswalk-guide.md](references/asdd-crosswalk-guide.md); the SDD templates in `assets/templates/` |
| `design` — Case Management | [case-design-guide.md](references/case/case-design-guide.md), [case-design-layers-guide.md](references/case/case-design-layers-guide.md), the case SDD template |
| `plan`, `decompose` | [plan-guide.md](references/plan-guide.md), [decompose-guide.md](references/decompose-guide.md), [multi-skill-patterns-guide.md](references/multi-skill-patterns-guide.md), [skill-capability-map-guide.md](references/skill-capability-map-guide.md) |
<!--skill-flavor:plan-and-tasks-format-row:start-->
| `plan`, `decompose`: format | [plan-and-tasks-format.md](references/plan-and-tasks-format.md) — header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, TaskCreate mapping, anti-hallucination rule, quality rules |
<!--skill-flavor:plan-and-tasks-format-row:end-->
| `author`, `extract`, `edit` | [author-guide.md](references/author-guide.md), [genome-from-sdd-guide.md](references/genome-from-sdd-guide.md), [scenario-proposal-guide.md](references/scenario-proposal-guide.md), [extract-guide.md](references/extract-guide.md), [edit-guide.md](references/edit-guide.md), [genome-format-guide.md](references/genome-format-guide.md), [extracted-genome-guide.md](references/extracted-genome-guide.md), [transactional-shape-guide.md](references/transactional-shape-guide.md), [skill-mapping-guide.md](references/skill-mapping-guide.md), [uipath-source-guide.md](references/uipath-source-guide.md), [source-frameworks-guide.md](references/source-frameworks-guide.md), [defect-verification-guide.md](references/defect-verification-guide.md), [parts-guide.md](references/parts-guide.md), [extraction-parts-guide.md](references/extraction-parts-guide.md); the genome templates in `assets/templates/` |
| Scripts | `scripts/check-genome.mjs` (§ Check, § Setup) and `scripts/docx.mjs` (`extract` a Word PDD to markdown; `export` an SDD to Word, both through pandoc) — `node`, any OS |

## Anti-patterns

1. **Skipping § Choosing the Verb.** A PDD silently treated as a generic document produces a degraded deliverable.
2. **Writing automation code or changing a project.** SDD, plan/tasks and genome markdown only; a build goes to `uipath-genome-builder`. In explore-first `decompose`, non-mutating `uip` discovery is the upper limit.
3. **Treating a single-project request as a plan** (§ Choosing the Verb item 8).
4. **Stopping at the SDD, or writing the genome before the SDD is `ready`.** A non-case design ends with both files (§ Chaining); a `draft` SDD waits for its blocking SME items. Never turn a Case Management SDD into a genome.
5. **Building from a genome here**, or rewriting a genome instead of editing it in place.
6. **Recommending a skill that contradicts filesystem signals.** `.flow` → `uipath-maestro-flow`, not `uipath-rpa`.
7. **Asking what the source, the SDD, a library or the filesystem can already answer.** Default first; spend a prompt only on a decision only the user can make.
8. **Recommending a product the customer's platform cannot run, or re-offering an excluded one.** Defaulting to cloud-modern picks (Maestro, Coded Apps, Document Understanding) on an Automation Suite engagement is the most expensive design error — every blocked product survives review only to fail at delivery.
