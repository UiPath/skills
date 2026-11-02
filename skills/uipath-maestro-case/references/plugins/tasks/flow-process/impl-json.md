# flow-process task — Implementation (Direct JSON Write)

> **Shared shape.** The rules every resource task follows — id/elementId format, `=bindings.` references, the Phase 2/3 split, binding dedup, output binding, and the placeholder fallback — are in [resource-task-common.md](../resource-task-common.md). This file states only what is specific to this type.

> **Convert writes this task.** `uip maestro case sdd convert` emits a resolved `flow-process` task with its `name` / `folderPath` bindings. Write it by hand only for a brownfield add, using the shape below.

## Task JSON Shape

The shape the Case Designer saves:

```json
{
  "id": "tF4nRw8Kq",
  "type": "flow-process",
  "displayName": "Look Up Users",
  "elementId": "Stage_aB3kL9-tF4nRw8Kq",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- **Do not flip to `type: "process"`** because a flow is a process in Orchestrator. The `flow-process` type comes from the sdd.md `Type:` and the `flow-index.json` match.
- No `serviceType`, `context` or `typeId` on the task: the Designer writes none.

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type flow-process --id "<entityKey>" --output json
```

An empty `Data.Inputs` array is valid (the flow takes no arguments) — write `data.inputs: []`.

**Step 1 — Root-level bindings:**

- `resource`: `"process"`
- **No `resourceSubType`.** The Designer binds a flow as a bare `process`; the flow's `Flow` type lives on the solution resource, not on the binding.
- `name` / `folderPath` defaults: from `registry-resolved.json` `name` / `folder-path`. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` ([planning.md § Registry Resolution](planning.md#registry-resolution)), never the raw sdd.md folder.

**Step 2 — Write task:**

1. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`.
2. Write `data.inputs[]` / `data.outputs[]` from the Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.
3. Append to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "flow-process"`
- the bindings array has 2 entries: `resource: "process"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs: []` is correct for a no-argument flow
- `id` captured in `id-map.json`

<!-- END: impl-json.md -->
