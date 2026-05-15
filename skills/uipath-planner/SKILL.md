---
name: uipath-planner
description: "UiPath task planner — reads SDDs from uipath-solution or elicits non-PDD requests, derives multi-skill task lists, emits live TaskCreate calls. Detects project type (.cs, .xaml, .flow, .bpmn, .py). For PDDs→uipath-solution first."
when_to_use: "User makes a non-trivial UiPath request — 'build a UiPath solution for X', 'set up a process from scratch', 'help me plan this' — OR provides an SDD path. Skip when project type and scope are already clear for a single-skill task — invoke the specialist directly."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# UiPath Task Planner

Your job is to **derive task lists, route to specialists, and emit live tasks** — never execute the work yourself.

The planner has two lanes:

- **Lane A — PDD-driven.** Triggered when the input is an SDD with a `## Planner Handoff` header. Reads the SDD, derives tasks per the project list, writes `<process>-tasks.md`, emits live `TaskCreate` calls. Zero or one user prompt. See [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).
- **Lane B — Non-PDD.** Triggered when there's no SDD. Elicits preferences via a batched `AskUserQuestion`, detects project type, multi-skill patterns or filesystem signals, writes `<feature>.md`, emits live tasks. Typically 0–3 user prompts (5-call hard cap). See [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

The lane is decided by the **Entry Guard** below.

## When to Use This Skill

- The request is **non-trivial** — multi-step, multi-skill, UI automation, or unclear scope
- The request is **ambiguous** — no single specialist skill clearly matches
- The user asks "what can I build?" or needs help choosing a project type
- The user provides an SDD path — Lane A runs

Skip this planner for simple, well-defined single-skill tasks (e.g., "create a workflow that sends an email") — load the specialist directly.

## Critical Rules

1. **Plan only — never execute the work yourself.** Do NOT write automation code (XAML, C#, Python, JSON) or create project files. Plan / tasks files and live `TaskCreate` calls are the only outputs you produce.
2. **For PDDs, hard-block and redirect to `uipath-solution`.** A PDD (PDF, docx, or markdown describing process steps + applications + exceptions) does NOT belong in this skill. The dedicated PDD→SDD skill produces a much better deliverable. The only escape is the user explicitly saying "skip SDD".
3. **Never exceed 5 `AskUserQuestion` calls in any planning session.** Each call is one user-facing prompt; batch related questions (e.g., the Step 4 UI elicitation in Lane B batches App type, Targeting approach, App state into one call). If you cannot fit the elicitation in 5 calls, plan with best available info and note the assumption. Lane A typically uses 0–2 calls.
4. **Always include a mandatory Testing task per generation skill** in the plan. Testing is non-negotiable — happy path + edge cases + error scenarios + e2e for Master Projects. The Testing task routes to the specialist's testing references and does NOT describe the testing procedure inline.
5. **Route — do not redescribe.** The plan says WHICH skill to load and IN WHAT ORDER. It does NOT describe specialist-internal flows (target configuration, OR registration, XAML authoring pipelines, auth flows, testing procedures). Each specialist's docs own those details.

## Entry Guard

When the planner is invoked, run this guard before anything else.

```
1. Did the user reference a document path?
   - No → Lane B (non-PDD elicitation)

2. The path resolves to a file. Read its first ~50 lines.
   - File contains the heading `## Planner Handoff` OR the HTML-comment marker `<!-- planner-handoff:v1 -->` → Lane A (read SDD, derive tasks). Either signal is sufficient — they are redundant on purpose so a renamed heading does not silently break detection.

3. Otherwise (no marker, or unparseable / binary file like .pdf / .docx):
   ask via AskUserQuestion:

   > What is the document at <path>?
   > 1. Solution Design Document (SDD) — proceed with task generation (Lane A, hand-written SDD)
   > 2. Process Design Document (PDD) — load uipath-solution first
   > 3. Other context — note its existence; proceed with non-PDD elicitation (Lane B)

4. Based on user's choice:
   - SDD → Lane A. Try to find the Planner Handoff header; if missing, proceed with safe defaults
     (interactive autonomy, single-product scope) and log a one-line warning.
   - PDD → HARD BLOCK with this message:

     > The document at <path> is a Process Design Document. UiPath has a dedicated skill
     > for PDD→SDD generation that produces a much better deliverable: uipath-solution.
     > Load it with this PDD path; it will produce an SDD that I can then use to generate
     > the task list.
     >
     > If you've already considered the SDD path and want a lightweight plan from this PDD
     > anyway, tell me "skip SDD" and I'll proceed with degraded inline reading (Lane B + PDD
     > as context).

   - Other context → Lane B, with the document path noted in plan header.
```

The `## Planner Handoff` heading **and** the `<!-- planner-handoff:v1 -->` marker are the load-bearing detection contract — `uipath-solution` writes both deterministically, this skill detects either. Templates ship with both; either alone is enough to take Lane A. Do not pattern-match on filename or extension; those are unreliable.

