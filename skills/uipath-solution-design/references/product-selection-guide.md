# Product Selection Guide

This is the most important decision the SDD makes. Select the wrong product and the implementation plan is wrong. This guide produces a scope recommendation from PDD signals, covering all 7 UiPath products and multi-project Solutions.

## Levels of Decision

| Level | Decision | Scope |
|---|---|---|
| **1. Primary scope** | Single product or multi-project Solution? | All PDDs |
| **1.5. RPA sub-type** | Process, Library, or Test Automation | Only when RPA is selected at Level 1 (or included in a Solution) |
| **1.75. Solution composition** | Which products and how many projects of each | Only when Level 1 = Solution |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Per RPA project in the final list |
| **2.5. Project decomposition** | Final project list with roles, frameworks, queues | All scopes (trivial for single-project; substantive for RPA Process queue patterns and Solutions) |
| **3. Capabilities** | HITL, Integration Service, API Workflow as component | All products |

## Level 1 — Primary Scope Selection

### Decision table

Walk through in priority order. **First match wins.** Signals that match *below* the primary become candidate additional projects in a Solution (see Solution Signals below).

| Priority | Signal in PDD | Primary Scope |
|----------|---------------|---------------|
| 1 | AI reasoning, LLM judgment, tool calling, RAG, knowledge retrieval | Agents |
| 2 | Web dashboard, internal tool, Action Center form as the deliverable | Coded Apps |
| 3 | System-to-system API integration (synchronous, no UI, no bots) | API Workflows |
| 4 | Case lifecycle with stages, SLA tracking, approval gates, task routing | Case Management |
| 5 | Orchestrating MULTIPLE automation types (RPA + agents + apps) | Maestro Flow |
| 6 | UI automation, data processing, reusable component, or application testing (no other product fits) | **RPA** (sub-type decided at Level 1.5) |
| 7 | Multiple coordinated projects across products or mixed RPA sub-types (e.g., Flow + API Workflows, or 2 Libraries + 1 Test Automation project) | **Solution** (composition decided at Level 1.75) |

### Solution Signals

A Solution is the correct primary when any of the following applies, even if a single product would otherwise match at priority 1-6:

- The PDD describes **two or more distinct top-level products** that must coexist (e.g., Flow that calls an API Workflow that is itself a deliverable).
- The PDD mentions **reusable components** that other automations consume (Library) AND a standalone process that uses them.
- The PDD calls out a **dedicated test suite / regression pack** alongside the process being tested (Test Automation + the Process it validates).
- The PDD describes **multiple independent streams** with no single runtime orchestrator (e.g., separate dispatchers feeding separate performers with no Flow tying them together).

When any of the above applies, set the default primary to **Solution** and pre-compose the product list from the matched signals. Otherwise default to the highest single-product match.

> **Ambiguous dual-product PDDs:** If exactly two products match with similar strength and no Solution signal applies, mark the higher-priority match as the default single-product recommendation and offer Solution (customize) as an alternative in the recommendation screen. Let the user confirm via `AskUserQuestion`.

### Signals per product

#### Agents (Python + agent.json)

**Signals the PDD is describing an Agent:**
- "AI reasoning", "LLM", "GPT", "Claude"
- "Tool calling", "function calling"
- "RAG", "knowledge base", "semantic search", "vector store"
- "Multi-step reasoning", "plan and execute"
- "Natural language interface"
- Agent decides what to do based on user input, not a fixed script

**Required PDD information (may trigger gap-filling Q&A):**
- Framework preference (LangGraph, LlamaIndex, OpenAI Agents, Simple Function)
- Tools the agent will use (external APIs, RPA processes, API workflows)
- Memory / RAG sources if applicable
- Evaluation criteria (trajectory, success metrics)

**Missing-info trigger:** If the PDD has agent signals but lacks framework/tools/evaluation details → use `AskUserQuestion` (see Gap Handling below).

