# connector-activity task — Implementation (Direct JSON Write)

> **Node `type` value: `execute-connector-activity` (schema-kebab).** NEVER write `connector-activity` (plugin folder name) or `connector_activity` into the JSON `type` field. The CLI `--type connector-activity` flag is a separate concept — used only when calling `uip maestro case tasks describe` (legacy) or `uip maestro case spec --type activity` (current). See SKILL.md Rule 16 + Plugin Index.

> **Phase split.** Runs across both phases. Phase 2 writes `data.typeId` + `data.connectionId` only — no `case spec` call in Phase 2. Phase 3 calls `case spec --input-details` once, reads the populated `caseShape`, and mints the task. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch the populated connector task scaffold via `uip maestro case spec --input-details`, then drop it into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md` and threads them through the spec call.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"c7ce0a96-2091-3d94-b16f-706ebb1eb351"` |
| `connection-id` | `"bc095c1f-671f-4669-8634-b7164fa46aa0"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"send-mail-v2"` |
| `input-values` | `{"bodyParameters":{"message.toRecipients":"user@example.com"},"queryParameters":{...}}` (already resolved IDs, dotted body keys) |
| `filter` (optional) | `{"groupOperator":"And","filters":[...]}` (FilterTree object — present only when planning Step 7 authored a filter) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Configuration Workflow

### Step 1 — Build `--input-details` JSON from tasks.md

Construct the input-details object from `tasks.md`, rewriting every value containing a reference to its canonical sink form (connector body fields use `=js:(<expr>)`):

```jsonc
{
    // bodyParameters from tasks.md input-values.bodyParameters (dotted keys preserved;
    // each value rewritten to canonical form per Step 1.a)
    "bodyParameters": "<input-values.bodyParameters with values rewritten>",
    // queryParameters from tasks.md input-values.queryParameters (same rewrite rule)
    "queryParameters": "<input-values.queryParameters with values rewritten>",
    // pathParameters from tasks.md input-values.pathParameters (same rewrite rule)
    "pathParameters":  "<input-values.pathParameters with values rewritten>",
    // filter — FilterTree object from tasks.md (or omit when not authored)
    "filter": "<filter from tasks.md or omit>"
}
```

Synthetic HTTP request activities (`object-name === "httpRequest"` / `"http-request"`) reject `bodyParameters` — pass HTTP body via `queryParameters` instead, or omit. The CLI rejects bodyParameters at validation time.

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

#### Step 1.a — Rewrite references to canonical sink form

Connector body sinks (`bodyParameters`, `queryParameters`, `pathParameters`) require `=js:(...)` wrap for every reference. Resolve cross-task refs first, then apply the wrap:

| Value in tasks.md | Value passed to CLI |
|---|---|
| `"=vars.X"` | `"=js:(vars.X)"` |
| `"=metadata.X"` | `"=js:(metadata.X)"` |
| `"=bindings.X"` | `"=js:(bindings.X)"` |
| `"=<other-prefix>.X"` (e.g. `=response.X`, `=Error.X`, `=datafabric.X`, `=orchestrator.JobAttachments[0]`) | `"=js:(<other-prefix>.X)"` — strip leading `=`, wrap in `=js:(...)` |
| `"<- "Stage"."Task".out"` | resolve to `"=vars.<outputVar>"` → `"=js:(vars.<outputVar>)"` |
| `"=js:(<expr>)"` (pre-wrapped operator expression) | pass-through unchanged |
| `"<literal value>"` (no leading `=`) | pass-through unchanged |

Full per-sink rule and FE source-of-truth: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

#### Step 1.b — Array-of-object body fields: pre-input scan (MANDATORY)

Before passing `bodyParameters` to the CLI, scan for keys containing literal `[*]`. Halt if any are present — the binding is malformed.

The `[*]` in `inputs.bodyFields[].name` is **schema notation** (JSONPath-style "array of") for documentation only — NOT a valid input key. Array-of-object body fields MUST be expressed in tasks.md `input-values.bodyParameters` as real JSON arrays under the parent name (see [`planning.md` § Array-of-object body fields](planning.md)). The planner is responsible for emitting the correct shape; this step is a safety net.

**Halt condition.** If any `bodyParameters` key contains literal `[*]`, halt with explicit error:
```
ERROR: bodyParameters key '<key>' contains literal '[*]'.
        Spec field was: <spec field name>. Expected: '<parent>' with a real JSON array value.
        Fix in tasks.md input-values.bodyParameters; do NOT pass [*] keys to the CLI.
```

