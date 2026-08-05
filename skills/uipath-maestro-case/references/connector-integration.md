# Connector Integration Reference

Selector for Case connector targets. This file chooses an owner; it does not duplicate that owner's discovery or JSON algorithm.

## When to Use

Select exactly one target before loading details:

| Target | Planning owner | Implementation owner |
|---|---|---|
| Connector activity task | [`connector-activity/planning.md`](plugins/tasks/connector-activity/planning.md) | [`connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md) |
| In-stage `wait-for-connector` task | [`connector-trigger-planning.md`](connector-trigger-planning.md#planning-pipeline) + [`connector-trigger/planning.md`](plugins/tasks/connector-trigger/planning.md) | [`connector-trigger-impl.md`](connector-trigger-impl.md) + [`connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md) |
| Case-level event trigger | trigger planning owner + [`event/planning.md`](plugins/triggers/event/planning.md) | trigger implementation owner + [`event/impl-json.md`](plugins/triggers/event/impl-json.md) |
| Connector-bound condition rule | trigger planning owner + the selected condition plugin | [`connector-trigger-impl.md` condition target](connector-trigger-impl.md#target-connector-bound-condition-rule) + that same condition plugin |

`case-spec-input-details.md` remains the Case-local schema owner for `--input-details`; target owners link it directly when needed.

## Prerequisites

Enter the selected planning owner only after the SKILL Rule 3 gate. It consumes Rule 17 and distinguishes TypeCache zero-match from an existing connector with no connection.

## Resolution Pipeline

### Step 1 — Find the activity-type-id

Activities route to their planning owner; event, wait-task, and connector-rule targets route to `connector-trigger-planning.md`. Do not resolve one through another target.

### Step 2 — Resolve the connection

Follow activity planning Step 2 or trigger planning Step 2. Each target owns its response.

#### Creating a Connection

Connection creation and its Retry / Skip fallback belong to the selected planning owner. An empty connection list routes there; it is not a missing connector type or a Rule 17 zero.

### Step 3 — Discover the operation contract via `case spec`

Planning uses the selected owner's lean call. Phase 3 raw-cache execution routes to activity implementation or `connector-trigger-impl.md`; [implementation Step 9.7](implementation.md#step-97--connector-eventtask-detail-raw-cache-gather-then-splice) orchestrates the batches.

### Step 4 — Resolve reference fields

Reference discovery and required-field mapping belong to the selected planning owner.

---

## Applying Results to caseplan.json

Do not compose connector JSON here. The selected implementation owner reads its target cache, applies the common splice contract, and writes its own envelope.

## Filter Authoring

Activity input and filter authoring is owned by the activity planning/implementation pair. Trigger FilterTree authoring is owned by `connector-trigger-planning.md`.

## Output Contract to Tasks.md

Use the selected planning owner's `tasks.md` format. Target-specific planning files own their envelope fields; the shared trigger owner owns the shared trigger metadata and filter contract.

<!-- END: connector-integration.md -->
