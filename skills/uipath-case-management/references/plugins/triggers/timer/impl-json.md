# timer trigger — JSON Implementation

Cross-cutting caseplan.json editing mechanics live in [`caseplan-editing.md`](../../../caseplan-editing.md).

## Purpose

Add a scheduled trigger to a case. Adapts shape to whether any Trigger node already exists in `schema.nodes`: emits the initial `trigger_1` minimal shape if none, or a secondary trigger with full render fields if one or more exist. Dual-file write: `caseplan.json` + `entry-points.json`.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `timeCycle` | yes | ISO 8601 repeating interval. Consumed verbatim — no parsing, no decomposition. |
| `displayName` | no | Defaults to `Trigger <N>` where `N = existingTriggerCount + 1`. |

## Adaptive recipe

Count existing Trigger nodes in `schema.nodes` **before** writing:

```text
existingTriggers = schema.nodes.filter(n => n.type === "case-management:Trigger")
```

### Case A — zero existing triggers (first-trigger path)

Emit the canonical first-trigger shape with the timer `uipath` block:

```json
{
  "id": "trigger_1",
  "type": "case-management:Trigger",
  "position": { "x": 0, "y": 0 },
  "data": {
    "label": "<displayName or \"Trigger 1\">",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timerType": "timeCycle",
      "timeCycle": "<timeCycle from tasks.md>"
    }
  }
}
```

No `style`, no `measured`, no `width`/`height`, no `data.parentElement`. Studio Web hydrates these on load.

### Case B — one or more existing triggers (secondary-trigger path)

Emit a secondary trigger with full render fields:

```json
{
  "id": "trigger_<6-rand>",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": <computed> },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "<displayName or \"Trigger <N>\">",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timerType": "timeCycle",
      "timeCycle": "<timeCycle from tasks.md>"
    }
  }
}
```

**Position `y` computation:**

```text
y = max(existingTriggers[i].position.y) + 140
```

When the only existing trigger is a `trigger_1` at `{x: 0, y: 0}`, the first secondary timer trigger lands at `{x: -100, y: 140}`.

The `x` coordinate is always `-100`.

## `entry-points.json` append (required in both cases)

Locate `entry-points.json` adjacent to `caseplan.json` (same directory). Append one entry:

```json
{
  "filePath": "/content/<caseplan-basename>.bpmn#<triggerId>",
  "uniqueId": "<UUID v4>",
  "type": "CaseManagement",
  "input":  { "type": "object", "properties": {} },
  "output": { "type": "object", "properties": {} },
  "displayName": "<same as node.data.label>"
}
```

- `<caseplan-basename>` — the literal filename of the case file (typically `caseplan.json`), producing a path like `/content/caseplan.json.bpmn#trigger_xxxxxx`.
- `<UUID v4>` — fresh `crypto.randomUUID()` per write. Non-deterministic; normalizer strips in golden diff.
- `displayName` matches `node.data.label` (including the `Trigger <N>` default if `displayName` absent).

**Write order:** `caseplan.json` first, then `entry-points.json`. If the second write fails, the skill surfaces the inconsistency to the user rather than silently half-applying.

## ID generation

- First-trigger path: literal `trigger_1` (no randomness).
- Secondary path: `trigger_` prefix + 6 random chars per [`caseplan-editing.md § ID Generation`](../../../caseplan-editing.md#id-generation).

Record `T<n> → <triggerId>` in `id-map.json` for downstream cross-reference.

## Post-write validation

After writing, confirm:

- `schema.nodes` contains the new Trigger node with the expected `id`
- `node.data.uipath.serviceType == "Intsvc.TimerTrigger"`
- `node.data.uipath.timerType == "timeCycle"`
- `node.data.uipath.timeCycle` is byte-identical to the input string
- For Case A: node has no `style`/`measured`/`width`/`height`/`data.parentElement`
- For Case B: `style == measured == {width: 96, height: 96}` and `data.parentElement == {id: "root", type: "case-management:root"}`
- `entry-points.json.entryPoints` has a new entry with `filePath` containing the new `triggerId` and `displayName` matching `node.data.label`

Run `uip maestro case validate <file> --output json` after all triggers for this plugin's batch are added.

## Validation

- [x] **Structural validity:** `uip maestro case validate` passes on output (expected failure profile for a triggers-only fragment with no stages/edges until downstream plugins run).
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised.