The CLI accepts the literal `field[*]` key (well-formed JSON) and validate passes, but runtime APIs reject with HTTP 400 `UnableToDeserializePostBody`. The check repeats as a post-write verification — see [Step 8 Post-Write Verification](#post-write-verification) item #11.

### Step 2 — Run `case spec` with input-details

```bash
uip maestro case spec --type activity \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --input-details "<json from Step 1>" \
  --output json
```

The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details` — see [case-spec-input-details.md § Validation rules](../../../case-spec-input-details.md#validation-rules-invalidinputdetailserror-on-violation)). The CLI returns the full `caseShape` populated with values from `--input-details`.

Save the response. The interesting parts:

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.identity` — connectorKey, connectorName, connectorVersion, objectName, objectDisplayName, full TypeCache entry |
| `spec.connection.folderKey` | `.Data.connection.folderKey` — needed for the FolderKey binding |
| `spec.caseShape.inputs[]` | `.Data.caseShape.inputs` — pre-filled body / queryParameters / pathParameters / file inputs |
| `spec.caseShape.outputs[]` | `.Data.caseShape.outputs` — response (JSON Schema body) / curated / Error |
| `spec.caseShape.context[]` | `.Data.caseShape.context` — 8-entry FE-canonical array, with `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders |
| `spec.diagnostics.fallbacks[]` | `.Data.diagnostics.fallbacks` — surface to `build-issues.md` when non-empty. |

> **Each connector task runs its own `case spec`.** Even when two tasks share the same `connection-id`, `caseShape` is task-shape-specific (different `objectName`, `httpMethod`, `inputs`, `outputs`). Never reuse another task's spec output.

### Step 3 — Required-field validation (HARD GATE)

This is a hard gate — do NOT proceed to write the task until every required field has a non-empty value in the `caseShape.inputs[].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` in [planning](planning.md) Step 3), collect `inputs.*[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[].body` and verify every required field has a value.
3. If any required field is missing, **AskUserQuestion** — list the missing fields with their `displayName` and what kind of value is expected. Free-form input is appropriate when the value space is open-ended (channel names, message bodies, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../../../../SKILL.md).
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder task per Rule 8 if user declines to provide a value.

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

### Step 4 — FilterBuilder detection (when planning authored a filter)

When `tasks.md` carries a `filter:` object, the activity's operation must declare a `FilterBuilder` design parameter. The CLI rejects the filter at configure time when no FilterBuilder param exists; the planning step 7 should already have caught this by checking `spec.filter` presence, but verify here as a safety net.

- `spec.filter` present (with `builder: "ceql"` and `fields[]`) → CEQL filter is supported. Pass the structured tree under `--input-details.filter`. The CLI compiles it into both halves of the contract: the runtime CEQL string at `caseShape.inputs[name="queryParameters"].body.<filterParamName>` AND the design-time tree under `essentialConfiguration.savedFilterTrees.<filterParamName>` (inside the `=jsonString:` blob in `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration`).
- **Do NOT pass a raw CEQL string under `queryParameters.where`** (or whichever connector-specific name) when authoring a filter. The CLI rejects this; even if it didn't, the design-time tree would be empty and Studio Web would render the filter widget as `undefined` when the activity is reopened.
- Tree shape, operator table, examples → [/uipath:uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

If the operation has no FilterBuilder parameter, server-side filtering is not supported — the spec will return `filter: undefined`. Filter downstream (post-execution) instead.

### Step 5 — Mint binding IDs

Mint two prefixed IDs for the connection + folder bindings:

| Binding | ID format |
|---|---|
| Connection binding | `b` + 8 alphanumeric chars (e.g. `bA1B2C3D4`) |
| Folder binding | `b` + 8 alphanumeric chars (different from connection binding) |

These ids are **picked inline by the agent** (per SKILL.md Rule 13) — no subprocess.

Save them as `<connBindingId>` and `<folderBindingId>` for Step 6.

### Step 6 — Substitute binding placeholders in `caseShape.context`

`caseShape.context[]` carries placeholders at the spec output:

```jsonc
[
    { "name": "connection", "type": "string", "value": "=bindings.{{CONN_BINDING_ID}}" },
    { "name": "folderKey",  "type": "string", "value": "=bindings.{{FOLDER_BINDING_ID}}" },  // present only when spec.connection.folderKey !== null
    // …other entries (connectorKey, resourceKey, objectName, method, path, metadata) — values are fully resolved already
]
```

Replace the two placeholders with the minted ids:

- `{{CONN_BINDING_ID}}` → `<connBindingId>` (Step 5)
- `{{FOLDER_BINDING_ID}}` → `<folderBindingId>` (Step 5; entry only present when folderKey was non-null)

The `metadata` context entry's `body.activityPropertyConfiguration.configuration` JSON-string contains an `essentialConfiguration` blob already populated by the CLI (with `instanceParameters`, `objectName`, `operation`, `httpMethod`, `path`, `savedFilterTrees` if any). Do not modify this blob — copy verbatim.

### Step 7 — Mint `var` / `id` / `elementId` on inputs and outputs

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`).

For each entry in `caseShape.inputs[]`:
- `var` = `v` + 8 alphanumeric chars (unique across the case — see uniqueness rule in [global-vars/impl-json.md](../../variables/global-vars/impl-json.md))
- `id` = same as `var`
- `elementId` = the task's elementId

For each entry in `caseShape.outputs[]`:
- Same fields, plus the **dedup rule**: `caseShape.outputs[]` returns generic names like `response` and `error` for every connector task. When multiple connector tasks exist in the same case, these collide. Apply the [uniqueness rule](../../variables/global-vars/impl-json.md#uniqueness-rule): collect all existing output `var` values across every task already in `caseplan.json`; if a `var` already exists, append a counter suffix starting at 2 (e.g., `response` → `response2`, `error` → `error2`). Update `var`, `id`, `value`, and `target` (as `=<new var>`) with the suffixed name. `name`, `displayName`, and `source` stay unchanged.

**Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is `caseShape.outputs[]` from `case spec` (Step 2 above). The dedup rule above applies first; output binding consumes the deduped names.

#### Step 7.a — Multipart file inputs

When `caseShape.inputs[]` contains an entry with `target: "file"` (multipart sink — emitted by `case spec` for activities whose IS spec has `multipart.parameters[].isFile === true`, e.g., Outlook Send Email):

- `target` is a **literal string** `"file"` (the IS request-shape multipart sink name), NOT an expression. Preserve verbatim — do not prepend `=`.
- `value` MUST be `"=vars.<fileVarId>"` (whole-record reference). The FE picker is `selectionOnly` for file inputs (`IntsvcActivityPropertiesUtils.tsx:272-279`) — only a file-typed case Variable can be wired; freeform expressions are rejected at picker time. Sub-field references (`=vars.<id>.FullName`) are NOT valid for file inputs — the runtime adapter expects the full JobAttachment record to dereference.
- No `source`, no `body`, no `displayName` on the multipart file input entry — `case spec` returns just `{name, type, target}`; mint `var` / `id` / `elementId` / `value` per Step 7 and stop.
- The runtime adapter dereferences `=vars.<fileVarId>` to the JobAttachment record at execution time and streams bytes from the JobAttachment store into the multipart `file` part of the outbound HTTP request.

### Step 8 — Build `data` and write to caseplan.json

Generate the task skeleton:

```json
{
  "id": "<taskId>",
  "type": "execute-connector-activity",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.ActivityExecution",
    "context": "<caseShape.context — placeholders substituted in Step 6>",
    "inputs":  "<caseShape.inputs  — var/id/elementId minted in Step 7>",
    "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied in Step 7>",
    "bindings": []
  }
}
```

Append the task to the target stage's `tasks[]` array. Default: own task set (one task per lane). **Exception:** if this task is a parallel member of a `runs-sequentially` group, push into the shared lane of that group (shared lane = parallel siblings inside the sequence, semantic).

### Step 9 — Append root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-task value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this task's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `spec.connection.folderKey` in Step 2 response. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).
- Binding IDs `<connBindingId>` / `<folderBindingId>` come from Step 5.

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

### Step 10 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 in [implementation.md](../../../implementation.md) (after all connector tasks), not per-task. See [bindings-v2-sync.md § When to Run](../../../bindings-v2-sync.md).

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.ActivityExecution" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| `case spec` fails | Phase 2 shape preserved — `data.typeId` + `data.connectionId` only, no Phase 3 inputs/outputs/context enrichment. Distinct from a Rule 8 placeholder (`data: {}`) — typeId/connectionId are resolved, only the spec-driven enrichment is skipped. Log per Rule 8 reporting | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-field gate fails (user declines) | Placeholder per Rule 8 OR re-prompt | `[SKIPPED] required field <name> missing — placeholder task per Rule 8` |
| All succeed | Full population per Steps 5-10 including bindings_v2 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"execute-connector-activity"`
2. `data.serviceType` is `"Intsvc.ActivityExecution"`
3. `data.context[]` has: `connectorKey`, `connection`, `resourceKey`, `folderKey` (when applicable), `objectName`, `method`, `path`, `metadata` — but NOT `operation` or `_label`
4. `data.context[name="connection"].value` is `=bindings.<connBindingId>` (substituted from `{{CONN_BINDING_ID}}`)
5. `data.context[name="folderKey"].value` is `=bindings.<folderBindingId>` (substituted from `{{FOLDER_BINDING_ID}}`); entry absent when `spec.connection.folderKey` was null
6. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify)
7. Root bindings exist for ConnectionId + folderKey with the minted ids
8. `data.bindings[]` is empty `[]`
9. Each entry in `data.inputs[]` and `data.outputs[]` has `var` / `id` / `elementId` minted (uniqueness rule applied for outputs)
10. `bindings_v2.json` `resources` array matches the schema-appropriate bindings array (v19: `root.data.uipath.bindings[]`; v20: top-level `bindings[]`) after the deferred sync
11. **No literal `[*]` keys in `data.inputs[name="body"].body` (or any input body).** Scan recursively (JSON.stringify + regex `"[^"]*\\[\\*\\][^"]*"\\s*:`). If any key contains literal `[*]`, halt — Step 1.b translation was skipped or incomplete. The body MUST use real arrays under parent names (e.g., `"toRecipients": [{...}]`), never `"toRecipients[*]": {...}`. Validate passes regardless; runtime APIs reject with HTTP 400.

## What NOT to Do

- **Do NOT add `operation` or `_label` to `data.context[]`.** The FE only adds `operation` for triggers; activity context must not have it.
- **Do NOT add `designTimeMetadata` to the metadata body.** The FE does not include it for case management tasks.
- **Do NOT add top-level `errorState` to the metadata body.** Error state belongs inside `activityPropertyConfiguration.errorState` only — that's already the shape in `caseShape.context`.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE crashes if activity tasks have task-level binding copies.
- **Do NOT modify `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration`.** It's a CLI-produced `=jsonString:…` blob with `essentialConfiguration.{instanceParameters, objectName, operation, httpMethod, path, savedFilterTrees}` — copy verbatim.
- **Do NOT pass a raw CEQL string under `queryParameters.where`** (or whichever connector-specific name) when authoring a filter. Pass the structured tree under `filter:` in tasks.md and let the CLI compile both halves.
- **Do NOT pass `ceqlExpression` directly under `--input-details`.** Derived only.
- **Do NOT pass `bodyParameters` for synthetic HTTP request activities.** Use `queryParameters` instead, or omit.
- **Do NOT pass literal `field[*]` keys in `bodyParameters`.** The `[*]` in `inputs.bodyFields[].name` is JSONPath-style schema notation meaning "array of"; it is NOT a valid input key. Express array-of-object body fields as real JSON arrays under the parent name (see [planning.md](planning.md)). Pre-input scan in [Step 1.b](#step-1b--array-of-object-body-fields-pre-input-scan-mandatory) halts on any literal `[*]` key.
- **Do NOT auto-inject `entryConditions`.** Step 10 in [implementation.md](../../../implementation.md) handles them — injecting here creates duplicates.
- **Never reuse a reference ID from a prior case or session.** Reference IDs (e.g., Jira project keys, Slack channel IDs) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources run list` against the current `--connection-id`. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).
- **Do NOT call legacy `uip maestro case tasks describe` or `uip is resources describe`.** `case spec --input-details` replaces both. The legacy commands still work but produce a different shape that doesn't include `caseShape` / placeholders.

## Known Limitations

- The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only (not `optionalConfiguration`). Tasks work at runtime (debug/publish) but the FE editor may not render certain fields until the user re-configures the task in the UI. DAP repopulates these on form open. Documented in `~/Documents/knowledge/Skill_CLI/connector/case-spec-fe-discrepancies.md` (CLI-side).
