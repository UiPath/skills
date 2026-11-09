# manual trigger — JSON Implementation

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../../case-editing-operations.md).

> **Layout-strip (Rule 19).** Omit `position`, `style`, `measured`, `width`, `height`, and `zIndex` from the trigger node. Keep `data.parentElement` when applicable, plus `data.isInvalidDropTarget`, `data.isPendingParent`, `data.typeVersion`, `data.display`, and `data.description`.

## Purpose

A manual trigger uses `data.inputs.serviceType: "None"`. `getTriggerType` maps `"Intsvc.TimerTrigger"` to timer and `"None"` to manual; any other spelling uses the `default` connector arm without error. Legal tokens are `"None"`, `"Intsvc.EventTrigger"`, and lowercase `"timer"`.

Count existing Trigger nodes in `schema.nodes`. Append the selected node to `caseplan.case` and its matching entry to sibling `entry-points.json.entryPoints` as an atomic pair; the orchestrator discovers runtime entry points there.

## Input spec (from `sdd.md`)

| Field | Required | Notes |
|---|---|---|
| `displayName` | yes | SDD row display name; if absent use `Trigger ${existingTriggerCount + 1}`. |
| `description` | yes | Always emit in `data.description`; use the element's `description:` or infer a natural-language description from surrounding sdd.md context. |

Compute position statefully below; do not accept it from the user.

## Pre-flight

1. Confirm **`caseplan.case` exists** at `<SolutionDir>/<ProjectName>/caseplan.case`; the `case` plugin creates it at T01. If absent, run that plugin first; do not synthesize it.
2. Confirm **`entry-points.json` exists** beside it; the `case` plugin's § Scaffold creates it at T01. If absent, hard-fail (`entry-points.json not found in <dir>. Run the case plugin first to scaffold the project.`); do not lazily create it.
3. Parse and validate both JSON files, then modify and write them.

## ID generation

Before writing, count:

```text
existingTriggers = schema.nodes.filter(n => n.type === "uipath.case.trigger")
```

Use literal `trigger_1` for zero existing triggers; otherwise use `trigger_` plus 6 random chars from `[A-Za-z0-9]`, using [`case-editing-operations.md § ID Generation`](../../../case-editing-operations.md#id-generation). Never randomize the first trigger; `trigger_1` matches the [timer](../timer/impl-json.md#id-generation) and [event](../event/impl-json.md) plugins.

If no display name is supplied, use `Trigger ${existingTriggers.length + 1}` (first trigger: `"Trigger 1"`; first secondary: `"Trigger 2"`). Generate the entry-point `uniqueId` inline:

```bash
node -e "console.log(crypto.randomUUID())"
```

Record `T<n> → trigger_xxxxxx` in `id-map.json` for downstream cross-reference, including global-vars resolution of this trigger's node id for an In-argument whose `sourceTriggers` names its T-number or leaves `sourceTriggers` blank for the primary trigger.

## Recipe — `caseplan.case` (append to `schema.nodes`)

Append, never prepend, the branch-selected node.

### Case A — zero existing triggers (first-trigger path)

```json
{
  "id": "trigger_1",
  "type": "uipath.case.trigger",
  "data": {
    "description": "<description from sdd.md or LLM-inferred>",
    "typeVersion": "1.0.0",
    "display": { "label": "<displayName or \"Trigger 1\">" },
    "inputs": { "serviceType": "None", "entryPointId": "<entry-points.json uniqueId>" }
  }
}
```

Do not emit `data.parentElement` in Case A; Studio Web hydrates layout on load.

### Case B — one or more existing triggers (secondary-trigger path)

```json
{
  "id": "<trigger_XXXXXX>",
  "type": "uipath.case.trigger",
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "description": "<description from sdd.md or LLM-inferred>",
    "typeVersion": "1.0.0",
    "display": { "label": "<displayName>" },
    "inputs": { "serviceType": "None", "entryPointId": "<entry-points.json uniqueId>" }
  }
}
```

Manual triggers always emit `data.inputs.serviceType` as `"None"` and `entryPointId` as the entry's `uniqueId`; older schemas may omit `inputs` when reading, but always emit both when writing. See [case-schema.md § Trigger Node](../../../case-schema.md#a-trigger-node--uipathcasetrigger).

## Recipe — `entry-points.json` (append to `entryPoints`)

Read, parse, and append:

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

`basename(caseplanFile)` includes the schema file extension, typically `caseplan.case`, so the fragment is like `/content/caseplan.case.bpmn#trigger_xY2mNp`. Leave `input` and `output` schemas empty; Step 6.3 back-fills them from the case's In/Out args ([entry-points-sync.md](../../../entry-points-sync.md)). Write with 4-space indent (`JSON.stringify(obj, null, 4)`).

## Write order

Write both files atomically and in this order:

1. `caseplan.case` with the node appended.
2. `entry-points.json` with the entry appended.

Verify `entry-points.json` before the first write and fail fast. If the second write fails, roll back `caseplan.case` by writing the pre-mutation content kept in memory.

## Post-write validation

Confirm that:

- `caseplan.case.nodes` ends with the new `uipath.case.trigger`, using `trigger_1` in Case A or generated `trigger_XXXXXX` in Case B.
- `nodes[].data.display.label` equals the resolved `displayName`; `nodes[].data.description` is present and non-empty (direct-JSON-write divergence); and `nodes[].data.typeVersion === "1.0.0"`.
- `nodes[].data.parentElement` is present in Case B and absent in Case A.
- The node has no `position`, `style`, `measured`, `width`, `height`, or `zIndex` (Rule 19).
- `nodes[].data.inputs.serviceType === "None"`; `inputs` may be absent only in older schemas, and `nodes[].data.inputs.entryPointId` equals this entry's `uniqueId`.
- **`schema.edges` is still `[]`** (Rule 21). The trigger connects to nothing; the case starts via the first stage's `case-entered` entry condition. Remove any authored edge before proceeding.
- `entry-points.json.entryPoints` contains the new entry whose `filePath` ends in `#<trigger_XXXXXX>` and whose `displayName === <displayName>`.

After all triggers for this plugin's batch are added, run `uip maestro case validate <caseplan.case> --output json`. A default-profile `Valid` is only a batch check; completion requires `validate --strict --sdd sdd.md` at [Step 12](../../../implementation.md#step-12--end-of-phase-3-validator-pass).

<!-- END: impl-json.md -->