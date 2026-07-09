# Placeholder Tasks Reference

How the skill handles unresolved task resources — what a placeholder task is, when one is created, what it preserves, what it leaves out, and how the user upgrades it to a fully wired task later.

## Why Placeholders Exist

Registry pulls are often incomplete during early authoring:

- The target tenant has not yet published the processes / agents / RPA / action-apps.
- Custom Integration Service connectors have not been registered.
- IS connections for registered connectors are not yet provisioned.

If the skill halted on every unresolved resource, the generated `caseplan.json` would be a small fragment — not reviewable, not validatable, not useful. Placeholders solve that: the full **workflow structure** (stages, conditions, SLA, ordering, task names + types) lands in `caseplan.json`, the SDD-declared data contract stays visible, and only the parts that strictly require a registry lookup (task-type-id, connection-id, schema verification, resource bindings) are deferred.

The user reviews structure first, then attaches real resources once they exist.

## What a Placeholder Is (vs a Mock)

| Field | Full task | Placeholder task | Mock (forbidden) |
|-------|-----------|---------------|------------------|
| `type` | ✓ | ✓ | ✓ |
| `displayName` | ✓ | ✓ | ✓ |
| `isRequired`, `shouldRunOnlyOnce` | ✓ | ✓ | ✓ |
| `data.typeId` (connector) / `data.name` + `data.folderPath` = `=bindings.<id>` (non-connector) | real ID | **key omitted** | fake ID |
| `data.connectionId` (connector) | real UUID | **key omitted** | fake UUID |
| `data.inputs[]` / `data.outputs[]` | schema-verified rows | best-effort SDD rows when declared; omitted only when no SDD row exists | fabricated schema fields or fake connector bodies |
| Input / output variable bindings | real JSON edits via `io-binding` plugin | unverified intent rows from SDD; no schema-specific enrichment | edits targeting invented resource schemas |
| Task-entry conditions | ✓ | ✓ | ✓ |
| Referenced by stage-exit `selected-tasks-completed` | ✓ | ✓ | ✓ |

**Mocks are forbidden for tasks** because Case's typed cross-task outputs reject references to non-existent output schemas at validation time. A fabricated task-type-id causes `uip maestro case validate` to emit errors about unknown bindings. A placeholder sidesteps this by having no resource identity at all — clean validation, clear `<UNRESOLVED>` markers in `tasks.md`, preserved SDD data intent, and an explicit upgrade path.

## When a Placeholder Is Created

During **execution** (Phase 2, Step 9), for any `tasks.md` entry whose `taskTypeId`, `typeId`, or `connectionId` is `<UNRESOLVED: …>`:

1. Skip the schema fetch (`uip maestro case spec` / `uip maestro case tasks describe`).
2. Write the task JSON node with structural fields and no resource identity — no `taskTypeId`, `connectionId`, `data.name`, `data.folderPath`, connector `context`, or root resource binding.
3. If the SDD/task entry declared `inputs:` or `outputs:`, preserve those rows as best-effort `data.inputs[]` / `data.outputs[]` using planner-known names, values, types, and the task `elementId`. Before writing outputs, check the global output-owner pool; a placeholder must not emit a `data.outputs[]` row whose `var` duplicates another task/trigger/rule output. Keep duplicate-intent rows in the fenced wiring notes / build issues for upgrade instead of shipping invalid duplicate output owners. If no rows were declared, leave `data: {}`.
4. Skip schema validation/enrichment for that task in `io-binding`; placeholder rows are unverified intent until the resource resolves.
5. Generate and capture the `TaskId` normally — task-entry conditions and stage-exit rules still reference it.

## JSON Shape

Placeholders occupy a `laneIndex` in `stageNode.data.tasks[laneIndex][]`, the same way full tasks do — default one task per lane for FE readability, lane is layout-only. **Exception:** when a placeholder participates in a `runs-sequentially` group and is meant to run in parallel with sibling tasks in that group, it shares the same `laneIndex` as those siblings (shared lane = parallel siblings inside the sequential group, semantic).