#### Coded Apps (Web)

**Signals the PDD is describing a Coded App:**
- "Dashboard", "web interface", "portal", "internal tool"
- "User submits a form"
- "Review screen" or "approval UI"
- "Action Center custom form"
- Deliverable is a web application users interact with

**Required PDD information (may trigger gap-filling Q&A):**
- Framework (React, Angular, Vue)
- App type (Web standalone vs. Action for automation-triggered)
- Pages / routes / user flows
- State management complexity
- Who calls the app (direct user, HITL form, Action Center task)

**Missing-info trigger:** If the PDD has web-UI signals but lacks framework/pages/flows → use `AskUserQuestion`.

#### API Workflows

**Signals the PDD is describing an API Workflow:**
- System-to-system integration with **no UI** and **no human interaction**
- Synchronous request-response pattern (milliseconds to seconds)
- Pulls, composes, or transforms data across SaaS systems (Workday, Zendesk, Salesforce, ServiceNow, etc.)
- Consumed by agents as a tool, called from Flows, or over HTTP by external systems
- High-throughput requirement (many small, fast operations)
- **No need for attended/unattended robots**

**Key distinction from RPA Library:** Libraries are compile-time reusable components for other automations. API Workflows are runtime-callable services over HTTP, serverless, no bots needed.

**Required PDD information:**
- Input schema (JSON) — parameters the caller provides
- Output schema (JSON) — data returned
- Connectors or HTTP endpoints to call
- Performance expectations (latency, throughput)

#### Case Management

**Signals the PDD is describing Case Management:**
- "Stages" or "phases" in the process
- "Approval gate" that blocks progression
- "SLA" or "service level agreement"
- "Escalation" on time or condition
- "Case" as a first-class concept (invoice case, ticket case, claim case)
- BPMN-style multi-lane flow
- Tasks that can run in parallel within a lane

**Required PDD information:**
- Stage definitions with entry/exit conditions
- Task definitions per stage
- SLA rules (time-based or condition-based)
- Escalation rules

#### Maestro Flow

**Signals the PDD is describing a Flow:**
- Orchestrating multiple automation types (RPA + agents + apps)
- Conditional routing between automations
- Data transformations between steps (filter, map, group-by)
- Scheduled triggers
- Subflows for reusable grouped logic
- "Flow" or "pipeline" terminology

**Required PDD information:**
- Node sequence with conditional branches
- Variables passed between nodes
- External systems involved
- Trigger type (manual, scheduled, event)

#### RPA (sub-type and decomposition decided in rpa-product-guide.md)

When Level 1 selects RPA, load the [RPA Product Guide](rpa-product-guide.md) for sub-type signals (Library / Test Automation / Process), Level 1.5 sub-type confirmation, Level 2 authoring mode, and Level 2.5 Part A decomposition. Do not reproduce those decisions here.

## Level 1.5 — RPA Sub-type Selection

