# SDD Writing Guide — Phase 3 of `design`

Phase 3 of `design` writes the full SDD to disk incrementally, resolves the SME items, checks it against its template and flips it to `ready`. The SDD is the deliverable: a genome is written from it only on demand — when the user asks for one or asks to build, since the build starts from the genome (Step 5). Reached from [design-guide.md](design-guide.md) once Phase 2 is approved — that guide's § Verb Rules and its Phase 1 / Phase 2 results apply throughout. Read this guide whole before the first Phase 3 write.

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| Step 2 | filling the template's Business Rules section (RPA §4, BPMN §3, Case § Business Rules, Flow §9, API workflow §7, Coded app §9, Agent §2), and [business-rules-guide.md](business-rules-guide.md) is not yet open from Phase 2 | [business-rules-guide.md](business-rules-guide.md) |
| Step 4 item 4 | an `[SME REVIEW]` item remains | [open-questions-guide.md](../shared/open-questions-guide.md) whole |
| Step 5, next turn | the SDD is `Status: ready`, no build skill handed the design over, and the request or a later message asks for its genome or a build (Step 5 item 3) | [author-guide.md](../author/author-guide.md) whole — the `author` verb; its § Read Plan names the rest |
<!--skill-flavor:client-word-read-row:start-->
| § Client Word Document | the user asks for the client-facing Word SDD / ASDD (their official template, a `.docx`) | [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) whole |
<!--skill-flavor:client-word-read-row:end-->

## Writing Rules

Every sentence of an SDD obeys these. Step 2 writes by them; the Step 4 item 8 wording check re-reads the file against them.

1. **Defaults fill gaps, never override the source.** A `[DEFAULT]` never contradicts a value the source states (a schedule, an order of steps, a system it names). It never adds a limit nothing in the source implies (a run cap, a stop count, a polling cadence) — the build skill's own defaults cover those. A step order the source states is kept; a reorder is an `[SME REVIEW]` alternative, never the applied default.
2. **Behavioural wording: what each part must do, never how its product does it.** The skill that builds a part owns how its product works (Critical Rule 5); a template's own instructions are all an SDD states about a product. Every other sentence says what must hold, in the business's terms:
   - **a failure** — rule 7;
   - **a human step** — who acts, each decision they can take and where the work goes after it, what they see and what they enter; never a form type, a button or how an outcome is wired;
   - **an integrated component** — what it receives, what it returns and when it is called; never its files, its commands, how it is packaged or deployed, or what else its project holds;
   - **a non-functional need** — what must hold and for which data, by name (the fields that must not be shown or kept, and where); never that a product's logs, history or storage honour it.
3. **What the design needs a product to be able to do is a Build Assumption, never a fact.** When a step works only if a product can do something no template states, write one row in the template's `### Build Assumptions`. Such a capability: read a format, be called from this host, take a file from where it arrives, keep data out of a record the platform stores, hand a file or record to a part another skill builds in the form that part takes. The row holds:
   - what the design relies on;
   - the nodes that rely on it;
   - the skill that confirms it at build;
   - what the design does instead when it does not hold, down to the extra step or component that fallback needs.

   A capability the source or a `facts` file asserts of a product is a row too: the owning skill confirms it, never the source. A design that relies on nothing unconfirmed writes `None.`
4. **A property the SDD claims of a run is checked against its own inventory before it is written.**
   - *Does not wait for people*: no human step lies on that path.
   - *Per item*: every step and gateway said to run per item is inside the loop that iterates the items, listed in its row.
   - *Rules only*: every decision names the table or rule that makes it, and every table names the component that runs it.
   - *Collected from the items*: the inventory names where each item's result is kept until the step that reads them all.
   - Every other behaviour the SDD promises of a run — one run at a time, a failure alerted or logged, work held until something arrives, a write made last — names the node that performs it.

   A claim the inventory does not bear out is a design defect: add the node, make it a Build Assumption, or drop the claim.
5. **A build prerequisite is named as one.** An item about something the build needs to exist first (a connection, a deployed component) names it as a prerequisite of the build. A connection not yet provisioned is an `[SME REVIEW]` item that names it as a prerequisite.
6. **A document extraction model (IXP) lists what it reads.** List each business document with the format it arrives in and the fields to extract. Sorting documents by kind, and bringing a document to where the model reads it, are steps of their own — never part of the model row. Two Build Assumptions rows go with every model:
   - that it reads each listed format — one row per format that is not a PDF or a scan, with the conversion step the design falls back on;
   - that each document reaches it in the form it takes from the step that received it.

   A document that arrives inside a message or a connector response is saved by a step of the inventory, before the first step that reads it, to where that step reads it. The save is a step, never only a Build Assumption.
