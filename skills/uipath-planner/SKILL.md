---
name: uipath-planner
description: "UiPath solution planner & designer. Always invoke for `pdd.md` / `sdd.md` files. Authors a Solution Design Document (SDD) from a Process Design Document (PDD), then derives the multi-skill, multi-project task list and emits live TaskCreate calls. Detects project type (.cs, .xaml, .flow, .bpmn, .py). For `uip solution` init/pack/publish/deploy/activate & `.uipx`→uipath-solution. For non-solution Orchestrator/IS/auth/traces→uipath-platform. For .xaml/.cs→uipath-rpa. For .flow→uipath-maestro-flow. For .bpmn→uipath-maestro-bpmn. For agent.json/.py→uipath-agents. For caseplan.json→uipath-maestro-case."
when_to_use: "User provides a PDD/SDD, says 'generate SDD'/'analyze this PDD'/design/architect/'turn this PDD into' a UiPath solution (selects product scope), OR makes a non-trivial request spanning SEPARATE buildable projects (a Flow orchestrating standalone RPA processes or agents that must themselves be built, 'build a solution from scratch'). Load BEFORE authoring an SDD or deriving tasks. Skip for SINGLE-project requests — even a Flow/Agent/RPA project with inline HITL/script/connector nodes in its own solution — invoke that specialist directly. Flow calling only existing/deployed processes→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# UiPath Planner — Design & Task Derivation

Two jobs, one entry point:

1. **Design** — turn a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD). Select scope (single product or multi-project Solution), write the SDD.
2. **Plan** — derive the per-skill task list from an SDD (or a non-PDD request), route to specialists, emit live `TaskCreate` calls.

Never execute the work. Outputs are SDD markdown, plan/tasks markdown, and live tasks — implementation always routes to a specialist.

The skill has three paths, decided by the **Entry Guard**:

- **Phase D — Design.** Input is a PDD, or an explicit "design / architect this" request. Author the SDD, then fall through into Lane A. See [sdd-generation-guide.md](references/sdd-generation-guide.md).
- **Lane A — PDD-driven.** Input is an SDD with the `## Planner Handoff` marker (written by Phase D, or hand-written). Read it, derive tasks, emit live tasks. Zero to two user prompts. See [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).
- **Lane B — Non-PDD.** No SDD; a non-PDD multi-project request. Elicit preferences, detect project type, write a plan, emit live tasks. 0–3 prompts (5-call cap). See [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

## When to Use This Skill

- User provides a **PDD** (PDF, docx, markdown) and asks to design or build from it → Phase D
- User asks to **design / architect / generate an SDD** for a UiPath automation → Phase D
- User provides an **SDD path** → Lane A
- The request is **non-trivial** — spans **separate buildable projects** that each need their own specialist (a Flow orchestrating standalone RPA processes or agents that must themselves be built) → Lane B
- The request is **ambiguous** — no single specialist clearly matches, or "what can I build?"

**Skip this skill for single-project tasks** — load the specialist directly. A request is **single-project** (one specialist owns it end-to-end) even when it bundles several things *inside one project*: a Flow with script nodes plus an inline HITL approval step plus its own solution wrapper is **one** `uipath-maestro-flow` task. Inline nodes (HITL QuickForm, script, connector, inline agent) and solution scaffolding are author sub-steps the specialist performs itself — not separate skills to orchestrate. Counting them as distinct skills and emitting a plan is the most common mis-trigger. This skill is only for work spanning **separate buildable projects** (distinct `.uipx` projects), or for turning a PDD into an architecture.

## Critical Rules

1. **Plan & design only — never author automation code.** Outputs: SDD markdown (Phase D), plan/tasks markdown (Lanes A/B), and live `TaskCreate` calls. NEVER write XAML, C#, Python, JSON, or project/scaffold files. Implementation always routes to a specialist. (SDD/plan authoring is the *only* file authoring this skill does.)
2. **Run the Entry Guard first.** Inspect the input and route to Phase D / Lane A / Lane B before anything else.
3. **Select scope before designing architecture (Phase D) — and gate every product by platform constraints.** Single product (RPA Process/Library/Test Auto, Maestro Flow, Case, Agents, Coded Apps, API Workflows) vs multi-project Solution determines the template(s) and project structure. Use the [Product Selection Guide](references/product-selection-guide.md): Constraint Gate → Level 1 → 1.5 (RPA sub-type) → 1.75 (Solution composition) → 2.5 (project decomposition). The delivery model (Cloud / Automation Suite / standalone — asked at Phase D entry) blocks unavailable products via [platform-availability-guide.md](references/platform-availability-guide.md); user-excluded products are never re-offered.
4. **The SDD is architecture only — no task lists.** Phase D produces the SDD (Project Structure, Data Definitions, Testing Strategy, …). Task derivation is Lane A's job. Never put Task 1 / Task N templates or *implementation* `TaskCreate` calls in the SDD. End the SDD with a `## Next Steps` section. (Progress-tracking `TaskCreate` calls are a separate, allowed use.)
5. **Write the `## Planner Handoff` header AND the `<!-- planner-handoff:v1 -->` marker into every SDD.** Load-bearing detection contract — the Entry Guard detects either signal (redundant on purpose). `Generated by: uipath-planner`. Fields: Execution autonomy, Delivery model, SDD scope, Project list section, Tasks file, Generated by, Generation date.
6. **Honour the template section structure as a hard superset contract.** Write single-product scope to `<PROCESS_NAME_KEBAB>-sdd.md`; write Solution scope to a `<SOLUTION_NAME_KEBAB>-solution-sdd.md` overview plus one `<PROJECT_NAME_KEBAB>-sdd.md` per project. If the user specifies an output path for the SDD, use it instead of these defaults. After writing, diff the generated H2/H3 headings against the template TOC — the generated set MUST be a superset. A missing template-required H2 is an SDD defect, not an `[SME REVIEW]` item — regenerate it.
7. **Testing is mandatory and thorough — never offer "happy path only".** Phase D writes a full §17 Testing Strategy (happy path, edge cases, error scenarios, e2e for Master Projects). The plan adds a mandatory Testing task **per generation skill**, routing to that specialist's testing references — never describing the procedure inline. Implementation specialists may scope down at execution time; the SDD and plan do not.
8. **Route — do not redescribe.** The plan says WHICH skill to load and IN WHAT ORDER. It does NOT describe specialist-internal flows (target configuration, OR registration, XAML pipelines, HITL field/outcome schema, auth, testing procedures). For a HITL step, pass business intent only ("manager approves or rejects an expense; can add a reason if rejected") — never a field-level spec; the HITL specialist chooses the schema shape.
9. **Per-phase prompt budget.** Phase D runs under its own checkpoint model (see [sdd-generation-guide.md](references/sdd-generation-guide.md)) — no hard numeric cap. Lanes A and B each cap at **5 `AskUserQuestion` calls**. Ask **execution autonomy exactly once** (Phase D entry) and write it into the handoff header; Lane A reads it and never re-asks. Scope/UI answers resolved in Phase D flow forward via the SDD.
10. **Fill gaps with `[DEFAULT]` or `[SME REVIEW]` — never silently invent business rules.** `[DEFAULT]` for industry-standard patterns (retry counts, timeouts); `[SME REVIEW]` for business-knowledge gaps. Resolve `[SME REVIEW]` items with the user before writing. For Agent/Coded App gaps, use `AskUserQuestion` (proceed-with-gap-filling vs different product) — never auto-fallback.
11. **The terminal artefact of a Solution build is a packed `.uipx`.** The SDD's §18 Next Steps points the user at the `uipath-solution` skill (`uip solution init` → `project add` per project → `resources refresh` → `pack`). A bare project folder is not the deliverable.
12. **Never copy SDD architecture into the plan, and never invent selectors or UI targets.** The plan references SDD section paths in skill prompts; it does not duplicate architecture content. Selectors require application inspection at development time — leave them for the specialist.

## Entry Guard

Run this guard before anything else.

```text
1. No document path?
   - Explicit design/architect language ("design this", "architect this",
     "generate an SDD"), OR an inline-described process with enough detail to
     substitute for a PDD (process steps + applications + exceptions) → Phase D.
   - Otherwise → Lane B. Lane B is the default for document-less
     multi-project requests.

2. Document path → read its first ~50 lines.
   - Contains `## Planner Handoff` OR `<!-- planner-handoff:v1 -->` → Lane A.
     (Either signal alone is sufficient — redundant on purpose.)
   - Reads as a PDD (process steps + application inventory + exceptions),
     or is a binary .pdf/.docx the user calls a PDD → Phase D.

3. Otherwise (no marker, ambiguous, or unparseable) — ask via AskUserQuestion:

   > What is the document at <path>?
   > 1. Process Design Document (PDD) — author the SDD (Phase D), then derive tasks
   > 2. Solution Design Document (SDD) — proceed with task generation (Lane A)
   > 3. Other context — read it; use its content to resolve Lane B elicitation
   >    questions (skip any question it answers) and as plan input (Lane B)

4. Route per the choice. For an SDD with no handoff header, proceed with safe
   defaults — see pdd-driven-lane-guide.md Step 1 for the default set and how
   defaults are surfaced to the user.
```

Do not pattern-match on filename or extension alone; those are unreliable. The `## Planner Handoff` heading and the `<!-- planner-handoff:v1 -->` marker are the load-bearing detection contract — Phase D writes both deterministically; the guard detects either.

## Phase D — Design (summary)

When triggered: input is a PDD, or an explicit design/architect request. Three phases; full detail in [sdd-generation-guide.md](references/sdd-generation-guide.md). All user questions use numbered-choice format.

1. **Phase 1 — PDD Analysis & Scope Selection.** Ask execution mode (Autonomous or Interactive) and delivery model (Cloud / Automation Suite / standalone) in one batched call — skip the delivery question when the PDD or request states it. Read the full PDD, extract structured information (including environment & constraint signals), run Constraint Gate → Level 1 (primary scope) → Level 1.5 (RPA sub-type) → Level 1.75 (Solution composition) → Level 2.5 (project decomposition). Step 2.5 runs an authenticated `uip` library search (CLI auth required). In Interactive mode, present a summary with the recommended scope at the top and alternatives below; in Autonomous mode, proceed.
2. **Phase 2 — Architecture Review.** Load the product-specific template. Generate the architectural core sections. Present for review in Interactive mode.
3. **Phase 3 — Full SDD Generation.** Generate all remaining sections including the thorough §17 Testing Strategy. Resolve `[SME REVIEW]` items first. Write the `## Planner Handoff` header + marker. Write the SDD to disk. **Fall through into Lane A** to derive tasks.

## Lane A — PDD-driven (summary)

When triggered: an SDD with the `Planner Handoff` marker is detected (or Phase D just wrote one).

1. Read the SDD's `## Planner Handoff` header (6 fields). Reuse the execution autonomy chosen in Phase D — do not re-ask.
2. If `<process>-tasks.md` already exists, ask `continue / regenerate` (1 prompt). See [plan-and-tasks-format.md → Regenerate logic](references/plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).
3. Parse the SDD project list section. Pick the multi-skill pattern.
4. Ask the UI batch (3 questions, 1 call) only if the SDD's Application Inventory lists UI applications and the answers aren't already resolved.
5. Derive tasks. Write `<process>-tasks.md`.
6. If `Execution autonomy: interactive` → `EnterPlanMode` for review. If `autonomous` → emit live tasks directly.
7. Emit `TaskCreate` calls + `addBlockedBy` edges. Hand off.

Full procedure: [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).

## Lane B — Non-PDD (summary)

When triggered: no SDD; a document-less multi-project request (the default route when no explicit design/architect language or inline-described process points to Phase D).

1. Step 1 — batched elicitation: bundle generation approach + execution autonomy + project-type fallback (when vague) + Solution scope (when the plan loads `uipath-maestro-flow`) into **one** `AskUserQuestion` call. Drop any question already resolved from context.
2. Step 2 — detect multi-skill patterns; emit multi-skill plan if applicable. See [multi-skill-patterns-guide.md](references/multi-skill-patterns-guide.md).
3. Step 3 — filesystem detection for single-skill plans.
4. Step 4 UI batch — only when the plan includes UI automation in `uipath-rpa`.
5. Write `YYYY-MM-DD-<feature>.md` to `docs/plans/` (project) or `./plans/` (no project).
6. If explore-first → `EnterPlanMode`. If simultaneous → emit plan as text + live tasks.

Full procedure: [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

## Skill capability map

High-level view of what each specialist owns. **Do not describe internal flows of any specialist in your plan** — each skill documents its own procedures and will drift out of sync if duplicated here.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | RPA workflows (XAML and C# coded): create, edit, build, run, debug. Owns **all** UI automation authoring end-to-end, including live-app exploration and probing. | No (relies on Studio) | **No** — defer to `uipath-solution` for `.uipx` multi-project, `uipath-platform` for single non-solution packages |
| `uipath-agents` | AI agents — code-based (LangGraph / LlamaIndex / OpenAI Agents) and low-code (`agent.json`) | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/` dir): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-maestro-flow` | `.flow` files orchestrating RPA, agents, apps | Yes (`uip login`) | **Partial** — follows plan `Solution scope` (SW or local); Orchestrator deploy of `.uipx`-wrapped solutions → `uipath-solution`; non-solution single package → `uipath-platform` |
| `uipath-maestro-case` | Case Management authoring (`caseplan.json` + generated BPMN) from an SDD | Yes (`uip login`) | **No** — deploys via `uipath-solution` (`.uipx`) |
| `uipath-api-workflow` | API Workflows (JSON `document.dsl`): author, run locally (`uip api-workflow run`), connector activities | Yes (`uip login`) | **No** — `uip solution pack/publish` via `uipath-solution` |
| `uipath-human-in-the-loop` | HITL node authoring — approval gates, escalations, write-back validation inside Flow / Maestro / coded-agent projects | No (authoring only) | **No** — ships inside the host project |
| `uipath-platform` | Auth (`uip login`), Orchestrator (folders, processes, jobs, machines, users, roles), resources (assets, queues, storage buckets + bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), traces, licensing | Yes (auth hub) | **Yes** — for non-solution single packages and Orchestrator-side post-deploy ops |
| `uipath-mcp-servers` | UiPath AgentHub MCP server registration (6 types: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`) and tool authoring on `uipath`-type servers (3 kinds: `is-activity`, `resource`, `raw`). Wraps IS connector activities, Orchestrator resources, external HTTP MCP endpoints, OpenAPI specs, published coded agents, local subprocess commands, or first-party UiPath services as MCP tools. NOT for FastMCP / Python `mcp` SDK work. | Yes (`uip login`) | **Yes** — registration is deployment (posts directly to AgentHub) |
| `uipath-solution` | `uip solution` lifecycle (init, pack, publish, deploy, activate) for `.uipx` solutions. Runs as the final skill in PDD-driven flows (deploy of `.uipx` solutions). | Yes (`uip login`) | **Yes** — for multi-project Solution (`.uipx`) deploys |

## Reference Navigation

### Phase D — Design

| File | Purpose |
|------|---------|
| [SDD Generation Guide](references/sdd-generation-guide.md) | Phase orchestrator — Phase 1, 2, 3 step-by-step instructions |
| [PDD Analysis Guide](references/pdd-analysis-guide.md) | How to extract structured data from PDDs in any format |
| [Product Selection Guide](references/product-selection-guide.md) | **Constraint Gate** (delivery model + exclusions filter), **Level 1** (primary scope), **Level 1.75** (Solution composition), **Level 2.5 Part B** (cross-product project list merge), **Level 3** (capability add-ons), template mapping |
| [Platform Availability Guide](references/platform-availability-guide.md) | Product × delivery-model availability matrix (Cloud / Automation Suite / standalone), alternatives for blocked products, verification rule for uncertain cells. Load whenever delivery model ≠ cloud. |
| [RPA Product Guide](references/rpa-product-guide.md) | RPA **Level 1.5** (sub-type), **Level 2** (authoring mode), **Level 2.5 Part A** (RPA decomposition), R-07 naming, REFramework. Load when Level 1 = RPA or a Solution includes RPA. |
| [Package Selection Guide](references/package-selection-guide.md) | NuGet package selection; Integration Service vs NuGet rules; per-product dependency manager. Load when filling §14 Packages or equivalent. |
| [Tenant Library Search Guide](references/tenant-library-search-guide.md) | Step 2.5 procedure for discovering deployed libraries via `uip or libraries list` + JMESPath filtering — auth preflight, ranking, zero-results branch, manual fallback. |

### SDD templates

| File | Purpose |
|------|---------|
| [RPA Template](assets/templates/rpa-sdd-template.md) | SDD template for RPA Process / Library / Test Automation |
| [Flow Template](assets/templates/flow-sdd-template.md) | SDD template for Maestro Flow |
| [Case Management Template](assets/templates/case-sdd-template.md) | SDD template for Case Management |
| [Agent Template](assets/templates/agent-sdd-template.md) | SDD template for UiPath Agents |
| [Coded App Template](assets/templates/coded-app-sdd-template.md) | SDD template for Coded Apps (web) |
| [API Workflow Template](assets/templates/api-workflow-sdd-template.md) | SDD template for API Workflows |

### Lanes A & B — Planning

| File | Purpose |
|------|---------|
| [PDD-driven Lane Guide](references/pdd-driven-lane-guide.md) | Lane A end-to-end — read SDD header, parse project list, derive tasks, write tasks.md, emit live tasks |
| [Non-PDD Lane Guide](references/non-pdd-lane-guide.md) | Lane B end-to-end — elicitation, project-type inference, filesystem detection, UI batch, write plan.md |
| [Multi-skill Patterns Guide](references/multi-skill-patterns-guide.md) | The named multi-skill patterns (RPA build+deploy, Flow with local/deployed resources, Agent with RPA tools, etc.). Used by both lanes. |
| [Plan and Tasks Format](references/plan-and-tasks-format.md) | Header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, TaskCreate mapping, anti-hallucination rule, quality rules |

## Anti-patterns

1. **Skipping the entry guard.** Always inspect the input first. A PDD silently treated as a generic doc produces a degraded deliverable.
2. **Writing automation code or modifying the project.** SDD and plan/tasks markdown only. In explore-first Lane B mode, non-mutating `uip` discovery is the upper limit.
3. **Treating a single-project request as a plan** — the most common mis-trigger. The inline-nodes rule lives in the Skip paragraph under When to Use This Skill.
4. **Copying the PDD structure into the SDD.** The SDD reorganizes content for implementation — it does not mirror the PDD's document flow.
5. **Defaulting to RPA Process when the PDD describes something else.** Use the Product Selection Guide decision tree. AI-reasoning signals → Agents; stages/SLA/approval → Case Management. Forcing single-product scope when the PDD describes multiple coordinated projects is the same mistake — offer Solution.
6. **Generating an Implementation Plan / task list inside the SDD.** Architecture only; the SDD ends with `## Next Steps`. Task derivation is Lane A's job.
7. **Describing specialist-internal flows in the plan or SDD.** Target configuration, OR registration, scaffolding, auth, pack/publish, testing procedures, HITL field schema — all owned by the specialist's own docs. Inlining creates drift.
8. **Asking about test coverage depth.** Testing is always thorough. The implementation specialist scopes down at execution time if the user wants a quick MVP; the planner does not offer the option.
9. **Recommending a skill that contradicts filesystem signals.** `.flow` → `uipath-maestro-flow`, not `uipath-rpa`.
10. **Inventing selectors from screenshots,** or asking the user what the planner / library / filesystem can already answer. Default first; spend a prompt only on decisions only the user can make.
11. **Renaming the `## Planner Handoff` heading or stripping the `<!-- planner-handoff:v1 -->` marker.** Either signal alone is sufficient for detection, but both should remain — removing both breaks Lane A detection silently.
12. **Recommending a product the customer's platform cannot run, or re-offering an excluded one.** Defaulting to cloud-modern picks (Maestro, Coded Apps, Document Understanding) on an Automation Suite engagement is the most expensive design error — every blocked product survives review only to fail at delivery. Run the Constraint Gate; once a user says "we don't want X", X stays blocked for the whole session.
