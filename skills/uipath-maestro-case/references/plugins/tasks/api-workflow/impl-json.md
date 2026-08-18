# api-workflow task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "tK7nRs3Wp",
  "type": "api-workflow",
  "displayName": "Monitor Order Inbox",
  "elementId": "Stage_aB3kL9-tK7nRs3Wp",
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

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `isRequired` and `shouldRunOnlyOnce` come directly from the normalized SDD task envelope; default `shouldRunOnlyOnce` to `false` when omitted.
- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type api-workflow --id "<entityKey>" --output json
```

Fallback: the schema persisted in resolution evidence. If unavailable, use the accepted placeholder path in [placeholder-tasks.md](../../../placeholder-tasks.md).

> **Built-inline sibling.** An API workflow created through [registry discovery](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) is fully resolved before lowering. Read its I/O from raw `entry-points.json`; fall back to the schema-document wrapper, then root workflow schemas, and record any fallback. Confirm it via `registry search --local`. Do not use tenant `tasks describe`. Its `folderPath` default is empty `""`; `resourceKey` keeps `solution_folder.<name>`.

**Step 1 — Root-level bindings:**

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"process"`
- `resourceSubType`: `"Api"`
- `name` / `folderPath` defaults: from the selected resolution-evidence entry. Tenant resources use the resolved fully qualified folder; built-inline siblings use empty `""` while `resourceKey="solution_folder.<name>"` retains the sentinel. Do not set `folderPath` to `solution_folder`.

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md).

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
3. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

   **Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is the `tasks describe` output (Step 0 above).
4. Append to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share `tasks[laneIndex][]`; if `lane` conflicts with mode, mode wins.

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "api-workflow"`
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "process"`, `resourceSubType: "Api"`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless placeholder)
- `id` captured in `id-map.json`

<!-- END: impl-json.md -->
