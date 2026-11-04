# Product Selection Guide

This is the most important decision the SDD makes. Select the wrong product and the architecture is wrong. This guide produces a scope recommendation from PDD signals, covering every UiPath product and multi-project Solutions.

## How selection works — four layers

Selection is layered, not one whole-process pick. **Solution is packaging, not a runtime tool** — and Integration Service, Action Center, IXP, and Libraries are capabilities/components, not automatic primaries. Layer 0 precedes everything: the [Suitability Gate](#level-0--suitability-gate) decides whether to automate at all. Then design the component topology; decide packaging last.

1. **Decompose the process into steps** — Phase 1 extraction + the [need profile](../design/design-guide.md#step-35-synthesize-the-need), recording the per-step factors (interface, determinism, state, human interaction, volume, risk, reuse, runtime, existing estate).
2. **Choose an executor per step** — the [Per-task component placement](component-placement-guide.md#per-task-component-placement-the-to-be-per-step) table (RPA / API / IXP / Agent / LLM activity / Function / HITL / Data Fabric).
3. **Choose the coordination & state host** — the Level 1 decision table: a single host absorbs in-process capabilities (absorption fold); Maestro (Flow / BPMN / Case) only when peer runtimes or the coordination shape exceed a single host.
4. **Choose packaging & deployment last** — standalone package vs Solution (`.uipx`), via Solution Signals / Level 1.75 and the Constraint Gate. A single-component design does not need a Solution wrapper by default.

The layers run **in order**: layers 1–2 execute in Phase 1 — Step 3.5 synthesizes the need AND types each extracted step with the placement table, producing the **step→executor map**. Level 1 (layer 3) consumes that map — it never matches raw keywords against the whole process. Solution Signals / Level 1.75 and the template's packaging decision are layer 4.

## Levels of Decision

This file is the canonical home for **Level 1**; **Levels 1.75 and 2.5 Part B** live in [solution-composition-guide.md](../design/solution-composition-guide.md), **Level 3** and per-task component placement in [component-placement-guide.md](component-placement-guide.md). RPA-specific levels (**1.5, 2, 2.5 Part A**) live only in the [RPA Product Guide](../design/rpa-product-guide.md); run Level 1.5 once per RPA project.

| Level | Decision | Scope | Canonical home |
|---|---|---|---|
| **0. Suitability** | Automate / redesign first / reuse native or estate / do not automate | All PDDs | This file |
| **1. Primary scope** | Single product or multi-project Solution? | All PDDs | This file |
| **1.5. RPA sub-type** | Process, Library, or Test Automation | Only when RPA is selected at Level 1 (or included in a Solution) | [RPA Product Guide](../design/rpa-product-guide.md#level-15--rpa-sub-type-selection) |
| **1.75. Solution composition** | Which products and how many projects of each | Only when Level 1 = Solution | [solution-composition-guide.md](../design/solution-composition-guide.md#level-175--solution-composition) |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Per RPA project in the final list | [RPA Product Guide](../design/rpa-product-guide.md#level-2--authoring-mode) |
| **2.5. Part A — RPA decomposition** | Single Project vs Master Project per RPA Process | Per RPA Process project in the scope | [RPA Product Guide](../design/rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) |
| **2.5. Part B — Merge** | Final unified project list with roles, frameworks, queues | All scopes | [solution-composition-guide.md](../design/solution-composition-guide.md#part-b--merge-into-the-final-project-list) |
| **3. Capabilities** | HITL, Integration Service, API Workflow as component | All products | [component-placement-guide.md](component-placement-guide.md#level-3--capability-add-ons) |

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

**Input is the step→executor map (layer 2), not raw keywords.** Type every extracted step with the [Per-task component placement](component-placement-guide.md#per-task-component-placement-the-to-be-per-step) table, then **fold the map** before reading it — mixed capabilities are NOT cross-product orchestration.

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