## Lane A — PDD-driven (summary)

When triggered: SDD detected at entry guard.

1. Read the SDD's `## Planner Handoff` header (6 fields: Execution autonomy, SDD scope, Project list section, Tasks file, Generated by, Generation date).
2. If `<process>-tasks.md` already exists, ask `continue / regenerate` (1 prompt). Regenerate preserves completed work via task identity matching — see [plan-and-tasks-format.md → Regenerate logic](references/plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).
3. Parse the SDD project list section. Pick the multi-skill pattern.
4. Ask the Step 4 UI batch (3 questions, 1 call) only if the SDD's Application Inventory section lists UI applications and the answers aren't already resolved from context.
5. Derive tasks. Write `<process>-tasks.md`.
6. If `Execution autonomy: interactive` → `EnterPlanMode` for review. If `autonomous` → emit live tasks directly.
7. Emit `TaskCreate` calls + `addBlockedBy` edges. Hand off.

Full procedure: [pdd-driven-lane-guide.md](references/pdd-driven-lane-guide.md).

## Lane B — Non-PDD (summary)

When triggered: no SDD; user described a task or asked for help planning one.

1. Step 1 — batched elicitation: bundle Q1 (generation approach) + Q2 (execution autonomy) + Q3 (project-type fallback, only when project type is vague) + Q5 (Solution scope, only when plan loads `uipath-maestro-flow`) into **one** `AskUserQuestion` call. Drop any question already resolved from context; if all resolve, skip the call entirely.
2. Step 2 — detect multi-skill patterns; emit multi-skill plan if applicable. See [multi-skill-patterns-guide.md](references/multi-skill-patterns-guide.md).
3. Step 3 — filesystem detection for single-skill plans.
4. Step 4 UI batch — only when plan includes UI automation in `uipath-rpa` (one batched `AskUserQuestion` for App type / Targeting approach / App state).
5. Write `YYYY-MM-DD-<feature>.md` to `docs/plans/` (project) or `./plans/` (no project).
6. If explore-first → `EnterPlanMode`. If simultaneous → emit plan as text + live tasks.

Full procedure: [non-pdd-lane-guide.md](references/non-pdd-lane-guide.md).

## RPA skill routing

All RPA work — modern and legacy — routes to `uipath-rpa`. The skill internally switches to its **Legacy mode** when `project.json` has `"targetFramework": "Legacy"` (or no `targetFramework` field).

| Signal | Route to |
|---|---|
| `project.json` has `"targetFramework": "Legacy"` or no `targetFramework` field | `uipath-rpa` (legacy mode — note in plan: `Mode: Legacy (.NET 4.6.1)`) |
| `project.json` has any other `targetFramework` (e.g., `"Portable"`, `"Windows"`) | `uipath-rpa` |
| No existing project | `uipath-rpa` (default for all new projects; modern, not legacy) |
| macOS host | `uipath-rpa` — cross-platform target only (Windows target not available on macOS) |
| Windows host | `uipath-rpa` — user can choose Windows or cross-platform target |

**Rules:**

1. Never recommend legacy mode for new projects unless the user explicitly requests legacy (.NET Framework 4.6.1, classic activities). For new projects, default to modern `uipath-rpa`.
2. On macOS, only cross-platform automation is supported — always route to modern `uipath-rpa`.

## Skill capability map

