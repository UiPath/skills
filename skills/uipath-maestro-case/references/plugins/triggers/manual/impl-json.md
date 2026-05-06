---
direct-json: supported
---

# manual trigger — JSON Implementation

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../../case-editing-operations.md).

> **v20 layout-strip (Rule 19).** Read `Schema:` header from `tasks.md`. In **v20 mode**, omit ALL of: `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Skip the position-computation step entirely. Keep `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`, `data.label`, `data.description`, `data.uipath`. Recipe shapes below show v19 fields; in v20 mode strip the listed render fields and skip position math. `entry-points.json` shape is identical across schemas.

## Purpose

Append one secondary manual trigger to the schema. This plugin performs **two file writes as an atomic pair**:

1. Append a `case-management:Trigger` node to `caseplan.json.nodes`.
2. Append a matching entry to `entry-points.json.entryPoints` (sibling of `caseplan.json`).

The sibling-file sync is the main reason this plugin needs a dedicated JSON recipe rather than reusing a generic "add node" primitive — orchestrator discovers entry points via `entry-points.json`, so a trigger node without a matching entry is invisible to runtime.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `displayName` | yes | T-entry title or `display-name:` field. Fallback: `Trigger ${existingTriggerCount + 1}`. The first manual trigger written into a fresh caseplan therefore defaults to `"Trigger 1"`. |
| `description` | yes | Always emitted into `data.description`. Sourced from the T-entry's `description:` field when present; otherwise the LLM infers a natural-language description from surrounding sdd.md context. |

Position is not a user input. It is computed statefully (see below).

## Pre-flight

1. **`caseplan.json` exists** at `<SolutionDir>/<ProjectName>/caseplan.json`. Created by the `case` plugin at T01. If absent, run that plugin first — do not synthesize.
2. **`entry-points.json` exists** in the same directory (sibling of `caseplan.json`). Written by the `case` plugin's § Scaffold at T01. If absent, hard-fail (`entry-points.json not found in <dir>. Run the case plugin first to scaffold the project.`). Do not lazily create it — a missing `entry-points.json` indicates an incomplete project scaffold, not a recoverable state.
3. Both files must be parseable JSON. Read → validate → modify → write.

## ID generation

- **Trigger node ID** — `trigger_` + 6 random chars from `[A-Za-z0-9]`. Algorithm per [`case-editing-operations.md § ID Generation`](../../../case-editing-operations.md#id-generation).
- **Entry-point `uniqueId`** — `crypto.randomUUID()`. Generate inline:

  ```bash
  node -e "console.log(crypto.randomUUID())"
  ```

Record `T<n> → trigger_xxxxxx` in `id-map.json` for downstream cross-reference (edges that target this trigger's id).

## Position (stateful)

**Before writing**, count every trigger node:

```text
existingTriggers = schema.nodes.filter(n => n.type === "case-management:Trigger")
```

Then compute:

```text
if existingTriggers.length === 0:
  position = { x: -100, y: 200 }
else:
  position = { x: -100, y: max(existingTriggers[].position.y) + 140 }
```

The `length === 0` branch fires for the primary trigger written into a fresh caseplan (case plugin emits `nodes: []`). Subsequent triggers fall into the `else` branch, stacking at `y + 140` each time.

Do not short-circuit to a hard-coded `y` value — the algorithm must handle any schema state the upstream mutations may have produced.

## Default-name fallback

If the T-entry does not supply `display-name`:

```text
displayName = `Trigger ${existingTriggers.length + 1}`
```

With `trigger_1` pre-seeded, the first secondary trigger without a display name becomes `"Trigger 2"`, the second `"Trigger 3"`, etc.

## Recipe — `caseplan.json` (append to `schema.nodes`)

Append (not prepend) the trigger node:

```json
{
  "id": "<trigger_XXXXXX>",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": <computed> },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "<displayName>",
    "description": "<description from sdd.md or LLM-inferred>"
  }
}
```

**No `data.uipath` key.** Absence of `uipath` is the manual trigger's signature. `serviceType` only appears on timer (`Intsvc.TimerTrigger`) and event (`Intsvc.EventTrigger`) variants.

## Recipe — `entry-points.json` (append to `entryPoints`)

Read the file, parse, append:

```json
{
  "filePath": "/content/<basename(caseplanFile)>.bpmn#<trigger_XXXXXX>",
  "uniqueId": "<crypto.randomUUID()>",
  "type": "CaseManagement",
  "input":  { "type": "object", "properties": {} },
  "output": { "type": "object", "properties": {} },
  "displayName": "<displayName>"
}
```

Where `basename(caseplanFile)` is the schema file's base name including extension (typically `caseplan.json`), yielding a `filePath` fragment like `/content/caseplan.json.bpmn#trigger_xY2mNp`.

Write back with **4-space indent** (`JSON.stringify(obj, null, 4)`).

## Write order

Write both files atomically in this order:

1. `caseplan.json` — node appended.
2. `entry-points.json` — entry appended.

If the second write fails, the `caseplan.json` mutation must be rolled back to avoid a half-written state. Simplest rollback: re-read the `caseplan.json` that existed pre-mutation (kept in memory), write it back. Prefer fail-fast: verify `entry-points.json` exists BEFORE the first write.

## Post-write validation

After writing, confirm:

- `caseplan.json.nodes` contains the new node with the generated `trigger_XXXXXX` id, at the end of the array.
- `nodes[].type === "case-management:Trigger"`.
- `nodes[].data.label` matches the resolved `displayName`.
- `nodes[].data.description` is present and non-empty (direct-JSON-write divergence — always emitted).
- `nodes[].data.parentElement` always present. `style`, `measured` present in v19; absent in v20 (Rule 19).
- `nodes[].data.uipath` is **absent** (manual triggers have no `uipath` key).
- `entry-points.json.entryPoints` contains a new entry with `filePath` ending in `#<trigger_XXXXXX>` and `displayName === <displayName>`.

Run `uip maestro case validate <caseplan.json> --output json` after all triggers for this plugin's batch are added.

