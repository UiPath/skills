---
name: uipath-planner
description: "UiPath solution planner & designer. Always invoke for PDD / SDD files (`pdd.md`, `*-sdd.md`). Authors a Solution Design Document (SDD) from a Process Definition Document (PDD) — or from another process-knowledge source (Confluence page, SOP, BPMN model, meeting transcript) — then derives the multi-skill, multi-project task list from an SDD, emitting live TaskCreate calls. Known-product single-project build, no PDD/SDD→that skill; ambiguous/'what should I build'→here. For `uip solution` lifecycle & `.uipx`→uipath-solution. For non-solution Orchestrator/IS/auth/traces→uipath-platform. For .xaml/.cs→uipath-rpa. For .flow→uipath-maestro-flow. For building/editing .bpmn→uipath-maestro-bpmn (a .bpmn as design input routes here). For agent.json/.py→uipath-agents. Sole case-SDD author. For caseplan.json build→uipath-maestro-case."
when_to_use: "User provides a PDD/SDD (or another process-knowledge source or a prompt — the planner asks clarifying questions), says 'generate SDD'/'analyze this PDD'/design/architect a UiPath solution, OR makes a non-trivial request spanning SEPARATE buildable projects (a Flow orchestrating RPA processes that must be built, 'build a solution from scratch'). A PDD or SDD ALWAYS routes here (Phase D) — author its SDD even for ONE RPA process; never hand a raw PDD to a specialist. Load BEFORE authoring an SDD or deriving tasks. Skip ONLY when no PDD/SDD and the request targets one project — even with inline HITL/script/connector nodes — invoke that specialist directly. Flow calling only existing/deployed processes→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Glob, Grep, WebFetch, AskUserQuestion, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# UiPath Planner — Design & Task Derivation

Two jobs share one entry point:
1. **Design** — convert a Process Definition Document (PDD) into an implementation-ready Solution Design Document (SDD), choosing single-product or multi-project Solution scope.
<!--skill-flavor:plan-job:start-->
2. **Plan** — derive per-skill tasks from an SDD or non-PDD request, route to specialists, and emit live `TaskCreate` calls.
<!--skill-flavor:plan-job:end-->

Never execute work. Produce only SDD markdown, plan/tasks markdown, and live tasks; implementation goes to a specialist.

## Paths

The **Entry Guard** selects:

