# event trigger — Planning

> **Required reads** — open each in full (a single `cat`, or the `Read` tool) before writing this
> construct. These are not optional context; the checks that grade this work live in them.
> - [`connector-trigger-planning.md`](../../../connector-trigger-planning.md) — connector resolution before you write the rule

A case-level trigger that fires on an external connector event. Starts the case when the event matches a filter.

The planning pipeline is shared with the [connector-trigger task](../../tasks/connector-trigger/planning.md) — see [connector-trigger-planning.md](../../../connector-trigger-planning.md) for the full 7-step resolution pipeline.

## When to Use

Pick this plugin when the sdd.md describes the case as starting in response to an external event:

- "When a new email arrives in Inbox"
- "On each new Jira issue with priority High"
- "When a file is uploaded to SharePoint"

Distinguish from:

- **User-initiated start** → [manual](../manual/planning.md)
- **Scheduled start** → [timer](../timer/planning.md)
- **In-stage event wait** → [connector-trigger task](../../tasks/connector-trigger/planning.md)

## Resolution Pipeline

Follow the pipeline in [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline). All steps are identical for both event triggers and in-stage connector-trigger tasks.

## Fields to Resolve

T-number is T02 for the first trigger row in sdd.md, T03+ for subsequent rows in multi-trigger cases — see [planning.md Case Triggers](../../../planning.md).

Ledger entry in `tasks/registry-resolved.json` — Rule 9's keys plus the resolved connector fields:

```json
{
  "stage": null,
  "task": "<display-name>",
  "taskType": "event-trigger",
  "cacheFile": "typecache-triggers-index.json",
  "searchQuery": "<trigger display name>",
  "matches": [],
  "selected": {},
  "type-id": "<uiPathActivityTypeId>",
  "connection-id": "<connection-uuid>",
  "connector-key": "<connectorKey>",
  "object-name": "<objectName>",
  "event-operation": "<eventOperation>",
  "event-mode": "polling",
  "input-values": { "eventParameters": { "parentFolderId": "AAMkADNm..." } },
  "filter": { "groupOperator": "And", "index": 0, "uuId": null, "filters": [{ "id": "subject", "operator": "Contains", "value": { "isLiteral": true, "rawString": "\"urgent\"", "value": "urgent" }, "uiId": null }] },
  "rationale": "<why this trigger and connection were selected>"
}
```

A case-level trigger has no stage, so `stage` is `null`. `event-mode` is `polling` or `webhooks`; `input-values` and `filter` are real JSON objects, not strings. The display name and description stay in `sdd.md` ([planning.md § Step 4](../../../planning.md)).

## Unresolved Fallback

Two entry paths: **Scenario A** — connector not found in TypeCache ([connector-trigger-planning.md § 1 No-match](../../../connector-trigger-planning.md#1-find-the-trigger-in-typecache), after the Rule 17 gate); **Scenario B** — connector found but connection unresolved, only after the create offer ([connector-trigger-planning.md § Resolve the connection](../../../connector-trigger-planning.md#2-resolve-the-connection)) is **declined** or fails. When `Connections` is empty, offer to create one first — do not jump straight here.

> **Rule 17 exception.** Empty `Connections` from `get-connection` (the trigger activity exists in typecache but no IS connection is registered) does NOT require the Rule 17 gate — proceed directly to placeholder.

> **Planning emits the element; execution emits a placeholder trigger node.** "Cannot resolve the connector / connection yet" is not a reason to drop the trigger from `caseplan.json` — the no-omission rule (planning.md completeness principle) applies to triggers the same as it does to stages, tasks, and conditions. The pattern mirrors the connector-trigger task placeholder in [placeholder-tasks.md](../../../placeholder-tasks.md): structure preserved, runtime config deferred.

If the connector or connection cannot be resolved:
- Mark **every connector-derived field** with `<UNRESOLVED: reason>` in the element — `type-id`, `connection-id`, `connector-key`, `object-name`, `event-operation`, and `event-mode` all derive from the connector / connection lookup, so when the connector itself is unresolved, none of them have authoritative values. Mark each one explicitly rather than omitting them (so the user sees the full attach checklist when upgrading).
- Omit `input-values:` and `filter:` from the element — there is no schema to wire against.
- **Execution creates a placeholder trigger node** with `serviceType: "Intsvc.EventTrigger"` as the only `data.inputs` field (no `context[]`, `metadata`, `inputs`, `outputs`, or `bindings`). The node carries `id`, `display.label`, `description`, `parentElement`, `typeVersion`, and standard render fields so the FE renders it as an event trigger awaiting attachment. See [`impl-json.md` § Placeholder fallback](impl-json.md#placeholder-fallback-unresolved-connector--connection).
- The matching `entry-points.json` entry **is still appended** — entry-points are structural BPMN references and do not depend on connector resolution.
- **No trigger-edge is created** (Rule 20). The first stage's `case-entered` entry condition starts the case regardless of whether this trigger is resolved or a placeholder.
- Document the missing trigger and its `<UNRESOLVED>` fields in the completion report so the user knows what to attach after registering the IS connection.

<!-- END: planning.md -->
