# timer trigger — JSON Implementation

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../../case-editing-operations.md).

> **Layout-strip (Rule 18).** Omit `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Keep `data.parentElement` (when applicable per Case A vs B below), `data.isInvalidDropTarget`, `data.isPendingParent`, `data.typeVersion`, `data.display`, `data.description`, `data.inputs`.

## Purpose

Add a scheduled trigger to a case. Adapts shape to whether any Trigger node already exists in `schema.nodes`: emits the initial `trigger_1` minimal shape if none, or a secondary trigger with full render fields if one or more exist. Dual-file write: `caseplan.json` + `entry-points.json`.

## Input spec (from `sdd.md`)

| Field | Required | Notes |
|---|---|---|
| `timeCycle` | yes | ISO 8601 repeating interval. Consumed verbatim — no parsing, no decomposition. |
| `displayName` | no | Defaults to `Trigger <N>` where `N = existingTriggerCount + 1`. |
| `description` | no | Free-text; from sdd.md or LLM-inferred. Mirrors the manual-trigger `data.description` field. |

## Adaptive recipe

Count existing Trigger nodes in `schema.nodes` **before** writing:

```text
existingTriggers = schema.nodes.filter(n => n.type === "uipath.case.trigger")
```

### Case A — zero existing triggers (first-trigger path)

Emit the canonical first-trigger shape with the timer `uipath` block:

```json
{
  "id": "trigger_1",
  "type": "uipath.case.trigger",
  "data": {
    "description": "<description from sdd.md or LLM-inferred>",
    "typeVersion": "1.0.0",
    "display": { "label": "<displayName or \"Trigger 1\">" },
    "inputs": {
      "serviceType": "timer",
      "timerType": "timeCycle",
      "timeCycle": "<timeCycle from sdd.md>"
    }
  }
}
```

No `data.parentElement` in Case A. Studio Web hydrates layout on load.

### Case B — one or more existing triggers (secondary-trigger path)

Emit a secondary trigger with `data.parentElement` included:

```json
{
  "id": "trigger_<6-rand>",
  "type": "uipath.case.trigger",
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "description": "<description from sdd.md or LLM-inferred>",
    "typeVersion": "1.0.0",
    "display": { "label": "<displayName or \"Trigger <N>\">" },
    "inputs": {
      "serviceType": "timer",
      "timerType": "timeCycle",
      "timeCycle": "<timeCycle from sdd.md>"
    }
  }
}
```

**In-argument bridges live on `data.inputs.outputs[]` — never on `data.outputs`.** When the SDD declares an In argument bound to this trigger, three entries are emitted together ([`global-vars/impl-json.md` § In argument](../../variables/global-vars/impl-json.md)): the formal slot in `root.inputs[]`, the companion in `root.inputOutputs[]`, and the **bridge** on this node at `data.inputs.outputs[]`. The bridge is what copies the value at fire time; a `data.outputs[]` array beside `data.inputs` is not read by anything and the In argument silently never arrives. `uip maestro case validate` does not catch it.

```json
"data": {
  "inputs": {
    "serviceType": "timer",
    "outputs": [
      { "name": "<argName>", "var": "<argName>", "type": "<type>", "source": "=vars.<formal slot id>", "value": "<argName>" }
    ]
  }
}
```

With no In arguments bound to this trigger, omit `outputs` entirely — do not emit an empty array.

## `entry-points.json` append (required in both cases)

Locate `entry-points.json` adjacent to `caseplan.json` (same directory). Append one entry:

```json
{
  "filePath": "/content/<caseplan-basename>.bpmn#<triggerId>",
  "uniqueId": "<UUID v4>",
  "type": "CaseManagement",
  "input":  { "type": "object", "properties": {} },
  "output": { "type": "object", "properties": {} },
  "displayName": "<same as node.data.display.label>"
}
```

- `<caseplan-basename>` — the literal filename of the case file (typically `caseplan.json`), producing a path like `/content/caseplan.json.bpmn#trigger_xxxxxx`.
- `<UUID v4>` — fresh `crypto.randomUUID()` per write. Non-deterministic; normalizer strips in golden diff.
- `displayName` matches `node.data.display.label` (including the `Trigger <N>` default if `displayName` absent).
- Leave this entry's `input`/`output` schemas (the `entry-points.json` fields above — not the trigger node's I/O) empty here — Step 6.3 back-fills them from the case's In/Out args ([entry-points-sync.md](../../../entry-points-sync.md)).

**Write order:** `caseplan.json` first, then `entry-points.json`. If the second write fails, the skill surfaces the inconsistency to the user rather than silently half-applying.

## ID generation

- First-trigger path: literal `trigger_1` (no randomness).
- Secondary path: `trigger_` prefix + 6 random chars per [`case-editing-operations.md § ID Generation`](../../../case-editing-operations.md#id-generation).

Record `T<n> → <triggerId>` in `id-map.json` for downstream cross-reference — incl. resolving an In-argument's bound trigger node when its `sourceTriggers` names this timer (or, when this timer is itself the primary trigger T02, an In-arg with blank `sourceTriggers`).

## Post-write validation

After writing, confirm:

- `schema.nodes` contains the new Trigger node with the expected `id`
- `node.data.inputs.serviceType == "timer"`
- `node.data.inputs.timerType == "timeCycle"`
- `node.data.inputs.timeCycle` is byte-identical to the input string
- Node has NO `position`, `style`, `measured`, `width`, `height`, `zIndex` (Rule 18 layout-strip)
- Case A: no `data.parentElement`. Case B: `data.parentElement == {id: "root", type: "case-management:root"}`
- **`schema.edges` is still `[]`** (Rule 20) — the trigger connects to nothing; the case starts via the first stage's `case-entered` entry condition. If an edge was authored, remove it before proceeding.
- `entry-points.json.entryPoints` has a new entry with `filePath` containing the new `triggerId` and `displayName` matching `node.data.display.label`

Run `uip maestro case validate <file> --output json` after all triggers for this plugin's batch are added.

<!-- END: impl-json.md -->
