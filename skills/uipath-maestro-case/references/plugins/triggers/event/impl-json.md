# event trigger — Implementation (Direct JSON Write)

Configure the case-level event trigger by writing directly into the trigger node in `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md). Phase 3 calls `uip maestro case spec --type trigger --input-details` once and consumes the populated `caseShape`.

For shared CLI invocation, placeholder substitution, and anti-patterns, see [connector-trigger-common.md](../../../connector-trigger-common.md). This doc covers only the **trigger-node-specific** parts.

> **v20 layout-strip (Rule 18).** Read `Schema:` header from `tasks.md`. In **v20 mode**, omit ALL of: `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Skip the position-computation step entirely. Keep `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`, `data.label`, `data.description`, `data.uipath`. Recipe shape below shows v19 fields; v20 strips listed render fields and skips position math. Skeleton-fallback logic and `entry-points.json` shape are identical across schemas.

## Prerequisites from Planning

The `tasks.md` entry provides: `type-id`, `connection-id`, `connector-key`, `object-name`, `event-operation`, `event-mode`, `input-values`, `filter`.

## Step 1 — Build `--input-details` JSON from tasks.md

Construct the input-details object literally from `tasks.md`:

```jsonc
{
    "eventParameters": "<input-values.eventParameters or omit>",
    "filter": "<filter from tasks.md or omit>"
}
```

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

## Step 2 — Run `case spec` with input-details

