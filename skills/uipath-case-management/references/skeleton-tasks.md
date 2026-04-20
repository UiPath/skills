# Skeleton Tasks Reference

How the skill handles unresolved task resources — what a skeleton task is, when one is created, what it preserves, what it leaves out, and how the user upgrades it to a fully wired task later.

## Why Skeletons Exist

Registry pulls are often incomplete during early authoring:

- The target tenant has not yet published the processes / agents / RPA / action-apps.
- Custom Integration Service connectors have not been registered.
- IS connections for registered connectors are not yet provisioned.

If the skill halted on every unresolved resource, the generated `caseplan.json` would be a small fragment — not reviewable, not validatable, not useful. Skeletons solve that: the full **workflow structure** (stages, edges, conditions, SLA, ordering, task names + types) lands in `caseplan.json`, and only the parts that strictly require a registry lookup (task-type-id, connection-id, input/output schemas) are deferred.

The user reviews structure first, then attaches real resources once they exist.

## What a Skeleton Is (vs a Mock)

| Field | Full task | Skeleton task | Mock (forbidden) |
|-------|-----------|---------------|------------------|
| `--type` | ✓ | ✓ | ✓ |
| `--display-name` | ✓ | ✓ | ✓ |
| `--is-required`, `--should-run-only-once` | ✓ | ✓ | ✓ |
| `--task-type-id` / `--type-id` | real ID | **omitted** | fake ID |
| `--connection-id` (connectors) | real UUID | **omitted** | fake UUID |
| `--input-values` (connectors) | real JSON | **omitted** | `{}` |
| Input / output variable bindings | real `var bind` calls | **skipped entirely** | `var bind` to nonexistent names |
| Task-entry conditions | ✓ | ✓ | ✓ |
| Referenced by stage-exit `selected-tasks-completed` | ✓ | ✓ | ✓ |

**Mocks are forbidden** because Case's typed cross-task outputs reject references to non-existent output schemas at validation time. A fabricated task-type-id causes `uip maestro case validate` to emit errors about unknown bindings. A skeleton sidesteps this by having no bindings at all — clean validation, clear `<UNRESOLVED>` markers in `tasks.md`, explicit upgrade path.

## When a Skeleton Is Created

During **execution** (Phase 2, Step 9), for any `tasks.md` entry whose `taskTypeId`, `type-id`, or `connection-id` is `<UNRESOLVED: …>`:

1. Skip the enrichment command (`tasks add --task-type-id …`).
2. Run the bare `tasks add` / `tasks add-connector` command with structural flags only.
3. Skip every `uip maestro case var bind` call for that task.
4. Capture the returned `TaskId` normally — task-entry conditions and stage-exit rules still reference it.

## CLI Shape

> Skeletons take `--lane <n>` the same way full tasks do — one task per lane index for FE readability. Lane is layout only; it carries no execution semantics.

### Non-connector tasks

```bash
uip maestro case tasks add <file> <stage-id> \
  --type <process|agent|rpa|action|api-workflow|case-management> \
  --display-name "<name>" \
  --lane <n> \
  [--is-required] \
  [--should-run-only-once] \
  --output json
```

> **`action` skeletons** do not receive `--task-title`. Without a resolved action-app schema, the title field has no UI to render against. Add it when the user attaches the action-app.

### Connector tasks

```bash
uip maestro case tasks add-connector <file> <stage-id> \
  --type <activity|trigger> \
  --display-name "<name>" \
  --lane <n> \
  --output json
```

### In-stage timer

Timers are a built-in type — they are never skeletons because they have no registry dependency. Use [`plugins/tasks/wait-for-timer/impl.md`](plugins/tasks/wait-for-timer/impl.md).

## Resulting JSON Shape

A skeleton task in `caseplan.json.nodes[<stage>].data.tasks[0][]`:

```json
{
  "id": "t8GQTYo8O",
  "displayName": "Validate Submission Completeness",
  "isRequired": true,
  "type": "process",
  "data": {},
  "entryConditions": [
    {
      "id": "Condition_xC1XyX",
      "displayName": "After Fetch Submission",
      "rules": [
        [{ "rule": "selected-tasks-completed", "id": "Rule_jdBFrJ", "selectedTasksIds": ["…"] }]
      ]
    }
  ]
}
```

Note the empty `data: {}` — no `taskTypeId`, no folder path, no input/output wiring.

## `tasks.md` Planning-Entry Shape

A skeleton-bound entry keeps every structural field and moves the lost wiring into a fenced code block the user will act on later:

````markdown
## T20: Add process task "Validate Submission Completeness" to "Submission Review"
- taskTypeId: <UNRESOLVED: process-index.json empty in tenant>
- folder-path: <UNRESOLVED>
- runOnlyOnce: false
- isRequired: true
- order: after T19
- verify: Confirm Result: Success, capture TaskId (skeleton — user to attach process + bindings)
```text
wiring notes (user must attach after publishing the process):
  lob = =metadata.lob
  sourceDocs <- "Submission Review"."Fetch Submission from U Submit".submissionData
  outputs expected: submissionComplete, missingItems, tier
```
````

