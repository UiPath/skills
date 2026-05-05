# event trigger — Implementation (Direct JSON Write)

Configure the case-level event trigger by writing directly into the trigger node in `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md).

For shared CLI calls, metadata construction, and anti-patterns, see [connector-trigger-common.md](../../../connector-trigger-common.md#implementation--shared-cli-calls). This doc covers only the **trigger-node-specific** parts.

> **v20 layout-strip (Rule 19).** Read `Schema:` header from `tasks.md`. In **v20 mode**, omit ALL of: `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Skip the position-computation step entirely. Keep `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`, `data.label`, `data.description`, `data.uipath`. Recipe shape below shows v19 fields; v20 strips listed render fields and skips position math. Skeleton-fallback logic and `entry-points.json` shape are identical across schemas.

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

Add each trigger output to the variables `inputOutputs[]` array (v19: `root.data.uipath.variables.inputOutputs[]`; v20: top-level `variables.inputOutputs[]`):

```json
{
  "id": "<output.var>",
  "name": "<output.name>",
  "type": "<output.type>",
  "elementId": "<triggerId>",
  "body": "<output.body from tasks describe — full schema>"
}
```

### 3e. In-arg trigger output mapping (entry 3) ownership

In-argument variables that point at this trigger get their full 3-entry shape (inputs[], inputOutputs[], and the trigger node's outputs[]) written by the variables plugin in Step 6.2 — see [`plugins/variables/global-vars/impl-json.md` § In Argument](../../variables/global-vars/impl-json.md). The trigger plugin captures the trigger's `trigger_xxxxxx` ID in the name → ID map; the variables plugin reads that map when writing entry 3 onto this trigger node. No additional work is required here.

Use **original** outputs from `tasks describe` (before simplification) for `body`. The `elementId` is the trigger node's ID.

## Skeleton fallback (unresolved connector / connection)

When the T-entry carries `<UNRESOLVED>` on `type-id`, `connection-id`, or `connector-key`, skip Steps 1-2 and 3c-3d, and write a skeleton node instead. Mirrors the connector-task skeleton pattern in [skeleton-tasks.md](../../../skeleton-tasks.md) — structure preserved, runtime config deferred.

```json
{
  "id": "<trigger_xxxxxx>",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": <stateful per §3a> },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "<display-name>",
    "description": "<description from sdd.md>",
    "uipath": { "serviceType": "Intsvc.EventTrigger" }
  }
}
```

`data.uipath` carries **only** `serviceType` — no `context[]`, `inputs[]`, `outputs[]`, `bindings[]`, `metadata`. Equivalent intent to a connector-task `data: {}` skeleton; trigger nodes need `label` / `description` / `parentElement` to render at all.

**Sibling artifacts:** append the matching `entry-points.json` entry per [manual/impl-json.md § Recipe — entry-points.json](../manual/impl-json.md#recipe--entry-pointsjson). Create the trigger-edge to the first stage normally — both endpoints exist, guardrails pass. No root bindings, no `inputOutputs[]` entries from this trigger.

**Log:** `[SKELETON] Event trigger "<display-name>" written as skeleton — connector "<connector-key>" / connection unresolved.`

**Upgrade:** regenerate from scratch (Rule 5) — no in-place mutation path. Trigger config is sibling-file-coupled (`entry-points.json`, root variable bindings); a partial in-place edit leaves siblings stale.

## Graceful degradation (resolved planning, runtime CLI failure)

If Steps 1-2 fail at runtime despite a resolved T-entry (connection deleted between planning and execution; transient `is describe` error):

| Step failed | What happens | Log |
|---|---|---|
| get-connection | Fall back to skeleton above | `[SKIPPED] get-connection failed — event trigger downgraded to skeleton` |
| tasks describe | Context populated, no outputs | `[SKIPPED] tasks describe failed — trigger outputs omitted` |

All issues appended per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `data.uipath.serviceType` is `"Intsvc.EventTrigger"` (not `WaitForEvent` or `CuratedTrigger`).
2. **Fully configured:** `context[]`, `metadata`, `inputs[]`, `outputs[]`, `bindings[]` all populated per §3c-3d (`outputs[]` simplified — no body/id/target/elementId, `_jsonSchema: null`; `inputs[]` has no `elementId`); the variables `inputOutputs[]` array (v19: `root.data.uipath.variables.inputOutputs[]`; v20: top-level `variables.inputOutputs[]`) has entries for each trigger output. **Skeleton:** all five `data.uipath` fields **absent** (not empty arrays); no root bindings or inputOutputs entries from this trigger; `[SKELETON]` log entry present.
3. Trigger node wired as `--source` in an edge to the first stage.
4. `entry-points.json` has a matching entry referencing the trigger node ID.
