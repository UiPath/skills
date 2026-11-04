# Design Guide — the `design` verb

`design` turns a PDD, or any process-knowledge source, into an implementation-ready SDD in three phases: **Phase 1** analyses the source and selects the scope, **Phase 2** reviews the architecture, **Phase 3** writes the full SDD incrementally and flips it to `ready` ([sdd-writing-guide.md](sdd-writing-guide.md)). The next turn writes the genome from the `ready` SDD (Verb Rule 8). The source may be a document or the request itself; every product, Case Management included, runs this guide. All user questions use numbered-choice format.

## Verb Rules

These add to the Critical Rules in [SKILL.md](../../SKILL.md).

1. **Select scope before designing architecture — and gate every product by platform constraints.** Single product (RPA Process/Library/Test Auto, Maestro Flow, Maestro BPMN, Case, Agents, Coded Apps, API Workflows) vs multi-project Solution determines the template(s) and project structure. Use the [Product Selection Guide](../shared/product-selection-guide.md): Constraint Gate → Level 1 → 1.5 (RPA sub-type) → 1.75 (Solution composition) → 2.5 (project decomposition). The delivery model (Cloud / Automation Suite / standalone — asked at `design` entry) blocks unavailable products via [platform-availability-guide.md](../shared/platform-availability-guide.md); user-excluded products are never re-offered.
<!--skill-flavor:sdd-no-task-lists:start-->
2. **The SDD is architecture only — no task lists.** `design` produces the SDD (Project Structure, Data Definitions, Testing Strategy, …). Task derivation is `plan`'s job. Never put Task 1 / Task N templates or *implementation* tasks created with the task-list tool in the SDD. End the SDD with a `## Next Steps` section. (Progress-tracking tasks created with the task-list tool are a separate, allowed use.)
<!--skill-flavor:sdd-no-task-lists:end-->
3. **Write the `## Planner Handoff` header AND the `<!-- planner-handoff:v1 -->` marker into every SDD.** They are the load-bearing detection contract — § Choosing the Verb detects either signal, so keep both. The fields and their rules: [sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 2.
4. **Honour the template section structure as a hard superset contract.** Write single-product scope to `<PROCESS_NAME_KEBAB>-sdd.md`; write Solution scope to a `<SOLUTION_NAME_KEBAB>-solution-sdd.md` overview plus one `<PROJECT_NAME_KEBAB>-sdd.md` per project. If the user specifies an output path for the SDD, use it instead of these defaults. After writing, diff the generated H2/H3 headings against the template TOC — the generated set MUST be a superset. A missing template-required H2/H3 is an SDD defect, not an `[SME REVIEW]` item — regenerate it.
5. **Testing is mandatory and thorough — never offer "happy path only".** `design` writes a full Testing Strategy section (happy path, edge cases, error scenarios, e2e for Master Projects). Implementation specialists may scope down at execution time; the SDD does not.
<!--skill-flavor:solution-terminal-artifact:start-->
6. **The terminal artefact of a Solution build is a packed `.uipx`.** The SDD's `## Next Steps` section points the user at the `uipath-solution` skill, which packs it. A bare project folder is not the deliverable. Exception: when the Constraint Gate blocks Solutions for the delivery model — standalone, Automation Suite older than 2.2510, or a user exclusion — rewrite Next Steps to per-package Orchestrator publish routed via `uipath-platform`.
<!--skill-flavor:solution-terminal-artifact:end-->
7. **Design resolves identities only.** A resource the design names is looked up (the Level 0 estate sweep, the tenant library search) and adopted when one match is confident; anything ambiguous or missing is written as the intended name with an `[SME REVIEW]` item. Schema discovery, project scaffolding and create-on-missing are build concerns, recorded as decisions for the build — `design` never runs them.
8. **Every `ready` SDD gets its genome on the next turn, a design-only request included** — except a design a build skill handed over, which goes back to that skill. The sequence and every condition on it: [sdd-writing-guide.md](sdd-writing-guide.md) § Step 3.
9. **Write the SDD skeleton first and flip `ready` last; the SDD write is a turn boundary.** The skeleton goes to disk before any other Phase 3 section, so a watchdog kill still leaves a gradeable file; `[SME REVIEW]` items gate the `ready` flip, never the skeleton write. Procedure: [sdd-writing-guide.md](sdd-writing-guide.md) Step 0; what the next turns run: its § Step 3. Scope and UI answers resolved in `design` flow forward to `plan` through the SDD.
10. **Keep the source's words.** Roles, domain nouns, stage and step labels, decision outcomes and system names are written exactly as the source writes them (`CFO`, `Vendor`, `Needs Info`, `Workday`) — never homogenised to a synonym (`Approver`, `Supplier`, `the HR system`). Only mechanical derivations change a name: PascalCase project and case names, kebab-case file names, camelCase variables.
11. **When sources conflict, the higher one wins:** platform constraints (the delivery model, a product's schema) → a regulatory or compliance constraint the source states or implies → tenant evidence (a deployed resource matching the described work) → what the user said → the source documents → the template's and product guide's defaults. A lower source overridden is a Decisions Made row (autonomous) or a line of the Step 5 review.
12. **A product the user names is the primary**, unless the Constraint Gate blocks it or Level 0 finds the work should not be automated: Level 1 confirms it instead of selecting, and Levels 1.5–3 still run inside it.
13. **Every key the automation builds is stable across retries.** A file name, sequence number, message ID or queue reference written for an output is built from the item's own identity (its reference, GUID or source ID), never the clock or a counter at write time — so a retry finds what the first attempt wrote instead of writing it twice.

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole |
| Phase 1 Step 0 | — | [platform-availability-guide.md](../shared/platform-availability-guide.md) § Resolving the Delivery Model |
| Phase 1 Step 1 | — | [pdd-analysis-guide.md](../shared/pdd-analysis-guide.md) whole |
| Phase 1 Step 2.5 | the source describes RPA-bearing work (UI, Excel or Office, files, desktop or on-prem systems) and the prompt allows `uip` commands | [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) |
| Phase 1 Steps 3.5–6 | — | [product-selection-guide.md](../shared/product-selection-guide.md) by named `##` sections, never whole (over 60 KB): § How selection works — four layers, § Levels of Decision, § Constraint Gate, § Level 0 — Suitability Gate, § Level 1 — Primary Scope Selection, § Level 2.5 — Project Decomposition, § Per-task component placement (the to-be, per step). Search for `^## ` to get the line numbers, then read each section's line range |
| Phase 1 Steps 4–6 | Level 1 = Solution, or the user picks "Solution (customize)" | product-selection-guide.md § Level 1.75 — Solution Composition |
| Phase 1 Step 5 | the primary is Agents or Coded Apps and product-specific information is missing | [scope-recommendation-guide.md](scope-recommendation-guide.md) § Gap Handling for Agent / Coded App |
| Phase 1 Step 6 | — | scope-recommendation-guide.md § Presenting the Recommendation (its Summary block holds the Recommended Scope, Project List and Queue Architecture formats) |
| Phase 1 Step 3.5 or Phase 2 Step 4 | an external system needs its Integration Service check, or a Level 3 add-on is in play (HITL, Integration Service, API Workflow as integrated component, reusable or shared assets) | product-selection-guide.md § Level 3 — Capability Add-ons |
| Phase 2 Step 1 | — | scope-recommendation-guide.md § Template Mapping |
| Phase 1 Step 4 | whenever the Constraint Gate runs — every delivery model: Cloud is not uniform, and its variants (Public Sector, Dedicated, Test Cloud) and per-tenant entitlements can block products inside the Cloud column | [platform-availability-guide.md](../shared/platform-availability-guide.md) |
| Phase 1 Step 4 | Level 1 = RPA, or a Solution includes RPA | [rpa-product-guide.md](rpa-product-guide.md) (Level 1.5, Level 2, Level 2.5 Part A, R-07 naming, REFramework) |
| Phase 1 Step 4 | Level 1 = Case Management, or a Solution includes a case | [case-product-guide.md](case-product-guide.md) whole except § SDD Conformance Checklist |
| Phase 1 Step 2 | the source signals a non-scriptable interactive sign-in (hardware 2FA token, smart card, biometric) | [attended-reauth-pattern-guide.md](attended-reauth-pattern-guide.md) |
| Phase 2 Step 1 | — | the SDD template(s) the Template Mapping names, in `../assets/templates/` |
| Phase 2 Step 2 | filling §14 Packages or its equivalent | [package-selection-guide.md](package-selection-guide.md) |
| Phase 2 Step 2 or Phase 3 | filling RPA §4 Business Rules or BPMN §5 Gateways | [business-rules-guide.md](business-rules-guide.md) |
| Phase 3 | Phase 2 Step 5 is approved (or skipped in autonomous mode) | [sdd-writing-guide.md](sdd-writing-guide.md) whole; its § Read Plan names Phase 3's reads |

## Anti-patterns

1. **Copying the PDD structure into the SDD.** The SDD reorganizes content for implementation — it does not mirror the PDD's document flow.
2. **Defaulting to RPA Process when the need profile points elsewhere.** Use the Product Selection Guide decision tree on the synthesized need, not keywords: genuine judgment/reasoning → Agents; stages/SLA/approval lifecycle → Case Management ("AI" over a rule-expressible decision is still RPA). Forcing single-product scope when the PDD describes multiple coordinated projects is the same mistake — offer Solution.
3. **Renaming the `## Planner Handoff` heading or stripping the `<!-- planner-handoff:v1 -->` marker.** Either signal alone is sufficient for detection, but both should remain — removing both breaks `plan` detection silently.

## Phase 1 — PDD Analysis & Scope Selection

### Step 0: Determine Execution Mode & Delivery Model

Before reading the PDD in full, search it for platform signals ("Automation Suite", "on-prem", "self-hosted", "Orchestrator", "cloud", a tenant URL) — the skip rule below depends on them — then ask **one structured prompt containing two questions** — execution mode and delivery model (three when the custom-host follow-up below applies; keep a prompt to at most four questions). Batching keeps the prompt budget flat: the delivery model gates every product decision (see [Product Selection Guide → Constraint Gate](../shared/product-selection-guide.md#constraint-gate)) and asking it later costs a second interruption.

**Delivery model** — run [platform-availability-guide.md § Resolving the Delivery Model](../shared/platform-availability-guide.md#resolving-the-delivery-model) first: its preflight, Question 2 (with the custom-host follow-up) and skip rule.

*Question 1 — Execution mode:*

> How should I handle this SDD generation? (The SDD is written this turn; its genome — the build blueprint — is written from the finished SDD on the next turn.)
>
> 1. **Autonomous** *(recommended)* — I will read the PDD, make all decisions, generate the full SDD, then write its genome on the next turn. I will only interrupt for hard blockers (PDD unreadable, Agent/Coded App missing critical info, unresolved `[SME REVIEW]` items before finalizing).
> 2. **Interactive** — I will pause at each phase checkpoint (summary, architecture, final SDD) for your review before proceeding.

**Skip Question 1 symmetrically** when the request already states the execution mode ("autonomous", "don't pause for checkpoints", "interactive review"). When both questions are resolved from context, skip the structured prompt entirely and record both values.

Record both choices — they go into the SDD's `## Planner Handoff` header ([sdd-writing-guide.md](sdd-writing-guide.md) Step 2) and propagate to `plan` (task derivation): execution mode drives task review behavior; delivery model is passed to specialists as a platform constraint.

In **Autonomous** mode:
- Skip Phase 1 summary presentation (generate internally, do not wait for confirmation) — the `## Recommended Scope` block still persists into the SDD ([sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 3)
- Skip Phase 2 architecture review (generate, do not wait)
- Ask only what blocks the design: the unresolved Step 0 questions, the Agent/Coded App gap question (Step 5), and one SME prompt holding the items with no defensible default ([sdd-writing-guide.md](sdd-writing-guide.md) Step 1.5). Every other confirmation a reference describes — the RPA sub-type, the scope, a tenant library pick, a revision round — is an interactive checkpoint: take its recommended option and record the pick in Decisions Made
- **Insert a "Decisions Made" block** at the top of the SDD (immediately after the Planner Handoff header and before any other section) listing the five highest-leverage architectural picks with one-sentence reasons. See [sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 3 for the exact block format. Do **NOT** ask a structured question — the picks are decided autonomously; the block makes them scannable in the SDD's first screenful so a reviewer can spot a wrong call without reading the whole document.

In **Interactive** mode:
- Present and wait at every checkpoint as described in the steps below

### Step 0.5: Create Progress Tasks

<!--skill-flavor:progress-tasks:start-->
Create progress-tracking tasks with the task-list tool so the user can see where the SDD generation stands; a host with no task-list tool skips this step.

```
title="Read PDD and extract data"                 in-progress label="Reading PDD…"
title="Select product"                            in-progress label="Selecting product…"
title="Generate architecture (Phase 2)"           in-progress label="Generating architecture…"
title="Write SDD skeleton to disk"                in-progress label="Writing SDD skeleton…"
title="Generate full SDD (Phase 3)"               in-progress label="Generating SDD sections…"
title="Resolve SME review items"                  in-progress label="Resolving SME review items…"
title="Finalize SDD (Status: ready)"              in-progress label="Finalizing SDD…"
title="Write genome (next turn)"                  in-progress label="Writing genome…"
```

The genome task stays `pending` when the SDD write ends the turn; the genome turn marks it `in_progress`, then `completed`. Omit it for a design a build skill handed over (Verb Rule 8).

Mark each task `in_progress` when its step starts and `completed` when it ends. Creating and updating them is best-effort and never blocks the SDD: if a task-list call fails, warn the user once, continue without progress tasks and never retry. The skeleton write is task 4, never the last task ([sdd-writing-guide.md](sdd-writing-guide.md#step-0-write-the-sdd-skeleton-to-disk--hard-gate) Step 0).

These tasks track SDD generation. Implementation tasks are owned by `plan` (task derivation), which runs after `design` writes the SDD and its genome — do NOT create implementation tasks here.
<!--skill-flavor:progress-tasks:end-->

### Step 1: Read the PDD

0. **No document** ("design X", a process described in the request): the request and whatever it attaches are the source; read every attached or named file, then continue at Step 2 — Step 3 finds the gaps and Step 6 asks what only the user can answer.
1. Determine the input format and route it to the right tool — Markdown (`.md`) and plain text (`.txt`): read directly; PDF (`.pdf`): read by page range; pasted text: from conversation context. See [PDD Analysis Guide → Supported Input Formats](../shared/pdd-analysis-guide.md#supported-input-formats). The source need not be a formal PDD — a Confluence page, BPMN model (`.bpmn`), meeting/Zoom transcript, SOP, or requirements doc also works ([Accepted process-knowledge sources](../shared/pdd-analysis-guide.md#accepted-process-knowledge-sources)); run heavier Phase 1 elicitation when the source is less structured than a PDD. Extract **both AS-IS and TO-BE** ([As-Is and To-Be Process](../shared/pdd-analysis-guide.md#as-is-and-to-be-process)).
2. **Size-based reading strategy** for PDFs:
   - **Under 10 pages:** read the entire document in one pass. Skip ToC lookup.
   - **10-50 pages:** read the ToC first, then read sections in priority order (overview → steps → exceptions → applications → credentials).
   - **Over 50 pages:** read ToC, then read high-priority sections (overview, process steps, exceptions) first, extract as you go, then read remaining sections.
3. For pasted text over 3000 words, ask the user to paste in sections.
4. **Error cases:** if the document cannot be read (corrupt PDF, password-protected, unsupported format), tell the user and ask them to provide it in a different format. If the document describes no process at all (no steps, no applications, no exceptions), tell the user and stop; a less structured process source continues, with heavier Phase 1 elicitation.
5. **Language handling:** if the PDD is not in English, ask a structured question with the numbered-choice format:

   > The PDD appears to be in <LANGUAGE>. Which language should the SDD use?
   >
   > 1. **English** *(recommended)* — SDD in English for broadest tool compatibility
   > 2. **<LANGUAGE>** — SDD in the same language as the PDD

   Regardless of choice, keep section headings and structural identifiers (BR-01, B1, E1) in English for tool compatibility.

### Step 2: Extract Structured Information

Follow the [PDD Analysis Guide](../shared/pdd-analysis-guide.md) to extract data from the PDD. Build an internal model with these components:

| Component | PDD Topic to Look For | Required |
|---|---|---|
| Process name and objective | Introduction | Yes |
| Key contacts | Process key contacts | No |
| Process overview (schedule, volumes, FTEs) | Process overview | Yes |
| In-scope activities | In scope | Yes |
| Out-of-scope activities | Out of scope | Yes |
| Process steps | Detailed process map / steps | Yes |
| Business exceptions | Exceptions handling | Yes |
| System errors | Error mapping and handling | Yes |
| Application inventory | In-scope application details | Yes |
| Development prerequisites | Prerequisites for development | No |
| Credentials and assets | Credentials and asset management | Yes |
| Test data | Appendix | No |

**Key Contacts go into §1 Delivery Team.** The PDD's Key Contacts section (SA, BA, developers, PM, SME / Process Owner) populates the Delivery Team table in §1 of the RPA template. Include only roles the PDD explicitly names — do not invent or leave rows as `[SME REVIEW]`; omit silent rows instead.

### Step 2.5: Tenant Library Discovery

The org's deployed libraries cannot be inferred from any PDD. Query the tenant feed to discover candidates the new project should reference. Run in BOTH Autonomous and Interactive modes — this drives §14 Packages and §16 "Shared libraries referenced".

Skip this step for non-RPA primaries (Agents, Coded Apps, Flow, BPMN, Case, API Workflows) — shared RPA libraries do not apply to those products' package models. Only the *library* discovery is RPA-scoped: the [Level 0 estate sweep](../shared/product-selection-guide.md#estate-sweep) (deployed processes, agents, Maestro processes, IXP projects, solutions, connections) runs for every scope when evaluating the suitability gate.

Run the procedure in [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md). Keyword source for step 2: PDD Application Inventory + org-prefix terms (`Common`, `Shared`, `<Company>` if mentioned in the PDD). Output mapping: every selected library → one row in every sub-project's §14 Packages table, and its package ID into §16 Deployment Environment → "Shared libraries referenced". If the auth preflight fails, use the guide's manual fallback and propagate the user's named libraries to §14 / §16 the same way.

**This step is best-effort — it never blocks SDD output.** If the auth preflight errors or auth is unavailable, **Autonomous mode skips library discovery and proceeds with public NuGet only** — do not retry or troubleshoot auth mid-generation, and do not pause. Skip the step entirely if the user's prompt forbids running `uip` commands.

### Step 3: Detect Gaps

Scan for missing or vague information. Use the Gap Detection Checklist in the [PDD Analysis Guide](../shared/pdd-analysis-guide.md) to classify each gap as `[DEFAULT]` or `[SME REVIEW]`.

### Step 3.5: Synthesize the Need

Before selecting a product, distil the extracted model into a **need profile** — the recommendation reasons from this multi-factor picture, NOT from surface keywords. No single factor decides the tool; capture all and weigh the overall fit:

- **Core need & target outcome** — one sentence: what outcome the automation must produce, and which KPI it moves (cycle time, manual effort, quality/accuracy, cost, throughput, or compliance). Design the "to-be" against that outcome, not a copy of the as-is.
- **Decision nature (determinism)** — are decisions rule-expressible (**deterministic**: same input → same output) or do they need judgment / reasoning over ambiguity (**non-deterministic**)? Assess per process AND per step. Deterministic → RPA / API / rule-based; genuine judgment → Agents. (One factor among those below — not the sole gate.)
- **Input structure** — structured / predictable vs messy / unstructured (email, free text, varied documents → Agent or IXP to interpret).
- **Integration surface** — for each external system: does a stable API / **Integration Service connector** exist, and is it **reachable from the executor's runtime under the delivery model** (on-prem HTTP(S) APIs → Automation Relay option, placement rule 5)? Reuse an existing connector first. If none exists: API Workflows, RPA, and coded Agents call the API directly (Direct HTTP); IS-only surfaces (Maestro Flow / BPMN / Case connector nodes, low-code Agent tools) need a custom connector (→ `uipath-connector-builder`) or an API Workflow wrapper — see [Product Selection Guide → Integration Service](../shared/product-selection-guide.md#integration-service). Verify with `uip is connectors list` — never assume a connector exists. UI-only system → RPA.
- **Interaction model** — system-to-system (no UI, no human) · UI automation · human-in-the-loop (immediate attended action vs **asynchronous approval** — async inside one process → long-running RPA + Action Center) · user-facing app.
- **State** — atomic (one shot) · transactional (per-item, retryable) · long-running (suspends / waits). Long-running inside ONE process → RPA long-running workflow; long-running across products → Maestro.
- **Coordination shape** — single task · linear/branching pipeline · staged case lifecycle (stages + SLA) · structured control-flow (parallel / events / subprocess). Use the control-flow structure extracted in Step 2 ([PDD Analysis Guide → Detailed Process Map](../shared/pdd-analysis-guide.md#detailed-process-map)).
- **Volume, latency & cost** — high-volume / repeatable favours deterministic (agentic cost is higher-variance and less predictable — estimate per model/tenant, and justify agentic at volume); note any latency requirement.
- **Risk, reversibility & auditability** — high-risk / irreversible / low-confidence steps need a HITL gate; compliance-critical work needs a deterministic, auditable record.
- **Change / volatility** — how often inputs, forms, or rules change (an uncaptured volatility assumption is a top cause of solutions that break in production; prefer IXP for changeable documents).
- **Reuse** — local operation vs shared callable capability (→ RPA Library / API Workflow / custom connector, built before consumers).
- **Runtime & resource locality** — where must the work execute? Machine-local resources — desktop apps, Excel/Office files, file shares, on-prem databases, terminal/mainframe, Citrix — are reachable only from a robot inside the environment → RPA regardless of determinism or API existence (exceptions: on-prem HTTP(S) APIs via confirmed Automation Relay, and robot-hosted Coded Functions, which also run inside the environment — see the placement rules). Windows · cross-platform · serverless · user desktop drives compatibility, robot type, and licensing (§11 Project Mode Decision in the RPA template).
- **Existing estate** — what is already deployed: processes, API Workflows, connectors (`uip is connectors list`), tenant libraries (Step 2.5), IXP models, user-named resources. Reuse before build.
- **Trigger** — who or what starts it.
- **Confidence** — the evidence behind each factor and what remains unknown; unknowns become `[SME REVIEW]` rows, and a genuinely ambiguous product choice goes to the user (Step 6) — never a silent default.

**Close Step 3.5 by typing every extracted step** with the [Product Selection Guide → Per-task component placement](../shared/product-selection-guide.md#per-task-component-placement-the-to-be-per-step) table — the resulting **step→executor map** is Level 1's input (layer 2 before layer 3; Level 1 never matches raw keywords against the whole process). Level 1 first folds absorbed capabilities into their hosts ([Decision table → Absorption fold](../shared/product-selection-guide.md#decision-table)) — capabilities a host invokes in-process are integrated components, not orchestration triggers — then reads the folded map.

Carry the need profile and the step→executor map into the Step 6 summary and the SDD `## Recommended Scope` reasoning so every product pick reads as `need → product`, auditable against the PDD. The dominant real-world pattern is **hybrid** (AI decides, deterministic RPA/API execute as governed tools, Maestro orchestrates when real orchestration is needed, HITL gates the risky steps) and **decomposed** into separate blocks — not one monolithic flow. Level 1 (Step 4) matches on the whole profile; PDD keywords are evidence, not the decision. When the need is genuinely ambiguous between products, ask the user (Step 6) — do not silently default.

### Step 4: Run Levels in Order

Each level lives in its canonical reference; output of each level feeds the next.

> **Constraint Gate applies at every level.** The delivery model from Step 0 and any user-stated product exclusions filter the candidates before each level recommends — see [Product Selection Guide → Constraint Gate](../shared/product-selection-guide.md#constraint-gate) and [platform-availability-guide.md](../shared/platform-availability-guide.md).

Run the levels in the order and under the conditions of [Product Selection Guide § Levels of Decision](../shared/product-selection-guide.md#levels-of-decision): Level 0 first — Levels 1+ run only on `proceed` / `proceed-with-redesign` / `partial`; Level 1.5 for an RPA primary, or per RPA project through Level 1.75 Pass C; Level 1.75 when Level 1 = Solution or the user picks "Solution (customize)" in Step 6; Level 2.5 Part A per RPA Process project; Part B always.

This step's output goes into the Phase 1 summary at Step 6 and drives the Phase 2 architectural core.

> Level 2 (Authoring mode — XAML / Coded / Hybrid) is decided per RPA project at Phase 2 Step 2 from [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Level 3 (Capability add-ons — HITL, Integration Service, etc.) is detected during PDD analysis and flagged in template sections during Phase 2 Step 4. Per-task component placement (which step lands on RPA / API / IXP / Agent / Function / HITL / Maestro / Data Fabric) runs twice: at Step 3.5 (the step→executor map that feeds Level 1) and at Phase 2 Steps 3–4 (recording placements in template inventories) — [Product Selection Guide → Per-task component placement](../shared/product-selection-guide.md#per-task-component-placement-the-to-be-per-step).

### Step 5: Check for Agent/Coded App Gaps

If the primary product is **Agents** or **Coded Apps** AND required product-specific information is missing from the PDD, run [scope-recommendation-guide.md](scope-recommendation-guide.md) § Gap Handling for Agent / Coded App. Never auto-fallback: the user chooses explicitly.

### Step 6: Present Summary + Scope Recommendation

Emit the summary block described in [scope-recommendation-guide.md](scope-recommendation-guide.md) § Presenting the Recommendation. The **recommended scope appears first**; single-product alternatives and "Solution (customize)" follow as alternatives in the confirmation structured question.

```markdown
## PDD Analysis Summary

**Process:** <PROCESS_NAME>
**Objective:** <OBJECTIVE_SUMMARY>
**Applications:** <APP_COUNT> — <APP_NAME (ROLE)>, ...
**Process Steps:** <STEP_COUNT> steps identified across <APP_COUNT> applications
**Business Rules:** <RULE_COUNT> extracted
**Business Exceptions:** <EXCEPTION_COUNT> defined in PDD
**System Errors:** <ERROR_COUNT> defined in PDD
**Gaps Detected:** <DEFAULT_COUNT> [DEFAULT], <SME_REVIEW_COUNT> [SME REVIEW]

<RECOMMENDED_SCOPE_SUMMARY_BLOCK — emit the "Summary block" from
scope-recommendation-guide.md → Presenting the Recommendation:
Recommended Scope + Project List + Queue Architecture>

### Clarifying Questions
<NUMBERED_QUESTIONS_IF_ANY>
```

Then ask a structured question with the confirmation question from scope-recommendation-guide.md § Presenting the Recommendation (recommendation as option 1, single-product alternatives, then "Solution (customize)").

**If the user picks "Solution (customize)":** re-run Level 1.75 per the customize branch in the guide, then re-emit this summary with the customized project list, then re-ask the confirmation question. Max 3 revisions — after that, proceed with the latest composition.

**If the user picks a single-product alternative:** re-run Step 4 with the user's choice as the forced primary (including Level 1.5 if it's RPA).

Ask at most 5 clarifying questions total, in a single round. If the user cannot answer some, tag those items as `[SME REVIEW]` and proceed.

## Phase 2 — Architecture Review

### Step 1: Load the Template(s)

Load from the [Template Mapping table](scope-recommendation-guide.md#template-mapping):

- **Single-product scope:** load the one template matching the Level 1 primary.
- **Solution scope:** load the solution overview structure PLUS one template per project in the Level 2.5 unified project list. RPA Master Projects share one RPA template file across their sub-projects; unrelated RPA projects each get their own file.

**The SDD is automation-type-agnostic — no type is privileged.** Section coverage follows the in-scope types: a single-product SDD uses that product's template; a Solution's per-project SDDs each use their product's template, tied together by the Solution overview's **component inventory** (every component listed with its type — RPA / API Workflow / Agent / Maestro Flow · BPMN · Case / Coded or Low-code App / DU-IXP / connector / HITL). Include per-type detail (Agent Configuration, Queue Architecture, API schemas, Gateways, Case stages, etc.) **only for the types actually in scope** — never emit "N/A" filler sections for absent types, and never assume an agentic (or RPA-only) shape. Delete rows that do not apply; replicate per-instance sections (e.g., one Agent Configuration per agent).

### Step 2: Generate the Architectural Core

Generate the sections the template's `Phase 2 sections:` line names (the Case template: Sections 1–4). What they hinge on:

- **RPA:** §10 applies Level 2.5 Part A ([rpa-product-guide.md](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals)) — Single vs Master Project, sub-projects, queue schema; §11 Project Structure is the most load-bearing section — `plan` derives tasks from it; §13 applies Level 2 ([rpa-product-guide.md](rpa-product-guide.md#level-2--authoring-mode)); §14 infers NuGet packages from §9 and the process steps.
- **Maestro BPMN:** §5 Gateways carries the decision tables and the reasoning list ([Business Rules Guide](business-rules-guide.md)).
- **Agents:** §9 Project Structure states Coded vs Low-code. **API Workflows:** §4 Execution Flow is high-level steps, no JavaScript.
- **Case Management:** Sections 1–4 per [case-product-guide.md](case-product-guide.md). Headings render in the template's long form (`## Section 1: Case Definition`, …): `uipath-maestro-case` parses the heading TEXT verbatim, and `§N` is notation in planner documents only.

### Step 3: Decompose Steps Into Implementation Units

Each template has a primary inventory table. Map PDD steps to units:

| Product | Primary Inventory | Unit Type |
|---|---|---|
| RPA (Single Project) | Workflow Inventory | `.xaml` or `.cs` workflow files |
| RPA (Master Project) | Workflow Inventory **per sub-project** | `.xaml` or `.cs` workflow files, grouped by sub-project |
| Flow | Nodes Inventory | Flow nodes |
| BPMN | Activities Inventory | BPMN activities / tasks (service, script, user, call activity, subprocess) |
| Case | §2 Stages & Tasks | Stage blocks plus task summary/detail blocks |
| Agents | Tools | Python functions, RPA/API workflow bindings |
| Coded Apps | Pages + Components | Routes and React/Angular/Vue components |
| API Workflows | Execution Flow steps | Activities (HTTP, Connector, Script) |

Each unit must have: **a concrete responsibility, specific PDD step references, and defined inputs/outputs.**

Type each step's verb and place it on the best-fit component per [Product Selection Guide → Per-task component placement](../shared/product-selection-guide.md#per-task-component-placement-the-to-be-per-step) — deterministic validate/transfer → RPA or API, document collect → IXP, judgment decide → Agent, atomic transform/compute → Function, review/sign-off → HITL, aggregate → Data Fabric. Record the placement in the inventory row; every non-primary placement becomes an integrated component in Step 4.

**For RPA Master Project:** decompose in two passes:
1. First, assign each PDD step to a sub-project based on the §10 sub-projects table (each sub-project lists its PDD steps).
2. Then, within each sub-project, decompose the assigned steps into workflow files.
3. For REFramework sub-projects, the main workflows (Init, GetTransactionData, Process, SetTransactionStatus) come from the framework — only the Process-specific workflows go in the inventory.

### Step 4: Flag Integrated Components

For each integrated component detected in Phase 1 (and each non-primary placement from Step 3), flag it in the appropriate section of the template:

- **HITL** — host-aware routing: Flow hosts → flag touchpoints; implementation task routes to `uipath-human-in-the-loop`. Coded Agents → escalation is part of the `uipath-agents` build task (the HITL skill defers coded-agent wiring to it). BPMN userTask → flagged in §9 HITL Touchpoints, authored inline by `uipath-maestro-bpmn` (no HITL-skill task). Case → `action` task detail block in §2 Stages & Tasks with Action App intent (never the HITL skill). RPA → Action Center / long-running workflow flagged in the RPA template.
- **Integration Service connectors** → list in Application Inventory (RPA) or Connectors section (others); check `uip is connectors list` — implementation task routes to `uipath-platform` to configure an existing connector, or `uipath-connector-builder` to build a custom one when none exists
- **IXP / Document Understanding models** (extraction from semi-structured documents) → list in the host template's "IXP / Document Understanding Models" table (Flow / BPMN / Case / Agent / RPA templates carry it); for an API Workflow or Coded App primary, record the model as its own row in §Solution / Project Breakdown instead. Implementation task routes to `uipath-ixp`, ordered before its consumers
- **Coded Functions** (TypeScript / JavaScript / Python — atomic deterministic transform / compute: parsing, scoring, custom-auth API calls, IS-connection queries) — only when extraction is justified per [placement rule 6](../shared/product-selection-guide.md#per-task-component-placement-the-to-be-per-step); host-native logic stays in the host's own inventory → list in the host template's "Coded Functions" table (Flow / BPMN / Case / Agent templates carry it). Implementation task routes to `uipath-functions`, ordered before its consumers; no per-project SDD file (see [Template Mapping](scope-recommendation-guide.md#template-mapping))
- **RPA processes called by Flow/BPMN/Agent/Case** → list in Integrated Components section; implementation task will create the RPA project
- **API Workflows called by Flow/BPMN/Agent/Case** — only when extraction is justified per [placement rule 6](../shared/product-selection-guide.md#per-task-component-placement-the-to-be-per-step) (host cannot call natively, 2+ consumers, or independent lifecycle); a host-capable direct call stays in the host inventory as `Access Method = Direct HTTP` → list in Integrated Components section; implementation task will create the API Workflow project. Extraction never changes `SDD scope` ([derived-component rule](../shared/product-selection-guide.md#solution-signals))

### Step 5: Present Architecture for Review

Present the architectural core to the user — for Case Management in the shape of [case-product-guide.md](case-product-guide.md) § Presenting the Case Design. Wait for approval or adjustments. A design a build skill handed over presents the build options the caller passed ([sdd-writing-guide.md](sdd-writing-guide.md) § Design Handed Over by a Build Skill).

**Approval criteria:** any response without specific change requests. Responses like "looks good", "ok", "proceed", "yes", or a topic change all count as approval. If the user requests specific changes, incorporate them and re-present the architecture (max 3 revisions — after that, proceed with the latest version and tag disagreements as `[SME REVIEW]`).

## Phase 3 — Full SDD Generation

Read [sdd-writing-guide.md](sdd-writing-guide.md) whole now, before writing anything: it holds the skeleton write (a hard gate), the remaining sections, SME resolution, the template-superset check, the `ready` flip, the turn boundary and the genome that follows. Never write Phase 3 from memory of it.
