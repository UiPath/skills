# manual trigger — JSON Implementation

Cross-cutting caseplan.json editing mechanics live in [`caseplan-editing.md`](../../../caseplan-editing.md).

## Purpose

Append one secondary manual trigger to the schema. This plugin performs **two file writes as an atomic pair**:

1. Append a `case-management:Trigger` node to `caseplan.json.nodes`.
2. Append a matching entry to `entry-points.json.entryPoints` (sibling of `caseplan.json`).

The sibling-file sync is the main reason this plugin needs a dedicated JSON recipe rather than reusing a generic "add node" primitive — orchestrator discovers entry points via `entry-points.json`, so a trigger node without a matching entry is invisible to runtime.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `displayName` | yes | T-entry title or `display-name:` field. Fallback: `Trigger ${existingTriggerCount + 1}`. |
| `description` | yes | Always emitted into `data.description`. Sourced from the T-entry's `description:` field when present; otherwise the LLM infers a natural-language description from surrounding sdd.md context. Never omit the key. |

Position is not a user input. It is computed statefully (see below).

## Pre-flight

1. **`caseplan.json` exists** at `<SolutionDir>/<ProjectName>/caseplan.json`. Created by the `case` plugin (T01 scaffold). If absent, run that plugin first — do not synthesize.
2. **`entry-points.json` exists** in the same directory (sibling of `caseplan.json`). Created by the `case` plugin at T01 scaffold. If absent, **fail hard**: `entry-points.json not found in <dir>. Re-run the case plugin (T01) to scaffold the project first.` Do not lazily create it — a missing `entry-points.json` indicates an incomplete project scaffold, not a recoverable state.
3. Both files must be parseable JSON. Read → validate → modify → write.

## ID generation

- **Trigger node ID** — `trigger_` + 6 random chars from `[A-Za-z0-9]`. Algorithm per [`caseplan-editing.md § ID Generation`](../../../caseplan-editing.md#id-generation).
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

The `length === 0` branch fires when the manual plugin is the first trigger added (primary trigger path). When one or more triggers already exist, the new trigger sits at `y = max(existing y) + 140`.

Do not short-circuit to a hard-coded `y=140` — the algorithm must handle any schema state the upstream mutations may have produced.

## Default-name fallback

If the T-entry does not supply `display-name`:

```text
displayName = `Trigger ${existingTriggers.length + 1}`
```

The first trigger without a display name becomes `"Trigger 1"`, the second `"Trigger 2"`, etc.

## Recipe — `caseplan.json` (append to `schema.nodes`)

Append (not prepend):

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

Write back with **4-space indent** (`JSON.stringify(obj, null, 4)`). The scaffold path initializes `entry-points.json` at 2-space indent; the append path uses 4-space. Match the append path here.

## Write order

Write both files atomically in this order:

1. `caseplan.json` — node appended.
2. `entry-points.json` — entry appended.

If the second write fails, the `caseplan.json` mutation must be rolled back to avoid a half-written state. Simplest rollback: re-read the `caseplan.json` that existed pre-mutation (kept in memory), write it back. Preferred posture: verify `entry-points.json` exists BEFORE the first write (fail-fast).

## Post-write validation

After writing, confirm:

- `caseplan.json.nodes` contains the new node with the generated `trigger_XXXXXX` id, at the end of the array.
- `nodes[].type === "case-management:Trigger"`.
- `nodes[].data.label` matches the resolved `displayName`.
- `nodes[].data.description` is present and non-empty (always emitted).
- `nodes[].data.parentElement`, `style`, `measured` all present with the documented values.
- `nodes[].data.uipath` is **absent** (manual triggers have no `uipath` key).
- `entry-points.json.entryPoints` contains a new entry with `filePath` ending in `#<trigger_XXXXXX>` and `displayName === <displayName>`.

Run `uip maestro case validate <caseplan.json> --output json` after all triggers for this plugin's batch are added.

## Design notes

- **`data.description` is always emitted.** Write either the sdd.md-supplied string or an LLM-inferred one — never omit the key.
- **Atomic dual-file write with rollback.** Pre-check that `entry-points.json` exists (fail-fast). Keep an in-memory rollback copy of `caseplan.json`; if the second write fails, rewrite the pre-mutation contents.

## Validation

- [x] **Structural validity:** `uip maestro case validate` passes on output (expected profile: 1 error — `Trigger has no outgoing edges` — per trigger until edges are added).
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised.
