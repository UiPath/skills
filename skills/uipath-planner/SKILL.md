---
name: uipath-planner
description: "UiPath planner and genome writer: always invoke to extract, author, document, create, update, edit, check or validate an automation genome or blueprint (`*-genome.md`) and for PDD / SDD files (`pdd.md`, `*-sdd.md`). design: PDD or process source (SOP, transcript, .bpmn as design input)→SDD + genome. decompose: multi-project request→plan. author / extract / edit: genome from an idea or SDD, from a UiPath project or solution (.xaml/.cs, .flow, .bpmn, agent.json, caseplan, Workflow.json, uipath.json, .uipx) to document, refactor or migrate, or from another framework's export. Sole case-SDD author. Build from a genome→uipath-genome. `.uipx` lifecycle→uipath-solution. Orchestrator/IS/auth→uipath-platform. Building .xaml/.cs→uipath-rpa; .flow→uipath-maestro-flow; .bpmn→uipath-maestro-bpmn; agent.json/.py→uipath-agents; caseplan.json→uipath-maestro-case. In-place Legacy activity upgrade→uipath-activity-migrator. Quality review→uipath-review."
when_to_use: "'generate an SDD', 'design/architect a UiPath solution'; 'propose a demo scenario'; reverse-engineer a project; 'refactor this process', 'rebuild it on Maestro or Portable' (extract first); a request spanning separate buildable projects; ambiguous 'what should I build'. A PDD always routes here, even for one RPA process. Skip only with no PDD, SDD, genome or existing automation to document, and one project (inline nodes count as one). Flow calling only deployed processes→uipath-maestro-flow."
argument-hint: "[design | decompose | author | extract | edit | check] [target]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion, Agent, Skill, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# UiPath Planner — design, decompose and genome-writing verbs

One skill, six verbs. It writes the documents — the SDD, the plan and the genome — and checks every genome it writes; `uipath-genome` builds from the genome. The user names a verb (`/uipath-planner author invoice-sdd.md`) or the request implies one (§ Choosing the Verb). This file routes and holds the rules every verb shares; each verb's guide holds its procedure, its own rules and its read plan, and opens only when the verb runs.

**Host tools.** These names mean whatever your host provides: a **structured question** is the host's multiple-choice question tool — with none, list numbered options in one message and wait for the reply;
<!--skill-flavor:host-tools-task-list:start-->
the **task-list tool** creates, updates and lists tasks with blocked-by links — with none, the plan is the task list;
<!--skill-flavor:host-tools-task-list:end-->
**plan mode** is the host's review-before-acting mode — with none, present the plan and wait for approval before changing anything.

## Setup

