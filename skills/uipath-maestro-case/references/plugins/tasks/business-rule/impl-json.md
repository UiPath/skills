# business-rule task — Implementation (Direct JSON Write)

> **Shared shape.** The rules every resource task follows — id/elementId format, `=bindings.` references, the Phase 2/3 split, binding dedup, output binding, and the placeholder fallback — are in [resource-task-common.md](../resource-task-common.md). This file states only what is specific to this type.


## Task JSON Shape

```json
{
  "id": "tR7mBx2Wd",
  "type": "business-rule",
  "displayName": "Score Credit Risk",
  "elementId": "Stage_aB3kL9-tR7mBx2Wd",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "description": "Evaluates the credit-risk decision table and returns the applicant's risk band.",
  "data": {
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- Same `data` shape as an [rpa](../rpa/impl-json.md) task; only `type` and the binding `resource` differ.
- **Do not flip to `type: "function"` or `"process"`** based on how the rule is described. The `business-rule` type comes from the sdd.md `Type:` and the `businessRule-index.json` match.
- **Never set `data.version: "v3"`.** The CLI authors `v2` tasks, which read the rule's outputs flat.


## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type business-rule --id "<entityKey>" --output json
```

`Data.Outputs` is the rule's decision output columns, flattened, then `Error` — write them as-is; never wrap them in a decision-name object. If the command fails with `has no argument contract on its resource`, the rule was deployed without `entry-points.json`: stop and tell the user to redeploy it from its solution (`uip solution publish` then `uip solution deploy run`) — do not hand-write the I/O.

**Step 1 — Root-level bindings:**


- `resource`: `"BusinessRule"` (capital B, capital R — not `"process"`)
- `resourceSubType`: omit
- `name` / `folderPath` defaults: from `registry-resolved.json` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)) — never the raw sdd.md "Folder", which may be a parent path and faults the task at runtime.

`uip maestro case bindings sync` turns the pair into one `bindings_v2.json` resource `{ "resource": "BusinessRule", "key": "<folder-path>.<name>" }`.


**Step 2 — Write task:**

2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

4. Append to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "business-rule"`
- the bindings array has 2 entries: `resource: "BusinessRule"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.outputs[].name` are flat column names (plus `Error`), none named after a decision
- `id` captured in `id-map.json`

<!-- END: impl-json.md -->
