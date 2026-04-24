# connector-trigger task — Implementation (Direct JSON Write)

Write a `wait-for-connector` task directly into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md).

For shared CLI calls, metadata construction, and anti-patterns, see [connector-trigger-common.md](../../../connector-trigger-common.md#implementation--shared-cli-calls). This doc covers only the **task-specific** parts.

## Prerequisites from Planning

The `tasks.md` entry provides: `type-id`, `connection-id`, `connector-key`, `object-name`, `event-operation`, `event-mode`, `input-values`, `filter`, `isRequired`, `runOnlyOnce`.

## Steps 1-2 — Shared CLI calls

Follow [connector-trigger-common.md § Implementation — Shared CLI Calls](../../../connector-trigger-common.md#implementation--shared-cli-calls): `get-connection` (Step 1) + `tasks describe` (Step 2).

## Step 3 — Build task and write to caseplan.json

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`).

### Task skeleton

```json
{
  "id": "<taskId>",
  "type": "wait-for-connector",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.WaitForEvent"
  }
}
```

### `data` population

- **Root bindings** — per [common §Root-level bindings](../../../connector-trigger-common.md#root-level-bindings)
- **`data.context[]`** — per [common §Context array](../../../connector-trigger-common.md#context-array)
- **`data.context[].metadata`** — per [common §Metadata body](../../../connector-trigger-common.md#metadata-body) + [common §essentialConfiguration](../../../connector-trigger-common.md#essentialconfiguration)
- **`data.inputs[]`** — per [common §Input body](../../../connector-trigger-common.md#input-body-from-tasksmd-values). **Include `elementId`** on each input.
- **`data.outputs[]`** — copy verbatim from `tasks describe` (Step 2). Set `elementId` to the task's elementId. Copy `_jsonSchema` from Error output if present.
- **`data.bindings[]`** — empty array `[]`
- **`entryConditions`** — do NOT auto-inject. Step 10 handles them.

Append the task to the target stage's `tasks[]` array in its own task set (one task per lane).

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.WaitForEvent" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| get-connection | Context from tasks.md values only. No bindings | `[SKIPPED] get-connection failed — bindings omitted` |
| tasks describe | Context + bindings. No outputs/enrichment | `[SKIPPED] tasks describe failed — outputs omitted` |
| All succeed | Full population | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"wait-for-connector"`, `data.serviceType` is `"Intsvc.WaitForEvent"`
2. Context, metadata, essentialConfiguration per [common §What NOT to Do](../../../connector-trigger-common.md#what-not-to-do-shared)
3. `data.bindings[]` is empty `[]`
4. `data.outputs[]` copied verbatim with `elementId` set
5. If `input-values` present: `body.filters.expression` + `body.queryParams` (no `body.parameters`)
