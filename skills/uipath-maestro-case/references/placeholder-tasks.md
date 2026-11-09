# Placeholder Tasks Reference

This reference defines unresolved task resources: creation, preserved/omitted fields, validation, and upgrade.

## Why Placeholders Exist

Registry pulls are often incomplete during early authoring:

- The target tenant has not yet published the processes / agents / RPA / action-apps.
- Custom Integration Service connectors have not been registered.
- IS connections for registered connectors are not yet provisioned.
- Studio Web TypeCache cannot serve a connector catalog — `registry pull` lists its `typecache-*` type in `Data.Errors` — so nothing that index serves resolves in that session ([connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx)).

Do not halt. Generate the complete reviewable, validatable workflow in `caseplan.case`—stages, conditions, SLA, ordering, task names, and types—and defer only registry-dependent `task-type-id`, `connection-id`, and input/output schemas. The user reviews structure, then attaches resources.

## What a Placeholder Is (vs a Mock)

| Field | Full task | Placeholder task | Mock (forbidden) |
|---|---|---|---|
| `type`, `displayName` | ✓ | ✓ | ✓ |
| `isRequired`, `shouldRunOnlyOnce` | ✓ | ✓ | ✓ |
| `data.typeId` (connector) / `data.name` + `data.folderPath` = `=bindings.<id>` (non-connector) | real ID | **key omitted** | fake ID |
| `data.connectionId` (connector) | real UUID | **key omitted** | fake UUID |
| `data.inputs[]` value JSON (connector) | real values | **omitted** | `{}` |
| Input/output variable bindings | real JSON edits via `io-binding` plugin | **skipped entirely** (no `data.inputs[]`) | edits to nonexistent inputs |
| Task-entry conditions; stage-exit `selected-tasks-completed` references | ✓ | ✓ | ✓ |

**Mocks are forbidden for tasks** because Case's typed cross-task outputs reject references to non-existent output schemas at validation time. A fabricated task-type-id causes `uip maestro case validate` to emit errors about unknown bindings. A placeholder sidesteps this by having no bindings at all — clean validation, clear `<UNRESOLVED>` markers in `registry-resolved.json`, explicit upgrade path.

## When a Placeholder Is Created

During **execution** (Phase 2, Step 9), create a placeholder for each `registry-resolved.json` entry whose `taskTypeId`, `typeId`, or `connectionId` is `<UNRESOLVED: …>`, or whose `gateDecision` is `"resolve-at-build"`.

