# event trigger — Implementation (Direct JSON Write)

Configure the case-level event trigger by writing directly into the trigger node in `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md).

For shared CLI calls, metadata construction, and anti-patterns, see [connector-trigger-common.md](../../../connector-trigger-common.md#implementation--shared-cli-calls). This doc covers only the **trigger-node-specific** parts.

## Prerequisites from Planning

The `tasks.md` entry provides: `type-id`, `connection-id`, `connector-key`, `object-name`, `event-operation`, `event-mode`, `input-values`, `filter`.

## Steps 1-2 — Shared CLI calls

Follow [connector-trigger-common.md § Implementation — Shared CLI Calls](../../../connector-trigger-common.md#implementation--shared-cli-calls): `get-connection` (Step 1) + `tasks describe` (Step 2).

## Step 3 — Build trigger node and write to caseplan.json

### 3a. Identify or create the trigger node

For a **single-trigger case**, configure the existing `trigger_1` node. For **multi-trigger cases**, create a new node:
- ID: `trigger_` + 6 alphanumeric chars
- Position: `{ x: -100, y: 620 }` (auto-stack below existing triggers)

Set the trigger's display name from `tasks.md`.

### 3b. `data` structure

```json
{
  "label": "<display-name>",
  "uipath": {
    "serviceType": "Intsvc.EventTrigger",
    "context": [],
    "inputs": [],
    "outputs": [],
    "bindings": []
  }
}
```

### 3c. Populate `data.uipath`

- **Root bindings** — per [common §Root-level bindings](../../../connector-trigger-common.md#root-level-bindings). Deduplicate against existing root bindings.
- **`context[]`** — per [common §Context array](../../../connector-trigger-common.md#context-array)
- **`context[].metadata`** — per [common §Metadata body](../../../connector-trigger-common.md#metadata-body) + [common §essentialConfiguration](../../../connector-trigger-common.md#essentialconfiguration)
- **`inputs[]`** — per [common §Input body](../../../connector-trigger-common.md#input-body-from-tasksmd-values). **No `elementId`** on trigger inputs (unlike task inputs).
- **`outputs[]`** — **simplified** from `tasks describe`. Strip `body`, `id`, `target`, `elementId`. Set `_jsonSchema: null`:

```json
[
  { "name": "response", "displayName": "Email Received", "type": "jsonSchema",
    "source": "=response", "_jsonSchema": null, "var": "response", "value": "response" },
  { "name": "Error", "displayName": "Error", "type": "jsonSchema",
    "source": "=Error", "_jsonSchema": null, "var": "error", "value": "error" }
]
```

> For `Error` output, `var` and `value` are always `"error"`.

- **`bindings[]`** — empty array `[]`

### 3d. Register trigger outputs as root inputOutputs

Add each trigger output to `root.data.uipath.variables.inputOutputs[]`:

```json
{
  "id": "<output.var>",
  "name": "<output.name>",
  "type": "<output.type>",
  "elementId": "<triggerId>",
  "body": "<output.body from tasks describe — full schema>"
}
```

Use **original** outputs from `tasks describe` (before simplification) for `body`. The `elementId` is the trigger node's ID.

## Graceful degradation

**If both CLI calls fail**, leave the trigger node unchanged — the default `trigger_1` with no connector configuration remains.

| Step failed | What happens | Log |
|---|---|---|
| get-connection | Trigger left as default | `[SKIPPED] get-connection failed — event trigger not configured` |
| tasks describe | Context populated, but no outputs | `[SKIPPED] tasks describe failed — trigger outputs omitted` |
| All succeed | Full configuration per §3a-3d | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `data.uipath.serviceType` is `"Intsvc.EventTrigger"` (not `WaitForEvent`)
2. Context, metadata, essentialConfiguration per [common §What NOT to Do](../../../connector-trigger-common.md#what-not-to-do-shared)
3. `data.uipath.outputs[]` simplified (no body/id/target/elementId, `_jsonSchema: null`)
4. `data.uipath.inputs[]` has no `elementId`
5. `root.data.uipath.variables.inputOutputs[]` has entries for each trigger output
6. Trigger node wired as `--source` in an edge to the first stage
