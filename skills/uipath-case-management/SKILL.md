---
name: uipath-case-management
description: "[PREVIEW] Case Management authoring from sdd.md. Produces tasks.md plan, executes uip maestro case CLI to build caseplan.json. For .xaml→uipath-rpa, .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

End-to-end guide for creating UiPath Case Management definitions. Takes a design document (`sdd.md`), generates a reviewable task plan (`tasks.md`), and executes the plan via the `uip maestro case` CLI to produce `caseplan.json`.

**Scope for this milestone:** creating a **new** case from `sdd.md`. Modifying an existing case is not supported — it requires remote fetch tooling that does not exist today.

## When to Use This Skill

- User provides an `sdd.md` and wants a Case Management project built from it
- User asks to create a new case management project or definition
- User asks to generate implementation tasks from an `sdd.md` or convert a spec into a plan
- User asks about the case management JSON schema — nodes, edges, tasks, rules, SLA
- User wants to manage runtime case instances (list, pause, resume, cancel) — see [references/case-commands.md](references/case-commands.md)

**Do not use this skill for:**
- `.xaml` workflows → use `uipath-rpa`
- `.flow` files → use `uipath-maestro-flow`
- Standalone agents, APIs, or processes outside a case context → use the corresponding UiPath skill

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
11. **Unresolved task resources produce skeleton tasks — never mock, never fabricate.** Keep the `<UNRESOLVED: ...>` marker on the `taskTypeId` / `type-id` / `connection-id` slot in `tasks.md`, and omit `inputs:` / `outputs:` from that task entry. At execution time, the task is written as a skeleton node in `caseplan.json` — structural fields only, no task-type-id, no connection-id, no variable bindings. Task-entry conditions and `selected-tasks-completed` rules still reference the skeleton's `TaskId`, so the workflow structure stays reviewable. The user attaches the real resource + bindings externally before runtime. See [references/skeleton-tasks.md](references/skeleton-tasks.md) for exact JSON shape. Never fabricate a task-type-id or connection-id to "fill the gap".
12. **Persist every registry resolution to `registry-resolved.json`** with full detail: search query, all matched results, selected result, rationale. This is the debug audit trail.
13. **Cross-task references** use `"Stage Name"."Task Name".output_name` in planning and resolve to `=vars.<outputVarId>` at execution time by reading the source output's `var` field from caseplan.json. Every ref must point to a task already in `tasks.md` order. Discover output names via `uip maestro case tasks describe` — do not fabricate. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md) and [references/plugins/variables/io-binding/impl-json.md](references/plugins/variables/io-binding/impl-json.md).
14. **Expression prefixes are fixed:** `=metadata.`, `=js:`, `=vars.`, `=datafabric.`, `=bindings.`, `=orchestrator.JobAttachments`, `=response`, `=result`, `=Error`, `=jsonString:`. Plain strings without a prefix are literals, not expressions.
15. **Connector integration uses direct JSON write.** Planning discovers fields via `is resources describe` (activities) or `is triggers describe` (triggers), resolves references via `is resources execute list`, and writes resolved values to `tasks.md`. Implementation calls `get-connection` + `tasks describe` and writes task data directly to `caseplan.json`. See each plugin's `planning.md` + `impl-json.md` for the full workflow.
16. **Enrichable non-connector task types** (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`) pass `--task-type-id` on `tasks add` to auto-populate inputs/outputs. Connector variants use `tasks add-connector` with `--type-id` + `--connection-id` instead.
17. **Every stage needs at least one inbound edge** or it will be orphaned. The Trigger node created automatically by `cases add` is the entry point for all single-trigger cases.
18. **One task per lane (UI layout only).** Pass `--lane <n>` on every `tasks add` / `tasks add-connector`, incrementing `n` per task within a stage. Lane is a rendering coordinate for the FE — it does not affect execution. Parallelism and sequencing are controlled entirely by task-entry conditions.
19. **User questions use AskUserQuestion with a "Something else" escape hatch.** Whenever a decision has finite enumerable choices (≤5), present a dropdown with those options AND "Something else" as the last option. For open-ended inputs (e.g., `1h` vs `2h` vs `1d`), use a direct prompt. Never force a false choice. **Exception:** the Phase 2a→2b hard stop (Rule #25) is a strict gate — its prompts (`Publish for review` / `Skip publish and continue` / `Abort`, and `Continue to phase 2b` / `Abort`) use a closed option set with no escape hatch. The equivalent of "Something else" at that boundary is `Abort` followed by manual edits to `caseplan.json`.
20. **Validate after build, not during.** Run `uip maestro case validate` only after all stages, edges, tasks, conditions, and SLA are added. Intermediate states are expected to be invalid. Retry up to 3× on failure; on the 3rd failure, halt and ask the user with options: `Retry with fix` / `Pause for manual edit` / `Abort`.
21. **Never run `uip maestro case debug` automatically** — it executes the case for real (sends emails, posts messages, calls APIs). Only run on explicit user consent.
22. **Always run `uip solution resource refresh` before `uip solution upload` or `uip maestro case debug`** — syncs connection resources from `bindings_v2.json` so Studio Web can resolve connector dependencies.
22. **Edit `content/*.json` only** — `content/*.bpmn` is auto-generated and will be overwritten.
23. **Execute CLI commands sequentially.** No parallel execution — each command may depend on IDs returned by the previous one.
24. **Never create `caseplan.json` in one shot — mutate incrementally, one category per Read → modify → Write cycle.** Categories: stages, edges, triggers, tasks, conditions (per scope), SLA, variables. One cycle per category — Read, apply every T-entry in that category, Write, re-Read before the next category. Do NOT compose a monolithic in-memory JSON covering multiple categories and flush once — that hides intermediate state and breaks per-category rollback. **Prefer the `Edit` tool over Read+Write** when a mutation is a narrowly-scoped, unambiguous single-field change (e.g., binding a task input `value` in Phase 2b) — Edit's tool-call shows the exact diff and avoids the full-file Read cost. Use Read+Write when the mutation is structural (new node, new edge, new condition array) or when Edit's `old_string` can't be made unique.
25. **HARD STOP between Phase 2a (skeleton) and Phase 2b (detail) — unconditional.** After Phase 2a builds the structural skeleton, run regular `uip maestro case validate` (no `--mode` flag) for informational output only — do NOT halt on errors/warnings. Phase 2a state is expected to be invalid: unbound required input values, missing condition rules, missing SLA. Surface counts in the hard-stop summary; the user decides whether to proceed. Then present the hard-stop **AskUserQuestion** prompt. This prompt is MANDATORY every run — never skip it for auto mode, non-interactive mode, upfront user consent, or implied prior approval. If the harness forbids interactive prompts, halt with a clear error instead of proceeding — silent skip is a bug. Phase 2a does NOT bind task input values, does NOT call `is resources describe` for connector tasks, does NOT write conditions, and does NOT write SLA — all deferred to Phase 2b. Phase 2b must re-read `tasks.md` AND `caseplan.json` before mutating. Full contract (prompt options, summary content, publish branch, abort cleanup, re-entry protocol) in [`references/phased-execution.md`](references/phased-execution.md).

## Workflow

Three hard stops: **Planning** (sdd.md → tasks.md) → approve → **Phase 2a** (skeleton) → publish-for-review stop → **Phase 2b** (detail) → post-build stop.

### Phase 1 — Planning (sdd.md → tasks.md)

**Read [references/planning.md](references/planning.md)** for the full procedure. Produces:

1. `tasks/tasks.md` — declarative task plan with T-numbered entries (stages → edges → tasks → conditions → SLA)
2. `tasks/registry-resolved.json` — full audit trail of registry lookups

Present `tasks.md` to the user for approval. **Do NOT proceed until the user explicitly approves.**

### Phase 2a — Skeleton build (tasks.md → structural caseplan.json)

**Read [references/implementation.md](references/implementation.md) + [references/phased-execution.md](references/phased-execution.md).** Builds structural shape only:

1. Solution + project + root case (Step 6)
2. Global variables + arguments (Step 6.1)
3. Stages (Step 7)
4. Edges (Step 8)
5. Triggers (full)
6. Tasks — shape only (Step 9):
   - Non-connector resolved: full `data.inputs[]` schema, empty `value` fields
   - Connector resolved: `type-id` + `connection-id` only; **no `is describe` call in 2a**
   - Unresolved: skeleton (empty `data: {}`) per Rule #11
7. Informational validate (Step 9.5.1): `uip maestro case validate` — expected to report errors/warnings (unbound values, missing conditions/SLA). Do NOT halt; surface counts in the summary.
8. **HARD STOP** (Step 9.5.2–9.5.5): AskUserQuestion — `Publish for review` / `Skip publish and continue` / `Abort`
   - On `Publish`: `uip solution resource refresh <SolutionDir> --output json` then `uip solution upload <SolutionDir> --output json`, print DesignerUrl, then AskUserQuestion — `Continue to phase 2b` / `Abort`
   - On `Abort`: dump `build-issues.md`, print paths, exit (no cleanup)

### Phase 2b — Detail build (skeleton → validated caseplan.json)

After approval, re-read `tasks.md` AND `caseplan.json` (Step 9.6) to rebuild name → ID maps. Then:

1. Connector task schema + defaults (Step 9.7) — `is resources describe` / `is triggers describe`, write `data.inputs[]` / `data.outputs[]`
2. Task input/output value binding for all task classes (Step 9.8) — per [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md); applies to both non-connector and connector tasks
3. Conditions, all 4 scopes (Step 10)
4. SLA + escalation (Step 11)
5. Full validate (Step 12) — `uip maestro case validate` (no `--mode`)
6. Dump `build-issues.md` (Step 12.1)
7. Post-build loop (Step 13) — AskUserQuestion dropdown; loop until user selects `Done`

## Quick Start

For a fresh case built from `sdd.md`, Steps 0–9:

### Step 0 — Resolve the `uip` binary

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` in place of `uip` if the plain command isn't on PATH.

### Step 1 — Login and pull registry

```bash
uip login status --output json
uip maestro case registry pull
```

If not logged in, ask the user to run `uip login` and stop.

### Step 2 — Locate the sdd.md

Accept the path from the user. If multiple `.md` files exist in the directory, use **AskUserQuestion** with candidates + "Something else".

### Step 3 — Resolve resources

For each task, trigger, and condition in `sdd.md`:

1. Identify the plugin from the sdd.md component type (see [references/planning.md §3](references/planning.md)).
2. Load the plugin's `planning.md`.
3. Apply registry discovery per [references/registry-discovery.md](references/registry-discovery.md).
4. Record resolutions in `registry-resolved.json` (full detail).
5. Mark unresolved resources with `<UNRESOLVED: ...>`.

### Step 4 — Generate tasks.md

Order: stages → edges → tasks → conditions → SLA. One T-numbered entry per item. See [references/planning.md §4](references/planning.md) for structure.

### Step 5 — HARD STOP: user approval

**AskUserQuestion**: `Approve and proceed` / `Request changes`. Loop on `Request changes`. Do not execute without explicit approval.

### Step 6 — Re-read tasks.md and execute Phase 2a

Re-read `tasks.md`, then open [references/implementation.md](references/implementation.md) and execute Phase 2a (Steps 6 – 9.1). Phase 2a builds solution + project + root + global vars + stages + edges + triggers + task shells only. **Do not bind input values, do not describe connector schemas, do not write conditions, do not write SLA** in Phase 2a — all deferred to Phase 2b.

### Step 7 — Informational validate + HARD STOP (Step 9.5)

```bash
uip maestro case validate <file> --output json
```

**Do NOT halt on errors/warnings** — Phase 2a state is expected invalid (unbound inputs, missing conditions, missing SLA). Capture error/warning counts for the summary.

Then **AskUserQuestion**: `Publish for review` / `Skip publish and continue` / `Abort`. On `Publish`, run `uip solution resource refresh <SolutionDir> --output json` then `uip solution upload <SolutionDir> --output json`, print `DesignerUrl`, then **AskUserQuestion**: `Continue to phase 2b` / `Abort`. On `Abort`, dump `tasks/build-issues.md`, print paths, exit.

Full contract in [references/phased-execution.md](references/phased-execution.md).

### Step 8 — Re-read and execute Phase 2b

Re-read `tasks.md` AND `caseplan.json` (Step 9.6). Execute Steps 9.7 – 12.1: connector detail, I/O binding, conditions, SLA, full validate, dump issues.

```bash
uip maestro case validate <file> --output json
```

Retry up to 3× on failure. On repeated failure, AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`.

### Step 9 — Post-build prompt

**AskUserQuestion** with options: `Run debug session` / `Publish to Studio Web` / `Done` / `Something else`. Loop until the user selects `Done`.

- `Run debug session` → ask for explicit consent, then run `uip solution resource refresh <SolutionDir> --output json` followed by `uip maestro case debug <ProjectDir>`
- `Publish to Studio Web` → run `uip solution resource refresh <SolutionDir> --output json` then `uip solution upload <SolutionDir> --output json` and share the Studio Web URL

## Reference Navigation

| I need to... | Read these |
|---|---|
| **Plan tasks from sdd.md** | [references/planning.md](references/planning.md) |
| **Execute tasks.md into a case** | [references/implementation.md](references/implementation.md) |
| **Phase 2a / 2b split + hard stop contract** | [references/phased-execution.md](references/phased-execution.md) |
| **Edit caseplan.json (cross-cutting mechanics)** | [references/caseplan-editing.md](references/caseplan-editing.md) |
| **Understand the case JSON schema** | [references/case-schema.md](references/case-schema.md) |
| **Know all CLI flags** | [references/case-commands.md](references/case-commands.md) |
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

**Structural plugins**:

| Plugin | Scope |
|--------|-------|
| [case](references/plugins/case/planning.md) | Root case (created once, T01) |
| [stages](references/plugins/stages/planning.md) | Regular and exception (a.k.a. secondary) stages |
| [edges](references/plugins/edges/planning.md) | Edges between Trigger/Stage nodes (type inferred) |
| [sla](references/plugins/sla/planning.md) | Default SLA, conditional SLA rules, escalation rules |
| [global-vars](references/plugins/variables/global-vars/planning.md) | Case variables and arguments (inputs/outputs/inputOutputs) |
| [io-binding](references/plugins/variables/io-binding/planning.md) | Task input/output wiring, cross-task references, JSON shapes |
| [logging](references/plugins/logging/impl-json.md) | Shared issue log — format, severity levels, file dump |

**Task plugins** (`references/plugins/tasks/`):

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

**Trigger plugins** (`references/plugins/triggers/`):

| Plugin | When |
|--------|------|
| [manual](references/plugins/triggers/manual/planning.md) | User-initiated start |
| [timer](references/plugins/triggers/timer/planning.md) | Scheduled start |
| [event](references/plugins/triggers/event/planning.md) | External connector event |

**Condition plugins** (`references/plugins/conditions/`):

| Plugin | Scope |
|--------|-------|
| [stage-entry-conditions](references/plugins/conditions/stage-entry-conditions/planning.md) | When a stage is entered |
| [stage-exit-conditions](references/plugins/conditions/stage-exit-conditions/planning.md) | When/how a stage exits |
| [task-entry-conditions](references/plugins/conditions/task-entry-conditions/planning.md) | When a task starts |
| [case-exit-conditions](references/plugins/conditions/case-exit-conditions/planning.md) | When the whole case completes or exits |

## Anti-patterns — What NOT to Do

Only anti-patterns without a direct Critical Rule counterpart. All other "don'ts" are covered by Rules above.

- **Do NOT skip registry lookups** based on assumptions like "this type is not discoverable." Always search the cache files first — see [references/registry-discovery.md](references/registry-discovery.md).
- **Do NOT fabricate input or output names in cross-task references.** Run `uip maestro case tasks describe` to discover actual names. A fabricated name becomes a silent runtime null.
- **Do NOT fabricate expression syntax for conditional SLA rules.** Describe the condition in natural language; the execution phase determines the exact expression form.
- **Do NOT invoke other skills automatically.** If the case needs a process, agent, or action that doesn't exist, emit a skeleton task (per Rule #11) and list the missing resources in the completion report so the user can register them externally. On-demand resource creation is a future milestone, not today.
- **Do NOT mutate `caseplan.json` (or sibling JSON files) via subprocess scripts.** Use Claude's Read + Write/Edit tools only — no `python`, `node`, `jq`, `sed`, `awk`, or helper scripts that open/parse/modify/save the file. Bash subprocesses remain OK for stdout-only helpers (e.g., `node -e "...console.log(randomId)"`). See [references/caseplan-editing.md § Tool usage](references/caseplan-editing.md#tool-usage--mandatory).

## Key Concepts

### Shell CLI usage

All `caseplan.json` mutation happens via Read/Write/Edit. The skill invokes shell CLI only for:

| Command group | What it does | Auth needed |
|----------|--------------|-------------|
| `uip maestro case registry pull/list/search`, `get-connector`, `get-connection` | Registry discovery (uses cached data after pull) | Yes (for `pull`) |
| `uip maestro case tasks describe` / `tasks enrich` | Task schema discovery for binding | Yes |
| `is resources describe` / `is triggers describe` / `is resources execute list` | Connector schema discovery | Yes |
| `uip maestro case validate` | Caseplan validation | No |
| `uip maestro case debug` | Live debug execution (explicit consent only) | Yes |
| `uip solution resource refresh` | Sync resource declarations from `bindings_v2.json` — run before `upload`/`debug` | No |
| `uip solution new` / `uip solution project add` / `uip solution upload` | Solution scaffold / registration / publish | Yes (for `upload`) |
| `uip maestro case instance`, `processes`, `incident`, `process`, `job` | Runtime query | Yes |

### CLI output format

All `uip maestro case` commands return:

```json
{ "Result": "Success", "Code": "...", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Always pass `--output json` when the output is parsed.

## Completion Output

On build completion: report `caseplan.json` path, build summary (stages/edges/tasks/conditions/SLA counts), validate status, every skeleton task + its upgrade resource (see [references/skeleton-tasks.md](references/skeleton-tasks.md)), missing IS connections. Then present post-build prompt per [references/phased-execution.md § Phase 2b Execution Order step 7](references/phased-execution.md). Never take post-build actions (debug, publish) automatically — AskUserQuestion first.

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