**`sdd convert --resolved` usually writes it for you.** If `Data.Unresolved[]` reports kind `placeholder`, it already emitted every applicable task in the JSON Shape below ([phased-execution.md § Convert first](phased-execution.md#convert-first--emit-from-the-document-before-authoring)); leave them unchanged. Apply the following only when a deferred task was emitted with `data` (older CLI or ledger lacking both markers), and to all tasks when the version guard sent Phase 2 to hand-authoring:

1. Skip `uip maestro case spec` / `uip maestro case tasks describe`.
2. Write structural fields only; omit `taskTypeId`, `connectionId`, `inputs`, and `outputs` (see JSON Shape).
3. Skip the `io-binding` plugin entirely. It logs a `SKIPPED` severity entry because no `data.inputs[]` schema exists ([`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md)).
4. Generate and capture `TaskId` normally; task-entry conditions and stage-exit rules still reference it.

## JSON Shape

Keep placeholders in normal `stageNode.data.tasks` position, preserving order and any `runs-sequentially` entry condition. Use consecutive single-task sets for a strict sequential chain; group same-set tasks only when explicitly parallel siblings.

A placeholder in `caseplan.case.nodes[<stage>].data.tasks[<lane>][]` is:

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
      "rules": [[{ "rule": "selected-tasks-completed", "id": "Rule_jdBFrJ", "selectedTasksIds": ["…"] }]]
    }
  ]
}
```

`data: {}` contains no `taskTypeId`, folder path, or input/output wiring. Apply this uniformly to connector placeholders (`execute-connector-activity` / `wait-for-connector`) and action placeholders; do not add `data.taskTitle` or other action keys.

### In-stage timer

Timers are built-in and never placeholders; use [`plugins/tasks/wait-for-timer/impl-json.md`](plugins/tasks/wait-for-timer/impl-json.md).

### Case-level event triggers

Case-level event triggers (`type: "uipath.case.trigger"` with `data.inputs.serviceType: "Intsvc.EventTrigger"`) use a distinct placeholder shape: retain `data.display.label`, `description`, `parentElement`, and `typeVersion`, plus `data.inputs` with `serviceType: "Intsvc.EventTrigger"` and one `context[]` entry carrying `objectName` (the SDD Source emitted by `sdd convert`; keep it). See [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md). Manual and timer triggers are never placeholders.

### Connector condition rules

If a `wait-for-connector` rule's connector is unresolved at write time, emit a stub `uipath` with `serviceType` and two `"placeholder"` context fields: `connectorKey` and `operation`. This deliberate mock fails `validate`, Studio Web, debug, and run until replaced. Report expected errors as unresolved connectors; never repair them ([connector-trigger-impl.md § What validate reports for a stub](connector-trigger-impl.md#what-validate-reports-for-a-stub)). Follow the full recipe, skip behavior, and upgrade path in [connector-trigger-impl.md § Placeholder fallback](connector-trigger-impl.md#placeholder-fallback).

## `registry-resolved.json` Entry Shape

A placeholder-bound entry is an ordinary Rule 10 ledger object with `selected: null`, the unresolved reason in the identity slot, and schema-less wiring in `wiringNotes`. The file is a bare top-level array, never an envelope:

```json
{
  "stage": "Submission Review",
  "task": "Validate Submission Completeness",
  "taskType": "process",
  "cacheFile": "processOrchestration-index.json",
  "searchQuery": "Validate Submission Completeness",
  "matches": [],
  "selected": null,
  "taskTypeId": "<UNRESOLVED: processOrchestration-index.json empty in tenant>",
  "folder-path": "<UNRESOLVED>",
  "rationale": "Empty exact-name lookup after a successful registry pull; user declined the Rule 18 create gate.",
  "wiringNotes": [
    "lob = =metadata.lob",
    "sourceDocs <- \"Submission Review\".\"Fetch Submission from U Submit\".submissionData",
    "outputs expected: submissionComplete, missingItems, tier"
  ]
}
```

- Omit resolved-schema keys `inputs` / `outputs`.
- Put intended wiring in `wiringNotes`, one string per mapping; Phase 2 reads it into the completion report.
- Keep every Rule 10 key. After a genuine empty lookup, `matches` is `[]` and `selected` is `null`; put `<UNRESOLVED: <reason>>` in `taskTypeId`, `typeId`, or `connectionId`.
- Do not restate the SDD contract: display name, required, run-only-once, activation mode, entry rule, lane, and verify text remain in `sdd.md`. See [planning.md § Step 4](planning.md).

## What Validation Catches

`uip maestro case validate` emits warnings, not errors, for placeholders under default and `--strict` profiles:

- `Task "<name>" (type "<type>") has an empty "data" block, so no other check can run on it.` — one per placeholder.
- `Stage "<name>" has no tasks` — only when a stage has no tasks at all, not even a placeholder.

Under `--sdd`, the ledger determines severity:

| Ledger evidence for the task | Code | Severity |
|---|---|---|
| Entry present with `matches: []` / `selected: null` | `STRICT_SDD_PLACEHOLDER_UNRESOLVABLE` | warning — correct placeholder; tenant lacks resource |
| No entry found (missing file or entries the reader cannot locate) | `STRICT_SDD_PLACEHOLDER_RESOLVED` | **error** — validation fails |

The ledger must be a bare top-level array; an unreadable envelope turns justified placeholders into `--sdd` failures. Expected warnings do not block the build. Cross-task bindings to nonexistent outputs still error, so fabricated task mocks are forbidden except for the sanctioned connector-rule stub.

## Upgrade Procedure — Placeholder → Full Task

> **Built-inline agents / API workflows / business rules are not placeholders.** A resource the user chose to **Create** at the Rule 18 gate is built and bound during planning ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery)), enters Phase 2 fully resolved, and skips this procedure. This procedure covers resources the user declined/skipped or whose build failed (register the real resource and recover as below), plus every other unresolved kind.

When the real resource is registered:

### 1. Re-pull the registry

**Confirm with the user via the `AskUserQuestion` tool before running**; force pull bypasses cache, is network-heavy, and may be slow. Then run:

```bash
uip maestro case registry pull --force
```

### 2. Resolve the task-type-id

Read the relevant cache directly per [registry-discovery.md](registry-discovery.md), such as `processOrchestration-index.json` or `action-apps-index.json`.

For a manually-built in-solution sibling (agent, api-workflow, or business-rule), run `uip maestro case registry search "<name>" --type <agent|api|businessRule> --local --output json` (`agent`, `api`, or `businessRule` respectively); select the exact-name `Data.Resources[].Resource`, and use `search`—`get --local` matches only opaque `entityKey`, not name. Its `Resource.EntityKey` is an opaque derived, audit-only key (not `.uipx` `Projects[].Id`); bind the node by name+folder. Read sibling I/O field names from raw `entry-points.json` (the `--output json` keys are PascalCased).

For an **api-workflow sibling**, read I/O using [api-workflow/planning.md § Registry Resolution](plugins/tasks/api-workflow/planning.md#registry-resolution): flat `entryPoints[0].input.properties` → `input.schema.document.properties` wrapper → `Workflow.json` root schemas when entry-point I/O is `null`; note any fallback in the report.

### 3. Fetch the schema

For non-connectors, run `uip maestro case tasks describe --type <type> --id <entityKey> --output json`. For connectors, run `uip maestro case registry get-connection` to obtain `connectionId`, then run `uip maestro case spec --type <activity|trigger> --activity-type-id <typeId> --connection-id <connId>` for unified identity, connection, inputs, outputs, filter, references, and populated `caseShape` when `--input-details` is supplied.

### 4. Edit the placeholder in place

Read `caseplan.case`, locate by `id`, and mutate only `data`; keep `id` and `elementId` unchanged so existing conditions and `selected-tasks-completed` rules remain valid.

| Task class | `data` mutation |
|---|---|
| `process`, `agent`, `rpa`, `api-workflow`, `function`, `business-rule`, `case-management` | Set `data.name`, `data.folderPath` (both `=bindings.<id>` refs); write `data.inputs[]` / `data.outputs[]` from `tasks describe`, each input initially `value: ""`. |
| `action` | Set `data.name`, `data.folderPath` (`=bindings.<id>`), `data.taskTitle`, `data.priority`, and `data.recipient` if known; write schema `data.inputs[]` / `data.outputs[]`. |
| `execute-connector-activity`, `wait-for-connector`, `external-agent`, `external-workflow` | Set `data.typeId`, `data.connectionId`; write `data.inputs[]` / `data.outputs[]` from `case spec` per the connector plugin's `impl-json.md`. |

Match the exact per-class shape in `plugins/tasks/<type>/impl-json.md`.

If many placeholders need upgrading, update `sdd.md` with missing context and re-invoke the skill from Phase 1; regeneration preserves declarative intent.

### 5. Bind inputs and outputs

Follow [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md):

1. Read `caseplan.case`; locate `data.inputs[]` by input `name`.
2. For literals/expressions from wiring notes (`foo = =metadata.x`), write the RHS string to `input.value`.
3. For cross-task references (`foo <- "Stage"."Task".output`), resolve the source output reference ID using [`io-binding/impl-json.md` § Output reference ID](plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative), then write `=vars.<outputReferenceId>` to the target `value`.
4. Write `caseplan.case` back.

### 6. Re-validate

Run:

```bash
uip maestro case validate <file> --strict --sdd sdd.md --output json
```

The no-configuration warning disappears when `data` is populated.

## Completion-Report Shape

When placeholders remain, list them explicitly:

```text
### Placeholder tasks (N)

| Stage | Task | Type | TaskId | Attach |
|-------|------|------|--------|--------|
| Submission Review | Validate Submission Completeness | process | t8GQTYo8O | processOrchestration-index.json — "Validate Submission Completeness" |
| Submission Review | Review Submission | action | ty5UcykfU | action-apps-index.json — "Review Submission" |
| … | … | … | … | … |

### External resources to register before upgrading placeholders

- **Processes** (N): Validate Submission Completeness, Route Submission Decision, Finalize Case Closure
- **Agents** (N): Classify Documents, Generate Carrier Emails, …
- **Action Apps** (N): Review Submission, Schedule Huddle Meeting, …
- **Custom IS connectors** (N): U Submit (GetSubmission), U Place (SubmitPlannedMarkets), …
```

Keep connector-catalog failures separate from build defects and missing resources ([connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx)):

```text
### Environment gaps (1)

- **Connector catalog unavailable** — Studio Web TypeCache (`studio_/typecache/api/Search/Catalog`) returned HTTP <STATUS> at <FAILURE_TIMESTAMP>; `registry pull` listed <INDEXES> in `Data.Errors`. <N> connector tasks and <N> event triggers are placeholders for this reason, not because a connector is missing. When the service recovers: `uip maestro case registry pull --force`, then upgrade per § Upgrade Procedure.
```

Report inline-built resources separately as resolved, not placeholders:

```text
### Agents / API workflows / business rules built inline (N)

| Stage | Task | Resource | Status |
|-------|------|----------|--------|
| Triage | Classify PO | Classify PO (agent) | built as in-solution sibling via uipath-agents; bound via --local |
| Enrich | Fetch Rates | RateFetcher (api-workflow) | built as in-solution sibling via uipath-api-workflow; bound via --local |

### Built but not referenced (reject case)

| Resource | Note |
|----------|------|
| Sentiment (agent) | built sibling on disk; task dropped from plan — reuse or remove manually |
```

Use placeholder/external lists to drive registration and upgrades. The built-inline list is informational because those resources are already wired.

## Anti-Patterns

- **Do NOT fabricate a task-type-id to silence the warning.** Validation may pass while runtime binding fails.
- **Do NOT partially bind inputs on a placeholder.** It has no `data.inputs[]`; the `io-binding` plugin logs `SKIPPED` and moves on.
- **Do NOT skip task-entry conditions on placeholders.** They are structural, use `TaskId`, and make workflow order visible.
- **Do NOT create placeholders for timer tasks.** Use the full `wait-for-timer` plugin.
- **Do NOT create a placeholder for an agent, API workflow, or business rule the user chose to build inline.** It is built and bound during planning ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery)).
- **Do NOT build an agent, API workflow, or business rule from SDD content alone.** Inline creation requires explicit selection at the Rule 18 gate; the result is an in-solution sibling that co-deploys with the case, never a separate tenant publish.
- **Invoking `uipath-agents` / `uipath-api-workflow` / `uipath-rules` for the inline build is sanctioned.** The "don't auto-invoke other skills" rule in `SKILL.md § Anti-patterns` still applies to every non-creatable kind (regular RPA process, action, function, case-management, connectors, agentic process) and to `uipath-planner`.

<!-- END: placeholder-tasks.md -->
