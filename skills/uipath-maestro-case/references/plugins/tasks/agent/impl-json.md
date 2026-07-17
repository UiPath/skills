# agent task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "tH3kLmNp9",
  "type": "agent",
  "displayName": "Classify Purchase Order",
  "elementId": "Stage_aB3kL9-tH3kLmNp9",
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

## Procedure

**Step 0 — Load the cached inputs/outputs schema:**

Read the T-entry's `schema-cache-key` from `tasks.md`, then consume that entry in `tasks/schema-cache.json`. Verify its request tuple is `(agent, <entityKey>, <elementId-or-null>)`. Do not call `tasks describe` during implementation. Multi-element agents use a distinct cache entry per element ID. If the entry is absent or mismatched, return to the [schema gather pass](../../../schema-cache-guide.md), fetch it once, persist it, then resume. If the resource is unresolved, use the placeholder per [placeholder-tasks.md](../../../placeholder-tasks.md).

> **Built-inline sibling.** An agent built inline at the Rule 17 gate ([planning.md § Creating an Agent inline](planning.md#creating-an-agent-inline)) is already a **fully resolved task** by Phase 2 — bound during planning. Its I/O was read during planning from the sibling's raw `entry-points.json` (`entryPoints[0].input.properties` / `.output.properties` — case-preserving), located/confirmed via `uip maestro case registry search "<Name>" --type agent --local --output json` (`search`, not `get` — `get --local` matches only the opaque `entityKey`, never the name), and persisted as the T-entry's `Nxx` cache response. Do **not** read field names from the `--output json` `Resource.{Inputs,Outputs}` — its keys are PascalCased. NOT tenant `tasks describe` (the sibling isn't in the tenant). The binding shape below is identical; `folderPath` default is **empty `""`** (co-located), NOT the `solution_folder` sentinel.

**Step 1 — Accumulate root-level bindings:**

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"process"`
- `resourceSubType`: `"Agent"`
- `name` / `folderPath` defaults: from `tasks.md` `name` / `folder-path` fields. `folder-path` is the resolved registry `folders[0].fullyQualifiedName` (per [planning.md § Registry Resolution](planning.md#registry-resolution)) — never the raw sdd.md "Folder", which may be a parent path and faults the job at runtime. **Built-inline sibling:** `folderPath` default is **empty `""`** (co-located — the case starts the agent in its own deployed folder) while `resourceKey="solution_folder.<name>"` keeps the sentinel. Do NOT set `folderPath` to `solution_folder` — it passes `validate` but fails invocation with `folder not exist`. See [planning.md § Step 3 Binding](planning.md#creating-an-agent-inline).

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md).

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

   **Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema is the cached `tasks describe` response (Step 0 above).
4. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "agent"`
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "process"`, `resourceSubType: "Agent"`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless placeholder)
- `id` captured in `id-map.json`
