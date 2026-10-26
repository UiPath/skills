# SDD Generation Guide

Transform a PDD into an SDD using the 3-phase interaction model in SKILL.md.

## Phase 1 — PDD Analysis & Scope Selection

### Step 0: Determine Execution Mode & Delivery Model

Before reading the PDD, make one `AskUserQuestion` call with two question objects: execution mode and delivery model. If the custom-host follow-up applies, replace Question 2 with two objects (three total; the tool accepts up to four). Delivery model gates every product decision; see [Product Selection Guide → Constraint Gate](product-selection-guide.md#constraint-gate).

**Run the delivery-model CLI preflight first, best-effort:**

```bash
uip login status --output json
```

Use authenticated `Data.BaseUrl` and tenant. `cloud.uipath.com` means **Automation Cloud** (full catalog, entitlement-gated per tenant); another `*.uipath.com` means an **Automation Cloud variant** (Public Sector / Dedicated / Test Cloud / region-specific): verify each gated product (Maestro, Agents, Coded Apps, API Workflows, Solutions) against tenant entitlements and mark unverifiable products `[SME REVIEW]`. Any other host means **self-hosted — Automation Suite OR standalone Orchestrator (ambiguous)**. `Status` ≠ `Logged in`, an error, or missing `BaseUrl` means unknown: ask Question 2 fully and tell the user that running `uip login` first enables detection next run. Known cloud hosts skip the platform question; a custom host never does.

For an ambiguous custom host, show `<HOST>` and put these objects in the same call:

**Question 2a — Platform:**

> I detected a self-hosted URL (`<HOST>`). Which platform is it?
>
> 1. **Automation Suite** — product + capability availability is gated by version (and the EKS/AKS install profile for the Maestro/Agents stack)
> 2. **Standalone Orchestrator (MSI)** — Orchestrator + Studio/Robot only; most modern products unavailable

**Question 2b — Automation Suite version (only if 2a = Automation Suite):**

> Which Automation Suite version?
>
> 1. **2.2510 or later**
> 2. **2024.10**
> 3. **Older**
> 4. **Not sure / not Automation Suite**

Record delivery model and, for Automation Suite, version; gate capabilities/products with [platform-availability-guide.md](platform-availability-guide.md). Never silently treat a custom host as Automation Suite. If version is unknown, gate against the latest matrix column and add an `[SME REVIEW]` version row in §16 Deployment Environment. An explicit user-stated model or PDD signal overrides preflight. Preflight is best-effort and never blocks (Rule G-8); on failure ask Question 2.

**Question 1 — Execution mode:**

> How should I handle this SDD generation?
>
> 1. **Autonomous** *(recommended)* — I will read the PDD, make all decisions, and generate the full SDD. I will only interrupt for hard blockers (PDD unreadable, Agent/Coded App missing critical info, unresolved `[SME REVIEW]` items before finalizing).
> 2. **Interactive** — I will pause at each phase checkpoint (summary, architecture, final SDD) for your review before proceeding.

**Question 2 — Delivery model:**

> Where will this automation run?
>
> 1. **UiPath Automation Cloud** — full product catalog available
> 2. **Automation Suite (self-hosted)** — product availability depends on the Suite version; I will gate recommendations accordingly
> 3. **Standalone Orchestrator (MSI)** — most restrictive; modern platform products unavailable
> 4. **Not sure** — I will proceed assuming Automation Cloud and flag the assumption as `[SME REVIEW]`

Skip Question 1 when the request states execution mode. Skip Question 2 only when fully resolved by the request, PDD signal (see [PDD Analysis Guide → Environment & Constraint Signals](pdd-analysis-guide.md#environment--constraint-signals)), or known cloud host. A custom/self-hosted host is not fully resolved. If both resolve from context, skip `AskUserQuestion`. Record both in the SDD `## Planner Handoff` header and pass them to Lane A and specialists.

In **Autonomous** mode, skip Phase 1 summary and Phase 2 architecture approval but persist `## Recommended Scope`; still ask Step 1.5 SME resolution and any Agent/Coded App gap question. Add `## Decisions Made` immediately after Planner Handoff and before all other sections, with the five highest-leverage architectural picks and one-sentence reasons, using Phase 3 Step 2's format; do not ask about those picks. In **Interactive** mode, await every checkpoint.

### Step 0.5: Create Progress Tasks

<!--skill-flavor:progress-tasks:start-->
Create these tasks with `TaskCreate`:

```
TaskCreate: subject="Read PDD and extract data",        activeForm="Reading PDD…"
TaskCreate: subject="Select product",                    activeForm="Selecting product…"
TaskCreate: subject="Generate architecture (Phase 2)",   activeForm="Generating architecture…"
TaskCreate: subject="Write SDD skeleton to disk",        activeForm="Writing SDD skeleton…"
TaskCreate: subject="Generate full SDD (Phase 3)",       activeForm="Generating SDD sections…"
TaskCreate: subject="Resolve SME review items",          activeForm="Resolving SME review items…"
TaskCreate: subject="Finalize SDD (Status: ready)",      activeForm="Finalizing SDD…"
```

Mark each `in_progress` on start and `completed` on completion. **Rule G-8:** task creation/update is best-effort and never blocks output. If any `TaskCreate` or `TaskUpdate` fails, warn the user once, continue without progress tasks, and do not retry; the SDD is authoritative. If creation failed, silently skip later updates. **Rule G-9:** task 4 is the disk write and precedes Phase 3; never reorder, collapse tasks 4 and 7, or make writing terminal. Implementation tasks belong to Lane A after Phase D; do not create them here.
<!--skill-flavor:progress-tasks:end-->

### Step 1: Read the PDD

Mark `Read PDD and extract data` `in_progress` when tasks exist.

1. Route `.md`/`.txt` to `Read`; `.pdf` to `Read` with `pages`; `.docx` to the conversion below; pasted text to conversation context. See [PDD Analysis Guide → Supported Input Formats](pdd-analysis-guide.md#supported-input-formats). A formal PDD is unnecessary: Confluence, BPMN (`.bpmn`), meeting/Zoom transcript, SOP, or requirements doc is acceptable ([Accepted process-knowledge sources](pdd-analysis-guide.md#accepted-process-knowledge-sources)); use heavier elicitation for less-structured sources. Extract AS-IS and TO-BE ([As-Is and To-Be Process](pdd-analysis-guide.md#as-is-and-to-be-process)).
2. PDFs: under 10 pages, read all once; 10–50, read ToC then overview → steps → exceptions → applications → credentials; over 50, read ToC and high-priority sections first, then the rest.
3. For pasted text over 3000 words, ask the user to paste sections.
4. `.docx` is binary: do not `Read` directly. Run from the destination directory:

```bash
# macOS / Linux / Git Bash:
bash <SKILL_DIR>/scripts/docx-extract.sh "<PDD_FILE_PATH>"
# Windows without Git Bash (Windows PowerShell 5.1 or pwsh 7+):
pwsh -File <SKILL_DIR>/scripts/docx-extract.ps1 "<PDD_FILE_PATH>"   # or: powershell -File ...
```

`<SKILL_DIR>` contains this skill's SKILL.md and `<PDD_FILE_PATH>` is the full `.docx` path. Read generated UTF-8 markdown and `-media/` screenshots; screenshots feed canonical-example extraction. Parse raw HTML `<table>` blocks. If pandoc is missing, relay its install command; if installation is impossible, say: "Please export the Word document as PDF or paste the content directly." Never use Word COM automation.
5. If unreadable (corrupt/password-protected/unsupported), explain and request another format. If not PDD-like (no process steps, application details, or exception handling), explain and stop.
6. For non-English PDDs, use `AskUserQuestion`:

> The PDD appears to be in <LANGUAGE>. Which language should the SDD use?
>
> 1. **English** *(recommended)* — SDD in English for broadest tool compatibility
> 2. **<LANGUAGE>** — SDD in the same language as the PDD

Keep headings and structural identifiers (BR-01, B1, E1) in English.

### Step 2: Extract Structured Information

Follow the [PDD Analysis Guide](pdd-analysis-guide.md). Build an internal model containing:

| Component | Source | Required |
|---|---|---|
| Process name/objective | Introduction | Yes |
| Key contacts | Process key contacts | No |
| Overview (schedule, volumes, FTEs) | Process overview | Yes |
| In-scope activities | In scope | Yes |
| Out-of-scope activities | Out of scope | Yes |
| Process steps | Detailed process map / steps | Yes |
| Business exceptions | Exceptions handling | Yes |
| System errors | Error mapping and handling | Yes |
| Application inventory | In-scope application details | Yes |
| Development prerequisites | Prerequisites for development | No |
| Credentials/assets | Credentials and asset management | Yes |
| Test data | Appendix | No |

Put explicitly named SA, BA, developers, PM, SME/Process Owner roles into §1 Delivery Team; omit unnamed roles, do not invent them or mark them `[SME REVIEW]`.

### Step 2.5: Tenant Library Discovery

Run [tenant-library-search-guide.md](tenant-library-search-guide.md) in both modes for RPA primaries. Keyword source step 2: PDD Application Inventory plus `Common`, `Shared`, and `<Company>` when mentioned. Map every selected library to one row in every sub-project's §14 Packages and its package ID to §16 Deployment Environment → `Shared libraries referenced`. If auth preflight fails, use the guide's manual fallback and propagate user-named libraries identically. This excludes Agents, Coded Apps, Flow, BPMN, Case, and API Workflows, but [Level 0 estate sweep](product-selection-guide.md#estate-sweep) (deployed processes, agents, Maestro processes, IXP projects, solutions, connections) applies to every scope. Discovery is best-effort and never blocks: in Autonomous mode, auth failure means skip without retry/troubleshooting and proceed with public NuGet only. Skip entirely if the user forbids `uip` commands.

### Step 3: Detect Gaps

Use the Gap Detection Checklist in the [PDD Analysis Guide](pdd-analysis-guide.md); classify every gap `[DEFAULT]` or `[SME REVIEW]`.

### Step 3.5: Synthesize the Need

Before selecting a product, distil the extracted model into a **need profile** — the recommendation reasons from this multi-factor picture, NOT from surface keywords. No single factor decides the tool; capture all and weigh the overall fit:

- **Core need & target outcome** — one sentence: what outcome the automation must produce, and which KPI it moves (cycle time, manual effort, quality/accuracy, cost, throughput, or compliance). Design the "to-be" against that outcome, not a copy of the as-is.
- **Decision nature (determinism)** — are decisions rule-expressible (**deterministic**: same input → same output) or do they need judgment / reasoning over ambiguity (**non-deterministic**)? Assess per process AND per step. Deterministic → RPA / API / rule-based; genuine judgment → Agents. (One factor among those below — not the sole gate.)
- **Input structure** — structured / predictable vs messy / unstructured (email, free text, varied documents → Agent or IXP to interpret).
- **Integration surface** — for each external system: does a stable API / **Integration Service connector** exist, and is it **reachable from the executor's runtime under the delivery model** (on-prem HTTP(S) APIs → Automation Relay option, placement rule 5)? Reuse an existing connector first. If none exists: API Workflows, RPA, and coded Agents call the API directly (Direct HTTP); IS-only surfaces (Maestro Flow / BPMN / Case connector nodes, low-code Agent tools) need a custom connector (→ `uipath-connector-builder`) or an API Workflow wrapper — see [Product Selection Guide → Integration Service](product-selection-guide.md#integration-service). Verify with `uip is connectors list` — never assume a connector exists. UI-only system → RPA.
- **Interaction model** — system-to-system (no UI, no human) · UI automation · human-in-the-loop (immediate attended action vs **asynchronous approval** — async inside one process → long-running RPA + Action Center) · user-facing app.
- **State** — atomic (one shot) · transactional (per-item, retryable) · long-running (suspends / waits). Long-running inside ONE process → RPA long-running workflow; long-running across products → Maestro.
- **Coordination shape** — single task · linear/branching pipeline · staged case lifecycle (stages + SLA) · structured control-flow (parallel / events / subprocess). Use the control-flow structure extracted in Step 2 ([PDD Analysis Guide → Detailed Process Map](pdd-analysis-guide.md#detailed-process-map)).
- **Volume, latency & cost** — high-volume / repeatable favours deterministic (agentic cost is higher-variance and less predictable — estimate per model/tenant, and justify agentic at volume); note any latency requirement.
- **Risk, reversibility & auditability** — high-risk / irreversible / low-confidence steps need a HITL gate; compliance-critical work needs a deterministic, auditable record.
- **Change / volatility** — how often inputs, forms, or rules change (an uncaptured volatility assumption is a top cause of solutions that break in production; prefer IXP for changeable documents).
- **Reuse** — local operation vs shared callable capability (→ RPA Library / API Workflow / custom connector, built before consumers).
- **Runtime & resource locality** — where must the work execute? Machine-local resources — desktop apps, Excel/Office files, file shares, on-prem databases, terminal/mainframe, Citrix — are reachable only from a robot inside the environment → RPA regardless of determinism or API existence (exceptions: on-prem HTTP(S) APIs via confirmed Automation Relay, and robot-hosted Coded Functions, which also run inside the environment — see the placement rules). Windows · cross-platform · serverless · user desktop drives compatibility, robot type, and licensing (§11 Project Mode Decision in the RPA template).
- **Existing estate** — what is already deployed: processes, API Workflows, connectors (`uip is connectors list`), tenant libraries (Step 2.5), IXP models, user-named resources. Reuse before build.
- **Trigger** — who or what starts it.
- **Confidence** — the evidence behind each factor and what remains unknown; unknowns become `[SME REVIEW]` rows, and a genuinely ambiguous product choice goes to the user (Step 6) — never a silent default.

**Close Step 3.5 by typing every extracted step** with the [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step) table — the resulting **step→executor map** is Level 1's input (layer 2 before layer 3; Level 1 never matches raw keywords against the whole process). Level 1 first folds absorbed capabilities into their hosts ([Decision table → Absorption fold](product-selection-guide.md#decision-table)) — capabilities a host invokes in-process are integrated components, not orchestration triggers — then reads the folded map.

Carry the need profile and the step→executor map into the Step 6 summary and the SDD `## Recommended Scope` reasoning so every product pick reads as `need → product`, auditable against the PDD. The dominant real-world pattern is **hybrid** (AI decides, deterministic RPA/API execute as governed tools, Maestro orchestrates when real orchestration is needed, HITL gates the risky steps) and **decomposed** into separate blocks — not one monolithic flow. Level 1 (Step 4) matches on the whole profile; PDD keywords are evidence, not the decision. When the need is genuinely ambiguous between products, ask the user (Step 6) — do not silently default.

### Step 4: Run Levels in Order

Mark `Read PDD and extract data` `completed` and `Select product` `in_progress` when applicable. Apply the delivery Constraint Gate and user exclusions before every level; see [Product Selection Guide → Constraint Gate](product-selection-guide.md#constraint-gate) and [platform-availability-guide.md](platform-availability-guide.md).

| Level | Decision | Reference | Run |
|---|---|---|---|
| 0 | suitability: automate / redesign first / reuse native or estate / do not automate | [Product Selection Guide → Level 0](product-selection-guide.md#level-0--suitability-gate) | always first; Levels 1+ only on `proceed` / `proceed-with-redesign` / `partial` |
| 1 | primary: Agents / Coded Apps / API Workflows / Case / Maestro BPMN / Maestro Flow / RPA / Solution | [Product Selection Guide → Level 1](product-selection-guide.md#level-1--primary-scope-selection) | always |
| 1.5 | RPA subtype: Process / Library / Test Automation | [RPA Product Guide → Level 1.5](rpa-product-guide.md#level-15--rpa-sub-type-selection) | when Level 1 = RPA; Solution RPA defers to Level 1.75 Pass C |
| 1.75 | solution composition | [Product Selection Guide → Level 1.75](product-selection-guide.md#level-175--solution-composition) | Level 1 = Solution or Step 6 chooses `Solution (customize)` |
| 2.5 Part A | RPA decomposition: Single vs Master Project | [RPA Product Guide → Level 2.5 Part A](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) | every RPA Process project |
| 2.5 Part B | merge unified project list | [Product Selection Guide → Level 2.5 Part B](product-selection-guide.md#part-b--merge-into-the-final-project-list) | always |

Level 2 authoring (XAML/Coded/Hybrid) is per RPA project in Phase 2 Step 2. Level 3 add-ons are detected during analysis and flagged in Phase 2 Step 4. Per-task placement runs at Step 3.5 and Phase 2 Steps 3–4; see [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step).

### Step 5: Check for Agent/Coded App Gaps

If primary is **Agents** or **Coded Apps** and required information is missing, use the Gap Handling flow in the [Product Selection Guide](product-selection-guide.md), with numbered choices. Ask whether to fill gaps or choose another product; batch at most 4 question objects per call, splitting more: Agents (framework, tools, memory, evaluation, bindings), Coded Apps (framework, app type, pages, state, caller). If changing product, ask fallback: RPA Process, Maestro Flow, Case Management, or Stop. Re-run Step 4 or end on Stop. Never auto-fallback.

### Step 6: Present Summary + Scope Recommendation

In Interactive mode, emit the [Product Selection Guide](product-selection-guide.md) “Presenting the Recommendation” summary with recommended scope first, then alternatives and `Solution (customize)`, and ask its confirmation question:

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
product-selection-guide.md → Presenting the Recommendation:
Recommended Scope + Project List + Queue Architecture>

### Clarifying Questions
<NUMBERED_QUESTIONS_IF_ANY>
```

Ask at most 5 clarifying questions in one round; unanswered items become `[SME REVIEW]`. `Solution (customize)` reruns Level 1.75, re-emits and re-asks, maximum 3 revisions, then uses latest composition. A single-product alternative reruns Step 4 with that forced primary, including Level 1.5 for RPA. Autonomous generates the summary internally but does not wait.

## Phase 2 — Architecture Review

Mark `Select product` `completed` and `Generate architecture (Phase 2)` `in_progress` when applicable.

### Step 1: Load the Template(s)

Use the [Template Mapping table in the Product Selection Guide](product-selection-guide.md#template-mapping): one matching template for single-product; solution overview plus one template per unified Level 2.5 project. RPA Master sub-projects share one RPA template file; unrelated RPA projects have separate files. Coverage follows in-scope types only; never privilege RPA, emit absent-type `N/A` filler, or assume agentic/RPA-only shape. The Solution component inventory lists every component/type: RPA / API Workflow / Agent / Maestro Flow · BPMN · Case / Coded or Low-code App / DU-IXP / connector / HITL. Replicate per-instance sections.

### Step 2: Generate the Architectural Core

Generate only applicable sections:

- **RPA (Process / Library / Test Automation):** §5 Data Definitions (C# records/dictionaries per §13); §9 Application Inventory (Integration Service connectors and email protocol); §10 Master Project Architecture (Level 2.5 Part A from [rpa-product-guide.md](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals), Single/Master, sub-projects, queue schema); §11 Project Structure (per sub-project, project type/framework/folders/workflow inventory; Lane A derives tasks); §12 Queue Architecture for any queue-defining/consuming project; §13 Implementation Mode (XAML/Coded/Hybrid via [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode)); §14 Packages from §9 and steps.
- **Maestro Flow:** §3 Nodes Inventory with node types; §4 Variables (direction/type); §5 Subflows; §7 Integrated Components (RPA, Agents, API Workflows, Connectors, HITL); §9 Project Structure.
- **Maestro BPMN:** §3 Pools & Lanes; §4 Activities Inventory with BPMN type; §5 Gateways & Sequence Flows (type, conditions, decision tables, reasoning list via [Business Rules Guide](business-rules-guide.md)); §6 Events (start/intermediate/boundary/end, message/timer/error); §7 Data Objects & Variables; §8 Subprocesses & Call Activities; §9 Integrated Components; §12 Project Structure.
- **Case Management:** §1 Case Definition (metadata, SLA, triggers, exit conditions, variables); §2 Stages & Tasks (complete stage/task summary/detail blocks); §3 Personas & App Views; §4 Integrations (connectors, API workflows, agents, processes/RPA, child cases, external agents, IXP, coded functions). Use long headings `## Section 1: Case Definition`, etc.; never legacy `§3 Stages` / `§4 Tasks Grid` / `§13 Task Type Registry`. Follow [case-design-layers-guide.md](case/case-design-layers-guide.md), [case-sdd-conformance-checklist.md](case/case-sdd-conformance-checklist.md), tenant grounding, and [case-design-lane-guide.md](case/case-design-lane-guide.md) for conversational non-PDD, delegated design, and draft finalization; those use the Case Design Lane, not this generic model.
- **Agents:** §2 Agent Framework (LangGraph / LlamaIndex / OpenAI Agents / Simple Function); §3 Tools; §4 Memory / RAG; §6 Orchestrator Bindings; §9 Project Structure (Coded/Low-code).
- **Coded Apps:** §2 App Type & Tech Stack; §3 Pages & Routes; §4 Components; §5 State Management; §6 API Integration; §10 Project Structure.
- **API Workflows:** §2 Input Schema; §3 Output Schema; §4 Execution Flow (high-level, no JavaScript); §5 Connectors & External Calls; §10 Project Structure.

### Step 3: Decompose Steps Into Implementation Units

| Product | Primary inventory | Unit |
|---|---|---|
| RPA Single | Workflow Inventory | `.xaml` or `.cs` files |
| RPA Master | Workflow Inventory per sub-project | grouped `.xaml` or `.cs` files |
| Flow | Nodes Inventory | Flow nodes |
| BPMN | Activities Inventory | service/script/user/call-activity/subprocess BPMN units |
| Case | §2 Stages & Tasks | stage plus task summary/detail blocks |
| Agents | Tools | Python functions, RPA/API bindings |
| Coded Apps | Pages + Components | routes and React/Angular/Vue components |
| API Workflows | Execution Flow | HTTP/Connector/Script activities |

Every unit needs concrete responsibility, PDD step references, inputs/outputs, verb typing and placement using [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step): deterministic validate/transfer → RPA/API; document collect → IXP; judgment → Agent; atomic transform/compute → Function; review/sign-off → HITL; aggregate → Data Fabric. Record placement and integrated non-primary components. For Master Projects: (1) assign steps to sub-projects from §10, (2) decompose within each, (3) for REFramework, Init/GetTransactionData/Process/SetTransactionStatus come from the framework; inventory only Process-specific workflows.

### Step 4: Flag Integrated Components

For each Phase 1 component and non-primary placement:

- **HITL:** Flow touchpoints → `uipath-human-in-the-loop`; Coded Agents escalation belongs to `uipath-agents` (HITL skill defers wiring); BPMN `userTask` → §9 HITL Touchpoints, authored inline by `uipath-maestro-bpmn`; Case → `action` task detail with Action App intent, never HITL skill; RPA → Action Center/long-running workflow.
- **Integration Service connectors:** list in RPA Application Inventory or other Connectors section; run `uip is connectors list`; route existing configuration to `uipath-platform`, absent custom connector to `uipath-connector-builder`.
- **IXP/Document Understanding:** list in host “IXP / Document Understanding Models” table for Flow/BPMN/Case/Agent/RPA; API Workflow/Coded App → own row in §Solution / Project Breakdown; route to `uipath-ixp` before consumers.
- **Coded Functions** (TypeScript / JavaScript / Python; parsing, scoring, custom-auth API calls, IS-connection queries): use only when justified by [placement rule 6](product-selection-guide.md#per-task-component-placement-the-to-be-per-step); host-native logic remains in host inventory. List in host “Coded Functions” table for Flow/BPMN/Case/Agent; route to `uipath-functions` before consumers; no per-project SDD file (see [Template Mapping](product-selection-guide.md#template-mapping)).
- RPA called by Flow/BPMN/Agent/Case → Integrated Components; implementation creates RPA project.
- API Workflow called by Flow/BPMN/Agent/Case only when host cannot call natively, has 2+ consumers, or needs independent lifecycle; otherwise record host direct call as `Access Method = Direct HTTP`. Extracted API Workflow goes in Integrated Components and implementation creates it. Extraction never changes `SDD scope` ([derived-component rule](product-selection-guide.md#solution-signals)).

### Step 5: Present Architecture for Review

In Interactive mode, present the architectural core and wait. Any response without specific change requests—including “looks good”, “ok”, “proceed”, “yes”, or a topic change—is approval. Incorporate specific changes and re-present, maximum 3 revisions; then proceed with latest and mark disagreements `[SME REVIEW]`. Autonomous generates without waiting.

## Phase 3 — Full SDD Generation

Mark `Generate architecture (Phase 2)` `completed` and `Write SDD skeleton to disk` `in_progress` when applicable.

### Step 0: Write the SDD Skeleton to Disk — Hard Gate

**Write now, before any Phase 3 section.** Step 1 cannot begin until `Write` creates the file. Before writing, run collision handling: if target exists, ask via `AskUserQuestion` whether to keep, regenerate, resume, or write `-v2-`; honor the answer. Keep/stop makes no write; resume patches the draft; only regenerate/no-file writes a fresh skeleton.

Write in order: (1) title/header and `## Document History`; (2) `<!-- planner-handoff:v1 -->`, exact `## Planner Handoff`, `Status: draft`, `Template validation: pending`; (3) autonomous `## Decisions Made` and both-mode `## Recommended Scope`; (4) all existing Phase 1/2 sections. Append remaining sections with `Edit`/`Write`; do not buffer or rewrite the whole file. A partial draft must remain gradeable; `Status: ready` is the last Phase D write. Step 1.5 and the superset check run against the on-disk file.

> Progress: mark `Write SDD skeleton to disk` completed and `Generate full SDD (Phase 3)` in_progress.

### Step 1: Generate Remaining Sections

Phase 1 produces Header & Document History (process name, today's date, version 1.0; Case title `# SDD — {Case Name}`), overview (§1), process/flow/lifecycle diagram (§2 for most), and applicable detailed steps/nodes. Phase 2 produces its template-specific core. Phase 3 produces remaining applicable sections: Business Rules (RPA §4 via [Business Rules Guide](business-rules-guide.md)), Value Mappings (RPA), Exception/Error Handling (all), Credentials & Assets (RPA), Deployment Environment (RPA — fill the Orchestrator row from the Step 0 delivery model (Cloud / Automation Suite + version / standalone); fill `[SME REVIEW]` for the rest when the PDD does not specify; never invent VM names, version pins, or robot types), Flow Triggers, Case SLA Rules & Escalations, Compliance Constraints, Roles & RACI, Agent Evaluation Criteria.

**Non-Functional Requirements — always:** security (Orchestrator secrets/assets, least-privilege IS scope, no entity calls exposed in network trace), performance (DB vs file, webhooks vs polling, avoid license-consuming Windows processes), scalability, availability, logging/monitoring. API Workflow already has §Performance & Scaling + §Security & Authentication; others capture equivalent subsection.

**Reusable Components / Libraries — always:** existing tenant Libraries from Step 2.5, Marketplace/org components, connectors, and new reusable assets (shared workflows → RPA **Library** via `uipath-rpa`; missing integration → custom connector via `uipath-connector-builder`), built before consumers; assets used by 2+ projects live at parent/solution level. See [Product Selection Guide → Reusability & shared assets](product-selection-guide.md#reusability--shared-assets).

**Testing Strategy — always thorough:** happy path, edge cases, errors, and Master end-to-end pipeline tests; do not ask about depth, though specialists may reduce scope for a quick MVP.

**Next Steps:** points to Lane A and replaces Implementation Plan; Phase D does not generate task lists.

<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section, a task list, or `TaskCreate` calls for implementation work. Those are owned by Lane A (task derivation). The SDD's `## Next Steps` section marks the boundary into Lane A, and that is the entire Phase D output surface.
<!--skill-flavor:phase3-output-surface:end-->

### Step 1.5: Resolve SME Review Items

Mark `Generate full SDD (Phase 3)` completed and `Resolve SME review items` in_progress when applicable. Run in both modes; this blocks a complete SDD. If no `[SME REVIEW]`, skip.

Batch with numbered choices under the 4-option cap: 1–4 items → one question; 5–8 → one call with two questions (each ≤4 options), grouped by section; over 8 → calls of up to 8 items (two questions), waiting between batches. Do not flatten >4 items into one question — the call will fail validation. Example for 1-4 items:

> Before I finalize the SDD, these items need your input:
>
> 1. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
> 2. **<ITEM_NAME>** (<SDD_SECTION>) — <QUESTION>. Default: `<DEFAULT_VALUE>`
>
> You can answer each, accept all defaults by replying "use defaults", or skip specific items.

Ask, update sections, and allow one more round (maximum 2 total). After 2 rounds retain unresolved items as `[SME REVIEW]`, apply recorded defaults, and proceed. Explicit skips remain marked with defaults. Classify every survivor in the Action Required table as `default-carried` or `blocking`. Blocking only means: (a) unknown delivery model for a matrix-gated selected product; (b) unknown access method for an in-scope §9 application; (c) contradictory PDD scope Level 0/1 cannot resolve; (d) user rejected Level 1 without choosing an alternative. Blocking keeps `Status: draft`.

### Step 2: Finalize the SDD File(s)

Mark `Resolve SME review items` completed and `Finalize SDD (Status: ready)` in_progress when applicable.

1. Assemble in template order by appending/patching the skeleton.
2. Every template has this exact handoff contract after `## Document History`; preserve both marker and heading:

```markdown
<!-- DO NOT RENAME: uipath-planner detects SDDs via this exact heading or the marker below. -->
<!-- planner-handoff:v1 -->
## Planner Handoff

| Field | Value |
|---|---|
| **Status** | draft → ready |
| **Execution autonomy** | <autonomous | interactive> |
| **Delivery model** | <cloud | automation-suite | standalone | unspecified> |
| **SDD scope** | <single-product | solution> |
| **Solution root SDD** | <SOLUTION_NAME_KEBAB>-solution-sdd.md |
| **Solution ID** | <SOLUTION_NAME_KEBAB> |
| **Project SDD role** | root | child |
| **Independently executable** | no |
| **Project list section** | §11 / §10 + §11 / Project Inventory |
| **Tasks file** | `<PROCESS_NAME_KEBAB>-tasks.md` |
| **Build handoff** | <prose — Case template ONLY> |
| **Generated by** | uipath-planner |
| **Generation date** | <YYYY-MM-DD> |
| **Template validation** | pending → passed |
```

First write `draft`; flip to `ready` only after Step 1.5 classifies all survivors `default-carried` and item 8 passes. Delivery value includes Suite version when known, e.g. `automation-suite 2025.1`. Solution rows appear in every SDD: root is `root`, children `child`, children `Independently executable: no`, all share canonical `<SOLUTION_NAME_KEBAB>-tasks.md`. Single-product omits solution rows. `Project list section` is template-specific: RPA single §11; RPA Master §10 + §11; Flow §3 + §7; BPMN §4 + §9; Case §2 + §4; etc. Case emits `Build handoff` instead of `Tasks file`; never both. Keep heading and marker redundant for detection.
`Delivery model` ← from Phase 1 Step 0: write exactly one enum token `cloud | automation-suite | standalone | unspecified` (append the Suite version when known, e.g. `automation-suite 2025.1`); Decisions Made row 1 `Picked` starts with the same token.
3. If autonomous, immediately after Planner Handoff and before Action Required/product body/ToC, emit:

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

Each Picked value is concrete; each reason is ≤20 words and cites PDD/process evidence. Row 1 always appears, including `cloud; no products blocked`. For solutions repeat rows 3–5 per RPA project; for non-RPA scopes collapse rows 3–5 to N/A plus the product-specific equivalent. This index does not replace detail. In both modes immediately emit `## Recommended Scope` (after Decisions Made, or after Planner Handoff in Interactive), copying Phase 1 summary `Recommendation:`, `Delivery model:`, and `Blocked by platform:` lines from [product-selection-guide.md → Summary block](product-selection-guide.md#summary-block).
4. If reviews remain, after those blocks and before product body emit:

```markdown
## Action Required — SME Review Items

| # | Section | Item | Question | Default applied | Blocking |
|---|---|---|---|---|---|
| 1 | <SECTION> | <ITEM> | <QUESTION> | <DEFAULT> | <yes/no> |

> These items are marked `[SME REVIEW]` in the document. Default-carried items (Blocking = no) do not block task derivation — the automation is built on the recorded defaults, which must be verified before production sign-off. Any Blocking = yes item keeps the handoff at `Status: draft`.
```
5. Target 300–800 markdown lines for single-project SDDs; Master may be 600–1200. Over 20 steps, group/summarize at parent; over 10 business rules, prioritize 10 most impactful.
6. Collision handling occurs before Step 0, not here; by this point the answer is already applied, so do not re-ask. If `<PROCESS_NAME_KEBAB>-sdd.md` exists, read handoff Status. For `ready` or no Status, ask:

> An SDD already exists at `<sdd-path>`. How should I proceed?
>
> 1. **Keep the existing SDD and stop** *(recommended)* — proceed to Lane A if you want to refresh the task list
> 2. **Regenerate from the PDD** — overwrites the existing SDD

For `draft`, ask:

> An unfinished SDD draft exists at `<sdd-path>` (interrupted generation). How should I proceed?
>
> 1. **Resume generation** *(recommended)* — finish the remaining sections, resolve SME items, run the completeness check, then flip Status to ready
> 2. **Regenerate from the PDD** — discard the draft and start over
> 3. **Generate alongside as `<name>-v2-sdd.md`** — for diffing

Default is keep.
7. Write to current working directory unless user specifies output path. Single product: `<PROCESS_NAME_KEBAB>-sdd.md`. Solution: `<SOLUTION_NAME_KEBAB>-solution-sdd.md` plus `<PROJECT_NAME_KEBAB>-sdd.md` per unified project. Put review warnings in root and affected child; each child has its own Planner Handoff.
8. **Template-superset check (mandatory before the item 9 summary).** After each file, re-read it and compare every H2/H3 with the template TOC; generated headings MUST be a superset — missing template sections are an SDD defect. Optional template-comment H3s may be omitted only when their condition applies. Minimum RPA H2s: §1 Process Overview, §2 Process Map, §3 Detailed Process Steps, §4 Business Rules, §5 Data Definitions, §6 Value Mappings, §7 Exception Handling, §8 Error Handling, §9 Application Inventory, §10 Master Project Architecture, §11 Project Structure, §12 Queue Architecture (omit only if no queue is defined/consumed), §13 Implementation Mode, §14 Packages, §15 Credentials & Assets, §16 Deployment Environment, §17 Testing Strategy, §18 Next Steps. Minimum Case H2s: §1 Case Definition, §2 Stages & Tasks, §3 Personas & App Views, §4 Integrations, `## Document History`, `## Planner Handoff`, `## Table of Contents`, `## Non-Functional Requirements`, `## Testing Strategy`, `## Next Steps`; verify each stage has `### Stage ...` or `### Secondary Stage ...`, each task has `##### Task ...`, and each detail contains exact `**Task envelope**` before its Required / Run Only Once / Skip Condition table. Other templates must contain every H2 in their TOC.

For missing required H2s, regenerate from template + Phase 1/2 data; if genuinely absent, emit an explicit `No business rules extracted from the PDD`-style note plus `[SME REVIEW]` row; never silently drop. Zero §4 Business Rules is a regeneration trigger because rules may be embedded in remarks, steps, or screenshots. When headings pass and no survivor is blocking, make the final write: `Status: ready`, `Template validation: passed`. Default-carried items do not block; blocking keeps `draft` and appears in the summary. Lane A derives only from `ready`.
9. Emit:

```markdown
## SDD Generated

<FILENAME_1> — <COUNT> sections, <LINE_COUNT> lines
<FILENAME_2> — <COUNT> sections, <LINE_COUNT> lines
...

<SME_REVIEW_COUNT> open SME review items (if any — list each with its class and default).

**Next — branch on the handoff `Status`:**
- `ready` — Phase D is complete and the SDD is on disk. Lane A (task derivation) continues on the next turn with this SDD path; open default-carried SME items travel with the derived tasks as assumptions — confirm them before production.
- `draft` (blocking SME items) — Blocked on: <BLOCKING_ITEMS>. Answer these and the SDD finalizes to `ready`; Lane A refuses drafts.
```

### Step 2.5: Word (.docx) Delivery — only when requested

Convert the written SDD; do not author Word by hand or use COM.

```bash
# macOS / Linux / Git Bash:
bash <SKILL_DIR>/scripts/sdd-to-docx.sh "<SDD_PATH>.md" [--reference-doc "<TEMPLATE>.docx"]
# Windows without Git Bash (Windows PowerShell 5.1 or pwsh 7+):
pwsh -File <SKILL_DIR>/scripts/sdd-to-docx.ps1 "<SDD_PATH>.md" [--reference-doc "<TEMPLATE>.docx"]   # or: powershell -File ...
```

`--reference-doc` applies fonts, heading styles, and margins; markdown structure remains. For an official client SDD/ASDD, ask for template path and follow [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md); do not invent structure. Keep readable Mermaid diagrams as code blocks; image rendering/styling is out of scope. Relay pandoc's install command if missing. Skip unless Word is requested.

### Step 3: Proceed to Lane A (Task Derivation)

Mark `Finalize SDD (Status: ready)` completed; all progress tasks are done.

<!--skill-flavor:phase-d-deliverable:start-->
The SDD is the deliverable of Phase D. **Do not generate an Implementation Plan section inside the SDD. Do not create implementation `TaskCreate` calls during Phase D. Do not start executing.**
<!--skill-flavor:phase-d-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin Lane A in the same turn as Phase D.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue into Lane A on the **next** turn. Rationale: Phase D (read PDD + guides, author §1–§18) and Lane A (parse SDD, derive tasks, emit `TaskCreate`) are each heavy; stacking both in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after a durable SDD write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->

On the next turn, if intent implies implementation (`create / build / implement / set up / make`), continue Lane A with `<sdd-path>`; it reads Planner Handoff, derives tasks, writes `<process-kebab>-tasks.md` beside the SDD, and emits specialist-routed live tasks; see [pdd-driven-lane-guide.md](pdd-driven-lane-guide.md). If intent is only design/architect/generate SDD, stop after the SDD.