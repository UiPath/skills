# connector-activity task — Implementation (Direct JSON Write)

> **Node `type` value: `execute-connector-activity` (schema-kebab), or `external-agent` / `external-workflow` for an external agent or automation (Step 5.a).** NEVER write `connector-activity` (plugin folder name) or `connector_activity` into JSON `type`. The CLI `--type connector-activity` flag is separate: use it only with `uip maestro case tasks describe` (legacy) or `uip maestro case spec --type activity` (current). See SKILL.md Rule 17 + Plugin Index.

> **Phase split.** Runs across both phases. Phase 2 writes `data.typeId` + `data.connectionId` only; do not call `case spec` in Phase 2. Phase 3 calls `case spec --input-details` once, reads `caseShape`, and mints the task. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch the populated scaffold with `uip maestro case spec --input-details` and put it in `caseplan.case`. Planning performs discovery/reference resolution; implementation reads resolved values from `registry-resolved.json`.

## Prerequisites from Planning

The SDD row provides `type-id`, `connection-id`, `connector-key`, `object-name`, resolved `input-values` (dotted body keys), optional `filter` (`FilterTree`, only when planning Step 7 authored one), `isRequired`, and `runOnlyOnce`. Example row shape: [planning.md § Fields to Resolve](planning.md#fields-to-resolve).

## Configuration Workflow

### Step 1 — Build `--input-details` JSON from the resolved entry

**Filter preflight:** run Step 4 for every top-level `filter:` before Step 2.

Build from `registry-resolved.json`, rewriting connector-body references per Step 1.a:

```jsonc
{
    "bodyParameters": "<resolved input-values.bodyParameters, values rewritten per Step 1.a>",
    "queryParameters": "<resolved input-values.queryParameters, values rewritten per Step 1.a>",
    "pathParameters": "<resolved input-values.pathParameters, values rewritten per Step 1.a>",
    "filter": "<filter from registry-resolved.json or omit>"
}
```

For synthetic HTTP request activities (`object-name === "httpRequest"` / `"http-request"`), do not pass `bodyParameters`; pass the HTTP body through `queryParameters` or omit it. The CLI rejects `bodyParameters`.

Pass a solution-resource picker’s resource **name** as a plain string; `case spec` resolves it and returns the binding. If it exists in multiple folders, add `"<picker>_folderKey": "<folder key>"` and rerun. Put the companion under the `inputs.*` list shown by `case spec` (it may differ from the picker). Orchestrator **Get Asset** uses `id` under `pathParameters` and `id_folderKey` under `queryParameters`. A wrong-list companion is refused and the error identifies the right one; with no companion listed, put it beside the picker. A gating scope selector such as `entityScope` is a reference field: write its lookup `value` (`folder`), not `displayName` (`Folder`).

#### Step 1.a — Rewrite references to canonical sink form

For `bodyParameters`, `queryParameters`, and `pathParameters`, wrap every reference in `=js:(...)`; resolve cross-task references first:

| SDD value | CLI value |
|---|---|
| `"=vars.X"`, `"=metadata.X"`, `"=bindings.X"` | `"=js:(vars.X)"`, `"=js:(metadata.X)"`, `"=js:(bindings.X)"` |
| `"=<other-prefix>.X"` (for example `=response.X`, `=Error.X`, `=datafabric.X`, `=orchestrator.JobAttachments[0]`) | `"=js:(<other-prefix>.X)"` (strip `=`, then wrap) |
| `"<- "Stage"."Task".out"` | Resolve with [output-reference-ID algorithm](../../variables/io-binding/impl-json.md#output-reference-id-authoritative) to `"=vars.<outputReferenceId>"` → `"=js:(vars.<outputReferenceId>)"` |
| `"=js:(<expr>)"` | Pass through unchanged |
| `"<literal value>"` (no leading `=`) | Pass through unchanged |

Full rule and FE source: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

#### Step 1.b — Array-of-object body fields: pre-input scan (MANDATORY)

Before passing `bodyParameters`, scan for keys containing literal `[*]` and halt. `inputs.bodyFields[].name` uses `[*]` only as schema notation, not an input key. Emit real JSON arrays under the parent name in `input-values.bodyParameters` (see [`planning.md` § Array-of-object body fields](planning.md)). Emit:

```text
ERROR: bodyParameters key '<key>' contains literal '[*]'.
        Spec field was: <spec field name>. Expected: '<parent>' with a real JSON array value.
        Fix in the resolved input-values.bodyParameters; do NOT pass [*] keys to the CLI.
```

The CLI accepts literal `field[*]` and validation passes, but runtime APIs return HTTP 400 `UnableToDeserializePostBody`. Repeat after writing; see [§ Post-Write Verification](#post-write-verification) item #12.

#### Step 1.c — Copy `input-values` verbatim; the escaping is already done (MANDATORY)

`registry-resolved.json` contains a real JSON object. Copy `input-values` byte for byte and re-escape nothing: its `=js:` values already carry `\\n` where JavaScript needs `\n`. Adding a level produces `\\\\n` and a literal backslash-n; dropping one produces `\n`, which JSON decodes to a raw line break and faults with `Invalid or unexpected token`. The only added level is during planning when the sdd.md cell becomes ledger JSON: [`planning.md` § 8 Build input-values](planning.md#8-build-input-values).

Pass the payload single-quoted. Bash strips one backslash level inside double quotes; `--input-details "…\\n…"` therefore delivers `\n` and reintroduces the fault. Single quotes preserve it.

### Step 2 — Run `case spec` with input-details

```bash
uip maestro case spec --type activity \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --input-details '<json from Step 1>' \
  --solution-folder "<SolutionDir>" \
  --output json > tasks/spec-cache.<elementId>.json
```

`--solution-folder` is the solution a picker's resource is added to. It defaults to the solution containing the current folder.

`.Data.CaseShape.context` must resolve. If `null`, upgrade the CLI; never adapt the splice to an older response. Create the cache only through the redirect above: save the raw `Result` / `Code` / `Data` envelope byte-for-byte. Do not author, wrap `caseShape`, hand-write, copy from `/tmp`, or use a partial response. Responses can be tens of KB (68 KB for Slack `send_message_to_channel_v2`); incomplete caches silently drop subtrees while `validate` may stay green. The `>` is the one redirect [SKILL.md](../../../../SKILL.md) Rule 14 permits.

**Save the whole response envelope verbatim** to `tasks/spec-cache.<elementId>.json` with the Write tool (Rule 14), not `cp` or a redirect. It is input to `uip maestro case splice`; do not unwrap, re-case, or edit it. The envelope key is `Data.CaseShape` (PascalCase); its shape is camelCase (`context` / `inputs` / `outputs`):

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.Identity` — connectorKey, connectorName, connectorVersion, objectName, objectDisplayName, full TypeCache entry |
| `spec.connection.folderKey` | `.Data.Connection.FolderKey` — needed for the FolderKey binding |
| `spec.caseShape.inputs[]` | `.Data.CaseShape.inputs` — pre-filled body / queryParameters / pathParameters / file inputs |
| `spec.caseShape.outputs[]` | `.Data.CaseShape.outputs` — response (JSON Schema body) / curated / Error |
| `spec.caseShape.context[]` | `.Data.CaseShape.context` — FE-canonical array; its `connection` / `folderKey` values are `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` sentinels that `splice` resolves |
| `spec.diagnostics.fallbacks[]` | `.Data.Diagnostics.Fallbacks` — surface to `build-issues.md` when non-empty. |
| `spec.resourceBindings[]` | `.Data.ResourceBindings` — only when a picker resolved: `resource`, `resourceKey`, and `rows[]` of `name`, `propertyAttribute`, `default`, `bindingIdPlaceholder` (kept camelCase, like `caseShape`). |

Do not pass `--skip-case-shape` in Phase 3; it conflicts with `--input-details` ([case-spec-input-details.md § Validation rules](../../../case-spec-input-details.md#validation-rules-invalidinputdetailserror-on-violation)). The CLI returns the full populated `caseShape`.

Run a separate `case spec` for every connector task. Never reuse another task’s output, even with the same `connection-id`; `caseShape` depends on `objectName`, `httpMethod`, `inputs`, and `outputs`.

### Step 3 — Required-field validation (HARD GATE)

Do not write the task until every required `caseShape.inputs[].body` field is non-empty:

1. From the lean planning spec (run with `--skip-case-shape` in [planning](planning.md) Step 3), collect `inputs.*[?required]`.
2. After Step 2, scan `caseShape.inputs[].body` for every required value.
3. If any is missing, **AskUserQuestion** with missing fields, `displayName`, and expected value type. Use free-form input for open values (channel names, message bodies, IDs); use AskUserQuestion dropdowns for finite values such as `enum`, per [SKILL.md](../../../../SKILL.md).
4. Re-run Step 2 after collecting values, or use a Rule 9 placeholder if the user declines.

Do not guess or skip required fields; ask rather than assume.

### Step 4 — FilterBuilder detection (when planning authored a filter)

When the resolved entry has `filter`, the operation must declare a `FilterBuilder` design parameter. Verify this even though planning Step 7 checks `spec.filter`; the CLI rejects a filter without one.

- With `spec.filter` containing `builder: "ceql"` and `fields[]`, pass the structured tree under `--input-details.filter`. The CLI compiles the runtime CEQL string at `caseShape.inputs[name="queryParameters"].body.<filterParamName>` and the design-time tree at `essentialConfiguration.savedFilterTrees.<filterParamName>` inside the `=jsonString:` blob in `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration`.
- Never pass raw CEQL under `queryParameters` for a FilterBuilder operation. Plain filter fields are native-syntax inputs, not authored FilterTrees.
- Tree shape and operators: [/uipath:uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

If `spec.filter` is undefined, repair the malformed top-level `filter:` before Step 2: find the matching plain query/body field and retain its sink; copy the exact native value from the SDD Inputs row or same-session confirmed model (never derive it from the FilterTree); remove `filter:`; add the value to declared `input-values`; preserve siblings; restart Step 1. If the field or exact value is unavailable or ambiguous, halt and ask; non-interactive runs report a blocker. Never drop the requirement or invent downstream filtering.

### Step 5 — Write the task skeleton, then `splice`

#### 5.a — Skeleton (agent-authored, from the SDD)

Write an empty `data` block with only SDD-known fields:

```json
{
  "id": "<taskId — t + 8 alphanumeric chars>",
  "type": "execute-connector-activity",
  "displayName": "<display name from sdd.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from sdd.md Required, default true>",
  "shouldRunOnlyOnce": "<from sdd.md Run Only Once, default false>",
  "description": "<the task's **Description:** line from sdd.md, word for word>",
  "data": {}
}
```

For an external agent or automation, use `external-agent` or `external-workflow` ([planning § External agents and automations](planning.md#external-agents-and-automations)); `splice` writes `serviceType`. The task's `**Description:**` line from sdd.md, word for word. Do not shorten or reword it. `**Design Rationale:**` is a different line and goes to `tasks/build-issues.md`; use it here only when the block writes no `**Description:**`.

Append to the target stage’s `data.tasks` using `activation-mode` + `entry-rule`, never `lane` alone. Strict `sequential` tasks are new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned next inner array although their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks each get a single-task inner array. Share an inner array only for `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale. Add `runs-sequentially` when the frontend toggle or ordered task-set rule selects it; if `lane` conflicts with mode, mode wins.

#### 5.b — Splice (CLI-authored)

```bash
uip maestro case splice "<caseplan.case>" \
  --task-id "<taskId>" \
  --spec "tasks/spec-cache.<elementId>.json" \
  --connection-id "<connection-id from registry-resolved.json>" \
  --output json
```

`splice` writes `data.serviceType`, `data.context` with sentinels resolved to `=bindings.<id>`, `data.inputs` / `data.outputs` with `id` / `var` / `elementId`, and ConnectionId + FolderKey root bindings with `default` (reusing an existing pair). It copies `body` keys untouched. Re-running with the same arguments is byte-identical; Phase 4 may splice again after fresh `case spec`. Read `Data.Summary` (`ContextEntries`, `Inputs`, `Outputs`, `ConnectionBindingId`, `FolderBindingId`, `BindingsReused`) and record it in `build-issues.md`.

For an external task, a `Warning` means splice guessed the sync service type because `executionType` was missing or not sync, async, or hybrid; record it in `build-issues.md` and verify the activity type id came from the external-agent or external-automation catalog.

Never hand-write `data.context`, `data.inputs`, `data.outputs`, or connector root bindings. **Do not open `connector-trigger-impl.md`, `connector-trigger/impl-json.md`, `case-spec-input-details.md`, or `bindings/impl-json.md` for this task after splicing:** they describe manual event-trigger transport and connector-bound rules, not spliced tasks. Never edit the spec envelope to make splice accept it; a rejected spec lacks `caseShape`, so run `case spec` again without `--skip-case-shape`. `--connection-id` must match the spec’s connection; splice refuses a mismatch and names both ids. Do not pass `--folder-key`; splice takes it from that spec. Each connector task uses its own spec and folder.

#### 5.c — What stays with the agent after splice

Make only these edits:

- **Output binding:** for every output referenced by the SDD (bare name or first segment of a `->` path), apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes), retaining `id` / `var` / `elementId`. Leave unreferenced outputs minted.
- **Output ids:** new outputs use `id` = `var` = camelCase name (`response`, `Error` → `error`); on collision with any id, var, or case variable, suffix `2`, `3`, …; retain an existing output id. If an older CLI minted a `v…` id that is not the name, before any read set `id` / `var` / `value` to the camelCase name, `target` to `=<new var>`, and apply suffixes from 2 per [uniqueness rule](../../variables/global-vars/impl-json.md#uniqueness-rule); preserve `name`, `displayName`, and `source`. Never rename an id already read. The Case Designer preserves name-shaped ids but rewrites `v…` ids without updating reads, causing `CASE_MGMT_REFERENCE_UNBOUND` after save.
- **Solution-resource pickers:** when `spec.resourceBindings[]` exists, do nothing. `splice` creates/reuses one root binding per `rows[]` item (same `resource`, `resourceKey`, `propertyAttribute`), replaces each `bindingIdPlaceholder`, and lists picker rows in task `data.bindings[]`; Summary reports `ResourceBindingIds`. If splice reports `This spec references {{RESOURCE_BINDING_ID:<field>}}, but its ResourceBindings define no row for it`, run `case spec` again. If Summary lacks `ResourceBindingIds` and `data.inputs` retains `{{RESOURCE_BINDING_ID:`, mint one id per row, a root binding for each (`id`, `type` = `"string"`, `resource`, `resourceKey`, `name`, `propertyAttribute`, `default`), replace the placeholder, and list each root binding in task `data.bindings[]`.
- **Multipart file inputs:** apply 5.d.

#### Step 5.d — Multipart file inputs (after splice)

When `caseShape.inputs[]` has `target: "file"` (emitted for `multipart.parameters[].isFile === true`, e.g. Outlook Send Email):

- Preserve literal string `target` = `"file"`; do not prepend `=`.
- Set `value` to `"=vars.<fileVarId>"` (whole-record reference). The FE picker is `selectionOnly` for file inputs (`IntsvcActivityPropertiesUtils.tsx:272-279`), so only a file-typed case Variable is valid; freeform expressions and sub-fields such as `=vars.<id>.FullName` are invalid. The adapter expects the full JobAttachment record.
- Keep no `source`, `body`, or `displayName`; `case spec` returns `{name, type, target}`, splice mints `var` / `id` / `elementId`, and one Edit sets `value`.
- The runtime adapter dereferences the variable to the JobAttachment record and streams bytes from JobAttachment storage into the multipart `file` part.

### Step 6 — Sync IS connection cache

After root bindings, populate the IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred** — run once at end of Step 9.7 in [implementation.md](../../../implementation.md) after all connector tasks, not per task. See [bindings-v2-sync.md § When to Run](../../../bindings-v2-sync.md).

## Graceful degradation

**Always create the task**, including on errors. Start with `data: { "serviceType": "Intsvc.ActivityExecution" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| `case spec` fails | Preserve Phase 2 `data.typeId` + `data.connectionId`; no Phase 3 inputs/outputs/context enrichment. This differs from Rule 9 placeholder `data: {}`. | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-field gate fails (user declines) | Rule 9 placeholder OR re-prompt | `[SKIPPED] required field <name> missing — placeholder task per Rule 9` |
| `get-connection` or `case spec` fails with `Connector catalog unavailable` (`ErrorCode: server_error`) | Rule 9 placeholder `data: {}`; do not preserve typeId/connectionId because nothing resolved. Every `execute-connector-activity` task takes this row ([connector-integration.md § Catalog unavailable](../../../connector-integration.md#catalog-unavailable-typecache-5xx)). | `[SKIPPED] connector catalog unavailable (TypeCache <status>) — placeholder task per Rule 9` |
| All succeed | Skeleton + `splice` (Step 5), then Step 6 sync | — |

Append all issues to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"execute-connector-activity"`, or `"external-agent"` / `"external-workflow"` per Step 5.a.
2. `data.serviceType` is splice-authored (`Intsvc.ActivityExecution`, or the sync/async agent/workflow type); never edit it.
3. `data.context[]` contains `connectorKey`, `connection`, `resourceKey`, `folderKey` when applicable, `objectName`, `method`, `path`, `metadata`, and `executionType` for an external task whose spec carries one; it does not contain `_label` or `operation` on `execute-connector-activity`. An external task retains splice-authored `operation` and `eventMode`, if any.
4. `data.context[name="connection"].value` is `=bindings.<ConnectionBindingId from splice Summary>`; no `{{` sentinel remains anywhere in `data`.
5. `data.context[name="folderKey"].value` is `=bindings.<FolderBindingId from splice Summary>`; omit it when `spec.connection.folderKey` is null.
6. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is the CLI-produced `=jsonString:…`; do not modify it.
7. Root ConnectionId and folderKey bindings exist with splice-reported ids and each has `default`.
8. `data.bindings[]` contains only splice-authored picker rows (absent or `[]` without a picker); never copy connection/folder bindings there.
9. Every `data.inputs[]` and `data.outputs[]` entry has splice-authored `var` / `id` / `elementId`, with output uniqueness from Step 5.c.
10. At Phase 3 exit, [implementation.md § Step 12 Check 12](../../../implementation.md#step-12--end-of-phase-3-validator-pass) re-asserts 3–8 for every connector node.
11. After deferred sync, `bindings_v2.json` `resources` matches top-level `bindings[]`.
12. **No literal `[*]` keys in `data.inputs[name="body"].body` (or any input body).** Scan recursively (`JSON.stringify` + regex `"[^"]*\[\*\][^"]*"\s*:`). Halt on any; Step 1.b was skipped or incomplete. Use real arrays under parent names, e.g. `"toRecipients": [{...}]`, never `"toRecipients[*]": {...}`. Validation may pass, but runtime returns HTTP 400.
13. **Lossless inputs (HARD GATE).** Every resolved `input-values` field appears unchanged in its matching `data.inputs[].body`; a resolved picker and `_folderKey` companion instead contain `=bindings.<id>`. A top-level `filter:` requires `spec.filter` and successful compilation. Otherwise halt and repair; never warn and continue.
14. **Spliced subtree is byte-identical to the cache (HARD GATE).** Compare written `data.context` / `data.inputs` / `data.outputs` with `tasks/spec-cache.<elementId>.json`; only placeholder substitutions and minted `var`/`id`/`elementId` may differ. `validate` does not catch content loss; missing `multipartParameters` can pass validation and fail with `400 "Unable to parse multipart body"`.
15. **No placeholder left behind.** No `{{RESOURCE_BINDING_ID:` remains, and every `rows[]` item has a root binding with its id.

## What NOT to Do

- **Do NOT resolve a picker yourself** (catalog search, `uip solution resources add`, or hand-written rows); `case spec` does it.
- **Do NOT add `operation` or `_label` to `data.context[]`.** FE adds `operation` only for triggers.
- **Do NOT add `designTimeMetadata` to the metadata body.**
- **Do NOT add top-level `errorState` to the metadata body.** It belongs inside `activityPropertyConfiguration.errorState`, as supplied by `caseShape.context`.
- **Do NOT copy connection or folder bindings into `data.bindings[]`.** Central root `bindings[]` owns them; only splice-authored picker rows belong there. Without a picker, omit the key or write `[]`; both are equivalent.
- **Do NOT hand-write `data.context`, `data.inputs`, `data.outputs`, or connector root bindings.** `uip maestro case splice` writes them from the saved envelope.
- **Do NOT translate, drop, or reroute an SDD filter.** Use a FilterTree only with `spec.filter`; otherwise preserve the exact SDD value in its declared plain sink or halt (Step 4).
- **Do NOT pass `ceqlExpression` directly under `--input-details`.** It is derived only.
- **Do NOT pass `bodyParameters` for synthetic HTTP request activities.** Use `queryParameters` or omit it.
- **Do NOT pass literal `field[*]` keys in `bodyParameters`.** `[*]` in `inputs.bodyFields[].name` is schema notation, not an input key; use real arrays under the parent name (see [planning.md](planning.md)). Step 1.b halts on such keys.
- **Do NOT auto-inject `entryConditions`.** Step 10 in [implementation.md](../../../implementation.md) handles them; injection here duplicates them.
- **Never reuse a reference ID from a prior case or session.** IDs such as Jira project keys and Slack channel IDs are scoped to the authenticated account behind the connection. Resolve fresh with `uip is resources run list` against the current `--connection-id`. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).
- **Do NOT call legacy `uip maestro case tasks describe` or `uip is resources describe`.** `case spec --input-details` replaces both; legacy output lacks `caseShape` / placeholders.

## Known Limitations

The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only, not `optionalConfiguration`. Runtime debug/publish works, but the FE editor may not render some fields until the user reconfigures the task; DAP repopulates them on form open.

<!-- END: impl-json.md -->