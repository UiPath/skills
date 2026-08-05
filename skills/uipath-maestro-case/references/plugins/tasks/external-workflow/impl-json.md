# external-workflow task — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes shape with empty input values. Phase 3 binds values per [io-binding/impl-json.md](../../variables/io-binding/impl-json.md). See [phased-execution.md](../../../phased-execution.md).

> **Placeholder is the normal outcome.** External automations are not reachable from the CLI ([planning.md § Registry Resolution](planning.md#registry-resolution--there-is-none)). Emit the resolved shape only when `tasks.md` carries `name`, `folder-path`, `operation`, and `connection-id` — all four concrete.

## Placeholder shape (default)

Per [placeholder-tasks.md](../../../placeholder-tasks.md) — structural fields only, `data: {}`, no `data.*` keys of any kind:

```json
{
  "id": "tK3mNp9Qx",
  "elementId": "Stage_aB3kL9-tK3mNp9Qx",
  "displayName": "Sync order to fulfilment system",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "type": "external-workflow",
  "data": {},
  "entryConditions": [ ... ]
}
```

`entryConditions` is still written (Rule 8 — conditions are structural and reference the TaskId). Skip the io-binding plugin: there is no `data.inputs[]` to write into.

## Resolved shape

```json
{
  "id": "tK3mNp9Qx",
  "elementId": "Stage_aB3kL9-tK3mNp9Qx",
  "displayName": "Sync order to fulfilment system",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "type": "external-workflow",
  "data": {
    "serviceType": "Intsvc.AsyncWorkflowExecution",
    "name": "=bindings.bG0SraLpg",
    "folderPath": "=bindings.bH1iJK2lm",
    "context": [
      { "name": "operation", "value": "RunWorkflow", "type": "string" },
      { "name": "eventMode", "value": "async", "type": "string" },
      { "name": "executionType", "value": "async", "type": "string" }
    ],
    "inputs": [],
    "outputs": [],
    "bindings": []
  },
  "entryConditions": [ ... ]
}
```

- `id`: `t` + 8 alphanumeric chars. `elementId`: `${stageId}-${taskId}`.
- `isRequired` / `shouldRunOnlyOnce` from the SDD task envelope; default `shouldRunOnlyOnce` to `false`.
- `data.name` / `data.folderPath` MUST be `=bindings.<id>` references — never literals.

## `serviceType` — always write it

| `tasks.md` `execution-mode:` | `data.serviceType` | `context.eventMode` | `context.executionType` |
|---|---|---|---|
| `async` (default) | `Intsvc.AsyncWorkflowExecution` | `async` | `async` |
| `sync` | `Intsvc.SyncWorkflowExecution` | `sync` | `sync` |

> **Never omit `data.serviceType`.** The packager's fallback is `Intsvc.SyncWorkflowExecution` while the designer's default is `Intsvc.AsyncWorkflowExecution`, so an omitted key silently inverts the execution mode. `uip maestro case validate` accepts either and flags neither — this is a write-time-only guarantee.

> **All three fields move together.** `serviceType`, `eventMode`, and `executionType` must agree. Nothing validates the pairing; a mismatched trio passes `validate` and misbehaves at runtime.

## Root-level bindings

Read [bindings/impl-json.md § Full binding shape — non-connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape (all required — omitting any causes Studio Web render failure). Per-task overrides:

- `resource`: `"process"`
- `resourceSubType`: omit
- `name` / `folderPath` defaults: from `tasks.md` `name` / `folder-path`
- `resourceKey`: `"<folderPath>.<name>"`

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md). Placeholders create **no** bindings.

> **Connection is not a root binding here.** Unlike `execute-connector-activity` / `wait-for-connector`, the external-automation shape carries its connection through `data.context[]`, not through a `Connection` binding pair. Do not emit ConnectionId / FolderKey bindings for this task type.

## Procedure

**Step 0 — Schema:** none available. There is no `tasks describe --type external-workflow` and no `case spec` path (the activity is not in the pulled TypeCache). Take `data.inputs[]` / `data.outputs[]` names from the `tasks.md` wiring notes only; never fabricate a contract.

**Step 1 — Root bindings** (resolved only): create the `name` + `folderPath` pair per above.

**Step 2 — Write task:**
1. Generate `id` (`t` + 8) and `elementId` (`<stageId>-<taskId>`).
2. Write `data.serviceType` from `execution-mode:` — explicitly, always.
3. Write the `data.context[]` triplet (`operation`, `eventMode`, `executionType`).
4. Set `data.name` / `data.folderPath` to `=bindings.<id>`.
5. Write `data.inputs[]` from the SDD Inputs rows, each `value: ""`; bind in Phase 3 per [io-binding](../../variables/io-binding/impl-json.md). Write `data.outputs[]` only for outputs the SDD declares.
6. Append to the stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone (same rule as every other task plugin).

**Step 3 — Entry conditions:** added in Step 10 by [task-entry-conditions](../../conditions/task-entry-conditions/impl-json.md).

## Post-Write Verification

- `type: "external-workflow"` (schema-kebab, not the folder name)
- Placeholder: `data` is exactly `{}` — no `serviceType`, no `context`, no `name`/`folderPath`
- Resolved: `data.serviceType` present and matching `execution-mode:`; `context[]` carries all three fields and agrees with `serviceType`
- Resolved: `data.name` and `data.folderPath` start with `=bindings.`, and the pair's `resourceKey` is `<folderPath>.<name>` (Step 12 Check 11)
- No ConnectionId / FolderKey bindings created for this task
- `entryConditions` present and non-empty — `validate` accepts an empty array and a missing key, so check it explicitly
- `id` captured in `id-map.json`

## Anti-patterns

- **Do NOT report "0 resources on this tenant"** after failing to find an external automation. Nothing was searched — there is no cache file. Say the index is not pulled.
- **Do NOT omit `data.serviceType`** to "let the default apply." The default is the wrong one.
- **Do NOT emit Connection/FolderKey root bindings.** Connection travels in `data.context[]` for this type.
- **Do NOT run the Rule 17 create-offer gate.** External automations are not creatable inline, and this is not a genuine 0-match.
- **Do NOT substitute `api-workflow`.** That is a UiPath API workflow with a real registry entry and a different `serviceType`; swapping types to get a resolvable resource changes what the case does.
