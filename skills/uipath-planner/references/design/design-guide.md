# Design Guide — the `design` verb

`design` converts a PDD or other process-knowledge source into an implementation-ready SDD in three phases: **Phase 1** analyzes the source and selects scope, **Phase 2** reviews architecture, and **Phase 3** incrementally writes the full SDD and flips it to `ready` ([sdd-writing-guide.md](sdd-writing-guide.md)). The next turn writes the genome from the `ready` SDD (Verb Rule 8). The source may be a document or the request itself; every product runs this guide; its template and its product guide hold what differs. Ask every user question as a structured question.

## Verb Rules

These supplement the Critical Rules in [SKILL.md](../../SKILL.md).

1. **Select scope before architecture and gate every product by platform constraints.** Select one product (RPA Process/Library/Test Auto, Maestro Flow, Maestro BPMN, Case, Agents, Coded Apps, API Workflows) or a multi-project Solution. Run [Product Selection Guide](../shared/product-selection-guide.md): Constraint Gate → Level 1 → 1.5 (RPA sub-type) → 1.75 (Solution composition) → 2.5 (project decomposition), with 1.75 and 2.5 in [solution-composition-guide.md](solution-composition-guide.md). Ask delivery model (Cloud / Automation Suite / standalone) at entry; [platform-availability-guide.md](../shared/platform-availability-guide.md) blocks unavailable products; user-excluded products are never re-offered.
2. **The SDD is architecture only, never task lists.** Include Project Structure, Data Definitions, Testing Strategy, etc. The implementation input is the genome `author` writes from the SDD.
<!--skill-flavor:sdd-no-task-lists:start-->
Never put Task 1 / Task N templates or *implementation* tasks created with the task-list tool in the SDD. End it with `## Next Steps`. Progress-tracking tasks created with the task-list tool are allowed separately.
<!--skill-flavor:sdd-no-task-lists:end-->
3. **Write both handoff signals into every SDD** ([sdd-writing-guide.md](sdd-writing-guide.md) Step 4 item 2).
4. **Treat template structure as a hard superset.** Single-product output is `<PROCESS_NAME_KEBAB>-sdd.md`; Solution output is `<SOLUTION_NAME_KEBAB>-solution-sdd.md` plus `<PROJECT_NAME_KEBAB>-sdd.md` per project; if the user specifies an output path for the SDD, use it instead of these defaults. Read every selected template end to end before generating — never a head slice or a heading list; column contracts sit deep in the file. Copy every template heading and table column header verbatim. The template owns every product-specific layout — its title, its headings, where its front matter sits, which sections repeat per project, which it makes conditional — and a guide never restates it. After writing, diff generated H2/H3 headings against the template TOC: the generated set MUST be a superset. Missing required H2/H3 is an SDD defect, not `[SME REVIEW]`; regenerate it.
5. **Testing is mandatory and thorough — never offer "happy path only".** Cover happy path, edge cases, errors, and e2e for Master Projects. Implementation specialists may scope down during execution; the SDD may not.
<!--skill-flavor:solution-terminal-artifact:start-->
6. **The terminal artefact of a Solution build is a packed `.uipx`.** Point `## Next Steps` to `uipath-solution`, which packs it; a bare project folder is not the deliverable. When the Constraint Gate blocks Solutions, Next Steps routes the publish per [SKILL.md § Chaining](../../SKILL.md#chaining) instead.
<!--skill-flavor:solution-terminal-artifact:end-->
7. **Design resolves identities only.** A resource the design names is looked up (the Level 0 estate sweep; for RPA, the tenant library search per Step 5) and adopted when one match is confident. For ambiguous or missing resources, use the intended name and an `[SME REVIEW]` item. Schema discovery, scaffolding, and create-on-missing are build concerns recorded as build decisions; `design` never runs them.
8. **Every `ready` SDD gets its genome on the next turn, including design-only requests**, except a build skill handoff, which returns to that skill. Follow [sdd-writing-guide.md](sdd-writing-guide.md) § Step 5; when revising an SDD whose genome is already on disk, update and check the genome in the same run per [sdd-writing-guide.md](sdd-writing-guide.md) § Keeping the Genome Current.
9. **Write the skeleton first and flip `ready` last; the SDD write is a turn boundary.** Write the skeleton before any other Phase 3 section so an early-ending turn leaves an SDD; `[SME REVIEW]` gates only the `ready` flip. Follow [sdd-writing-guide.md](sdd-writing-guide.md) Step 1 and its § Step 5. Scope and UI answers flow to the genome through the SDD.
10. **Keep source wording.** Preserve roles, domain nouns, stage/step labels, outcomes, and system names exactly (`CFO`, `Vendor`, `Needs Info`, `Workday`); do not homogenize them (`Approver`, `Supplier`, `the HR system`). Only mechanical derivations change names: PascalCase project/case names, kebab-case file names, camelCase variables.
11. **When sources conflict, the higher one wins:** platform constraints (delivery model/product schema) → stated or implied regulatory/compliance constraint → tenant evidence (deployed matching resource) → user statement → source documents → template/product-guide defaults. Record an overridden lower source as a Decisions Made row (autonomous) or a Phase 2 Step 5 review line.
12. **A product the user names is the primary**, unless the Constraint Gate blocks it or Level 0 finds the work should not be automated: Level 1 confirms it instead of selecting, and Levels 1.5–3 still run inside it.
13. **Make every automation-built key retry-stable.** Build file names, sequence numbers, message IDs, and queue references from the item's identity (reference, GUID, or source ID), never clock or write-time counters, so a retry finds what the first attempt wrote instead of writing it twice.
14. **A caller's design request changes only the steps its guide names.** A `planner-design-request: v1` block carries `execution`, limits interactive execution to the Phase 2 Step 5 checkpoint, permits autonomous stopping only for a hard blocker, and ends with `planner-design-result: v1`: [caller-request-guide.md](caller-request-guide.md).

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole |
| start | the request carries a `planner-design-request: v1` block | [caller-request-guide.md](caller-request-guide.md) whole |
| Phase 1 Step 1 | — | [platform-availability-guide.md](../shared/platform-availability-guide.md) whole: § Resolving the Delivery Model at Step 1, the rest at Step 8 on every delivery model (Cloud variants — Public Sector, Dedicated, Test Cloud — and per-tenant entitlements block products too) |
| Phase 1 Step 3 | — | [pdd-analysis-guide.md](../shared/pdd-analysis-guide.md) whole |
| Phase 1 Step 4 | the source signals a non-scriptable interactive sign-in (hardware 2FA token, smart card, biometric) | [attended-reauth-pattern-guide.md](attended-reauth-pattern-guide.md) |
| Phase 1 Step 5 | the scope may contain an RPA project — the source describes RPA-bearing work (UI, Excel or Office, files, desktop or on-prem systems) — and the prompt allows `uip` commands | [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) |
| Phase 1 Steps 7–10 | — | [product-selection-guide.md](../shared/product-selection-guide.md) whole; [solution-composition-guide.md](solution-composition-guide.md) § Level 2.5 — Project Decomposition; [component-placement-guide.md](../shared/component-placement-guide.md) § Per-task component placement (the to-be, per step) |
| Phase 1 Step 7 or Phase 2 Step 4 | an external system needs its Integration Service check, or a Level 3 add-on is in play (HITL, Integration Service, API Workflow as integrated component, reusable or shared assets) | component-placement-guide.md § Level 3 — Capability Add-ons |
| Phase 1 Step 8 | Level 1 = RPA, or a Solution includes RPA | [rpa-product-guide.md](rpa-product-guide.md) (Level 1.5, Level 2, Level 2.5 Part A, R-07 naming, REFramework) |
| Phase 1 Step 8 | Level 1 = Case Management, or a Solution includes a case | [case-product-guide.md](case-product-guide.md) whole |
| Phase 1 Steps 8–10 | Level 1 = Solution, or the user picks "Solution (customize)" | solution-composition-guide.md § Level 1.75 — Solution Composition |
| Phase 1 Step 9 | the primary is Agents or Coded Apps and product-specific information is missing | [scope-recommendation-guide.md](scope-recommendation-guide.md) § Gap Handling for Agent / Coded App |
| Phase 1 Step 10 | — | scope-recommendation-guide.md § Presenting the Recommendation (its Summary block holds the Recommended Scope, Project List and Queue Architecture formats) |
| Phase 1 Step 10 | `Execution autonomy` is `interactive` and the request carries no `planner-design-request: v1` block | [interview-guide.md](../interview/interview-guide.md) whole |
| Phase 2 Step 1 | — | scope-recommendation-guide.md § Template Mapping; then the SDD template(s) it names, in `../assets/templates/` |
| Phase 2 Step 2 | filling §14 Packages or its equivalent | [package-selection-guide.md](package-selection-guide.md) |
| Phase 2 Step 2 or Phase 3 | filling RPA §4 Business Rules or BPMN §3 Business Rules and Decisions | [business-rules-guide.md](business-rules-guide.md) |
| Phase 3 | Phase 2 Step 5 is approved (or skipped in autonomous mode) | [sdd-writing-guide.md](sdd-writing-guide.md) whole; its § Read Plan names Phase 3's reads |

## Anti-patterns

1. **Do not copy PDD structure into the SDD.** Reorganize for implementation.
2. **Defaulting to RPA Process when the need profile points elsewhere.** Use the Product Selection Guide decision tree on the synthesized need, not keywords: genuine judgment/reasoning → Agents; stages/SLA/approval lifecycle → Case Management ("AI" over a rule-expressible decision is still RPA). Forcing single-product scope when the PDD describes multiple coordinated projects is the same mistake — offer Solution.
3. **Renaming or stripping a handoff signal** ([sdd-writing-guide.md](sdd-writing-guide.md) Step 4 item 2).

## Phase 1 — PDD Analysis & Scope Selection

### Step 1: Determine Execution Autonomy & Delivery Model

Before fully reading the PDD, search for platform signals ("Automation Suite", "on-prem", "self-hosted", "Orchestrator", "cloud", tenant URL). Run [platform-availability-guide.md § Resolving the Delivery Model](../shared/platform-availability-guide.md#resolving-the-delivery-model) first: its preflight, Question 2 (with the custom-host follow-up) and skip rule. Then ask **one structured question** that batches `Execution autonomy` (Question 1) with the delivery model (that guide's Question 2), adding the custom-host follow-up when applicable ([SKILL.md § Prompt Budget](../../SKILL.md#prompt-budget)). The delivery model gates every product decision ([Product Selection Guide → Constraint Gate](../shared/product-selection-guide.md#constraint-gate)).

**Question 1 — Execution autonomy:**

> How should I handle this SDD generation? (The SDD is written this turn; its genome — the build blueprint — is written from the finished SDD on the next turn.)
>
> 1. **Autonomous** *(recommended)* — I will read the PDD, make all decisions, generate the full SDD, then write its genome on the next turn. I will only interrupt for hard blockers (PDD unreadable, Agent/Coded App missing critical info, unresolved `[SME REVIEW]` items before finalizing).
> 2. **Interactive** — I will pause at each phase checkpoint (scope summary, architecture review) for your review before proceeding.

Skip Question 1 symmetrically when the request states the mode ("autonomous", "don't pause for checkpoints", "interactive review"). A caller's `execution` answers it; ask only when missing (Verb Rule 14). When both execution and delivery model are known from context, skip the prompt and record both.

Record both in `## Planner Handoff` ([sdd-writing-guide.md](sdd-writing-guide.md) Step 4); they propagate to the genome: execution controls follow-up rounds and delivery model applies to every component.

In **Autonomous** mode, skip presenting the Phase 1 summary and the Phase 2 review (generate both internally; do not wait for confirmation); write the Recommended Scope block where the template places it ([sdd-writing-guide.md](sdd-writing-guide.md) Step 4 item 3). Ask only unresolved Step 1 questions, the Agent/Coded App gap question (Step 9), and one SME prompt for items without defensible defaults ([sdd-writing-guide.md](sdd-writing-guide.md) Step 3). Take recommended options for all other confirmations (RPA sub-type, scope, tenant library, revision), record them in Decisions Made. Never offer the interview (Step 10): every gap keeps its marker and default ([interview-guide.md](../interview/interview-guide.md) Verb Rule 1). Write the `Decisions Made` block where the template places it ([sdd-writing-guide.md](sdd-writing-guide.md) Step 4 item 3); never ask a structured question for it.

In **Interactive** mode, present and await every checkpoint below.

### Step 2: Create Progress Tasks

<!--skill-flavor:progress-tasks:start-->
Create progress-tracking tasks with the task-list tool; a host without it skips this step:

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

The genome task remains `pending` when SDD writing ends the turn; the genome turn marks it `in_progress`, then `completed`. Omit it for a build-skill handoff (Verb Rule 8). Mark each task `in_progress` at start and `completed` at end. Creation/update are best-effort and never block the SDD: on task-list failure, warn once, continue without tasks, and never retry. Skeleton writing is task 4, never last ([sdd-writing-guide.md](sdd-writing-guide.md#step-1-write-the-sdd-skeleton-to-disk--hard-gate) Step 1). These tasks track SDD generation.
<!--skill-flavor:progress-tasks:end-->

### Step 3: Read the PDD

1. **No document** ("design X", a process described in the request): use the request and attachments as source, read every attached/named file, then continue at Step 4; Step 6 identifies gaps and Step 10 asks user-only questions.
2. Route input by format: Markdown (`.md`) and plain text (`.txt`) directly; PDF (`.pdf`) by page range; Word (`.docx`, `.doc`) converted to Markdown; pasted conversation text directly. Follow [PDD Analysis Guide → Supported Input Formats](../shared/pdd-analysis-guide.md#supported-input-formats). Confluence, BPMN (`.bpmn`), meeting/Zoom transcript, SOP, and requirements doc also work ([Accepted process-knowledge sources](../shared/pdd-analysis-guide.md#accepted-process-knowledge-sources)); use heavier Phase 1 elicitation for less-structured sources. Extract **AS-IS and TO-BE** ([As-Is and To-Be Process](../shared/pdd-analysis-guide.md#as-is-and-to-be-process)).
3. PDF: under 10 pages, read all in one pass and skip ToC; 10–50, read ToC then overview → steps → exceptions → applications → credentials; over 50, read ToC and high-priority sections (overview, process steps, exceptions), extract while reading, then read the remainder.
4. For pasted text over 3000 words, ask for sections.
5. If unreadable (corrupt PDF, password-protected, unsupported), tell the user and request another format. If it describes no process (no steps, applications, exceptions), tell the user and stop; less-structured process sources continue with heavier elicitation.
6. If caller supplies `language`, use it. Otherwise, for non-English PDDs ask a structured question:

   > The PDD appears to be in <LANGUAGE>. Which language should the SDD use?
   >
   > 1. **English** *(recommended)* — SDD in English for broadest tool compatibility
   > 2. **<LANGUAGE>** — SDD in the same language as the PDD

   Keep section headings and structural identifiers (BR-01, B1, E1) in English regardless.

### Step 4: Extract Structured Information

Follow the [PDD Analysis Guide](../shared/pdd-analysis-guide.md) and build this model:

| Component | PDD topic | Required |
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

Put explicitly named Key Contacts (SA, BA, developers, PM, SME / Process Owner) in the template's Delivery Team section (RPA §1). Include only named roles; omit silent rows and do not invent or leave them `[SME REVIEW]`.

### Step 5: Tenant Library Discovery

Run [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) in BOTH Autonomous and Interactive modes for any scope containing an RPA project — the source describes RPA-bearing work (UI, Excel or Office, files, desktop or on-prem systems). Use PDD Application Inventory plus org-prefix terms (`Common`, `Shared`, `<Company>` if mentioned) as the keyword source for its step 2. Map each selected library to one row in every sub-project's §14 Packages and its package ID to §16 Deployment Environment → "Shared libraries referenced". If auth preflight fails, use the guide's manual fallback and propagate named libraries identically.

Skip when the source describes no RPA-bearing work; shared RPA libraries do not apply, but the [Level 0 estate sweep](../shared/product-selection-guide.md#estate-sweep) still runs for every scope (deployed processes, agents, Maestro processes, IXP projects, solutions, connections). **This step is best-effort — it never blocks SDD output.** In Autonomous mode, auth failure/unavailability means skip discovery and proceed with public NuGet only; do not retry, troubleshoot, or pause. Skip entirely when the user forbids `uip` commands.

### Step 6: Detect Gaps

Use the Gap Detection Checklist in [PDD Analysis Guide](../shared/pdd-analysis-guide.md) and classify every missing/vague item `[DEFAULT]` or `[SME REVIEW]`.

### Step 7: Synthesize the Need

Before product selection, create a need profile — not a keyword match. No single factor decides the tool; capture all and weigh the overall fit:

- **Core need & target outcome:** outcome and KPI (cycle time, manual effort, quality/accuracy, cost, throughput, compliance); design TO-BE against it, not AS-IS.
- **Decision nature:** deterministic rule-expressible (same input → same output) vs non-deterministic judgment/reasoning; assess per process and step. Deterministic → RPA/API/rules; genuine judgment → Agents; not the sole gate.
- **Input structure:** structured/predictable vs messy/unstructured; email, free text, varied documents → Agent or IXP.
- **Integration surface:** per external system:
  - Assess its stable API or **Integration Service connector**, and whether the executor's runtime reaches it under the delivery model (on-prem HTTP(S) → Automation Relay, placement rule 5). Reuse connectors first.
  - Verify with `uip is connectors list`; never assume a connector exists.
  - No connector: API Workflows, RPA and coded Agents use Direct HTTP. Integration Service-only surfaces (Maestro Flow / BPMN / Case connector nodes, low-code Agent tools) need `uipath-connector-builder` or an API Workflow wrapper ([Component Placement Guide → Integration Service](../shared/component-placement-guide.md#integration-service)).
  - UI-only system → RPA.
- **Interaction model:** system-to-system; UI; human-in-the-loop (immediate attended vs **asynchronous approval**—async inside one process → long-running RPA + Action Center); user-facing app.
- **State:** atomic; transactional/retryable; long-running/suspends/waits. Long-running in one process → RPA long-running workflow; across products → Maestro.
- **Coordination:** single task; linear/branching pipeline; staged case lifecycle (stages + SLA); structured control flow (parallel/events/subprocess), using [PDD Analysis Guide → Detailed Process Map](../shared/pdd-analysis-guide.md#detailed-process-map).
- **Volume, latency & cost:** high-volume repeatability favors deterministic; agentic cost is higher-variance/less predictable, so estimate per model/tenant and justify it at volume; note any latency requirement.
- **Risk, reversibility & auditability:** risky, irreversible, or low-confidence steps need HITL; compliance-critical work needs deterministic auditable records.
- **Change/volatility:** frequency of input/form/rule changes; use IXP for changeable documents.
- **Reuse:** local vs shared callable capability (RPA Library/API Workflow/custom connector, built before consumers).
- **Runtime/resource locality:**
  - Desktop apps, Excel/Office, file shares, on-prem database, terminal/mainframe and Citrix require an in-environment robot → RPA, regardless of determinism or API.
  - Exceptions: confirmed Automation Relay for on-prem HTTP(S), and robot-hosted Coded Functions.
  - Windows, cross-platform, serverless and user desktop determine compatibility, robot type and licensing (RPA template §11 Project Mode Decision).
- **Existing estate:** processes, API Workflows, connectors (`uip is connectors list`), tenant libraries (Step 5), IXP models, and user-named resources; reuse before build.
- **Trigger, confidence:** record trigger, evidence, and unknowns; unknowns become `[SME REVIEW]`, and genuinely ambiguous product choice goes to Step 10, never a silent default.

Close by typing every extracted step using [Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step). It produces the step→executor map for Level 1 (layer 2 before layer 3). Level 1 first folds absorbed capabilities into their hosts ([Decision table → Absorption fold](../shared/product-selection-guide.md#decision-table)), then reads the folded map: in-process capabilities are integrated components, not orchestration triggers. Carry the profile and map into Step 10 and `## Recommended Scope` so each choice is auditable as need → product. Hybrid, decomposed designs are normal: AI decides, governed RPA/API execute, Maestro orchestrates where needed, and HITL gates risk — not one monolithic flow. Level 1 matches the whole profile; keywords are evidence only.

### Step 8: Run Levels in Order

At every level, apply delivery model and user exclusions through the Constraint Gate ([Product Selection Guide → Constraint Gate](../shared/product-selection-guide.md#constraint-gate), [platform-availability-guide.md](../shared/platform-availability-guide.md)). Follow [Product Selection Guide § Levels of Decision](../shared/product-selection-guide.md#levels-of-decision):

1. Level 0 first.
2. Levels 1+ only on `proceed` / `proceed-with-redesign` / `partial`.
3. Level 1.5 for an RPA primary, or per RPA project through Level 1.75 Pass C.
4. Level 1.75 when Level 1 = Solution or the user picks "Solution (customize)" in Step 10.
5. Level 2.5 Part A per RPA Process project; Part B always.

Feed results to Step 10 and Phase 2.

Level 2 (XAML / Coded / Hybrid) is decided per RPA project at Phase 2 Step 2 using [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Detect Level 3 add-ons (HITL, Integration Service, etc.) in analysis and flag them in Phase 2 Step 4. Run per-task placement ([Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step)) twice: at Step 7, for the step→executor map that feeds Level 1; at Phase 2 Steps 3–4, to record placements in the template inventories.

### Step 9: Check for Agent/Coded App Gaps

If primary is **Agents** or **Coded Apps** and required product information is missing, run [scope-recommendation-guide.md](scope-recommendation-guide.md) § Gap Handling for Agent / Coded App. Never auto-fallback: the user chooses explicitly.

### Step 10: Summary, Interview, Scope Confirmation

Step 10 runs four moves in this order; autonomous mode skips it (Step 1), and a caller's request runs only move 4, and only when the choice is genuinely ambiguous (Verb Rule 14):

1. **Summary.** Emit the summary block below.
2. **Interview offer.** Build the gap list and make the offer of [interview-guide.md](../interview/interview-guide.md); it is not made when the list holds no entry to ask.
   - **Accepted:** run the interview on the P0 `before writing` entries. Its answers replace the Clarifying Questions block; every other entry is written as an SDD item.
   - **Declined, or not offered:** the Clarifying Questions block and its limit (end of this step).
3. **Product again on a P0 change.** An answer that changes a need-profile factor (Step 7) reruns Step 8, then Step 9 when its condition now holds, and the summary's Recommended Scope block is emitted again.
4. **Scope confirmation**, on the answered facts — the structured question below.

**The summary.** Emit [scope-recommendation-guide.md](scope-recommendation-guide.md) § Presenting the Recommendation, recommended scope first and alternatives after it:

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
<NUMBERED_QUESTIONS_IF_ANY — left out when the interview is offered; a decline asks them then>
```

**The confirmation.** Ask the guide's structured confirmation question: recommendation option 1, single-product alternatives, then "Solution (customize)". **If the user picks "Solution (customize)":** re-run Level 1.75's customize branch, re-emit the summary with the customized project list, and re-ask, within the revision cap of [SKILL.md § Prompt Budget](../../SKILL.md#prompt-budget); then proceed with the latest composition. **If the user picks a single-product alternative:** re-run Step 8 with that forced primary, including Level 1.5 for RPA.

**Without the interview**, ask the clarifying questions in one round — at most 5, at most 4 per structured question ([SKILL.md § Prompt Budget](../../SKILL.md#prompt-budget)); if the user cannot answer some, tag those items as `[SME REVIEW]` and proceed. With it, every point left open keeps its `[SME REVIEW]` marker, and Phase 3 Step 3 asks the items the interview did not ([sdd-writing-guide.md](sdd-writing-guide.md)).

## Phase 2 — Architecture Review

### Step 1: Load the Template(s)

Use [Template Mapping table](scope-recommendation-guide.md#template-mapping): load the matching single-product template, or for Solution the overview plus one template per project in the Level 2.5 unified list. RPA Master Projects share one RPA template across sub-projects; unrelated RPA projects get separate files.

The SDD is automation-type-agnostic: include only in-scope type coverage. Solution overview component inventory lists every component and type (RPA / API Workflow / Agent / Maestro Flow · BPMN · Case / Coded or Low-code App / DU-IXP / connector / HITL). Include type-specific detail (Agent Configuration, Queue Architecture, API schemas, Gateways, Case stages, etc.) only when applicable; never add N/A filler, never assume an agentic (or RPA-only) shape, and delete inapplicable rows. Replicate per-instance sections (e.g., one Agent Configuration per agent).

### Step 2: Generate the Architectural Core

Generate the sections the template's `Phase 2 sections:` line names. What they hinge on:

- **RPA:** §10 applies Level 2.5 Part A ([rpa-product-guide.md](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals)) — Single vs Master Project, sub-projects, queue schema; §11 Project Structure is the most load-bearing section — the genome's components come from it; §13 applies Level 2 ([rpa-product-guide.md](rpa-product-guide.md#level-2--authoring-mode)); §14 infers NuGet packages from §9 and the process steps.
- **Maestro BPMN:** §3 Business Rules and Decisions carries the decision tables and the reasoning list ([Business Rules Guide](business-rules-guide.md)).
- **Agents:** §9 Project Structure states Coded vs Low-code. **API Workflows:** §4 Execution Flow is high-level steps, no JavaScript.
- **Case Management:** Sections 1–4 per [case-product-guide.md](case-product-guide.md).

### Step 3: Decompose Steps Into Implementation Units

| Product | Primary Inventory | Unit Type |
|---|---|---|
| RPA (Single Project) | Workflow Inventory | `.xaml` or `.cs` workflow files |
| RPA (Master Project) | Workflow Inventory **per sub-project** | `.xaml` or `.cs` workflow files, grouped by sub-project |
| Flow | Nodes Inventory | Flow nodes |
| BPMN | §2 Steps | One row per step |
| Case | §2 Stages & Tasks | Stage blocks plus task summary/detail blocks |
| Agents | Tools | Python functions, RPA/API workflow bindings |
| Coded Apps | Pages + Components | Routes and React/Angular/Vue components |
| API Workflows | Execution Flow steps | Activities (HTTP, Connector, Script) |

Each unit must have: **a concrete responsibility, specific PDD step references, and defined inputs/outputs.** Type and place each step using [Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step):

- deterministic validate/transfer → RPA or API;
- document collect → IXP;
- judgment decide → Agent;
- atomic transform/compute → Function;
- review/sign-off → HITL;
- aggregate → Data Fabric.

Record placement in the inventory; every non-primary placement becomes an integrated component in Step 4.

For RPA Master Project, assign each PDD step to a §10 sub-project, then, within each sub-project, decompose its assigned steps into workflow files. In REFramework sub-projects, Init, GetTransactionData, Process, and SetTransactionStatus come from the framework; inventory only Process-specific workflows.

### Step 4: Flag Integrated Components

For each Phase 1 integrated component and non-primary placement, flag the template section:

- **HITL:** flag each touchpoint for the owner its host names in [component-placement-guide.md § HITL](../shared/component-placement-guide.md#hitl-human-in-the-loop).
- **Integration Service connectors:** list in Application Inventory (RPA) or the Connectors section (other types); check `uip is connectors list`; route existing connector configuration to `uipath-platform`, custom build to `uipath-connector-builder`.
- **IXP / Document Understanding models:** for semi-structured extraction, list in the host's "IXP / Document Understanding Models" table (Flow/BPMN/Case/Agent/RPA); for API Workflow or Coded App primary, make a row in §Solution / Project Breakdown. Route implementation to `uipath-ixp`, before consumers.
- **Coded Functions** (TypeScript / JavaScript / Python): atomic deterministic transform / compute (e.g., parsing, scoring, custom-auth API calls, Integration Service connection queries) only when justified by [placement rule 6](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step); keep host-native logic in host inventory. List in host "Coded Functions" table (Flow/BPMN/Case/Agent); route to `uipath-functions` before consumers; no per-project SDD file (see [Template Mapping](scope-recommendation-guide.md#template-mapping)).
- **RPA called by Flow/BPMN/Agent/Case:** list in Integrated Components; implementation creates the RPA project.
- **API Workflow called by Flow/BPMN/Agent/Case:** extract only when justified by [placement rule 6](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step) (host cannot call natively, 2+ consumers, or independent lifecycle). Otherwise record host inventory `Access Method = Direct HTTP`. Extracted workflow goes in Integrated Components; implementation creates it. Extraction never changes `SDD scope` ([derived-component rule](../shared/product-selection-guide.md#solution-signals)).

### Step 5: Present Architecture for Review

Present the architectural core to the user, in the shape of the product guide's § Design Review when the product guide has one. Wait for approval or adjustments. A design a build skill handed over presents the build options the caller passed ([sdd-writing-guide.md](sdd-writing-guide.md) § Design Handed Over by a Build Skill). A caller's `execution: interactive` request runs this review as its one checkpoint; `autonomous` skips it (Verb Rule 14).

Any response without specific change requests approves it, including "looks good", "ok", "proceed", "yes", or a topic change. Incorporate specific changes and re-present, within the revision cap of [SKILL.md § Prompt Budget](../../SKILL.md#prompt-budget); then proceed with the latest and tag disagreements `[SME REVIEW]`.

## Phase 3 — Full SDD Generation

Read [sdd-writing-guide.md](sdd-writing-guide.md) whole before writing anything. It governs the skeleton hard gate, remaining sections, SME resolution, template-superset check, `ready` flip, turn boundary, and following genome. Never write Phase 3 from memory.
