---
direct-json: supported
---

# manual trigger — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../../case-editing-operations.md) lists `triggers/manual = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

## Purpose

Append one secondary manual trigger to the schema. This plugin performs **two file writes as an atomic pair**:

1. Append a `case-management:Trigger` node to `caseplan.json.nodes`.
2. Append a matching entry to `entry-points.json.entryPoints` (sibling of `caseplan.json`).

The sibling-file sync is the main reason this plugin needs a dedicated JSON recipe rather than reusing a generic "add node" primitive — orchestrator discovers entry points via `entry-points.json`, so a trigger node without a matching entry is invisible to runtime.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `displayName` | yes | T-entry title or `display-name:` field. Fallback: `Trigger ${existingTriggerCount + 1}`. Because `cases add` seeds `trigger_1`, the first secondary trigger's default name is `"Trigger 2"`. |
| `description` | yes | Always emitted into `data.description`. Sourced from the T-entry's `description:` field when present; otherwise the LLM infers a natural-language description from surrounding sdd.md context. **Deliberate divergence from CLI** — CLI emits `description` only when the flag is passed. |

Position is not a user input. It is computed statefully (see below).

## Pre-flight

1. **`caseplan.json` exists** at `<SolutionDir>/<ProjectName>/caseplan.json`. Created by the `case` plugin (scaffolding + `cases add`). If absent, run that plugin first — do not synthesize.
2. **`entry-points.json` exists** in the same directory (sibling of `caseplan.json`). Created by `uip maestro case init`. If absent, **fail hard with the same error message the CLI emits** (`entry-points.json not found in <dir>. Run 'uip maestro case init' to create a project first.`). Do not lazily create it — a missing `entry-points.json` indicates an incomplete project scaffold, not a recoverable state.
3. Both files must be parseable JSON. Read → validate → modify → write.

## ID generation

- **Trigger node ID** — `trigger_` + 6 random chars from `[A-Za-z0-9]`. Algorithm per [`case-editing-operations-json.md § ID Generation`](../../../case-editing-operations-json.md#id-generation).
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

The `length === 0` branch is unreachable after `cases add` (which seeds `trigger_1` at y=0). In practice every secondary trigger takes the `else` branch. First secondary therefore sits at `y = 0 + 140 = 140`. Second secondary at `y = max(0, 140) + 140 = 280`. And so on.

Match the CLI exactly. Do not short-circuit to a hard-coded `y=140` for the first secondary — the algorithm must handle any schema state the upstream mutations may have produced.

## Default-name fallback

If the T-entry does not supply `display-name`:

```text
displayName = `Trigger ${existingTriggers.length + 1}`
```

With `trigger_1` pre-seeded, the first secondary trigger without a display name becomes `"Trigger 2"`, the second `"Trigger 3"`, etc.

## Recipe — `caseplan.json` (append to `schema.nodes`)

CLI uses `.push()` — append (not prepend). Match it:

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

Write back with **4-space indent** (matching CLI's `appendEntryPoint` — `JSON.stringify(obj, null, 4)`). This diverges from `init.ts` which seeds the file at 2-space indent; CLI is inconsistent with itself. Match the append path, not the init path, for byte-closer goldens.

## Write order

Write both files atomically in this order:

1. `caseplan.json` — node appended.
2. `entry-points.json` — entry appended.

If the second write fails, the `caseplan.json` mutation must be rolled back to avoid a half-written state. Simplest rollback: re-read the `caseplan.json` that existed pre-mutation (kept in memory), write it back. The CLI does not implement rollback — it just hard-fails early if `entry-points.json` is absent. Prefer the same fail-fast posture: verify `entry-points.json` exists BEFORE the first write.

## Post-write validation

After writing, confirm:

- `caseplan.json.nodes` contains the new node with the generated `trigger_XXXXXX` id, at the end of the array.
- `nodes[].type === "case-management:Trigger"`.
- `nodes[].data.label` matches the resolved `displayName`.
- `nodes[].data.description` is present and non-empty (direct-JSON-write divergence — always emitted).
- `nodes[].data.parentElement`, `style`, `measured` all present with the documented values.
- `nodes[].data.uipath` is **absent** (manual triggers have no `uipath` key).
- `entry-points.json.entryPoints` contains a new entry with `filePath` ending in `#<trigger_XXXXXX>` and `displayName === <displayName>`.

Run `uip maestro case validate <caseplan.json> --output json` after all triggers for this plugin's batch are added.

## Known CLI divergences

Direct-JSON-write is a superset of the CLI's `triggers add-manual`. Divergences below are deliberate.

- **`data.description` is always emitted.** CLI writes `data.description` only when the `--description` flag is passed. JSON path always emits — either the sdd.md-supplied string or an LLM-inferred one. Golden diff normalizes `description: ""` / absent so equivalence holds.
- **Both files are written atomically.** CLI hard-fails on missing `entry-points.json` but does not roll back `caseplan.json` if the entry-points append fails after schema write. JSON path pre-checks and keeps an in-memory rollback copy; same observable contract (file state converges) but safer failure mode.

## Compatibility

Captured against CLI version `0.1.21`.

- [x] **Golden parity (ad-hoc):** manual side-by-side comparison of `uip maestro case triggers add-manual` output against direct-JSON-write output passed for both `caseplan.json` (trigger node appended) and `entry-points.json` (matching entry appended) after ID + UUID normalization at the time this plugin was migrated.
- [x] **Validation parity:** both outputs produce the same set of errors + warnings from `uip maestro case validate` (expected profile: 1 error — `Trigger has no outgoing edges` — per trigger, no other changes)
- [ ] **Downstream JSON/CLI append:** edges plugin (now JSON — see [plugins/edges/impl-json.md](../../edges/impl-json.md)) accepts a `trigger_XXXXXX` id produced here as `source` — not yet exercised end-to-end in a combined fixture
- [ ] **Round-trip:** CLI-written trigger → direct-JSON-write adds a second trigger → validate passes with only the expected failures — not yet exercised
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised
