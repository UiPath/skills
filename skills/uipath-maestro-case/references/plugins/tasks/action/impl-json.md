# action task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

## Task JSON Shape

```json
{
  "id": "ty5UcykfU",
  "type": "action",
  "displayName": "Review Purchase Order",
  "elementId": "Stage_aB3kL9-ty5UcykfU",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "taskTitle": "Please review this PO and approve or reject",
    "priority": "High",
    "recipient": { "Type": 2, "Value": "approver@corp.com" },
    "labels": "<labels string>",
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "inputs": [],
    "outputs": []
  }
}
```

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.

## Action-Specific Fields

> **Unresolved → `"data": {}`.** When `action-app-id` is `<UNRESOLVED>` (or `action-apps-index.json` returned 0 nodes), the entire shape collapses to `"data": {}`. **No exception** for `taskTitle`, `priority`, `recipient`, `labels`, `name`, `folderPath`, `inputs`, `outputs`, or optional `actionCatalogName` — omit every `data.*` key. See [placeholder-tasks.md](../../../placeholder-tasks.md).

| Field | Notes |
|---|---|
| `data.taskTitle` | Required on **resolved** action tasks — validator rejects empty. Placeholders omit it (along with every other `data.*` action-specific key); see [placeholder-tasks.md](../../../placeholder-tasks.md). |
| `data.priority` | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `data.recipient` | `ActionTaskAssignee` object: `{ "Type": <int>, "Value": "<id-or-email>" }`. See fallback below for unresolved-UUID handling. |
| `data.actionCatalogName` | **Optional.** Must bind to an existing action catalog resource. Omit unless tasks.md references a known catalog. |
| `data.labels` | Label set from tasks.md |

`recipient.Type` values: `0` = user ID (sdd `User:`), `1` = group ID (sdd `UserGroup:` / `Role:`), `2` = email address, `3` = `"=vars.<varId>"` (sdd `Expression:`). **Fallback when sdd.md value is not a resolved UUID:** write `{ "Type": <picked>, "Value": "<sdd-string-as-is>" }` — schema-conformant placeholder, user resolves Value later. Drop `data.recipient` only when no Type maps. **Never invent a non-conforming shape** (`{ kind, id }`, `{ scope, target, value }`, etc.) — Studio Web canvas crashes silently; CLI validate misses it.

## Procedure

**Step 0 — Get inputs/outputs schema:**

```bash
uip maestro case tasks describe --type action --id "<action-app-id>" --output json
```

Fallback: planning-captured schema from tasks.md. If unavailable, placeholder per [placeholder-tasks.md](../../../placeholder-tasks.md).

**Step 1 — Root-level bindings:**

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"app"`
- `resourceSubType`: omit (no resourceSubType for action tasks)
- `name` / `folderPath` defaults: from `tasks.md` `name` / `folder-path` fields

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md).

**Step 2 — Write task:**

1. Generate `id` (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`)
2. Set `data.taskTitle`, `data.priority`, `data.labels` from tasks.md now (plain strings, not Phase-3 bindings); set `data.actionCatalogName` only when tasks.md references an existing catalog. **`data.recipient` is an object, NEVER a bare string.** The tasks.md `recipient:` line carries a bare value (the SDD typed prefix is stripped in planning) — wrap it as `{ "Type": <int>, "Value": <value> }`, inferring Type from the value shape (`=vars.X` → `3`, email → `2`, UUID → `0`/`1`). E.g. `recipient: =vars.assignedLoanOfficer` → `{ "Type": 3, "Value": "=vars.assignedLoanOfficer" }`. Do not copy the bare value through as `data.recipient`.
3. Set `data.name` = `=bindings.<nameBindingId>`, `data.folderPath` = `=bindings.<folderPathBindingId>`
4. Write `data.inputs[]` / `data.outputs[]` from Step 0 schema. Each input: `{ name, type, id, var, elementId, value: "" }`. Each output: `{ name, type, id, var, value, source, target, elementId }`.

   **Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is the `tasks describe` output (Step 0 above).
5. Append to target stage's `tasks[laneIndex][]`

> Entry conditions added in Step 10. Only `data.inputs[].value` is deferred to Phase 3 per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md); the scalar `data.*` fields above are final at Step 2.

## Post-Write Verification

- `type: "action"`
- `data.taskTitle` non-empty
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "app"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated (unless placeholder)
- `data.recipient` is an **object** `{ Type, Value }`, never a bare string — present whenever tasks.md recorded a `recipient:` line (omitted only for group/role, Skip, or no-Type-maps)
- `id` captured in `id-map.json`

## Anti-patterns

- **Do NOT emit `data.recipient` as a bare string, drop it, or "resolve" it.** It is always the object `{ Type, Value }` written at Step 2 (not an io-binding target). The tasks.md value (`=vars.X`, email, UUID) is the `Value` — wrap it, don't pass it through. `Type 3` `=vars.X` is the finished runtime reference; copying it through as a string, deferring to Phase 3, or rewriting it to the var's email each break the task. Symptoms: `data.recipient` is a string, or missing while `tasks.md` has `recipient: =vars.X`.
- **CLI `validate` does NOT check `data.recipient`** — verify presence/shape explicitly (Post-Write Verification).