Rules:
- **Omit `inputs:` and `outputs:` lines** — no schema to wire against.
- **Capture the intended wiring in a fenced ```` ```text ```` code block** so the user sees the mapping when they upgrade. **Do not start wiring lines with `#`** — they would render as markdown H1 headings; the fenced code block renders as preformatted text.
- **Keep every other field** — order, verify, is-required, run-only-once, display-name.

## What Validation Catches

`uip maestro case validate` on a caseplan with skeletons emits warnings, not errors:

- `Stage "<name>" has a task with no configuration` — one per skeleton.
- `Stage "<name>" has no tasks` — if every task in a stage is absent (not even a skeleton).

These are **expected** and do not block the build. Errors only appear when cross-task bindings reference non-existent outputs — which is exactly why the skill forbids mocks.

## Upgrade Procedure — Skeleton → Full Task

When the user has registered the real resource:

### 1. Re-pull the registry

```bash
uip maestro case registry pull --force
```

### 2. Resolve the task-type-id

Read the relevant cache file directly per [registry-discovery.md](registry-discovery.md) — e.g., `process-index.json` for processes, `action-apps-index.json` for action apps.

### 3. Attach the resource to the skeleton

There is no single `tasks edit --task-type-id` flag today. The upgrade path depends on the task type:

| Task type | Upgrade approach |
|-----------|------------------|
| `process`, `agent`, `rpa`, `api-workflow`, `case-management` | `uip maestro case tasks remove <file> <stage-id> <task-id>` then re-add with `--task-type-id <entityKey>`. Conditions referencing the skeleton's TaskId will break — re-add them with the new TaskId. |
| `action` | Same remove + re-add, passing `--task-type-id <actionAppId>` and `--task-title "<title>"`. |
| `connector-activity`, `connector-trigger` | Remove + re-add via `tasks add-connector --type-id … --connection-id … --input-values '…'`. |

> **Tip:** If the user has many skeletons to upgrade, a cleaner workflow is to update `sdd.md` with whatever context was missing (e.g., the now-registered process name) and re-invoke the skill from Phase 1. The regeneration path preserves the declarative intent; manual edits on `caseplan.json` are brittle.

### 4. Bind inputs and outputs

Use the fenced `wiring notes` code block from `tasks.md` as the reference. For each input:

```bash
# Literal / expression
uip maestro case var bind <file> <stage-id> <task-id> <input-name> --value "=metadata.lob" --output json

# Cross-task
uip maestro case var bind <file> <stage-id> <task-id> <input-name> \
  --source-stage <source-stage-id> \
  --source-task <source-task-id> \
  --source-output <output-name> \
  --output json
```

Run `uip maestro case tasks describe --id <entityKey>` first to confirm the exact input/output names — do not guess.

### 5. Re-validate

```bash
uip maestro case validate <file>
```

The "task with no configuration" warning disappears once the task-type-id is attached.

## Completion-Report Shape

When the build finishes with skeletons, the skill's completion report must list them explicitly:

```
### Skeleton tasks (N)

| Stage | Task | Type | TaskId | Attach |
|-------|------|------|--------|--------|
| Submission Review | Validate Submission Completeness | process | t8GQTYo8O | process-index.json — "Validate Submission Completeness" |
| Submission Review | Review Submission | action | ty5UcykfU | action-apps-index.json — "Review Submission" |
| … | … | … | … | … |

### External resources to register before upgrading skeletons

- **Processes** (N): Validate Submission Completeness, Route Submission Decision, Finalize Case Closure
- **Agents** (N): Classify Documents, Generate Carrier Emails, …
- **Action Apps** (N): Review Submission, Schedule Huddle Meeting, …
- **Custom IS connectors** (N): U Submit (GetSubmission), U Place (SubmitPlannedMarkets), …
```

The user uses this list to drive external resource creation, then runs the upgrade procedure.

## Anti-Patterns

- **Do NOT fabricate a task-type-id to silence the warning.** Validation will pass but runtime will fail with binding errors.
- **Do NOT partially bind inputs on a skeleton.** `var bind` either binds a full resolved input or nothing — half-bound skeletons are harder to upgrade than bare ones.
- **Do NOT skip task-entry conditions on skeletons.** Conditions are structural; they work on the TaskId and must be created so the workflow order is visible in review.
- **Do NOT manually edit `caseplan.json` to add task-type-ids.** Use `tasks remove` + re-`add` so the JSON shape matches what the CLI would produce (including `elementId` generation and other internals).
- **Do NOT create skeletons for timer tasks.** Timers have no registry dependency — use the full `wait-for-timer` plugin.
