# Solution Composition Guide

Levels 1.75 and 2.5 Part B of product selection — read by `design` when Level 1 = Solution (Level 1.75) and for every scope (Level 2.5). Levels 0–1 and the Constraint Gate: [product-selection-guide.md](../shared/product-selection-guide.md); per-task placement and Level 3: [component-placement-guide.md](../shared/component-placement-guide.md).

## Level 1.75 — Solution Composition

Applies only when Level 1 = Solution OR when the user picks "Solution (customize)" from the recommendation screen at Phase 1 Step 6. Skip otherwise.

The goal of Level 1.75 is to produce a concrete list of projects the SDD will cover. Composition runs in three passes.

### Pass A — Select products to include (multi-select)

**Gate the option list first.** Before composing the questions, drop every product the [Constraint Gate](../shared/product-selection-guide.md#constraint-gate) blocks for this delivery model (matrix block or user exclusion) — do not show a blocked product as a selectable option. When a dropped product had matching Level 1 signals, say so in the question preamble with the alternative from the availability matrix. When the matrix lists no alternative (e.g., Coded Apps on Automation Suite — no on-prem equivalent), state that and mark the touchpoint `[SME REVIEW]`; do not substitute a product the planner cannot build.

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

**Derived component projects — never Pass A options.** Coded Functions, IXP models, and custom connectors enter the project list from the step→executor map and Level 3 flags — one row per component, ordered before its consumers. Do not offer them in Pass A; confirm them in the recommendation summary instead. They get build tasks but no per-project SDD file (see [Template Mapping](scope-recommendation-guide.md#template-mapping)).

Present this project list in the Phase 1 summary ([scope-recommendation-guide.md](scope-recommendation-guide.md) § Presenting the Recommendation).

## Level 2.5 — Project Decomposition

Produces the final project list that Phase 2 turns into SDD sections. Runs for every scope, but the substantive work differs:

| Scope | What Level 2.5 does |
|---|---|
| Single product, single project (e.g., one Agent, one Flow, one Coded App) | Trivial — produces a one-row project list. Skip Part A. |
| RPA Process (single product) | Part A — run the RPA decomposition signals from the [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals). Skip Part B (Part A's narrower table is the final project list). |
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
