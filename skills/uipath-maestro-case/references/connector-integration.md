# Connector Integration Reference

Selector for Case connector targets. This file chooses an owner; it does not duplicate that owner's discovery or JSON algorithm.

## When to Use

Select exactly one target before loading details:

| Target | Planning owner | Implementation owner |
|---|---|---|
| Connector activity task | [`connector-activity/planning.md`](plugins/tasks/connector-activity/planning.md) | [`connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md) |
| In-stage `wait-for-connector` task | [`connector-trigger-common.md`](connector-trigger-common.md#planning-pipeline) + [`connector-trigger/planning.md`](plugins/tasks/connector-trigger/planning.md) | common owner + [`connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md) |
| Case-level event trigger | common owner + [`event/planning.md`](plugins/triggers/event/planning.md) | common owner + [`event/impl-json.md`](plugins/triggers/event/impl-json.md) |
| Connector-bound condition rule | common owner + the selected condition plugin | [`connector-trigger-common.md` condition target](connector-trigger-common.md#target-connector-bound-condition-rule) + that same condition plugin |

`case-spec-input-details.md` remains the Case-local schema owner for `--input-details`; target owners link it directly when needed.

## Prerequisites

Enter the selected planning owner only after the SKILL Rule 3 gate. It consumes Rule 17 and distinguishes TypeCache zero-match from an existing connector with no connection.

## Resolution Pipeline

### Step 1 — Find the activity-type-id

Activities route to their planning owner; event, wait-task, and connector-rule targets route to the trigger common. Do not resolve one through another target.

### Step 2 — Resolve the connection

Follow activity planning Step 2 or trigger common Step 2. Each target owns its response.

#### Creating a Connection

Connection creation and its Retry / Skip fallback belong to the selected planning owner. An empty connection list routes there; it is not a missing connector type or a Rule 17 zero.

### Step 3 — Discover the operation contract via `case spec`

Planning uses the selected owner's lean call. Phase 3 raw-cache execution routes to activity implementation or trigger common; [implementation Step 9.7](implementation.md#step-97--connector-eventtask-detail-raw-cache-gather-then-splice) orchestrates the batches.

### Step 4 — Resolve reference fields

Reference discovery and required-field mapping belong to the selected planning owner.

---

## Applying Results to caseplan.json

Do not compose connector JSON here. The selected implementation owner reads its target cache, applies the common splice contract, and writes its own envelope.

## Filter Authoring

For an activity with array objects, multipart files, or a requested supported server filter, its owner conditionally loads [`complex-inputs-guide.md`](plugins/tasks/connector-activity/complex-inputs-guide.md). Scalar activities without filters do not. Trigger FilterTree authoring stays in `connector-trigger-common.md`.

## Output Contract to Tasks.md

Use the selected planning owner's `tasks.md` format. Target-specific planning files own their envelope fields; the shared trigger owner owns the shared trigger metadata and filter contract.
