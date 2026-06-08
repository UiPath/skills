# event trigger — Implementation (Direct JSON Write)

Configure the case-level event trigger by writing directly into the trigger node in `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md). Phase 3 calls `uip maestro case spec --type trigger --input-details` once and consumes the populated `caseShape`.

For shared CLI invocation, placeholder substitution, anti-patterns, and the canonical form for filter expressions with variable references, see [connector-trigger-common.md](../../../connector-trigger-common.md). For the per-sink canonical-form table covering all expression-syntax decisions in this skill, see [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink). This doc covers only the **trigger-node-specific** parts.

> **v20 layout-strip (Rule 19).** Read `Schema:` header from `tasks.md`. In **v20 mode**, omit ALL of: `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Skip the position-computation step entirely. Keep `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`, `data.label`, `data.description`, `data.uipath`. Recipe shape below shows v19 fields; v20 strips listed render fields and skips position math. Placeholder-fallback logic and `entry-points.json` shape are identical across schemas.

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
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder per the Placeholder fallback section below if user declines.

> **Do NOT guess or skip missing required event parameters.** Trigger registration fails at runtime when a required event parameter is missing.

## Step 4 — Mint binding IDs and trigger registration key

Per [common § Step 3](../../../connector-trigger-common.md#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key). For event triggers, `<eventTriggerKey>` uses `<connection-id>_<startNode.id>` where `startNode.id` is the trigger node's own id (since the event trigger IS the start node for its case-entry path) — matches FE convention at `PackagingUtil.ts:227`.

## Step 5 — Substitute placeholders in `caseShape.context`

Per [common § Step 4](../../../connector-trigger-common.md#step-4--substitute-placeholders-in-caseshapecontext).

## Step 6 — Mint `var` / `id` on trigger CONFIG inputs

For each entry in `caseShape.inputs[]` (these are trigger configuration: `eventParameters`, `filter`, etc.):
- `var` = `v` + 8 alphanumeric chars
- `id` = same as `var`
- **No `elementId`** on trigger inputs (different from in-stage task inputs).

> **`caseShape.outputs[]` are NOT minted here.** Under B's redesign, all writes to `triggerNode.data.uipath.outputs[]` are owned by the variables plugin (see [`../../variables/global-vars/impl-json.md` § Dispatcher Loop](../../variables/global-vars/impl-json.md)). This plugin captures the un-minted `caseShape.outputs[]` into `tasks/trigger-spec-cache.json` (Step 8) for the variables plugin to consume.

## Step 7 — Build trigger node and write to caseplan.json

### 7a. Identify or create the trigger node

For a **single-trigger case**, configure the existing `trigger_1` node. For **multi-trigger cases**, create a new node:
- ID: `trigger_` + 6 alphanumeric chars
- Position: `{ x: -100, y: 620 }` (auto-stack below existing triggers; v19 only)

Set the trigger's display name from `tasks.md`. Record `T<N> → trigger_xxxxxx` in `id-map.json` so the variables plugin can resolve T-number references.

### 7b. `data` structure

```json
{
  "label": "<display-name>",
  "uipath": {
    "serviceType": "Intsvc.EventTrigger",
    "context": "<caseShape.context — placeholders substituted in Step 5>",
    "inputs":  "<caseShape.inputs  — var/id minted in Step 6; NO elementId>",
    "outputs": [],
    "bindings": []
  }
}
```

> `outputs: []` is initialized empty. The variables plugin populates it in Phase 3 Step 6.2 using the sidecar from Step 8 below.

## Step 8 — Write trigger-spec-cache.json sidecar

Write the un-minted `caseShape` into the shared sidecar artifact for the variables plugin to consume. Path: `tasks/trigger-spec-cache.json` (relative to project directory). Keyed by T-number.

```jsonc
// tasks/trigger-spec-cache.json
{
  "T02": {
    "context": "<caseShape.context — post-substitution from Step 5>",
    "inputs":  "<caseShape.inputs — un-minted, with body schema intact>",
    "outputs": "<caseShape.outputs — un-minted, with body schema intact>"
  },
  "T03": { ... }
}
```

**Important — un-minted shape:**

- Do NOT mint `var` / `id` / `elementId` on the `outputs[]` entries written to the sidecar — the variables plugin mints them at Step 6.2 according to whether the SDD references each output. The plain field name from the schema is preserved (e.g., `name: "subject"`).
- Do NOT strip `body` from the outputs — the variables plugin needs the full JSON Schema when emitting the root companion (especially for `jsonSchema`-typed outputs).

**Sidecar lifecycle:**

- **Persistence.** The sidecar persists across hard stops (Phase 2 approval gate, Phase 2 publish-for-preview, etc.) so Phase 3 re-entry doesn't lose spec data. Do NOT regenerate on re-entry — read the existing file.
- **Regeneration.** Rule 6 (`Continue with regenerate from scratch`) replaces the sidecar entirely (Write, not append), starting from an empty `{}`. Rule 7 (`Continue without regenerate`) preserves the existing sidecar.
- **Multi-trigger append.** Trigger plugin runs once per trigger T-entry. Each invocation **merges by T-number** into the existing sidecar JSON: read the file, set or replace the top-level `<T-number>` key, write back. Append order is **T-number ascending** (T02 then T03 then ...). Re-running a single trigger T-entry overwrites only its own key; other triggers' keys are untouched. This makes the sidecar **idempotent** for multi-trigger cases.
- **Abort cleanup.** On `Abort` (per [`phased-execution.md`](../../../phased-execution.md) abort semantics), the sidecar persists alongside other artifacts — `phased-execution.md` mandates no artifact deletion on abort; user owns partial state. On the next run with regenerate-from-scratch (Rule 6) the sidecar is overwritten; otherwise it is reused.
- **Edit discipline.** Per Rule 13, edit via Read + Write/Edit only. Do NOT use jq, sed, or any other tool that bypasses the file-state tracker.

The variables plugin consumes this in Phase 3 Step 6.2 — see [`../../variables/global-vars/impl-json.md` § Inputs the plugin reads](../../variables/global-vars/impl-json.md) and § Dispatcher Loop.

## Step 9 — Append root-level bindings

Per [common § Root-level bindings](../../../connector-trigger-common.md#root-level-bindings). Two entries (ConnectionId, FolderKey), `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

## Step 10 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

## Placeholder fallback (unresolved connector / connection)

When the T-entry carries `<UNRESOLVED>` on `type-id`, `connection-id`, or `connector-key`, skip Steps 2-10 and write a placeholder node instead. Mirrors the connector-task placeholder pattern in [placeholder-tasks.md](../../../placeholder-tasks.md) — structure preserved, runtime config deferred.

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

`data.uipath` carries **only** `serviceType` — no `context[]`, `inputs[]`, `outputs[]`, `bindings[]`, `metadata`. Equivalent intent to a connector-task `data: {}` placeholder; trigger nodes need `label` / `description` / `parentElement` to render at all.

**Sibling artifacts:** append the matching `entry-points.json` entry per [manual/impl-json.md § Recipe — entry-points.json](../manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints). No trigger-edge is created (edges retired) — the first stage's `case-entered` entry condition starts the case. No root bindings, no `inputOutputs[]` entries from this trigger.

**Log:** `[SKIPPED] Event trigger "<display-name>" written as placeholder — connector "<connector-key>" / connection unresolved.`

**Upgrade:** regenerate from scratch (Rule 5) — no in-place mutation path. Trigger config is sibling-file-coupled (`entry-points.json`, root variable bindings); a partial in-place edit leaves siblings stale.

## Graceful degradation — unified placeholder conditions

Three distinct conditions can trigger placeholder fallback for an event trigger. All three downgrade to the same placeholder shape (per § Placeholder fallback above); only the surfacing message and the AskUserQuestion offered differ.

| Trigger | What's happening | Placeholder action | Log |
|---|---|---|---|
| **Planning-time unresolved** (tasks.md T-entry carries `<UNRESOLVED>` on `type-id` / `connection-id` / `connector-key`) | Registry lookup didn't find the connector or connection at planning time | Skip Steps 2–10 entirely; write the placeholder node directly per § Placeholder fallback | `[SKIPPED] Event trigger "<display-name>" written as placeholder — connector "<connector-key>" / connection unresolved.` |
| **`case spec` failure at Phase 3** (T-entry was resolved at planning, but the CLI call fails at implementation — connection deleted between phases, transient API error) | Spec call itself errored | Catch the exception; fall through to placeholder fallback shape | `[SKIPPED] case spec failed — event trigger downgraded to placeholder` |
| **Required-event-param gate failure at Phase 3** (spec call succeeded, but `caseShape.inputs[name="eventParameters"].body` is missing required fields after AskUserQuestion either declined or didn't fully resolve) | Required event parameter never collected | If user picked decline or re-prompt failed, fall through to placeholder | `[SKIPPED] required event parameter <name> missing — event trigger downgraded to placeholder` |

**Why full placeholder (not `typeId`/`connectionId` preservation)?** Event triggers are sibling-file-coupled (`entry-points.json` entry, root variable bindings for In args). A partial in-place edit leaves siblings stale. Phase-3 `case spec` failure on event triggers therefore downgrades fully to placeholder — asymmetric with connector-task graceful-degradation, which preserves `data.typeId + data.connectionId` because the in-stage parent node can render without sibling-file coupling (see [`../../tasks/connector-activity/impl-json.md`](../../tasks/connector-activity/impl-json.md) for the connector-task fallback table — it preserves more state because the coupling profile is different).

All issues appended per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `data.uipath.serviceType` is `"Intsvc.EventTrigger"` (not `WaitForEvent` or `CuratedTrigger`).
2. **Fully configured:** `context[]`, `inputs[]` (CONFIG inputs only — no `elementId`), `outputs[]` (empty array — populated later by variables plugin Step 6.2), and `bindings[] = []` all present per §7b.
3. **`tasks/trigger-spec-cache.json` exists** with this trigger's T-number as a top-level key, containing un-minted `context`, `inputs`, `outputs` from `caseShape`.
4. **`id-map.json`** contains `"T<N>": { "kind": "trigger", "id": "<triggerId>" }` for this trigger.
5. **Placeholder:** all four `data.uipath` fields beyond `serviceType` **absent** (not empty arrays); no root bindings entries from this trigger; no `trigger-spec-cache.json` entry from this trigger; `[SKIPPED]` log entry present.
6. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify).
7. When the trigger has event parameters: `data.context[name="metadata"].body.bindings[Property].metadata.ParentResourceKey` is `EventTrigger.<eventTriggerKey>` (substituted from `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`).
8. No edge from this trigger (edges retired) — the case starts via the first stage's `case-entered` entry condition. `schema.edges` stays `[]`.
9. `entry-points.json` has a matching entry referencing the trigger node ID.

Run `uip maestro case validate <file> --output json` after all triggers for this plugin's batch are added.
