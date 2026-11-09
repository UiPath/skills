# process task — Implementation (Direct JSON Write)

> **Shared shape.** Shared rules—id/elementId format, `=bindings.` references, Phase 2/3 split, binding dedup, output binding, and placeholder fallback—are in [resource-task-common.md](../resource-task-common.md). This file covers only this type.

## Task JSON Shape

```json
{"id":"t8GQTYo8O","type":"process","displayName":"Run KYC","elementId":"Stage_aB3kL9-t8GQTYo8O","isRequired":true,"shouldRunOnlyOnce":false,"description":"Runs the KYC check against the supplier record and returns the outcome.","data":{"name":"=bindings.bG0SraLpg","folderPath":"=bindings.bH1iJK2lm","inputs":[],"outputs":[]}}
```

## Procedure

**Step 0 — Get inputs/outputs schema:** run:

```bash
uip maestro case tasks describe --type process --id "<entityKey>" --output json
```

**Step 1 — Root-level bindings:** Set `resource` to `"process"` and `resourceSubType` to `"ProcessOrchestration"`. Get `name` / `folderPath` defaults from `registry-resolved.json` `name` / `folder-path`; `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)). Never use the raw sdd.md "Folder": it may be a parent path and faults the job at runtime.

**Step 2 — Write task:**

2. Set `data.name` = `=bindings.<nameBindingId>` and `data.folderPath` = `=bindings.<folderPathBindingId>`.
3. Write `data.inputs[]` / `data.outputs[]` from the Step 0 schema. Each input is `{ name, type, id, var, elementId, value: "" }`; each output is `{ name, type, id, var, value, source, target, elementId }`.
4. Append to the target stage's `data.tasks` using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks each get a single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Add entry conditions in Step 10. Add input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- Verify `type: "process"`.
- Verify the bindings array has 2 entries: `resource: "process"`, `resourceSubType: "ProcessOrchestration"`, with `propertyAttribute` = `name` / `folderPath`.
- Capture `id` in `id-map.json`.

<!-- END: impl-json.md -->