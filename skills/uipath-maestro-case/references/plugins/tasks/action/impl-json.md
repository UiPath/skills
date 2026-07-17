# action task — Implementation (Direct JSON Write)

Two paths — **QuickForm** (default; inline form, no app) and **App-based** (deployed Action Center app). Pick per [planning.md § Path Selection](planning.md#path-selection); the `tasks.md` `hitl-kind` field (`quick` | `app`) records the choice.

> **Phase split.**
> - **App-based:** Phase 2 writes shape with empty input values; Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md).
> - **QuickForm:** fully authored in Phase 2 — the input bindings live inside the `.hitl.json` (`=vars.<v>`), and `data.inputs[]`/`data.outputs[]` stay empty, so the task has **no** Phase-3 io-binding step of its own. Downstream tasks that consume a QuickForm output bind it in *their* Phase 3 via `=vars.<variable>`.
>
> See [phased-execution.md](../../../phased-execution.md).

---

## QuickForm (default — no deployed app)

Author two artifacts: a `<TaskLabel>.hitl.json` schema file alongside `caseplan.json`, and the action task carrying `data.context[hitlType]="quick"`. No deployed app, no `tasks describe`, **no `root.data.uipath.bindings[]` entries**. Generate two fresh UUID v4 values up front: `schemaId` (schema identity) and `_schemaFileId` (placeholder file id — **must differ** from `schemaId`).

### `<TaskLabel>.hitl.json`

Sits next to `caseplan.json`. Filename = the task's label. Unified `fields[]` array — `direction` sets each field's role.

```json
{
  "schemaId": "<schemaId-uuid-v4>",
  "fields": [
    { "id": "invoiceid", "label": "Invoice ID", "type": "text",   "direction": "input",  "binding": "=vars.invoiceId" },
    { "id": "amount",    "label": "Amount",     "type": "number", "direction": "input",  "binding": "=vars.amount" },
    { "id": "decision",  "label": "Decision",   "type": "text",   "direction": "output", "variable": "decision", "required": true },
    { "id": "notes",     "label": "Notes",      "type": "text",   "direction": "inOut",  "binding": "=vars.draftNotes", "variable": "notes" }
  ],
  "outcomes": [
    { "id": "approve", "name": "Approve", "type": "string", "isPrimary": true,  "action": "Continue" },
    { "id": "reject",  "name": "Reject",  "type": "string", "isPrimary": false, "action": "End" }
  ]
}
```

| Field property | Rule |
|---|---|
| `id` | lowercase the label, spaces→`-`, strip non-alphanumeric. `"Invoice ID"`→`"invoiceid"`, `"Due Date"`→`"due-date"`. |
| `label` | Display label — never empty (validator rejects). |
| `type` | `.hitl.json` native type — see case-vocab map below. |
| `direction` | `"input"` (reviewer reads) · `"output"` (reviewer enters) · `"inOut"` (reviewer edits a prefilled value). |
| `binding` | Required for `input`/`inOut`: `"=vars.<v>"` — the case variable feeding the field. |
| `variable` | Required for `output`/`inOut`: the var the entered value writes to; downstream reads `=vars.<variable>`. |
| `required` | `true` for mandatory outputs; omit otherwise. |

`outcomes[]`: `{ id, name, type:"string", isPrimary:<bool>, action:"Continue"|"End" }` — first entry is the primary action; use domain names (Approve/Reject), never a bare Submit.

**case-vocab → `.hitl.json` native type** (the [SDD Case Variables](../../../sdd-generation-rules.md) type feeding each field):

| case vocab | `.hitl.json` `type` |
|---|---|
| `string` | `text` |
| `integer` / `float` / `double` | `number` |
| `boolean` | `boolean` |
| `date` | `date` |
| `datetime` | `dateTime` |
| `jsonSchema` / `file` | no native QuickForm type — use `text`, or prefer **App-based** when the reviewer needs rich/file I/O |

### Task JSON

```json
{
  "id": "ta1b2c3d4",
  "type": "action",
  "displayName": "InvoiceReview",
  "elementId": "Stage_aB3kL9-ta1b2c3d4",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "taskTitle": "Please review this invoice and approve or reject",
    "context": [
      { "name": "hitlType",                     "type": "string",  "value": "quick" },
      { "name": "_schemaFileId",                "type": "string",  "value": "<_schemaFileId-uuid-v4>" },
      { "name": "hitlSchemaId",                 "type": "string",  "value": "<schemaId-uuid-v4>" },
      { "name": "taskTitle",                    "type": "string",  "value": "Please review this invoice and approve or reject" },
      { "name": "labels",                       "type": "string" },
      { "name": "priority",                     "type": "string",  "value": "Medium" },
      { "name": "actionCatalogName",            "type": "string" },
      { "name": "enableActionableNotifications","type": "boolean", "value": "false" },
      { "name": "assignmentCriteria",           "type": "string",  "value": "user" },
      { "name": "recipient",                    "type": "json",    "body": { "Type": 2, "Value": "approver@company.com" } }
    ],
    "inputs": [],
    "outputs": []
  }
}
```

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `data.taskTitle` appears **both** top-level and in `context[]` — both required.
- `hitlType` = `"quick"`. `hitlSchemaId` = the `.hitl.json` `schemaId` **exactly**. `_schemaFileId` = the other UUID (placeholder; Studio Web replaces it when it processes the project).
- `labels` / `actionCatalogName`: leave the entry present but with no `value` for QuickForm.
- `data.inputs[]` / `data.outputs[]`: **empty arrays** — the schema lives in the `.hitl.json`.
- No `data.name` / `data.folderPath` (those are App-based). No `root.data.uipath.bindings[]`.
- **Entry conditions** are added by the shared Step 10 (`current-stage-entered`), same as any task — a task with none fails `validate` (`Task has no entry rules`). No QuickForm-specific handling.
- `recipient` / `priority`: `context[recipient].body` is the `{ Type, Value }` object and `context[priority].value` the level — same values and Type rules as App-based (§ Action-Specific Fields).

