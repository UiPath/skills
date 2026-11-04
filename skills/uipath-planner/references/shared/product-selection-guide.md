# Product Selection Guide

This is the most important decision the SDD makes. Select the wrong product and the architecture is wrong. This guide produces a scope recommendation from PDD signals, covering every UiPath product and multi-project Solutions.

## How selection works — four layers

Selection is layered, not one whole-process pick. **Solution is packaging, not a runtime tool** — and Integration Service, Action Center, IXP, and Libraries are capabilities/components, not automatic primaries. Layer 0 precedes everything: the [Suitability Gate](#level-0--suitability-gate) decides whether to automate at all. Then design the component topology; decide packaging last.

1. **Decompose the process into steps** — Phase 1 extraction + the [need profile](../design/design-guide.md#step-35-synthesize-the-need), recording the per-step factors (interface, determinism, state, human interaction, volume, risk, reuse, runtime, existing estate).
2. **Choose an executor per step** — the [Per-task component placement](#per-task-component-placement-the-to-be-per-step) table (RPA / API / IXP / Agent / LLM activity / Function / HITL / Data Fabric).
3. **Choose the coordination & state host** — the Level 1 decision table: a single host absorbs in-process capabilities (absorption fold); Maestro (Flow / BPMN / Case) only when peer runtimes or the coordination shape exceed a single host.
4. **Choose packaging & deployment last** — standalone package vs Solution (`.uipx`), via Solution Signals / Level 1.75 and the Constraint Gate. A single-component design does not need a Solution wrapper by default.

The layers run **in order**: layers 1–2 execute in Phase 1 — Step 3.5 synthesizes the need AND types each extracted step with the placement table, producing the **step→executor map**. Level 1 (layer 3) consumes that map — it never matches raw keywords against the whole process. Solution Signals / Level 1.75 and the template's packaging decision are layer 4.

## Levels of Decision

This file is the canonical home for **Levels 1, 1.75, 2.5 Part B, and 3**. RPA-specific levels (**1.5, 2, 2.5 Part A**) live only in the [RPA Product Guide](../design/rpa-product-guide.md); run Level 1.5 once per RPA project.

| Level | Decision | Scope | Canonical home |
|---|---|---|---|
| **0. Suitability** | Automate / redesign first / reuse native or estate / do not automate | All PDDs | This file |
| **1. Primary scope** | Single product or multi-project Solution? | All PDDs | This file |
| **1.5. RPA sub-type** | Process, Library, or Test Automation | Only when RPA is selected at Level 1 (or included in a Solution) | [RPA Product Guide](../design/rpa-product-guide.md#level-15--rpa-sub-type-selection) |
| **1.75. Solution composition** | Which products and how many projects of each | Only when Level 1 = Solution | This file |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Per RPA project in the final list | [RPA Product Guide](../design/rpa-product-guide.md#level-2--authoring-mode) |
| **2.5. Part A — RPA decomposition** | Single Project vs Master Project per RPA Process | Per RPA Process project in the scope | [RPA Product Guide](../design/rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) |
| **2.5. Part B — Merge** | Final unified project list with roles, frameworks, queues | All scopes | This file |
| **3. Capabilities** | HITL, Integration Service, API Workflow as component | All products | This file |

## Constraint Gate

The delivery model (asked or detected at Phase 1 Step 0) and any user-stated product exclusions filter every candidate **before** any level recommends it. Run the gate at Level 1 (before presenting the primary scope), at Level 1.75 Pass A (before composing the option list), and at Level 3 (before flagging a capability add-on).

1. **Look each candidate product up in [platform-availability-guide.md](platform-availability-guide.md)** under the customer's delivery model column.
2. **Not available → BLOCK.** Remove the product from the recommendation and from Level 1.75 Pass A options. Recommend the matrix's documented alternative instead. Record the block in the `Decisions Made` row 1 and in the Recommended Scope summary (`Blocked by platform:` line). Row 1 is emitted even when nothing is blocked — it then reads `<delivery model>; no products blocked`.
3. **Partial / uncertain → WARN.** Keep the product but attach an explicit warning line naming what is limited or unverified, and apply the verification rule in [platform-availability-guide.md](platform-availability-guide.md) before finalizing the SDD.
4. **User exclusions are blocks.** When the user excludes a product ("we don't want Maestro"), treat it exactly like a matrix block for the rest of the session: never re-offer it at any level or revision, record the exclusion and its reason in the Recommended Scope summary.
5. **Never silently substitute.** A blocked product's alternative changes the architecture — present the substitution and its consequence in the summary, not buried in a section.

> Delivery model `unspecified` (user picked "Not sure") gates nothing — proceed assuming Automation Cloud, and carry an `[SME REVIEW]` row stating the assumption and which recommended products would be affected if the customer is actually on Automation Suite or standalone.

## Level 0 — Suitability Gate

Not every process should be automated as-is — a Solution Architect first decides WHETHER, not which product. From the need profile, check each item and record the outcome in the Recommended Scope reasoning:

1. **Native capability** — the target system's own configuration already covers the need (workflow rules, scheduled reports, webhooks) → recommend configuration, not automation.
2. **Existing estate** — an already-deployed process / API Workflow / connector / library / model / solution covers steps → reuse, don't rebuild. Run the [Estate sweep](#estate-sweep) below.
3. **Process stability** — the process, UI, or rules are mid-change → defer or flag `[SME REVIEW]`; automating a moving target is rework.
4. **Redesign first** — steps that exist only to work around manual limitations drop out of the to-be; never automate waste (PDD Analysis Guide → As-Is and To-Be).
5. **Access feasibility** — licenses, API access, credentials, and environment access exist or are obtainable.
6. **Economics** — volume × time saved vs build + run + maintain cost; thin cases → downscope or recommend against.
7. **Residual human work** — what stays manual after automation; when the human loop dominates, automation may not pay.

**Outcomes:** `proceed` (default) · `proceed-with-redesign` (the to-be drops or reshapes steps) · `partial` (automate a subset; rest stays manual or native) · `do-not-automate` (recommend the native capability / process fix — confirm with the user, then end `design` with the [findings note](#do-not-automate-findings-note) instead of a full SDD). Levels 1+ run only on `proceed` / `proceed-with-redesign` / `partial`.

### Estate sweep

Operationalizes item 2. Best-effort and auth-required — same rules as tenant library discovery: never blocks `design`, no mid-generation auth troubleshooting, skip entirely when the user's prompt forbids `uip` commands. Query only the rows matching the step→executor map's candidate products, filtering results by PDD Application Inventory and process-name keywords:

| Estate | Discovery |
|---|---|
| Deployed RPA processes | `uip or processes list --all-folders --output json` |
| Tenant RPA libraries | Step 2.5 tenant library discovery (RPA scopes only) |
| IS connectors / live connections | `uip is connectors list --output json` · `uip is connections list --output json` |
| Deployed Agents | No dedicated listing verb — published agents run as Orchestrator processes: check the `uip or processes list` output |
| Maestro processes | `uip maestro flow processes list --output json` · `uip maestro bpmn processes list --output json` · `uip maestro case processes list --output json` |
| IXP projects / models | `uip ixp projects list --output json` — newer CLIs only; on `unknown command` apply the drift rule below or user-named estate |
| Deployed Solutions | `uip solution deploy list --output json` |
| Data Fabric entities | `uip df entities list --output json` |
| API Workflows | No dedicated listing verb — they publish into Orchestrator: check the `uip or processes list` output, else user-named estate |
| Coded Apps, Coded Functions | No CLI listing — user-named estate only; ask when signals suggest one exists |

CLI surfaces drift across versions. When the installed CLI rejects a listed verb (`unknown command` / `unknown option`), discover the supported surface with `uip <group> --help`, or fall back to the platform API (Orchestrator OData for `or` resources) using the existing authenticated context — never invent a verb. Note any substitution in the Recommended Scope reasoning.

**The estate is the session tenant's** — the same condition as [tenant-library-search-guide.md](tenant-library-search-guide.md) § Default search target. A listing that fails on permissions (HTTP 400/403, no folder accessible) records that estate row as unknown, like an auth failure.

**One round, then stop.** Issue the whole sweep as a single batch of `list` calls, read the results once, and decide. Do NOT re-run the sweep with new filters, alternate search terms, or client-side post-processing after a round that returned zero rows or an empty `Data` array — an empty estate is a final answer (`no reuse candidates`), not a signal to search harder. Do NOT retry a rejected flag with a guessed alternative: apply the drift rule above once, and if that call also fails, record the estate as unknown in the Recommended Scope reasoning and proceed. Every extra sweep round costs a full reasoning cycle inside the same turn that still has to author §1–§18.

Record every covering hit as a reuse candidate in the Recommended Scope reasoning (Level 0 outcome line) and in the consuming template section (§Packages, Integrated Components, or connector rows). A hit that covers steps flips those steps to reuse — outcome `partial` or a downscoped to-be.

### Do-not-automate findings note

Confirm the outcome with the user, then write `<PROCESS_NAME_KEBAB>-findings.md` instead of an SDD and end `design`. Structure:

1. `# <PROCESS_NAME> — Suitability Findings` + generation date
2. `## Outcome` — `do-not-automate`, plus each failed gate item (1–7) with one line of evidence
3. `## Recommended Alternative` — the native capability, process fix, or estate reuse that covers the need, with its owner
4. `## Revisit Triggers` — what would change the decision (volume growth, a stable API appearing, process stabilization)
5. `## Action Required — SME Review Items` — only when open questions remain

The note carries NO `## Planner Handoff` header and NO `planner-handoff:v1` marker — it is terminal: it must never route to `plan` and needs no Status field. `partial` does not produce a findings note — dropped steps are recorded in the SDD's Recommended Scope reasoning.

## Level 1 — Primary Scope Selection

> **Match on the need, not the keyword.** Each row's "Signal in PDD" is *evidence* of an underlying need — the decision is the need it points to, not the literal term. Read the [need profile](../design/design-guide.md#step-35-synthesize-the-need) and pick the product whose purpose fits the need:
>
> **No single factor decides — weigh the whole need profile.** Determinism (rule-expressible vs judgment) is one key factor, not the sole gate; also weigh input structure, whether a stable API exists (API-first — avoid UI fragility), volume/cost (agentic execution is costlier and far less cost-predictable than deterministic — estimate per model/tenant at volume), risk/reversibility/confidence (→ a HITL gate), auditability/compliance, and coordination shape. See the full [need profile](../design/design-guide.md#step-35-synthesize-the-need). Genuine judgment/reasoning is the only thing that justifies an **Agent** (not the words "AI"/"smart"/"automatic"). The dominant pattern is **hybrid** — AI decides, deterministic RPA/API execute as governed tools, Maestro orchestrates when real orchestration is needed (see Light vs real orchestration), HITL gates the risky/low-confidence steps — so a mostly-deterministic process with one judgment step is a deterministic primary + an Agent component, not an Agent overall.
>
> - judgment / reasoning not expressible as fixed rules, or dynamic tool planning → **Agents**
> - a fixed generative step inside a known path → **LLM activity in the host workflow**, not an Agent
> - fixed document classification / extraction → **IXP / Document Understanding** (a component via the placement table; standalone IXP project only when extraction is the entire deliverable)
> - a user-facing screen as the deliverable → **Coded Apps**
> - headless system-to-system integration, no UI, no bot → **API Workflows**
> - a staged case lifecycle with SLA / approvals (potentially ad-hoc tasks) → **Case Management**
> - structured control-flow (formal gateways / events / subprocess) without a case → **Maestro BPMN**
> - a plain multi-automation pipeline → **Maestro Flow**
> - a human approval inside ONE process → **long-running RPA + Action Center** (not Maestro, not a HITL project)
> - headless deterministic compute — no UI, no orchestration → **Coded Function** (component — leaner than an RPA process; placement table)
> - UI automation, or machine-local resource work — Excel/Office, file/folder operations, on-prem databases, desktop email, terminal/mainframe → **RPA**
> - reusable compile-time component → **RPA Library** (additive); regression validation → **Test Automation** (additive — rarely the primary runtime)
>
> **Anti-pattern:** never route on a keyword when the need contradicts it — "AI" over a deterministic rule set is RPA, not Agents; a "dashboard" that is really a scheduled report is not necessarily a Coded App. When evidence and need disagree, the need wins; when the product is genuinely unclear, ask the user (see Presenting the Recommendation).

### Decision table

**Input is the step→executor map (layer 2), not raw keywords.** Type every extracted step with the [Per-task component placement](#per-task-component-placement-the-to-be-per-step) table, then **fold the map** before reading it — mixed capabilities are NOT cross-product orchestration.

**Absorption fold.** A capability step is *absorbed* when a host executor invokes it in-process — an activity or synchronous call whose result returns within the same run:

| Host | Absorbs in-process |
|---|---|
| RPA | DU/IXP extraction (activity or model call), LLM activity, IS connector / direct HTTP call (incl. a published API Workflow), synchronous child calls — invoke a published process or agent and consume the result in the same run, ONE in-flight approval (long-running + Action Center) |
| API Workflow | Connector / HTTP calls, nested synchronous API Workflow calls |
| Coded App | Backend calls to published API Workflows / processes / agents — the app coordinates its own backend |
| Agent | Tools planned at runtime (RPA, API Workflows, Functions, connectors) — ONLY under the coordinator exception below |

Absorbed steps become integrated components (Level 3 + template inventory), not orchestration triggers. **Absorbed ≠ not built:** a consumed IXP model, custom connector, Library, or API Workflow can still be its own buildable project and plan task, ordered before its host — absorption is a runtime statement, not a build statement.

The folded map decides WHICH rows are even eligible as primaries:

- **One host remains** (every other capability absorbed; same-executor projects decoupled by a queue hand-off count as one host — Level 2.5 Part A decides decomposition) → walk rows 1–3 and 7 in priority order; first match wins.
- **Two or more peer runtimes remain** — independently deployed products coordinated at runtime — **or the coordination/state shape exceeds any single host** (case stages/SLA, formal gateways / events / parallel branches, long-running waits spanning multiple automations) → rows 1–3 and 7 are **not eligible as primaries** — walk rows 4–6 (Case → BPMN → Flow) for the coordination host; every remaining peer becomes an integrated component or a Solution project (Level 1.75). A FIXED process with judgment steps is a deterministic host + an Agent component (absorbed when called synchronously in-run; a peer under Maestro when long-running) — **never an Agent-primary design**.
- **Exception — the agent IS the coordinator:** an open-ended or conversational agent that plans its own tool calls at runtime (no fixed process shape to orchestrate) is Agent-primary with RPA / API Workflows as tools (multi-skill Pattern 5). A fixed process that contains judgment steps is NOT this exception.

Signals that match *below* the primary become candidate additional projects in a Solution (see Solution Signals below).

| Priority | Signal in PDD | Primary Scope |
|----------|---------------|---------------|
| 1 | AI reasoning, LLM judgment, tool calling, RAG, knowledge retrieval | Agents |
| 2 | Web dashboard, internal tool, Action Center form as the deliverable | Coded Apps |
| 3 | System-to-system API integration (synchronous, no UI, no bots) | API Workflows |
| 4 | Case lifecycle with stages, SLA tracking, approval gates, task routing | Case Management |
| 5 | Standards-based BPMN process orchestration — parallel / inclusive / event-based gateways, boundary events (activity timeouts / errors), intermediate message or timer events, subprocesses or call activities, multi-instance loops, OR an explicit BPMN 2.0 process-model request — with NO case stages/SLA (those → Case) | Maestro BPMN |
| 6 | Orchestrating MULTIPLE automation types (RPA + agents + apps) with linear / branching node flow and no formal BPMN structure | Maestro Flow |
| 7 | UI automation (web / desktop / Citrix / mainframe), Excel & Office automation, file & folder operations, on-prem database work, desktop email, data processing, reusable component, application testing, or a single process with an in-flight human approval (long-running workflow + Action Center) | **RPA** (sub-type decided at Level 1.5) |
| 8 | Multiple coordinated projects across products or mixed RPA sub-types (e.g., Flow + API Workflows, or 2 Libraries + 1 Test Automation project) | **Solution** (composition decided at Level 1.75) |

Apply the [Constraint Gate](#constraint-gate) to the matched primary before presenting it — a first-match product that is blocked on the customer's delivery model is replaced by the matrix's alternative, not presented with a caveat.

> Row 8 (Solution) is a **packaging/composition outcome** (layer 4), not a runtime product: it is reached ONLY via a [Solution Signal](#solution-signals) — the PDD itself names multiple top-level deliverables, each already typed by rows 1–7 and the placement table. Components the design derives never count toward row 8 ([derived-component rule](#solution-signals)). A single-component design ships as that product — standalone package or single-project Solution per the template's packaging decision.

### Maestro disambiguation — BPMN vs Flow vs Case

All three are Maestro / orchestration-adjacent; apply first-match-wins with these need-based rules:

- **Case Management (priority 4)** wins when work is framed as a **case** moving through **stages** with **SLA / approval gates, escalation, task routing**. Case compiles to BPMN internally — a stage-and-SLA lifecycle is Case even though it is BPMN under the hood.
- **Maestro BPMN (priority 5)** wins for a **structured, long-running (stateful) control-flow process** — spanning many systems and decision points — with formal BPMN semantics but **no case / stage / SLA lifecycle**: parallel / inclusive / event-based gateways, boundary events (per-activity timeouts or error catches), intermediate message / timer events, subprocesses or call activities (invoking a separate Maestro / agentic / case instance), multi-instance loops, or an explicit "model this as BPMN / a swimlane process" request.
- **Maestro Flow (priority 6)** is the default orchestrator for the simpler **node-graph pipeline** — linear or single-branch sequencing of RPA / agents / apps / APIs with data transforms between steps — when none of the BPMN structures above are required.

Rule of thumb: **case entity + stages + SLA → Case; formal gateways/events/subprocess without a case → BPMN; plain multi-automation pipeline → Flow.** When Flow vs BPMN is genuinely close, default to Flow and offer BPMN as an alternative via a structured question — never force BPMN.

**Don't over-orchestrate — RPA does light orchestration itself:** never pick Maestro (Flow or BPMN) just to trigger a single RPA Dispatcher→Performer — that is an RPA Process. A single process that pauses for one human approval is a **long-running RPA workflow + Action Center** ([RPA Product Guide → Long-running workflows](../design/rpa-product-guide.md#long-running-workflows-persistence--action-center)), not Maestro + HITL. Mixed capabilities inside one host never justify Maestro — an RPA process calling an IXP model, an LLM activity, a synchronous API, an agent, or another published process stays an RPA Process ([absorption fold](#decision-table)).

**Light vs real orchestration** — the tie-breaker when several automations appear in one process:

- **Light → stays RPA:** child calls are synchronous and sequential, the parent run completes in one session, state lives in the parent run + queues, failure handling is the parent's retry / REFramework. Calling an agent or a published process from RPA is light orchestration, not a Maestro trigger.
- **Real → Maestro:** state must outlive any single run (multi-day waits, event / timer resume), parallel or event-driven branches, per-step end-to-end visibility / SLA / compensation, multiple human touchpoints, or the parent would be pure glue between peers with no work of its own.

### Solution Signals

A Solution is the correct primary when any of the following applies, even if a single product would otherwise match at priority 1-6:

- The PDD describes **two or more distinct top-level products** that must coexist (e.g., Flow that calls an API Workflow that is itself a deliverable).
- The PDD mentions **reusable components** that other automations consume (Library) AND a standalone process that uses them.
- The PDD calls out a **dedicated test suite / regression pack** alongside the process being tested (Test Automation + the Process it validates).
- The PDD describes **multiple independent streams** with no single runtime orchestrator (e.g., separate dispatchers feeding separate performers with no Flow tying them together).

When any of the above applies, set the default primary to **Solution** and pre-compose the product list from the matched signals. Otherwise default to the highest single-product match.

**Derived components never escalate scope.** Deliverables named by the requirements set the scope; the part count of the design never does. Solution Signals test what the **PDD names as deliverables** — every scope-shaped decision downstream (single-product vs Solution, template choice, SDD file layout, packaging) follows that answer, never the number of buildable parts the design ends up with. Any supporting component the design introduces (wrapper API Workflow, custom connector, IXP model, Coded Function, Library) inherits its consumer's scope: an integrated-component row in the primary's template plus a build task ordered before its consumer — no solution overview, no per-project SDD, no `SDD scope: solution` flip.

> **Ambiguous dual-product PDDs:** If exactly two products match with similar strength and no Solution signal applies, mark the higher-priority match as the default single-product recommendation and offer Solution (customize) as an alternative in the recommendation screen. Let the user confirm via a structured question.

### Signals per product

Evidence of each need, and the information the SDD needs from the PDD — when an Agent or Coded App lacks it, ask a structured question ([scope-recommendation-guide.md](../design/scope-recommendation-guide.md) § Gap Handling for Agent / Coded App).

| Product | Signals in the PDD | Required PDD information |
|---|---|---|
| Agents (Python + agent.json) | "AI reasoning", "LLM", "GPT", "Claude"; "Tool calling", "function calling"; "RAG", "knowledge base", "semantic search", "vector store"; "Multi-step reasoning", "plan and execute"; "Natural language interface"; Agent decides what to do based on user input, not a fixed script | Framework preference (LangGraph, LlamaIndex, OpenAI Agents, Simple Function); Tools the agent will use (external APIs, RPA processes, API workflows); Memory / RAG sources if applicable; Evaluation criteria (trajectory, success metrics) |
| Coded Apps (Web) | "Dashboard", "web interface", "portal", "internal tool"; "User submits a form"; "Review screen" or "approval UI"; "Action Center custom form"; Deliverable is a web application users interact with | Framework (React, Angular, Vue); App type (Web standalone vs. Action for automation-triggered); Pages / routes / user flows; State management complexity; Who calls the app (direct user, HITL form, Action Center task) |
| API Workflows | System-to-system integration with **no UI** and **no human interaction**; Synchronous request-response pattern (milliseconds to seconds); Pulls, composes, or transforms data across SaaS systems (Workday, Zendesk, Salesforce, ServiceNow, etc.); Consumed by agents as a tool, called from Flows, or over HTTP by external systems; High-throughput requirement (many small, fast operations); **No need for attended/unattended robots** | Input schema (JSON) — parameters the caller provides; Output schema (JSON) — data returned; Connectors or HTTP endpoints to call; Performance expectations (latency, throughput) |
| Case Management | "Stages" or "phases" in the process; "Approval gate" that blocks progression; "SLA" or "service level agreement"; "Escalation" on time or condition; "Case" as a first-class concept (invoice case, ticket case, claim case); BPMN-style multi-lane flow **organized into case stages with SLA / approval gates** (a bare pool/lane BPMN model with no case lifecycle → Maestro BPMN, priority 5); Tasks that can run in parallel within a lane | Stage definitions with entry/exit conditions; Task definitions per stage; SLA rules (time-based or condition-based); Escalation rules |
| Maestro BPMN | Explicit "BPMN", "BPMN 2.0", "process model", "process diagram", or "swimlane process" request; Parallel work that forks and rejoins (parallel gateway) or multiple simultaneous conditional branches (inclusive gateway); A race between events / first-to-arrive routing (event-based gateway); Per-activity timeouts, deadlines, or "cancel / compensate this step if it runs too long or errors" (boundary events); Waiting for or sending a message / signal between running process instances (intermediate message events); Timer waits ("wait N days", scheduled intermediate pauses) that are NOT a case SLA; Reusable containers (subprocesses) or invoking a separate Maestro / agentic / case process (call activities); Processing each item of a collection with sequential or parallel instances (multi-instance loops); Long-running, structured control flow — but NO case entity, stages, SLA, or RACI (→ Case), and beyond a simple linear/branching pipeline (→ Flow) | Control-flow map — activities, gateways, and sequence order; Parallel vs sequential branches and their join points; Events — start-trigger type, intermediate waits / messages, boundary timeouts / errors; Process variables passed between nodes (name, type, direction); Integrated components each activity invokes (RPA, Agent, API Workflow, HITL, connector); Retry / timeout policy per activity; subprocess and call-activity boundaries |
| Maestro Flow | Orchestrating multiple automation types (RPA + agents + apps); Conditional routing between automations; Data transformations between steps (filter, map, group-by); Scheduled triggers; Subflows for reusable grouped logic; "Flow" or "pipeline" terminology | Node sequence with conditional branches; Variables passed between nodes; External systems involved; Trigger type (manual, scheduled, event) |

**Determinism gate (apply before selecting Agents):** confirm the core task needs **non-deterministic** judgment — decisions that cannot be written as explicit rules. If every decision is rule-expressible (even when the PDD says "AI", "smart", or "automatic"), the task is deterministic → RPA / API Workflows / rule-based logic, NOT an Agent. Reserve Agents for genuine reasoning, interpretation, or adaptation over ambiguous input. **Middle tier:** simple summarization or content generation with **no decisioning/escalation** is an *LLM activity inside an RPA/Flow project*, not a standalone Agent — pick an Agent only for decision-making or multi-step reasoning.

**Key distinction from RPA Library:** Libraries are compile-time reusable components for other automations. API Workflows are runtime-callable services over HTTP, serverless, no bots needed.

**RPA:** When Level 1 selects RPA, load the [RPA Product Guide](../design/rpa-product-guide.md) for sub-type signals (Library / Test Automation / Process), Level 1.5 sub-type confirmation, Level 2 authoring mode, and Level 2.5 Part A decomposition. Do not reproduce those decisions here.

## Level 1.75 — Solution Composition

Applies only when Level 1 = Solution OR when the user picks "Solution (customize)" from the recommendation screen at Phase 1 Step 6. Skip otherwise.

The goal of Level 1.75 is to produce a concrete list of projects the SDD will cover. Composition runs in three passes.

### Pass A — Select products to include (multi-select)

**Gate the option list first.** Before composing the questions, drop every product the [Constraint Gate](#constraint-gate) blocks for this delivery model (matrix block or user exclusion) — do not show a blocked product as a selectable option. When a dropped product had matching Level 1 signals, say so in the question preamble with the alternative from the availability matrix. When the matrix lists no alternative (e.g., Coded Apps on Automation Suite — no on-prem equivalent), state that and mark the touchpoint `[SME REVIEW]`; do not substitute a product the planner cannot build.

Keep each structured question to at most 4 options and each prompt to at most four questions — some hosts reject more. Pass A deliberately uses **two questions (8 option slots)** so the full product palette fits one screen, covering **9 candidate products across those 8 slots**: Maestro Flow and Maestro BPMN share one **"Maestro orchestration"** option and are disambiguated by a short follow-up (Pass A.5) only when that option is selected. Pass A therefore stays a single structured prompt containing two questions, each multi-select with ≤4 options. The user answers both questions on one screen; both sets of selections return together.

Ask exactly this prompt (shown as JSON; map it onto your host's question tool):

```json
{
  "questions": [
    {
      "question": "Which core automation layers should the Solution include?",
      "multiSelect": true,
      "options": [
        { "label": "RPA",             "description": "Attended/unattended RPA Process, Library, or Test Automation project(s)" },
        { "label": "Maestro orchestration", "description": "Long-running orchestration across RPA, Agents, APIs, HITL — Flow (node pipeline) or BPMN (standards-based process model); engine chosen next" },
        { "label": "Case Management", "description": "Stage-based workflows with SLA, approvals, and evidence" },
        { "label": "Agents",          "description": "LLM-driven reasoning, tool use, and decisioning" }
      ]
    },
    {
      "question": "Which supporting products should the Solution include?",
      "multiSelect": true,
      "options": [
        { "label": "Coded Apps",      "description": "Custom web UI for operators or business users" },
        { "label": "API Workflows",   "description": "Callable system-to-system integration hosted in Orchestrator" },
        { "label": "RPA Library",     "description": "Reusable workflows distributed via NuGet — implies RPA selected above" },
        { "label": "RPA Test Automation", "description": "Regression / validation project — implies RPA selected above" }
      ]
    }
  ]
}
```

**Pre-selection rules** — before asking, mark each option as pre-selected if the corresponding Level 1 signal matched:

| Option | Pre-select when |
|---|---|
| RPA | Level 1 RPA signals matched (UI, transactional processing, queue-based) |
| Maestro orchestration | Level 1 Flow signals matched OR Maestro BPMN signals matched (orchestration across products, or BPMN gateways / events / subprocess / parallel structure) |
| Case Management | Level 1 Case signals matched (stages, SLA, approvals) |
| Agents | Level 1 Agent signals matched (AI reasoning, tool use) |
| Coded Apps | Level 1 Coded Apps signals matched (custom UI, data entry forms) |
| API Workflows | Level 1 API Workflow signals matched OR another selected product needs a callable integration |
| RPA Library | Library signals matched in the PDD (shared helpers, NuGet distribution) — and pre-select RPA if so |
| RPA Test Automation | Test Automation signals matched (regression pack, assertions) — and pre-select RPA if so |

Assume the question tool has no pre-selection field (options carry only label / description). Mark the recommendation instead: order recommended options first, append **"(Recommended)"** to their labels, and state the signal-matched set in the question text (e.g., "Signals matched: RPA + Agents — keep or adjust"). The user confirms, adds, or removes. Options with no matching signals get no "(Recommended)" tag — the user adds them explicitly if they disagree.

### Pass A.5 — Disambiguate the Maestro engine (only when "Maestro orchestration" is selected)

"Maestro orchestration" resolves to **Maestro Flow** or **Maestro BPMN**. Resolve without a prompt when possible:

- Exactly one of Flow / BPMN Level 1 signals matched and the user did not override → record that engine; **skip the follow-up**. With no BPMN structural signals, default to **Flow**.
- Neither matched, or both matched → ask one follow-up, appending "(Recommended)" to the engine label whose signals matched (no pre-selection field exists):

```json
{
  "questions": [
    {
      "question": "Which Maestro orchestration engine(s) should the Solution use?",
      "multiSelect": true,
      "options": [
        { "label": "Maestro Flow", "description": "Node-graph pipeline — linear/branching orchestration of RPA, Agents, APIs, HITL. Simpler, fastest to author." },
        { "label": "Maestro BPMN", "description": "Standards-based BPMN 2.0 — parallel/event gateways, boundary timeouts, subprocesses, message events, multi-instance loops." }
      ]
    }
  ]
}
```

Selecting both is legal (rare) — one Flow project plus one BPMN project. Feed the chosen engine(s) into the project list as the product for that row. BPMN is never the silent default: choose it only on matched structure or an explicit user pick.

### Pass B — Resolve quantities per product

For products that naturally appear more than once in a Solution (RPA projects most commonly), ask for the count. Ask a numbered-choice structured question with defaults derived from the signals:

> How many RPA projects does the Solution need?
>
> 1. **1** *(recommended if the PDD describes a single end-to-end RPA flow)*
> 2. **2**
> 3. **3 or more** — you will specify the list in the next step

If the user picks "3 or more", follow up with a free-text-style question (a structured question with numbered options covering the most likely counts, plus "Other" for custom).

Flow, Case Management, Agents, Coded Apps, and API Workflows default to **1** each unless the PDD explicitly describes multiple instances.

### Pass C — Run Level 1.5 per RPA project

For each RPA project in the composition, run Level 1.5 to pick its sub-type (Process / Library / Test Automation). Present one structured question per RPA project — do not batch unless the PDD clearly assigns the same sub-type to all of them.

### Output of Level 1.75

Produce a **project list** that feeds Level 2 and Level 2.5:

| # | Project Name (proposed) | Product | RPA Sub-type | Source Signal |
|---|---|---|---|---|
| 1 | `<NAME>_Flow` | Maestro Flow | — | "orchestrates extraction + reporting" |
| 2 | `<NAME>_Extractor` | RPA | Process | "email ingestion + DU extraction" |
| 3 | `<NAME>_SharedUtils` | RPA | Library | "reusable helpers across projects" |
| 4 | `<NAME>_Regression` | RPA | Test Automation | "weekly regression pack" |
| 5 | `<NAME>_LookupApi` | API Workflows | — | "called as a tool from the Flow" |
| 6 | `<NAME>_ScoreFunction` | Function | — | "deterministic scoring called by the Flow" |

**Derived component projects — never Pass A options.** Coded Functions, IXP models, and custom connectors enter the project list from the step→executor map and Level 3 flags — one row per component, ordered before its consumers. Do not offer them in Pass A; confirm them in the recommendation summary instead. They get build tasks but no per-project SDD file (see [Template Mapping](../design/scope-recommendation-guide.md#template-mapping)).

Present this project list in the Phase 1 summary ([scope-recommendation-guide.md](../design/scope-recommendation-guide.md) § Presenting the Recommendation).

## Level 2.5 — Project Decomposition

Produces the final project list that Phase 2 turns into SDD sections. Runs for every scope, but the substantive work differs:

| Scope | What Level 2.5 does |
|---|---|
| Single product, single project (e.g., one Agent, one Flow, one Coded App) | Trivial — produces a one-row project list. Skip Part A. |
| RPA Process (single product) | Part A — run the RPA decomposition signals from the [RPA Product Guide](../design/rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals). Skip Part B (Part A's narrower table is the final project list). |
| Solution (Level 1.75) | Part A — run the RPA decomposition signals on every RPA Process project in the composition. Part B — merge with the non-RPA projects from the Level 1.75 project list to produce the unified project list. |

### Part B — Merge into the final project list

After Part A has been applied to every RPA Process project, merge with the rest of the Level 1.75 composition (or the single product from Level 1) to produce the unified project list.

Produce:

1. **Pattern** per project group: Single Project, Master Project (queue-connected), or N/A (non-RPA).
2. **Unified project list** — one row per concrete project the SDD will describe, covering all products in the scope.
3. **Queue schema** for any Master Projects. The canonical shape is **§12 of the RPA template** — two tables per Master Project group:
   - `Queue Definitions` with columns `Queue Name | Producer Project | Consumer Project | Trigger Type | Max Retries`
   - `Queue Item Schema` (one sub-section per queue) with columns `Field Name | Type | Source | Description`
   Do not invent a different shape here. At Part B, list only the queue names + producer/consumer mapping as a preview; the full schema is filled in Phase 2 against the template.
4. **Cross-product integration notes** — which Flow nodes call which RPA project, which Agent tools call which API Workflow, etc.

Example unified project list for a Solution (Flow + RPA Library×2 + RPA Test Automation + RPA Process expanded into a Master Project):

| # | Project Name | Product | Sub-type | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|---|---|
| 1 | `<NAME>_Flow` | Maestro Flow | — | Orchestrates extraction and reporting | — | — | — |
| 2 | `<NAME>_Dispatcher` | RPA | Process | Collects emails, dispatches to processing queue | Sequence | — | `<QUEUE_1>` |
| 3 | `<NAME>_Performer` | RPA | Process | Processes each transaction item | REFramework | `<QUEUE_1>` | `<REPORTING_QUEUE>` |
| 4 | `<NAME>_SharedUtils` | RPA | Library | Reusable date/string/mapping helpers used by Performer | — | — | — |
| 5 | `<NAME>_IntegrationLib` | RPA | Library | Salesforce + ServiceNow wrappers used by Performer | — | — | — |
| 6 | `<NAME>_Regression` | RPA | Test Automation | Regression pack validating Performer behavior | — | — | — |

## Per-task component placement (the to-be, per step)

Type each step and place it on the component that fits — the canonical UiPath placement model. Applied **twice**: at Phase 1 Step 3.5 to build the step→executor map that feeds Level 1 (layer 2 before layer 3), and at Phase 2 Steps 3–4 of the [Design Guide](../design/design-guide.md) to record each placement in the template's inventory table and flag non-primary components as integrated components. This is how the SDD says **where** API / RPA / Agents / DU / DMN / HITL / Maestro are each needed.

| Task type (verb) | Best-fit component | Routes to |
|---|---|---|
| **Validate / Transfer** — deterministic, rule-based | RPA, or Integration Service / API Workflow if a stable API exists and is reachable from that runtime (rule 5) | `uipath-rpa` / `uipath-platform` / `uipath-api-workflow` |
| **Read / write / transform machine-local data** — Excel/Office files, files & folders on local or network storage, on-prem databases, desktop email | RPA (Excel / Database / Mail activities) — cloud runtimes cannot reach these; API Workflow / Function only when the source is cloud-reachable (rule 5) or the Function is robot-hosted (on-prem endpoints — desktop apps and interactive UI stay RPA) | `uipath-rpa` |
| **Collect** from semi-structured documents | Document Understanding / IXP | `uipath-ixp` (or a DU activity inside RPA/Flow) |
| **Decide / classify** — judgment | AI Agent; or a Business Rules project (DMN decision table) for threshold / eligibility logic | `uipath-agents` / `uipath-rules` |
| **Create / author / summarize** free-form | AI Agent; simple generation with no decisioning = an LLM activity inside the host project (no separate project or task) | `uipath-agents` (standalone Agent only) |
| **Review / Escalate / sign-off**, exception handling | HITL — host-aware: Flow host → HITL skill; coded Agents → escalation wired by `uipath-agents` (per the HITL skill's own deferral); BPMN → inline userTask by the BPMN specialist; Case → inline `action` task detail block in the Case Blueprint; RPA → Action Center / long-running | `uipath-human-in-the-loop` (Flow hosts only) |
| **Wait / approve inside ONE process** | Long-running RPA (persistence + Action Center); an ordinary scheduled or queue-triggered run is just RPA + an Orchestrator trigger — never Maestro | `uipath-rpa` (trigger config → `uipath-platform`) |
| **Sequence / coordinate MULTIPLE automations** — real orchestration only: state outliving a run, parallel / event branches, end-to-end visibility. Synchronous in-run child calls are light orchestration absorbed by the host (Decision table) | Maestro orchestration (Flow / BPMN / Case) | `uipath-maestro-flow` / `-bpmn` / `-case` |
| **Transform / compute** — atomic deterministic custom logic (parsing, scoring, custom-auth API call, ERP query via IS connection) | Host-native code first (rule 6); a Coded Function (TypeScript / JavaScript / Python) when extraction is justified — typed input → deterministic code → typed output; invoked from Maestro / agents / Orchestrator. Runs serverless or robot-hosted — robot-hosted Functions execute inside the environment and reach on-prem endpoints; interactive UI / desktop-app / attended work stays RPA | `uipath-functions` |
| **Aggregate / persist shared data across systems** | Data Fabric entities are the **persistence**, not an executor — the aggregation logic runs in an API Workflow / Function / RPA query that reads and writes the entities | executor per this table + `uipath-platform` (entities) |

Rules:
1. **DU / IXP is extraction from semi-structured documents — NOT free-form authoring** (that's an Agent). Route document-heavy `Collect` to `uipath-ixp`.
2. **Business Rules / DMN** is its own BusinessRules project (`uipath-rules`), deployed in the solution and called by Maestro (BPMN business rule task, Case `business-rule` task) or RPA. Each deterministic decision table that a deployed rule evaluates is a separate project and task routed to `uipath-rules`; rule logic an Agent reasons over stays in the Agent.
3. **Data Fabric / Data Service is storage, never an executor** — entities hold the shared data (`uipath-platform`); the computation over them is always placed on an executor (API Workflow / Function / RPA).
4. **Coded Functions are components, not primaries** — a Function is consumed by Maestro / agents / Orchestrator callers; a request that is *only* a Function is a single-project deferral to `uipath-functions`, not a plan.
5. Deterministic `Validate` / `Transfer` should not reflexively become RPA when a stable API / connector exists **and is reachable from that executor's runtime** — prefer Integration Service / API Workflow (API-first). On-prem HTTP(S) APIs can be reached from Automation Cloud via **Automation Relay** (Integration Service + API Workflows only; needs Unified Standard/Enterprise or Flex Standard/Advanced licensing plus a Relay client deployed on-network) — offer it and confirm with the user; unconfirmed → RPA + `[SME REVIEW]`. Non-HTTP local interfaces (file shares, desktop apps, raw database connections, terminals) are robot-only → RPA.
6. **Extraction test — a separate deployed component must be justified.** Default is host-native: RPA runs Invoke Code, coded Agents use their own Python, API Workflows use script activities, Maestro transforms data between nodes. Mint a separate component (Coded Function, API Workflow) only when at least one holds: (a) the host's surface cannot express the logic or call (low-code IS-only surface, custom auth the host cannot do); (b) 2+ consumers share it; (c) it needs a lifecycle independent of the host — separate versioning, scaling, or ownership. One consumer + host-capable → keep it in the host; no new project, no new task. A call to a third-party system is not subject to this test: it follows the [Integration Service](#integration-service) tiers, so a system with no catalog connector gets a custom connector even for one consumer. Inverse guard: a headless deterministic compute step needing no UI, no activities, and no attended context prefers a Coded Function over minting an RPA process — RPA is not the default home for pure code.

## Level 3 — Capability Add-ons

These are capabilities added to the primary product, not standalone products. When detected, flag them in the appropriate template section. `plan` (task derivation) reads the flags from the SDD when it derives the task list and routes the work to the correct skill.

### HITL (Human-in-the-Loop)

**Scope:** Adds approval gates, exception escalation, and write-back validation. **Only Flow hosts route to `uipath-human-in-the-loop`** (in a single-project request the Flow specialist authors the inline node itself — the HITL-skill task applies to planner-generated multi-project plans). Every other host owns HITL itself: coded Agents → escalation wired by `uipath-agents` (the HITL skill's own deferral); BPMN → inline userTask authored by `uipath-maestro-bpmn`; Case → inline `action` task detail block authored by `uipath-maestro-case`; RPA → Action Center / long-running workflow.

**Signals the PDD needs HITL:**
- "Approval before..."
- "Human reviews..."
- "If confidence is low, escalate..."
- "Validate before writing back..."
- "Fills in missing data..."

**How to flag:** Add a "HITL Touchpoints" line in the host template's relevant section (node table, agent description). For Flow hosts the planner adds an "Add HITL node per §X" task routed to `uipath-human-in-the-loop`; for coded-Agent hosts the escalation is part of the `uipath-agents` build task; for BPMN / Case / RPA hosts the touchpoint stays with the host's own specialist — no HITL-skill task.

### Integration Service

**Scope:** Adds connector activities (Salesforce, Jira, ServiceNow, Slack, etc.) to RPA, Flow, Case Management, or Agents. IS connectors are the standard integration surface for **API Workflows, Maestro (Flow / BPMN / Case), and Agents** — these consume connector activities, not raw UI. A system with no catalog connector gets a custom connector, not a raw API call.

**Signals the PDD needs Integration Service:**
- Third-party SaaS system mentioned (not a custom web app): Salesforce, Jira, ServiceNow, Slack, HubSpot, Workday, Zendesk, etc.
- "Create a ticket in...", "Post a message to...", "Read records from..."

**Check availability — reuse before build.** For each required integration, retrieve the catalog before assuming a connector exists (auth required; best-effort like tenant library discovery):

```bash
uip is connectors list --output json                          # full catalog
uip is connectors list --filter "<KEYWORD>" --output json     # narrow by system name
```

- **Connector exists →** reuse it, whether or not a connection is configured yet. Flag `Access Method = Integration Service — <CONNECTOR_SLUG>`; the planner adds a "Configure <X> connector" task routed to `uipath-platform`, and a missing connection is an `[SME REVIEW]` provisioning item.
- **No connector, and the API is REST+JSON →** build a **custom connector**, for every consumer, including one that could call HTTP itself. Flag `Access Method = Custom connector — <CONNECTOR_SLUG>`; the task is routed to `uipath-connector-builder` and ordered before its consumers. Do not fall back to a direct HTTP call or an API Workflow wrapper because only one host consumes the API. An unverified connector is an `[SME REVIEW]` item — never assume one exists. The connector is an integrated component — scope is unchanged ([derived-component rule](#solution-signals)).
- **No connector, and a custom connector cannot cover the API** (not REST+JSON, or an auth scheme the connector builder cannot express) → a direct authenticated call (tier 4 below). Flag `Access Method = Direct HTTP`, keep the key in a `Credential` asset, and write the justification in the SDD.

#### Integration mechanism — connection before raw API call

For each third-party system the design talks to, pick the highest tier that works and record it in the SDD:

| Tier | Approach | Use when |
|---|---|---|
| 1 | IS **connector activity** | A catalog connector covers the operation |
| 2 | HTTP request through that connector's **IS connection** | Connector exists, activity missing |
| 3 | **Build a custom connector** (`uipath-connector-builder`) | No catalog connector; REST+JSON API |
| 4 | Direct authenticated call, key in a `Credential` asset | Nothing above fits; justify it in the SDD |

A `Credential` asset keeps the secret safe, not the integration managed: a tier-4 call is absent from `uip is connections list` and cannot be re-pointed per environment. A missing catalog connector argues for tier 3, not tier 4.

### API Workflow (as integrated component)

**Scope:** When API Workflow is NOT the primary but is called by the primary (Maestro Flow, Maestro BPMN, Case Management, Agent, another API Workflow).

**Signals** (must also pass the extraction test — [placement rule 6](#per-task-component-placement-the-to-be-per-step)):
- The primary product invokes a callable system-to-system integration with structured JSON input/output (not UI), AND at least one extraction justifier holds: the host cannot make the call natively (IS-only surface), 2+ consumers share the integration, or it needs independent versioning / scaling / ownership.

A third-party API with no catalog connector gets a custom connector (see Integration Service above), not an API Workflow wrapper.

**How to flag:** In the primary product's template, list API Workflow invocations in the relevant section (Flow nodes, BPMN Activities Inventory serviceTask rows, Agent tools, Case tasks). The planner picks this up and creates a per-API-Workflow task that routes to `uipath-api-workflow`. Scope is unchanged ([derived-component rule](#solution-signals)).

### Reusability & shared assets

Design for reuse — a modular solution built from small automations is cheaper to build and maintain. For each candidate shared asset, **reuse before build**, and when building new, treat it as its own buildable project built **before** its consumers:

- **RPA Library** — shared/common workflows (date/string/mapping helpers, app wrappers) extracted into a Library (Level 1.5 sub-type). **Reuse:** discover deployed tenant libraries via the [Tenant Library Search](tenant-library-search-guide.md) (Phase 1 Step 2.5) and reference them in §Packages. **Build new:** a new Library is its own RPA project routed to `uipath-rpa`, consumed by others.
- **Custom connector** — when the catalog has no Integration Service connector (see [Integration Service](#integration-service) above), build a reusable custom connector via `uipath-connector-builder`; one connector serves many projects.
- **Reusable components** — shared components from the Marketplace / org repo (reuse) or new-to-build. List both in the SDD's **Reusable Components** section (reused existing + new reusable).
- **Shared scope / modularity** — an asset used by 2+ projects (Library, custom connector, IS connection, asset, queue) lives at the **parent-folder / solution level**, built once and referenced by all — never duplicated per project.

Flag every reused and new-to-build shared asset in the SDD; the planner emits a build task for each new one (Library → `uipath-rpa`; custom connector → `uipath-connector-builder`), ordered before its consumers.
