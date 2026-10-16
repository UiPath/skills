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


> **Built-inline sibling.** A rule built inline at the Rule 18 gate ([planning.md § Creating a business rule inline](planning.md#creating-a-business-rule-inline)) is already a **fully resolved task** by Phase 2 — bound during planning. Its I/O was read during planning from the rules project's raw `entry-points.json` (`entryPoints[0].input.properties` / `.output.properties` — case-preserving), located/confirmed via `uip maestro case registry search "<Name>" --type businessRule --local --output json` (`search`, not `get` — `get --local` matches only the opaque `entityKey`, never the name). Do **not** read field names from the `--output json` `Resource.{Inputs,Outputs}` — its keys are PascalCased. NOT tenant `tasks describe` (the sibling isn't in the tenant). Skip Step 0 for it; the binding shape below is identical, only the `folderPath` default differs: it is **empty `""`**, NOT the `solution_folder` sentinel (`resourceKey` keeps the sentinel; `folderPath` does not).


**Step 1 — Root-level bindings:**


- `resource`: `"BusinessRule"`
- `resourceSubType`: omit
- `name` / `folderPath` defaults: from `registry-resolved.json` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)). **Built-inline sibling:** `folderPath` default is **empty `""`** (co-located — the case runs the rule in its own deployed folder) while `resourceKey="solution_folder.<name>"` keeps the sentinel. Do NOT set `folderPath` to `solution_folder` — it passes `validate` but fails invocation with `Folder does not exist`. See [planning.md § Creating a business rule inline](planning.md#creating-a-business-rule-inline).


**Step 2 — Write task:**

2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`, `data.version` = `"v3"`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`. The rule's whole result is one output, `output` with `source: "=result"`, plus `Error`; read a decision's column downstream as `vars.<output var>.<decision>.<column>`.

   To store one decision column in a case variable, write an extract row `<decision>.<column> -> <case variable>` per the [nested extract example](../../variables/io-binding/impl-json.md). Its `source` is `=<decision>.<column>`: every output row reads a field of the rule's result, the way Studio Web and `sdd convert` write it, and only the bare `output` row reads the whole result as `=result`. Never write `=result.<decision>.<column>` (case `validate` rejects it: `VARIABLE_DOES_NOT_EXIST`) or `=output.<decision>.<column>` (validate passes it, but it reads an `output` field the rule's result does not have). The leaf name and type come from the `output` row's `_jsonSchema`. Keep the `output` and `Error` rows next to the extract: Studio Web writes both on every business rule task, so rule 5's parent suppression does not apply here. Write the extract row's `type` by hand from the leaf: `splice --described` types only the rows describe returns (`output`, `Error`), and the parser drops a row without `type`:

   ```json
   { "name": "riskBand", "type": "string", "id": "riskBand", "var": "riskBand", "originalVar": "riskBand",
     "value": "riskBand", "source": "=RiskDecision.riskBand", "target": "=riskBand",
     "elementId": "Stage_aB3kL9-tR7kWm2Pd" }
   ```

4. Append to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "business-rule"`, `data.version: "v3"`
- `data.outputs` is `output` (`source: "=result"`) plus `Error`, plus any `=<decision>.<column>` extract rows
- the bindings array has 2 entries: `resource: "BusinessRule"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `id` captured in `id-map.json`

<!-- END: impl-json.md -->