---

## App-based (deployed Action Center app)

Binds to a resolved deployed app. `data.name` / `data.folderPath` are `=bindings.<id>` references; 2 root bindings are added.

### Task JSON Shape

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

### Action-Specific Fields

| Field | Notes |
|---|---|
| `data.taskTitle` | Required on resolved action tasks — validator rejects empty. |
| `data.priority` | `"Low"` \| `"Medium"` (default) \| `"High"` \| `"Critical"` |
| `data.recipient` | `ActionTaskAssignee` object: `{ "Type": <int>, "Value": "<id-or-email>" }`. See fallback below. |
| `data.actionCatalogName` | **Optional.** Must bind to an existing action catalog resource. Omit unless tasks.md references a known catalog. |
| `data.labels` | Label set from tasks.md |

`recipient.Type` values: `0` = user ID (sdd `User:`), `1` = group ID (sdd `UserGroup:` / `Role:`), `2` = email address, `3` = `"=vars.<varId>"` (sdd `Expression:`). **Fallback when sdd.md value is not a resolved UUID:** write `{ "Type": <picked>, "Value": "<sdd-string-as-is>" }` — schema-conformant placeholder, user resolves Value later. Drop `data.recipient` only when no Type maps. **Never invent a non-conforming shape** (`{ kind, id }`, `{ scope, target, value }`, etc.) — Studio Web canvas crashes silently; CLI validate misses it. (These Type rules apply to QuickForm's `context[recipient].body` too.)

### Procedure

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

---

## Placeholder (unresolved)

> **Unresolved → `"data": {}`.** When neither path yields a real task (no deployed app resolves and no QuickForm is derivable, per [planning.md § Unresolved Fallback](planning.md#unresolved-fallback-placeholder)), the entire shape collapses to `"data": {}`. **No exception** for `taskTitle`, `priority`, `recipient`, `labels`, `name`, `folderPath`, `context`, `inputs`, `outputs`, or `actionCatalogName` — omit every `data.*` key, and write **no** `.hitl.json` file. See [placeholder-tasks.md](../../../placeholder-tasks.md).

## Post-Write Verification

**QuickForm:**
- `type: "action"`; `data.taskTitle` non-empty and equal to `context[taskTitle].value`
- a `<TaskLabel>.hitl.json` exists alongside `caseplan.json` with `schemaId`, `fields[]` (unified, `direction`-typed), `outcomes[]`
- `context[]` has `hitlType:"quick"`, `_schemaFileId`, `hitlSchemaId` — and `context[hitlSchemaId].value` == `.hitl.json` `schemaId`; `_schemaFileId` ≠ `hitlSchemaId`
- `data.inputs[]` and `data.outputs[]` are empty arrays; no `data.name`/`data.folderPath`; `root.data.uipath.bindings[]` NOT modified
- `uip maestro case validate` Status `Valid`; `id` captured in `id-map.json`

**App-based:**
- `type: "action"`; `data.taskTitle` non-empty
- `data.name` and `data.folderPath` start with `=bindings.`
- the bindings array has 2 entries: `resource: "app"`, no `resourceSubType`, `propertyAttribute` = `name` / `folderPath`
- `data.inputs` and `data.outputs` populated
- `data.recipient` is an **object** `{ Type, Value }`, never a bare string — present whenever tasks.md recorded a `recipient:` line (omitted only for group/role, Skip, or no-Type-maps)
- `id` captured in `id-map.json`

## Anti-patterns

- **Do NOT emit `data.recipient` as a bare string, drop it, or "resolve" it.** It is always the object `{ Type, Value }` (App-based `data.recipient`; QuickForm `context[recipient].body`). The tasks.md value (`=vars.X`, email, UUID) is the `Value` — wrap it, don't pass it through. `Type 3` `=vars.X` is the finished runtime reference; copying it through as a string, deferring to Phase 3, or rewriting it to the var's email each break the task.
- **Do NOT give a QuickForm task `data.name`/`data.folderPath` or root `bindings[]`** — those are App-based only. A QuickForm task binds nothing at the root; its inputs bind inside the `.hitl.json`.
- **Do NOT populate `data.inputs[]`/`data.outputs[]` on a QuickForm task** — the schema lives in the `.hitl.json`; these arrays stay empty.
- **CLI `validate` does NOT check `data.recipient`, the `.hitl.json` binding, or context completeness** — verify presence/shape explicitly (Post-Write Verification).
