# rpa task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "tQ2pVx7Lm",
  "type": "rpa",
  "displayName": "Extract Invoice Data",
  "elementId": "Stage_aB3kL9-tQ2pVx7Lm",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.
- **Do not flip to `type: "process"`** based on registry. The `rpa` vs `process` distinction comes from sdd.md intent.

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type rpa --id "<entityKey>" --output json
```

Fallback: planning-captured schema from tasks.md. If unavailable, placeholder per [placeholder-tasks.md](../../../placeholder-tasks.md).

> **Built-inline sibling.** An RPA process built inline at the Rule 17 gate ([planning.md § Creating an RPA process inline](planning.md#creating-an-rpa-process-inline)) is already a **fully resolved task** by Phase 2 — bound during planning. Its I/O was read during planning from the sibling's on-disk **`project.json` `entryPoints[].input/output`** (case-preserving names, .NET FQN types — RPA siblings have no `entry-points.json`), located/confirmed via `uip maestro case registry search "<Name>" --type process --local --output json` (`search`, not `get`; registry token is `process`, not `rpa`). Do **not** read field names from the `--output json` `Resource.{Inputs,Outputs}` — keys come back PascalCased. NOT tenant `tasks describe` (the sibling isn't in the tenant). Skip Step 0 for it; the binding shape below is identical, only the `folderPath` default differs: **empty `""`** (co-located), NOT the `solution_folder` sentinel (`resourceKey` keeps the sentinel; `folderPath` does not). Write `data.inputs[]`/`data.outputs[]` `type` in **case vocabulary** — never the raw .NET FQN. For **pinned** fields, use the pinned vocab from the Step-1 contract as-is (a `file` pin stays `file` regardless of the builder's .NET pick); reverse-map via the [planning.md § Step 1](planning.md#creating-an-rpa-process-inline) table only for **unpinned/extra** fields, resolving its ambiguous rows as `System.DateTime` → `datetime` unless pinned `date`.

**Step 1 — Root-level bindings:**

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"process"`
- `resourceSubType`: omit (no resourceSubType for rpa tasks)
- `name` / `folderPath` defaults: from `tasks.md` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)) — never the raw sdd.md "Folder", which may be a parent path and faults the job at runtime. **Built-inline sibling:** `folderPath` default is **empty `""`** (co-located) while `resourceKey="solution_folder.<name>"` keeps the sentinel. Do NOT set `folderPath` to `solution_folder` — it passes `validate` but fails invocation with `folder not exist`. See [planning.md § Step 3 Binding](planning.md#creating-an-rpa-process-inline).

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md).

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

   **Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is the `tasks describe` output (Step 0 above); for a built-inline sibling it is the planning-recorded contract from `project.json` `entryPoints` (Step 0 skipped).
4. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "rpa"` (NOT `"process"`)
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "process"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless placeholder)
- `id` captured in `id-map.json`