A placeholder task in `caseplan.json.nodes[<stage>].data.tasks[<lane>][]`:

```json
{
  "id": "t8GQTYo8O",
  "elementId": "Stage_aB3kL9-t8GQTYo8O",
  "displayName": "Validate Submission Completeness",
  "isRequired": true,
  "type": "process",
  "data": {
    "inputs": [
      {
        "name": "sourceDocs",
        "type": "jsonSchema",
        "id": "validateSourceDocs",
        "var": "validateSourceDocs",
        "elementId": "Stage_aB3kL9-t8GQTYo8O",
        "value": "=vars.sourceDocs"
      }
    ],
    "outputs": [
      {
        "name": "submissionComplete",
        "type": "boolean",
        "id": "validateSubmissionComplete",
        "var": "submissionComplete",
        "value": "submissionComplete",
        "source": "=submissionComplete",
        "target": "=submissionComplete",
        "elementId": "Stage_aB3kL9-t8GQTYo8O"
      }
    ]
  },
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

Note what is absent: no `taskTypeId`, no folder path, no connector `typeId` / `connectionId`, no connector `context`, and no root resource binding. `data.inputs[]` / `data.outputs[]` appear only because the SDD declared those rows; a placeholder with no declared rows uses `data: {}`. Best-effort outputs still obey global `var` uniqueness. If two unresolved tasks both declare `result -> auditPostResult`, write only one JSON output owner for `auditPostResult`; keep the other producer's intent in the wiring notes so the user can rebind it after the real resource exists. The shape is uniform across classes: connector placeholders use `type` `execute-connector-activity` / `wait-for-connector`. For action placeholders, include `data.taskTitle` and `data.priority` only when SDD/planning already supplied them or when adding `inputs`/`outputs` would otherwise leave an action with data but no visible title. The key is exactly `data.taskTitle`; never use top-level `title` or `data.title`.

### In-stage timer

Timers are a built-in type — they are never placeholders because they have no registry dependency. Use [`plugins/tasks/wait-for-timer/impl-json.md`](plugins/tasks/wait-for-timer/impl-json.md).

### Case-level event triggers

Case-level event triggers (`type: "case-management:Trigger"` with `serviceType: "Intsvc.EventTrigger"`) follow the same pattern but use a different shape — trigger nodes need `data.label` / `description` / `parentElement` to render at all, so the placeholder keeps those plus `data.uipath: { serviceType: "Intsvc.EventTrigger" }`. Full spec in [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md). Manual and timer triggers are never placeholders (no registry dependency).

### Connector condition rules

When a `wait-for-connector` rule's connector hasn't resolved at write-time, emit the rule with a **stub `uipath`** (`serviceType` + 2 `"placeholder"` context fields: `connectorKey` + `operation`) — a deliberate mock that validates clean but fails at Studio Web / debug / run until replaced. Full recipe + skip behavior + upgrade path: [connector-trigger-common.md § Placeholder fallback](connector-trigger-common.md#placeholder-fallback).

## `tasks.md` Planning-Entry Shape

A placeholder-bound entry keeps every structural field and preserves declared `inputs:` / `outputs:` rows, then repeats them in a fenced code block the user will verify after attaching the real resource:

````markdown
## T20: Add process task "Validate Submission Completeness" to "Submission Review"
- taskTypeId: <UNRESOLVED: process-index.json empty in tenant>
- folder-path: <UNRESOLVED>
- inputs:
  - lob = "=metadata.lob"
  - sourceDocs <- "Submission Review"."Fetch Submission from U Submit".submissionData
- outputs:
  - submissionComplete
  - missingItems
  - tier
- runOnlyOnce: false
- isRequired: true
- order: after T19
- verify: Confirm Result: Success, capture TaskId (placeholder — user to attach process + bindings)
```text
wiring notes (user must attach after publishing the process):
  lob = =metadata.lob
  sourceDocs <- "Submission Review"."Fetch Submission from U Submit".submissionData
  outputs expected: submissionComplete, missingItems, tier