See [RPA Product Guide → Level 1.5](rpa-product-guide.md#level-15--rpa-sub-type-selection).

When a Solution composition at Level 1.75 includes two or more RPA projects, run Level 1.5 **once per project** — do not assume they share a sub-type.

## Level 1.75 — Solution Composition

Applies only when Level 1 = Solution OR when the user picks "Solution (customize)" from the recommendation screen at Phase 1 Step 6. Skip otherwise.

The goal of Level 1.75 is to produce a concrete list of projects the SDD will cover. Composition runs in three passes.

### Pass A — Select products to include (multi-select)

`AskUserQuestion` has a hard 4-option cap per question. Pass A covers 8 candidate products, so it **must be a single `AskUserQuestion` call containing two question objects**, each with `multiSelect: true` and ≤4 options. The user answers both questions on one screen; both sets of selections return together.

Invoke exactly like this:

```json
AskUserQuestion({
  "questions": [
    {
      "question": "Which core automation layers should the Solution include?",
      "multiSelect": true,
      "options": [
        { "label": "RPA",             "description": "Attended/unattended RPA Process, Library, or Test Automation project(s)" },
        { "label": "Maestro Flow",    "description": "Long-running orchestration across RPA, Agents, APIs, and HITL" },
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
| Maestro Flow | Level 1 Flow signals matched (orchestration across products) |
| Case Management | Level 1 Case signals matched (stages, SLA, approvals) |
| Agents | Level 1 Agent signals matched (AI reasoning, tool use) |
| Coded Apps | Level 1 Coded Apps signals matched (custom UI, data entry forms) |
| API Workflows | Level 1 API Workflow signals matched OR another selected product needs a callable integration |
| RPA Library | Library signals matched in the PDD (shared helpers, NuGet distribution) — and pre-select RPA if so |
| RPA Test Automation | Test Automation signals matched (regression pack, assertions) — and pre-select RPA if so |

Use the client's pre-selection mechanism (`defaultSelected: true` or equivalent) so the user opens the screen with the recommended composition already checked. They can uncheck, add, or leave as-is. If no signals match for an option, leave it unchecked — the user adds it explicitly if they disagree.

### Pass B — Resolve quantities per product

For products that naturally appear more than once in a Solution (RPA projects most commonly), ask for the count. Use numbered-choice `AskUserQuestion` with defaults derived from the signals:

> How many RPA projects does the Solution need?
>
> 1. **1** *(recommended if the PDD describes a single end-to-end RPA flow)*
> 2. **2**
> 3. **3 or more** — you will specify the list in the next step

If the user picks "3 or more", follow up with a free-text-style question (use `AskUserQuestion` with numbered options covering the most likely counts, plus "Other" for custom).

Flow, Case Management, Agents, Coded Apps, and API Workflows default to **1** each unless the PDD explicitly describes multiple instances.

### Pass C — Run Level 1.5 per RPA project

For each RPA project in the composition, run Level 1.5 to pick its sub-type (Process / Library / Test Automation). Present one `AskUserQuestion` per RPA project — do not batch unless the PDD clearly assigns the same sub-type to all of them.

### Output of Level 1.75

Produce a **project list** that feeds Level 2 and Level 2.5:

| # | Project Name (proposed) | Product | RPA Sub-type | Source Signal |
|---|---|---|---|---|
| 1 | `<NAME>_Flow` | Maestro Flow | — | "orchestrates extraction + reporting" |
| 2 | `<NAME>_Extractor` | RPA | Process | "email ingestion + DU extraction" |
| 3 | `<NAME>_SharedUtils` | RPA | Library | "reusable helpers across projects" |
| 4 | `<NAME>_Regression` | RPA | Test Automation | "weekly regression pack" |
| 5 | `<NAME>_LookupApi` | API Workflows | — | "called as a tool from the Flow" |

Present this project list in the Phase 1 summary (see "Presenting the Recommendation" below).

## Level 2 — Authoring Mode (RPA only)

See [RPA Product Guide → Level 2](rpa-product-guide.md#level-2--authoring-mode). Applies to every RPA project in the scope (Process, Library, or Test Automation).

## Level 2.5 — Project Decomposition

Produces the final project list that Phase 2 turns into SDD sections. Runs for every scope, but the substantive work differs:

| Scope | What Level 2.5 does |
|---|---|
| Single product, single project (e.g., one Agent, one Flow, one Coded App) | Trivial — produces a one-row project list. Skip Part A. |
| RPA Process (single product) | Part A — run the RPA decomposition signals from the [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals). Skip Part B (Part A's narrower table is the final project list). |
| Solution (Level 1.75) | Part A — run the RPA decomposition signals on every RPA Process project in the composition. Part B — merge with the non-RPA projects from the Level 1.75 project list to produce the unified project list. |

### Part A — RPA decomposition signals

See [RPA Product Guide → Level 2.5 Part A](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals). That file holds the 6 signals, the common decomposition patterns (Dispatcher/Performer, Dispatcher/DU/Output), and the narrower single-product project list. Apply Part A to every RPA Process project in the scope.

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

## Level 3 — Capability Add-ons

These are capabilities added to the primary product, not standalone products. When detected, flag them in the appropriate template section and create implementation tasks that will route to the correct skill.

### HITL (Human-in-the-Loop)

**Scope:** Adds approval gates, exception escalation, and write-back validation to **Flow, Maestro, or Coded Agents** (not RPA, Case Management, or Coded Apps).

**Signals the PDD needs HITL:**
- "Approval before..."
- "Human reviews..."
- "If confidence is low, escalate..."
- "Validate before writing back..."
- "Fills in missing data..."

**How to flag:** In the Flow / Maestro / Agent template, add a "HITL Touchpoints" line in the relevant section (node table, agent description). In the implementation plan, add a task "Add HITL node per §X" — this will route to the `uipath-human-in-the-loop` skill at execution.

### Integration Service

**Scope:** Adds connector activities (Salesforce, Jira, ServiceNow, Slack, etc.) to RPA, Flow, Case Management, or Agents.

**Signals the PDD needs Integration Service:**
- Third-party SaaS system mentioned (not a custom web app): Salesforce, Jira, ServiceNow, Slack, HubSpot, Workday, Zendesk, etc.
- "Create a ticket in...", "Post a message to...", "Read records from..."

**How to flag:** In the Application Inventory section, list the connector explicitly. In the implementation plan, add a task "Configure X connector" — this will route to the `uipath-platform` skill at execution.

### API Workflow (as integrated component)

**Scope:** When API Workflow is NOT the primary but is called by the primary (Flow, Agent, Case Management, another API Workflow).

**Signals:**
- The primary product invokes a callable system-to-system integration
- Input/output is structured JSON, not UI

**How to flag:** In the primary product's template, list API Workflow invocations in the relevant section (Flow nodes, Agent tools, Case tasks). In the implementation plan, add a task "Create API Workflow X" — future API Workflow skill will handle; for now, reference the API Workflow template.

## Template Mapping

### Single-product scope

Based on the Level 1 primary, select one template:

| Primary Product | Template |
|---|---|
| RPA Process, Library, Test Automation | `../assets/templates/rpa-sdd-template.md` |
| Maestro Flow | `../assets/templates/flow-sdd-template.md` |
| Case Management | `../assets/templates/case-sdd-template.md` |
| Agents | `../assets/templates/agent-sdd-template.md` |
| Coded Apps | `../assets/templates/coded-app-sdd-template.md` |
| API Workflows | `../assets/templates/api-workflow-sdd-template.md` |

### Solution scope (Level 1 = Solution or user picked Solution (customize))

A Solution produces **one SDD file per project in the Level 2.5 unified project list** plus a **solution overview SDD** that ties them together. Use the kebab-case project name from the unified list as the filename.

| Output file | Template | How many |
|---|---|---|
| `<SOLUTION_NAME_KEBAB>-solution-sdd.md` | Solution overview (see structure below) | Exactly 1 |
| `<PROJECT_NAME_KEBAB>-sdd.md` | Per-project — pick the template matching that project's product | One per project in the unified list |

For RPA projects in the Solution, use the RPA template once per RPA *group* — if the Level 2.5 Part A decomposition produced a Master Project (e.g., Dispatcher + Performer + Reporting), those sub-projects share one RPA SDD file (§10/§11 cover the sub-projects). If two RPA projects are unrelated (e.g., a Library not called by the Performer), they each get their own RPA SDD file.

### Solution overview SDD structure

The solution overview SDD includes:

1. Solution Overview (objective, business context)
2. Project Inventory — the unified project list from Level 2.5 Part B
3. Cross-Project Data Flow — how projects call each other (Flow → RPA, Agent tool → API Workflow, RPA Performer → Library)
4. Shared Assets & Queues — assets, credentials, and queues referenced by more than one project
5. Per-Project SDD Index — filename + one-line scope per project
6. Consolidated Implementation Plan — task ordering across projects (integrated components built before their consumers)

## Gap Handling for Agent / Coded App

When the primary product is Agents or Coded Apps and the PDD is missing required information (listed in the signals above):

1. Use `AskUserQuestion` with the numbered-choice format:

> The PDD describes <PRODUCT>-specific capabilities, but requirements are missing for: <LIST_GAPS>.
>
> 1. **Proceed with <PRODUCT>** *(recommended)* — I will ask follow-up questions to fill the gaps
> 2. **Use a different product** — I will ask which product to use instead

2. If user chooses **option 1** → use `AskUserQuestion` again with a batch of 4-6 product-specific gap-filling questions (numbered, with defaults where possible)

3. If user chooses **option 2** → use `AskUserQuestion` for the fallback:

> Which product should I use instead?
>
> 1. **RPA Process** — standard UI/data automation
> 2. **Maestro Flow** — orchestrate multiple automations
> 3. **Case Management** — staged lifecycle with SLA
> 4. **Stop** — do not generate an SDD

4. Re-run product selection with the fallback as primary

Do not auto-fallback. The user must choose explicitly.

## Presenting the Recommendation

The recommendation screen always puts the **recommended scope at the top** and offers **single-product alternatives plus "Solution (customize)"** below. The recommended scope is determined by Level 1:

- If Level 1 produced a single product → the recommendation is that single product (with its Level 1.5 sub-type if RPA).
- If Level 1 produced Solution (one or more Solution Signals matched) → the recommendation is the **pre-composed Solution**, with the pre-checked product list from Pass A of Level 1.75.

### Summary block

Emit this block as the Phase 1 summary content:

```markdown
## Recommended Scope
**Recommendation:** <SINGLE_PRODUCT | SOLUTION(<PRODUCT_1>, <PRODUCT_2>, ...)>
**Reasoning:**
- <SIGNAL_FROM_PDD> → <PRODUCT_MAPPING>
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

### Confirmation question

Right after emitting the summary, confirm the scope via `AskUserQuestion` with the numbered-choice format. **The recommended option is always item 1.**

> I recommend the following scope for this SDD. Which should I use?
>
> 1. **<RECOMMENDED_SCOPE>** *(recommended)* — <ONE_LINE_REASON>
> 2. **<STRONGEST_SINGLE_PRODUCT_ALTERNATIVE>** — <ONE_LINE_REASON_OR_TRADEOFF>
> 3. **<SECOND_SINGLE_PRODUCT_ALTERNATIVE_OR_OMIT_IF_NONE>** — <ONE_LINE_REASON>
> 4. **Solution (customize)** — I will ask you to check every product the Solution should include

When the recommendation is already a Solution, still include **Solution (customize)** as an option so the user can adjust the composition. When the recommendation is a single product, **Solution (customize)** lets the user upgrade to a multi-project design.

### Customize branch

If the user picks **Solution (customize)**:

1. Run Level 1.75 Pass A (paired multi-select) — pre-check the recommended products from the default composition (or from the signals if the default was single-product).
2. Run Level 1.75 Pass B — resolve quantities per product.
3. Run Level 1.75 Pass C — sub-type per RPA project.
4. Run Level 2.5 to produce the unified project list.
5. Re-emit the summary block with the customized project list, then re-run the confirmation question. The customized composition replaces option 1 (still marked *recommended*) so the user can confirm or customize again (max 3 revisions — after that, proceed with the latest composition and tag disagreements as `[SME REVIEW]`).

### If the user disagrees with a single-product recommendation

Re-run Level 1 (and Level 1.5 if the chosen fallback is RPA) with the user's preference as the forced primary, then re-present.
