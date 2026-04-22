---
direct-json: supported
---

# timer trigger — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../../case-editing-operations.md) lists `triggers/timer = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

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

Emit the initial `trigger_1` shape. This is the canonical first-trigger shape produced by `uip maestro case cases add` today (see [`cli/packages/case-tool/src/commands/cases.ts`](https://github.com/UiPath/uipath-cli) `buildMinimalSchema`), extended with the timer `uipath` block:

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

When the only existing trigger is the CLI-seeded `trigger_1` at `{x: 0, y: 0}`, the first secondary timer trigger lands at `{x: -100, y: 140}`.

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

**Write order:** `caseplan.json` first, then `entry-points.json`. Matches CLI's `saveTrigger` order — if the second write fails, the skill surfaces the inconsistency to the user rather than silently half-applying.

## ID generation

- First-trigger path: literal `trigger_1` (no randomness).
- Secondary path: `trigger_` prefix + 6 random chars per [`case-editing-operations-json.md § ID Generation`](../../../case-editing-operations-json.md#id-generation).

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

## Known CLI divergences

None functional. JSON recipe mirrors CLI output exactly for the secondary-trigger path. The first-trigger path (Case A) is not reachable via CLI `triggers add-timer` today — the CLI always appends a secondary because `cases add` pre-seeds `trigger_1` as a manual trigger. The JSON recipe's Case A exists to support the upcoming `case` plugin migration that will stop auto-seeding `trigger_1`; until that lands, only Case B is exercised.

## Compatibility

Captured against CLI version `0.1.21`. See [`docs/uipath-case-management/migration-fixtures/timer/`](../../../../../../docs/uipath-case-management/migration-fixtures/timer/) for fixtures.

- [x] **Golden diff:** normalized `json-write-output/` matches `cli-output/` after trigger-ID + UUID normalization — `docs/uipath-case-management/migration-fixtures/timer/diff.sh` passes
- [x] **Validation parity:** both outputs produce the same set of errors/warnings from `uip maestro case validate` (expected failure profile for a triggers-only fragment with no stages/edges)
- [ ] **Downstream CLI mutation append:** `uip maestro case edges add --source <json-written-trigger-id>` and friends accept the JSON-written node — not yet exercised
- [ ] **Round-trip:** CLI-written timer → direct-JSON-write adds a second timer → validate passes with only expected failures — not yet exercised
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised
