# Design Guide — the `design` verb

`design` converts a PDD or other process-knowledge source into an implementation-ready SDD in three phases: **Phase 1** analyzes the source and selects scope, **Phase 2** reviews architecture, and **Phase 3** incrementally writes the full SDD and flips it to `ready` ([sdd-writing-guide.md](sdd-writing-guide.md)). The next turn writes the genome from the `ready` SDD (Verb Rule 8). The source may be a document or the request; this applies to every product, including Case Management. Ask all user questions in numbered-choice format.

## Verb Rules

These supplement the Critical Rules in [SKILL.md](../../SKILL.md).

1. **Select scope before architecture and gate every product by platform constraints.** Choose one product (RPA Process/Library/Test Auto, Maestro Flow, Maestro BPMN, Case, Agents, Coded Apps, API Workflows) or a multi-project Solution. Use [Product Selection Guide](../shared/product-selection-guide.md): Constraint Gate → Level 1 → 1.5 (RPA sub-type) → 1.75 (Solution composition) → 2.5 (project decomposition); 1.75 and 2.5 are in [solution-composition-guide.md](solution-composition-guide.md). Ask delivery model (Cloud / Automation Suite / standalone) at entry; [platform-availability-guide.md](../shared/platform-availability-guide.md) blocks unavailable products. Never re-offer user-excluded products.
2. **The SDD is architecture only; it has no task lists.** It contains Project Structure, Data Definitions, Testing Strategy, and so on. `author` writes the implementation genome from it.
<!--skill-flavor:sdd-no-task-lists:start-->
Never put Task 1 / Task N templates or *implementation* tasks created with the task-list tool in the SDD. End it with `## Next Steps`. Progress-tracking tasks created with the task-list tool are allowed separately.
<!--skill-flavor:sdd-no-task-lists:end-->
3. **Put both `## Planner Handoff` and `<!-- planner-handoff:v1 -->` in every SDD.** They are the load-bearing detection contract; § Choosing the Verb detects either. Apply fields and rules in [sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 2.
4. **Treat the template as a hard superset contract.** Write single-product scope to `<PROCESS_NAME_KEBAB>-sdd.md`; write Solution scope to `<SOLUTION_NAME_KEBAB>-solution-sdd.md` plus `<PROJECT_NAME_KEBAB>-sdd.md` per project. Use a user-specified SDD path instead. Read each selected template end to end before generating, never only a head slice or heading list; column contracts sit deep in the file. Copy every table's column headers verbatim. After writing, diff generated H2/H3 headings against the template TOC; the generated set MUST be a superset. A missing required H2/H3 is an SDD defect, not `[SME REVIEW]`; regenerate it.
5. **Testing is mandatory and thorough.** Write a full Testing Strategy covering happy path, edge cases, error scenarios, and e2e for Master Projects; never offer “happy path only.” Specialists may scope down at execution, not in the SDD.
<!--skill-flavor:solution-terminal-artifact:start-->
6. **A Solution build ends in a packed `.uipx`.** `## Next Steps` points to `uipath-solution`, which packs it; a bare project folder is not the deliverable.
<!--skill-flavor:solution-terminal-artifact:end-->
Exception: if the Constraint Gate blocks Solutions for standalone, Automation Suite older than 2.2510, or user exclusion, route `Next Steps` to per-package Orchestrator publish via `uipath-platform`.
7. **Design resolves identities only.** A resource the design names is looked up (the Level 0 estate sweep, the tenant library search, where Step 2.5 applies) and adopted when one match is confident. Record ambiguous or missing resources under their intended names with `[SME REVIEW]`. Schema discovery, scaffolding, and create-on-missing are build concerns recorded as build decisions; `design` never runs them.
8. **Every `ready` SDD gets its genome next turn, including a design-only request,** except when a build skill handed over design, which returns to that skill. Apply sequence and conditions in [sdd-writing-guide.md](sdd-writing-guide.md) § Step 3. Revising an SDD whose genome is already on disk also updates and checks that genome: [sdd-writing-guide.md](sdd-writing-guide.md) § Keeping the Genome Current.
9. **Write the skeleton first and flip `ready` last; the SDD write is a turn boundary.** Put the skeleton on disk before other Phase 3 sections so an early-ending turn leaves it available. `[SME REVIEW]` gates only the `ready` flip, not skeleton writing. Follow [sdd-writing-guide.md](sdd-writing-guide.md) Step 0; next turns follow its § Step 3. Scope and UI answers flow to the genome through the SDD.
10. **Keep source wording.** Preserve roles, domain nouns, stage/step labels, decision outcomes, and system names exactly (`CFO`, `Vendor`, `Needs Info`, `Workday`), never homogenised to a synonym (`Approver`, `Supplier`, `the HR system`). Only mechanical derivations change names: PascalCase project/case names, kebab-case filenames, camelCase variables.
11. **Resolve conflicts in this order:** platform constraints (delivery model and product schema) → stated or implied regulatory/compliance constraints → tenant evidence matching the work → user statement → source documents → template/product-guide defaults. Record a lower-level override as an autonomous Decisions Made row or a Step 5 review line.
12. **A user-named product is primary** unless Constraint Gate blocks it or Level 0 finds the work should not be automated. Level 1 confirms it; Levels 1.5–3 still run inside it.
13. **Every automation-built key is retry-stable.** Build filenames, sequence numbers, message IDs, and queue references from item identity (reference, GUID, or source ID), never clock or write-time counter, so retries find existing output.
14. **A caller's design request changes only the steps named by its guide.** A `planner-design-request: v1` block carries `execution`, limits interactive mode to the Phase 2 Step 5 checkpoint, lets autonomous mode stop only for a hard blocker, and ends with `planner-design-result: v1`: [caller-request-guide.md](caller-request-guide.md).

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole |
| start | request carries `planner-design-request: v1` | [caller-request-guide.md](caller-request-guide.md) whole |
| Phase 1 Step 0 | — | [platform-availability-guide.md](../shared/platform-availability-guide.md) § Resolving the Delivery Model |
| Phase 1 Step 1 | — | [pdd-analysis-guide.md](../shared/pdd-analysis-guide.md) whole |
| Phase 1 Step 2.5 | source describes RPA-bearing work (UI, Excel or Office, files, desktop or on-prem systems) and prompt allows `uip` commands | [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) |
| Phase 1 Steps 3.5–6 | — | [product-selection-guide.md](../shared/product-selection-guide.md) whole; [solution-composition-guide.md](solution-composition-guide.md) § Level 2.5 — Project Decomposition; [component-placement-guide.md](../shared/component-placement-guide.md) § Per-task component placement (the to-be, per step) |
| Phase 1 Steps 4–6 | Level 1 = Solution, or user picks "Solution (customize)" | solution-composition-guide.md § Level 1.75 — Solution Composition |
| Phase 1 Step 5 | primary is Agents or Coded Apps and product-specific information is missing | [scope-recommendation-guide.md](scope-recommendation-guide.md) § Gap Handling for Agent / Coded App |
| Phase 1 Step 6 | — | scope-recommendation-guide.md § Presenting the Recommendation; its Summary block defines Recommended Scope, Project List, and Queue Architecture formats |
| Phase 1 Step 3.5 or Phase 2 Step 4 | external system needs Integration Service check, or Level 3 add-on is in play (HITL, Integration Service, API Workflow as integrated component, reusable/shared assets) | component-placement-guide.md § Level 3 — Capability Add-ons |
| Phase 2 Step 1 | — | scope-recommendation-guide.md § Template Mapping |
| Phase 1 Step 4 | whenever Constraint Gate runs; Cloud variants (Public Sector, Dedicated, Test Cloud) and tenant entitlements may block products | [platform-availability-guide.md](../shared/platform-availability-guide.md) |
| Phase 1 Step 4 | Level 1 = RPA, or Solution includes RPA | [rpa-product-guide.md](rpa-product-guide.md) (Level 1.5, Level 2, Level 2.5 Part A, R-07 naming, REFramework) |
| Phase 1 Step 4 | Level 1 = Case Management, or Solution includes a case | [case-product-guide.md](case-product-guide.md) and [case-data-and-time-guide.md](case-data-and-time-guide.md), both whole |
| Phase 2 Step 5 | design includes a case | [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Presenting the Case Design |
| Phase 1 Step 2 | source signals non-scriptable interactive sign-in (hardware 2FA token, smart card, biometric) | [attended-reauth-pattern-guide.md](attended-reauth-pattern-guide.md) |
| Phase 2 Step 1 | — | SDD template(s) named by Template Mapping, in `../assets/templates/` |
| Phase 2 Step 2 | filling §14 Packages or equivalent | [package-selection-guide.md](package-selection-guide.md) |
| Phase 2 Step 2 or Phase 3 | filling RPA §4 Business Rules or BPMN §5 Gateways | [business-rules-guide.md](business-rules-guide.md) |
| Phase 3 | Phase 2 Step 5 approved, or skipped in autonomous mode | [sdd-writing-guide.md](sdd-writing-guide.md) whole; its § Read Plan names Phase 3 reads |

## Anti-patterns

1. Do not copy PDD structure into the SDD; reorganize for implementation.
2. Do not default to RPA Process when the need profile points elsewhere. Use the Product Selection Guide decision tree, not keywords: genuine judgment/reasoning → Agents; stages/SLA/approval lifecycle → Case Management; “AI” over a rule-expressible decision remains RPA. If multiple coordinated projects are described, offer Solution rather than forcing one product.
3. Do not rename `## Planner Handoff` or strip `<!-- planner-handoff:v1 -->`; either signal detects the SDD, but removing both silently breaks detection.

## Phase 1 — PDD Analysis & Scope Selection

### Step 0: Determine Execution Mode & Delivery Model

Before fully reading the PDD, search for platform signals ("Automation Suite", "on-prem", "self-hosted", "Orchestrator", "cloud", tenant URL), because the skip rule depends on them. Then ask one structured prompt containing execution mode and delivery model, plus the custom-host follow-up when applicable (maximum four questions). Run [platform-availability-guide.md § Resolving the Delivery Model](../shared/platform-availability-guide.md#resolving-the-delivery-model) first, including its preflight, Question 2, custom-host follow-up, and skip rule.

**Question 1 — Execution mode:**

> How should I handle this SDD generation? (The SDD is written this turn; its genome — the build blueprint — is written from the finished SDD on the next turn.)
>
> 1. **Autonomous** *(recommended)* — read the PDD, make decisions, generate the SDD, then write its genome next turn; interrupt only for hard blockers (PDD unreadable, Agent/Coded App critical gap, unresolved `[SME REVIEW]` before finalization).
> 2. **Interactive** — pause at each phase checkpoint (summary, architecture, final SDD) for review.

Skip Question 1 when context states the mode ("autonomous", "don't pause for checkpoints", "interactive review"). A caller's `execution` answers it; ask only if missing (Verb Rule 14). When both questions are resolved from context, skip the structured prompt and record both values.

Record execution mode and delivery model in `## Planner Handoff` ([sdd-writing-guide.md](sdd-writing-guide.md) Step 2) and propagate them to the genome: execution controls follow-up rounds; delivery model applies to every named component.

**Autonomous:** skip Phase 1 summary presentation and Phase 2 review, but persist `## Recommended Scope` in the SDD ([sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 3). Ask only blocking Step 0 questions, the Agent/Coded App gap question (Step 5), and one SME prompt containing items without defensible defaults ([sdd-writing-guide.md](sdd-writing-guide.md) Step 1.5). Take recommended options for all other confirmations (RPA subtype, scope, tenant-library pick, revision), record them in Decisions Made. **Insert a "Decisions Made" block** immediately after Planner Handoff and before any other section, listing the five highest-leverage architectural picks and one-sentence reasons, using the exact format in [sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 3. Do **NOT** ask a structured question — the picks are decided autonomously; the block makes them scannable in the SDD's first screenful.

**Interactive:** present and await every checkpoint below.

### Step 0.5: Create Progress Tasks

<!--skill-flavor:progress-tasks:start-->
Create progress-tracking tasks with the task-list tool; a host without that tool skips this step:

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

The genome task remains `pending` when SDD writing ends the turn; the genome turn changes it to `in_progress`, then `completed`. Omit it for a design handed over by a build skill (Verb Rule 8). Mark each task `in_progress` at start and `completed` at end. Creation/update is best-effort and never blocks SDD output: if a call fails, warn once, continue without progress tasks, and never retry. Skeleton writing is task 4, never the last ([sdd-writing-guide.md](sdd-writing-guide.md#step-0-write-the-sdd-skeleton-to-disk--hard-gate) Step 0).

These tasks track SDD generation.
<!--skill-flavor:progress-tasks:end-->
The genome `author` writes after the SDD and is the implementation input; do not create implementation tasks here.

### Step 1: Read the PDD

0. **No document** (for example, “design X”): treat the request and attachments as source; read every attached/named file, then continue at Step 2. Step 3 finds gaps and Step 6 asks user-only questions.
1. Route input by format: Markdown (`.md`) and plain text (`.txt`) directly; PDF (`.pdf`) by page range; Word (`.docx`, `.doc`) converted to Markdown; pasted text from conversation. Apply [PDD Analysis Guide → Supported Input Formats](../shared/pdd-analysis-guide.md#supported-input-formats). Any process-knowledge source works, including Confluence, BPMN (`.bpmn`), meeting/Zoom transcript, SOP, or requirements document ([Accepted process-knowledge sources](../shared/pdd-analysis-guide.md#accepted-process-knowledge-sources)); use heavier Phase 1 elicitation for less-structured sources. Extract both AS-IS and TO-BE ([As-Is and To-Be Process](../shared/pdd-analysis-guide.md#as-is-and-to-be-process)).
2. PDFs: under 10 pages, read all in one pass and skip ToC; 10–50 pages, read ToC then overview → steps → exceptions → applications → credentials; over 50 pages, read ToC, prioritize overview/steps/exceptions and extract while reading, then read the remainder.
3. For pasted text over 3000 words, ask the user to paste sections.
4. If unreadable (corrupt PDF, password-protected, unsupported), tell the user and request another format. If it contains no process (no steps, applications, or exceptions), tell the user and stop; less-structured process sources continue with heavier elicitation.
5. If not English, ask unless caller `language` answers it:

   > The PDD appears to be in <LANGUAGE>. Which language should the SDD use?
   >
   > 1. **English** *(recommended)* — SDD in English for broadest tool compatibility
   > 2. **<LANGUAGE>** — SDD in the same language as the PDD

   Keep section headings and structural identifiers (BR-01, B1, E1) in English regardless of choice.

### Step 2: Extract Structured Information

Follow [PDD Analysis Guide](../shared/pdd-analysis-guide.md) and build this model:

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

Key Contacts (SA, BA, developers, PM, SME / Process Owner) populate the §1 Delivery Team table of the RPA template; include only roles the PDD explicitly names; do not invent or mark silent rows `[SME REVIEW]`, omit them.

### Step 2.5: Tenant Library Discovery

The tenant feed, not the PDD, identifies deployed libraries. Run [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) in BOTH Autonomous and Interactive modes to populate §14 Packages and §16 “Shared libraries referenced”. Skip for non-RPA primaries (Agents, Coded Apps, Flow, BPMN, Case, API Workflows); the [Level 0 estate sweep](../shared/product-selection-guide.md#estate-sweep) (deployed processes, agents, Maestro processes, IXP projects, solutions, connections) still runs for every scope when evaluating the suitability gate. Keyword source for guide step 2 is PDD Application Inventory plus org-prefix terms (`Common`, `Shared`, `<Company>` if mentioned). Map each selected library to one row in every sub-project §14 table and its package ID to §16 Deployment Environment → “Shared libraries referenced”. If auth preflight fails, use the guide's manual fallback and propagate user-named libraries identically.

**This step is best-effort — it never blocks SDD output.** If auth errors or is unavailable, **Autonomous mode skips library discovery and proceeds with public NuGet only** — do not retry or troubleshoot auth mid-generation, and do not pause. Skip entirely when the prompt forbids `uip` commands.

### Step 3: Detect Gaps

Use the Gap Detection Checklist in [PDD Analysis Guide](../shared/pdd-analysis-guide.md); classify each gap `[DEFAULT]` or `[SME REVIEW]`.

### Step 3.5: Synthesize the Need

Distill the model before product selection; choose from the whole profile, not keywords:

- **Core need/outcome:** state outcome and KPI (cycle time, manual effort, quality/accuracy, cost, throughput, or compliance); design TO-BE, not as-is repetition.
- **Decision nature:** deterministic rule-expressible (same input → same output) favors RPA/API/rules; genuine judgment/reasoning over ambiguity favors Agents. Assess per process and step; this is not the sole gate.
- **Input:** structured/predictable versus messy/unstructured (email, free text, varied documents → Agent or IXP).
- **Integration:** for every external system check stable API / **Integration Service connector** and executor-runtime reachability under delivery model; on-prem HTTP(S) APIs may use Automation Relay (placement rule 5). Reuse connectors; if absent, API Workflows, RPA, and coded Agents use Direct HTTP, while IS-only surfaces (Maestro Flow/BPMN/Case connector nodes, low-code Agent tools) need `uipath-connector-builder` or API Workflow wrapper—see [Component Placement Guide → Integration Service](../shared/component-placement-guide.md#integration-service). Verify with `uip is connectors list`; never assume a connector exists. UI-only system → RPA.
- **Interaction:** system-to-system; UI; human-in-loop (immediate attended action or **asynchronous approval**—async inside one process → long-running RPA + Action Center); user-facing app.
- **State:** atomic; transactional/per-item retryable; long-running/suspending. Long-running within one process → RPA long-running workflow; across products → Maestro.
- **Coordination:** single task; linear/branching pipeline; staged case lifecycle (stages + SLA); structured control flow (parallel/events/subprocess). Use [PDD Analysis Guide → Detailed Process Map](../shared/pdd-analysis-guide.md#detailed-process-map).
- **Volume/latency/cost:** high-volume repeatable favors deterministic; agentic cost is higher-variance, so estimate per model/tenant and justify agentic at volume; note any latency requirement.
- **Risk/reversibility/auditability:** high-risk, irreversible, or low-confidence steps need HITL; compliance-critical work needs deterministic auditable records.
- **Change/volatility:** record input/form/rule volatility; uncaptured volatility is a top cause of production breakage; use IXP for changeable documents.
- **Reuse:** local operation versus shared callable capability (RPA Library / API Workflow / custom connector, built before consumers).
- **Runtime/locality:** desktop apps, Excel/Office, file shares, on-prem databases, terminal/mainframe, and Citrix require a robot inside the environment → RPA regardless of determinism/API, except confirmed Automation Relay for on-prem HTTP(S) and robot-hosted Coded Functions (also inside). Windows, cross-platform, serverless, and user desktop determine compatibility, robot type, and licensing (§11 Project Mode Decision in RPA template).
- **Existing estate:** reuse deployed processes, API Workflows, connectors (`uip is connectors list`), tenant libraries (Step 2.5), IXP models, and user-named resources.
- **Trigger:** who/what starts it.
- **Confidence:** record evidence and unknowns; unknowns become `[SME REVIEW]`, and genuine product ambiguity goes to Step 6, never silent default.

Close by typing every extracted step with [Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step), producing the step→executor map for Level 1. Fold absorbed capabilities first ([Decision table → Absorption fold](../shared/product-selection-guide.md#decision-table)); in-process capabilities are integrated components, not orchestration triggers. Carry profile and map into the Step 6 summary and SDD `## Recommended Scope`, making every pick auditable as `need → product`. The dominant pattern is hybrid and decomposed into separate blocks — not one monolithic flow: AI decides, governed RPA/API executes, Maestro orchestrates when needed, and HITL gates risk. Level 1 uses the whole profile; ask when genuinely ambiguous.

### Step 4: Run Levels in Order

At every level, filter by Step 0 delivery model and user exclusions ([Product Selection Guide → Constraint Gate](../shared/product-selection-guide.md#constraint-gate), [platform-availability-guide.md](../shared/platform-availability-guide.md)). Follow [Product Selection Guide § Levels of Decision](../shared/product-selection-guide.md#levels-of-decision): Level 0 first; Levels 1+ only on `proceed` / `proceed-with-redesign` / `partial`; Level 1.5 for RPA primary or per RPA project through Level 1.75 Pass C; Level 1.75 when Level 1 = Solution or user chooses “Solution (customize)”; Level 2.5 Part A per RPA Process project; Part B always. Feed output to Step 6 and Phase 2.

Level 2 (XAML / Coded / Hybrid) is decided per RPA project at Phase 2 Step 2 via [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Detect Level 3 add-ons during analysis and flag them in Phase 2 Step 4. Run per-task placement at Step 3.5 and again at Phase 2 Steps 3–4 ([Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step)).

### Step 5: Check for Agent/Coded App Gaps

If primary is **Agents** or **Coded Apps** and required product information is missing, run [scope-recommendation-guide.md](scope-recommendation-guide.md) § Gap Handling for Agent / Coded App. Never auto-fallback; the user must choose.

### Step 6: Present Summary + Scope Recommendation

Emit the block in [scope-recommendation-guide.md](scope-recommendation-guide.md) § Presenting the Recommendation, with recommended scope first and alternatives afterward:

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

Ask the guide's structured confirmation question: recommendation option 1, single-product alternatives, then “Solution (customize)”. A caller skips this unless choice is genuinely ambiguous (Verb Rule 14). **If the user picks “Solution (customize)”:** re-run Level 1.75 per the customize branch in the guide, re-emit the summary, and re-ask; maximum 3 revisions, then proceed with latest composition. **If the user picks a single-product alternative:** re-run Step 4 with it as the forced primary, including Level 1.5 for RPA. Ask at most 5 clarifying questions in one round; unanswered items become `[SME REVIEW]` and work continues.

## Phase 2 — Architecture Review

### Step 1: Load the Template(s)

Use [Template Mapping table](scope-recommendation-guide.md#template-mapping). Single-product scope loads its primary template. Solution loads the solution overview plus one template per project in the Level 2.5 unified project list; RPA Master Projects share one RPA template across sub-projects, unrelated RPA projects have separate files.

The SDD is type-agnostic: include only in-scope type coverage. Solution overview component inventory lists every component and type (RPA / API Workflow / Agent / Maestro Flow · BPMN · Case / Coded or Low-code App / DU-IXP / connector / HITL). Include Agent Configuration, Queue Architecture, API schemas, Gateways, Case stages, etc. **only for the types actually in scope**; never emit N/A filler, and never assume an agentic (or RPA-only) shape; delete inapplicable rows; replicate per-instance sections (e.g., one Agent Configuration per agent).

### Step 2: Generate the Architectural Core

Generate sections named by the template's `Phase 2 sections:` line (Case template: Sections 1–4):

- **RPA:** §10 applies Level 2.5 Part A ([rpa-product-guide.md](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals)) for Single/Master Project, sub-projects, and queue schema; §11 Project Structure (the most load-bearing section) drives genome components; §13 applies Level 2 ([rpa-product-guide.md](rpa-product-guide.md#level-2--authoring-mode)); §14 infers NuGet packages from §9 and steps.
- **Maestro BPMN:** §5 Gateways contains decision tables and reasoning list ([Business Rules Guide](business-rules-guide.md)).
- **Agents:** §9 Project Structure states Coded versus Low-code. **API Workflows:** §4 Execution Flow is high-level only, with no JavaScript.
- **Case Management:** Sections 1–4 follow [case-product-guide.md](case-product-guide.md) and [case-data-and-time-guide.md](case-data-and-time-guide.md). Render long headings (`## Section 1: Case Definition`, …): `uipath-maestro-case` parses heading text verbatim; `§N` is planner notation only.

### Step 3: Decompose Steps Into Implementation Units

Map each PDD step to the primary inventory:

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

Every unit needs concrete responsibility, specific PDD step references, and defined inputs/outputs. Type each verb and place it using [Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step): deterministic validate/transfer → RPA or API; document collect → IXP; judgment decide → Agent; atomic transform/compute → Function; review/sign-off → HITL; aggregate → Data Fabric. Record placement in the inventory; every non-primary placement becomes an integrated component in Step 4.

For RPA Master Project: (1) assign each PDD step to a sub-project using §10 sub-projects table; (2) decompose assigned steps into workflow files; (3) for REFramework sub-projects, Init, GetTransactionData, Process, and SetTransactionStatus come from the framework, so inventory only Process-specific workflows.

### Step 4: Flag Integrated Components

For each Phase 1 integrated component and each non-primary placement, flag the template section:

- **HITL:** Flow hosts flag touchpoints and route implementation to `uipath-human-in-the-loop`; Coded Agents put escalation in the `uipath-agents` build task because HITL defers coded-agent wiring; BPMN `userTask` is flagged in §9 HITL Touchpoints and authored inline by `uipath-maestro-bpmn` (no HITL-skill task); Case uses an `action` task detail block in §2 Stages & Tasks with Action App intent (never HITL skill); RPA flags Action Center / long-running workflow.
- **Integration Service connectors:** list in Application Inventory (RPA) or Connectors section (others); check `uip is connectors list`; route implementation to `uipath-platform` for an existing connector or `uipath-connector-builder` when none exists.
- **IXP / Document Understanding models:** for semi-structured extraction, list in host “IXP / Document Understanding Models” table (Flow / BPMN / Case / Agent / RPA); for API Workflow or Coded App primary, make a row in §Solution / Project Breakdown. Route to `uipath-ixp`, before consumers.
- **Coded Functions:** TypeScript / JavaScript / Python for atomic deterministic transform/compute (parsing, scoring, custom-auth API calls, IS-connection queries), only when justified by [placement rule 6](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step); host-native logic remains in host inventory. List in host “Coded Functions” table (Flow / BPMN / Case / Agent); route to `uipath-functions` before consumers; no per-project SDD file (see [Template Mapping](scope-recommendation-guide.md#template-mapping)).
- **RPA processes called by Flow/BPMN/Agent/Case:** list in Integrated Components; implementation creates the RPA project.
- **API Workflows called by Flow/BPMN/Agent/Case:** extract only when justified by [placement rule 6](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step) (host cannot call natively, 2+ consumers, or independent lifecycle). A host-capable direct call stays in host inventory as `Access Method = Direct HTTP`; otherwise list in Integrated Components and implementation creates the API Workflow project. Extraction never changes `SDD scope` ([derived-component rule](../shared/product-selection-guide.md#solution-signals)).

### Step 5: Present Architecture for Review

Present the architectural core; for Case Management use [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Presenting the Case Design. Wait for approval or adjustments. A build handoff presents caller-provided build options ([sdd-writing-guide.md](sdd-writing-guide.md) § Design Handed Over by a Build Skill). `execution: interactive` uses this as its one checkpoint; autonomous skips it (Verb Rule 14).

Any response without specific changes approves, including “looks good”, “ok”, “proceed”, “yes”, or topic change. For requested changes, incorporate and re-present; maximum 3 revisions, then proceed with latest and tag disagreements `[SME REVIEW]`.

## Phase 3 — Full SDD Generation

Read [sdd-writing-guide.md](sdd-writing-guide.md) whole before writing: it defines the skeleton hard gate, remaining sections, SME resolution, template-superset check, `ready` flip, turn boundary, and following genome. Never write Phase 3 from memory.