---
name: uipath-planner
description: "UiPath task planner — reads SDDs from uipath-solution-design or elicits non-PDD requests, derives multi-skill task lists, emits live TaskCreate calls. Detects project type (.cs, .xaml, .flow, .py). For PDDs→uipath-solution-design first."
when_to_use: "User makes a non-trivial UiPath request — 'build a UiPath solution for X', 'set up a process from scratch', 'help me plan this' — OR provides an SDD path. Skip when project type and scope are already clear for a single-skill task — invoke the specialist directly."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# UiPath Task Planner

Your job is to **derive task lists, route to specialists, and emit live tasks** — never execute the work yourself.

The planner has two lanes:

- **Lane A — PDD-driven.** Triggered when the input is an SDD with a `## Planner Handoff` header. Reads the SDD, derives tasks per the project list, writes `<process>-tasks.md`, emits live `TaskCreate` calls. Zero or one user prompt. See [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).
- **Lane B — Non-PDD.** Triggered when there's no SDD. Elicits preferences, detects project type, multi-skill patterns or filesystem signals, writes `<feature>.md`, emits live tasks. 1-5 user prompts. See [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

The lane is decided by the **Entry Guard** below.

## When to Use This Skill

- The request is **non-trivial** — multi-step, multi-skill, UI automation, or unclear scope
- The request is **ambiguous** — no single specialist skill clearly matches
- The user asks "what can I build?" or needs help choosing a project type
- The user provides an SDD path — Lane A runs

Skip this planner for simple, well-defined single-skill tasks (e.g., "create a workflow that sends an email") — load the specialist directly.

## Critical Rules

