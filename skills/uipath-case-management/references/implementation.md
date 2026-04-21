# Implementation Phase: tasks.md → caseplan.json

Execute the approved `tasks.md` plan, building `caseplan.json` via either `uip maestro case` CLI commands or direct JSON edits (per-plugin). Validate, then optionally debug or publish.

> **Prerequisite:** The user must have explicitly approved `tasks.md` from the [Planning Phase](planning.md) before starting.
>
> **Input:** `tasks/tasks.md` — the complete handoff artifact.

## Strategy selection (per plugin)

Before executing each plugin's T-entries, consult the strategy matrix in [case-editing-operations.md](case-editing-operations.md).

- **`Strategy = JSON`** → use the plugin's `impl-json.md` + [case-editing-operations-json.md](case-editing-operations-json.md) for cross-cutting mechanics (ID generation, Pre-flight Checklist, primitive ops).
- **`Strategy = CLI`** → use the plugin's `impl-cli.md` + [case-editing-operations-cli.md](case-editing-operations-cli.md) for cross-cutting mechanics.

Mixing strategies within a single skill run is expected during the migration. Both paths conform to the same spec, so output is interchangeable.

> **Per-node-type detail lives in plugins.** This document covers the cross-cutting execution workflow. For how to execute a specific node, consult the matching plugin's `impl-cli.md` or `impl-json.md` per the strategy matrix:
> - Root case → `plugins/case/impl-cli.md`
> - Stages → `plugins/stages/impl-json.md` (pilot) — `plugins/stages/impl-cli.md` is the fallback
> - Edges → `plugins/edges/impl-json.md` (JSON strategy) — `plugins/edges/impl-cli.md` is the fallback
> - Tasks → `plugins/tasks/<type>/impl-cli.md`
> - Triggers → `plugins/triggers/<type>/impl-cli.md`
> - Conditions → `plugins/conditions/<scope>/impl-cli.md`
> - SLA → `plugins/sla/impl-json.md` (primary) — `plugins/sla/impl-cli.md` is the fallback
> - Global variables & arguments → `plugins/variables/global-vars/impl-json.md`
> - Task I/O binding → `plugins/variables/io-binding/impl-json.md`
> - Logging → `plugins/logging/impl-json.md`

---

## Issue Log — Initialize Before Step 6

Before any build step, initialize an empty issue list. All plugins append to this shared list during execution. See [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md) for the entry format, severity levels, and file schema.

```python
issues = []  # shared across all steps — passed to each plugin
```

## Step 6 — Create the Case project structure

The case file must live inside a solution + project. Scaffolding commands (solution new → case init → project add) plus the `cases add` invocation that creates `caseplan.json` live in [`plugins/case/impl-cli.md`](plugins/case/impl-cli.md). Run them in order, then capture the initial Trigger node ID returned by `cases add` for use in Step 8.

## Step 6.1 — Declare global variables and arguments

For each variable/argument T-entry from `tasks.md §4.2.1`, write entries directly into `caseplan.json` per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md). This step populates `root.data.uipath.variables` (inputs, outputs, inputOutputs) and trigger output mappings. Execute these before adding stages — downstream tasks and conditions reference variables via `=vars.<id>`.

## Step 7 — Add stages

For each stage in `tasks.md §4.4`, execute per [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). Strategy per the matrix in [case-editing-operations.md](case-editing-operations.md) — currently `stages` is on the **JSON** strategy (pilot); [`plugins/stages/impl-cli.md`](plugins/stages/impl-cli.md) is the fallback. **Capture the generated `StageId` for every stage** into the name → ID map (and into `id-map.json` for JSON strategy) — downstream edges, tasks, conditions, and SLA all reference it.

`isRequired` from `tasks.md` is planning-only metadata; it is not passed on `stages add`. It is consumed later by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — Connect stages with edges

For each edge in `tasks.md §4.5`, execute per [`plugins/edges/impl-json.md`](plugins/edges/impl-json.md). Strategy per the matrix in [case-editing-operations.md](case-editing-operations.md) — currently `edges` is on the **JSON** strategy; [`plugins/edges/impl-cli.md`](plugins/edges/impl-cli.md) is the fallback. Edge type is inferred automatically from the source node's `type` in `schema.nodes`.

For multi-trigger cases, add the additional triggers first via the appropriate trigger plugin, then wire their IDs as edge sources.

## Step 9 — Add tasks and bind inputs/outputs

For each task entry in `tasks.md §4.6`, open the matching plugin's `impl-cli.md` (`plugins/tasks/<type>/impl-cli.md`) and run its command. **Capture the `TaskId` returned in `--output json`** — cross-task references and conditions need it.

After adding a task, bind its inputs by editing `caseplan.json` directly per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md):

1. Read `caseplan.json`, find the task's `data.inputs[]` by name.
2. For literals/expressions (`input = "<value>"`): write the value string to `input.value`.
3. For cross-task references (`input <- "Stage"."Task".output`): resolve the source output's `var` field from the JSON, then write `=vars.<var>` to the target input's `value`.
4. Write `caseplan.json` back.

For **connector tasks**, pass variable references inline in `--input-values` at creation time (e.g., `"=vars.amount"`). Resolve cross-task `var` IDs from `caseplan.json` before constructing the `--input-values` JSON.

**Binding order.** Process tasks in the order listed in `tasks.md` (already dependency-sorted by `order: after T<n>`). Bind each task's inputs immediately after adding it. If a cross-task reference points to a task not yet added, halt — `tasks.md` ordering is wrong; report to the user.

