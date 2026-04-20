# Implementation Phase: tasks.md → caseplan.json

Execute the approved `tasks.md` plan by translating each declarative task specification into `uip maestro case` CLI commands. Build `caseplan.json`, validate, and optionally debug or publish.

> **Prerequisite:** The user must have explicitly approved `tasks.md` from the [Planning Phase](planning.md) before starting.
>
> **Input:** `tasks/tasks.md` — the complete handoff artifact.

> **Per-node-type CLI detail lives in plugins.** This document covers the cross-cutting execution workflow. For how to run the exact CLI for a specific node, consult the matching plugin's `impl.md`:
> - Root case → `plugins/case/impl.md`
> - Stages → `plugins/stages/impl.md`
> - Edges → `plugins/edges/impl.md`
> - Tasks → `plugins/tasks/<type>/impl.md`
> - Triggers → `plugins/triggers/<type>/impl.md`
> - Conditions → `plugins/conditions/<scope>/impl.md`
> - SLA → `plugins/sla/impl.md`

---

## Step 6 — Create the Case project structure

The case file must live inside a solution + project. Scaffolding commands (solution new → case init → project add) plus the `cases add` invocation that creates `caseplan.json` live in [`plugins/case/impl.md`](plugins/case/impl.md). Run them in order, then capture the initial Trigger node ID returned by `cases add` for use in Step 8.

## Step 7 — Add stages

For each stage in `tasks.md §4.4`, run the CLI per [`plugins/stages/impl.md`](plugins/stages/impl.md). **Capture the `StageId` for every stage** into the name → ID map — downstream edges, tasks, conditions, and SLA all reference it.

`isRequired` from `tasks.md` is planning-only metadata; it is not passed on `stages add`. It is consumed later by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — Connect stages with edges

For each edge in `tasks.md §4.5`, run the CLI per [`plugins/edges/impl.md`](plugins/edges/impl.md). Edge type is inferred automatically from the `--source` node.

For multi-trigger cases, add the additional triggers first via the appropriate trigger plugin, then wire their IDs as edge sources.

## Step 9 — Add tasks and bind inputs/outputs

For each task entry in `tasks.md §4.6`, open the matching plugin's `impl.md` (`plugins/tasks/<type>/impl.md`) and run its command. **Capture the `TaskId` returned in `--output json`** — cross-task references and conditions need it.

After adding a task, bind its inputs per the two modes documented in [bindings-and-expressions.md](bindings-and-expressions.md):

**Literal / expression mode** (for `input_name = "<value>"`):

```bash
uip maestro case var bind <file> <stage-id> <task-id> <input-name> --value "<value>" --output json
```

**Cross-task reference mode** (for `input_name <- "Stage Name"."Task Name".output_name`):

1. Look up the source stage ID and source task ID from the capture map built in Steps 7 and 9.
2. Run:

```bash
uip maestro case var bind <file> <target-stage-id> <target-task-id> <input-name> \
  --source-stage <source-stage-id> \
  --source-task <source-task-id> \
  --source-output <output-name> \
  --output json
```

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

**Skip `uip maestro case var bind` entirely for skeleton tasks** — it rejects bindings without a resolved task-type schema. Capture the intended wiring from the fenced `wiring notes` code block in `tasks.md` into the completion report so the user knows what to hook up after registering the resource.

Skeleton tasks integrate with the rest of the graph:
- **Task-entry conditions** use the captured skeleton `TaskId` normally.
- **Stage-exit `selected-tasks-completed`** rules reference skeleton `TaskId`s normally.
- **Cross-task variable bindings** are deferred — the user adds them via `uip maestro case var bind` after attaching the real resource.

## Step 10 — Add conditions

For each condition in `tasks.md §4.7`, open the matching plugin:

- Stage entry → [`plugins/conditions/stage-entry-conditions/impl.md`](plugins/conditions/stage-entry-conditions/impl.md)
- Stage exit → [`plugins/conditions/stage-exit-conditions/impl.md`](plugins/conditions/stage-exit-conditions/impl.md)
- Task entry → [`plugins/conditions/task-entry-conditions/impl.md`](plugins/conditions/task-entry-conditions/impl.md)
- Case exit → [`plugins/conditions/case-exit-conditions/impl.md`](plugins/conditions/case-exit-conditions/impl.md)

## Step 11 — SLA and escalation

For each entry in `tasks.md §4.8`, run the matching sub-operation per [`plugins/sla/impl.md`](plugins/sla/impl.md): `sla set` for defaults, `sla rules add` for conditional overrides (root only), `sla escalation add` for notification rules.

## Step 12 — Validate

```bash
uip maestro case validate <file>
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Step 13.

On failure: output lists `[error]` and `[warning]` entries with path and message. Fix the reported issues (usually via a targeted re-run of the earlier step) and re-run `validate`.

**Retry policy.** Up to 3 validation retries per session. After the 3rd failure, halt and ask the user with **AskUserQuestion**: show the remaining errors and options — `Retry with fix`, `Pause for manual edit`, `Abort`.

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