```
````

Rules:
- **Keep SDD-declared `inputs:` and `outputs:` lines** even though there is no schema to verify them against yet. Copy them into placeholder `data.inputs[]` / `data.outputs[]` as best-effort intent only when the JSON row stays structurally valid. If an output row would duplicate an existing output `var`, do not emit the duplicate JSON row; preserve that row in the fenced wiring notes / build issues instead.
- **Capture the same intended wiring in a fenced ```` ```text ```` code block** so the user sees what must be verified when they upgrade. **Do not start wiring lines with `#`** — they would render as markdown H1 headings; the fenced code block renders as preformatted text.
- **Keep every other field** — order, verify, is-required, run-only-once, display-name.

## What Validation Catches

`uip maestro case validate` on a caseplan with placeholders emits warnings, not errors:

- `Stage "<name>" has a task with no configuration` — one per placeholder whose `data` is empty.
- `Stage "<name>" has no tasks` — if every task in a stage is absent (not even a placeholder).

These are **expected** and do not block the build. Best-effort placeholder I/O rows preserve planner intent; they do not make the task runnable. Errors only appear when cross-task bindings reference non-existent outputs — which is exactly why the skill forbids fabricated task mocks (except the sanctioned connector-rule stub — see § Connector condition rules).

## Upgrade Procedure — Placeholder → Full Task

> **Built-inline agents / API workflows are not placeholders.** An `agent` or `api-workflow` the user chose to **Create** at the Rule 17 gate is built and bound during planning ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery)) — it enters Phase 2 as a fully resolved task, never a placeholder, and skips this procedure. This procedure covers creatable resources the user **declined/skipped or whose build failed** (their recovery is the same as any other unresolved kind — register the real resource, below), plus every other unresolved kind.

When the user has registered the real resource:

### 1. Re-pull the registry

**Confirm with the user via the `AskUserQuestion` tool before running** — force pull bypasses the cache, is network-heavy, and may be slow.

```bash
uip maestro case registry pull --force
```

### 2. Resolve the task-type-id

Read the relevant cache file directly per [registry-discovery.md](registry-discovery.md) — e.g., `process-index.json` for processes, `action-apps-index.json` for action apps. For a **manually-built in-solution sibling** (agent or api-workflow), find it offline by name with `uip maestro case registry search "<name>" --type <agent|api> --local --output json` (`agent` for an agent sibling, `api` for an api-workflow sibling; select the exact-name `Data.Resources[].Resource` entry; use `search` — `get --local` matches only the opaque `entityKey`, not the name). Its `Resource.EntityKey` is an opaque derived key (not the `.uipx` `Projects[].Id`), audit-only; the node binds by name+folder. Read the sibling's I/O field names from its raw `entry-points.json` (the `--output json` keys are PascalCased). For an **api-workflow sibling**, read its I/O per the fallback chain in [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution) — flat `entryPoints[0].input.properties` → `input.schema.document.properties` wrapper → `Workflow.json` root schemas when the entry-point I/O is `null`; note any fallback in the report.

### 3. Fetch the schema

