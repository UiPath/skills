# stages — JSON Implementation

> **Node `type` value: `case-management:Stage`** — use this exact string for primary and secondary stages; never use `uipath.case.stage`, `uipath.stage`, or another variant.

Cross-cutting direct-JSON rules: [`case-editing-operations.md`](../../case-editing-operations.md).

## Input spec (from `sdd.md`)

- `displayName` (element title): required stage label.
- `description`: required; always emit the SDD row's description field.
- `isRequired`: required; use the `sdd.md` value, or `false` if unspecified. Consumed by `required-stages-completed`.
- Stage kind: required; `primary` or `secondary`, from the SDD Section 2 heading (`### Stage <N>: …` vs `### Secondary Stage: …`) and `Stage Kind`. Emit as `data.stageType`: omit for primary; use `"secondary"` for secondary.

## ID generation

Use prefix `Stage_`, suffix length 6, and the algorithm in [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation). Record `T<n> → Stage_xxxxxx` in `id-map.json` for downstream cross-reference.

## Layout fields

Do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, or `zIndex` (Rule 19 layout-strip); among layout-related values, keep only `data.parentElement`, `data.isInvalidDropTarget`, and `data.isPendingParent`.

## Recipe — Primary Stage

Append or prepend the object below to top-level `nodes` (append preferred for simpler diffing; both valid). Use the stage's `**Description:**` line from `sdd.md` word for word; do not shorten or reword it. Put `**Design Rationale:**` in `tasks/build-issues.md`; use it here only when the block has no `**Description:**`.

```json
{
  "id": "<Stage_xxxxxx>",
  "type": "case-management:Stage",
  "data": {
    "label": "<displayName>",
    "description": "<the stage's **Description:** line from sdd.md, word for word>",
    "isRequired": <true|false from sdd.md; false if unspecified>,
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": []
  }
}
```

`parentElement.id` stays `"root"` although no `"root"` node is on disk; `transformCaseInMemoryJsonToDiskJson` keeps it intact. Do not initialize `entryConditions` or `exitConditions` on a primary Stage; the stage-entry-conditions / stage-exit-conditions plugins add them later.

> **Do NOT author edges (Rule 21)** — adding a stage node NEVER adds an edge. Model an SDD "A → B" arrow as B's `entryConditions` (plus A's `exitConditions` when A diverges), never as an edge. See [stages/planning.md § Wiring constraints](planning.md).

## Recipe — Secondary Stage

A non-interrupting SLA lane remains a secondary stage: when its only entry is an `sla-status-change` response described as parallel oversight (`is-interrupting: false`), use `stageType: "secondary"` and `isRequired: false`. Do NOT emit a regular stage: it joins the main flow and, when required, gates case completion. `validate` accepts either shape, so this distinction is your responsibility.

Use the primary recipe with `data.stageType: "secondary"`, and additionally initialize:

```json
"stageType": "secondary",
"entryConditions": [],
"exitConditions": []
```

The secondary node therefore retains all primary fields and has these additional `data` fields.

## Semantic position

Add the node to the top-level `nodes` array; append or prepend is valid for the frontend, with append preferred for simpler diffing.

## Post-write validation

After writing, confirm that:

- `nodes` contains the new node with its generated ID and `nodes[].type` is always `case-management:Stage`.
- `nodes[].data.label` matches the element's displayName and `nodes[].data.isRequired` is present and boolean.
- Node-level `position`, `style`, `measured`, `width`, `height`, and `zIndex` are absent (Rule 19).
- A secondary stage has `data.stageType == "secondary"`, `data.entryConditions: []`, and `data.exitConditions: []` at creation.
- A primary Stage has no `data.entryConditions` or `data.exitConditions` at creation; the condition plugins create and populate them later if `sdd.md` calls for them.
- **`schema.edges` is still `[]`** (Rule 21). If non-empty, remove the mistakenly authored edge per [case-editing-operations.md § Delete an edge](../../case-editing-operations.md#delete-an-edge--defensive-only) before proceeding.

Run `uip maestro case validate <file> --output json` after all stages for this plugin's batch are added. A default-profile `Valid` is only a batch check; the build ends with `validate --strict --sdd sdd.md` at [Step 12](../../implementation.md#step-12--end-of-phase-3-validator-pass).

<!-- END: impl-json.md -->