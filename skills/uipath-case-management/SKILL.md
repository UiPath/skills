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
5. **Follow the plugin for every node type.** Every task, trigger, and condition variant has its own plugin under `references/plugins/`. Open the matching `planning.md` during planning and the appropriate execution doc — `impl-cli.md` for CLI-strategy plugins, `impl-json.md` for JSON-strategy plugins (check the matrix in [`references/case-editing-operations.md`](references/case-editing-operations.md)). Do not guess CLI flags or JSON shapes from memory.
6. **`tasks.md` entries are declarative.** No `uip` CLI commands inside `tasks.md`. Each entry is parameters, IDs, and metadata only. The execution phase translates specs into CLI calls.
7. **One T-entry per sdd.md declaration — no omissions.** Every stage, edge, task, trigger, condition, and SLA rule declared in `sdd.md` gets its own T-numbered entry, even when the declared value looks like a "default" (e.g., condition rule-type `current-stage-entered` / `case-entered`, stage-exit type `exit-only`, `is-interrupting: false`, `runOnlyOnce: true`). Never group multiple items under one T-number. Never skip a declaration on the grounds that "the default behavior would already cover it" — if `sdd.md` wrote it down, `tasks.md` must emit a T-task for it.
8. **Always regenerate `tasks.md` from scratch** — never do incremental updates. Avoids stale state from previous runs.
9. **HARD STOP before execution.** After generating `tasks.md`, present it to the user and require explicit approval via **AskUserQuestion** (`Approve and proceed` / `Request changes`). Do not execute until approved.
10. **After approval, re-read `tasks.md` before executing.** `tasks.md` is the complete handoff artifact — all IDs, inputs, outputs, and references are captured there.
11. **Unresolved task resources produce skeleton tasks — never mock, never fabricate.** Keep the `<UNRESOLVED: ...>` marker on the `taskTypeId` / `type-id` / `connection-id` slot in `tasks.md`, and omit `inputs:` / `outputs:` from that task entry. At execution time, the task is created in `caseplan.json` with `--type` + `--display-name` only (skeleton task) — no task-type-id, no connection-id, no variable bindings. Task-entry conditions and `selected-tasks-completed` rules still reference the skeleton's `TaskId`, so the workflow structure stays reviewable. The user attaches the real resource + bindings externally before runtime. See [references/skeleton-tasks.md](references/skeleton-tasks.md). Never fabricate a task-type-id or connection-id to "fill the gap".
12. **Persist every registry resolution to `registry-resolved.json`** with full detail: search query, all matched results, selected result, rationale. This is the debug audit trail.
13. **Cross-task references** use `"Stage Name"."Task Name".output_name` in planning and resolve to `=vars.<outputVarId>` at execution time by reading the source output's `var` field from caseplan.json. Every ref must point to a task already in `tasks.md` order. Discover output names via `uip maestro case tasks describe` — do not fabricate. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md) and [references/plugins/variables/io-binding/impl-json.md](references/plugins/variables/io-binding/impl-json.md).
14. **Expression prefixes are fixed:** `=metadata.`, `=js:`, `=vars.`, `=datafabric.`, `=bindings.`, `=orchestrator.JobAttachments`, `=response`, `=result`, `=Error`, `=jsonString:`. Plain strings without a prefix are literals, not expressions.
15. **Connector integration uses the 3-step pipeline**: `get-connector` → `get-connection` → (optional) `tasks describe --connection-id`. One plugin (`connector-activity` / `connector-trigger` / event-`trigger`) per integration pattern — schema is data-driven. See [references/connector-integration.md](references/connector-integration.md).
16. **Enrichable non-connector task types** (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`) pass `--task-type-id` on `tasks add` to auto-populate inputs/outputs. Connector variants use `tasks add-connector` with `--type-id` + `--connection-id` instead.
17. **Every stage needs at least one inbound edge** or it will be orphaned. The Trigger node created automatically by `cases add` is the entry point for all single-trigger cases.
18. **One task per lane (UI layout only).** Pass `--lane <n>` on every `tasks add` / `tasks add-connector`, incrementing `n` per task within a stage. Lane is a rendering coordinate for the FE — it does not affect execution. Parallelism and sequencing are controlled entirely by task-entry conditions.
19. **User questions use AskUserQuestion with a "Something else" escape hatch.** Whenever a decision has finite enumerable choices (≤5), present a dropdown with those options AND "Something else" as the last option. For open-ended inputs (e.g., `--every 1h` vs `2h` vs `1d`), use a direct prompt. Never force a false choice.
20. **Validate after build, not during.** Run `uip maestro case validate` only after all stages, edges, tasks, conditions, and SLA are added. Intermediate states are expected to be invalid. Retry up to 3× on failure; on the 3rd failure, halt and ask the user with options: `Retry with fix` / `Pause for manual edit` / `Abort`.
21. **Never run `uip maestro case debug` automatically** — it executes the case for real (sends emails, posts messages, calls APIs). Only run on explicit user consent.
22. **Edit `content/*.json` only** — `content/*.bpmn` is auto-generated and will be overwritten.
23. **Execute CLI commands sequentially.** No parallel execution — each command may depend on IDs returned by the previous one.
24. **Check the plugin migration matrix before every plugin's execution.** [`references/case-editing-operations.md`](references/case-editing-operations.md) declares per plugin whether to use the `uip maestro case` CLI or direct JSON edits. Default is CLI; migrated plugins opt in to JSON. When a plugin is on the JSON strategy, follow its `impl-json.md` + [`references/case-editing-operations-json.md`](references/case-editing-operations-json.md) instead of the CLI command. Mixing strategies in the same run is expected during the migration.

## Workflow

Two phases with a hard stop between them: **Planning** generates a reviewable `tasks.md` from `sdd.md`. **Implementation** executes `tasks.md` via the `uip maestro case` CLI.

### Phase 1 — Planning (sdd.md → tasks.md)

**Read [references/planning.md](references/planning.md)** for the full procedure. Produces:

1. `tasks/tasks.md` — declarative task plan with T-numbered entries (stages → edges → tasks → conditions → SLA)
2. `tasks/registry-resolved.json` — full audit trail of registry lookups

Present `tasks.md` to the user for approval. **Do NOT proceed until the user explicitly approves.**

### Phase 2 — Implementation (tasks.md → caseplan.json)

**Read [references/implementation.md](references/implementation.md)** for the full execution procedure. Steps:

1. Create the solution + project + case file (Step 6)
2. Add stages (Step 7)
3. Add edges (Step 8)
4. Add tasks and bind inputs/outputs (Step 9) — per-task-type detail in `plugins/tasks/<type>/impl-cli.md` (or `impl-json.md` once migrated)
5. Add conditions (Step 10) — per-scope detail in `plugins/conditions/<scope>/impl-cli.md` (or `impl-json.md` once migrated)
6. Configure SLA and escalation (Step 11)
7. Validate (Step 12)
8. Post-build loop (Step 13) — AskUserQuestion dropdown for next steps; loop until user selects `Done`

After the user approves `tasks.md`, re-read `tasks.md` before proceeding.

## Quick Start

For a fresh case built from `sdd.md`, the 8 steps:

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

### Step 6 — Re-read tasks.md and execute

Re-read `tasks.md`, then open [references/implementation.md](references/implementation.md) and execute each T-entry in order. Open the matching plugin's `impl-cli.md` (or `impl-json.md`, per the strategy matrix) for each task/trigger/condition.

### Step 7 — Validate

```bash
uip maestro case validate <file>
```

Retry up to 3× on failure. On repeated failure, AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`.

### Step 8 — Post-build prompt

**AskUserQuestion** with options: `Run debug session` / `Publish to Studio Web` / `Done` / `Something else`. Loop until the user selects `Done`.

## Reference Navigation

| I need to... | Read these |
|---|---|
| **Plan tasks from sdd.md** | [references/planning.md](references/planning.md) |
| **Execute tasks.md into a case** | [references/implementation.md](references/implementation.md) |
| **Know which strategy (CLI vs JSON) per plugin** | [references/case-editing-operations.md](references/case-editing-operations.md) |
| **Edit caseplan.json directly (JSON strategy)** | [references/case-editing-operations-json.md](references/case-editing-operations-json.md) |
| **Run mutations via CLI (CLI strategy)** | [references/case-editing-operations-cli.md](references/case-editing-operations-cli.md) |
| **Understand the case JSON schema** | [references/case-schema.md](references/case-schema.md) |
| **Know all CLI flags** | [references/case-commands.md](references/case-commands.md) |
| **Resolve task types from registry** | [references/registry-discovery.md](references/registry-discovery.md) |
| **Wire inputs/outputs and cross-task refs** | [references/bindings-and-expressions.md](references/bindings-and-expressions.md) |
| **Configure a connector activity / trigger / event** | [references/connector-integration.md](references/connector-integration.md) |
| **Handle unresolved resources (skeleton tasks)** | [references/skeleton-tasks.md](references/skeleton-tasks.md) |
| **Create the root case (T01)** | [references/plugins/case/planning.md](references/plugins/case/planning.md) + [`impl-cli.md`](references/plugins/case/impl-cli.md) |
| **Create a stage (regular or exception)** | [references/plugins/stages/planning.md](references/plugins/stages/planning.md) + [`impl-json.md`](references/plugins/stages/impl-json.md) (pilot) / [`impl-cli.md`](references/plugins/stages/impl-cli.md) (fallback) |
| **Connect nodes with edges** | [references/plugins/edges/planning.md](references/plugins/edges/planning.md) + [`impl-cli.md`](references/plugins/edges/impl-cli.md) |
| **Configure SLA (default, conditional, escalation)** | [references/plugins/sla/planning.md](references/plugins/sla/planning.md) + [`impl-cli.md`](references/plugins/sla/impl-cli.md) |
| **Declare global variables and arguments** | [references/plugins/variables/global-vars/planning.md](references/plugins/variables/global-vars/planning.md) + [`impl-json.md`](references/plugins/variables/global-vars/impl-json.md) |
| **Wire task inputs/outputs (I/O binding)** | [references/plugins/variables/io-binding/planning.md](references/plugins/variables/io-binding/planning.md) + [`impl-json.md`](references/plugins/variables/io-binding/impl-json.md) |
| **Add a specific task type** | `references/plugins/tasks/<type>/planning.md` + `impl-cli.md` |
| **Add a specific trigger type** | `references/plugins/triggers/<type>/planning.md` + `impl-cli.md` |
| **Add a specific condition scope** | `references/plugins/conditions/<scope>/planning.md` + `impl-cli.md` |

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

- **Do NOT put `uip maestro case ...` CLI commands inside `tasks.md`.** `tasks.md` is declarative only — causes double-execution or mis-parsing.
- **Do NOT incrementally update an existing `tasks.md`.** Always regenerate from scratch.
- **Do NOT skip registry lookups** based on assumptions like "this type is not discoverable." Always search the cache files first.
- **Do NOT group multiple sdd.md tasks under one T-number.** Each task, trigger, edge, or condition gets its own numbered entry.
- **Do NOT fabricate input or output names in cross-task references.** Run `uip maestro case tasks describe` to discover actual names. A fabricated name becomes a silent runtime null.
- **Do NOT fabricate expression syntax for conditional SLA rules.** Describe the condition in natural language; the execution phase determines the exact expression form.
- **Do NOT fabricate task-type-ids or connection-ids.** When a resource is unresolved, use skeleton-task creation: `tasks add --type <t> --display-name <n>` with no `--task-type-id`, and for connectors `tasks add-connector --type <t> --display-name <n>` with no `--type-id` / `--connection-id`. Skip input/output bindings entirely — skeletons have no input schema. See [references/skeleton-tasks.md](references/skeleton-tasks.md).
- **Do NOT invoke other skills automatically.** If the case needs a process, agent, or action that doesn't exist, emit a skeleton task (per Rule #11) and list the missing resources in the completion report so the user can register them externally. On-demand resource creation is a future milestone, not today.
- **Do NOT place multiple tasks in the same lane.** The FE renders same-lane tasks stacked in one column, which is unreadable for non-trivial stages. Give each task its own `--lane` index. Lane carries no execution semantics — it's layout only.
- **Do NOT edit `content/*.bpmn` files.** They are auto-generated and will be overwritten.
- **Do NOT run `uip maestro case debug` automatically.** It executes the case for real — sends emails, posts messages, calls APIs. Only run on explicit user consent.
- **Do NOT execute CLI commands in parallel.** Each command may depend on IDs returned by the previous one — run them sequentially.
- **Do NOT validate after each individual command.** Intermediate states are expected to be invalid. Run `uip maestro case validate` once after the full build.

## Key Concepts

### Local vs cloud commands

| Commands | What they do | Auth needed |
|----------|--------------|-------------|
| `uip maestro case cases`, `stages`, `tasks`, `edges`, `var`, `sla` | Edit local `caseplan.json` | No |
| `uip maestro case registry pull/list/search`, `get-connector`, `get-connection` | Registry discovery (uses cached data after pull) | Yes (for `pull`) |
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
