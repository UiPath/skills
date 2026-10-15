# function task — Implementation (Direct JSON Write)

> **Shared shape.** The rules every resource task follows — id/elementId format, `=bindings.` references, the Phase 2/3 split, binding dedup, output binding, and the placeholder fallback — are in [resource-task-common.md](../resource-task-common.md). This file states only what is specific to this type.


## Task JSON Shape

```json
{
  "id": "tF4nRw8Kq",
  "type": "function",
  "displayName": "Normalize Vendor Record",
  "elementId": "Stage_aB3kL9-tF4nRw8Kq",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "description": "Normalizes the vendor record fields and returns the canonical vendor payload.",
  "data": {
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- **Do not flip to `type: "api-workflow"` or `"agent"`** based on how the function is described. The `function` type comes from the sdd.md `Type:` and the `function-index.json` match.


## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type function --id "<entityKey>" --output json
```

An empty `Data.Inputs` array is valid (the function takes no arguments) — write `data.inputs: []`.

**Step 1 — Root-level bindings:**


- `resource`: `"process"`
- `resourceSubType`: `"Function"`
- `name` / `folderPath` defaults: from `registry-resolved.json` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)) — never the raw sdd.md "Folder", which may be a parent path and faults the job at runtime.


**Step 2 — Write task:**

2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

4. Append to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "function"`
- the bindings array has 2 entries: `resource: "process"`, `resourceSubType: "Function"`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs: []` is correct for a no-argument function
- `id` captured in `id-map.json`

<!-- END: impl-json.md -->
