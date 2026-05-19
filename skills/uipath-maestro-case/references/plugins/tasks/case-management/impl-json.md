# case-management task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "tZ8rMn4Vp",
  "type": "case-management",
  "displayName": "Run Vendor Onboarding Sub-Case",
  "elementId": "Stage_aB3kL9-tZ8rMn4Vp",
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

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type case-management --id "<entityKey>" --output json
```

Fallback: planning-captured schema from tasks.md. If unavailable, placeholder per [placeholder-tasks.md](../../../placeholder-tasks.md).

**Step 1 — Root-level bindings:**

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"process"`
- `resourceSubType`: `"CaseManagement"`
- `name` / `folderPath` defaults: from `tasks.md` `name` / `folder-path` fields

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md).

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. **Recursion guard** — confirm the sub-case `entityKey` from tasks.md does NOT match the current case's own entityKey (direct recursion) and does not appear as an ancestor in already-written `case-management` tasks (transitive recursion). If either check fails, flag for user review.
3. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
4. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

   **Output aliasing per `<-` notation** (parsed from tasks.md `outputs:` row; documented in [`../../variables/io-binding/planning.md`](../../variables/io-binding/planning.md#discovering-inputoutput-names)):
   - `<sdd-name> <- <response-path>` → `source: "=<response-path>"`, `var/id/target/value: "<sdd-name>"`. `name` stays as the schema's display name.
   - Bare `<name>` → camelCase the schema field → `var/id/target/value` = camelCased, `source: "=<schema-field-name>"`.
   - Dot-paths supported on the right side (`result.score`, `data.user.email`). Array indexing not supported in v1.
   - [Uniqueness rule](../../variables/global-vars/impl-json.md#uniqueness-rule) applies to `var/id/target` on collision; `source` is never suffixed.
5. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Input value bindings in Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).

## Post-Write Verification

- `type: "case-management"`
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "process"`, `resourceSubType: "CaseManagement"`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless placeholder)
- No circular self-reference
- `id` captured in `id-map.json`