**Pass `--lane <n>` on every task add**, incrementing per task within a stage (starting at 0). Lane is a FE layout coordinate; it does not affect execution. Sequencing and parallelism come from task-entry conditions.

### Step 9.1 — Skeleton tasks for unresolved resources

When a task entry's `taskTypeId` (or `type-id` / `connection-id` for connector tasks) is `<UNRESOLVED: …>`, create a **skeleton task** instead of halting. See [skeleton-tasks.md](skeleton-tasks.md) for the canonical reference.

**Process / agent / rpa / action / api-workflow / case-management:**

```bash
uip maestro case tasks add <file> <stage-id> \
  --type <process|agent|rpa|action|api-workflow|case-management> \
  --display-name "<name>" \
  [--is-required] \
  [--should-run-only-once] \
  --output json
```

**Connector activity / trigger:**

```bash
uip maestro case tasks add-connector <file> <stage-id> \
  --type <activity|trigger> \
  --display-name "<name>" \
  --output json
```

**Skip all input binding for skeleton tasks** — they have no inputs (created without `--task-type-id`). Capture the intended wiring from the fenced `wiring notes` code block in `tasks.md` into the completion report so the user knows what to hook up after registering the resource.

Skeleton tasks integrate with the rest of the graph:
- **Task-entry conditions** use the captured skeleton `TaskId` normally.
- **Stage-exit `selected-tasks-completed`** rules reference skeleton `TaskId`s normally.
- **Cross-task variable bindings** are deferred — the user binds them after attaching the real resource.

## Step 10 — Add conditions

For each condition in `tasks.md §4.7`, open the matching plugin (`impl-cli.md` when the strategy matrix lists the scope as `CLI`; `impl-json.md` when `JSON`):

- Stage entry → [`plugins/conditions/stage-entry-conditions/impl-cli.md`](plugins/conditions/stage-entry-conditions/impl-cli.md) / [`impl-json.md`](plugins/conditions/stage-entry-conditions/impl-json.md)
- Stage exit → [`plugins/conditions/stage-exit-conditions/impl-cli.md`](plugins/conditions/stage-exit-conditions/impl-cli.md) / [`impl-json.md`](plugins/conditions/stage-exit-conditions/impl-json.md)
- Task entry → [`plugins/conditions/task-entry-conditions/impl-cli.md`](plugins/conditions/task-entry-conditions/impl-cli.md) / [`impl-json.md`](plugins/conditions/task-entry-conditions/impl-json.md)
- Case exit → [`plugins/conditions/case-exit-conditions/impl-cli.md`](plugins/conditions/case-exit-conditions/impl-cli.md) / [`impl-json.md`](plugins/conditions/case-exit-conditions/impl-json.md)

## Step 11 — SLA and escalation

SLA is on the **JSON** strategy per the matrix in [case-editing-operations.md](case-editing-operations.md). Group `tasks.md §4.8` entries by target (root or stage), then compose and write the full `slaRules[]` array per target in a single mutation per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). The JSON path supports per-conditional-rule escalations, ExceptionStage SLA, and multi-recipient single rules — all gap-fills over the CLI's capabilities. Fallback to [`plugins/sla/impl-cli.md`](plugins/sla/impl-cli.md) only if the JSON strategy fails empirically.

## Step 12 — Validate

```bash
uip maestro case validate <file>
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Step 13.

On failure: output lists `[error]` and `[warning]` entries with path and message. Fix the reported issues (usually via a targeted re-run of the earlier step) and re-run `validate`.

**Retry policy.** Up to 3 validation retries per session. After the 3rd failure, halt and ask the user with **AskUserQuestion**: show the remaining errors and options — `Retry with fix`, `Pause for manual edit`, `Abort`.

## Step 12.1 — Dump issue log

Write the issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md), grouped by plugin with a summary index. This file is the source of truth for the completion report. Write it even if zero issues were logged (confirms a clean build).

## Step 13 — Post-build prompt

Once validation passes, ask the user what to do next.

Use **AskUserQuestion** with options:

- `Run debug session` — proceed to Step 14.
- `Publish to Studio Web` — proceed to Step 15.
- `Done` — exit.
- `Something else` — free-form prompt.

After debug or publish completes, return to this prompt so the user can chain the other action (e.g., debug first, then publish). Exit when the user selects `Done`.

For further authoring changes (add a task, tweak a condition, etc.), the user updates `sdd.md` and re-runs the skill from Phase 1 — this skill does not offer in-place incremental edits.

## Step 14 — Optional: Debug session

> Debug executes the case for real — it will send emails, post messages, call APIs, write to databases. Only run debug when the user explicitly asks. Never run it automatically.

```bash
uip maestro case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json
```

Requires `uip login`. Uploads to Studio Web, runs in Orchestrator, streams results.

## Step 15 — Optional: Publish to Studio Web

**Default publish target.** Uploads the case to Studio Web for visualization and editing.

```bash
uip solution upload "<SolutionDir>" --output json
```

Accepts the solution directory (the folder containing the `.uipx`) directly — no intermediate bundling step. `upload` pushes to Studio Web — share the returned URL with the user.

> **Do NOT run `uip maestro case pack` + `uip solution publish` unless the user explicitly asks for Orchestrator deployment.** That path puts the case directly into Orchestrator, bypassing Studio Web. Default is always Studio Web.