- **Phase D — Design:** PDD or explicit design/architect request. Write the SDD; that write ends the turn, and Lane A continues next turn. See [sdd-generation-guide.md](references/sdd-generation-guide.md). Case Management uses Phase D's Case Design Lane ([case-design-lane-guide.md](references/case/case-design-lane-guide.md)), a conversational design ending in ONE Case Review confirmation.
- **Lane A — PDD-driven:** SDD containing `## Planner Handoff` (written by Phase D or manually). Read it, derive and emit live tasks; zero to two prompts. See [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).
- **Lane B — Non-PDD:** no SDD and a non-PDD multi-project request. Elicit preferences, detect project type, write a plan, and emit live tasks; 0–3 prompts, 5-call cap. See [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

## When to Use This Skill

Use Phase D for a PDD or process-knowledge source (PDD, Confluence page, BPMN model, meeting/Zoom transcript, SOP, requirements document, PDF, Word, Markdown, `.txt`, `.bpmn`, or pasted content) when asked to design/build from it or explicitly to design, architect, or generate an SDD. Use Lane A for an SDD path and Lane B for non-trivial work spanning separate buildable projects, each needing its own specialist, or ambiguous requests such as “what can I build?”.

**Skip this skill for single-project tasks:** load the specialist directly. One specialist owns a single project end-to-end even when it bundles multiple items: a Flow with script nodes, inline HITL approval, and its solution wrapper remains one `uipath-maestro-flow` task. Inline HITL QuickForm, script, connector, inline agent, and solution-scaffolding work are specialist sub-steps, not separate skills. This skill is only for distinct `.uipx` projects or PDD-to-architecture work.

## Critical Rules

<!--skill-flavor:plan-design-only-outputs:start-->
1. **Plan and design only; never author automation code.** Produce only SDD markdown (Phase D), plan/tasks markdown (Lanes A/B), and live `TaskCreate` calls. NEVER write XAML, C#, Python, JSON, or project/scaffold files; implementation routes to a specialist. SDD/plan authoring is the only file authoring allowed.
<!--skill-flavor:plan-design-only-outputs:end-->
2. **Run the Entry Guard first:** inspect input and route to Phase D, Lane A, or Lane B before anything else.
3. **Phase D selects scope before architecture and gates every product by platform constraints.** Choose single product (RPA Process/Library/Test Auto, Maestro Flow, Maestro BPMN, Case, Agents, Coded Apps, API Workflows) or multi-project Solution. Use [Product Selection Guide](references/product-selection-guide.md): Constraint Gate → Level 1 → 1.5 (RPA subtype) → 1.75 (Solution composition) → 2.5 (project decomposition). Ask delivery model (Cloud / Automation Suite / standalone) at entry; [platform-availability-guide.md](references/platform-availability-guide.md) blocks unavailable products; user-excluded products are never re-offered.
<!--skill-flavor:sdd-no-task-lists:start-->
4. **The SDD is architecture only.** Include Project Structure, Data Definitions, Testing Strategy, and other template sections, never Task 1 / Task N templates or implementation `TaskCreate` calls. End with `## Next Steps`; task derivation belongs to Lane A. Progress-tracking `TaskCreate` calls are allowed.
<!--skill-flavor:sdd-no-task-lists:end-->
5. **Every SDD must contain `## Planner Handoff` and `<!-- planner-handoff:v1 -->`.** Either signal detects it. Include `Generated by: uipath-planner`; Status (draft → ready), Execution autonomy, Delivery model, SDD scope, solution-root block when scope is Solution (Solution root SDD, Solution ID, Project SDD role root|child, Independently executable: no on children—the root Project Inventory + SDD Index are the sole executable entry; root and children share ONE canonical tasks file), Project list, Tasks file, Generated by, Generation date, and Template validation. Put the header after `## Document History`. First incremental write: `Status: draft`; only after SME resolution and template-superset validation: `Status: ready` and `Template validation: passed`. The marker identifies a planner SDD; Status determines consumability. Missing Status is legacy and treated as ready.
6. **Template structure is a hard superset contract.** Single-product output is `<PROCESS_NAME_KEBAB>-sdd.md`; Solution output is `<SOLUTION_NAME_KEBAB>-solution-sdd.md` plus `<PROJECT_NAME_KEBAB>-sdd.md` per project. A specified output path overrides defaults. After writing, diff generated H2/H3 headings against the template TOC; generated headings MUST be a superset. Missing template H2/H3 is an SDD defect, not `[SME REVIEW]`; regenerate it.
7. **Testing is mandatory and thorough.** Cover happy path, edge cases, error scenarios, and e2e for Master Projects. The plan adds one mandatory Testing task per generation skill, routed to that specialist's testing references, never describing its procedure inline. Specialists may scope down during execution; SDD and plan may not.
8. **Route, do not redescribe.** State WHICH skill to load and IN WHAT ORDER, not target configuration, OR registration, XAML pipelines, HITL field/outcome schema, auth, or testing procedures. For HITL, pass business intent only ("manager approves or rejects an expense; can add a reason if rejected") — never a field-level spec; the specialist chooses schema.
9. **Prompt budgets:** Phase D follows [sdd-generation-guide.md](references/sdd-generation-guide.md)'s checkpoint model, with no hard numeric cap. Lanes A/B allow at most **5 `AskUserQuestion` calls** each. Ask execution autonomy exactly once at Phase D entry and write it into the handoff; Lane A reads and never re-asks. Phase D scope/UI answers flow through the SDD.
10. **Fill gaps only with `[DEFAULT]` or `[SME REVIEW]`; never silently invent business rules.** `[DEFAULT]` is for industry-standard patterns (retry counts, timeouts); `[SME REVIEW]` is for business gaps. Resolve `[SME REVIEW]` before finalizing; they gate `Status: ready`, not the Phase 3 Step 0 skeleton write. For Agent/Coded App gaps, use `AskUserQuestion` (proceed with gap-filling vs different product), never auto-fallback.
   - These are the entire gap vocabulary; every consumer — the `Action Required — SME Review Items` block, gap counts, the `Status: ready` flip, Lane A assumptions, and reviewers — finds them by exact match on `[SME REVIEW]` / `[DEFAULT]`.
   - **Write the marker verbatim, with nothing else inside the brackets.** Explain after the closing bracket: `| UiPath version | [SME REVIEW] not recorded in the PDD |`. Never use `[SME REVIEW — not recorded]`, `[PLACEHOLDER]`, `[TBD]`, `[TODO]`, `<fill in>`, `N/A`, or “to be confirmed”. A decorated or renamed marker is invisible to every consumer above — the gap silently disappears.
   - When mapping/copying another document (source SDD to client template, PDD to SDD, or SDD section to another), carry markers byte-for-byte; add only newly found gaps and never edit inherited ones.
<!--skill-flavor:solution-terminal-artifact:start-->
11. **The terminal Solution artefact is a packed `.uipx`.** In `## Next Steps`, direct the user to `uipath-solution`: `uip solution init` → `project add` per project → `resources refresh` → `pack`. A bare project folder is not deliverable. If the Constraint Gate blocks Solutions for standalone, Automation Suite older than 2.2510, or user exclusion, rewrite Next Steps to per-package Orchestrator publish routed via `uipath-platform`.
<!--skill-flavor:solution-terminal-artifact:end-->
12. Never copy SDD architecture into the plan or invent selectors/UI targets. Reference SDD section paths in prompts; specialists inspect applications during development.
13. **Sole author of Case Management SDDs.** Every case design path — conversational, build handoff from `uipath-maestro-case`, draft finalization, PDD-driven — runs the Case Design Lane ([case-design-lane-guide.md](references/case/case-design-lane-guide.md)), which owns the conversation, the one confirmation, and the write; the case model and its defaults live in [case-design-layers-guide.md](references/case/case-design-layers-guide.md) and the render contract in the case SDD template. Design time resolves identities only — never schema discovery, project scaffolding, or create-on-missing; those are build concerns, recorded as gate decisions. **Open the lane's files with the Read tool, never `cat`.** **The design reading set is exactly three files** — the lane guide, the layers guide, and the case SDD template. `case-sdd-conformance-checklist.md` is NOT one of them: it belongs to the gate subagent at the end. **A design-only request (stops before `caseplan.json`) seeds `sdd.md` to disk as the FIRST tool call after the reading set**, before any design reasoning — the seed's content depends on none of it — then appends section by section. The lane's § Sketch bounded no-build item 0 owns the cadence.

## Entry Guard

Run this guard before anything else:

```text
0. Product design-lane signals — check first. Products with a dedicated Phase D design lane
   (today: Case Management — references/case/case-design-lane-guide.md) route to Phase D
   through that product lane when:
   - a build skill hands off a build request because design input is missing (same conversation):
     lane Build handoff mode;
   - the user requests that product's design without a PDD: lane direct;
   - the product's design draft exists/is named and the user requests finalization:
     lane draft finalization.
   The three-path taxonomy remains unchanged; the lane is Phase D's product-specific entrance.

1. No document path?
   - Explicit design/architect language (“design this”, “architect this”, “generate an SDD”),
     or an inline process with enough detail to substitute for a PDD (steps + applications +
     exceptions) → Phase D — Design.
   - A thin design request still goes to Phase D; elicit missing steps/applications/exceptions
     with AskUserQuestion in Phase 1, never Lane B.
   - Otherwise → Lane B — Non-PDD, the default document-less multi-project route.

2. Document path → read its first ~50 lines.
   - `## Planner Handoff` OR `<!-- planner-handoff:v1 -->` → Lane A — PDD-driven; either signal suffices.
   - A PDD or any process-knowledge source (steps + applications + exceptions in a PDD,
     Confluence page, BPMN model, meeting/Zoom transcript, SOP, requirements doc, or binary
     .pdf/.docx called a PDD) → Phase D — Design. Transcripts/thin wikis trigger heavier Phase 1 elicitation.

3. Otherwise (no marker, ambiguous, or unparseable), ask with AskUserQuestion:
   What is the document at <path>?
   1. Process Definition Document (PDD) — author the SDD (Phase D — Design), then derive tasks
   2. Solution Design Document (SDD) — proceed with task generation (Lane A — PDD-driven)
   3. Other context — read it; use it for Lane B elicitation (skip answered questions)
      and plan input (Lane B — Non-PDD)

4. Route by the answer. For an SDD without a handoff header, use safe defaults;
   see pdd-driven-lane-guide.md Step 1 for the default set and surfacing rules.
```

Do not pattern-match on filename or extension alone. `## Planner Handoff` and `<!-- planner-handoff:v1 -->` are the load-bearing contract; Phase D writes both deterministically and the guard detects either.

## Phase D — Design (summary)

Triggered by a PDD or explicit design/architect request. Full procedure: [sdd-generation-guide.md](references/sdd-generation-guide.md). All questions use numbered choices.

1. **Phase 1 — PDD Analysis & Scope Selection:** in one batched call ask execution mode (Autonomous or Interactive) and delivery model (Cloud / Automation Suite / standalone), skipping delivery when stated in the request/PDD or resolved by `uip login status` from session `BaseUrl`. Read the full PDD; extract structured information, environment/constraint signals, and as-is/to-be; synthesize the need profile (Step 3.5: product picks derive from need, not keywords); run Constraint Gate → Level 1 → Level 1.5 → Level 1.75 → Level 2.5. Step 2.5 runs authenticated `uip` library search (CLI auth required). Interactive mode presents recommended scope first and alternatives; Autonomous proceeds.
2. **Phase 2 — Architecture Review:** load the product template, generate architectural core sections, and present review in Interactive mode.
3. **Phase 3 — Full SDD Generation:** Step 0 is a hard gate: write the SDD skeleton to disk—header, `## Planner Handoff`/marker with `Status: draft`, `## Decisions Made`, `## Recommended Scope`, and Phase 1/2 sections—BEFORE any Phase 3 section; append each remaining section as you generate it so a watchdog kill leaves a gradeable file. Generate all remaining sections, including thorough Testing Strategy. Resolve `[SME REVIEW]` before finalizing; unresolved items carry recorded defaults and do not block ready, while architecture-blocking items keep `draft`. The LAST write sets `Status: ready` after the superset check. The SDD write is a turn boundary: autonomous mode ends after the SDD summary and continues in Lane A next turn; never stack both phases in one turn.

## Lane A — PDD-driven (summary)

Triggered by an SDD with the `Planner Handoff` marker (or one Phase D just wrote). Full procedure: [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).

1. Read `## Planner Handoff`. `Status: draft` means refuse task derivation (unfinished Phase D or blocking SME item) and offer resume/regenerate. Missing Status means legacy/ready. On ready SDDs, open default-carried SME items travel as assumptions; reuse Phase D autonomy and never re-ask. For `SDD scope: solution`, resolve the root, verify every indexed child exists, has the same Solution ID, and is ready; read every child architecture, merge shared resources, and emit ONE canonical tasks file (see pdd-driven-lane-guide Step 3).
2. If `<process>-tasks.md` exists, ask `continue / regenerate` (1 prompt); see [plan-and-tasks-format.md → Regenerate logic](references/plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).
3. Parse the SDD project list and select the multi-skill pattern.
4. Ask the UI batch (3 questions, 1 call) only when Application Inventory lists UI applications and answers are unresolved.
5. Derive tasks and write `<process>-tasks.md`.
<!--skill-flavor:lane-a-review-handoff:start-->
6. For `Execution autonomy: interactive`, use `EnterPlanMode` for review; for `autonomous`, emit live tasks directly.
7. Emit `TaskCreate` calls plus `addBlockedBy` edges, then hand off.
<!--skill-flavor:lane-a-review-handoff:end-->

## Lane B — Non-PDD (summary)

Triggered by no SDD and a document-less multi-project request, unless explicit design/architect language or an inline-described process routes to Phase D. Full procedure: [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

1. **Step 1 — detect before asking:** read context docs; use cross-platform `Glob`/`Read`/`Grep`; classify multi-skill pattern; infer project type from need; resolve delivery model.
2. **Step 2 — single-skill exit:** if one specialist owns one project end-to-end, stop Lane B and load that specialist with detected context; create no plan or tasks.
3. **Step 3 — batched elicitation:** in one `AskUserQuestion` call ask generation approach, execution autonomy, project-type fallback if vague, and delivery model if a gated product is a candidate; omit resolved questions.
4. **Step 4 UI batch:** only when the plan includes UI automation in `uipath-rpa`.
<!--skill-flavor:lane-b-write-and-present:start-->
5. Write `YYYY-MM-DD-<feature>.md` to `docs/plans/` (project) or `./plans/` (no project); embed the plan path in every task prompt.
6. For explore-first, use `EnterPlanMode`; for simultaneous, emit plan text plus live tasks.
<!--skill-flavor:lane-b-write-and-present:end-->

## Skill capability map

Do not describe specialist internals in plans; each skill owns its procedures.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | RPA workflows (XAML and C# coded): create, edit, build, run, debug; all UI authoring end-to-end, including live-app exploration/probing. | No (relies on Studio) | **No** — `uipath-solution` for `.uipx` multi-project; `uipath-platform` for single non-solution packages |
| `uipath-agents` | Code-based AI agents (LangGraph / LlamaIndex / OpenAI Agents) and low-code `agent.json` | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/`): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-functions` | Coded Functions: Python (`uip function new -l py`; Pydantic typed I/O) or TypeScript/JavaScript (`-l ts / js`, TypeScript default; `defineFunction` + schema-first typed I/O); atomic deterministic transforms, custom-auth API calls, ERP/IS queries; serverless or RPA robot; JS/TS delivered as run-as-job function or HTTP endpoint (Coded App backends), one calling mode per function; invoked from Maestro (Flow/BPMN), agents-as-tools, Orchestrator API, or HTTP trigger; no LLM/agent loop (use `uipath-agents`). | Yes (`uip login`) | **Yes** — `uip function pack/publish` |
| `uipath-rules` | Business Rules: one `.dmn` decision table (DMN 1.5) per project; `uip rules init`, `refresh`, `validate`, `debug`; called by BPMN business rule tasks, Case `business-rule` tasks, and RPA | Yes (`uip login` for `debug`) | **No** — `uip solution pack/publish/deploy` via `uipath-solution` |
| `uipath-maestro-flow` | `.flow` orchestration of RPA, agents, and apps | Yes (`uip login`) | **Partial** — `.uipx` solution via `uipath-solution`; non-solution single package via `uipath-platform` |
| `uipath-maestro-bpmn` | `.bpmn`, standards-based BPMN 2.0 orchestration with gateways, events, boundary timeouts, subprocesses, multi-instance, RPA, agents, APIs, HITL; owns inline userTask/HITL nodes | Yes (`uip login`) | **Yes** — packages, uploads, publishes/deploys, runs via `uip maestro bpmn`; `.uipx` solution via `uipath-solution` |
| `uipath-maestro-case` | Case authoring: `caseplan.case` from SDD (`case pack` compiles to `caseplan.case.bpmn`; direct `.bpmn` authoring is `uipath-maestro-bpmn`) | Yes (`uip login`) | **Partial** — publishes to Studio Web and Orchestrator; `.uipx` via `uipath-solution` |
| `uipath-api-workflow` | API Workflows (`document.dsl` JSON), local `uip api-workflow run`, connector activities | Yes (`uip login`) | **No** — `uip solution pack/publish` via `uipath-solution` |
| `uipath-human-in-the-loop` | HITL node authoring—approval gates, escalations, write-back validation inside **Flow**; coded-agent HITL → `uipath-agents`; BPMN/Case/RPA own inline userTask/task type/Action Center | No (authoring only) | **No** — ships inside host project |
| `uipath-platform` | Auth (`uip login`); Orchestrator folders, processes, jobs, machines, users, roles; assets, queues, storage buckets/files, libraries, webhooks, triggers; Integration Service connectors, connections, activities, IS triggers; Data Fabric entities/records/files/choice-sets (`uip df`); traces and licensing | Yes (auth hub) | **Yes** — single non-solution packages and Orchestrator post-deploy ops |
| `uipath-ixp` | Document Understanding/IXP extraction for semi-structured documents (invoices, forms): taxonomy, model, classify/extract/validate; standalone or extraction step consumed by a primary | Yes (`uip login`) | **Partial** — model publish/tag via `uip ixp`; host project consumes it |
| `uipath-connector-builder` | Integration Service custom REST+JSON connectors via `uip is connectors builder` when catalog lacks required integration; needed by API Workflows/Maestro/Agents, while RPA can call API directly | Yes (`uip login`) | **Yes** — import/publish via `uip is connectors` |
| `uipath-mcp-servers` | AgentHub MCP registration (6 types: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`) and resource-tool authoring on `uipath` servers (`automation`, `agent`, `agentic-process`, `api-workflow`); wraps Orchestrator resources, external HTTP MCP, OpenAPI, published coded agents, subprocess commands, or UiPath services; NOT FastMCP/Python `mcp` SDK work | Yes (`uip login`) | **Yes** — registration posts directly to AgentHub |
| `uipath-solution` | `uip solution` lifecycle (`init`, `pack`, `publish`, `deploy`, `activate`) for `.uipx`; final PDD-driven skill for `.uipx` deployment | Yes (`uip login`) | **Yes** — multi-project Solution deploys |

## Reference Navigation

### Phase D — Design

| File | Purpose |
|---|---|
| [SDD Generation Guide](references/sdd-generation-guide.md) | Phase orchestrator: Phases 1–3 step-by-step |
| [Case Design Lane Guide](references/case/case-design-lane-guide.md) | Case conversation: entry, tenant grounding, authoring policy, one Case Review, write |
| [Case Design Layers Guide](references/case/case-design-layers-guide.md) | Case model and every design **Default**: skeleton (triggers, stages, ten task types), gates, data, time, naming, closure checklist |
| [PDD Analysis Guide](references/pdd-analysis-guide.md) | Structured extraction from PDDs in any format |
| [Business Rules Guide](references/business-rules-guide.md) | Validation vs decision vs reasoning rules, DMN tables, reasoning list; load for RPA §4 or BPMN §5 |
| [Product Selection Guide](references/product-selection-guide.md) | Constraint Gate, Level 1, Level 1.75, Level 2.5 Part B, Level 3, template mapping |
| [Platform Availability Guide](references/platform-availability-guide.md) | Product × delivery-model matrix; load at every Constraint Gate. Cloud is not uniform: GovCloud / Dedicated / Test Cloud and tenant entitlements can block products; includes alternatives and uncertain-cell verification |
| [RPA Product Guide](references/rpa-product-guide.md) | RPA Level 1.5, Level 2 authoring, Level 2.5 Part A, R-07 naming, REFramework; load when Level 1 = RPA or a Solution includes RPA |
| [Package Selection Guide](references/package-selection-guide.md) | NuGet, Integration Service vs NuGet, per-product dependency manager; load for §14 Packages or equivalent |
| [Tenant Library Search Guide](references/tenant-library-search-guide.md) | Step 2.5 `uip or libraries list` + JMESPath filtering, auth preflight, ranking, zero-results, manual fallback |
| [Attended Re-auth Pattern Guide](references/attended-reauth-pattern-guide.md) | Portal automation contract for human-only login (hardware 2FA, smart card, biometric): handoff, verified resume, attended robot, `uipath-rpa`; load when sign-in is non-scriptable |
| [ASDD Crosswalk Guide](references/asdd-crosswalk-guide.md) | Client-facing Word SDD/ASDD: warn for template path, match markdown SDD, compute missing pieces; standard UiPath SDD crosswalk; load at Step 2.5 when the user wants the official document |

### SDD templates

| File | Purpose |
|---|---|
| [RPA Template](assets/templates/rpa-sdd-template.md) | RPA Process / Library / Test Automation SDD |
| [Flow Template](assets/templates/flow-sdd-template.md) | Maestro Flow SDD |
| [BPMN Template](assets/templates/bpmn-sdd-template.md) | Maestro BPMN SDD |
| [Case Management Template](assets/templates/case/case-sdd-template.md) | Case Management SDD / downstream Case Definition Blueprint |
| [Agent Template](assets/templates/agent-sdd-template.md) | UiPath Agents SDD |
| [Coded App Template](assets/templates/coded-app-sdd-template.md) | Coded Apps web SDD |
| [API Workflow Template](assets/templates/api-workflow-sdd-template.md) | API Workflows SDD |

### Scripts (Phase D)

| Script | Purpose |
|---|---|
| `scripts/docx-extract.{sh,ps1}` | `.docx` PDD → UTF-8 markdown + screenshots via pandoc; run at Phase D Step 1 when Word renders garbled; never use Word COM. Twins: `bash …/docx-extract.sh` on macOS/Linux/Git-Bash; `pwsh -File …/docx-extract.ps1` (or `powershell -File …` for Windows PowerShell 5.1) on Windows; keep behavior identical |
| `scripts/sdd-to-docx.{sh,ps1}` | SDD markdown → styled `.docx`, optional corporate `--reference-doc`; run at Phase D Step 2.5 only when the user asks for Word output; twins use `bash` `.sh` / `pwsh -File` `.ps1` |

### Lanes A & B — Planning

| File | Purpose |
|---|---|
| [PDD-driven Lane Guide](references/pdd-driven-lane-guide.md) | Lane A end-to-end: header, project list, task derivation, tasks.md, live tasks |
| [Non-PDD Lane Guide](references/non-pdd-lane-guide.md) | Lane B: elicitation, project inference, filesystem detection, UI batch, plan.md |
| [Multi-skill Patterns Guide](references/multi-skill-patterns-guide.md) | Named patterns (RPA build+deploy, Flow with local/deployed resources, Agent with RPA tools, etc.) |
<!--skill-flavor:plan-and-tasks-format-row:start-->
| [Plan and Tasks Format](references/plan-and-tasks-format.md) | Header/task rows, identity tuple, statuses, regenerate preservation, TaskCreate mapping, anti-hallucination, quality rules |
<!--skill-flavor:plan-and-tasks-format-row:end-->

## Anti-patterns

1. **Skipping the Entry Guard.** Always inspect first; treating a PDD as generic degrades the deliverable.
2. **Writing automation code or modifying the project.** Only SDD and plan/tasks markdown; in explore-first Lane B, non-mutating `uip` discovery is the limit.
3. **Treating a single-project request as a plan** — the most common mis-trigger. Use the inline-nodes rule under When to Use This Skill.
4. **Copying the PDD structure into the SDD.** Reorganize for implementation, do not mirror document flow.
5. **Defaulting to RPA Process when the need profile points elsewhere.** Use the Product Selection Guide; genuine judgment/reasoning → Agents, stages/SLA/approval lifecycle → Case Management, while AI over a rule-expressible decision remains RPA. Multiple coordinated projects require offering Solution.
6. **Generating an implementation plan/task list inside the SDD.** Architecture only, ending `## Next Steps`; Lane A derives tasks.
7. **Describing specialist-internal flows in the plan or SDD.** Target configuration, OR registration, scaffolding, auth, pack/publish, testing, and HITL field schema belong to specialist docs.
8. **Asking about test coverage depth.** Testing is always thorough; specialist may scope down at execution, planner does not offer it.
9. **Recommending a skill that contradicts filesystem signals.** `.flow` means `uipath-maestro-flow`, not `uipath-rpa`.
10. **Inventing selectors from screenshots,** or asking what planner/library/filesystem can answer. Default first and spend prompts only on user decisions.
11. **Renaming `## Planner Handoff` or stripping `<!-- planner-handoff:v1 -->`.** Either signal detects, but both should remain because removing both silently breaks Lane A.
12. **Recommending a product the customer's platform cannot run, or re-offering an excluded one.** Run Constraint Gate. Defaulting to cloud-modern Maestro, Coded Apps, or Document Understanding on Automation Suite is the most expensive design error; once excluded, a product stays blocked for the session.