Single CLI call replaces the legacy `get-connection` + `case tasks describe --type connector-trigger` two-call pattern. See [common § Phase 3 Implementation Step 2](../../../connector-trigger-common.md#step-2--run-case-spec-with-input-details) for the command and response handling.

## Step 3 — Required-event-param validation (HARD GATE)

This is a hard gate — do NOT proceed to write the trigger node until every required event parameter has a non-empty value in the populated `caseShape.inputs[name="eventParameters"].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` per [common § Planning Pipeline 5](../../../connector-trigger-common.md#5-validate-required-event-parameters-hard-gate)), collect `inputs.eventParameters[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[name="eventParameters"].body` and verify every required event parameter has a value.
3. If any required event parameter is missing, **AskUserQuestion** — list the missing parameters with their `name` and what kind of value is expected.
4. Re-run Step 2 after collecting the missing values, OR fall back to skeleton per the Skeleton fallback section below if user declines.

> **Do NOT guess or skip missing required event parameters.** Trigger registration fails at runtime when a required event parameter is missing.

## Step 4 — Mint binding IDs and trigger registration key

Per [common § Step 3](../../../connector-trigger-common.md#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key). For event triggers, `<eventTriggerKey>` uses `<connection-id>_<startNode.id>` where `startNode.id` is the trigger node's own id (since the event trigger IS the start node for its case-entry path) — matches FE convention at `PackagingUtil.ts:227`.

## Step 5 — Substitute placeholders in `caseShape.context`

Per [common § Step 4](../../../connector-trigger-common.md#step-4--substitute-placeholders-in-caseshapecontext).

## Step 6 — Mint `var` / `id` on outputs (no `elementId` on inputs)

For each entry in `caseShape.inputs[]`:
- `var` = `v` + 8 alphanumeric chars
- `id` = same as `var`
- **No `elementId`** on trigger inputs (different from in-stage task inputs).

For each entry in `caseShape.outputs[]`: same fields plus `elementId = <triggerNodeId>`. Apply the dedup rule per [common § Step 5](../../../connector-trigger-common.md#step-5--mint-var--id--elementid-on-inputs-and-outputs) (`response` / `error` collide across multiple connector tasks/triggers).

> **Trigger output simplification.** Unlike in-stage `wait-for-connector` task outputs, event-trigger outputs are simplified for the trigger node: strip `body`, `target`, set `_jsonSchema: null`. Keep `name`, `displayName`, `type`, `source`, plus the minted `var` / `id` / `value` / `elementId`. The full `body` schema flows into the variables `inputOutputs[]` array (Step 8) so consumer tasks can resolve the schema. Mirrors FE event-trigger packaging.

## Step 7 — Build trigger node and write to caseplan.json

### 7a. Identify or create the trigger node

For a **single-trigger case**, configure the existing `trigger_1` node. For **multi-trigger cases**, create a new node:
- ID: `trigger_` + 6 alphanumeric chars
- Position: `{ x: -100, y: 620 }` (auto-stack below existing triggers; v19 only)

Set the trigger's display name from `tasks.md`.

### 7b. `data` structure

```json
{
  "label": "<display-name>",
  "uipath": {
    "serviceType": "Intsvc.EventTrigger",
    "context": "<caseShape.context — placeholders substituted in Step 5>",
    "inputs":  "<caseShape.inputs  — var/id minted in Step 6; NO elementId>",
    "outputs": "<caseShape.outputs — simplified per Step 6; var/id/elementId minted, dedup applied>",
    "bindings": []
  }
}
```

## Step 8 — Register trigger outputs as root inputOutputs

Add each trigger output to the variables `inputOutputs[]` array (v19: `root.data.uipath.variables.inputOutputs[]`; v20: top-level `variables.inputOutputs[]`):

```json
{
  "id": "<output.var>",
  "name": "<output.name>",
  "type": "<output.type>",
  "elementId": "<triggerId>",
  "body": "<output.body from caseShape.outputs BEFORE simplification — full schema>"
}
```

Use the **original** `body` from `caseShape.outputs` (before Step 6 simplification stripped it from the trigger node). The `elementId` is the trigger node's ID.

### 8a. In-arg trigger output mapping (entry 3) ownership

In-argument variables that point at this trigger get their full 3-entry shape (inputs[], inputOutputs[], and the trigger node's outputs[]) written by the variables plugin in Step 6.2 — see [`plugins/variables/global-vars/impl-json.md` § In Argument](../../variables/global-vars/impl-json.md). The trigger plugin captures the trigger's `trigger_xxxxxx` ID in the name → ID map; the variables plugin reads that map when writing entry 3 onto this trigger node. No additional work is required here.

## Step 9 — Append root-level bindings

Per [common § Root-level bindings](../../../connector-trigger-common.md#root-level-bindings). Two entries (ConnectionId, FolderKey), `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

## Step 10 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

## Skeleton fallback (unresolved connector / connection)

When the T-entry carries `<UNRESOLVED>` on `type-id`, `connection-id`, or `connector-key`, skip Steps 2-10 and write a skeleton node instead. Mirrors the connector-task skeleton pattern in [skeleton-tasks.md](../../../skeleton-tasks.md) — structure preserved, runtime config deferred.

```json
{
  "id": "<trigger_xxxxxx>",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": <stateful per §7a> },
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

If `case spec` fails at runtime despite a resolved T-entry (connection deleted between planning and execution; transient API error):

| Step failed | What happens | Log |
|---|---|---|
| `case spec` | Fall back to skeleton above | `[SKIPPED] case spec failed — event trigger downgraded to skeleton` |
| Required-event-param gate fails | Skeleton per Rule 8 OR re-prompt | `[SKIPPED] required event parameter <name> missing — event trigger downgraded to skeleton` |

All issues appended per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `data.uipath.serviceType` is `"Intsvc.EventTrigger"` (not `WaitForEvent` or `CuratedTrigger`).
2. **Fully configured:** `context[]`, `inputs[]` (no `elementId`), `outputs[]` (simplified — no `body`, no `target`, `_jsonSchema: null`), and `bindings[] = []` all present per §7b. The variables `inputOutputs[]` array (v19: `root.data.uipath.variables.inputOutputs[]`; v20: top-level `variables.inputOutputs[]`) has entries for each trigger output with the full `body` schema.
3. **Skeleton:** all four `data.uipath` fields beyond `serviceType` **absent** (not empty arrays); no root bindings or inputOutputs entries from this trigger; `[SKELETON]` log entry present.
4. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify).
5. When the trigger has event parameters: `data.context[name="metadata"].body.bindings[Property].metadata.ParentResourceKey` is `EventTrigger.<eventTriggerKey>` (substituted from `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`).
6. Trigger node wired as `--source` in an edge to the first stage.
7. `entry-points.json` has a matching entry referencing the trigger node ID.