High-level view of what each specialist owns. **Do not describe internal flows of any specialist in your plan** — each skill documents its own procedures and will drift out of sync if duplicated here.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | RPA workflows — modern (XAML + C# coded) and legacy (.NET 4.6.1, classic XAML). Create, edit, build, run, debug. Owns **all** UI automation authoring end-to-end, including live-app exploration and probing. Skill auto-detects legacy via `targetFramework: "Legacy"`. | No (relies on Studio) | **No** — defer to `uipath-solution` for `.uipx` multi-project, `uipath-platform` for single non-solution packages |
| `uipath-agents` | AI agents — code-based (LangGraph / LlamaIndex / OpenAI Agents) and low-code (`agent.json`) | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/` dir): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-maestro-flow` | `.flow` files orchestrating RPA, agents, apps | Yes (`uip login`) | **Partial** — follows plan `Solution scope` (SW or local); `uipath-platform` for Orchestrator |
| `uipath-platform` | Auth (`uip login`), Orchestrator (folders, processes, jobs, machines, users, roles), resources (assets, queues, storage buckets + bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), traces, licensing | Yes (auth hub) | **Yes** — for non-solution single packages and Orchestrator-side post-deploy ops |
| `uipath-solution` | PDD→SDD architecture authoring AND `uip solution` lifecycle (init, pack, publish, deploy, activate). Runs in PDD-driven flows as the first skill (design) and again as the final skill (deploy of `.uipx` solutions). | Yes (`uip login` for ops half) | **Yes** — for multi-project Solution (`.uipx`) deploys |

## Reference Navigation

| File | Purpose |
|------|---------|
| [PDD-driven Lane Guide](references/pdd-driven-lane-guide.md) | Lane A end-to-end — read SDD header, parse project list, derive tasks, write tasks.md, emit live tasks |
| [Non-PDD Lane Guide](references/non-pdd-lane-guide.md) | Lane B end-to-end — elicitation, project-type inference, filesystem detection, UI batch, write plan.md |
| [Multi-skill Patterns Guide](references/multi-skill-patterns-guide.md) | The named multi-skill patterns (RPA build+deploy, Flow with local/deployed resources, Agent with RPA tools, etc.). Used by both lanes. |
| [Plan and Tasks Format](references/plan-and-tasks-format.md) | Header schema, task row schema, identity tuple, status states, regenerate-with-preservation algorithm, TaskCreate mapping, anti-hallucination rule, quality rules |

## Anti-patterns

1. **Skipping the entry guard.** Always inspect the input first. A PDD silently treated as a generic doc produces a degraded plan and skips the dedicated SDD skill.
2. **Writing automation code or modifying the project.** Plans only. In explore-first Lane B mode, non-mutating `uip` discovery is allowed; that's the upper limit.
3. **Exceeding 5 `AskUserQuestion` calls.** If the elicitation can't fit, plan with best available info and note the assumption.
4. **Recommending a skill that contradicts filesystem signals.** `.flow` files → `uipath-maestro-flow`, not `uipath-rpa`.
5. **Asking the UI-targeting batch when the plan has no UI automation.** Pure data processing, API calls, agent-only, flow-only plans skip Step 4 entirely.
6. **Describing specialist-internal flows in the plan.** Target-configuration procedures, OR registration, scaffolding pipelines, auth steps, pack/publish details, testing procedures — all owned by the specialist's own docs. Inlining creates drift.
7. **Saving a plan with placeholders** (TBD, TODO, as needed, similar to Task N).
8. **Asking the user to choose between XAML and C#.** Project type is inferred from the request; RPA workflows are XAML by default. Coded mode is set only when the user independently says "coded workflow", "C# workflow", or ".cs file".
9. **Surfacing C# as recommended for routine UI automation.** Form-fill, Type Into, Click, dropdown selection, Excel / email / file work — all bread-and-butter XAML. C# coded fallback is an internal `uipath-rpa` decision for individual subtasks, never a top-level recommendation from the planner.
10. **Adding a third option to the UI-targeting question.** Only two options exist: "I build it, you review it" (default) and "You indicate each element". Never invent a third "build it manually" option — a developer choosing manual authoring wouldn't be using a coding agent.
11. **Leaking internal jargon or implementation details into user-facing questions.** Never mention "snapshot", "hand-wire", "AutomationId", "selector candidate", "autonomous capture", "target configuration". Speak in plain developer language: "the live app", "Studio", "elements", "selectors", "inspect", "discover".
12. **Injecting domain or app names into question text.** Ask "What kind of application are we automating?" — not "What kind of HR application…". Domain lives in the plan header, not the questions.
13. **Recommending legacy mode for new projects.** Legacy mode in `uipath-rpa` is for existing .NET Framework 4.6.1 projects only. New projects always default to modern `uipath-rpa` unless the user explicitly asks for legacy.
14. **Omitting the mandatory Testing task per generation skill.** Every generation skill in the plan gets a `Testing (MANDATORY)` task that routes to that skill's testing references. Never replace it with a `Validate:` sub-step. Never describe test-case authoring / data-driven testing / mock testing in the plan.
15. **Asking about test coverage depth.** Testing is always thorough. The implementation specialist can scope down at execution time if the user wants a quick MVP; the planner does not offer the option.
16. **Omitting `Execution autonomy` from the plan header, or leaving `Stop conditions` empty when autonomy is `autonomous`.** Downstream specialists rely on both to decide whether to interrupt. Populate `Stop conditions` with the hard blockers realistic for this specific plan (auth, app state, element-capture limits, missing resources) — do not leave a generic placeholder.
17. **Generating an SDD or copying SDD content into the plan.** SDD is owned by `uipath-solution`. The plan references SDD section paths in skill prompts but does not duplicate architecture content.
18. **Asking the user what the planner / library / filesystem can already answer.** Project type is resolved by explicit naming, keyword signals, and filesystem detection before any prompt fires. Skill capability is fixed in the capability map — never ask "which skill should I use". Existence of a `project.json`, `.flow`, `.uipath/`, or `pyproject.toml` is observable. Default first; ask only when no safe default applies. A user prompt is the most expensive resource the planner has — spend it on decisions only the user can make.
