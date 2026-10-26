# Product Selection Guide

Produce the scope recommendation from PDD signals for all 8 UiPath products and multi-project Solutions. Select in layers: **Solution is packaging, not a runtime tool**; Integration Service, Action Center, IXP, and Libraries are capabilities/components, not automatic primaries.

## How selection works — four layers

Layer 0 decides whether to automate. Then:

1. **Decompose the process into steps** in Phase 1 extraction and the [need profile](sdd-generation-guide.md#step-35-synthesize-the-need), recording interface, determinism, state, human interaction, volume, risk, reuse, runtime, and existing estate.
2. **Choose an executor per step** with [Per-task component placement](#per-task-component-placement-the-to-be-per-step), producing the **step→executor map** (RPA / API / IXP / Agent / LLM activity / Function / HITL / Data Fabric).
3. **Choose the coordination/state host** from Level 1. A host absorbs in-process capabilities; choose Maestro (Flow / BPMN / Case) only when peer runtimes or coordination shape exceed one host.
4. **Choose packaging/deployment last**: standalone package or Solution (`.uipx`) via Solution Signals / Level 1.75 and the Constraint Gate. A single component does not need a Solution wrapper by default.

Layers 1–2 run in Phase 1 Step 3.5; Level 1 consumes the typed map, never raw keywords. Solution Signals / Level 1.75 and template packaging are layer 4.

## Levels of Decision

| Level | Decision | Scope | Canonical home |
|---|---|---|---|
| **0. Suitability** | Automate / redesign first / reuse native or estate / do not automate | All PDDs | This file |
| **1. Primary scope** | Single product or multi-project Solution? | All PDDs | This file |
| **1.5. RPA sub-type** | Process, Library, or Test Automation | RPA selected at Level 1 or in Solution | [RPA Product Guide](rpa-product-guide.md#level-15--rpa-sub-type-selection) |
| **1.75. Solution composition** | Products and project quantities | Level 1 = Solution | This file |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Each RPA project | [RPA Product Guide](rpa-product-guide.md#level-2--authoring-mode) |
| **2.5 Part A** | RPA decomposition | Each RPA Process project | [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) |
| **2.5 Part B** | Final projects, roles, frameworks, queues | All scopes | This file |
| **3. Capabilities** | HITL, Integration Service, API Workflow as components | All products | This file |

## Constraint Gate

The delivery model (asked or detected at Phase 1 Step 0) and user exclusions filter candidates **before** recommendation. Run it at Level 1, Level 1.75 Pass A, and Level 3.

1. Look up each candidate in [platform-availability-guide.md](platform-availability-guide.md) under the customer's delivery-model column.
2. **Not available → BLOCK:** remove it from recommendations and Level 1.75 Pass A; recommend the matrix alternative; record the block in `Decisions Made` row 1 and Recommended Scope `Blocked by platform:`. Always emit row 1: `<delivery model>; no products blocked` when none is blocked.
3. **Partial / uncertain → WARN:** keep it, name the limitation or uncertainty explicitly, and apply the verification rule in [platform-availability-guide.md](platform-availability-guide.md) before finalizing the SDD.
4. **User exclusions are blocks:** treat an excluded product exactly like a matrix block for the rest of the session: never re-offer it at any level or revision; record the exclusion and reason in Recommended Scope.
5. **Never silently substitute:** present the alternative and architectural consequence in the summary.

Delivery model `unspecified` gates nothing: proceed assuming Automation Cloud and add an `[SME REVIEW]` row stating the assumption and which recommendations would change on Automation Suite or standalone.

## Level 0 — Suitability Gate

From the need profile, record each result in Recommended Scope reasoning:

1. **Native capability:** if configuration already covers it (workflow rules, scheduled reports, webhooks), recommend configuration.
2. **Existing estate:** reuse deployed process / API Workflow / connector / library / model / solution; run the [Estate sweep](#estate-sweep).
3. **Process stability:** defer or flag `[SME REVIEW]` when process, UI, or rules are changing.
4. **Redesign first:** remove workaround steps from the to-be; never automate waste (PDD Analysis Guide → As-Is and To-Be).
5. **Access feasibility:** licenses, APIs, credentials, and environments exist or are obtainable.
6. **Economics:** compare volume × time saved with build/run/maintenance cost; downscope or recommend against thin cases.
7. **Residual human work:** assess remaining manual work; if the human loop dominates, automation may not pay.

Outcomes: `proceed` (default), `proceed-with-redesign` (the to-be drops or reshapes steps), `partial` (automate a subset; rest stays manual or native), or `do-not-automate`. The last recommends native capability/process fix, confirms with the user, then ends Phase D with the [findings note](#do-not-automate-findings-note) instead of a full SDD. Levels 1+ run only for `proceed`, `proceed-with-redesign`, or `partial`.

### Estate sweep

Best-effort and auth-required, like tenant library discovery: never blocks Phase D, do not troubleshoot auth mid-generation, and skip when the prompt forbids `uip` commands. Query only rows matching the step→executor map and filter by PDD Application Inventory and process-name keywords.

| Estate | Discovery |
|---|---|
| Deployed RPA processes | `uip or processes list --all-folders --output json` |
| Tenant RPA libraries | Step 2.5 tenant library discovery (RPA scopes only) |
| IS connectors / live connections | `uip is connectors list --output json` · `uip is connections list --output json` |
| Deployed Agents | `uip agent list --output json` |
| Maestro processes | `uip maestro flow processes list --output json` · `uip maestro bpmn processes list --output json` · `uip maestro case processes list --output json` |
| IXP projects / models | `uip ixp projects list --output json` — newer CLIs only; on `unknown command` apply the drift rule below or user-named estate |
| Deployed Solutions | `uip solution deploy list --output json` |
| Data Fabric entities | `uip df entities list --output json` |
| API Workflows | No dedicated listing verb — check `uip or processes list` output, else user-named estate |
| Coded Apps, Coded Functions | No CLI listing — user-named estate only; ask when signals suggest one exists |

When a listed verb or flag is rejected with `unknown command` / `unknown option`, discover the surface with `uip <group> --help`, or use the platform API (Orchestrator OData for `or` resources) with the existing authenticated context; never invent a verb. Record substitutions in Recommended Scope reasoning.

**One round, then stop:** issue the whole sweep as one batch of `list` calls, read results once, and decide. Do not rerun with new filters, alternate terms, or client-side post-processing after zero rows or an empty `Data` array; that is final (`no reuse candidates`). Do not retry a rejected flag with a guessed alternative: apply the drift rule once, and if it fails, record the estate unknown and proceed. Every extra round costs a full reasoning cycle in the same turn that must author §1–§18.

Record every covering hit in Recommended Scope reasoning (Level 0 outcome) and the consuming template (§Packages, Integrated Components, or connector rows). A covering hit changes those steps to reuse and outcome `partial` or a downscoped to-be.

### Do-not-automate findings note

Confirm with the user, then write `<PROCESS_NAME_KEBAB>-findings.md` instead of an SDD and end Phase D:

1. `# <PROCESS_NAME> — Suitability Findings` + generation date
2. `## Outcome` — `do-not-automate`, with each failed gate item (1–7) and one evidence line
3. `## Recommended Alternative` — native capability, process fix, or estate reuse and owner
4. `## Revisit Triggers` — volume growth, stable API, process stabilization, etc.
5. `## Action Required — SME Review Items` — only if questions remain

The note has NO `## Planner Handoff` header and NO `planner-handoff:v1` marker; it is terminal, never routes to Lane A, and needs no Status field. `partial` produces an SDD, not a findings note — dropped steps are recorded in the SDD's Recommended Scope reasoning.

## Level 1 — Primary Scope Selection

Match the need profile, not keywords. Weigh determinism, structure, stable API/API-first, volume and cost, risk/reversibility/confidence, auditability/compliance, and coordination shape. Genuine judgment/reasoning alone justifies **Agent**; a deterministic process with one judgment step is a deterministic primary plus Agent component. Agentic execution costs more and is less predictable, so estimate per model/tenant at volume. The usual design is hybrid: AI decides, governed RPA/API execute, Maestro orchestrates only when needed, and HITL gates risky/low-confidence steps.

| Need | Product/component |
|---|---|
| Judgment, reasoning, dynamic tool planning | Agents |
| Fixed generative step in known path | LLM activity in host workflow, not Agent |
| Fixed document classification/extraction | IXP / Document Understanding; standalone IXP only when extraction is the entire deliverable |
| User-facing screen deliverable | Coded Apps |
| Headless system integration, no UI/bot | API Workflows |
| Case lifecycle, SLA, approvals, possibly ad-hoc tasks | Case Management |
| Formal control flow without case | Maestro BPMN |
| Plain multi-automation pipeline | Maestro Flow |
| One human approval in one process | Long-running RPA + Action Center |
| Headless deterministic compute, no UI/orchestration | Coded Function |
| UI or machine-local work (Excel/Office, files/folders, on-prem DB, desktop email, terminal/mainframe) | RPA |
| Reusable compile-time component | RPA Library, additive |
| Regression validation | Test Automation, additive and rarely primary |

Never route on a contradictory keyword: “AI” over rules is RPA, and a dashboard that is really a scheduled report is not necessarily Coded Apps. If unclear, ask the user (see Presenting the Recommendation).

### Decision table

Input is the step→executor map, not raw keywords. Type every step with [Per-task component placement](#per-task-component-placement-the-to-be-per-step), then apply the **absorption fold**; mixed capabilities are not cross-product orchestration.

| Host | Absorbs in-process |
|---|---|
| RPA | DU/IXP extraction, LLM activity, IS connector/direct HTTP (including published API Workflow), synchronous child process/agent calls whose result is consumed in-run, ONE in-flight approval (long-running + Action Center) |
| API Workflow | Connector/HTTP calls and nested synchronous API Workflow calls |
| Coded App | Backend calls to published API Workflows/processes/agents |
| Agent | Runtime-planned tools (RPA, API Workflows, Functions, connectors), ONLY under the coordinator exception below |

Absorbed means integrated component, not unbuilt. A consumed IXP model, connector, Library, or API Workflow may still be a separate buildable project ordered before its host.

- One host remains, including same-executor projects separated by queue hand-off: walk rows 1–3 and 7 in priority order; Level 2.5 Part A decides decomposition.
- Two or more peer runtimes, or coordination/state exceeds one host (case stages/SLA, formal gateways/events/parallel branches, or long-running waits across automations): rows 1–3 and 7 are ineligible; choose Case → BPMN → Flow (rows 4–6), and make peers components or Solution projects. A fixed process with judgment is deterministic host + Agent component (absorbed when called synchronously in-run; a peer under Maestro when long-running), never Agent-primary.
- **Coordinator exception:** an open-ended/conversational Agent that plans runtime tools with no fixed process shape is Agent-primary with RPA/API tools (multi-skill Pattern 5). A fixed process containing judgment is not this exception.

Signals that match *below* the primary become candidate additional projects in a Solution (see Solution Signals below).

| Priority | Signal in PDD | Primary |
|---|---|---|
| 1 | AI reasoning, LLM judgment, tool calling, RAG, knowledge retrieval | Agents |
| 2 | Web dashboard, internal tool, Action Center form as deliverable | Coded Apps |
| 3 | System-to-system synchronous API integration, no UI/bots | API Workflows |
| 4 | Case lifecycle, stages, SLA, approval gates, task routing | Case Management |
| 5 | Formal BPMN gateways/events/subprocesses OR explicit BPMN 2.0 request, with no case stages/SLA | Maestro BPMN |
| 6 | Multiple automation types with linear/branching node flow and no formal BPMN | Maestro Flow |
| 7 | UI/desktop/Citrix/mainframe, Excel/Office, files/folders, on-prem DB, desktop email, data processing, reusable component, testing, or one in-flight approval | **RPA** (sub-type at Level 1.5) |
| 8 | Multiple coordinated products or mixed RPA sub-types | **Solution** (composition at Level 1.75) |

Apply the [Constraint Gate](#constraint-gate) to the matched primary before presenting it; replace blocked products with the matrix alternative.

Row 8 is packaging/composition, reached only through [Solution Signals](#solution-signals). Derived components never count toward it. A single component ships as that product, standalone or single-project Solution according to the template decision.

### Maestro disambiguation — BPMN vs Flow vs Case

- Case Management wins for a case moving through stages with SLA/approval gates, escalation, or task routing, even though it compiles to BPMN.
- Maestro BPMN wins for structured, stateful control flow without case/stage/SLA: parallel/inclusive/event-based gateways, boundary events, intermediate message/timer events, subprocesses/call activities, multi-instance loops, or explicit BPMN/swimlane request.
- Maestro Flow is the default plain node graph: linear/single-branch RPA/agent/app/API sequencing with transforms.

Rule: **case + stages + SLA → Case; formal gateways/events/subprocess without case → BPMN; plain pipeline → Flow.** When Flow/BPMN is genuinely close, default to Flow and offer BPMN through `AskUserQuestion` — never force BPMN.

Do not choose Maestro for one RPA Dispatcher→Performer or a single approval: use RPA Process or long-running RPA + Action Center. Mixed capabilities inside one host remain that host, including RPA calling IXP, LLM activity, synchronous API, Agent, or published process.

**Light orchestration stays RPA:** synchronous sequential child calls, one-session completion, state in parent run/queues, and parent retry/REFramework. **Real orchestration uses Maestro:** state outlives a run, event/timer resume, parallel/event branches, per-step visibility/SLA/compensation, multiple human touchpoints, or parent is pure glue between peers.

### Solution Signals

A Solution is the correct primary when any of the following applies, even if a single product would otherwise match at priority 1-6:

- The PDD describes **two or more distinct top-level products** that must coexist (e.g., Flow that calls an API Workflow that is itself a deliverable).
- The PDD mentions **reusable components** that other automations consume (Library) AND a standalone process that uses them.
- The PDD calls out a **dedicated test suite / regression pack** alongside the process being tested (Test Automation + the Process it validates).
- The PDD describes **multiple independent streams** with no single runtime orchestrator (e.g., separate dispatchers feeding separate performers with no Flow tying them together).

When any of the above applies, set the default primary to **Solution** and pre-compose the product list from the matched signals. Otherwise default to the highest single-product match.

**Derived components never escalate scope.** Deliverables named by the requirements set the scope; the part count of the design never does. Solution Signals test what the **PDD names as deliverables** — every scope-shaped decision downstream (single-product vs Solution, template choice, SDD file layout, packaging) follows that answer, never the number of buildable parts the design ends up with. Any supporting component the design introduces (wrapper API Workflow, custom connector, IXP model, Coded Function, Library) inherits its consumer's scope: an integrated-component row in the primary's template plus a build task ordered before its consumer — no solution overview, no per-project SDD, no `SDD scope: solution` flip.

> **Ambiguous dual-product PDDs:** If exactly two products match with similar strength and no Solution signal applies, mark the higher-priority match as the default single-product recommendation and offer Solution (customize) as an alternative in the recommendation screen. Let the user confirm via `AskUserQuestion`.

### Signals per product

#### Agents (Python + agent.json)

Signals: AI reasoning, LLM/GPT/Claude, tool/function calling, RAG/knowledge base/semantic search/vector store, multi-step reasoning/plan-and-execute, natural-language interface, or runtime decisions based on user input. Apply the determinism gate first: explicit-rule decisions are deterministic and route to RPA/API/rule logic, not Agent. Simple summarization/content generation without decisioning/escalation is an LLM activity in RPA/Flow, not standalone Agent.

Required PDD information: framework (LangGraph, LlamaIndex, OpenAI Agents, Simple Function); tools (external APIs, RPA processes, API workflows); memory/RAG sources; evaluation criteria (trajectory, success metrics). Missing any required agent framework/tools/evaluation detail → `AskUserQuestion` (see Gap Handling).

#### Coded Apps (Web)

Signals: dashboard/web interface/portal/internal tool, user form, review/approval screen, Action Center custom form, or web application deliverable. Required: framework (React, Angular, Vue), app type (Web standalone vs. Action), pages/routes/user flows, state-management complexity, and caller (direct user, HITL form, Action Center task). Missing framework/pages/flows → `AskUserQuestion`.

#### API Workflows

Signals: no-UI/no-human system integration; synchronous request-response; SaaS data pull/compose/transform; agent/Flow/HTTP consumption; high throughput; no attended/unattended robots. Required: JSON input schema, JSON output schema, connectors/HTTP endpoints, latency/throughput expectations. Libraries are compile-time reusable; API Workflows are runtime HTTP services.

#### Case Management

Signals: stages/phases, approval gates, SLA, timed/conditional escalation, case as first-class concept, or multi-lane work organized into case stages with SLA/approval (bare BPMN lanes → Maestro BPMN), or tasks that can run in parallel within a lane. Required: stage entry/exit, tasks per stage, SLA rules, escalation rules.

#### Maestro BPMN

Signals:
- Explicit "BPMN", "BPMN 2.0", "process model", "process diagram", or "swimlane process" request
- Parallel work that forks and rejoins (parallel gateway) or multiple simultaneous conditional branches (inclusive gateway)
- A race between events / first-to-arrive routing (event-based gateway)
- Per-activity timeouts, deadlines, or "cancel / compensate this step if it runs too long or errors" (boundary events)
- Waiting for or sending a message / signal between running process instances (intermediate message events)
- Timer waits ("wait N days", scheduled intermediate pauses) that are NOT a case SLA
- Reusable containers (subprocesses) or invoking a separate Maestro / agentic / case process (call activities)
- Processing each item of a collection with sequential or parallel instances (multi-instance loops)
- Long-running, structured control flow — but NO case entity, stages, SLA, or RACI (→ Case), and beyond a simple linear/branching pipeline (→ Flow)

Required: activities/gateways/order; branch/join behavior; start/intermediate/boundary events; variables (name, type, direction); invoked components (RPA, Agent, API Workflow, HITL, connector); retry/timeout; subprocess/call boundaries.

#### Maestro Flow

Signals: multiple automation types, conditional routing, data transformations between steps (filter, map, group-by), schedules, subflows, or Flow/pipeline terminology. Required: node sequence/branches, variables, external systems, trigger (manual, scheduled, event).

#### RPA (sub-type and decomposition decided in rpa-product-guide.md)

When Level 1 selects RPA, load [RPA Product Guide](rpa-product-guide.md) for Library/Test Automation/Process, Level 1.5, Level 2, and Level 2.5 Part A. Do not reproduce those decisions here.

## Level 1.5 — RPA Sub-type Selection

See [RPA Product Guide → Level 1.5](rpa-product-guide.md#level-15--rpa-sub-type-selection). In a Solution with two or more RPA projects, run Level 1.5 once per project.

## Level 1.75 — Solution Composition

Run only when Level 1 = Solution or the user selects Solution (customize). Passes: A products, B quantities, C RPA sub-types.

### Pass A — Select products to include (multi-select)

Before questions, remove products blocked by the [Constraint Gate](#constraint-gate), including user exclusions. Explain matched blocked products and matrix alternatives; when none exists (for example, Coded Apps on Automation Suite), state that and mark `[SME REVIEW]`. Use exactly **two question objects**, each `multiSelect: true` and ≤4 options, in one call; the 8 slots cover 9 candidate products because Maestro Flow/BPMN share one option. Disambiguate that option in Pass A.5.

Invoke exactly like this:

```json
AskUserQuestion({
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
})
```

**Pre-selection rules** — before calling `AskUserQuestion`, mark each option as pre-selected if the corresponding Level 1 signal matched:

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

`AskUserQuestion` options have no pre-selection field (options carry only label / description). Mark the recommendation instead: order recommended options first, append **"(Recommended)"** to their labels, and state the signal-matched set in the question text (e.g., "Signals matched: RPA + Agents — keep or adjust"). The user confirms, adds, or removes. Options with no matching signals get no "(Recommended)" tag — the user adds them explicitly if they disagree.

### Pass A.5 — Disambiguate the Maestro engine (only when "Maestro orchestration" is selected)

If exactly one of Flow/BPMN matched and the user did not override, use it and skip the follow-up. With no BPMN structure, default to Flow. If neither or both matched, ask:

```json
AskUserQuestion({
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
})
```

Mark matched engine labels `(Recommended)`; no pre-selection field exists. Both may be selected (one Flow and one BPMN project). BPMN requires matched structure or explicit user selection; never silently default to BPMN.

### Pass B — Resolve quantities per product

For products that may repeat, especially RPA, use numbered-choice `AskUserQuestion` with signal-derived defaults:

> How many RPA projects does the Solution need?
>
> 1. **1** *(recommended if the PDD describes a single end-to-end RPA flow)*
> 2. **2**
> 3. **3 or more** — you will specify the list in the next step

For `3 or more`, follow up with numbered likely counts plus `Other` for custom. Flow, Case Management, Agents, Coded Apps, and API Workflows default to **1** unless multiple instances are explicit.

### Pass C — Run Level 1.5 per RPA project

Run one `AskUserQuestion` per RPA project for Process / Library / Test Automation; do not batch unless the PDD clearly assigns one sub-type to all.

### Output of Level 1.75

Produce a project list:

| # | Project Name (proposed) | Product | RPA Sub-type | Source Signal |
|---|---|---|---|---|
| 1 | `<NAME>_Flow` | Maestro Flow | — | "orchestrates extraction + reporting" |
| 2 | `<NAME>_Extractor` | RPA | Process | "email ingestion + DU extraction" |
| 3 | `<NAME>_SharedUtils` | RPA | Library | "reusable helpers across projects" |
| 4 | `<NAME>_Regression` | RPA | Test Automation | "weekly regression pack" |
| 5 | `<NAME>_LookupApi` | API Workflows | — | "called as a tool from the Flow" |
| 6 | `<NAME>_ScoreFunction` | Function | — | "deterministic scoring called by the Flow" |

Include all selected products and quantities. Derived Coded Functions, IXP models, and custom connectors are never Pass A options: add one row per step→executor/Level 3 component, before consumers; they get build tasks but no per-project SDD file (see [Template Mapping](#template-mapping)). Present the list in Phase 1 summary.

## Level 2 — Authoring Mode (RPA only)

See [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Apply to every RPA Process, Library, and Test Automation project.

## Level 2.5 — Project Decomposition

| Scope | Action |
|---|---|
| Single non-RPA product/project | One-row list; skip Part A |
| Single RPA Process | Run RPA Part A; Part A list is final; skip Part B |
| Solution | Run Part A for every RPA Process, then Part B merge |

### Part A — RPA decomposition signals

See [RPA Product Guide → Level 2.5 Part A](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals), which contains the 6 signals, Dispatcher/Performer and Dispatcher/DU/Output patterns, and narrower list. Apply it to every RPA Process.

### Part B — Merge into the final project list

Merge Part A results with non-RPA Level 1.75 projects (or Level 1 single product). Produce: (1) pattern per group: Single Project, Master Project (queue-connected), or N/A; (2) unified list, one row per concrete SDD-described project; (3) queue schema preview; (4) cross-product integration notes.

Example unified project list for a Solution (Flow + RPA Library×2 + RPA Test Automation + RPA Process expanded into a Master Project):

| # | Project Name | Product | Sub-type | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|---|---|
| 1 | `<NAME>_Flow` | Maestro Flow | — | Orchestrates extraction and reporting | — | — | — |
| 2 | `<NAME>_Dispatcher` | RPA | Process | Collects emails, dispatches to processing queue | Sequence | — | `<QUEUE_1>` |
| 3 | `<NAME>_Performer` | RPA | Process | Processes each transaction item | REFramework | `<QUEUE_1>` | `<REPORTING_QUEUE>` |
| 4 | `<NAME>_SharedUtils` | RPA | Library | Reusable date/string/mapping helpers used by Performer | — | — | — |
| 5 | `<NAME>_IntegrationLib` | RPA | Library | Salesforce + ServiceNow wrappers used by Performer | — | — | — |
| 6 | `<NAME>_Regression` | RPA | Test Automation | Regression pack validating Performer behavior | — | — | — |

The canonical queue schema is **§12 of the RPA template**, two tables per Master Project group:
- `Queue Definitions`: `Queue Name | Producer Project | Consumer Project | Trigger Type | Max Retries`
- `Queue Item Schema`: one sub-section per queue, `Field Name | Type | Source | Description`

At Part B list only queue names and producer/consumer mapping; fill the full schema in Phase 2. Notes must identify Flow→RPA, Agent→API Workflow, and similar calls.

## Per-task component placement (the to-be, per step)

Apply this table twice: Phase 1 Step 3.5 to create the step→executor map and Phase 2 Steps 3–4 of the [SDD Generation Guide](sdd-generation-guide.md) to populate inventory and integrated components.

| Task type | Best-fit component | Routes to |
|---|---|---|
| **Validate / Transfer**, deterministic | RPA, or IS/API Workflow when stable reachable API exists | `uipath-rpa` / `uipath-platform` / `uipath-api-workflow` |
| Local/network Excel/Office, files/folders, on-prem DB, desktop email | RPA; API Workflow/Function only for cloud-reachable source or robot-hosted Function; desktop/interactive UI stays RPA | `uipath-rpa` |
| **Collect** semi-structured documents | IXP / Document Understanding, standalone or activity | `uipath-ixp` |
| **Decide / classify**, judgment | AI Agent, or Business Rules/DMN for threshold/eligibility | `uipath-agents` / `uipath-rules` |
| **Create / author / summarize** free-form | Agent; no-decision generation is host LLM activity | `uipath-agents` (standalone only) |
| **Review / Escalate / sign-off** | Host-aware HITL: Flow skill; coded Agent escalation; BPMN userTask; Case inline `action`; RPA Action Center/long-running | `uipath-human-in-the-loop` for Flow hosts only |
| **Wait / approve inside ONE process** | Long-running RPA + Action Center; scheduled/queue run is RPA + Orchestrator trigger, never Maestro | `uipath-rpa` (trigger → `uipath-platform`) |
| **Sequence / coordinate MULTIPLE automations**, real orchestration | Maestro Flow/BPMN/Case; synchronous in-run calls are absorbed | `uipath-maestro-flow` / `-bpmn` / `-case` |
| **Transform / compute**, atomic deterministic custom logic (parsing, scoring, custom-auth API call, ERP query via IS connection) | Host-native first; Coded Function only when justified; TypeScript/JavaScript/Python typed input→code→typed output; serverless or robot-hosted | `uipath-functions` |
| **Aggregate / persist shared data** | Data Fabric entities are persistence; logic runs in API Workflow/Function/RPA | executor above + `uipath-platform` |

Rules:
1. DU/IXP extracts semi-structured documents, not free-form authoring; route document-heavy `Collect` to `uipath-ixp`.
2. Business Rules/DMN is its own BusinessRules project (`uipath-rules`), deployed and called by Maestro BPMN business rule task, Case `business-rule` task, or RPA. Each deployed deterministic decision table is a separate project/task; Agent reasoning remains in Agent.
3. Data Fabric/Data Service is storage, never executor; computation is placed on API Workflow/Function/RPA.
4. Coded Functions are components, not primaries. Function-only requests defer as one project to `uipath-functions`, not a plan.
5. Prefer stable reachable APIs/connectors over RPA for deterministic Validate/Transfer. On-prem HTTP(S) may use **Automation Relay** (Integration Service + API Workflows only; Unified Standard/Enterprise or Flex Standard/Advanced licensing plus on-network Relay client): offer and confirm; unconfirmed → RPA + `[SME REVIEW]`. Non-HTTP local interfaces are robot-only → RPA.
6. Default host-native: RPA HTTP/Invoke Code, coded Agent Python, API Workflow script + HTTP, Maestro node transforms. Create Coded Function/API Workflow/custom connector only if (a) host cannot express/call it (low-code IS-only surface, custom auth the host cannot do), (b) 2+ consumers share it, or (c) independent versioning/scaling/ownership is needed. One consumer plus host capability means no new project/task. Pure headless deterministic compute with no UI/activities/attended context prefers Coded Function over RPA.

## Level 3 — Capability Add-ons

Add-ons belong to the primary and are flagged in its template; Lane A derives and routes tasks from these flags.

### HITL (Human-in-the-Loop)

Adds approval, exception escalation, and write-back validation. **Only Flow hosts route to `uipath-human-in-the-loop`**; in a single-project request the Flow specialist authors the inline node. Coded Agents use `uipath-agents` escalation, BPMN inline userTask via `uipath-maestro-bpmn`, Case inline `action` via `uipath-maestro-case`, and RPA Action Center/long-running.

Signals: approval before; human review; low-confidence escalation; validation before write-back; missing-data completion. Add `HITL Touchpoints` to the host section. Flow gets an “Add HITL node per §X” task; other hosts do not create a HITL-skill task.

### Integration Service

Adds connector activities to RPA, Flow, Case, or Agents. IS is the standard integration surface for API Workflows, Maestro Flow/BPMN/Case, and Agents; RPA may use HTTP Request when no connector exists.

Signals include third-party SaaS (Salesforce, Jira, ServiceNow, Slack, HubSpot, Workday, Zendesk, etc.) and create/post/read operations.

Before assuming a connector, run both as appropriate (auth-required, best-effort):

```bash
uip is connectors list --output json                          # full catalog
uip is connectors list --filter "<KEYWORD>" --output json     # narrow by system name
```

Existing connector → reuse; flag `Access Method = Integration Service — <CONNECTOR_SLUG>` and create `Configure <X> connector` task routed to `uipath-platform`. No connector and HTTP-capable consumer — API Workflows (Unified HTTP Request activity), RPA (HTTP Request activity), coded Agents (Python HTTP client) → direct HTTP, flag `Access Method = Direct HTTP`; do not create connector/API Workflow for one host-capable consumer. IS-only consumer (Maestro Flow / BPMN / Case connector nodes, low-code Agent tools) → custom connector (`Access Method = Custom connector — <CONNECTOR_SLUG>`, `uipath-connector-builder`) or small API Workflow; prefer custom connector for 2+ projects or IS-level governance. Unverified connector is `[SME REVIEW]`. Wrapper remains integrated and does not change scope.

### API Workflow (as integrated component)

Applies when a non-primary API Workflow is called by Flow, BPMN, Case, Agent, or another API Workflow. It requires structured JSON input/output, no UI, and the extraction test: host cannot call natively, 2+ consumers, or independent versioning/scaling/ownership. Otherwise use `Access Method = Direct HTTP` and create no project/task. List calls in the host inventory (Flow nodes, BPMN `serviceTask`, Agent tools, Case tasks); Lane A creates a `uipath-api-workflow` task before the consumer. Scope is unchanged.

### Reusability & shared assets

Reuse before build; new shared assets are projects built before consumers:

- RPA Library: shared workflows; discover deployed libraries with [Tenant Library Search](tenant-library-search-guide.md) (Phase 1 Step 2.5), reference in §Packages; new Library → `uipath-rpa`.
- Custom connector: build via `uipath-connector-builder` when catalog lacks one.
- Marketplace/org-repo and new reusable components: list in **Reusable Components**.
- Assets used by 2+ projects (Library, connector, IS connection, asset, queue) live at parent-folder/solution level, built once and referenced, never duplicated.

Flag every reused/new shared asset; planner emits each new build task before consumers.

## Template Mapping

### Single-product scope

| Primary Product | Template |
|---|---|
| RPA Process, Library, Test Automation | `../assets/templates/rpa-sdd-template.md` |
| Maestro Flow | `../assets/templates/flow-sdd-template.md` |
| Maestro BPMN | `../assets/templates/bpmn-sdd-template.md` |
| Case Management | `../assets/templates/case/case-sdd-template.md` |
| Agents | `../assets/templates/agent-sdd-template.md` |
| Coded Apps | `../assets/templates/coded-app-sdd-template.md` |
| API Workflows | `../assets/templates/api-workflow-sdd-template.md` |

**Coded Functions are never Level 1 primary and have no standalone template.** Use the host `### Coded Functions` table; in a Solution, list the row and route the task to `uipath-functions`, but create NO per-project SDD. Function-only requests are Lane B single-skill deferrals to `uipath-functions`.

### Solution scope (Level 1 = Solution or user picked Solution (customize))

Create one solution overview plus one per-project SDD for each Level 2.5 unified project, using kebab-case names:

| Output file | Template | How many |
|---|---|---|
| `<SOLUTION_NAME_KEBAB>-solution-sdd.md` | Solution overview | Exactly 1 |
| `<PROJECT_NAME_KEBAB>-sdd.md` | Project product template | One per unified project |

For RPA, use one template per RPA group; Master Project sub-projects share one RPA SDD (§10/§11), unrelated RPA projects get separate files. Component rows (Coded Function, IXP model, custom connector) get no SDD: use host tables plus solution Project Inventory; Lane A orders tasks before consumers.

### Solution overview SDD structure

1. Solution Overview (objective, business context)
2. Planner Handoff with `Project SDD role: root`, `Solution ID: <SOLUTION_NAME_KEBAB>`, `Solution root SDD: <its own filename>`, canonical `Tasks file: <SOLUTION_NAME_KEBAB>-tasks.md` (the ONE tasks file named by every child), and cross-project ordering. Keep it within the first ~50 lines; no task list.
3. Project Inventory — the unified project list from Level 2.5 Part B
4. Cross-Project Data Flow — how projects call each other (Flow → RPA, Agent tool → API Workflow, RPA Performer → Library)
5. Shared Assets & Queues — assets, credentials, and queues referenced by more than one project
6. Per-Project SDD Index — filename + one-line scope per project

## Gap Handling for Agent / Coded App

When required Agent/Coded App information is missing:

1. Use numbered-choice `AskUserQuestion`:

> The PDD describes <PRODUCT>-specific capabilities, but requirements are missing for: <LIST_GAPS>.
>
> 1. **Proceed with <PRODUCT>** *(recommended)* — I will ask follow-up questions to fill the gaps
> 2. **Use a different product** — I will ask which product to use instead

2. Option 1 → ask batched product-specific gap questions, with defaults; maximum 4 question objects per call, so split calls when more than 4 gaps remain.
3. Option 2 → ask:

> Which product should I use instead?
>
> 1. **RPA Process** — standard UI/data automation
> 2. **Maestro Flow** — orchestrate multiple automations
> 3. **Case Management** — staged lifecycle with SLA
> 4. **Stop** — do not generate an SDD

4. Re-run selection with fallback primary. Never auto-fallback.

## Presenting the Recommendation

Put the recommended scope first, then single-product alternatives and **Solution (customize)**. A single-product Level 1 result is the recommendation with RPA sub-type; a Solution result is the pre-composed Level 1.75 list.

### Summary block

Emit:

```markdown
## Recommended Scope
**Recommendation:** <SINGLE_PRODUCT | SOLUTION(<PRODUCT_1>, <PRODUCT_2>, ...)>
**Delivery model:** <cloud | automation-suite <version-if-known> | standalone | unspecified — assumed cloud [SME REVIEW]>
**Blocked by platform:** <PRODUCT → ALTERNATIVE_APPLIED (matrix | user exclusion), ... | none>
**Need profile:** <ONE_LINE_CORE_NEED_AND_TARGET_KPI — from sdd-generation-guide.md Step 3.5>
**Reasoning:**
- <NEED_FACTOR — determinism / input structure / integration surface / coordination shape / volume / risk / trigger> → <PRODUCT>
- ...
**Alternatives considered:**
- <REJECTED_OPTION> — rejected because <REASON>
- ...

## Project List
<UNIFIED_PROJECT_LIST_FROM_LEVEL_2.5_PART_B — include Product, Sub-type, Role, Framework, Input/Output Queue columns>

## Queue Architecture (RPA Master Project rows only)
<QUEUE_TABLE_OR_N/A>
**Decomposition signals matched:** <LIST_MATCHED_SIGNALS_PER_RPA_PROCESS_PROJECT_OR_N/A>
```

The Phase 1 block is conversational, but `Recommendation:`, `Delivery model:`, and `Blocked by platform:` must also survive into every SDD's `## Recommended Scope`, between `## Decisions Made` and `## Action Required`, in both execution modes (Phase 3 Step 2 item 3). Autonomous mode therefore retains the Constraint Gate outcome in the SDD.

### Confirmation question

Immediately after the summary, confirm with numbered `AskUserQuestion`; item 1 is always recommended:

> I recommend the following scope for this SDD. Which should I use?
>
> 1. **<RECOMMENDED_SCOPE>** *(recommended)* — <ONE_LINE_REASON>
> 2. **<STRONGEST_SINGLE_PRODUCT_ALTERNATIVE>** — <ONE_LINE_REASON_OR_TRADEOFF>
> 3. **<SECOND_SINGLE_PRODUCT_ALTERNATIVE_OR_OMIT_IF_NONE>** — <ONE_LINE_REASON>
> 4. **Solution (customize)** — I will ask you to check every product the Solution should include

Include Solution (customize) even when Solution is already recommended.

### Customize branch

If selected: (1) Level 1.75 Pass A paired multi-select, pre-checking default/signal products; (2) Pass B quantities; (3) Pass C RPA sub-types; (4) Level 2.5 unified list; (5) re-emit summary and confirmation. Customized composition replaces item 1, still recommended; allow at most 3 revisions, then proceed with latest and tag disagreements `[SME REVIEW]`.

If the user disagrees with a single-product recommendation, rerun Level 1 (and Level 1.5 for RPA) with the preference forced primary, then re-present.