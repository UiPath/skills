# connector-trigger task — Planning

> **Required reads** — open each in full (a single `cat`, or the `Read` tool) before writing this
> construct. These are not optional context; the checks that grade this work live in them.
> - [`connector-trigger-planning.md`](../../../connector-trigger-planning.md) — connector resolution before you write the rule

A connector-based trigger **inside a stage** — waits for an external event before continuing.

The planning pipeline is shared with the [event trigger](../../triggers/event/planning.md) — see [connector-trigger-planning.md](../../../connector-trigger-planning.md) for the full resolution pipeline (TypeCache lookup → connection pick → `case spec` discovery → reference resolution → required-field gate → SDD mapping → input-values + filter authoring).

## When to Use

Pick this plugin when the sdd.md describes a task that **suspends the stage until an external event fires**:

- "Wait until a new row appears in Salesforce"
- "Continue when a Slack reaction is added"
- "Suspend until an email arrives in Inbox"

Distinguish from:

- **Case-level event triggers** (start the case from outside) → [`plugins/triggers/event/`](../../triggers/event/planning.md)
- **Connector activity** (call out, don't wait) → [connector-activity](../connector-activity/planning.md)
- **Timer wait** (not connector-driven) → [wait-for-timer](../wait-for-timer/planning.md)

## Resolution Pipeline

Follow the pipeline in [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline). All steps are identical for both in-stage triggers and case-level event triggers.

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 9's keys plus the resolved connector fields:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "connector-trigger",
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

`event-mode` is `polling` or `webhooks`; `input-values` and `filter` are real JSON objects, not strings.

Output bindings are **not** recorded here: they come from the SDD Outputs table through the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list), which is a reasoning form and never written to disk. Required, run-only-once, activation mode (`event-triggered`), entry rule (`wait-for-connector`), and lane likewise stay in `sdd.md` ([planning.md § Step 4](../../../planning.md)).

## Unresolved Fallback

Two entry paths: **Scenario A** — connector not found in TypeCache ([connector-trigger-planning.md § 1 No-match](../../../connector-trigger-planning.md#1-find-the-trigger-in-typecache), after the Rule 17 gate); **Scenario B** — connector found but connection unresolved, only after the create offer ([connector-trigger-planning.md § Resolve the connection](../../../connector-trigger-planning.md#2-resolve-the-connection)) is **declined** or fails. When `Connections` is empty, offer to create one first — do not jump straight here.

> **Rule 17 exception.** Empty `Connections` from `get-connection` (the connector trigger exists in typecache but no IS connection is registered) does NOT require the Rule 17 gate — proceed directly to placeholder.

If the connector or connection cannot be resolved:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` and `filter:`
- Execution creates a placeholder task (display-name + type only) per [placeholder-tasks.md](../../../placeholder-tasks.md)

<!-- END: planning.md -->
