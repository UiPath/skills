---
name: uipath-maestro-case
description: "[PREVIEW] Case Management authoring from sdd.md. Produces tasks.md plan, writes caseplan.json directly via per-plugin JSON recipes. For .xaml→uipath-rpa, .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

Builds UiPath Case Management definitions from `sdd.md`. Generates `tasks.md` plan, executes via `uip maestro case` CLI to produce `caseplan.json`.

**Scope:** new case from `sdd.md` only. Modifying existing case not supported (no remote fetch tooling).

## When to Use This Skill

- User provides `sdd.md` and wants Case Management project built
- User asks to create new case management project or definition
- User asks to generate implementation tasks from `sdd.md` or convert spec to plan
- User asks about case management JSON schema — nodes, edges, tasks, rules, SLA
- User wants to manage runtime case instances (list, pause, resume, cancel) — see [references/case-commands.md](references/case-commands.md)

**Do not use for:** `.xaml` → `uipath-rpa`. `.flow` → `uipath-maestro-flow`. Standalone agents/APIs/processes outside case context → corresponding UiPath skill.

## Critical Rules

1. **sdd.md is the sole input** — trust it as written. This skill does not validate or gap-fill `sdd.md`. If the file is ambiguous, use AskUserQuestion to clarify, do not infer silently.
2. **Always run `uip maestro case registry pull` before planning** — caches the registry at `~/.uipcli/case-resources/` so all subsequent discovery is local.
3. **Registry discovery is direct cache-file inspection, not CLI search.** `uip maestro case registry search` has known gaps (especially for action-apps). Read the `<type>-index.json` files directly. See [references/registry-discovery.md](references/registry-discovery.md).
4. **Always use `--output json`** on every `uip maestro case` read command whose output is parsed programmatically.
5. **Follow the plugin for every node type.** Every task, trigger, and condition variant has its own plugin under `references/plugins/`. Open the matching `planning.md` during planning and `impl-json.md` during execution. Do not guess JSON shapes from memory.
6. **`tasks.md` entries are declarative.** No `uip` CLI commands inside `tasks.md`. Each entry is parameters, IDs, and metadata only. The execution phase translates specs into CLI calls.
7. **One T-entry per sdd.md declaration — no omissions.** Every stage, edge, task, trigger, condition, and SLA rule declared in `sdd.md` gets its own T-numbered entry, even when the declared value looks like a "default" (e.g., condition rule-type `current-stage-entered` / `case-entered`, stage-exit type `exit-only`, `is-interrupting: false`, `runOnlyOnce: true`). Never group multiple items under one T-number. Never skip a declaration on the grounds that "the default behavior would already cover it" — if `sdd.md` wrote it down, `tasks.md` must emit a T-task for it.
8. **Always regenerate `tasks.md` from scratch** — never do incremental updates. Avoids stale state from previous runs.
9. **HARD STOP before execution.** After generating `tasks.md`, present it to the user and require explicit approval via **AskUserQuestion** (`Approve and proceed` / `Request changes`). Do not execute until approved.
10. **After approval, re-read `tasks.md` before executing.** `tasks.md` is the complete handoff artifact — all IDs, inputs, outputs, and references are captured there.
11. **Unresolved task resources produce skeleton tasks — never mock, never fabricate.** Keep the `<UNRESOLVED: ...>` marker on the `taskTypeId` / `type-id` / `connection-id` slot in `tasks.md`, and omit `inputs:` / `outputs:` from that task entry. At execution time, the task JSON node is written with `type` + `displayName` only (and structural fields like `id`, `elementId`, `isRequired`), with `data: {}` and no `taskTypeId` / `connectionId` keys — no variable bindings. Task-entry conditions and `selected-tasks-completed` rules still reference the skeleton's `TaskId`, so the workflow structure stays reviewable. The user attaches the real resource + bindings externally before runtime. See [references/skeleton-tasks.md](references/skeleton-tasks.md). Never fabricate a task-type-id or connection-id to "fill the gap".
12. **Persist every registry resolution to `registry-resolved.json`** with full detail: search query, all matched results, selected result, rationale. This is the debug audit trail.
13. **Cross-task references** use `"Stage Name"."Task Name".output_name` in planning and resolve to `=vars.<outputVarId>` at execution time by reading the source output's `var` field from caseplan.json. Every ref must point to a task already in `tasks.md` order. Discover output names via `uip maestro case tasks describe` — do not fabricate. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md) and [references/plugins/variables/io-binding/impl-json.md](references/plugins/variables/io-binding/impl-json.md).
14. **Expression prefixes are fixed:** `=metadata.`, `=js:`, `=vars.`, `=datafabric.`, `=bindings.`, `=orchestrator.JobAttachments`, `=response`, `=result`, `=Error`, `=jsonString:`. Plain strings without a prefix are literals, not expressions.
15. **Connector integration uses direct JSON write.** Planning discovers fields via `is resources describe` (activities) or `is triggers describe` (triggers), resolves references via `is resources execute list`, and writes resolved values to `tasks.md`. Implementation calls `get-connection` + `tasks describe` and writes task data directly to `caseplan.json`. See each plugin's `planning.md` + `impl-json.md` for the full workflow.
16. **Enrichable non-connector task types** (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`) get their `data.inputs[]` / `data.outputs[]` schema from `uip maestro case tasks describe --task-type-id <id>` and the resolved `taskTypeId` written into `data.context`. Connector variants write `data.typeId` + `data.connectionId` directly. See each plugin's `impl-json.md`.
17. **Every stage needs at least one inbound edge** or it will be orphaned. The Trigger node written by the triggers plugin at T02 is the entry point for all single-trigger cases.
18. **One task per lane (UI layout only).** Each task occupies its own lane index within a stage. In `caseplan.json`, lanes are the outer index of `stageNode.data.tasks[laneIndex][]` — increment `laneIndex` per task within a stage. Lane is a rendering coordinate for the FE — it does not affect execution. Parallelism and sequencing are controlled entirely by task-entry conditions.
19. **User questions use AskUserQuestion with a "Something else" escape hatch.** Whenever a decision has finite enumerable choices (≤5), present a dropdown with those options AND "Something else" as the last option. For open-ended inputs (e.g., `--every 1h` vs `2h` vs `1d`), use a direct prompt. Never force a false choice. **Exception:** the Phase 2a→2b hard stop (Rule #24) is a strict gate — its prompts (`Publish for review` / `Skip publish and continue` / `Abort`, and `Continue to phase 2b` / `Abort`) use a closed option set with no escape hatch. The equivalent of "Something else" at that boundary is `Abort` followed by manual edits to `caseplan.json`.
20. **Validate after build, not during.** Run `uip maestro case validate` only after all stages, edges, tasks, conditions, and SLA are added. Intermediate states are expected to be invalid. Retry up to 3× on failure; on the 3rd failure, halt and ask the user with options: `Retry with fix` / `Pause for manual edit` / `Abort`.
21. **Never run `uip maestro case debug` automatically** — it executes the case for real (sends emails, posts messages, calls APIs). Only run on explicit user consent.
22. **Edit `content/*.json` only** — `content/*.bpmn` is auto-generated and will be overwritten.
23. **One T-entry per Read → modify → Write cycle.** Apply each T-entry incrementally: Read `caseplan.json`, mutate for that single T-entry, Write back, then re-Read for the next T-entry. Do NOT compose a large in-memory JSON covering multiple stages/edges/tasks/conditions and flush once — that hides intermediate state, inflates diffs, breaks review, and loses rollback granularity. Batched single-file writes are allowed only within a single T-entry's own mutation (e.g., one stage node + its required render fields).
24. **HARD STOP between Phase 2a (skeleton) and Phase 2b (detail) — unconditional.** After Phase 2a builds the structural skeleton, run regular `uip maestro case validate` (no `--mode` flag) for informational output only — do NOT halt on errors/warnings. Phase 2a state is expected to be invalid: unbound required input values, missing condition rules, missing SLA. Surface counts in the hard-stop summary; the user decides whether to proceed. Then present the hard-stop **AskUserQuestion** prompt. This prompt is MANDATORY every run — never skip it for auto mode, non-interactive mode, upfront user consent, or implied prior approval. If the harness forbids interactive prompts, halt with a clear error instead of proceeding — silent skip is a bug. Phase 2a does NOT bind task input values, does NOT call `is resources describe` for connector tasks, does NOT write conditions, and does NOT write SLA — all deferred to Phase 2b. Phase 2b must re-read `tasks.md` AND `caseplan.json` before mutating. Full contract (prompt options, summary content, publish branch, abort cleanup, re-entry protocol) in [`references/phased-execution.md`](references/phased-execution.md).

## Workflow

Three hard stops: **Planning** (sdd.md → tasks.md) → approve → **Phase 2a** (skeleton) → publish-for-review stop → **Phase 2b** (detail) → post-build.

### Phase 1 — Planning

Read [references/planning.md](references/planning.md). Produces:

- `tasks/tasks.md` — T-numbered entries (stages → edges → tasks → conditions → SLA)
- `tasks/registry-resolved.json` — audit trail

HARD STOP: AskUserQuestion approval. Loop on `Request changes`.

### Phase 2a — Skeleton build

Read [references/implementation.md](references/implementation.md) + [references/phased-execution.md](references/phased-execution.md). Builds structural shape only:

1. Solution + project + root case (Step 6)
2. Global variables + arguments (Step 6.1)
3. Stages (Step 7), edges (Step 8), triggers
4. Tasks — shape only (Step 9): non-connector with full `data.inputs[]` schema + empty values; connector with `type-id` + `connection-id` only (no `is describe`); unresolved as skeletons per Rule 7
5. Informational validate (Step 9.5.1) — do NOT halt on errors/warnings
6. **HARD STOP** (Step 9.5.2–9.5.5): `Publish for review` / `Skip publish and continue` / `Abort`. On `Publish`: `uip solution upload`, print DesignerUrl, AskUserQuestion: `Continue to phase 2b` / `Abort`. On `Abort`: dump `build-issues.md`, exit (no cleanup).

### Phase 2b — Detail build

Re-read `tasks.md` AND `caseplan.json` (Step 9.6). Then:

1. Connector schema + defaults (Step 9.7) — `is resources/triggers describe`
2. I/O binding all task classes (Step 9.8) — per [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md)
3. Conditions all 4 scopes (Step 10)
4. SLA + escalation (Step 11)
5. Full validate (Step 12). Retry up to 3×; on 3rd failure AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`
6. Dump `build-issues.md` (Step 12.1)
7. Post-build loop (Step 13) — AskUserQuestion until `Done`

## Reference Navigation

| I need to... | Read |
|---|---|
| **Plan tasks from sdd.md** | [references/planning.md](references/planning.md) |
| **Execute tasks.md into a case** | [references/implementation.md](references/implementation.md) |
| **Phase 2a / 2b split + hard stop contract** | [references/phased-execution.md](references/phased-execution.md) |
| **Edit caseplan.json directly** | [references/case-editing-operations.md](references/case-editing-operations.md) |
| **Understand the case JSON schema** | [references/case-schema.md](references/case-schema.md) |
| **Know surviving CLI commands (registry, validate, debug, runtime)** | [references/case-commands.md](references/case-commands.md) |
| **Resolve task types from registry** | [references/registry-discovery.md](references/registry-discovery.md) |
| **Wire inputs/outputs and cross-task refs** | [references/bindings-and-expressions.md](references/bindings-and-expressions.md) |
| **Configure a connector activity / trigger / event** | [references/connector-integration.md](references/connector-integration.md) |
| **Handle unresolved resources (skeleton tasks)** | [references/skeleton-tasks.md](references/skeleton-tasks.md) |
| **Create the root case (T01)** | [references/plugins/case/planning.md](references/plugins/case/planning.md) + [`impl-json.md`](references/plugins/case/impl-json.md) |
| **Create a stage (regular or exception)** | [references/plugins/stages/planning.md](references/plugins/stages/planning.md) + [`impl-json.md`](references/plugins/stages/impl-json.md) |
| **Connect nodes with edges** | [references/plugins/edges/planning.md](references/plugins/edges/planning.md) + [`impl-json.md`](references/plugins/edges/impl-json.md) |
| **Configure SLA (default, conditional, escalation)** | [references/plugins/sla/planning.md](references/plugins/sla/planning.md) + [`impl-json.md`](references/plugins/sla/impl-json.md) |
| **Declare global variables and arguments** | [references/plugins/variables/global-vars/planning.md](references/plugins/variables/global-vars/planning.md) + [`impl-json.md`](references/plugins/variables/global-vars/impl-json.md) |
| **Wire task inputs/outputs (I/O binding)** | [references/plugins/variables/io-binding/planning.md](references/plugins/variables/io-binding/planning.md) + [`impl-json.md`](references/plugins/variables/io-binding/impl-json.md) |
| **Add a specific task type** | `references/plugins/tasks/<type>/planning.md` + `impl-json.md` |
| **Add a specific trigger type** | `references/plugins/triggers/<type>/planning.md` + `impl-json.md` |
| **Add a specific condition scope** | `references/plugins/conditions/<scope>/planning.md` + `impl-json.md` |

### Plugin Index

**Structural:**

| Plugin | Scope |
|--------|-------|
| [case](references/plugins/case/planning.md) | Root case (T01) |
| [stages](references/plugins/stages/planning.md) | Regular and exception stages |
| [edges](references/plugins/edges/planning.md) | Edges between Trigger/Stage nodes |
| [sla](references/plugins/sla/planning.md) | Default SLA, conditional rules, escalation |
| [global-vars](references/plugins/variables/global-vars/planning.md) | Case variables and arguments |
| [io-binding](references/plugins/variables/io-binding/planning.md) | Task I/O wiring, cross-task refs |
| [logging](references/plugins/logging/impl-json.md) | Shared issue log |

**Tasks** (`references/plugins/tasks/`):

| Plugin | sdd.md component type |
|--------|-----------------------|
| [process](references/plugins/tasks/process/planning.md) | PROCESS, AGENTIC_PROCESS |
| [agent](references/plugins/tasks/agent/planning.md) | AGENT |
| [rpa](references/plugins/tasks/rpa/planning.md) | RPA |
| [action](references/plugins/tasks/action/planning.md) | HITL |
| [api-workflow](references/plugins/tasks/api-workflow/planning.md) | API_WORKFLOW |
| [case-management](references/plugins/tasks/case-management/planning.md) | CASE_MANAGEMENT |
| [connector-activity](references/plugins/tasks/connector-activity/planning.md) | CONNECTOR_ACTIVITY |
| [connector-trigger](references/plugins/tasks/connector-trigger/planning.md) | CONNECTOR_TRIGGER |
| [wait-for-timer](references/plugins/tasks/wait-for-timer/planning.md) | TIMER (in-stage) |

**Triggers** (`references/plugins/triggers/`):

| Plugin | When |
|--------|------|
| [manual](references/plugins/triggers/manual/planning.md) | User-initiated start |
| [timer](references/plugins/triggers/timer/planning.md) | Scheduled start |
| [event](references/plugins/triggers/event/planning.md) | External connector event |

**Conditions** (`references/plugins/conditions/`):

| Plugin | Scope |
|--------|-------|
| [stage-entry-conditions](references/plugins/conditions/stage-entry-conditions/planning.md) | Stage entered |
| [stage-exit-conditions](references/plugins/conditions/stage-exit-conditions/planning.md) | Stage exits |
| [task-entry-conditions](references/plugins/conditions/task-entry-conditions/planning.md) | Task starts |
| [case-exit-conditions](references/plugins/conditions/case-exit-conditions/planning.md) | Case completes/exits |

## Anti-patterns

- **Do NOT put `uip maestro case ...` CLI commands inside `tasks.md`.** `tasks.md` is declarative only — causes double-execution or mis-parsing.
- **Do NOT incrementally update an existing `tasks.md`.** Always regenerate from scratch.
- **Do NOT skip registry lookups** based on assumptions like "this type is not discoverable." Always search the cache files first.
- **Do NOT group multiple sdd.md tasks under one T-number.** Each task, trigger, edge, or condition gets its own numbered entry.
- **Do NOT fabricate input or output names in cross-task references.** Run `uip maestro case tasks describe` to discover actual names. A fabricated name becomes a silent runtime null.
- **Do NOT fabricate expression syntax for conditional SLA rules.** Describe the condition in natural language; the execution phase determines the exact expression form.
- **Do NOT fabricate task-type-ids or connection-ids.** When a resource is unresolved, write a skeleton task: JSON node with `type` + `displayName`, `data: {}`, no `taskTypeId` / `connectionId` keys. Skip input/output bindings entirely — skeletons have no input schema. See [references/skeleton-tasks.md](references/skeleton-tasks.md).
- **Do NOT invoke other skills automatically.** If the case needs a process, agent, or action that doesn't exist, emit a skeleton task (per Rule #11) and list the missing resources in the completion report so the user can register them externally. On-demand resource creation is a future milestone, not today.
- **Do NOT place multiple tasks in the same lane.** The FE renders same-lane tasks stacked in one column, which is unreadable for non-trivial stages. Give each task its own lane index in `stageNode.data.tasks[laneIndex][]`. Lane carries no execution semantics — it's layout only.
- **Do NOT edit `content/*.bpmn` files.** They are auto-generated and will be overwritten.
- **Do NOT run `uip maestro case debug` automatically.** It executes the case for real — sends emails, posts messages, calls APIs. Only run on explicit user consent.
- **Do NOT validate after each individual T-entry.** Intermediate states are expected to be invalid. Run `uip maestro case validate` once at end of Phase 2a (informational) and once at end of Phase 2b (authoritative).
- **Do NOT batch multiple T-entries into one JSON write.** Every T-entry gets its own Read → mutate → Write cycle (Rule #23). Composing a large in-memory JSON spanning many stages/edges/tasks and flushing once hides intermediate state and breaks review granularity.
- **Do NOT skip the Phase 2a → 2b hard stop for any reason.** Auto mode, non-interactive mode, prior blanket approval, and a clean Phase 2a all still require the AskUserQuestion prompt (Rule #24). Halt with an explicit error if the harness refuses the prompt.
- **Do NOT halt on Phase 2a validate errors/warnings.** The validate call at end of Phase 2a is informational — unbound inputs, missing conditions, and missing SLA are expected (they arrive in Phase 2b). Surface counts in the hard-stop summary; let the user decide.
- **Do NOT mutate `caseplan.json` (or sibling JSON files) via subprocess scripts.** Use Claude's Read + Write/Edit tools only — no `python`, `node`, `jq`, `sed`, `awk`, or helper scripts that open/parse/modify/save the file. Bash subprocesses remain OK for stdout-only helpers (e.g., `node -e "...console.log(randomId)"`), CLI metadata fetches, validate, debug, and solution scaffold/upload. See [references/case-editing-operations.md § Tool usage](references/case-editing-operations.md#tool-usage--mandatory).

## Key Concepts

### Local vs cloud commands

`caseplan.json` mutations are direct file edits (Read + Write/Edit). CLI is used only for the operations below:

| Commands | What they do | Auth needed |
|----------|--------------|-------------|
| `uip solution new`, `uip solution project add`, `uip solution upload` | Solution scaffold + Studio Web upload | Yes (for `upload`) |
| `uip maestro case registry pull/list/search`, `get-connector`, `get-connection`, `tasks describe`, `is resources/triggers describe` | Registry + metadata discovery (read-only) | Yes (for `pull`) |
| `uip maestro case validate` | Validate `caseplan.json` | No |
| `uip maestro case instance`, `processes`, `incidents`, `process run`, `job traces`, `debug` | Query/manage live Orchestrator state | Yes |

### CLI output format

All `uip maestro case` commands return:

```json
{ "Result": "Success", "Code": "...", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Always pass `--output json` when the output is parsed.

## Completion Output

When the build completes, report to the user:

1. **File path** of `caseplan.json`
2. **What was built** — summary of stages, edges, tasks, conditions, SLA
3. **Validation status** — whether `uip maestro case validate` passes (or remaining errors)
4. **Skeleton tasks + unresolved resources** — list every skeleton task created (TaskId, type, display-name, stage) alongside the external resource the user must register to upgrade it (task-type-id / connection-id). Include the wiring-notes from `tasks.md` so the user knows which inputs/outputs to attach. See [references/skeleton-tasks.md](references/skeleton-tasks.md) for the upgrade procedure.
5. **Missing connections** — any connector tasks needing IS connections that don't exist yet
6. **Next step** — **AskUserQuestion** dropdown (per Rule #19):
   - `Run debug session` → ask for explicit consent, then run `uip maestro case debug`
   - `Publish to Studio Web` → `uip solution upload <SolutionDir>`
   - `Done`
   - `Something else`

Do not take any of these actions automatically — wait for explicit selection.

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
