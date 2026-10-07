# business-rule task — Implementation (Direct JSON Write)

> **Shared shape.** The rules every resource task follows — id/elementId format, `=bindings.` references, the Phase 2/3 split, binding dedup, output binding, and the placeholder fallback — are in [resource-task-common.md](../resource-task-common.md). This file states only what is specific to this type.


## Task JSON Shape

```json
{
  "id": "tR7kWm2Pd",
  "type": "business-rule",
  "displayName": "Score Credit Risk",
  "elementId": "Stage_aB3kL9-tR7kWm2Pd",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "description": "Scores the applicant against the credit risk rule and returns the risk band.",
  "data": {
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "version": "v3",
    "inputs": [],
    "outputs": []
  }
}
```


## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type business-rule --id "<entityKey>" --output json
```


**Step 1 — Root-level bindings:**


- `resource`: `"BusinessRule"`
- `resourceSubType`: omit
- `name` / `folderPath` defaults: from `registry-resolved.json` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)).


**Step 2 — Write task:**

2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`, `data.version` = `"v3"`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`. The rule's whole result is one output, `output` with `source: "=result"`, plus `Error`; read a decision's column downstream as `vars.<output var>.<decision>.<column>`.

   To store one decision column in a case variable, write an extract row `result.<decision>.<column> -> <case variable>` per the [nested extract example](../../variables/io-binding/impl-json.md). The first segment `result` matches the `output` row's source; the leaf name and type come from that row's `_jsonSchema`:

   ```json
   { "name": "riskBand", "type": "string", "id": "riskBand", "var": "riskBand", "originalVar": "riskBand",
     "value": "riskBand", "source": "=result.RiskDecision.riskBand", "target": "=riskBand",
     "elementId": "Stage_aB3kL9-tR7kWm2Pd" }
   ```

4. Append to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "business-rule"`, `data.version: "v3"`
- `data.outputs` is `output` (`source: "=result"`) plus `Error`, plus any `=result.<decision>.<column>` extract rows
- the bindings array has 2 entries: `resource: "BusinessRule"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `id` captured in `id-map.json`

<!-- END: impl-json.md -->