1. **Plan only — never execute the work yourself.** Do NOT write automation code (XAML, C#, Python, JSON) or create project files. Plan / tasks files and live `TaskCreate` calls are the only outputs you produce.
2. **For PDDs, hard-block and redirect to `uipath-solution-design`.** A PDD (PDF, docx, or markdown describing process steps + applications + exceptions) does NOT belong in this skill. The dedicated PDD→SDD skill produces a much better deliverable. The only escape is the user explicitly saying "skip SDD".
3. **Never exceed 5 `AskUserQuestion` calls in any planning session.** Each call is one user-facing prompt; batch related questions (e.g., the Step 4 UI elicitation in Lane B batches App type, Targeting approach, App state into one call). If you cannot fit the elicitation in 5 calls, plan with best available info and note the assumption. Lane A typically uses 0–2 calls.
4. **Always include a mandatory Testing task per generation skill** in the plan. Testing is non-negotiable — happy path + edge cases + error scenarios + e2e for Master Projects. The Testing task routes to the specialist's testing references and does NOT describe the testing procedure inline.
5. **Route — do not redescribe.** The plan says WHICH skill to load and IN WHAT ORDER. It does NOT describe specialist-internal flows (target configuration, OR registration, XAML authoring pipelines, auth flows, testing procedures). Each specialist's docs own those details.

## Entry Guard

When the planner is invoked, run this guard before anything else.

```
1. Did the user reference a document path?
   - No → Lane B (non-PDD elicitation)

2. The path resolves to a file. Read its first ~50 lines.
   - File contains the exact heading "## Planner Handoff" → Lane A (read SDD, derive tasks)

3. Otherwise (no marker, or unparseable / binary file like .pdf / .docx):
   ask via AskUserQuestion:

   > What is the document at <path>?
   > 1. Solution Design Document (SDD) — proceed with task generation (Lane A, hand-written SDD)
   > 2. Process Design Document (PDD) — load uipath-solution-design first
   > 3. Other context — note its existence; proceed with non-PDD elicitation (Lane B)

4. Based on user's choice:
   - SDD → Lane A. Try to find the Planner Handoff header; if missing, proceed with safe defaults
     (interactive autonomy, single-product scope) and log a one-line warning.
   - PDD → HARD BLOCK with this message:

     > The document at <path> is a Process Design Document. UiPath has a dedicated skill
     > for PDD→SDD generation that produces a much better deliverable: uipath-solution-design.
     > Load it with this PDD path; it will produce an SDD that I can then use to generate
     > the task list.
     >
     > If you've already considered the SDD path and want a lightweight plan from this PDD
     > anyway, tell me "skip SDD" and I'll proceed with degraded inline reading (Lane B + PDD
     > as context).

   - Other context → Lane B, with the document path noted in plan header.
```

The `## Planner Handoff` heading is the load-bearing detection contract — `uipath-solution-design` writes it deterministically, this skill detects it. Do not pattern-match on filename or extension; those are unreliable.

## Lane A — PDD-driven (summary)

When triggered: SDD detected at entry guard.

1. Read the SDD's `## Planner Handoff` header (6 fields: Execution autonomy, SDD scope, Project list section, Tasks file, Generated by, Generation date).
2. If `<process>-tasks.md` already exists, ask `continue / regenerate` (1 prompt). Regenerate preserves completed work via task identity matching — see [plan-and-tasks-format.md → Regenerate logic](references/plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).
3. Parse the SDD project list section. Pick the multi-skill pattern.
4. Ask the Step 4 UI batch (3 questions, 1 call) only if §9 contains UI applications and the answers aren't already resolved from context.
5. Derive tasks. Write `<process>-tasks.md`.
6. If `Execution autonomy: interactive` → `EnterPlanMode` for review. If `autonomous` → emit live tasks directly.
7. Emit `TaskCreate` calls + `addBlockedBy` edges. Hand off.

Full procedure: [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).

## Lane B — Non-PDD (summary)

When triggered: no SDD; user described a task or asked for help planning one.

1. Q1 — Generation approach (explore-first vs simultaneous). Skip for simple/single-skill.
2. Q2 — Execution autonomy (autonomous vs interactive). Skip in explore-first mode.
3. Project type — infer from explicit mode, keyword signals, or filesystem; ask only if vague (max 1 prompt).
4. Step 2 — detect multi-skill patterns; emit multi-skill plan if applicable. See [multi-skill-patterns-guide.md](references/multi-skill-patterns-guide.md).
5. Step 3 — filesystem detection for single-skill plans.
6. Step 4 UI batch — only when plan includes UI automation in `uipath-rpa`.
7. Write `YYYY-MM-DD-<feature>.md` to `docs/plans/` (project) or `~/Documents/UiPath/Plans/` (no project).
8. If explore-first → `EnterPlanMode`. If simultaneous → emit plan as text + live tasks.

Full procedure: [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

## RPA skill routing

Two RPA skills exist. Pick the right one (applies to both lanes):

| Signal | Route to |
|---|---|
| `project.json` has `"targetFramework": "Legacy"` or no `targetFramework` field | `uipath-rpa-legacy` |
| `project.json` has any other `targetFramework` (e.g., `"Portable"`, `"Windows"`) | `uipath-rpa` |
| No existing project | `uipath-rpa` (default for all new projects) |
| macOS host | `uipath-rpa` — cross-platform target only (Windows target not available on macOS) |
| Windows host | `uipath-rpa` — user can choose Windows or cross-platform target |

**Rules:**

1. Never suggest `uipath-rpa-legacy` for new projects unless the user explicitly requests legacy.
2. On macOS, only cross-platform automation is supported — always route to `uipath-rpa`.

## Skill capability map

High-level view of what each specialist owns. **Do not describe internal flows of any specialist in your plan** — each skill documents its own procedures and will drift out of sync if duplicated here.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | RPA workflows (XAML and C# coded): create, edit, build, run, debug. Owns **all** UI automation authoring end-to-end. | No (relies on Studio) | **No** — defer to `uipath-platform` |
| `uipath-rpa-legacy` | Legacy RPA workflows (.NET Framework 4.6.1, XAML only). **Existing legacy projects only** — never for new projects unless user explicitly requests legacy. | No | **No** — defer to `uipath-platform` |
| `uipath-agents` | AI agents — code-based (LangGraph / LlamaIndex / OpenAI Agents) and low-code (`agent.json`) | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/` dir): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-maestro-flow` | `.flow` files orchestrating RPA, agents, apps | Yes (`uip login`) | **Partial** — Studio Web by default; `uipath-platform` for Orchestrator |
| `uipath-platform` | Auth, Orchestrator resources, solution lifecycle (pack/publish/deploy), Integration Service, Test Manager | Yes (auth hub) | **Yes** — the deploy destination |
| `uipath-interact` | Inspect and interact with live desktop/browser UI: click, type, screenshot, inspect. For app launching, ad-hoc exploration, post-build verification. Does NOT author workflows or generate selectors — that's `uipath-rpa`. | No auth | **No** |
| `uipath-solution-design` | PDD→SDD architecture only. Always runs BEFORE this skill in PDD-driven flows. | N/A | **No** |

## Reference Navigation

| File | Purpose |
|------|---------|
| [PDD-driven Lane Guide](references/pdd-driven-lane-guide.md) | Lane A end-to-end — read SDD header, parse project list, derive tasks, write tasks.md, emit live tasks |
| [Non-PDD Lane Guide](references/non-pdd-lane-guide.md) | Lane B end-to-end — elicitation, project-type inference, filesystem detection, UI batch, write plan.md |
| [Multi-skill Patterns Guide](references/multi-skill-patterns-guide.md) | The 6 named multi-skill patterns (RPA build+deploy, Flow with missing resources, Build+verify UI, Agent with RPA tools, etc.). Used by both lanes. |
| [Plan and Tasks Format](references/plan-and-tasks-format.md) | Header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, TaskCreate mapping, anti-hallucination rule, quality rules |

## Anti-patterns

1. **Skipping the entry guard.** Always inspect the input first. A PDD silently treated as a generic doc produces a degraded plan and skips the dedicated SDD skill.
2. **Writing automation code or modifying the project.** Plans only. In explore-first Lane B mode, non-mutating `uip` discovery is allowed; that's the upper limit.
3. **Exceeding 5 `AskUserQuestion` calls.** If the elicitation can't fit, plan with best available info and note the assumption.
4. **Recommending a skill that contradicts filesystem signals.** `.flow` files → `uipath-maestro-flow`, not `uipath-rpa`.
5. **Asking the UI-targeting batch when the plan has no UI automation.** Pure data processing, API calls, agent-only, flow-only plans skip Step 4 entirely.
6. **Routing UI automation through `uipath-interact` for element discovery or selector work.** `uipath-rpa` is the sole workflow authoring skill. `uipath-interact` is only for live-app interaction and post-build verification.
7. **Describing specialist-internal flows in the plan.** Target-configuration procedures, OR registration, scaffolding pipelines, auth steps, pack/publish details, testing procedures — all owned by the specialist's own docs. Inlining creates drift.
8. **Saving a plan with placeholders** (TBD, TODO, as needed, similar to Task N).
9. **Asking the user to choose between XAML and C#.** Project type is inferred from the request; RPA workflows are XAML by default. Coded mode is set only when the user independently says "coded workflow", "C# workflow", or ".cs file".
10. **Surfacing C# as recommended for routine UI automation.** Form-fill, Type Into, Click, dropdown selection, Excel / email / file work — all bread-and-butter XAML. C# coded fallback is an internal `uipath-rpa` decision for individual subtasks, never a top-level recommendation from the planner.
11. **Adding a third option to the UI-targeting question.** Only two options exist: "I build it, you review it" (default) and "You indicate each element". Never invent a third "build it manually" option — a developer choosing manual authoring wouldn't be using a coding agent.
12. **Leaking internal jargon or implementation details into user-facing questions.** Never mention "snapshot", "hand-wire", "AutomationId", "selector candidate", "autonomous capture", "target configuration". Speak in plain developer language: "the live app", "Studio", "elements", "selectors", "inspect", "discover".
13. **Injecting domain or app names into question text.** Ask "What kind of application are we automating?" — not "What kind of HR application…". Domain lives in the plan header, not the questions.
14. **Routing new projects to `uipath-rpa-legacy`.** Legacy is for existing .NET Framework 4.6.1 projects only. New projects always go to `uipath-rpa` unless the user explicitly asks for legacy.
15. **Omitting the mandatory Testing task per generation skill.** Every generation skill in the plan gets a `Testing (MANDATORY)` task that routes to that skill's testing references. Never replace it with a `Validate:` sub-step. Never describe test-case authoring / data-driven testing / mock testing in the plan.
16. **Asking about test coverage depth.** Testing is always thorough. The implementation specialist can scope down at execution time if the user wants a quick MVP; the planner does not offer the option.
17. **Generating an SDD or copying SDD content into the plan.** SDD is owned by `uipath-solution-design`. The plan references SDD section paths in skill prompts but does not duplicate architecture content.