For non-connector tasks, run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` to get the per-resource input/output schema. For connector tasks, run `uip maestro case registry get-connection` to obtain the `connectionId`, then `uip maestro case spec --type <activity|trigger> --activity-type-id <typeId> --connection-id <connId>` to get the unified spec output (identity, connection, inputs, outputs, filter, references, and a populated `caseShape` when `--input-details` is supplied).

### 4. Edit the placeholder in place

Read `caseplan.json`, locate the placeholder task by `id`, and mutate its `data` field in place. Keep the task's `id` and `elementId` unchanged — any conditions or `selected-tasks-completed` rules referencing the TaskId stay valid.

| Task class | `data` mutation |
|---|---|
| `process`, `agent`, `rpa`, `api-workflow`, `case-management` | Set `data.name`, `data.folderPath` (both `=bindings.<id>` refs). Write `data.inputs[]` / `data.outputs[]` from the `tasks describe` schema (each input `value: ""` to start). |
| `action` | Set `data.name`, `data.folderPath` (`=bindings.<id>`), `data.taskTitle`, `data.priority`, `data.recipient` (if known). Write `data.inputs[]` / `data.outputs[]` from the schema. |
| `execute-connector-activity`, `wait-for-connector` | Set `data.typeId`, `data.connectionId`. Write `data.inputs[]` / `data.outputs[]` from the `case spec` schema (per the connector plugin's `impl-json.md`). |

Per-class JSON shape lives in `plugins/tasks/<type>/impl-json.md` — match those exactly.

> **Tip:** If the user has many placeholders to upgrade, a cleaner workflow is to update `sdd.md` with whatever context was missing (e.g., the now-registered process name) and re-invoke the skill from Phase 1. The regeneration path preserves the declarative intent.

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

When the build finishes with placeholders, the skill's completion report must list them explicitly:

```
### Placeholder tasks (N)

| Stage | Task | Type | TaskId | Attach |
|-------|------|------|--------|--------|
| Submission Review | Validate Submission Completeness | process | t8GQTYo8O | process-index.json — "Validate Submission Completeness" |
| Submission Review | Review Submission | action | ty5UcykfU | action-apps-index.json — "Review Submission" |
| … | … | … | … | … |

### External resources to register before upgrading placeholders

- **Processes** (N): Validate Submission Completeness, Route Submission Decision, Finalize Case Closure
- **Agents** (N): Classify Documents, Generate Carrier Emails, …
- **Action Apps** (N): Review Submission, Schedule Huddle Meeting, …
- **Custom IS connectors** (N): U Submit (GetSubmission), U Place (SubmitPlannedMarkets), …
```

When agents / API workflows were **built inline** at the gate, list them separately — they are resolved, not placeholders:

```
### Agents / API workflows built inline (N)

| Stage | Task | Resource | Status |
|-------|------|----------|--------|
| Triage | Classify PO | Classify PO (agent) | built as in-solution sibling via uipath-agents; bound via --local |
| Enrich | Fetch Rates | RateFetcher (api-workflow) | built as in-solution sibling via uipath-api-workflow; bound via --local |

### Built but not referenced (reject case)

| Resource | Note |
|----------|------|
| Sentiment (agent) | built sibling on disk; task dropped from plan — reuse or remove manually |
```

The user uses the placeholder/external lists to drive external resource creation, then runs the upgrade procedure; the "built inline" list is informational (already wired).

## Anti-Patterns

- **Do NOT fabricate a task-type-id to silence the warning.** Validation will pass but runtime will fail with binding errors.
- **Do NOT fabricate schema fields on a placeholder.** Preserve only rows the SDD/task entry declared. If no row was declared, leave the corresponding `data.inputs[]` / `data.outputs[]` array absent.
- **Do NOT skip task-entry conditions on placeholders.** Conditions are structural; they work on the TaskId and must be created so the workflow order is visible in review.
- **Do NOT create placeholders for timer tasks.** Timers have no registry dependency — use the full `wait-for-timer` plugin.
- **Do NOT create a placeholder for an agent or API workflow the user chose to build inline.** It is built + bound during planning ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery)) — a resolved task, not a placeholder.
- **Do NOT build an agent or API workflow from SDD content alone.** Inline create runs only for resources the user explicitly selected at the Rule 17 gate. The built resource is an in-solution **sibling** that co-deploys with the case — never a separate tenant publish.
- **Invoking `uipath-agents` / `uipath-api-workflow` for the inline build is sanctioned** — it is not a violation of the "don't auto-invoke other skills" anti-pattern, which still applies to every non-creatable kind (regular RPA process, action, connectors, agentic process) and to `uipath-planner`.
