# Product Selection Guide

Select scope from PDD signals across all 8 UiPath products and multi-project Solutions. **Solution is packaging, not a runtime tool**; Integration Service, Action Center, IXP, and Libraries are capabilities/components, not automatic primaries.

## How selection works — four layers

1. **Decompose** the process in Phase 1, including the [need profile](sdd-generation-guide.md#step-35-synthesize-the-need) and per-step interface, determinism, state, human interaction, volume, risk, reuse, runtime, and existing-estate factors.
2. Apply [Per-task component placement](#per-task-component-placement-the-to-be-per-step) to create the **step→executor map**.
3. Select the coordination/state host from the folded map. A host absorbs in-process capabilities; use Maestro Flow / BPMN / Case only when peer runtimes or coordination/state exceed one host.
4. Choose packaging last: standalone package or Solution (`.uipx`) through Solution Signals / Level 1.75 and the Constraint Gate. A single component does not need a Solution wrapper by default.

Layers 1–2 run in Phase 1 Step 3.5. Level 1 consumes the step→executor map, never raw whole-process keywords. Level 1.75 and template packaging are layer 4.

## Levels and canonical homes

| Level | Decision | Scope | Canonical home |
|---|---|---|---|
| **0. Suitability** | Automate / redesign / reuse / do not automate | All PDDs | This file |
| **1. Primary scope** | Single product or Solution | All PDDs | This file |
| **1.5. RPA sub-type** | Process, Library, or Test Automation | RPA selected or in a Solution | [RPA Product Guide](rpa-product-guide.md#level-15--rpa-sub-type-selection) |
| **1.75. Solution composition** | Products and project quantities | Level 1 = Solution | This file |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Each RPA project | [RPA Product Guide](rpa-product-guide.md#level-2--authoring-mode) |
| **2.5 Part A** | Single vs Master Project | Each RPA Process | [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) |
| **2.5 Part B** | Unified project list, roles, frameworks, queues | All scopes | This file |
| **3. Capabilities** | HITL, Integration Service, API Workflow components | All products | This file |

## Constraint Gate

The delivery model from Phase 1 Step 0 and user product exclusions filter candidates **before** each recommendation. Run the gate at Level 1, Level 1.75 Pass A, and Level 3.

1. Look up every candidate in [platform-availability-guide.md](platform-availability-guide.md) under the customer's delivery-model column.
2. **Not available → BLOCK.** Remove it from recommendations and Level 1.75 options; recommend the matrix's documented alternative. Record the block in `Decisions Made` row 1 and the `Blocked by platform:` line. Emit row 1 even when nothing is blocked: `<delivery model>; no products blocked`.
3. **Partial / uncertain → WARN.** Keep the product, name the limitation or uncertainty, and apply the verification rule in [platform-availability-guide.md](platform-availability-guide.md) before finalizing the SDD.
4. **User exclusions are blocks.** Never re-offer an excluded product. Record the exclusion and reason in the Recommended Scope summary.
5. **Never silently substitute.** Present the alternative and architectural consequence in the summary.

`unspecified` / user-selected “Not sure” gates nothing: assume Automation Cloud and carry an `[SME REVIEW]` row stating the assumption and affected recommendations for Automation Suite or standalone.

## Level 0 — Suitability Gate

Decide whether to automate before choosing a product. Record the result in Recommended Scope reasoning:

1. **Native capability:** use target-system configuration, workflow rules, scheduled reports, or webhooks instead of automation.
2. **Existing estate:** reuse deployed processes, API Workflows, connectors, libraries, models, or Solutions; run the [Estate sweep](#estate-sweep).
3. **Process stability:** defer or mark `[SME REVIEW]` when the process, UI, or rules are changing.
4. **Redesign first:** remove steps that only work around manual limitations; follow PDD Analysis Guide → As-Is and To-Be.
5. **Access feasibility:** verify licenses, API access, credentials, and environment access.
6. **Economics:** compare volume × time saved with build, run, and maintenance cost; downscope or recommend against thin cases.
7. **Residual human work:** assess whether remaining human work dominates the benefit.

Outcomes: `proceed` (default), `proceed-with-redesign`, `partial`, or `do-not-automate`. Run Levels 1+ only for the first three. For `do-not-automate`, recommend the native capability or process fix, confirm with the user, then end Phase D with the [findings note](#do-not-automate-findings-note), not a full SDD. `partial` produces an SDD; record dropped steps in its Recommended Scope reasoning.

### Estate sweep

Run best-effort, auth-required discovery under the same rules as tenant library discovery. Never block Phase D, troubleshoot authentication mid-generation, or run when the prompt forbids `uip` commands. Query only products in the step→executor map and filter by PDD Application Inventory and process-name keywords.

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

When a listed verb returns `unknown command` / `unknown option`, discover the surface with `uip <group> --help`, or use the platform API (Orchestrator OData for `or` resources) with the existing authenticated context. Never invent a verb. Record substitutions in Recommended Scope reasoning. Run one batch of `list` calls, read results once, and decide. Do not rerun with new filters, keyword permutations, or client-side post-processing after zero rows or an empty `Data` array; treat it as `no reuse candidates`. Do not retry a rejected flag with a guessed alternative; apply the drift rule once, then record the estate unknown and proceed. Every extra sweep round costs a reasoning cycle in the same turn that must author §1–§18.

Record every covering hit as a reuse candidate in Recommended Scope reasoning (Level 0 outcome line) and the consuming template (`§Packages`, Integrated Components, or connector rows). A covering hit changes those steps to reuse and the outcome to `partial` or a downscoped to-be.

### Do-not-automate findings note

Confirm with the user, then write `<PROCESS_NAME_KEBAB>-findings.md` and end Phase D. Include:

1. `# <PROCESS_NAME> — Suitability Findings` + generation date
2. `## Outcome` — `do-not-automate` and one evidence line for each failed gate item (1–7)
3. `## Recommended Alternative` — native capability, process fix, or estate reuse and owner
4. `## Revisit Triggers` — changes such as volume growth, a stable API, or process stabilization
5. `## Action Required — SME Review Items` — only if questions remain

Do not include `## Planner Handoff` or `planner-handoff:v1`. This terminal note never routes to Lane A and needs no Status field.

## Level 1 — Primary Scope Selection

Match the underlying need, not literal keywords. Weigh determinism, input structure, stable API availability, volume/cost, risk/reversibility/confidence, auditability/compliance, and coordination shape. Agentic execution is costlier and less predictable at volume than deterministic execution. Genuine judgment/reasoning is required for an **Agent**. The common design is hybrid: AI decides, deterministic RPA/API executes governed tools, Maestro orchestrates only when required, and HITL gates risky or low-confidence work. A mostly deterministic process with one judgment step is deterministic-primary plus an Agent component, not Agent-primary.

### Product priority and primary signals

1. Judgment not expressible as fixed rules or dynamic tool planning → **Agents**.
2. User-facing screen/deliverable → **Coded Apps**.
3. Headless system-to-system integration with no UI or bot → **API Workflows**.
4. Case lifecycle with stages, SLA, approvals, escalation, or task routing → **Case Management**.
5. Formal BPMN control flow without case stages/SLA → **Maestro BPMN**.
6. Plain multi-automation pipeline → **Maestro Flow**.
7. UI or machine-local work; Excel/Office, files/folders, on-prem databases, desktop email, terminal/mainframe → **RPA**; reusable compile-time component → RPA Library; regression validation → Test Automation.
8. Multiple coordinated top-level products or mixed RPA sub-types → **Solution**, but only through [Solution Signals](#solution-signals).

Additional distinctions:

- A fixed generative step follows a known path → LLM activity in the host, not Agent.
- Fixed document classification/extraction → IXP / Document Understanding component; standalone IXP only when extraction is the entire deliverable.
- A single human approval in one process → long-running RPA + Action Center, not Maestro or a HITL project.
- Headless deterministic compute without UI or orchestration → Coded Function component.
- “AI”, “smart”, “automatic”, or “dashboard” do not override the need; deterministic rules are not an Agent and a scheduled report is not necessarily a Coded App.

Apply the [Constraint Gate](#constraint-gate) to the matched primary before presenting it.

### Step-map folding and absorption

Type every step with [Per-task component placement](#per-task-component-placement-the-to-be-per-step), then fold the map. Mixed capabilities are not automatically cross-product orchestration.

A capability is absorbed when the host invokes it in-process and consumes the result in the same run:

| Host | Absorbs |
|---|---|
| RPA | DU/IXP model, LLM activity, IS connector/direct HTTP, published API Workflow/process/agent synchronous child call, ONE in-flight approval via long-running + Action Center |
| API Workflow | Connector/HTTP call and nested synchronous API Workflow |
| Coded App | Backend calls to published API Workflows/processes/agents |
| Agent | Runtime-planned tools, including RPA, API Workflows, Functions, and connectors, only under the coordinator exception |

Absorption makes the capability an integrated component, not “not built”: a consumed model, connector, Library, or API Workflow may still be a buildable project ordered before its host.

- One host remains after absorption; same-executor queue hand-offs count as one host → consider rows 1–3 and 7 in priority order. Level 2.5 decides decomposition.
- Two or more independently deployed peer runtimes remain, or coordination/state exceeds one host → rows 1–3 and 7 are not primary candidates; choose Case → BPMN → Flow and make peers integrated components or Solution projects. A fixed process with judgment is deterministic host + Agent component, never Agent-primary.
- **Coordinator exception:** an open-ended/conversational Agent that plans runtime tool calls with no fixed process shape is Agent-primary, with RPA/API Workflows as tools. A fixed process containing judgment is not this exception.

### Maestro disambiguation — BPMN vs Flow vs Case

- **Case** wins for a case entity moving through stages with SLA, approvals, escalation, or task routing, even though it compiles to BPMN.
- **BPMN** is for structured long-running control flow without case/stage/SLA: parallel/inclusive/event-based gateways, boundary events, intermediate message/timer events, subprocesses/call activities, multi-instance loops, or explicit BPMN 2.0/swimlane requests.
- **Flow** is the default linear/single-branch node graph across RPA, agents, apps, and APIs when no BPMN structure is required.

Do not over-orchestrate. Use Maestro only when state outlives a run, branches are parallel/event-driven, per-step visibility/SLA/compensation is required, there are multiple human touchpoints, or a parent is pure glue between peers. A Dispatcher→Performer or synchronous RPA child call remains RPA. When Flow vs BPMN is close, default to Flow and offer BPMN with `AskUserQuestion`.

### Solution Signals

Use Solution when the PDD names:

- two or more distinct top-level products that must coexist;
- reusable components consumed by a standalone process;
- a dedicated regression/test suite alongside the process it validates; or
- multiple independent streams without one runtime orchestrator.

Otherwise use the highest single-product match. Derived components never escalate scope: supporting API Workflows, connectors, IXP models, Functions, or Libraries inherit the consumer's scope, appear as integrated-component rows and ordered build tasks, and do not create a solution overview, per-project SDD, or `SDD scope: solution`.

If exactly two products match similarly and no Solution Signal applies, recommend the higher-priority single product and offer Solution (customize) through `AskUserQuestion`.

### Product-specific signals and required information

#### Agents

Signals: AI/LLM/GPT/Claude reasoning, tool/function calling, RAG/knowledge base/semantic search/vector store, multi-step plan-and-execute, natural-language interface, or runtime decisions based on user input. Confirm non-deterministic judgment; rule-expressible decisions are RPA/API/rules. Simple summarization or generation without decisioning/escalation is an LLM activity in the host.

Required: framework preference (LangGraph, LlamaIndex, OpenAI Agents, Simple Function), tools, memory/RAG sources, and evaluation criteria (trajectory, success metrics). Missing these when Agent signals exist → use `AskUserQuestion` under [Gap Handling](#gap-handling-for-agent--coded-app).

#### Coded Apps

Signals: dashboard, web interface/portal/internal tool, user form, review screen, approval UI, Action Center custom form, or web application deliverable. Required: framework (React, Angular, Vue), app type (Web standalone vs. Action for automation-triggered), pages/routes/user flows, state complexity, and caller. Missing framework/pages/flows → `AskUserQuestion`.

#### API Workflows

Signals: headless system integration, synchronous request-response, SaaS data composition/transformation, HTTP consumption by agents/Flows/external systems, or high throughput without robots. Required: JSON input schema, JSON output schema, connectors/endpoints, latency, and throughput. Libraries are compile-time NuGet components; API Workflows are runtime HTTP services.

#### Case Management

Signals: case, stages/phases, approval gates, SLA, escalation, or parallel tasks within a lane. Required: stage entry/exit, tasks per stage, SLA rules, and escalation rules.

#### Maestro BPMN

Signals: BPMN/BPMN 2.0/process diagram/swimlane request; parallel or inclusive gateways; event-based races; boundary timeout/error/cancel/compensation; intermediate message/signal/timer events; subprocesses/call activities; multi-instance loops; or structured long-running flow beyond Flow, without case/stages/SLA. Required: control-flow map, branch/join behavior, events, variables, components, retry/timeout policy, and subprocess/call boundaries.

#### Maestro Flow

Signals: multiple automation types, conditional routing, data transforms, scheduled triggers, subflows, or Flow/pipeline language. Required: node sequence/branches, variables, external systems, and trigger type (manual, scheduled, event).

#### RPA

When RPA is selected, load [RPA Product Guide](rpa-product-guide.md) for sub-type, authoring mode, and decomposition. Do not reproduce those decisions here.

## Level 1.5 — RPA Sub-type

See [RPA Product Guide → Level 1.5](rpa-product-guide.md#level-15--rpa-sub-type-selection). In a Solution with multiple RPA projects, run it once per project.

## Level 1.75 — Solution Composition

Run only when Level 1 = Solution or the user chooses Solution (customize). Produce the concrete project list.

### Pass A — Products

Apply the [Constraint Gate](#constraint-gate) before asking. Remove blocked products; state matched blocked signals and the availability-matrix alternative, or state that no alternative exists and mark `[SME REVIEW]`. Use one `AskUserQuestion` call with exactly two question objects, both `multiSelect: true`, each with ≤4 options. The eight slots cover nine candidates because Maestro Flow/BPMN share one option:

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

Mark signal-matched options first, append `(Recommended)`, and state the matched set in the question text; there is no pre-selection field. Pre-select conceptually: RPA for UI/transactional/queue signals; Maestro for Flow/BPMN signals; Case for stages/SLA; Agents for reasoning/tools; Coded Apps for custom UI; API Workflows for API signals or callable integration; RPA Library for shared helpers/NuGet; Test Automation for regression/assertions. Library/Test signals also pre-select RPA. Users may add/remove options.

### Pass A.5 — Maestro engine

Only when Maestro orchestration is selected. If exactly one engine signal matched and the user did not override, use it; with no BPMN structure, default to Flow. If neither or both matched, ask:

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

Append `(Recommended)` to matched labels. Both may be selected; create one project of each. Never silently choose BPMN.

### Pass B — Quantities

Ask quantities for products that may repeat, especially RPA, using numbered choices:

> How many RPA projects does the Solution need?
>
> 1. **1** *(recommended if the PDD describes a single end-to-end RPA flow)*
> 2. **2**
> 3. **3 or more** — you will specify the list in the next step

For `3 or more`, ask a follow-up with likely counts plus `Other`. Flow, Case Management, Agents, Coded Apps, and API Workflows default to 1 unless multiple instances are explicit.

### Pass C — RPA sub-types

Run Level 1.5 once per RPA project; ask separately unless the PDD clearly assigns the same subtype to all.

### Output

Create a project list with `# | Project Name (proposed) | Product | RPA Sub-type | Source Signal`; include derived Coded Functions, IXP models, and custom connectors from the step map/Level 3, ordered before consumers. They are never Pass A options, have build tasks, and no per-project SDD file.

## Level 2 — Authoring Mode

See [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Apply to every RPA project.

## Level 2.5 — Project Decomposition

| Scope | Action |
|---|---|
| One non-RPA project | Produce one row; skip Part A |
| One RPA Process | Run [RPA decomposition signals](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals); its narrower list is final |
| Solution | Run Part A for every RPA Process, then Part B merge |

### Part A

See [RPA Product Guide → Level 2.5 Part A](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals), including six signals and Dispatcher/Performer and Dispatcher/DU/Output patterns.

### Part B — Merge into the final project list

Merge all projects and produce:

1. Pattern: Single Project, Master Project (queue-connected), or N/A.
2. One unified row per concrete project with product, subtype, role, framework, and queues.
3. Queue schema using canonical §12 RPA-template tables: `Queue Definitions` columns `Queue Name | Producer Project | Consumer Project | Trigger Type | Max Retries`; and `Queue Item Schema` per queue with `Field Name | Type | Source | Description`. At Part B list queue names and producer/consumer only; fill the full schema in Phase 2.
4. Cross-product integration notes: Flow→RPA, Agent→API Workflow, and equivalent calls.

## Per-task component placement (the to-be, per step)

Apply this table at Phase 1 Step 3.5 and again at Phase 2 Steps 3–4 of the [SDD Generation Guide](sdd-generation-guide.md) for the template inventory and integrated-component flags.

| Task type | Best-fit component | Routes to |
|---|---|---|
| Validate / Transfer, deterministic | RPA, or IS/API Workflow when a stable reachable API exists | `uipath-rpa` / `uipath-platform` / `uipath-api-workflow` |
| Local/network Excel/Office, files/folders, on-prem DB, desktop email | RPA; cloud API/Function only for cloud-reachable sources | `uipath-rpa` |
| Collect semi-structured documents | IXP / Document Understanding, standalone only when extraction is the deliverable | `uipath-ixp` |
| Decide/classify judgment | Agent; Business Rules/DMN for thresholds/eligibility | `uipath-agents`; DMN inside Maestro or Agent |
| Free-form create/author/summarize | Agent; simple non-decisioning generation is host LLM activity | `uipath-agents` for standalone Agent |
| Review/escalate/sign-off/exception | Host-aware HITL: Flow skill; coded-Agent escalation; BPMN userTask; Case `action`; RPA Action Center/long-running | `uipath-human-in-the-loop` for Flow hosts |
| Wait/approve inside one process | Long-running RPA + Action Center; ordinary triggers remain RPA + Orchestrator trigger | `uipath-rpa` (trigger config → `uipath-platform`) |
| Real multi-automation coordination | Maestro Flow/BPMN/Case; synchronous in-run calls are absorbed | `uipath-maestro-flow` / `-bpmn` / `-case` |
| Atomic deterministic compute | Host-native code first; Coded Function when extraction is justified; robot-hosted Functions can reach on-prem | `uipath-functions` |
| Aggregate/persist shared data | Data Fabric entities are storage; executor performs computation | executor + `uipath-platform` |

Rules:

1. DU/IXP is extraction, not free-form authoring.
2. Business Rules/DMN is not a standalone project; put tables in the host's rules section.
3. Data Fabric/Data Service is storage, never an executor.
4. Coded Functions are components, not primaries; a Function-only request is a single-project deferral to `uipath-functions`, not a plan.
5. Prefer stable reachable APIs/connectors over RPA. Automation Cloud can reach on-prem HTTP(S) through **Automation Relay** (Integration Service + API Workflows only; requires Unified Standard/Enterprise or Flex Standard/Advanced licensing and an on-network Relay client): offer and confirm; unconfirmed → RPA + `[SME REVIEW]`. Non-HTTP local interfaces remain RPA.
6. Run the extraction test before creating a deployed Function/API Workflow/custom connector. Create one only if (a) the host cannot express the logic/call, (b) 2+ consumers share it, or (c) it needs independent versioning, scaling, or ownership. Otherwise keep it host-native with no new project/task. Conversely, headless deterministic compute with no UI/activities/attended context prefers a Coded Function over RPA.

## Level 3 — Capability Add-ons

Capabilities are added to the primary and flagged in its template; Lane A derives tasks and routes them accordingly.

### HITL

Signals: approval before, human review, low-confidence escalation, validation before write-back, or filling missing data. Add `HITL Touchpoints` to the host section. Only Flow hosts route a planner-generated multi-project task to `uipath-human-in-the-loop`; in single-project Flow requests the specialist authors the inline node. Coded Agents own escalation through `uipath-agents`; BPMN uses inline `userTask` via `uipath-maestro-bpmn`; Case uses inline `action` detail via `uipath-maestro-case`; RPA uses Action Center/long-running workflow.

### Integration Service

Use connector activities for SaaS systems in RPA, Flow, Case, and Agents; API Workflows and Maestro use connector activities rather than raw UI. RPA may use HTTP Request when no connector exists. Signals include named SaaS systems and create/read/post operations.

Run connector discovery before assuming availability:

```bash
uip is connectors list --output json                          # full catalog
uip is connectors list --filter "<KEYWORD>" --output json     # narrow by system name
```

If a connector exists, reuse it and set `Access Method = Integration Service — <CONNECTOR_SLUG>`; add a configuration task routed to `uipath-platform`. If absent and the host can call HTTP, use `Access Method = Direct HTTP`; do not create a connector/API Workflow for one host-capable consumer. If the host is IS-only, build a custom connector (`Access Method = Custom connector — <CONNECTOR_SLUG>`, task `uipath-connector-builder`) or a small API Workflow. Prefer the connector for 2+ consumers or IS-level connection governance. Mark unverified connectors `[SME REVIEW]`. Wrappers remain integrated components and do not change scope.

### API Workflow as an integrated component

Flag only when the primary invokes structured JSON system integration and the extraction test holds: host cannot call it natively, 2+ consumers share it, or it needs independent versioning/scaling/ownership. A host-capable direct call remains `Access Method = Direct HTTP`, with no API Workflow project/task. List invocations in Flow nodes, BPMN serviceTask rows, Agent tools, or Case tasks; create an ordered `uipath-api-workflow` task when needed.

### Reusability & shared assets

Reuse before build. Discover tenant libraries with [Tenant Library Search](tenant-library-search-guide.md) (Phase 1 Step 2.5) and reference them in §Packages. New RPA Libraries route to `uipath-rpa`; custom connectors route to `uipath-connector-builder`; reusable Marketplace/org components go in **Reusable Components**. Assets used by 2+ projects (Library, connector, IS connection, asset, queue) live at parent-folder/Solution level, are built once, and are referenced by all consumers. Flag reused and new assets; order new-asset tasks before consumers.

## Template Mapping

### Single product

| Primary Product | Template |
|---|---|
| RPA Process, Library, Test Automation | `../assets/templates/rpa-sdd-template.md` |
| Maestro Flow | `../assets/templates/flow-sdd-template.md` |
| Maestro BPMN | `../assets/templates/bpmn-sdd-template.md` |
| Case Management | `../assets/templates/case/case-sdd-template.md` |
| Agents | `../assets/templates/agent-sdd-template.md` |
| Coded Apps | `../assets/templates/coded-app-sdd-template.md` |
| API Workflows | `../assets/templates/api-workflow-sdd-template.md` |

Coded Functions are never Level 1 primaries and have no standalone template. Put their contract in the host's `### Coded Functions` table. In a Solution, include a project-list row and `uipath-functions` task but no per-project SDD. A Function-only request is a Lane B single-skill deferral to `uipath-functions`.

### Solution scope

Create exactly one `<SOLUTION_NAME_KEBAB>-solution-sdd.md` using the Solution overview structure and one `<PROJECT_NAME_KEBAB>-sdd.md` per unified project, using its product template. For RPA, use one SDD per RPA group; a Master Project's Dispatcher/Performer/Reporting share one RPA SDD, while unrelated RPA projects get separate files. Component rows (Coded Function, IXP model, custom connector) get no SDD file; document them in host tables and the overview inventory.

Solution overview sections:

1. Solution Overview.
2. Planner Handoff in the first ~50 lines, with `Project SDD role: root`, `Solution ID: <SOLUTION_NAME_KEBAB>`, `Solution root SDD: <its own filename>`, and `Tasks file: <SOLUTION_NAME_KEBAB>-tasks.md`; include cross-project ordering notes, but no task list.
3. Project Inventory.
4. Cross-Project Data Flow.
5. Shared Assets & Queues.
6. Per-Project SDD Index.

## Gap Handling for Agent / Coded App

When required information is missing, ask:

> The PDD describes <PRODUCT>-specific capabilities, but requirements are missing for: <LIST_GAPS>.
>
> 1. **Proceed with <PRODUCT>** *(recommended)* — I will ask follow-up questions to fill the gaps
> 2. **Use a different product** — I will ask which product to use instead

For option 1, ask batched product-specific gap questions, using at most 4 question objects per call and splitting larger sets. For option 2, ask:

> Which product should I use instead?
>
> 1. **RPA Process** — standard UI/data automation
> 2. **Maestro Flow** — orchestrate multiple automations
> 3. **Case Management** — staged lifecycle with SLA
> 4. **Stop** — do not generate an SDD

Do not auto-fallback. Re-run selection with the chosen fallback primary.

## Presenting the Recommendation

Put the recommended scope first, then single-product alternatives and `Solution (customize)`. If Level 1 is single product, recommend it with RPA subtype. If Level 1 is Solution, recommend the pre-composed Solution.

Emit this Phase 1 summary:

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

The `## Recommended Scope` lines `Recommendation:`, `Delivery model:`, and `Blocked by platform:` must also survive in the SDD. Every template places `## Recommended Scope` between `## Decisions Made` and `## Action Required`, in both execution modes (Phase 3 Step 2 item 3). Autonomous mode skips presentation, so the SDD copy is the durable Constraint Gate record.

Immediately ask:

> I recommend the following scope for this SDD. Which should I use?
>
> 1. **<RECOMMENDED_SCOPE>** *(recommended)* — <ONE_LINE_REASON>
> 2. **<STRONGEST_SINGLE_PRODUCT_ALTERNATIVE>** — <ONE_LINE_REASON_OR_TRADEOFF>
> 3. **<SECOND_SINGLE_PRODUCT_ALTERNATIVE_OR_OMIT_IF_NONE>** — <ONE_LINE_REASON>
> 4. **Solution (customize)** — I will ask you to check every product the Solution should include

Keep option 4 even when the recommendation is already a Solution.

### Customize branch

If the user chooses `Solution (customize)`, run Level 1.75 Pass A, Pass B, Pass C, and Level 2.5; re-emit the summary and confirmation. The customized composition replaces option 1. Allow at most 3 revisions; then proceed with the latest and mark disagreements `[SME REVIEW]`.

If the user rejects a single-product recommendation, re-run Level 1 (and Level 1.5 when the fallback is RPA) with the user's preference forced as primary, then re-present.