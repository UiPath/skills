# SDD Writing Guide — Phase 3 of `design`

Phase 3 of `design` writes the full SDD to disk incrementally, resolves the SME items, checks it against its template and flips it to `ready`; the next turns write its genome and run `plan`. Reached from [design-guide.md](design-guide.md) once Phase 2 is approved — that guide's § Verb Rules and its Phase 1 / Phase 2 results apply throughout. Read this guide whole before the first Phase 3 write.

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| Step 1 | filling RPA §4 Business Rules or BPMN §5 Gateways, and [business-rules-guide.md](business-rules-guide.md) is not yet open from Phase 2 | [business-rules-guide.md](business-rules-guide.md) |
| Step 2.5 | the user asks for the official client SDD/ASDD in the customer's own structure | [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) |
| Step 3, next turn | the SDD is `Status: ready` and is not a Case Management SDD | [author-guide.md](author-guide.md) whole — the `author` verb; its § Read Plan names the rest |
| Step 3, turn after | the user's intent implies implementation | [plan-guide.md](plan-guide.md) whole — the `plan` verb; its § Read Plan names the rest |

## Phase 3 — Full SDD Generation

> **Progress:** Mark "Generate architecture (Phase 2)" as `completed`. Mark "Write SDD skeleton to disk" as `in_progress`.

### Step 0: Write the SDD Skeleton to Disk — Hard Gate

**Write the file to disk now, before generating any Phase 3 section.** This is an action, not advice: Step 1 does not begin until a `Write` call has created the SDD file (Step 2 item 7 resolves the path and the Solution-scope file set). Do NOT hold the entire SDD in context and write only at the very end.

**First, run the collision check — the skeleton write is the write that can clobber.** Before writing anything, apply the re-run handling in Step 2 item 6: if a target file already exists, resolve it with that `AskUserQuestion` (keep / regenerate / resume / write as `-v2-`) and honour the answer here. "Keep the existing SDD and stop" ends `design` with no write at all; "Resume generation" patches the existing draft instead of overwriting it. Only "Regenerate" and the no-file-exists case write a fresh skeleton. Item 6 then has nothing left to ask.

The skeleton write contains, in this order:

1. The title/header + `## Document History`.
2. The `<!-- planner-handoff:v1 -->` marker **and** the `## Planner Handoff` header, with `Status: draft` and `Template validation: pending` (full field list in Step 2 item 2). Both signals MUST be in this first write so detection — and grading — works even on a partial file: the marker says "planner SDD", the `Status` field says whether it is consumable.
3. The `## Decisions Made` block (autonomous mode) and the `## Recommended Scope` block (both modes) — formats in Step 2 item 3.
4. Every Phase 1 / Phase 2 section you already have.

Then append the remaining Phase 3 sections to that file with follow-up `Edit` / `Write` calls **as you generate them** — do not buffer them in context and do not rewrite the whole file per section.

**Rationale.** A long autonomous turn can be hard-killed by the per-turn watchdog mid-generation. An incrementally-written file leaves a gradeable, useful SDD on disk; a buffered one leaves nothing at all. Step 1.5 (SME resolution) and the Step 2 superset check still run — they patch and verify the file already on disk rather than gating the first write. Flipping `Status` to `ready` is the LAST write of `design`, so an interrupted run leaves `draft` on disk and `plan` refuses to derive tasks from it.

> **Progress:** Mark "Write SDD skeleton to disk" as `completed`. Mark "Generate full SDD (Phase 3)" as `in_progress`.

### Step 1: Generate Remaining Sections

Fill in all sections of the chosen template not covered in Phase 1 or Phase 2. Section assignments per phase:

**Phase 1 produces (for all templates):**
- Header & Document History (process name, today's date, version 1.0). The Case template's title heading is `# SDD — {Case Name}`.
- Overview section (§1)
- Process/Flow/Lifecycle diagram (§2 for most templates)
- Detailed steps / nodes description where applicable

**Phase 2 produces:** See [design-guide.md](design-guide.md) Phase 2 Step 2 (template-specific architectural core)

**Phase 3 produces:** All remaining sections — typically:
- Business Rules (RPA, Case). RPA §4: [Business Rules Guide](business-rules-guide.md)
- Value Mappings (RPA)
- Exception / Error Handling (all)
- Credentials & Assets (RPA)
- Deployment Environment (RPA — robot type, Studio/Robot versions, VM hosts, screen resolution, scalability). Fill the Orchestrator row from the Step 0 delivery model (Cloud / Automation Suite + version / standalone); fill `[SME REVIEW]` for the rest when the PDD does not specify — these fields typically come from the deployment team, not the PDD. Never invent VM names, version pins, or robot types.
- Triggers (Flow)
- SLA Rules & Escalations (Case)
- Compliance Constraints (Case)
- Roles & RACI Matrix (Case)
- Evaluation Criteria (Agents)
- **Non-Functional Requirements — always (best practice).** Security (credentials in Orchestrator / secret assets, least-privilege IS connection scope, don't expose entity calls in the network trace), performance (DB vs file, webhooks vs polling, avoid license-consuming Windows processes), scalability, availability, and logging / monitoring. Applies to every product; the API Workflow template already carries §Performance & Scaling + §Security & Authentication — other templates capture the equivalent under a Non-Functional Requirements subsection.
- **Reusable Components / Libraries — always (best practice).** List reused existing shared assets (tenant Libraries discovered in Phase 1 Step 2.5, Marketplace / org components, existing connectors) AND new reusable assets to build (shared workflows → an RPA **Library** routed to `uipath-rpa`; a missing integration → a **custom connector** routed to `uipath-connector-builder`), each built before its consumers. Assets used by 2+ projects live at the parent-folder / solution level. See [Product Selection Guide → Reusability & shared assets](product-selection-guide.md#reusability--shared-assets).
- **Testing Strategy — always thorough.** Cover happy path, edge cases, error scenarios, and (for Master Projects) end-to-end pipeline tests. Do NOT ask the user about test depth — depth is non-negotiable here. Implementation specialists may scope tests down at execution time if the user wants a quick MVP.
- **Next Steps — points at `plan` (task derivation).** Replaces the legacy "Implementation Plan" section. `plan` owns the implementation task list; `design` does not generate one.

<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section, a task list, or `TaskCreate` calls for implementation work. Those are owned by `plan` (task derivation). The SDD's `## Next Steps` section marks the boundary into `plan`, and that is the entire `design` output surface.
<!--skill-flavor:phase3-output-surface:end-->

### Step 1.5: Resolve SME Review Items

> **Progress:** Mark "Generate full SDD (Phase 3)" as `completed`. Mark "Resolve SME review items" as `in_progress`.

Before finalizing the SDD (the skeleton is already on disk from Step 0), collect all `[SME REVIEW]` items. If there are any:

> **Batching rule — `AskUserQuestion` 4-option cap.** Each `AskUserQuestion` question accepts at most 4 options. If there are 1-4 items, send one question. If there are 5-8 items, send a single `AskUserQuestion` call with **two questions** (each ≤4 options), grouped by SDD section. If there are more than 8 items, send one `AskUserQuestion` call per batch of up to 8 (two questions each), waiting for answers between batches. **Do not flatten >4 items into one question** — the call will fail validation.

1. Batch them into one or more `AskUserQuestion` calls using numbered-choice format. Example for 1-4 items:

> Before I finalize the SDD, these items need your input:
>
> 1. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
> 2. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
>
> You can answer each, accept all defaults by replying "use defaults", or skip specific items.

2. Update the SDD sections with the user's answers.
3. If the user partially answers or asks follow-ups, do one more round (max 2 rounds total). After 2 rounds, keep remaining unresolved items as `[SME REVIEW]`, apply each item's recorded default in its section, and proceed to Step 2.
4. Any items the user explicitly skips remain as `[SME REVIEW]` in the final file with their defaults applied.
5. **Classify every surviving item:** `default-carried` (a recorded default is applied in its section — the normal case) or `blocking` (no defensible default AND the answer materially changes the architecture). Blocking is a closed list: (a) delivery model unknown while a selected product is matrix-gated on it; (b) an in-scope §9 application whose access method is unknown; (c) contradictory PDD scope statements Level 0/1 could not resolve; (d) the user rejected the Level 1 recommendation without choosing an alternative. Record the class in the Action Required table (Step 2 item 4). Blocking items keep the SDD at `Status: draft` (Step 2 item 8 rule 4).
6. If there are zero `[SME REVIEW]` items, skip this step entirely.

This step runs in BOTH Autonomous and Interactive modes — it is a hard blocker to producing a complete SDD.

### Step 2: Finalize the SDD File(s)

> **Progress:** Mark "Resolve SME review items" as `completed`. Mark "Finalize SDD (Status: ready)" as `in_progress`.

1. Assemble all sections in template order. The Step 0 skeleton already holds the header + handoff + `## Decisions Made` / `## Recommended Scope` + Phase 1/2 sections — finalize it by appending/patching the remaining sections in template order rather than rewriting from scratch.
2. **Fill the `## Planner Handoff` header** that appears near the top of every template. Every template places it after `## Document History`. This is the load-bearing detection contract. § Choosing the Verb accepts **either** the heading OR the adjacent `<!-- planner-handoff:v1 -->` HTML marker as a detection signal — both ship in every template and both should survive into the generated file (so a later session, or a hand-written SDD, still routes to `plan`):

   ```markdown
   <!-- DO NOT RENAME: uipath-planner detects SDDs via this exact heading or the marker below. -->
   <!-- planner-handoff:v1 -->
   ## Planner Handoff

   | Field | Value |
   |---|---|
   | **Status** | draft → ready                                  ← the first incremental write stamps `draft`; flip to `ready` ONLY after Step 1.5 ran (every surviving SME item classified `default-carried`) AND the item 8 template-superset check passes. A `blocking` SME item keeps `draft`. `plan` derives tasks from `ready` only.
   | **Execution autonomy** | <autonomous | interactive>          ← from Phase 1 Step 0
   | **Delivery model** | <cloud | automation-suite | standalone | unspecified> ← from Phase 1 Step 0 (append the Suite version when known, e.g. `automation-suite 2025.1`)
   | **SDD scope** | <single-product | solution>                  ← from Phase 1 Step 4 (Level 1 / Level 1.75)
   | **Solution root SDD** | <SOLUTION_NAME_KEBAB>-solution-sdd.md ← solution scope ONLY — write into EVERY SDD (the root names itself); omit all four solution rows for single-product
   | **Solution ID** | <SOLUTION_NAME_KEBAB>                       ← same value in the root and every child; `plan` verifies the match
   | **Project SDD role** | root | child                           ← `root` in the solution overview, `child` in every per-project SDD
   | **Independently executable** | no                              ← children only; `plan` refuses to derive tasks from a child directly
   | **Project list section** | §11 / §10 + §11 / Project Inventory ← template-specific (RPA single: §11; RPA Master: §10 + §11; Flow: §3 + §7; BPMN: §4 + §9; Case: §2 + §4; etc.)
   | **Tasks file** | `<PROCESS_NAME_KEBAB>-tasks.md`             ← planner writes here on first run. Solution scope: root AND every child carry the SAME canonical `<SOLUTION_NAME_KEBAB>-tasks.md` — exactly one tasks file per solution, never one per project
   | **Genome** | <PROCESS_NAME_KEBAB>-genome.md               ← NOT written by `design`: the genome turn (`author` through genome-from-sdd-guide.md, Step 3 item 3) adds this row after `Tasks file`. Solution scope: one genome named after the root solution SDD, `<SOLUTION_NAME_KEBAB>-genome.md`, with its row in the ROOT SDD only. Case template: never
   | **Build handoff** | <prose — Case template ONLY>         ← the Case template emits this row INSTEAD of `Tasks file`: the case build writes `caseplan.json` directly and has no tasks file, so there is no path to carry. Every other template emits `Tasks file`; never emit both
   | **Generated by** | uipath-planner
   | **Generation date** | <YYYY-MM-DD>
   | **Template validation** | pending → passed                   ← set to `passed` together with the `ready` flip (item 8)
   ```

   Do NOT rename the heading or strip the marker. They are redundant on purpose — keeping both means a hand-edit of one signal does not silently break `plan` detection.

3. **Autonomous-mode Decisions Made block.** If `Execution autonomy: autonomous`, insert a `## Decisions Made` block immediately after the Planner Handoff header and before any `Action Required — SME Review Items` block or product body. It sits before the Table of Contents in every template. The block makes the highest-leverage architectural picks scannable in the SDD's first screenful so a reviewer can spot a wrong call without reading the whole document. In `Execution autonomy: interactive`, this block is optional — the user already reviewed each decision at the Phase 1/Phase 2 checkpoints. Skip the block for interactive runs.

   Format:

   ```markdown
   ## Decisions Made

   > Autonomous mode picked the five architectural decisions below without a user checkpoint. Override by rerunning in Interactive mode (`Execution autonomy: interactive` in the Planner Handoff header above) or by editing the relevant SDD section.

   | # | Decision | Picked | One-sentence reason |
   |---|---|---|---|
   | 1 | **Platform constraints** (Constraint Gate) | <DELIVERY_MODEL; BLOCKED_PRODUCTS_WITH_ALTERNATIVES_OR_NONE> | <SOURCE_OF_DELIVERY_MODEL_AND_MATRIX_RULE_APPLIED> |
   | 2 | **Scope** (Level 1) | <SINGLE_PRODUCT_OR_SOLUTION_COMPOSITION> | <REASON_TIED_TO_PDD_SIGNAL> |
   | 3 | **RPA sub-type** (Level 1.5) — per RPA project | <PROCESS_OR_LIBRARY_OR_TEST_AUTOMATION> | <REASON_TIED_TO_PDD_SIGNAL> |
   | 4 | **Authoring mode** (Level 2) — per RPA project | <XAML_OR_CODED_OR_HYBRID> | <REASON_TIED_TO_PROCESS_BODY_SHAPE> |
   | 5 | **Framework** — per RPA Process project | <REFRAMEWORK_OR_SEQUENCE> | <REASON_TIED_TO_PER_ITEM_INDEPENDENCE> |
   ```

   Rules for the block:
   - Each "Picked" cell is a single concrete value, not a placeholder.
   - Each "One-sentence reason" is ≤ 20 words and cites the PDD signal or process characteristic that drove the pick.
   - Row 1 always appears, even when nothing was blocked (`cloud; no products blocked`) — the reviewer must see which platform the architecture assumes.
   - For Solution scope, rows 3-5 repeat per RPA project (use a sub-table or one row per project — keep concise).
   - For non-RPA scopes (e.g., Single-product Agent), rows 3-5 collapse to N/A with one row covering the product-specific Level-1.5-equivalent (framework choice, app type, etc.).
   - The block does NOT replace the per-section detail later in the SDD — the product body still carries the full justification in its architecture, stage/task, framework, or project-structure sections. The block is the **scannable index** of those decisions.

   In BOTH modes, also emit the `## Recommended Scope` block directly after `## Decisions Made` (directly after the Planner Handoff header when that block is absent — interactive runs): copy the Phase 1 summary's `Recommendation:`, `Delivery model:`, and `Blocked by platform:` lines (see [product-selection-guide.md → Summary block](product-selection-guide.md#summary-block)). Autonomous mode skips the Phase 1 presentation, so this copy is the only durable record of the Constraint Gate outcome.

4. If any `[SME REVIEW]` items remain, add a consolidated warning section after the Planner Handoff header (and after the `## Decisions Made` / `## Recommended Scope` blocks if present) and before the product body. This sits before the Table of Contents in every template:

```markdown
## Action Required — SME Review Items

| # | Section | Item | Question | Default applied | Blocking |
|---|---|---|---|---|---|
| 1 | <SECTION> | <ITEM> | <QUESTION> | <DEFAULT> | <yes/no> |

> These items are marked `[SME REVIEW]` in the document. Default-carried items (Blocking = no) do not block task derivation — the automation is built on the recorded defaults, which must be verified before production sign-off. Any Blocking = yes item keeps the handoff at `Status: draft`.
```

5. **Target SDD length: 300-800 lines of markdown** for single-project SDDs. **Master Project SDDs may reach 600-1200 lines** due to per-sub-project structure sections — this is expected. For processes with more than 20 steps, group related steps and summarize at the parent level. For processes with more than 10 business rules, prioritize the 10 most impactful.
6. **Re-run handling — already resolved at Step 0.** This check runs BEFORE the Step 0 skeleton write (that is the write that can clobber an existing file); by the time you reach here the answer is already applied, so do not re-ask. The question, for reference and for the Step 0 gate: if `<PROCESS_NAME_KEBAB>-sdd.md` already exists, ask the user via `AskUserQuestion`:

   First read the existing file's handoff `Status`:

   - **`Status: ready` (or no Status field — legacy):**

   > An SDD already exists at `<sdd-path>`. How should I proceed?
   >
   > 1. **Keep the existing SDD and stop** *(recommended)* — proceed to `plan` if you want to refresh the task list
   > 2. **Regenerate from the PDD** — overwrites the existing SDD

   - **`Status: draft` (interrupted run):**

   > An unfinished SDD draft exists at `<sdd-path>` (interrupted generation). How should I proceed?
   >
   > 1. **Resume generation** *(recommended)* — finish the remaining sections, resolve SME items, run the completeness check, then flip Status to ready
   > 2. **Regenerate from the PDD** — discard the draft and start over
   > 3. **Generate alongside as `<name>-v2-sdd.md`** — for diffing

   Default is "keep" — overwriting an SDD the user might have hand-edited is the more destructive action.

7. Write the output file(s) to the current working directory. If the user specified an output path for the SDD, use it instead of these defaults:
   - **Single-product scope:** one file at `<PROCESS_NAME_KEBAB>-sdd.md`.
   - **Solution scope:** the solution overview at `<SOLUTION_NAME_KEBAB>-solution-sdd.md` PLUS one per-project SDD at `<PROJECT_NAME_KEBAB>-sdd.md` for each project in the unified project list. Put the `[SME REVIEW]` warning block in the solution overview AND in any per-project file where a review item lives in that project. Each per-project SDD gets its own `## Planner Handoff` header.

8. **Template-superset check (mandatory before the item 9 summary).** After writing each SDD file, re-read it and extract every H2 (`## `) and H3 (`### `) heading. Compare against the template's Table of Contents and required subsections. The generated SDD's heading set MUST be a superset — extra subsections are fine, missing template sections are an SDD defect. Exception: an H3 subsection whose template comment marks it optional (e.g. "omit when no document extraction is in scope") may be omitted entirely when its condition applies; every other template H3 is required.

   Minimum required H2 headings per template:
   - **RPA template:** §1 Process Overview, §2 Process Map, §3 Detailed Process Steps, §4 Business Rules, §5 Data Definitions, §6 Value Mappings, §7 Exception Handling, §8 Error Handling, §9 Application Inventory, §10 Master Project Architecture, §11 Project Structure, §12 Queue Architecture (omit only when the design defines or consumes no Orchestrator queue), §13 Implementation Mode, §14 Packages, §15 Credentials & Assets, §16 Deployment Environment, §17 Testing Strategy, §18 Next Steps
   - **Case template:** §1 Case Definition, §2 Stages & Tasks, §3 Personas & App Views, §4 Integrations, plus the unnumbered H2s `## Document History`, `## Planner Handoff`, `## Table of Contents`, `## Non-Functional Requirements`, `## Testing Strategy`, `## Next Steps`. Also verify every modeled stage has a `### Stage ...` or `### Secondary Stage ...` block, every modeled task has a `##### Task ...` detail block, and every task detail block contains the exact marker `**Task envelope**` before its Required / Run Only Once / Skip Condition table.
   - **Other templates:** check the template file's TOC; the rule is the same — every H2 in the template appears in the generated SDD.

   For any missing required H2:
   1. Regenerate that section from the template + Phase 1 extraction data + Phase 2 architecture.
   2. If the template's contents for that section depend on a Phase 1 / Phase 2 input that is genuinely absent (e.g. §4 Business Rules but the PDD has zero rule signals), emit the section with an explicit "No business rules extracted from the PDD" note plus an `[SME REVIEW]` row asking the user to supply any.
   3. Never silently drop a section.
   4. **Ready flip — the final write of `design`.** When every required heading is present and every remaining `[SME REVIEW]` item is classified `default-carried` (Step 1.5 rule 5), update the handoff: `Status: ready`, `Template validation: passed`. Open default-carried items do NOT block ready — they gate production sign-off, not task derivation. Any `blocking` item keeps `Status: draft`; the item 9 summary names it and asks. Skipping the flip leaves the file at `draft` and `plan` will refuse to derive tasks from it.

   Common slip-fail: skipping §4 Business Rules because the PDD has no dedicated "Business Rules" section. Rules are usually buried in "Remarks", step descriptions, or screenshots — the PDD analysis guide's "Embedded business rules" pointer applies. Treat zero rules in §4 as a regeneration trigger, not a finished section.

9. Output a summary in the conversation:

```markdown
## SDD Generated

<FILENAME_1> — <COUNT> sections, <LINE_COUNT> lines
<FILENAME_2> — <COUNT> sections, <LINE_COUNT> lines
...

<SME_REVIEW_COUNT> open SME review items (if any — list each with its class and default).

**Next — branch on the handoff `Status`:**
- `ready` — `design` is complete and the SDD is on disk. The genome is written from it on the next turn (Step 3), then `plan` (task derivation) runs with this SDD path; open default-carried SME items travel into the genome and the derived tasks as assumptions — confirm them before production. A Case Management SDD gets no genome.
- `draft` (blocking SME items) — Blocked on: <BLOCKING_ITEMS>. Answer these and the SDD finalizes to `ready`; no genome is written and `plan` refuses drafts until then.
```

### Step 2.5: Word (.docx) Delivery — only when requested

When the user asks for a Word or client-facing deliverable, convert the written SDD — do not author Word content by hand or drive Word via COM.

**Plain `.docx` of the SDD:**

```bash
node "<SKILL_DIR>/scripts/docx.mjs" export "<SDD_PATH>.md" [--reference-doc "<TEMPLATE>.docx"]
```

`<SKILL_DIR>` is the folder containing this skill's SKILL.md. The output defaults to `<SDD_BASENAME>.docx` in the current working directory, with a table of contents; the script prints its path. `--reference-doc` applies a customer template's fonts, heading styles, and margins. The section structure stays as the markdown SDD.

**Official client SDD/ASDD (customer's structure):** the markdown SDD is agent-first; the official Word document is the client deliverable in the customer's own section layout. Ask the user for the template path, then follow [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) to match the markdown SDD into the template's sections and compute the missing pieces. Do not invent the official section structure.

**Diagrams:** keep them as Mermaid and make them readable — clear node labels, one node per step, a logical direction. They convert as code blocks. Rendering them to images and styling the final document are not this skill's job — leave that to the user or their doc tooling.

Exit codes: 0 written; 1 usage error, or the SDD or reference document not found — fix the path and re-run; 2 pandoc missing — relay the install command it prints; 3 conversion failed — report it and deliver the markdown SDD. Without `node`, deliver the markdown SDD and say the Word export did not run.

Skip this step entirely when the user did not ask for Word output.

### Step 3: Next Turns — the Genome, then `plan`

> **Progress:** Mark "Finalize SDD (Status: ready)" as `completed`. All progress tasks are now done.

<!--skill-flavor:design-deliverable:start-->
The SDD is the deliverable of `design`. **Do not generate an Implementation Plan section inside the SDD. Do not create implementation `TaskCreate` calls during `design`. Do not start executing.**
<!--skill-flavor:design-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin the genome or `plan` in the same turn as `design`.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue on the **next** turn with the sequence below. Rationale: `design` (read PDD + guides, author §1–§18), `author` (read the SDD, write and check the genome) and `plan` (parse SDD, derive tasks, emit `TaskCreate`) are each heavy; stacking two of them in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after each durable write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->

Then continue:

1. **`Status: draft`** (a blocking SME item) → no genome and no `plan`. The item 9 summary names the blocking items. The turn that receives the user's answers patches them into the SDD, reruns the superset check and flips it to `ready` as its last write, then ends; the genome (item 3) runs on the following turn.
2. **A Case Management SDD** → no genome, ever: `uipath-maestro-case` builds from the SDD.
3. **Next turn — the genome.** Run the `author` verb on the `ready` SDD ([genome-from-sdd-guide.md](genome-from-sdd-guide.md)). It writes `<PROCESS_NAME_KEBAB>-genome.md` beside the SDD with a `Designed in:` line, checks it, and adds `| **Genome** | <path> |` to the Planner Handoff table after `Tasks file` — the only edit to the SDD. Solution scope: one process genome for the solution, `<SOLUTION_NAME_KEBAB>-genome.md` beside the root solution SDD, with the `Genome` row in the root's handoff only. Write the genome even when `uipath-genome-builder` is not installed, and say that building from it needs `uipath-genome-builder`. The genome write is a turn boundary too: end the turn after `author`'s summary.
4. **Turn after — `plan`, or stop.**
   The request's intent decides, never the execution mode — in both modes:
   - The user's intent implies implementation ("create / build / implement / set up / make") → continue into `plan` with `<sdd-path>` on the turn after the genome, without asking. `autonomous`: `plan` emits the tasks directly; `interactive`: `plan` presents them for review in its own Step 8 — do not add a "shall I plan?" question here. `plan` reads the `## Planner Handoff` header, including the `Genome` row, and writes `<process-kebab>-tasks.md` alongside the SDD — see [plan-guide.md](plan-guide.md). With `uipath-genome-builder` installed it routes the build through Pattern 7 ([multi-skill-patterns-guide.md](multi-skill-patterns-guide.md)): `uipath-genome-builder` builds every component from the genome; without it, `plan` derives per-skill tasks from the SDD.
   - The user only asked to "design / architect / generate an SDD" → stop after the genome in either mode; the SDD and the genome are the deliverable. Offer `plan` in one line of `author`'s summary.
