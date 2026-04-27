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
| `type` | ✓ | ✓ | ✓ |
| `displayName` | ✓ | ✓ | ✓ |
| `isRequired`, `shouldRunOnlyOnce` | ✓ | ✓ | ✓ |
| `data.context.taskTypeId` (non-connector) / `data.typeId` (connector) | real ID | **key omitted** | fake ID |
| `data.connectionId` (connector) | real UUID | **key omitted** | fake UUID |
| `data.inputs[]` value JSON (connector) | real values | **omitted** | `{}` |
| Input / output variable bindings | real JSON edits via `io-binding` plugin | **skipped entirely** (no `data.inputs[]` to edit) | edits targeting nonexistent input names |
| Task-entry conditions | ✓ | ✓ | ✓ |
| Referenced by stage-exit `selected-tasks-completed` | ✓ | ✓ | ✓ |

**Mocks are forbidden** because Case's typed cross-task outputs reject references to non-existent output schemas at validation time. A fabricated task-type-id causes `uip maestro case validate` to emit errors about unknown bindings. A skeleton sidesteps this by having no bindings at all — clean validation, clear `<UNRESOLVED>` markers in `tasks.md`, explicit upgrade path.

## When a Skeleton Is Created

During **execution** (Phase 2, Step 9), for any `tasks.md` entry whose `taskTypeId`, `typeId`, or `connectionId` is `<UNRESOLVED: …>`:

1. Skip the schema fetch (`uip maestro case tasks describe` / `is resources describe`).
2. Write the task JSON node with structural fields only — no `taskTypeId` / `connectionId` / `inputs` / `outputs` keys (see JSON Shape below).
3. Skip the `io-binding` plugin entirely for that task (see [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md) — skeleton tasks log a `SKIPPED` severity entry and move on, because there is no `data.inputs[]` schema to write into).
4. Generate and capture the `TaskId` normally — task-entry conditions and stage-exit rules still reference it.

## JSON Shape

Skeletons occupy their own `laneIndex` in `stageNode.data.tasks[laneIndex][]`, the same way full tasks do — one task per lane for FE readability. Lane is layout only; it carries no execution semantics.

A skeleton task in `caseplan.json.nodes[<stage>].data.tasks[<lane>][]`:

```json
{
  "id": "t8GQTYo8O",
  "elementId": "Stage_aB3kL9-t8GQTYo8O",
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

Note the empty `data: {}` — no `taskTypeId`, no folder path, no input/output wiring. Connector skeletons follow the same shape with `type` set to `connector-activity` or `connector-trigger` and no `data.typeId` / `data.connectionId` keys.

> **`action` skeletons** omit `data.taskTitle`. Without a resolved action-app schema, the title field has no UI to render against. Add it when the user attaches the action-app.

### In-stage timer

Timers are a built-in type — they are never skeletons because they have no registry dependency. Use [`plugins/tasks/wait-for-timer/impl-json.md`](plugins/tasks/wait-for-timer/impl-json.md).

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

### 3. Fetch the schema

Run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` to get the per-resource input/output schema. For connector tasks, run `is resources describe` (activity) or `is triggers describe` (trigger) instead, and run `uip maestro case registry get-connection` to obtain the `connectionId`.

### 4. Edit the skeleton in place

Read `caseplan.json`, locate the skeleton task by `id`, and mutate its `data` field in place. Keep the task's `id` and `elementId` unchanged — any conditions or `selected-tasks-completed` rules referencing the TaskId stay valid.

| Task class | `data` mutation |
|---|---|
| `process`, `agent`, `rpa`, `api-workflow`, `case-management` | Set `data.name`, `data.folderPath`, `data.context.taskTypeId = <entityKey>`. Write `data.inputs[]` / `data.outputs[]` from the `tasks describe` schema (each input `value: ""` to start). |
| `action` | Set `data.context.taskTypeId = <actionAppId>`, `data.taskTitle`, `data.priority`, `data.recipient` (if known). Write `data.inputs[]` / `data.outputs[]` from the schema. |
| `connector-activity`, `connector-trigger` | Set `data.typeId`, `data.connectionId`. Write `data.inputs[]` / `data.outputs[]` from the `is describe` schema. |

Per-class JSON shape lives in `plugins/tasks/<type>/impl-json.md` — match those exactly.

> **Tip:** If the user has many skeletons to upgrade, a cleaner workflow is to update `sdd.md` with whatever context was missing (e.g., the now-registered process name) and re-invoke the skill from Phase 1. The regeneration path preserves the declarative intent.

### 5. Bind inputs and outputs

Wire each input per the `io-binding` plugin — see [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). In short:

1. Read `caseplan.json`; locate the task's `data.inputs[]` by input `name`.
2. For literals/expressions from the `wiring notes` code block (`foo = =metadata.x`) — write the RHS string to `input.value`.
3. For cross-task references (`foo <- "Stage"."Task".output`) — resolve the source task's output `var` from `caseplan.json`, then write `=vars.<var>` to the target input's `value`.
4. Write `caseplan.json` back.

### 6. Re-validate

```bash
uip maestro case validate <file> --output json
```

The "task with no configuration" warning disappears once `data` is populated.

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
- **Do NOT partially bind inputs on a skeleton.** A skeleton has no `data.inputs[]` to edit — the io-binding plugin logs a `SKIPPED` entry and moves on. Half-bound skeletons are harder to upgrade than bare ones.
- **Do NOT skip task-entry conditions on skeletons.** Conditions are structural; they work on the TaskId and must be created so the workflow order is visible in review.
- **Do NOT create skeletons for timer tasks.** Timers have no registry dependency — use the full `wait-for-timer` plugin.
