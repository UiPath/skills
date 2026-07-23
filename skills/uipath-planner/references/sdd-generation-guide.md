# SDD Generation Guide

Step-by-step instructions for transforming a PDD into an SDD. Follow the 3-phase interaction model described in SKILL.md.

## Phase 1 — PDD Analysis & Scope Selection

### Step 0: Determine Execution Mode & Delivery Model

Before reading the PDD, ask **one `AskUserQuestion` call containing two question objects** — execution mode and delivery model (three objects when the custom-host follow-up below applies; the tool accepts up to four per call). Batching keeps the prompt budget flat: the delivery model gates every product decision (see [Product Selection Guide → Constraint Gate](product-selection-guide.md#constraint-gate)) and asking it later costs a second interruption.

**Delivery-model CLI preflight — run first, best-effort.** Before composing the questions, try to resolve the delivery model from the active CLI session:

```bash
uip login status --output json
```

`uip login status` returns the authenticated `Data.BaseUrl` (host) and tenant. That separates **Automation Cloud** from **self-hosted**, but it does NOT reveal whether a self-hosted host is Automation Suite or standalone Orchestrator, nor the Automation Suite version/capabilities — validate those explicitly.

| `Data.BaseUrl` host | Resolves to | Question 2 |
|---|---|---|
| `cloud.uipath.com` (or `alpha.uipath.com` / `staging.uipath.com`) | **Automation Cloud** — full catalog, entitlement-gated per tenant | skip (confidently resolved) |
| any other `*.uipath.com` host | **Automation Cloud variant** (Public Sector / Dedicated / Test Cloud / region-specific) — catalog is variant-, region-, and entitlement-gated | skip the platform question, but verify each gated product (Maestro, Agents, Coded Apps, API Workflows, Solutions) against the tenant's actual entitlements; unverifiable → `[SME REVIEW]` per product |
| any other (customer / on-prem) host | **self-hosted — Automation Suite OR standalone Orchestrator (ambiguous)** | **do not skip** — ask the custom-host follow-up below |
| `Status` ≠ `Logged in`, call errors, or no `BaseUrl` | unknown | ask Question 2 in full; tell the user that running `uip login` first lets the next run auto-detect |

**Custom-host follow-up** — when the preflight hits the ambiguous row, replace Question 2 with these **two question objects** in the same batched Step 0 `AskUserQuestion` call (the call then carries three questions). Show the detected host:

*Question 2a — Platform:*

> I detected a self-hosted URL (`<HOST>`). Which platform is it?
>
> 1. **Automation Suite** — product + capability availability is gated by version (and the EKS/AKS install profile for the Maestro/Agents stack)
> 2. **Standalone Orchestrator (MSI)** — Orchestrator + Studio/Robot only; most modern products unavailable

*Question 2b — Automation Suite version (applies only when 2a = Automation Suite):*

> Which Automation Suite version?
>
> 1. **2.2510 or later**
> 2. **2024.10**
> 3. **Older**
> 4. **Not sure / not Automation Suite**

Record the delivery model, and for Automation Suite the **version** — it determines which capabilities/products are available (gate via [platform-availability-guide.md](platform-availability-guide.md)). Never silently treat a custom host as Automation Suite; standalone blocks far more. If the user picks Automation Suite but cannot give the version ("Not sure"), gate against the latest matrix column and add an `[SME REVIEW]` version row in §16 Deployment Environment.

Precedence: an explicit user-stated delivery model or a PDD signal **wins over** the preflight — never override an explicit statement with the detected value. The preflight is **best-effort and never blocks** (Rule G-8): on any CLI failure, fall back to asking Question 2.

*Question 1 — Execution mode:*

> How should I handle this SDD generation?
>
> 1. **Autonomous** *(recommended)* — I will read the PDD, make all decisions, and generate the full SDD. I will only interrupt for hard blockers (PDD unreadable, Agent/Coded App missing critical info, unresolved `[SME REVIEW]` items before finalizing).
> 2. **Interactive** — I will pause at each phase checkpoint (summary, architecture, final SDD) for your review before proceeding.

*Question 2 — Delivery model:*

> Where will this automation run?
>
> 1. **UiPath Automation Cloud** — full product catalog available
> 2. **Automation Suite (self-hosted)** — product availability depends on the Suite version; I will gate recommendations accordingly
> 3. **Standalone Orchestrator (MSI)** — most restrictive; modern platform products unavailable
> 4. **Not sure** — I will proceed assuming Automation Cloud and flag the assumption as `[SME REVIEW]`

**Skip Question 2** only when the delivery model is **fully** resolved — the user's request states it, the PDD carries a delivery-model signal (see [PDD Analysis Guide → Environment & Constraint Signals](pdd-analysis-guide.md#environment--constraint-signals)), or the preflight landed on a **known cloud host**. A custom / self-hosted host does NOT fully resolve it (Automation Suite vs standalone is ambiguous, and the AS version is unknown) — ask the custom-host follow-up above, batched into the Step 0 call. Record the resolved value. Only if the user picks Automation Suite and cannot give the version do you skip the version follow-up — then gate against the latest matrix column and add an `[SME REVIEW]` version row in §16 Deployment Environment.

**Skip Question 1 symmetrically** when the request already states the execution mode ("autonomous", "don't pause for checkpoints", "interactive review"). When both questions are resolved from context, skip the `AskUserQuestion` call entirely and record both values.

Record both choices — they go into the SDD's `## Planner Handoff` header (Phase 3 Step 2) and propagate to Lane A (task derivation): execution mode drives task review behavior; delivery model is passed to specialists as a platform constraint.

In **Autonomous** mode:
- Skip Phase 1 summary presentation (generate internally, do not wait for confirmation) — the `## Recommended Scope` block still persists into the SDD (Phase 3 Step 2 item 3)
- Skip Phase 2 architecture review (generate, do not wait)
- Still ask the SME Review resolution question before writing (Step 1.5) — this is a hard blocker
- Still ask the Agent/Coded App gap-filling question if triggered — this is a hard blocker
- **Insert a "Decisions Made" block** at the top of the SDD (immediately after the Planner Handoff header and before any other section) listing the five highest-leverage architectural picks with one-sentence reasons. See Phase 3 Step 2 item 3 for the exact block format. Do **NOT** use `AskUserQuestion` — the picks are decided autonomously; the block makes them scannable in the SDD's first screenful so a reviewer can spot a wrong call without reading the whole document.

In **Interactive** mode:
- Present and wait at every checkpoint as described in the steps below

### Step 0.5: Create Progress Tasks

Create progress-tracking tasks via `TaskCreate` so the user can see where the SDD generation stands.

```
TaskCreate: subject="Read PDD and extract data",        activeForm="Reading PDD…"
TaskCreate: subject="Select product",                    activeForm="Selecting product…"
TaskCreate: subject="Generate architecture (Phase 2)",   activeForm="Generating architecture…"
TaskCreate: subject="Generate full SDD (Phase 3)",       activeForm="Generating SDD sections…"
TaskCreate: subject="Resolve SME review items",          activeForm="Resolving SME review items…"
TaskCreate: subject="Write SDD to disk",                 activeForm="Writing SDD…"
```

Mark each task `in_progress` when starting and `completed` when done.

**Rule G-8 — Task creation is best-effort and never blocks SDD output.** If any `TaskCreate` or `TaskUpdate` call fails (tool unavailable, runtime error, timeout), log a single warning to the user, continue the SDD generation without progress tasks, and do not retry. The SDD file itself is the authoritative deliverable. Progress tasks are a UX convenience only.

> If Step 0.5 `TaskCreate` failed, silently skip every subsequent `Mark "X" as in_progress / as completed` instruction in this guide — the tasks do not exist to update, and a second warning to the user is noise.

These tasks track SDD generation. Implementation tasks are owned by Lane A (task derivation), which runs after Phase D writes the SDD — do NOT create implementation tasks here.

### Step 1: Read the PDD

> **Progress:** Mark "Read PDD and extract data" as `in_progress`.

1. Determine the input format and route it to the right tool — Markdown (`.md`) and plain text (`.txt`): `Read` directly; PDF (`.pdf`): `Read` with `pages`; Word (`.docx`): convert with `scripts/docx-extract.sh` (pandoc); pasted text: from conversation context. See [PDD Analysis Guide → Supported Input Formats](pdd-analysis-guide.md#supported-input-formats). The source need not be a formal PDD — a Confluence page, BPMN model (`.bpmn`), meeting/Zoom transcript, SOP, or requirements doc also works ([Accepted process-knowledge sources](pdd-analysis-guide.md#accepted-process-knowledge-sources)); run heavier Phase 1 elicitation when the source is less structured than a PDD. Extract **both AS-IS and TO-BE** ([As-Is and To-Be Process](pdd-analysis-guide.md#as-is-and-to-be-process)).
2. **Size-based reading strategy** for PDFs:
   - **Under 10 pages:** read the entire document in one pass. Skip ToC lookup.
   - **10-50 pages:** read the ToC first, then read sections in priority order (overview → steps → exceptions → applications → credentials).
   - **Over 50 pages:** read ToC, then read high-priority sections (overview, process steps, exceptions) first, extract as you go, then read remaining sections.
3. For pasted text over 3000 words, ask the user to paste in sections.
4. **Docx handling:** .docx is a binary format — do NOT Read it directly or attempt to extract data from garbled output. Convert first. Run from the directory where the markdown should land (output defaults to the current working directory):

   ```bash
   # macOS / Linux / Git Bash:
   bash <SKILL_DIR>/scripts/docx-extract.sh "<PDD_FILE_PATH>"
   # Windows without Git Bash (Windows PowerShell 5.1 or pwsh 7+):
   pwsh -File <SKILL_DIR>/scripts/docx-extract.ps1 "<PDD_FILE_PATH>"   # or: powershell -File ...
   ```

   `<SKILL_DIR>` is the folder containing this skill's SKILL.md; `<PDD_FILE_PATH>` is the full path to the .docx. The script produces a UTF-8 markdown file plus a `-media/` folder with embedded screenshots — Read both (screenshots feed the canonical-example extraction). Complex multi-paragraph tables may come out as raw HTML `<table>` blocks — parse them, they carry the same data. If the script reports pandoc missing, relay its install command to the user; only if the user cannot install pandoc, fall back to: "Please export the Word document as PDF or paste the content directly." Never drive Word via COM automation.
5. **Error cases:** if the document cannot be read (corrupt PDF, password-protected, unsupported format), tell the user and ask them to provide it in a different format. If the document does not appear to be a PDD (no process steps, no application details, no exception handling), tell the user and stop.
6. **Language handling:** if the PDD is not in English, use `AskUserQuestion` with the numbered-choice format:

   > The PDD appears to be in <LANGUAGE>. Which language should the SDD use?
   >
   > 1. **English** *(recommended)* — SDD in English for broadest tool compatibility
   > 2. **<LANGUAGE>** — SDD in the same language as the PDD

   Regardless of choice, keep section headings and structural identifiers (BR-01, B1, E1) in English for tool compatibility.

### Step 2: Extract Structured Information

Follow the [PDD Analysis Guide](pdd-analysis-guide.md) to extract data from the PDD. Build an internal model with these components:

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

Skip this step for non-RPA primaries (Agents, Coded Apps, Flow, BPMN, Case, API Workflows) — shared RPA libraries do not apply to those products' package models. Only the *library* discovery is RPA-scoped: the [Level 0 estate sweep](product-selection-guide.md#estate-sweep) (deployed processes, agents, Maestro processes, IXP projects, solutions, connections) runs for every scope when evaluating the suitability gate.

Run the procedure in [tenant-library-search-guide.md](tenant-library-search-guide.md). Keyword source for step 2: PDD Application Inventory + org-prefix terms (`Common`, `Shared`, `<Company>` if mentioned in the PDD). Output mapping: every selected library → one row in every sub-project's §14 Packages table, and its package ID into §16 Deployment Environment → "Shared libraries referenced". If the auth preflight fails, use the guide's manual fallback and propagate the user's named libraries to §14 / §16 the same way.

**This step is best-effort — it never blocks SDD output.** If the auth preflight errors or auth is unavailable, **Autonomous mode skips library discovery and proceeds with public NuGet only** — do not retry or troubleshoot auth mid-generation, and do not pause. Skip the step entirely if the user's prompt forbids running `uip` commands.

### Step 3: Detect Gaps

Scan for missing or vague information. Use the Gap Detection Checklist in the [PDD Analysis Guide](pdd-analysis-guide.md) to classify each gap as `[DEFAULT]` or `[SME REVIEW]`.

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

> **Progress:** Mark "Read PDD and extract data" as `completed`. Mark "Select product" as `in_progress`.

This step orchestrates four levels of decision. Each level lives in its own canonical reference; this guide does not restate them. Run in order — output of each level feeds the next.

> **Constraint Gate applies at every level.** The delivery model from Step 0 and any user-stated product exclusions filter the candidates before each level recommends — see [Product Selection Guide → Constraint Gate](product-selection-guide.md#constraint-gate) and [platform-availability-guide.md](platform-availability-guide.md).

| Level | Decision | Canonical reference | When |
|---|---|---|---|
| **Level 0** | Suitability — automate / redesign first / reuse native or estate / do not automate | [Product Selection Guide → Level 0](product-selection-guide.md#level-0--suitability-gate) | Always, first — Levels 1+ run only on `proceed` / `proceed-with-redesign` / `partial` |
| **Level 1** | Primary scope (Agents / Coded Apps / API Workflows / Case / Maestro BPMN / Maestro Flow / RPA / Solution) | [Product Selection Guide → Level 1](product-selection-guide.md#level-1--primary-scope-selection) | Always |
| **Level 1.5** | RPA sub-type (Process / Library / Test Automation) | [RPA Product Guide → Level 1.5](rpa-product-guide.md#level-15--rpa-sub-type-selection) | Run when Level 1 = RPA. For Solution composition with RPA projects, defer to Pass C of Level 1.75. |
| **Level 1.75** | Solution composition (which products and how many) | [Product Selection Guide → Level 1.75](product-selection-guide.md#level-175--solution-composition) | Run when Level 1 = Solution OR user picks "Solution (customize)" in Step 6 |
| **Level 2.5 Part A** | RPA decomposition (Single vs Master Project) | [RPA Product Guide → Level 2.5 Part A](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) | Run for every RPA Process project in the scope |
| **Level 2.5 Part B** | Merge into unified project list | [Product Selection Guide → Level 2.5 Part B](product-selection-guide.md#part-b--merge-into-the-final-project-list) | Always — produces the canonical project list |

This step's output goes into the Phase 1 summary at Step 6 and drives the Phase 2 architectural core.

> Level 2 (Authoring mode — XAML / Coded / Hybrid) is decided per RPA project at Phase 2 Step 2 from [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Level 3 (Capability add-ons — HITL, Integration Service, etc.) is detected during PDD analysis and flagged in template sections during Phase 2 Step 4. Per-task component placement (which step lands on RPA / API / IXP / Agent / Function / HITL / Maestro / Data Fabric) runs twice: at Step 3.5 (the step→executor map that feeds Level 1) and at Phase 2 Steps 3–4 (recording placements in template inventories) — [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step).

### Step 5: Check for Agent/Coded App Gaps

If the primary product is **Agents** or **Coded Apps** AND required product-specific information is missing from the PDD, follow the Gap Handling flow in the [Product Selection Guide](product-selection-guide.md). All questions use the numbered-choice format.

Summary:
1. Ask the user: proceed with gap-filling or use a different product?
2. If proceed → batch the gap-filling questions, at most 4 question objects per `AskUserQuestion` call — split into two calls when more remain (Agents: framework, tools, memory, evaluation, bindings. Coded Apps: framework, app type, pages, state, caller)
3. If different product → ask which fallback (RPA Process, Maestro Flow, Case Management, Stop)
4. Re-run Step 4 with fallback, or end if "Stop"

Never auto-fallback. The user must choose explicitly.

### Step 6: Present Summary + Scope Recommendation

Emit the summary block described in "Presenting the Recommendation" in the [Product Selection Guide](product-selection-guide.md). The **recommended scope appears first**; single-product alternatives and "Solution (customize)" follow as alternatives in the confirmation `AskUserQuestion` call.

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

Then call `AskUserQuestion` with the confirmation question from the Product Selection Guide's "Presenting the Recommendation" section (recommendation as option 1, single-product alternatives, then "Solution (customize)").

**If the user picks "Solution (customize)":** re-run Level 1.75 per the customize branch in the guide, then re-emit this summary with the customized project list, then re-ask the confirmation question. Max 3 revisions — after that, proceed with the latest composition.

**If the user picks a single-product alternative:** re-run Step 4 with the user's choice as the forced primary (including Level 1.5 if it's RPA).

Ask at most 5 clarifying questions total, in a single round. If the user cannot answer some, tag those items as `[SME REVIEW]` and proceed.

## Phase 2 — Architecture Review

> **Progress:** Mark "Select product" as `completed`. Mark "Generate architecture (Phase 2)" as `in_progress`.

### Step 1: Load the Template(s)

Load from the [Template Mapping table in the Product Selection Guide](product-selection-guide.md#template-mapping):

- **Single-product scope:** load the one template matching the Level 1 primary.
- **Solution scope:** load the solution overview structure PLUS one template per project in the Level 2.5 unified project list. RPA Master Projects share one RPA template file across their sub-projects; unrelated RPA projects each get their own file.

**The SDD is automation-type-agnostic — no type is privileged.** Section coverage follows the in-scope types: a single-product SDD uses that product's template; a Solution's per-project SDDs each use their product's template, tied together by the Solution overview's **component inventory** (every component listed with its type — RPA / API Workflow / Agent / Maestro Flow · BPMN · Case / Coded or Low-code App / DU-IXP / connector / HITL). Include per-type detail (Agent Configuration, Queue Architecture, API schemas, Gateways, Case stages, etc.) **only for the types actually in scope** — never emit "N/A" filler sections for absent types, and never assume an agentic (or RPA-only) shape. Delete rows that do not apply; replicate per-instance sections (e.g., one Agent Configuration per agent).

### Step 2: Generate the Architectural Core

The architectural core sections differ per template. For each product, generate these sections in Phase 2:

**RPA (Process / Library / Test Automation):**
- §5 Data Definitions (C# records or dictionary tables per §13 Implementation Mode)
- §9 Application Inventory (flag Integration Service connectors, specify email protocol)
- §10 Master Project Architecture (apply Level 2.5 Part A from [rpa-product-guide.md](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) — Single vs Master Project, sub-projects, queue schema)
- §11 Project Structure (per sub-project if Master Project: project type, framework, folder layout, workflow inventory) — the most load-bearing SDD section: Lane A derives tasks from it
- §12 Queue Architecture (any project defining or consuming queues — definitions, configuration, item schemas, processing rules)
- §13 Implementation Mode (XAML / Coded / Hybrid — apply Level 2 from [rpa-product-guide.md](rpa-product-guide.md#level-2--authoring-mode))
- §14 Packages (infer NuGet packages from §9 Application Inventory and process steps)

**Maestro Flow:**
- §3 Nodes Inventory (with node type per node)
- §4 Variables (direction, type)
- §5 Subflows (if any)
- §7 Integrated Components (RPA, Agents, API Workflows, Connectors, HITL touchpoints)
- §9 Project Structure

**Maestro BPMN:**
- §3 Pools & Lanes (participants / roles)
- §4 Activities Inventory (BPMN element type per activity)
- §5 Gateways & Sequence Flows (gateway type, branch conditions)
- §6 Events (start / intermediate / boundary / end; message / timer / error definitions)
- §7 Data Objects & Variables (direction, type, scope)
- §8 Subprocesses & Call Activities
- §9 Integrated Components (RPA, Agents, API Workflows, Connectors, HITL touchpoints)
- §12 Project Structure

**Case Management:**
- §3 Stages
- §4 Tasks Grid (per stage, lanes × index)
- §7 Data Definitions (case data objects, supporting objects, data flow)
- §13 Task Type Registry (RPA / AGENT / API_WORKFLOW / CONNECTOR / HITL)
- §14 Integrated Components
- §15 Project Structure

**Agents:**
- §2 Agent Framework (LangGraph / LlamaIndex / OpenAI Agents / Simple Function)
- §3 Tools
- §4 Memory / RAG
- §6 Orchestrator Bindings
- §9 Project Structure (Coded vs Low-code)

**Coded Apps:**
- §2 App Type & Tech Stack
- §3 Pages & Routes
- §4 Components
- §5 State Management
- §6 API Integration
- §10 Project Structure

**API Workflows:**
- §2 Input Schema
- §3 Output Schema
- §4 Execution Flow (high-level steps, no JavaScript)
- §5 Connectors & External Calls
- §10 Project Structure

### Step 3: Decompose Steps Into Implementation Units

Each template has a primary inventory table. Map PDD steps to units:

| Product | Primary Inventory | Unit Type |
|---|---|---|
| RPA (Single Project) | Workflow Inventory | `.xaml` or `.cs` workflow files |
| RPA (Master Project) | Workflow Inventory **per sub-project** | `.xaml` or `.cs` workflow files, grouped by sub-project |
| Flow | Nodes Inventory | Flow nodes |
| BPMN | Activities Inventory | BPMN activities / tasks (service, script, user, call activity, subprocess) |
| Case | Tasks Grid | Tasks per lane/index |
| Agents | Tools | Python functions, RPA/API workflow bindings |
| Coded Apps | Pages + Components | Routes and React/Angular/Vue components |
| API Workflows | Execution Flow steps | Activities (HTTP, Connector, Script) |

Each unit must have: **a concrete responsibility, specific PDD step references, and defined inputs/outputs.**

Type each step's verb and place it on the best-fit component per [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step) — deterministic validate/transfer → RPA or API, document collect → IXP, judgment decide → Agent, atomic transform/compute → Function, review/sign-off → HITL, aggregate → Data Fabric. Record the placement in the inventory row; every non-primary placement becomes an integrated component in Step 4.

**For RPA Master Project:** decompose in two passes:
1. First, assign each PDD step to a sub-project based on the §10 sub-projects table (each sub-project lists its PDD steps).
2. Then, within each sub-project, decompose the assigned steps into workflow files.
3. For REFramework sub-projects, the main workflows (Init, GetTransactionData, Process, SetTransactionStatus) come from the framework — only the Process-specific workflows go in the inventory.

### Step 4: Flag Integrated Components

For each integrated component detected in Phase 1 (and each non-primary placement from Step 3), flag it in the appropriate section of the template:

- **HITL** — host-aware routing: Flow hosts → flag touchpoints; implementation task routes to `uipath-human-in-the-loop`. Coded Agents → escalation is part of the `uipath-agents` build task (the HITL skill defers coded-agent wiring to it). BPMN userTask → flagged in §9 HITL Touchpoints, authored inline by `uipath-maestro-bpmn` (no HITL-skill task). Case → inline HITL task type in the Tasks Grid (never the HITL skill). RPA → Action Center / long-running workflow flagged in the RPA template.
- **Integration Service connectors** → list in Application Inventory (RPA) or Connectors section (others); check `uip is connectors list` — implementation task routes to `uipath-platform` to configure an existing connector, or `uipath-connector-builder` to build a custom one when none exists
- **IXP / Document Understanding models** (extraction from semi-structured documents) → list in the host template's "IXP / Document Understanding Models" table (Flow / BPMN / Case / Agent / RPA templates carry it); for an API Workflow or Coded App primary, record the model as its own row in §Solution / Project Breakdown instead. Implementation task routes to `uipath-ixp`, ordered before its consumers
- **Coded Functions** (TypeScript / JavaScript / Python — atomic deterministic transform / compute: parsing, scoring, custom-auth API calls, IS-connection queries) — only when extraction is justified per [placement rule 6](product-selection-guide.md#per-task-component-placement-the-to-be-per-step); host-native logic stays in the host's own inventory → list in the host template's "Coded Functions" table (Flow / BPMN / Case / Agent templates carry it). Implementation task routes to `uipath-functions`, ordered before its consumers; no per-project SDD file (see [Template Mapping](product-selection-guide.md#template-mapping))
- **RPA processes called by Flow/Agent/Case** → list in Integrated Components section; implementation task will create the RPA project
- **API Workflows called by Flow/Agent/Case** — only when extraction is justified per [placement rule 6](product-selection-guide.md#per-task-component-placement-the-to-be-per-step) (host cannot call natively, 2+ consumers, or independent lifecycle); a host-capable direct call stays in the host inventory as `Access Method = Direct HTTP` → list in Integrated Components section; implementation task will create the API Workflow project

### Step 5: Present Architecture for Review

Present the architectural core to the user. Wait for approval or adjustments.

**Approval criteria:** any response without specific change requests. Responses like "looks good", "ok", "proceed", "yes", or a topic change all count as approval. If the user requests specific changes, incorporate them and re-present the architecture (max 3 revisions — after that, proceed with the latest version and tag disagreements as `[SME REVIEW]`).

## Phase 3 — Full SDD Generation

> **Progress:** Mark "Generate architecture (Phase 2)" as `completed`. Mark "Generate full SDD (Phase 3)" as `in_progress`.

> **Write early, append incrementally — the file on disk is the deliverable.** Do NOT hold the entire SDD in context and write only at the very end. As soon as Phase 2 has produced the architectural core, write a first valid file: the header + `## Planner Handoff` header **and** the `<!-- planner-handoff:v1 -->` marker + `## Decisions Made` block (autonomous) + the Phase 1 / Phase 2 sections you already have. Then append the remaining Phase 3 sections to that file with follow-up `Edit`/`Write` calls. Rationale: a long autonomous turn can hit the per-turn watchdog mid-generation — an incrementally-written file leaves a gradeable, useful SDD on disk instead of nothing. The Planner Handoff header + marker MUST be in this first write so detection (and grading) works even on a partial file — **with `Status: draft` and `Template validation: pending`**: the marker says "planner SDD", the Status field says whether it is consumable. Step 1.5 (SME resolution) and the Step 2 superset check still run; they patch and verify the already-on-disk file rather than gating the first write. Flipping `Status` to `ready` is the LAST write of Phase D — an interrupted run leaves `draft` on disk and Lane A refuses to derive tasks from it.

### Step 1: Generate Remaining Sections

Fill in all sections of the chosen template not covered in Phase 1 or Phase 2. Section assignments per phase:

**Phase 1 produces (for all templates):**
- Header & Document History (process name, today's date, version 1.0)
- Overview section (§1)
- Process/Flow/Lifecycle diagram (§2 for most templates)
- Detailed steps / nodes description where applicable

**Phase 2 produces:** See Phase 2 Step 2 above (template-specific architectural core)

**Phase 3 produces:** All remaining sections — typically:
- Business Rules (RPA, Case)
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
- **Reusable Components / Libraries — always (best practice).** List reused existing shared assets (tenant Libraries discovered in Step 2.5, Marketplace / org components, existing connectors) AND new reusable assets to build (shared workflows → an RPA **Library** routed to `uipath-rpa`; a missing integration → a **custom connector** routed to `uipath-connector-builder`), each built before its consumers. Assets used by 2+ projects live at the parent-folder / solution level. See [Product Selection Guide → Reusability & shared assets](product-selection-guide.md#reusability--shared-assets).
- **Testing Strategy — always thorough.** Cover happy path, edge cases, error scenarios, and (for Master Projects) end-to-end pipeline tests. Do NOT ask the user about test depth — depth is non-negotiable here. Implementation specialists may scope tests down at execution time if the user wants a quick MVP.
- **Next Steps — points at Lane A (task derivation).** Replaces the legacy "Implementation Plan" section. Lane A owns the implementation task list; Phase D does not generate one.

> **What Phase 3 does NOT produce:** an Implementation Plan section, a task list, or `TaskCreate` calls for implementation work. Those are owned by Lane A (task derivation). The SDD's `## Next Steps` section marks the boundary into Lane A, and that is the entire Phase D output surface.

### Step 1.5: Resolve SME Review Items

> **Progress:** Mark "Generate full SDD (Phase 3)" as `completed`. Mark "Resolve SME review items" as `in_progress`.

Before writing the SDD, collect all `[SME REVIEW]` items. If there are any:

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

### Step 2: Write the SDD File(s)

> **Progress:** Mark "Resolve SME review items" as `completed`. Mark "Write SDD to disk" as `in_progress`.

1. Assemble all sections in template order. If you followed the write-early principle above, the file already holds the header + handoff + Phase 1/2 sections — finalize it by appending/patching the remaining sections in template order rather than rewriting from scratch.
2. **Fill the `## Planner Handoff` header** that appears in every template after `## Document History`. This is the load-bearing detection contract. The Entry Guard accepts **either** the heading OR the adjacent `<!-- planner-handoff:v1 -->` HTML marker as a detection signal — both ship in every template and both should survive into the generated file (so a later session, or a hand-written SDD, still routes to Lane A):

   ```markdown
   <!-- DO NOT RENAME: uipath-planner detects SDDs via this exact heading or the marker below. -->
   <!-- planner-handoff:v1 -->
   ## Planner Handoff

   | Field | Value |
   |---|---|
   | **Status** | draft → ready                                  ← the first incremental write stamps `draft`; flip to `ready` ONLY after Step 1.5 ran (every surviving SME item classified `default-carried`) AND the item 8 template-superset check passes. A `blocking` SME item keeps `draft`. Lane A derives tasks from `ready` only.
   | **Execution autonomy** | <autonomous | interactive>          ← from Phase 1 Step 0
   | **Delivery model** | <cloud | automation-suite | standalone | unspecified> ← from Phase 1 Step 0 (append the Suite version when known, e.g. `automation-suite 2025.1`)
   | **SDD scope** | <single-product | solution>                  ← from Phase 1 Step 4 (Level 1 / Level 1.75)
   | **Solution root SDD** | <SOLUTION_NAME_KEBAB>-solution-sdd.md ← solution scope ONLY — write into EVERY SDD (the root names itself); omit all four solution rows for single-product
   | **Solution ID** | <SOLUTION_NAME_KEBAB>                       ← same value in the root and every child; Lane A verifies the match
   | **Project SDD role** | root | child                           ← `root` in the solution overview, `child` in every per-project SDD
   | **Independently executable** | no                              ← children only; Lane A refuses to derive tasks from a child directly
   | **Project list section** | §11 / §10 + §11 / Project Inventory ← template-specific (RPA single: §11; RPA Master: §10 + §11; Flow: §3 + §7; BPMN: §4 + §9; etc.)
   | **Tasks file** | `<PROCESS_NAME_KEBAB>-tasks.md`             ← planner writes here on first run. Solution scope: root AND every child carry the SAME canonical `<SOLUTION_NAME_KEBAB>-tasks.md` — exactly one tasks file per solution, never one per project
   | **Generated by** | uipath-planner
   | **Generation date** | <YYYY-MM-DD>
   | **Template validation** | pending → passed                   ← set to `passed` together with the `ready` flip (item 8)
   ```

   Do NOT rename the heading or strip the marker. They are redundant on purpose — keeping both means a hand-edit of one signal does not silently break Lane A detection.

3. **Autonomous-mode Decisions Made block.** If `Execution autonomy: autonomous`, insert a `## Decisions Made` block immediately after the Planner Handoff header and before any `Action Required — SME Review Items` block or the Table of Contents. The block makes the five highest-leverage architectural picks scannable in the SDD's first screenful so a reviewer can spot a wrong call without reading the whole document. In `Execution autonomy: interactive`, this block is optional — the user already reviewed each decision at the Phase 1/Phase 2 checkpoints. Skip the block for interactive runs.

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
   - The block does NOT replace the per-section detail later in the SDD — §10 / §11 / §13 still carry the full justification. The block is the **scannable index** of those decisions.

   In BOTH modes, also emit the `## Recommended Scope` block directly after `## Decisions Made` (directly after the Planner Handoff header when that block is absent — interactive runs): copy the Phase 1 summary's `Recommendation:`, `Delivery model:`, and `Blocked by platform:` lines (see [product-selection-guide.md → Summary block](product-selection-guide.md#summary-block)). Autonomous mode skips the Phase 1 presentation, so this copy is the only durable record of the Constraint Gate outcome.

4. If any `[SME REVIEW]` items remain, add a consolidated warning section after the Planner Handoff header (and after the `## Decisions Made` / `## Recommended Scope` blocks if present) and before the Table of Contents:

```markdown
## Action Required — SME Review Items

| # | Section | Item | Question | Default applied | Blocking |
|---|---|---|---|---|---|
| 1 | <SECTION> | <ITEM> | <QUESTION> | <DEFAULT> | <yes/no> |

> These items are marked `[SME REVIEW]` in the document. Default-carried items (Blocking = no) do not block task derivation — the automation is built on the recorded defaults, which must be verified before production sign-off. Any Blocking = yes item keeps the handoff at `Status: draft`.
```

5. **Target SDD length: 300-800 lines of markdown** for single-project SDDs. **Master Project SDDs may reach 600-1200 lines** due to per-sub-project structure sections — this is expected. For processes with more than 20 steps, group related steps and summarize at the parent level. For processes with more than 10 business rules, prioritize the 10 most impactful.
6. **Re-run handling.** If `<PROCESS_NAME_KEBAB>-sdd.md` already exists, ask the user via `AskUserQuestion`:

   First read the existing file's handoff `Status`:

   - **`Status: ready` (or no Status field — legacy):**

   > An SDD already exists at `<sdd-path>`. How should I proceed?
   >
   > 1. **Keep the existing SDD and stop** *(recommended)* — proceed to Lane A if you want to refresh the task list
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
   - **Other templates:** check the template file's TOC; the rule is the same — every H2 in the template appears in the generated SDD.

   For any missing required H2:
   1. Regenerate that section from the template + Phase 1 extraction data + Phase 2 architecture.
   2. If the template's contents for that section depend on a Phase 1 / Phase 2 input that is genuinely absent (e.g. §4 Business Rules but the PDD has zero rule signals), emit the section with an explicit "No business rules extracted from the PDD" note plus an `[SME REVIEW]` row asking the user to supply any.
   3. Never silently drop a section.
   4. **Ready flip — the final write of Phase D.** When every required heading is present and every remaining `[SME REVIEW]` item is classified `default-carried` (Step 1.5 rule 5), update the handoff: `Status: ready`, `Template validation: passed`. Open default-carried items do NOT block ready — they gate production sign-off, not task derivation. Any `blocking` item keeps `Status: draft`; the item 9 summary names it and asks. Skipping the flip leaves the file at `draft` and Lane A will refuse to derive tasks from it.

   Common slip-fail: skipping §4 Business Rules because the PDD has no dedicated "Business Rules" section. Rules are usually buried in "Remarks", step descriptions, or screenshots — the PDD analysis guide's "Embedded business rules" pointer applies. Treat zero rules in §4 as a regeneration trigger, not a finished section.

9. Output a summary in the conversation:

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

When the user asks for a Word or client-facing deliverable, convert the written SDD — do not author Word content by hand or drive Word via COM.

**Plain `.docx` of the SDD:**

```bash
# macOS / Linux / Git Bash:
bash <SKILL_DIR>/scripts/sdd-to-docx.sh "<SDD_PATH>.md" [--reference-doc "<TEMPLATE>.docx"]
# Windows without Git Bash (Windows PowerShell 5.1 or pwsh 7+):
pwsh -File <SKILL_DIR>/scripts/sdd-to-docx.ps1 "<SDD_PATH>.md" [--reference-doc "<TEMPLATE>.docx"]   # or: powershell -File ...
```

`--reference-doc` applies a customer template's fonts, heading styles, and margins. The section structure stays as the markdown SDD.

**Official client SDD/ASDD (customer's structure):** the markdown SDD is agent-first; the official Word document is the client deliverable in the customer's own section layout. Ask the user for the template path, then follow [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) to match the markdown SDD into the template's sections and compute the missing pieces. Do not invent the official section structure.

**Diagrams:** keep them as Mermaid and make them readable — clear node labels, one node per step, a logical direction. They convert as code blocks. Rendering them to images and styling the final document are not this skill's job — leave that to the user or their doc tooling.

If the script reports pandoc missing, relay its install command.

Skip this step entirely when the user did not ask for Word output.

### Step 3: Proceed to Lane A (Task Derivation)

> **Progress:** Mark "Write SDD to disk" as `completed`. All progress tasks are now done.

The SDD is the deliverable of Phase D. **Do not generate an Implementation Plan section inside the SDD. Do not create implementation `TaskCreate` calls during Phase D. Do not start executing.**

> **The SDD write is a turn boundary — do not begin Lane A in the same turn as Phase D.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue into Lane A on the **next** turn. Rationale: Phase D (read PDD + guides, author §1–§18) and Lane A (parse SDD, derive tasks, emit `TaskCreate`) are each heavy; stacking both in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after a durable SDD write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.

Then continue based on the user's intent:

- If the user's intent implies implementation ("create / build / implement / set up / make") → on the next turn, continue into Lane A with `<sdd-path>`. Lane A reads the `## Planner Handoff` header you wrote, derives tasks, writes `<process-kebab>-tasks.md` alongside the SDD, and emits live tasks routing to specialist skills — see [pdd-driven-lane-guide.md](pdd-driven-lane-guide.md).
- If the user only asked to "design / architect / generate an SDD" → stop here; the SDD is enough.