7. **A failure states its attempts, its wait and its end.** Write the attempts worth making, the wait between them and what happens when they run out ("three attempts a minute apart, then the instance fails and support is alerted"). Attempts are a number and a wait, or none — never "the platform's policy" or a default. A failure a person resolves is a human step, not an error row.
8. **Work the source states of each item runs once per item.** When a rule, check, exception or decision applies to each item of a batch (each invoice, each unit, each line, each attachment), the design iterates the items. One loop or multi-instance scope holds every step from the first per-item read to the last per-item decision, and its row names what it iterates and where each item's result is kept until the step that reads them all (rule 4). Items the source nests (units within a system) are iterated with that nesting. A gateway that routes the whole batch on one item's outcome, or a loop around one step of several per-item steps, is a design defect.
9. **Every system, connection and service the design names comes from somewhere.** It is in the source, the tenant or connector lookup returned it, or a template or guide pattern calls for it. A need nothing names ("a worklist", "an alert channel") is written as the need, with an `[SME REVIEW]` item asking which system serves it; never an invented connector or service name. Data the platform holds itself (Data Fabric entities, storage buckets, queues) is read and written through its own nodes and activities, never through an Integration Service connection.
10. **A number or guarantee nobody stated is not written.** A speed ("sub-second"), a volume, an availability, idempotency or exactly-once delivery appears only when the source states it. A need for one is an `[SME REVIEW]` item.

## Phase 3 — Full SDD Generation

### Step 1: Write the SDD Skeleton to Disk — Hard Gate

**Write the file to disk now, before generating any Phase 3 section.** This is an action, not advice: Step 2 does not begin until a file write has created the SDD file (Step 4 item 7 resolves the path and the Solution-scope file set). Do NOT hold the entire SDD in context and write only at the very end.

**A lighter request keeps the template's shape.** A request that limits effort — a draft (`*.draft.md`), a first pass, "a version to review", "keep it compact", "just the outline", "don't polish or validate it yet" — sets how much detail each block carries, never which blocks exist. Write every heading, table and per-item block the product template defines, one block per item it inventories (each project, step, stage, task, gateway, integration), and every trigger, entry, exit and business rule as the executable condition the template asks for. Missing detail is shorter prose or an `[SME REVIEW]` marker inside its block. Never merge per-item blocks into one summary table, drop a section because it is thin (one with nothing to record says so), or leave a rule only in prose. Every later step — finalize, the template check, the genome — adds detail to the structure the SDD already has and cannot rebuild a structure it never had. A Case Management draft is checked before the turn ends: `node "<SKILL_DIR>/scripts/case-sdd-check.mjs" --draft "<NAME>.draft.md"` prints `OK` — its first line `# SDD — <Case Name>` (never `# SDD Draft — …` or `# <Name> — Solution Design Draft`), `## Section 1: Case Definition` with its `### Case Variables`, `## Section 2: Stages & Tasks`, and a `### Stage <N>: <Name>` block for every primary stage the source names, a `### Secondary Stage: <Name>` block per lane; repair each `FAIL:` line in place and run it again.

**First, run the collision check — the skeleton write is the write that can clobber.** Before writing anything, check each target file (Step 4 item 7). When one already exists, read its handoff `Status` and ask with a structured question:

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

Honour the answer here. "Keep the existing SDD and stop" ends `design` with no write at all; default is keep, since the user may have hand-edited the file. "Resume generation" patches the existing draft instead of overwriting it. Only "Regenerate" and the no-file-exists case write a fresh skeleton. A caller's `existing-output: replace` is the answer "Regenerate": ask nothing ([caller-request-guide.md](caller-request-guide.md)). A draft at another path to finalize gets no question (Step 4 item 6).

The skeleton write contains, in this order:

1. The title/header + `## Document History`.
2. Both handoff signals, with `Status: draft` and `Template validation: pending` (Step 4 item 2) — in this first write, so a partial file is still detected.
3. The rest of the template's front matter, in its order (Step 4 item 3).
4. Every Phase 1 / Phase 2 section you already have.