1. **A genome is in play** (a path given, or one this run wrote) **and the verb is `author`, `extract`, `edit` or `check`**: read its first line and its section headings once. They answer every read-plan condition about the genome: its level (the first-line marker), whether it is extracted (a Source Map with a step table, not a stub), its source framework (the Source Map's `Source framework` row), whether it is transactional (a Transactional Shape that is not the stub), its SDD (the `Designed in:` line) and, for a process genome, its components (the Components table). A genome handed on for a build skips this step: `uipath-genome` reads it.
2. **Open the verb's guide** (§ Verbs) and read it whole. Its § Read Plan names every other file the verb reads, the phase that opens it and the condition that must hold; a file no condition reached stays closed. A file the plan reads whole is read whole — not grepped or skimmed; a pointer that names a section (`guide.md § Section`) is a read of that whole section; a catalog file (a framework selectors guide) is read by its heading list, then by the sections in play. Never work from memory of a guide.

## Verbs

| Verb | Input | Output | Guide |
|---|---|---|---|
| `design` | A PDD or any process-knowledge source, or "design / architect this" | SDD markdown (`*-sdd.md`) with the `## Planner Handoff` header, then the genome of the agreed design (`author`, [genome-from-sdd-guide.md](references/author/genome-from-sdd-guide.md)) | [design-guide.md](references/design/design-guide.md), then [sdd-writing-guide.md](references/design/sdd-writing-guide.md) for Phase 3 |
<!--skill-flavor:plan-job:start-->
| `decompose` | A request spanning separate buildable projects, with no SDD | A dated plan and live tasks created with the task-list tool | [decompose-guide.md](references/decompose/decompose-guide.md) |
<!--skill-flavor:plan-job:end-->
| `author` | An idea, description, SOP, transcript, PDD, TO-BE or agreed SDD, when a genome or blueprint is asked for; an SDD to build that has no genome yet; an agreed SDD `design` just wrote; a workshop or demo goal that needs a scenario | `*-genome.md`, and `*-prebuild.md` beside it | [author-guide.md](references/author/author-guide.md) |
| `extract` | A UiPath project or solution with its deployed state, or another automation or test framework's export | `*-genome.md` with its Source Map, and `*-prebuild.md` beside it | [extract-guide.md](references/extract/extract-guide.md) |
| `edit` | A `*-genome.md` and a change: add, split, remove, re-extract what changed, apply the pre-build answers | The same genome, edited in place; its `*-prebuild.md` rewritten | [edit-guide.md](references/edit/edit-guide.md) |
| `check` | A `*-genome.md` to check or validate | One `FAIL:` line per finding, reported; the genome unchanged | § Check |
| *build* | A `*-genome.md` | Not this skill: hand the genome path to `uipath-genome` | — |

## Choosing the Verb

Checked in order; the first match decides. Do not pattern-match on a filename or extension alone: the first-line genome marker, the `## Planner Handoff` heading and the `<!-- planner-handoff:v1 -->` marker are the load-bearing signals.

1. **The user named a verb** → that verb.
2. **A genome** — a `*-genome.md`, or a file whose first line is `<!-- UIPATH-AUTOMATION-GENOME` — to build, execute, implement or follow → invoke `uipath-genome` with `build "<GENOME_MD>"` and the user's request quoted verbatim, then stop; to change, split or re-extract → `edit`, or `design` for a change to what the SDD holds on a genome with a `Designed in:` line ([edit-guide.md § Any genome](references/edit/edit-guide.md)); to check or validate → `check`.
3. **A design handed back by a build skill** — a build skill (`uipath-maestro-case`) found no SDD to build from — or **an SDD draft to finalize** (`*.draft.md`) → `design`; [sdd-writing-guide.md](references/design/sdd-writing-guide.md) § Design Handed Over by a Build Skill and Step 2 item 6 state what changes. **A caller's design request** — a fenced block whose first line is `planner-design-request: v1` → `design`; [caller-request-guide.md](references/design/caller-request-guide.md) states what changes.
4. **An existing automation** — a UiPath project or solution, or another framework's export — to document, reverse-engineer, size or blueprint → `extract`; to refactor or migrate → `extract`, then `uipath-genome` (§ Chaining). A Windows-Legacy project whose activities are upgraded in place → `uipath-activity-migrator`.
5. **A genome or blueprint asked for** from a description, an SOP, a transcript, a PDD, a TO-BE or an SDD, or an explicit workshop, demo or scenario request ("propose a demo scenario with X") → `author`. An explicit genome request outranks Critical Rule 4's PDD → SDD default. A request for an SDD *and* a genome or blueprint is `design`, which writes both.
6. **A document path** → read its first ~50 lines. The `## Planner Handoff` heading or the `<!-- planner-handoff:v1 -->` marker (either alone suffices) marks an SDD: its handoff's `Genome` row names a genome that exists on disk → that genome, routed by item 2; otherwise → `author` from the SDD ([genome-from-sdd-guide.md](references/author/genome-from-sdd-guide.md)), then `uipath-genome` when the request's intent is to build (§ Chaining). A PDD or any process-knowledge source — steps, applications and exceptions in a PDD, Confluence page, BPMN model, meeting transcript, SOP or requirements doc, or a document the user calls a PDD → `design`; a less structured source still goes to `design`, with heavier elicitation. Anything else → ask once with a structured question: *PDD → `design`*, *SDD → `author`* (as for an SDD with the handoff header), *other context → `decompose`*, reading the document as its context.
7. **No document** → explicit design language ("design this", "architect this", "generate an SDD"), or a process described inline with enough detail to stand in for a PDD (process steps + applications + exceptions) → `design`. A design request thin on detail still goes to `design`, which elicits what is missing through structured questions in Phase 1 rather than degrading to a `decompose` plan. Otherwise → `decompose`: a request spanning separate buildable projects, or one still ambiguous after detection ("what should I build?", "automate our invoice handling, not sure with what") — its Step 2 exits single-project requests to the specialist.
8. **One project one specialist owns end to end, with no PDD, SDD or genome** → not this skill: load that specialist directly. A Flow with script nodes, an inline HITL step and its own solution wrapper is one `uipath-maestro-flow` project — inline nodes and solution scaffolding are steps the specialist performs, never separate skills to orchestrate. Counting them as skills and writing a plan is the most common mis-trigger.

## Chaining

A verb hands its output to the next one only along these edges:

- **`design` → `author` → `uipath-genome`, one turn each.** A `ready` SDD gets its genome on the next turn, then the genome goes to `uipath-genome` when the request's intent is to build; a `draft` SDD waits. An SDD handed in with no genome takes the same path from `author`. A design a build skill handed over goes back to that skill instead, with no genome; a caller's request with `stop-after: sdd` ends at its result ([caller-request-guide.md](references/design/caller-request-guide.md)). The sequence and every condition: [sdd-writing-guide.md](references/design/sdd-writing-guide.md) § Step 3.
- **`extract` → `uipath-genome`** for a refactor or migration request, in the same session, once the user's edits are in; an unattended run hands the genome over without asking.
- **`design` revise → `edit`, same run.** An SDD change on an SDD whose `Genome` row names a genome on disk ends with that genome updated and given the strict check ([sdd-writing-guide.md](references/design/sdd-writing-guide.md) § Keeping the Genome Current).
- **`uipath-genome` → `edit` → `uipath-genome`.** A deviation the build reports in the genome comes back here as an `edit`, then the build runs again; the builder never changes the genome.
- **`uipath-genome` not installed** (it is absent from the session's list of available skills) → the genome verbs still write and check genomes, and `design` still writes the genome; say that building them needs `uipath-genome`.
- **Build → publish, only when asked.** The build is local and writes nothing to a tenant.
<!--skill-flavor:deploy-after-build:start-->
When the request asks to publish, deploy or go live, the publish follows the build's hand-off: through `uipath-solution`, or per package to Orchestrator through `uipath-platform` when Solutions (`.uipx`) are blocked for the SDD's `Delivery model` — standalone, Automation Suite older than 2.2510, or a user exclusion ([platform-availability-guide.md](references/shared/platform-availability-guide.md)).
<!--skill-flavor:deploy-after-build:end-->

## Check

```bash
node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict
```

`<SKILL_DIR>` is the folder holding this `SKILL.md`; the level argument is the one the genome's first-line marker names. A process genome's check covers every component genome its Components table links. An extracted genome checked against its source export adds `--processes "<INVENTORY_JSON>" --recordsets "<RECORDSETS_JSON>"` (both together; the two files the framework migration pack's `data` command writes). Exit 0 passes; exit 1 prints one `FAIL:` line per finding; exit 2 is a usage error — fix the command, never the genome. A hand-run check whose level argument is not the marker's level reports the marker as missing: run it again with the marker's level — that `FAIL` is not a genome finding. `node` missing → say the check did not run.

- **`check`** runs it and reports each `FAIL` with the section it names; it changes nothing. A fix the user then asks for is an `edit`.
- **`author`, `extract` and `edit`** run it on every genome they wrote or changed, fix every `FAIL` and run it again — at most three rounds; a `FAIL` left after the third is named in the closing summary.

## Critical Rules

Every verb obeys these; each verb's guide adds its own under § Verb Rules.

1. **Plan, design and specify — never author automation code yourself.** `design`, `decompose`, `author`, `extract` and `edit` deliver only SDD, plan and genome markdown,
<!--skill-flavor:plan-design-only-outputs:start-->
plus live tasks created with the task-list tool;
<!--skill-flavor:plan-design-only-outputs:end-->
they NEVER write automation code (XAML, C#, Python) or project or scaffold files. Extraction's working files — inventory JSON under the work dir, part briefs and ledgers — are not deliverables and are exempt. Implementation always routes to a specialist, and every genome build to `uipath-genome`.
2. **Choose the verb first** (§ Choosing the Verb) and run § Setup, before anything else. Every verb then reads by its guide's § Read Plan, in at most three turns — never file by file as each file names the next.
3. **One writer, one builder, one handoff.** `author`, `extract` and `edit` write every genome and end with its strict check (§ Check); `uipath-genome` builds every genome as written and never changes one — not even a one-line fix the user names. The genome is what passes to `uipath-genome`; for a designed genome the agreed SDD is its source ([genome-format-guide.md § Design Links](references/shared/genome-format-guide.md)).
4. **The output follows the input.** A PDD or process source gets an **SDD, then the genome of the agreed SDD** (§ Chaining); an SDD to build gets a **genome**, then the build; a request spanning separate buildable projects with no SDD gets a **dated plan**; a genome or blueprint request, a refactor or a migration gets a **genome**; a **PDD** is never written — it is input only.
5. **Route — do not redescribe.** An SDD, a plan and a genome say WHICH skill builds each part and IN WHAT ORDER. They never describe a specialist's internal flow (target configuration, Object Repository registration, XAML pipelines, scaffolding, pack/publish, HITL field or outcome schema, auth, testing procedures). For a HITL step, pass business intent only ("manager approves or rejects an expense; can add a reason if rejected") — the HITL specialist chooses the schema.
6. **Fill gaps with markers — never silently invent business rules.** SDDs and plans use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts) and `[SME REVIEW]` for business-knowledge gaps; resolve `[SME REVIEW]` items with the user before finalizing — they gate the `Status: ready` flip, not the skeleton write. Genomes use the best interpretation plus `*[Inferred]*` ([genome-format-guide.md § Ambiguity Marker](references/shared/genome-format-guide.md)). For an Agent or Coded App gap, ask with a structured question (proceed with gap filling, or a different product) — never fall back on your own. Exact tokens, nothing inside the brackets, byte-for-byte carry-over: [sdd-writing-guide.md § Gap Markers](references/design/sdd-writing-guide.md#gap-markers).
7. **Never invent selectors or UI targets.** Selectors need the application inspected at development time; an SDD, a plan and an authored genome leave them to the specialist. A target carried over from the source is not invented: `extract` records where the source's targets live (objects, ids, counts) in the Source Map, and `uipath-genome` migrates them at build.
8. **Gate every product by the platform.** The delivery model (Automation Cloud, Automation Suite, standalone Orchestrator) blocks unavailable products through [platform-availability-guide.md](references/shared/platform-availability-guide.md), in every verb that chooses a product (`design`, `decompose`, `author` without an SDD, `extract` for its targets); a product the user excluded is never offered again in the session.
9. **Prompt budget.** `design` runs its own checkpoint model ([design-guide.md](references/design/design-guide.md)); `decompose` caps at **5 structured questions**. Ask execution autonomy **exactly once**, at `design` entry — never when a caller's request carries `execution` — and write it into the handoff header; `author` on an SDD reads it and never asks again. Scope and UI answers resolved in `design` flow forward through the SDD.

## Reference Navigation

| Verb | Guides it may read (its § Read Plan decides when) |
|---|---|
| `design` | [design-guide.md](references/design/design-guide.md) whole — its § Read Plan names every other guide (Phase 3: [sdd-writing-guide.md](references/design/sdd-writing-guide.md)) and the SDD templates in `assets/templates/`; [asdd-crosswalk-guide.md](references/design/asdd-crosswalk-guide.md) with `scripts/sdd-to-docx.mjs` (client Word SDD, on request) |
| `decompose` | [decompose-guide.md](references/decompose/decompose-guide.md), [multi-skill-patterns-guide.md](references/shared/multi-skill-patterns-guide.md) |
<!--skill-flavor:plan-and-tasks-format-row:start-->
| `decompose`: format | [plan-and-tasks-format.md](references/shared/plan-and-tasks-format.md) — header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, task-list tool mapping, anti-hallucination rule, quality rules |
<!--skill-flavor:plan-and-tasks-format-row:end-->
| `author`, `extract`, `edit` | [author-guide.md](references/author/author-guide.md), [genome-from-sdd-guide.md](references/author/genome-from-sdd-guide.md), [scenario-proposal-guide.md](references/author/scenario-proposal-guide.md), [extract-guide.md](references/extract/extract-guide.md), [edit-guide.md](references/edit/edit-guide.md), [genome-format-guide.md](references/shared/genome-format-guide.md), [extracted-genome-guide.md](references/shared/extracted-genome-guide.md), [transactional-shape-guide.md](references/shared/transactional-shape-guide.md), [skill-mapping-guide.md](references/shared/skill-mapping-guide.md), [uipath-source-guide.md](references/extract/uipath-source-guide.md) with [uipath-rpa-signals-guide.md](references/extract/uipath-rpa-signals-guide.md) and [uipath-non-rpa-signals-guide.md](references/extract/uipath-non-rpa-signals-guide.md), [source-frameworks-guide.md](references/extract/source-frameworks-guide.md), [defect-verification-guide.md](references/shared/defect-verification-guide.md), [extraction-parts-guide.md](references/shared/extraction-parts-guide.md), [prebuild-guide.md](references/shared/prebuild-guide.md); the genome templates in `assets/templates/` |

## Anti-patterns

1. **Skipping § Choosing the Verb.** A PDD silently treated as a generic document produces a degraded deliverable.
2. **Writing automation code or changing a project.** SDD, plan and genome markdown only; a build goes to `uipath-genome`. In explore-first `decompose`, non-mutating `uip` discovery is the upper limit.
3. **Recommending a skill that contradicts filesystem signals.** `.flow` → `uipath-maestro-flow`, not `uipath-rpa`.
4. **Asking what the source, the SDD, a library or the filesystem can already answer.** Default first; spend a prompt only on a decision only the user can make.
5. **Recommending a product the customer's platform cannot run, or re-offering an excluded one.** Defaulting to cloud-modern picks (Maestro, Coded Apps, Document Understanding) on an Automation Suite engagement is the most expensive design error — every blocked product survives review only to fail at delivery.
