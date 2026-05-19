# connector-trigger task — Implementation (Direct JSON Write)

> **Node `type` value: `wait-for-connector` (schema-kebab).** NEVER write `connector-trigger` (plugin folder name) into the JSON `type` field. The CLI `--type connector-trigger` flag is a separate concept — used only when calling the legacy `uip maestro case tasks describe` command. The current path uses `uip maestro case spec --type trigger`. See SKILL.md Rule 16 + Plugin Index.

> **Phase split.** Runs across both phases. Phase 2 writes `data.typeId` + `data.connectionId` only — no `case spec` call in Phase 2. Phase 3 calls `case spec --type trigger --input-details` once, reads the populated `caseShape`, substitutes placeholders, and mints the task. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch the populated trigger task scaffold via `uip maestro case spec --type trigger --input-details`, then drop it into `caseplan.json` as a `wait-for-connector` task. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md` and threads them through the spec call.

For shared CLI invocation, placeholder substitution, and anti-patterns, see [connector-trigger-common.md](../../../connector-trigger-common.md). This doc covers only the **task-specific** parts.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"7dc57f24-894c-5ae2-a902-66056fa40609"` |
| `connection-id` | `"fc82e610-c454-4bc7-a1a5-b5aa529d1ba6"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"Message"` |
| `event-operation` | `"EMAIL_RECEIVED"` |
| `event-mode` | `"polling"` or `"webhooks"` |
| `input-values` | `{"eventParameters":{"parentFolderId":"AAMkADNm..."}}` (already resolved IDs) |
| `filter` (optional) | `{"groupOperator":"And","filters":[...]}` (FilterTree object — present only when planning Step 7 authored a filter) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Configuration Workflow

### Step 1 — Build `--input-details` JSON from tasks.md

Construct the input-details object literally from `tasks.md`:

```jsonc
{
    // eventParameters from tasks.md input-values.eventParameters (or omit when absent)
    "eventParameters": "<input-values.eventParameters or omit>",
    // filter — FilterTree object from tasks.md (or omit when not authored)
    "filter": "<filter from tasks.md or omit>"
}
```

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

### Step 2 — Run `case spec` with input-details

Single CLI call replaces the legacy `get-connection` + `case tasks describe --type connector-trigger` two-call pattern. See [common § Phase 3 Implementation Step 2](../../../connector-trigger-common.md#step-2--run-case-spec-with-input-details) for the command and response handling.

### Step 3 — Required-event-param validation (HARD GATE)

This is a hard gate — do NOT proceed to write the task until every required event parameter has a non-empty value in the populated `caseShape.inputs[name="eventParameters"].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` per [common § Planning Pipeline 5](../../../connector-trigger-common.md#5-validate-required-event-parameters-hard-gate)), collect `inputs.eventParameters[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[name="eventParameters"].body` and verify every required event parameter has a value.
3. If any required event parameter is missing, **AskUserQuestion** — list the missing parameters with their `name` and what kind of value is expected.
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder task per Rule 8 if user declines to provide a value.

> **Do NOT guess or skip missing required event parameters.** Trigger registration fails at runtime when a required event parameter is missing.

### Step 4 — Mint binding IDs and trigger registration key

Per [common § Step 3](../../../connector-trigger-common.md#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key). Note for in-stage triggers: `<eventTriggerKey>` uses `<connection-id>_<startNode.id>` — `startNode.id` is the case-level start node, NOT the stage id (matches FE convention).

### Step 5 — Substitute placeholders in `caseShape.context`

Per [common § Step 4](../../../connector-trigger-common.md#step-4--substitute-placeholders-in-caseshapecontext). Three placeholders: `{{CONN_BINDING_ID}}`, `{{FOLDER_BINDING_ID}}` (when present), `{{TRIGGER_REGISTRATION_KEY}}` (when the trigger has event parameters).

### Step 6 — Mint `var` / `id` / `elementId` on inputs and outputs

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`).

For each entry in `caseShape.inputs[]`:
- `var` = `v` + 8 alphanumeric chars
- `id` = same as `var`
- `elementId` = the task's elementId

For each entry in `caseShape.outputs[]`: same fields, **plus the dedup rule** per [common § Step 5](../../../connector-trigger-common.md#step-5--mint-var--id--elementid-on-inputs-and-outputs) (`response` / `error` collide across multiple connector tasks/triggers).

**Output binding per `->` and `=` operators** (parsed from tasks.md `outputs:` row; documented in [`../../variables/io-binding/planning.md`](../../variables/io-binding/planning.md#discovering-inputoutput-names)):

- For each `caseShape.outputs[]` entry, check whether the SDD's `outputs:` row in tasks.md references it (matched by schema field name on the left side of `->` or as a bare name).
- **`<sdd-field-path> -> <sdd-name>`** (extract) → reassign-shape: override the minted `var/value` with `<sdd-name>`, keep `id` at the camelCased leaf segment, set `originalVar` to the same. **`source` is `=<sdd-field-path>` verbatim.** The SDD writes the full runtime path (e.g., `response.subject`, `Error`); skill never adds, removes, or infers envelope prefixes. Resolve `name` (display name) and type from the Step 0 schema — top-level entries match by their `source` field (with `=` stripped); nested fields are found by navigating the parent entry's `body` schema. **`originalVar` is load-bearing** — tells FE's `mutateRootVariables` (`VariableMutationUtils.ts:135`) to skip root-mirroring, preserving the case-Variable companion across FE edits.
- **Bare `<name>` in SDD** (no operator) → match against a top-level Step 0 entry; if matched, write camelCased name to `var/id/value`; `source` is the entry's pre-populated value verbatim. No `originalVar`.
- **`<sdd-name> = <expression>`** (set / compute / copy) → emit a Scenario E entry on `caseShape.outputs[]`: `{name: "<sdd-name>", custom: true, var: "<sdd-name>", value: "<expression>", source: "<same as value>", target: "", body: "", type: <case var's type>, elementId: "root"}`. **No `id`**, no `originalVar`. NO root mirror — FE's `isUpdateExistingOutput` filter skips it.
- Schema fields with no SDD reference → fall back to today's auto-mint shape (`var` = camelCased schema name, dedup-suffix on collision).
- Dot-paths in `->` paths are supported (e.g., `response.message.ts`, `Error.code`). Array indexing not supported in v1.
- Target case variable on both `->` and `=` MUST exist in Case Variables table (validated at planning time).

### Step 7 — Build task and write to caseplan.json

```json
{
  "id": "<taskId>",
  "type": "wait-for-connector",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": "<caseShape.context — placeholders substituted in Step 5>",
    "inputs":  "<caseShape.inputs  — var/id/elementId minted in Step 6>",
    "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied in Step 6>",
    "bindings": []
  }
}
```

Append the task to the target stage's `tasks[]` array. Default: own task set (one task per lane). **Exception:** if this task is a parallel member of a `runs-sequentially` group, push into the shared lane of that group (shared lane = parallel siblings inside the sequence, semantic).

### Step 8 — Append root-level bindings

Per [common § Root-level bindings](../../../connector-trigger-common.md#root-level-bindings). Two entries (ConnectionId, FolderKey), `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

### Step 9 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.WaitForEvent" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| `case spec` fails | Phase 2 shape preserved — `data.typeId` + `data.connectionId` only, no Phase 3 inputs/outputs/context enrichment. Distinct from a Rule 8 placeholder (`data: {}`) — typeId/connectionId are resolved, only the spec-driven enrichment is skipped. Log per Rule 8 reporting | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-event-param gate fails (user declines) | Placeholder per Rule 8 OR re-prompt | `[SKIPPED] required event parameter <name> missing — placeholder task per Rule 8` |
| All succeed | Full population per Steps 4-9 including bindings_v2 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"wait-for-connector"` and `data.serviceType` is `"Intsvc.WaitForEvent"`
2. `data.context[]` populated from `caseShape.context` with placeholders substituted (`=bindings.<connBindingId>`, etc.)
3. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify)
4. When the trigger has event parameters: `data.context[name="metadata"].body.bindings[Property].metadata.ParentResourceKey` is `EventTrigger.<eventTriggerKey>` (substituted from `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`)
5. Root bindings exist for ConnectionId + folderKey with the minted ids; `data.bindings[]` is empty `[]`
6. Each entry in `data.inputs[]` / `data.outputs[]` has `var` / `id` / `elementId` minted; uniqueness rule applied for outputs
7. `bindings_v2.json` `resources` array matches the schema-appropriate bindings array (v19: `root.data.uipath.bindings[]`; v20: top-level `bindings[]`) after the deferred sync