Then append the remaining Phase 3 sections to that file with follow-up file edits or writes **as you generate them** — do not buffer them in context and do not rewrite the whole file per section.

Step 3 and the Step 4 superset check patch and verify the file already on disk; the `ready` flip (Step 4 item 9) is the last write of `design`.

### Step 2: Generate Remaining Sections

Write every section by [§ Writing Rules](#writing-rules).

Fill in all sections of the chosen template not covered in Phase 1 or Phase 2. Section assignments per phase:

**Phase 1 produces (for all templates):**
- Header & Document History (process name, today's date, version 1.0; the title as the template writes it). When the Phase 1 Step 10 interview ran, a second Document History row, as [interview-guide.md](../interview/interview-guide.md) § Where Answers Go words it.
- Overview section (§1)
- Process/Flow/Lifecycle diagram (§2 for most templates)
- Detailed steps / nodes description where applicable

**Phase 2 produces:** See [design-guide.md](design-guide.md) Phase 2 Step 2 (template-specific architectural core)

**Phase 3 produces:** All remaining sections — typically:
- Business Rules (every template; its home per rule type: [Business Rules Guide § Homes per template](business-rules-guide.md#homes-per-template))
- Value Mappings (RPA)
- Exception / Error Handling (all)
- Credentials & Assets (RPA)
- Deployment Environment (RPA — Orchestrator, Studio/Robot versions, environments, scalability; robot type lives in §11 Project Mode Decision). Fill the Orchestrator row from the Step 1 delivery model (Cloud / Automation Suite + version / standalone); fill `[SME REVIEW]` for the rest when the PDD does not specify — these fields typically come from the deployment team, not the PDD. Never invent VM names, version pins, or robot types.
- Triggers (Flow)
- Evaluation Criteria (Agents)
- **Non-Functional Requirements — always.** Each worded per [§ Writing Rules](#writing-rules) rule 2:
  - security — which credentials and data must be protected and from whom; each part reaches only the systems and data it needs; the fields that must not be shown or kept, and where;
  - performance — how fast each path must respond and how much it must handle;
  - scalability;
  - availability;
  - logging / monitoring.

  Applies to every product; the API Workflow template carries §Performance & Scaling and §Security & Authentication — other templates capture the equivalent under a Non-Functional Requirements subsection.
- **Reusable Components / Libraries — always (best practice).** List both, each built before its consumers:
  - reused existing shared assets (tenant Libraries discovered in Phase 1 Step 5, Marketplace / org components, existing connectors);
  - new reusable assets to build (shared workflows → an RPA **Library** routed to `uipath-rpa`; a missing integration → a **custom connector** routed to `uipath-connector-builder`).

  Assets used by 2+ projects live at the parent-folder / solution level. See [Component Placement Guide → Reusability & shared assets](../shared/component-placement-guide.md#reusability--shared-assets).
- **Testing Strategy — always** ([design-guide.md](design-guide.md) Verb Rule 5); never ask the user about test depth.
- **Next Steps — points at the build** ([design-guide.md](design-guide.md) Verb Rule 2).

### Step 3: Resolve SME Review Items

Before finalizing the SDD (the skeleton is already on disk from Step 1), collect all `[SME REVIEW]` items. One item is one decision: the same gap marked in several sections is asked once. When the Phase 1 Step 10 interview ran, ask only the items whose answerer is one of the user's roles ([interview-guide.md](../interview/interview-guide.md) § Asking rule 1), and none the interview put to the user: an item not asked keeps its default, or is `blocking` when it has none (rule 5). Otherwise every item is asked. In autonomous mode, ask only the items with no defensible default (the candidates for `blocking`, rule 5), in one structured question; every other item stays in the Action Required table with its default applied. If there are any to ask:

> **Batching rule.** One item per question, with the item's own options (the default applied first) or its default named, within the caps of [SKILL.md § Prompt Budget](../../SKILL.md#prompt-budget). Items beyond one structured question take further ones, grouped by SDD section, waiting for answers between them. Never drop an item to fit a prompt.

1. Batch them into one or more structured questions. Example for 1-4 items:

> Before I finalize the SDD, these items need your input:
>
> 1. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
> 2. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
>
> You can answer each, accept all defaults by replying "use defaults", or skip specific items.

2. Update the SDD sections with the user's answers.
3. If the user partially answers or asks follow-ups, do one more round, within the round cap of [SKILL.md § Prompt Budget](../../SKILL.md#prompt-budget). After the last round, keep remaining unresolved items as `[SME REVIEW]`, apply each item's recorded default in its section, and proceed to Step 4.
4. Any items the user explicitly skips remain as `[SME REVIEW]` in the final file with their defaults applied.
5. **Classify every surviving item** `default-carried` (a recorded default is applied in its section — the normal case) or `blocking`. An item is `blocking` only when no defensible default exists AND the answer changes the architecture — one of these:
   - the source says the platform is self-hosted but not which one (Automation Suite or standalone), and a selected product's availability differs between them. An unknown delivery model with no such signal is `unspecified — assumed cloud`, default-carried ([product-selection-guide.md](../shared/product-selection-guide.md) § Constraint Gate);
   - an in-scope system has no access route the source or a default can supply (no API, no UI and no file interface known);
   - the source's scope statements contradict each other and Level 0/1 could not resolve them;
   - the user rejected the Level 1 recommendation without choosing an alternative.

   An access *detail* that is unknown (a mail protocol, an API version) takes its default and is default-carried. An item answered with "use defaults" stays `[SME REVIEW]`, default-carried: a default nobody with business knowledge confirmed is still a gap. Record the class in the Action Required section (Step 4 item 4). Blocking items keep the SDD at `Status: draft` (Step 4 item 9).
6. If there are zero `[SME REVIEW]` items, skip this step entirely.

This step runs in BOTH Autonomous and Interactive modes — it is a hard blocker to producing a complete SDD. A caller's design request asks nothing here: every item keeps its default and class, and `blocking` items go to the caller in the result ([caller-request-guide.md](caller-request-guide.md) § The Run).

### Step 4: Finalize the SDD File(s)

1. Assemble all sections in template order. The Step 1 skeleton already holds the header, the handoff, the template's front matter and the Phase 1/2 sections — finalize it by appending/patching the remaining sections in template order rather than rewriting from scratch.
2. **Fill the `## Planner Handoff` header** — every template places it after `## Document History`, with the `<!-- planner-handoff:v1 -->` marker beside it. These two handoff signals are the detection contract: § Choosing the Verb accepts **either** one, and every SDD keeps both:

   The template holds the table; these fields carry rules beyond their placeholder:

   - **Status** — the first incremental write stamps `draft`; flip to `ready` ONLY after Step 3 ran (every surviving SME item classified `default-carried`) AND the item 8 template-superset check passes (item 9). A `blocking` SME item keeps `draft`. The genome is written only from `ready`.
   - **Execution autonomy**, **Delivery model** — from Phase 1 Step 1; append the Suite version when known (`automation-suite 2025.1`). `Execution autonomy` governs only how the SDD and its genome are written — checkpoint stops, Decisions Made, the genome's follow-up rounds; it never answers or waives a question of `uipath-genome`.
   - **Solution root SDD**, **Solution ID**, **Project SDD role**, **Independently executable** — solution scope ONLY, written into EVERY SDD (the root names itself; `root` in the overview, `child` in each per-project SDD; `Independently executable: no` on children, so a child is built only through the Solution root's genome). Omit all four for single-product.
   - **Genome** — never written by `design`: a genome written on demand adds it as the table's last row (Step 5 item 3).
   - **Template validation** — set to `passed` as soon as the item 8 template-superset check passes, whatever the `Status`: it records that every required section is present. A `draft` held by a blocking item is complete and reads `passed`; only an unfinished run leaves `pending`.

   Never rename the heading or strip the marker.

   **Keep the `<!-- planner-sdd-body:v1 -->` line** the template places directly above the first body section, after the Table of Contents. It is not a template instruction: a caller's host reads every H2 above it as front matter ([caller-request-guide.md](caller-request-guide.md) § SDD Signals a Caller's Host May Read).

3. **Decisions Made block.** Write it when `Execution autonomy` is `autonomous` or the run is a caller's design request; a template that makes it a body chapter (BPMN §10 Design Decisions) writes it in every mode. Write it where the template places it. It makes the highest-leverage architectural picks scannable.

   The template holds the table, row 1 always **Platform constraints**.

   Rules for the block:
   - Each "Picked" cell is a single concrete value, not a placeholder.
   - Each "One-sentence reason" is ≤ 20 words and cites the PDD signal or process characteristic that drove the pick.
   - Add one row for every further decision a guide sends to Decisions Made (a departure from a project shape the PDD names, a source-precedence override).
   - Row 1 always appears, even when nothing was blocked (`cloud; no products blocked`) — the reviewer must see which platform the architecture assumes.
   - RPA scope also carries row 6, **Attendance / Initiation**: who runs the process and what starts it, two answers, copied to §11 Project Mode Decision's Attendance and Initiation columns.
   - For Solution scope, rows 3-6 repeat per RPA project (use a sub-table or one row per project — keep concise).
   - For non-RPA scopes (e.g., Single-product Agent), rows 3-5 are replaced by the template's own product row (framework choice, app type, trigger) — never `N/A` rows. A Flow or BPMN SDD also carries the **Maestro engine** row: the row-5 structures the process needs, counted ([product-selection-guide.md § Maestro disambiguation](../shared/product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case)); two or more on a Flow template means the wrong template — rewrite it on the BPMN template.
   - The block does NOT replace the per-section detail later in the SDD — the product body still carries the full justification in its architecture, stage/task, framework, or project-structure sections. The block is the **scannable index** of those decisions.

   In both modes, also write the Recommended Scope block where the template places it: copy the Phase 1 summary's `Recommendation:`, `Delivery model:`, `Blocked by platform:`, and `Need profile:` lines (see [scope-recommendation-guide.md → Summary block](scope-recommendation-guide.md#summary-block)). Autonomous mode skips the Phase 1 presentation, so this copy is the only durable record of the Constraint Gate outcome. Then run `node "<SKILL_DIR>/scripts/scope-check.mjs" "<SDD_PATH>"` on every SDD file written; a `FAIL:` line is a defect — fix the line or table it names (`Blocked by platform:`, `Need profile:`, an RPA SDD's §11 `### Project Mode Decision`) and rerun until it prints `OK`.

4. If any `[SME REVIEW]` items remain, add the `## Action Required — SME Review Items` section where the template places it. It is written in the item form of [open-questions-guide.md](../shared/open-questions-guide.md), one item per decision, as the template's block shows:
   - each item is numbered `D1`, `D2`, … in the order of the sections it concerns;
   - its marker in the body names it (`[SME REVIEW] D2: <note>`);
   - a `default-carried` item lists its options, the default applied marked `(built now)`, or as a value its `Default:`. For a value or material nobody has yet (a production amount, sample documents), the `Default:` is what the design builds until it arrives (an empty setting, a placeholder document), never an invented value;
   - a `blocking` item has no default: an `Until answered:` line in its place;
   - each ends on `Answer (by <role>):`.

   Where the SDD's items land in one genome file, the genome keeps each item's id on the entry it carries the item into ([genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md) item 6). Once the genome exists, the section is written again from it ([sdd-from-genome-guide.md](../shared/sdd-from-genome-guide.md) item 6).

5. **Length follows content, never padding.** Every step, rule, exception, application and example the source states is kept — business rules all of them ([business-rules-guide.md](business-rules-guide.md) § 4). What is cut is restatement: a fact lives in one section and others name it; no template instruction, placeholder or empty example row survives; a table row replaces prose that says the same; a section the template makes conditional and whose condition does not hold is omitted.
6. **Re-run handling** — Step 1 resolved it; never ask again.
   - **A draft at another path to finalize** (`<name>.draft.md`, or a draft the user names): no question. The draft is the settled design — read it whole, write the final at its basename minus `.draft` (a path the user names wins) from Step 1 onwards, and keep the draft on disk. Never add, drop or rename a business element: every element of the draft's inventory (projects, steps, stages, tasks, variables, rules) and every expression appears in the final, verbatim. The template's draft rules, when its Validation footer holds them, are the only other change.

7. Write the output file(s) to the current working directory. If the user specified an output path for the SDD, use it instead of these defaults:
   - **Single-product scope:** one file at `<PROCESS_NAME_KEBAB>-sdd.md`.
   - **Solution scope:** the solution overview at `<SOLUTION_NAME_KEBAB>-solution-sdd.md` PLUS one per-project SDD at `<PROJECT_NAME_KEBAB>-sdd.md` for each project in the unified project list. Put the `[SME REVIEW]` warning block in the solution overview AND in any per-project file where a review item lives in that project. Each per-project SDD gets its own `## Planner Handoff` header.

8. **Template-superset check (mandatory before the item 9 ready flip).** After writing each SDD file, re-read it and extract every H2 (`## `) and H3 (`### `) heading. Compare against the template's Table of Contents and required subsections. The generated SDD's heading set MUST be a superset — extra subsections are fine, missing template sections are an SDD defect. A template heading is not required when the template itself makes it conditional:
   - an alternative the design did not pick ("Generate EITHER Option A OR Option B — delete the other");
   - a subsection whose own note sets a condition that does not hold ("Include only when…", "omit when…", "Master Project only").

   A subsection the template repeats per sub-project ("repeat this section per sub-project") may sit one heading level deeper. Every other template H2 and H3 is required. An RPA SDD's §11 Project Structure always carries `### Project Type`, `### Project Mode Decision` (its ten-column table, one row per project) and `### Recommended Structure`, for a Single Project too; `scope-check.mjs` fails one whose Project Mode Decision is missing or compressed.

   **A Case Management SDD** is first run through `node "<SKILL_DIR>/scripts/case-sdd-check.mjs" "<NAME>.md"` (a `*.draft.md` takes `--draft`); each `FAIL:` line is a defect in the file: repair it in place and run it again until it prints `OK`.

   **A template whose Validation footer holds a conformance checklist** is checked against it in the same pass, after the headings:
   1. **When:** against the written file, before the `Status: ready` flip, in every mode.
   2. **Who:** a read-only subagent when the host has one — it returns the PASS/FAIL table and the parent edits; otherwise inline, in the transcript.
   3. **How:** read the written file once. Answer every item PASS or FAIL with one verbatim quote from the file — the line that violates (FAIL) or the line that satisfies (PASS). Judge structure by the role and position of a block (which heading level, which table, which column), not by prose wording.
   4. **Repair:** fix every FAIL with a targeted edit, then answer only the failed items again — at most 3 rounds, then stop and present what remains.

   `Template validation: passed` needs every heading present, every checklist item PASS and `br-coverage.mjs` printing `OK` (below).

   The SDD's own Table of Contents then lists exactly the H2 sections the SDD has: an omitted conditional section leaves no entry behind.

   **Wording check, in the same pass.** Re-read every section below `<!-- planner-sdd-body:v1 -->` for a sentence that says how a UiPath product behaves, is configured, is laid out on disk or is commanded, beyond the template's own instructions. Reword each as what must hold, move it to Build Assumptions, or delete it ([§ Writing Rules](#writing-rules)). Then check each property claimed of a run against the inventory once more (§ Writing Rules rule 4), and that every per-item rule sits inside its loop (rule 8).

   **Consistency check, in the same pass.** Every step name, rule ID, exception ID and decision reference (`D3`) in the body names the one place that defines it, and means what that place and the source mean by it: an exception the PDD defines keeps the PDD's trigger and handling. Every route in the diagram matches the inventory, the human-step section and the tests. Every step, rule and exception of the source appears. Fix each mismatch where it is wrong, never by deleting the reference. `Template validation: passed` records that the sections are present, worded this way and consistent; it never certifies that a product can do what a Build Assumption names.

   For any missing required H2:
   1. Regenerate that section from the template + Phase 1 extraction data + Phase 2 architecture.
   2. If the template's contents for that section depend on a Phase 1 / Phase 2 input that is genuinely absent (e.g. §4 Business Rules but the PDD has zero rule signals), emit the section with an explicit "No business rules extracted from the PDD" note. With that note, add an `[SME REVIEW]` row asking the user to supply any.
   3. Never silently drop a section.

   **Business rules, in the same pass.** Run `node "<SKILL_DIR>/scripts/br-coverage.mjs" --source "<PDD_PATH>" "<SDD_PATH>" [<CHILD_SDD_PATH> ...]` on every SDD file of the design ([business-rules-guide.md](business-rules-guide.md) § 4); each `FAIL:` line is a rule lost, cited by its ID alone or renumbered: repair it in its home and run it again until it prints `OK`. `Template validation: passed` needs it, in every template. A source that is not a text file takes the guide's check by hand.

   Every template: a source with no dedicated rules section still holds rules (remarks, step descriptions, screenshots — the PDD analysis guide's "Embedded business rules"), so zero extracted rules is a regeneration trigger, not a finished section.

9. **Ready flip — the final write of `design`.** When every required heading is present, `br-coverage.mjs` prints `OK`, and every remaining `[SME REVIEW]` item is classified `default-carried` (Step 3 rule 5), update the handoff: `Status: ready` (`Template validation: passed` is already set — item 2). Open default-carried items do NOT block ready — they gate production sign-off, not the genome or the build. Any `blocking` item keeps `Status: draft` with `Template validation: passed`; the item 10 summary names it and asks. Skipping the flip leaves the file at `draft` and `author` will refuse to write its genome.

10. Output a summary in the conversation. When items are open, it counts them by the role that answers them and names `interview <SDD_PATH>` as the way to have them asked. A caller's design request replaces it with the `planner-design-result` block, its prose in the request's `audience` ([caller-request-guide.md](caller-request-guide.md) § The Result):

```markdown
## SDD Generated

<FILENAME_1> — <COUNT> sections, <LINE_COUNT> lines
<FILENAME_2> — <COUNT> sections, <LINE_COUNT> lines
...

<SME_REVIEW_COUNT> open SME review items (if any — list each with its class and default).

**Next — branch on the handoff `Status`:**
- `ready` — `design` is complete and the SDD is on disk. Open default-carried SME items gate production sign-off — confirm them before production. <REQUEST ASKED FOR A GENOME OR A BUILD: "The genome, the step-by-step build specification a coding agent follows, is written from it on the next turn, then <the build, which asks only the setup questions this SDD does not already answer, first offering to take the defaults it carries | nothing more>."> <OTHERWISE: one line offering the genome and the build: "Ask for its genome to get the build blueprint, or to build it."> A design a build skill handed over gets no genome.
- `draft` (blocking SME items) — Blocked on: <BLOCKING_ITEMS>. Answer these and the SDD finalizes to `ready`; no genome is written until then.
```

### Step 5: Next Turns — the Genome and the Build, on Demand

**A caller's request with `stop-after: sdd` skips this whole step**, the turn boundary included: its result ends the run in the same turn and the caller continues ([caller-request-guide.md](caller-request-guide.md)).

The SDD is the deliverable of `design` ([design-guide.md](design-guide.md) Verb Rule 2). **Do not start executing.**

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin the genome or the build in the same turn as `design`.** Once the SDD is on disk, the superset check has passed, and the Step 4 item 10 summary is emitted, end the turn. When the request asked for a genome or a build, continue on the **next** turn with the sequence below. This is a turn checkpoint, **not** a structured question — do not prompt the user.
<!--skill-flavor:turn-boundary:end-->

Then continue:

1. **`Status: draft`** (a blocking SME item) → no genome and no build. The Step 4 item 10 summary names the blocking items. The turn that receives the user's answers patches them into the SDD, reruns the superset check and flips it to `ready` as its last write, then ends; the genome (item 3), when asked for, runs on the following turn.
2. **A design a build skill handed over** → no genome and no build: § Design Handed Over by a Build Skill returns it to the caller.
3. **The genome — only on demand.** It is written when the request, or a later message, asks for the genome ("write its genome", "the blueprint"). It is also written for a build ("create / build / implement / set up / make", "so we can build it", "ready to build"), since the build starts from the genome. A request that only asks to "design / architect / generate an SDD", or whose intent is unclear, gets no genome: stop after the SDD in either mode, with the Step 4 item 10 summary's one-line offer. When the next message asks for an SDD change, apply it to the SDD first (`revise`: change only the sections the request touches, then rerun Step 4 items 8–10); the genome follows the revised SDD. Run the `author` verb on the `ready` SDD only when no genome exists yet — its `Genome` handoff row is missing or names no file on disk ([genome-from-sdd-guide.md](../author/genome-from-sdd-guide.md)); an existing genome is updated through [§ Keeping the Genome Current](#keeping-the-genome-current) (`edit`), never rewritten by `author`. That guide's items 2 and 7 set the follow-up rounds, the genome's name and the `Genome` handoff row. Write the genome even when `uipath-genome` is not installed, and say that building from it needs `uipath-genome`. The genome write is a turn boundary too: end the turn after `author`'s summary.
4. **Turn after — the build, or stop.** The request's intent decides, never the execution mode — in both modes:
   - The intent implies implementation ("create / build / implement / set up / make", "so we can build it", "ready to build") → invoke `uipath-genome` with `build "<GENOME_MD>"` and the user's build request quoted verbatim on the turn after the genome, without asking. Do not add a "shall I build?" question here. It asks its own configuration questions, builds every component through its owning skill and ends with the hand-off folder. A request that also asks to publish or deploy follows [SKILL.md](../../SKILL.md) § Chaining. `uipath-genome` not installed → stop after the genome; `author`'s summary says the build needs it.
   - The request asked for the genome only → stop after it; the SDD and the genome are the deliverable. Offer the build in one line of `author`'s summary.

## Keeping the Genome Current

An SDD change is either a `design` revise (a `revise:` caller request, a design change routed from a designed genome, an SDD change asked for after the genome is written) or a user's edit to the SDD the planner is told about. After one:

1. **The SDD's `Genome` handoff row names a genome on disk** (the root's row, for a solution) → end the same run with `edit` "The SDD was revised: update the genome" ([edit-guide.md](../edit/edit-guide.md)) and its strict check ([SKILL.md](../../SKILL.md) § Check).
2. **A caller's request with `stop-after: sdd`** → end at its result instead.
3. **The `Genome` row is missing, or names no file on disk** → no genome to update; one is written only on demand (Step 5 item 3).

## Gap Markers

`[DEFAULT]` and `[SME REVIEW]` are the entire gap vocabulary of an SDD and a plan ([SKILL.md](../../SKILL.md) Critical Rule 6). A placeholder value a template names in its own cell rules — a value the build resolves, such as a registry identity the design could not match — is a cell value, not a gap marker. It is always paired with an `[SME REVIEW]` item.

1. **The exact string is load-bearing.** The `Action Required — SME Review Items` block, the gap counts, the `Status: ready` flip, the genome's carry-over and every reviewer grepping the file find the items by exact match on `[SME REVIEW]` / `[DEFAULT]`.
2. **Write the marker verbatim, with nothing else inside the brackets.** The note goes *after* the closing bracket: `| UiPath version | [SME REVIEW] not recorded in the PDD |`. Never fold the note inside (`[SME REVIEW — not recorded]`) and never substitute another word (`[PLACEHOLDER]`, `[TBD]`, `[TODO]`, `<fill in>`, an invented `<UPPER_SNAKE>` token such as `<SME_PROVIDED>`, `N/A`, prose like "to be confirmed"). A sample value nobody supplied (test data, a mailbox) is `[SME REVIEW] <what is needed>` or a plainly fictitious example value — never an angle-bracket token, which reads as an unfilled template slot. A decorated or renamed marker is invisible to every consumer above — the gap silently disappears.
3. **Carry markers through byte-for-byte when mapping or copying content out of another document** (a source SDD into a client template, a PDD into an SDD, one SDD section into another). Re-wording a marker you did not author destroys a gap someone else recorded. Add new markers for the gaps *you* find; never edit the ones already there. The one exception is a caller's declared `open-item-marker`, which becomes `[SME REVIEW]` ([caller-request-guide.md](caller-request-guide.md)).

## Design Handed Over by a Build Skill

A build skill that finds no SDD to build from hands its request here in the same conversation (SKILL.md Choosing the Verb item 3); `uipath-maestro-case` does. `design` runs as for any request, with three differences:

1. **The output path is the caller's** (`sdd.md` at the working root for `uipath-maestro-case`). Never overwrite an existing file there: stop and say it exists.
2. **The Phase 2 Step 5 review carries the caller's build options.** Its one question offers `Build it — straight through` / `Build it — pause at the build preview` / `Change something`. With open items that name a prerequisite of the build, the first option reads `Build despite N flagged items — straight through`. The answer is the build consent and the build-review preference; it is never asked again.
3. **The write does not end the turn and gets no genome.** After the `ready` flip, the caller continues its own build in this conversation, verifying the identities the SDD resolved instead of re-discovering them.

## Client Word Document

<!--skill-flavor:client-word-document:start-->
Only on request: an official client template, a Word SDD / ASDD, a `.docx`. Run it after the SDD is on disk, from the markdown SDD, following [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md). The markdown SDD stays as-is: the client document is a separate file beside it, and its section structure is the customer's template, never this skill's.
<!--skill-flavor:client-word-document:end-->
