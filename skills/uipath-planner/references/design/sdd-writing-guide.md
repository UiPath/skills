# SDD Writing Guide — Phase 3 of `design`

Phase 3 of `design` writes the full SDD to disk incrementally, resolves the SME items, checks it against its template and flips it to `ready`; the next turns write its genome and, when the request is to build, hand it to `uipath-build-from-genome`. Reached from [design-guide.md](design-guide.md) once Phase 2 is approved — that guide's § Verb Rules and its Phase 1 / Phase 2 results apply throughout. Read this guide whole before the first Phase 3 write.

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| Step 1 | filling RPA §4 Business Rules or BPMN §5 Gateways, and [business-rules-guide.md](business-rules-guide.md) is not yet open from Phase 2 | [business-rules-guide.md](business-rules-guide.md) |
| Step 2 item 6 | finalizing a Case Management draft | [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Finalizing a Case Draft |
| Step 2 item 8 | a Case Management SDD | [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § SDD Conformance Checklist |
| Step 3, next turn | the SDD is `Status: ready` and no build skill handed the design over | [author-guide.md](../author/author-guide.md) whole — the `author` verb; its § Read Plan names the rest |
<!--skill-flavor:client-word-read-row:start-->
| § Client Word Document | the user asks for the client-facing Word SDD / ASDD (their official template, a `.docx`) | [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) whole |
<!--skill-flavor:client-word-read-row:end-->

## Phase 3 — Full SDD Generation

### Step 0: Write the SDD Skeleton to Disk — Hard Gate

**Write the file to disk now, before generating any Phase 3 section.** This is an action, not advice: Step 1 does not begin until a file write has created the SDD file (Step 2 item 7 resolves the path and the Solution-scope file set). Do NOT hold the entire SDD in context and write only at the very end.

**First, run the collision check — the skeleton write is the write that can clobber.** Before writing anything, apply the re-run handling in Step 2 item 6: if a target file already exists, resolve it with that structured question (keep / regenerate / resume / write as `-v2-`) and honour the answer here. "Keep the existing SDD and stop" ends `design` with no write at all; "Resume generation" patches the existing draft instead of overwriting it. Only "Regenerate" and the no-file-exists case write a fresh skeleton. Item 6 then has nothing left to ask. A caller's `existing-output: replace` is the answer "Regenerate": ask nothing ([caller-request-guide.md](caller-request-guide.md)).

The skeleton write contains, in this order:

1. The title/header + `## Document History`.
2. The `<!-- planner-handoff:v1 -->` marker **and** the `## Planner Handoff` header, with `Status: draft` and `Template validation: pending` (full field list in Step 2 item 2). Both signals MUST be in this first write so detection — and grading — works even on a partial file: the marker says "planner SDD", the `Status` field says whether it is consumable.
3. The `## Decisions Made` block (autonomous mode) and the `## Recommended Scope` block (both modes) — formats in Step 2 item 3.
4. Every Phase 1 / Phase 2 section you already have.

Then append the remaining Phase 3 sections to that file with follow-up file edits or writes **as you generate them** — do not buffer them in context and do not rewrite the whole file per section.

**Rationale.** A turn can end before it finishes — an interrupt, a context limit, a host time limit. An incrementally-written file leaves a gradeable, useful SDD on disk; a buffered one leaves nothing at all. Step 1.5 (SME resolution) and the Step 2 superset check still run — they patch and verify the file already on disk rather than gating the first write. Flipping `Status` to `ready` is the LAST write of `design`, so an interrupted run leaves `draft` on disk and `author` refuses to write its genome.

### Step 1: Generate Remaining Sections

**Defaults fill gaps, never override the source.** A `[DEFAULT]` never contradicts a value the source states (a schedule, an order of steps, a system it names) and never adds a limit nothing in the source implies (a run cap, a stop count, a polling cadence) — the build skill's own defaults cover those. A step order the source states is kept; a reorder is an `[SME REVIEW]` alternative, never the applied default.

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
- Evaluation Criteria (Agents)
- **Non-Functional Requirements — always (best practice).** Security (credentials in Orchestrator / secret assets, least-privilege IS connection scope, don't expose entity calls in the network trace), performance (DB vs file, webhooks vs polling, avoid license-consuming Windows processes), scalability, availability, and logging / monitoring. Applies to every product; the API Workflow template already carries §Performance & Scaling + §Security & Authentication — other templates capture the equivalent under a Non-Functional Requirements subsection.
- **Reusable Components / Libraries — always (best practice).** List reused existing shared assets (tenant Libraries discovered in Phase 1 Step 2.5, Marketplace / org components, existing connectors) AND new reusable assets to build (shared workflows → an RPA **Library** routed to `uipath-rpa`; a missing integration → a **custom connector** routed to `uipath-connector-builder`), each built before its consumers. Assets used by 2+ projects live at the parent-folder / solution level. See [Component Placement Guide → Reusability & shared assets](../shared/component-placement-guide.md#reusability--shared-assets).
- **Testing Strategy — always thorough.** Cover happy path, edge cases, error scenarios, and (for Master Projects) end-to-end pipeline tests. Do NOT ask the user about test depth — depth is non-negotiable here. Implementation specialists may scope tests down at execution time if the user wants a quick MVP.
- **Next Steps — points at the build.** The genome `author` writes from the `ready` SDD is the implementation input; `design` writes no task list.

<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section, a task list, or implementation tasks created with the task-list tool. The genome `author` writes from the `ready` SDD is the implementation input. The SDD's `## Next Steps` section marks that boundary, and that is the entire `design` output surface.
<!--skill-flavor:phase3-output-surface:end-->

### Step 1.5: Resolve SME Review Items

Before finalizing the SDD (the skeleton is already on disk from Step 0), collect all `[SME REVIEW]` items. One item is one decision: the same gap marked in several sections is asked once. In autonomous mode, ask only the items with no defensible default (the candidates for `blocking`, rule 5), in one prompt; every other item stays in the Action Required table with its default applied. If there are any to ask:

> **Batching rule — 4-option cap per structured question.** Give each structured question at most 4 options. If there are 1-4 items, send one question. If there are 5-8 items, send a single structured prompt with **two questions** (each ≤4 options), grouped by SDD section. If there are more than 8 items, send one structured prompt per batch of up to 8 (two questions each), waiting for answers between batches. **Do not flatten >4 items into one question** — hosts that cap options reject it.

1. Batch them into one or more structured questions using numbered-choice format. Example for 1-4 items:

> Before I finalize the SDD, these items need your input:
>
> 1. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
> 2. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
>
> You can answer each, accept all defaults by replying "use defaults", or skip specific items.

2. Update the SDD sections with the user's answers.
3. If the user partially answers or asks follow-ups, do one more round (max 2 rounds total). After 2 rounds, keep remaining unresolved items as `[SME REVIEW]`, apply each item's recorded default in its section, and proceed to Step 2.
4. Any items the user explicitly skips remain as `[SME REVIEW]` in the final file with their defaults applied.
5. **Classify every surviving item:** `default-carried` (a recorded default is applied in its section — the normal case) or `blocking` — only when no defensible default exists AND the answer changes the architecture: the source says the platform is self-hosted but not which one (Automation Suite or standalone) while a selected product's availability differs between them — an unknown delivery model with no such signal is `unspecified — assumed cloud`, default-carried ([product-selection-guide.md](../shared/product-selection-guide.md) § Constraint Gate); an in-scope system has no access route the source or a default can supply (no API, no UI and no file interface known); the source's scope statements contradict each other and Level 0/1 could not resolve them; the user rejected the Level 1 recommendation without choosing an alternative. An access *detail* that is unknown (a mail protocol, an API version) takes its default and is default-carried. An item answered with "use defaults" stays `[SME REVIEW]`, default-carried: a default nobody with business knowledge confirmed is still a gap. Record the class in the Action Required table (Step 2 item 4). Blocking items keep the SDD at `Status: draft` (Step 2 item 8 rule 4).
6. If there are zero `[SME REVIEW]` items, skip this step entirely.

This step runs in BOTH Autonomous and Interactive modes — it is a hard blocker to producing a complete SDD. A caller's design request asks nothing here: every item keeps its default and class, and `blocking` items go to the caller in the result ([caller-request-guide.md](caller-request-guide.md) § The Run).

### Step 2: Finalize the SDD File(s)

1. Assemble all sections in template order. The Step 0 skeleton already holds the header + handoff + `## Decisions Made` / `## Recommended Scope` + Phase 1/2 sections — finalize it by appending/patching the remaining sections in template order rather than rewriting from scratch.
2. **Fill the `## Planner Handoff` header** that appears near the top of every template. Every template places it after `## Document History`. This is the load-bearing detection contract. § Choosing the Verb accepts **either** the heading OR the adjacent `<!-- planner-handoff:v1 -->` HTML marker as a detection signal — both ship in every template and both should survive into the generated file (so a later session, or a hand-written SDD, is still recognised as an SDD):

   The template holds the table; these fields carry rules beyond their placeholder:

   - **Status** — the first incremental write stamps `draft`; flip to `ready` ONLY after Step 1.5 ran (every surviving SME item classified `default-carried`) AND the item 8 template-superset check passes. A `blocking` SME item keeps `draft`. The genome is written only from `ready`.
   - **Execution autonomy**, **Delivery model** — from Phase 1 Step 0; append the Suite version when known (`automation-suite 2025.1`).
   - **Solution root SDD**, **Solution ID**, **Project SDD role**, **Independently executable** — solution scope ONLY, written into EVERY SDD (the root names itself; `root` in the overview, `child` in each per-project SDD; `Independently executable: no` on children, so a child is built only through the Solution root's genome). Omit all four for single-product.
   - **Genome** — never written by `design`: the genome turn adds it as the table's last row (Step 3 item 3).
   - **Template validation** — set to `passed` as soon as the item 8 template-superset check passes, whatever the `Status`: it records that every required section is present. A `draft` held by a blocking item is complete and reads `passed`; only an unfinished run leaves `pending`.

   Do NOT rename the heading or strip the marker. They are redundant on purpose — keeping both means a hand-edit of one signal does not silently break SDD detection.

   **Keep the `<!-- planner-sdd-body:v1 -->` line** the template places directly above the first body section, after the Table of Contents. It is not a template instruction: a caller's host reads every H2 above it as front matter ([caller-request-guide.md](caller-request-guide.md) § SDD Signals a Caller's Host May Read).

3. **Autonomous-mode Decisions Made block.** If `Execution autonomy: autonomous`, insert a `## Decisions Made` block immediately after the Planner Handoff header and before any `Action Required — SME Review Items` block or product body. It sits before the Table of Contents in every template. The block makes the highest-leverage architectural picks scannable in the SDD's first screenful so a reviewer can spot a wrong call without reading the whole document. In `Execution autonomy: interactive`, this block is optional — the user already reviewed each decision at the Phase 1/Phase 2 checkpoints. Skip the block for interactive runs.

   The template holds the table, row 1 always **Platform constraints**.

   Rules for the block:
   - Each "Picked" cell is a single concrete value, not a placeholder.
   - Each "One-sentence reason" is ≤ 20 words and cites the PDD signal or process characteristic that drove the pick.
   - Add one row for every further decision a guide sends to Decisions Made (a departure from a project shape the PDD names, a source-precedence override).
   - Row 1 always appears, even when nothing was blocked (`cloud; no products blocked`) — the reviewer must see which platform the architecture assumes.
   - For Solution scope, rows 3-5 repeat per RPA project (use a sub-table or one row per project — keep concise).
   - For non-RPA scopes (e.g., Single-product Agent), rows 3-5 are replaced by the template's own product row (framework choice, app type, trigger) — never `N/A` rows.
   - The block does NOT replace the per-section detail later in the SDD — the product body still carries the full justification in its architecture, stage/task, framework, or project-structure sections. The block is the **scannable index** of those decisions.

   In BOTH modes, also emit the `## Recommended Scope` block directly after `## Decisions Made` (directly after the Planner Handoff header when that block is absent — interactive runs): copy the Phase 1 summary's `Recommendation:`, `Delivery model:`, and `Blocked by platform:` lines (see [scope-recommendation-guide.md → Summary block](scope-recommendation-guide.md#summary-block)). Autonomous mode skips the Phase 1 presentation, so this copy is the only durable record of the Constraint Gate outcome.

4. If any `[SME REVIEW]` items remain, add a consolidated warning section after the Planner Handoff header (and after the `## Decisions Made` / `## Recommended Scope` blocks if present) and before the product body. This sits before the Table of Contents in every template:

```markdown
## Action Required — SME Review Items

| # | Section | Item | Question | Default applied | Blocking |
|---|---|---|---|---|---|
| 1 | <SECTION> | <ITEM> | <QUESTION> | <DEFAULT> | <yes/no> |

> These items are marked `[SME REVIEW]` in the document. Default-carried items (Blocking = no) do not block the genome or the build — the automation is built on the recorded defaults, which must be verified before production sign-off. Any Blocking = yes item keeps the handoff at `Status: draft`.
```

5. **Length follows content, never padding.** Every step, rule, exception, application and example the source states is kept — business rules all of them ([business-rules-guide.md](business-rules-guide.md) § 4). What is cut is restatement: a fact lives in one section and others name it; no template instruction, placeholder or empty example row survives; a table row replaces prose that says the same; a section the template makes conditional and whose condition does not hold is omitted.
6. **Re-run handling — already resolved at Step 0.** This check runs BEFORE the Step 0 skeleton write (that is the write that can clobber an existing file); by the time you reach here the answer is already applied, so do not re-ask. The question, for reference and for the Step 0 gate: if `<PROCESS_NAME_KEBAB>-sdd.md` already exists, ask the user with a structured question:

   First read the existing file's handoff `Status`:

   - **`Status: ready` (or no Status field — legacy):**

   > An SDD already exists at `<sdd-path>`. How should I proceed?
   >
   > 1. **Keep the existing SDD and stop** *(recommended)* — build from its genome, or run `author` on it when it has none
   > 2. **Regenerate from the PDD** — overwrites the existing SDD

   - **`Status: draft` (interrupted run):**

   > An unfinished SDD draft exists at `<sdd-path>` (interrupted generation). How should I proceed?
   >
   > 1. **Resume generation** *(recommended)* — finish the remaining sections, resolve SME items, run the completeness check, then flip Status to ready
   > 2. **Regenerate from the PDD** — discard the draft and start over
   > 3. **Generate alongside as `<name>-v2-sdd.md`** — for diffing

   Default is "keep" — overwriting an SDD the user might have hand-edited is the more destructive action.
   - **A draft at another path to finalize** (`<name>.draft.md`, or a draft the user names): no question. The draft is the settled design — read it whole, write the final at its basename minus `.draft` (a path the user names wins) from Step 0 onwards, and keep the draft on disk. Never add, drop or rename a business element: every element of the draft's inventory (projects, steps, stages, tasks, variables, rules) and every expression appears in the final, verbatim. The product guide's draft repairs are the only other change (Case Management: [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Finalizing a Case Draft).

7. Write the output file(s) to the current working directory. If the user specified an output path for the SDD, use it instead of these defaults:
   - **Single-product scope:** one file at `<PROCESS_NAME_KEBAB>-sdd.md`.
   - **Solution scope:** the solution overview at `<SOLUTION_NAME_KEBAB>-solution-sdd.md` PLUS one per-project SDD at `<PROJECT_NAME_KEBAB>-sdd.md` for each project in the unified project list. Put the `[SME REVIEW]` warning block in the solution overview AND in any per-project file where a review item lives in that project. Each per-project SDD gets its own `## Planner Handoff` header.

8. **Template-superset check (mandatory before the item 9 summary).** After writing each SDD file, re-read it and extract every H2 (`## `) and H3 (`### `) heading. Compare against the template's Table of Contents and required subsections. The generated SDD's heading set MUST be a superset — extra subsections are fine, missing template sections are an SDD defect. A template heading is not required when the template itself makes it conditional: an alternative the design did not pick ("Generate EITHER Option A OR Option B — delete the other"), and a subsection whose own note sets a condition that does not hold ("Include only when…", "omit when…", "Master Project only"). A subsection the template repeats per sub-project ("repeat this section per sub-project") may sit one heading level deeper. Every other template H2 and H3 is required.

   Minimum required H2 headings per template:
   - **RPA template:** every H2 its Table of Contents lists; §12 Queue Architecture may be omitted only when the design defines or consumes no Orchestrator queue.
   - **Case template:** §1 Case Definition, §2 Stages & Tasks, §3 Personas & App Views, §4 Integrations, plus the unnumbered H2s `## Document History`, `## Planner Handoff`, `## Table of Contents`, `## Non-Functional Requirements`, `## Testing Strategy`, `## Next Steps`. Also verify every modeled stage has a `### Stage ...` or `### Secondary Stage ...` block, every modeled task has a `##### Task ...` detail block, and every task detail block contains the exact marker `**Task envelope**` before its Required / Run Only Once / Skip Condition table. Then walk [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § SDD Conformance Checklist against the file (items 30–33 only when finalizing a draft); `Template validation: passed` needs every item PASS.
   - **Other templates:** every H2 the template's Table of Contents lists.

   The SDD's own Table of Contents then lists exactly the H2 sections the SDD has: an omitted conditional section leaves no entry behind.

   For any missing required H2:
   1. Regenerate that section from the template + Phase 1 extraction data + Phase 2 architecture.
   2. If the template's contents for that section depend on a Phase 1 / Phase 2 input that is genuinely absent (e.g. §4 Business Rules but the PDD has zero rule signals), emit the section with an explicit "No business rules extracted from the PDD" note plus an `[SME REVIEW]` row asking the user to supply any.
   3. Never silently drop a section.
   4. **Ready flip — the final write of `design`.** When every required heading is present and every remaining `[SME REVIEW]` item is classified `default-carried` (Step 1.5 rule 5), update the handoff: `Status: ready` (`Template validation: passed` is already set — item 2). Open default-carried items do NOT block ready — they gate production sign-off, not the genome or the build. Any `blocking` item keeps `Status: draft` with `Template validation: passed`; the item 9 summary names it and asks. Skipping the flip leaves the file at `draft` and `author` will refuse to write its genome.

   Common slip-fail: skipping §4 Business Rules because the PDD has no dedicated "Business Rules" section. Rules are usually buried in "Remarks", step descriptions, or screenshots — the PDD analysis guide's "Embedded business rules" pointer applies. Treat zero rules in §4 as a regeneration trigger, not a finished section.

9. Output a summary in the conversation. A caller's design request replaces it with the `planner-design-result: v1` block, its prose in the request's `audience` ([caller-request-guide.md](caller-request-guide.md) § The Result):

```markdown
## SDD Generated

<FILENAME_1> — <COUNT> sections, <LINE_COUNT> lines
<FILENAME_2> — <COUNT> sections, <LINE_COUNT> lines
...

<SME_REVIEW_COUNT> open SME review items (if any — list each with its class and default).

**Next — branch on the handoff `Status`:**
- `ready` — `design` is complete and the SDD is on disk. The genome is written from it on the next turn (Step 3), then `uipath-build-from-genome` builds it when the request is to build; open default-carried SME items travel into the genome as `*[Inferred]*` assumptions — confirm them before production. A design a build skill handed over gets no genome.
- `draft` (blocking SME items) — Blocked on: <BLOCKING_ITEMS>. Answer these and the SDD finalizes to `ready`; no genome is written until then.
```

### Step 3: Next Turns — the Genome, then the Build

**A caller's request with `stop-after: sdd` skips this whole step**, the turn boundary included: its result ends the run in the same turn and the caller continues ([caller-request-guide.md](caller-request-guide.md)).

<!--skill-flavor:design-deliverable:start-->
The SDD is the deliverable of `design`. **Do not generate an Implementation Plan section inside the SDD. Do not create implementation tasks with the task-list tool during `design`. Do not start executing.**
<!--skill-flavor:design-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin the genome or the build in the same turn as `design`.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue on the **next** turn with the sequence below. Rationale: `design` (read PDD + guides, author §1–§18), `author` (read the SDD, write and self-review the genome) and the build (`uipath-build-from-genome`: configuration questions, then every component through its owning skill) are each heavy; stacking two of them in one unbroken autonomous turn is what pushes a turn past the host's time or context limit and loses the whole run. Yielding after each durable write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** a structured question — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->

Then continue:

1. **`Status: draft`** (a blocking SME item) → no genome and no build. The item 9 summary names the blocking items. The turn that receives the user's answers patches them into the SDD, reruns the superset check and flips it to `ready` as its last write, then ends; the genome (item 3) runs on the following turn.
2. **A design a build skill handed over** → no genome and no build: § Design Handed Over by a Build Skill returns it to the caller.
3. **Next turn — the genome.** Run the `author` verb on the `ready` SDD ([genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md)); its items 2 and 7 set the follow-up rounds, the genome's name and the `Genome` handoff row. Write the genome even when `uipath-build-from-genome` is not installed, and say that building from it needs `uipath-build-from-genome`. The genome write is a turn boundary too: end the turn after `author`'s summary.
4. **Turn after — the build, or stop.** The request's intent decides, never the execution mode — in both modes:
   - The intent implies implementation ("create / build / implement / set up / make", "so we can build it", "ready to build") → invoke `uipath-build-from-genome` with the genome path on the turn after the genome, without asking — do not add a "shall I build?" question here. It asks its own configuration questions (an SDD's `Execution autonomy` never waives them), builds every component through its owning skill and ends with the hand-off folder. A request that also asks to publish or deploy follows [SKILL.md](../../SKILL.md) § Chaining. `uipath-build-from-genome` not installed → stop after the genome; `author`'s summary says the build needs it.
   - The user only asked to "design / architect / generate an SDD", or the intent is unclear → stop after the genome in either mode; the SDD and the genome are the deliverable. Offer the build in one line of `author`'s summary.

## Design Handed Over by a Build Skill

A build skill that finds no SDD to build from hands its request here (`uipath-maestro-case`: SKILL.md Choosing the Verb item 3), in the same conversation. `design` runs as for any request, with three differences:

1. **The output path is the caller's** — `sdd.md` at the working root for `uipath-maestro-case`. Never overwrite an existing file there: stop and say it exists.
2. **The Phase 2 Step 5 review carries the caller's build options** (case: [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Presenting the Case Design). The answer is the build consent; it is never asked again.
<!--skill-flavor:build-handoff-row:start-->
3. **The write does not end the turn and gets no genome:** after the `ready` flip, the caller's build starts in this conversation (`uipath-maestro-case`: `uip solution init` and its Phase 1), verifying the identities the SDD resolved instead of re-discovering them.
<!--skill-flavor:build-handoff-row:end-->

## Client Word Document

<!--skill-flavor:client-word-document:start-->
Only on request: an official client template, a Word SDD / ASDD, a `.docx`. Run it after the SDD is on disk, from the markdown SDD, following [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md). The markdown SDD stays as-is: the client document is a separate file beside it, and its section structure is the customer's template, never this skill's.
<!--skill-flavor:client-word-document:end-->
