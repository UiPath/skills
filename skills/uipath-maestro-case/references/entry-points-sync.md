# entry-points.json Input/Output Refresh

Refresh `entry-points.json` `entryPoints[].input` / `.output` JSON-Schemas from declared case In/Out arguments; these fields are the external-caller contract.

Trigger plugins scaffold ([`plugins/case/impl-json.md`](plugins/case/impl-json.md)) and append ([`plugins/triggers/*/impl-json.md`](plugins/triggers/manual/impl-json.md)) entries with empty `input`/`output` (`{ "type": "object", "properties": {} }`) at Step 6.1, before variables exist. Back-fill them here; do not change trigger plugins.

This mirrors Studio Web’s canvas transformation: `PO.Frontend/src/utils/PackagingUtil.ts` (`getEntryPoints()`, `getEntryPointJsonSchemaForVariable()`, `getTypeAndFormatForType()`, `JOB_ATTACHMENTS_DEFINITION`) and `src/services/uipath/variables/VariableUtil.ts` (`getVariablesDefinedInRootUiPath`). The FE regenerates this file on every canvas save and, since PR #6062, first load; this skill does the same.

## When to Run

Run at **Phase 2 Step 6.3**, immediately after Step 6.2, after all `entryPoints[]` and `variables.inputs[]` / `outputs[]` are final. Phase 3 neither adds nor renames them (uniqueness suffixes `var`/`id`, never `name`), and this step keys on `name`, so the Phase-2 publish-for-review artifact remains correct. On regenerate-from-scratch (Rule 7), recompute fully and never append; the operation is idempotent.

**Check 6** (end of Phase 3, [`implementation.md` § Step 12](implementation.md)) re-verifies parity.

## Source → target

- `input`: `variables.inputs[]` whose `elementId` equals the entry trigger id (`filePath` after its last `#`).
- `output`: every `variables.outputs[]` item, for every entry.

Project only formal In/Out args; do not project root `variables.inputOutputs[]` state or trigger-payload `Variable`s. For each Out-arg, merge its `outputs[]` entry (`{id,name,type,var}`) with the `inputOutputs[]` companion matching `name` and `elementId:"root"`; the companion supplies `default`/`required`/`body`. In-args need no merge.

## Procedure

1. Read `caseplan.case` (`variables.inputs[]`, `variables.outputs[]`, `variables.inputOutputs[]`) and `entry-points.json`.
2. For every existing `entryPoints[]`, set `triggerId` to the substring of `filePath` after its last `#`, `input` to `projectSchema(inputs[] where elementId === triggerId)`, and `output` to `projectSchema(all merged Out-args)`.
3. Preserve `filePath`, `uniqueId`, `type`, `displayName`, and any `isTransactionRoot: true` verbatim. Do not recompute `displayName` or mint `uniqueId` (`uniqueId` is the BPMN start-event `entryPointId`); this skill does not set `isTransactionRoot` but must preserve it.
4. Preserve top-level `$schema` and `$id`; write the whole file with **4-space indent**. Never append entries; trigger plugins own them at Step 6.1.

The FE entry set equals existing `entryPoints[]`: `getEntryPoints` emits only BPMN start events with an `entryPointId` outside `bpmn:SubProcess`. Case triggers are top-level and already have minted `uniqueId`/`entryPointId`, so refresh creates and drops none.

### projectSchema(vars) → schema object

Mirror `getEntryPointJsonSchemaForVariable`:

- Empty `vars` returns `{ "type": "object", "properties": {} }`, with no `required` or `definitions`.
- **Non-empty** →

```json
{ "type": "object", "properties": { /* one per var, source order */ }, "required": [ /* see below */ ], "definitions": { /* only if needed */ } }
```
- Otherwise emit keys in order `type`, `properties`, `required`, then `definitions` if needed; emit one property per var in source order, keyed by `var.name`.
- `required` contains every `var.name` with `required === true`, in source order, with no type exclusion.
- Emit `definitions` when a `file` var or a `jsonSchema`/`array` body contains a JobAttachment schema; its value is `JOB_ATTACHMENTS_DEFINITION` below.

The current type enum ([`global-vars/planning.md` § Types](plugins/variables/global-vars/planning.md)) is `string | number | integer | float | double | boolean | datetime | date | jsonSchema | file`; retain `array` and `time` for FE fidelity/future-proofing. Array-shaped data may arrive as `jsonSchema` with an array body.

### Per-variable property body

| `var.type` | Body | `title` / `default` |
|---|---|---|
| `string`, `integer`, `number`, `boolean` | `{ "type": <same type> }` | both |
| `float` | `{ "type": "number", "format": "float" }` | both |
| `double` | `{ "type": "number", "format": "double" }` | both |
| `date` | `{ "type": "string", "format": "date" }` | both |
| `datetime` | `{ "type": "string", "format": "date-time" }` | both |
| `time` | `{ "type": "string", "format": "time" }` | both |
| `file` | `{ "$ref": "#/definitions/job-attachment" }` | neither |
| `jsonSchema` | inlined body | neither |
| `array` | `{ "type": "array", "items": <items>, "title": <name> }` | title only |

For scalar/date/time/float/double types, emit `type`, optional `format`, `title: var.name`, then `default` only when `var.default` is truthy. Preserve the default verbatim as a string; omit `""` or absent values. Unmatched types fall back to `{ "type": <rawType> }`. `file` sets the definitions flag.

For `jsonSchema`, use `var.body ?? var._jsonSchema`. If absent/null or an unparsable string, emit `{}`. Otherwise parse strings, delete `$schema`, apply `rewriteJobAttachmentRefs`, and inline the result.

For `array`, parse string `var.body` (unparseable means `{}`). Choose `<items>` in this order: `rewriteJobAttachmentRefs(body.items)` when `body?.items` exists; `{ "$ref": "#/definitions/job-attachment" }` when `var.subType` is `file` or `octet-stream` (set the definitions flag); `getTypeAndFormatForType(var.subType)` for a primitive; otherwise `{}`. `title` is always `var.name`; arrays have no default.

### rewriteJobAttachmentRefs (nested JobAttachment rewrite)

Walk a schema node. Return non-object/null nodes unchanged. Replace any node carrying `"x-uipath-resource-kind": "JobAttachment"` with `{ "$ref": "#/definitions/job-attachment" }` and set the definitions flag. Preserve an already equal `{ "$ref": "#/definitions/job-attachment" }` and set the flag. Recurse through object/array children except under `definitions` and `$defs`; if no descendant matches, return the original node unchanged (identity preserved).

### JOB_ATTACHMENTS_DEFINITION (constant)

Emit this exact fixed constant, independent of the file variable’s `body`:

```json
{
    "job-attachment": {
        "type": "object",
        "properties": {
            "ID": { "type": "string", "description": "Orchestrator attachment key" },
            "FullName": { "type": "string", "description": "File name" },
            "MimeType": { "type": "string", "description": "The MIME type of the content, such as \"application/json\" or \"image/png" },
            "Metadata": { "type": "object", "description": "Dictionary<string, string> of metadata", "additionalProperties": { "type": "string" } }
        },
        "required": ["ID"],
        "x-uipath-resource-kind": "JobAttachment"
    }
}
```

The decoded `MimeType.description` is `The MIME type of the content, such as "application/json" or "image/png` (plain quotes, final quote unclosed). In file JSON text it contains exactly three `\"` and no other backslash. Write it with Write/Edit as JSON text, never through a shell or code string that adds a second escaping layer (`\\\"`). After writing, the parsed value must contain no `\`.

## FE branch coverage (audit)

Cover every FE branch: `getEntryPoints` start events with/without `entryPointId`; `bpmn:SubProcess` exclusion; truthy/falsy `displayName`; set/unset `isTransactionRoot`; input scoping by `elementId === startNode.id`; all outputs; empty/non-empty schemas; all-variable `required`; `jsonSchema` present/null/unparseable; `file`; `array` and its four item fallbacks; scalar/date/datetime/time/float/double mappings; unmatched raw types; `rewriteJobAttachmentRefs` non-object, JobAttachment, existing `$ref`, recursion excluding `definitions`/`$defs`, and no-match identity; truthy-only defaults; and Out-arg companion sourcing.

## Check 6 — Entry-point schema parity (Step 12 validator)

Non-HALT. For each entry, with `triggerId` equal to `filePath` after `#`:

1. Verify `input == projectSchema(inputs[] where elementId == triggerId)` and `output == projectSchema(merged Out-args)`, including keys, type/format mapping, file `$ref`, inlined `jsonSchema`, title/default presence, empty `{type,properties:{}}` shape without `required`, and `definitions` presence.
2. Verify `required` contains every var with `required === true`, with no type exclusion.
3. Verify `filePath` `#` fragments are unique. Trigger append is blind and may duplicate entries; refresh propagates schemas but cannot deduplicate them.
4. Verify every `inputs[].elementId` matches an entry trigger fragment. An orphaned In-arg silently vanishes from the contract.

On a (1)/(2) mismatch, re-run the Procedure and re-check once. On a (3)/(4) finding or continuing (1)/(2) divergence, log it to `## Open Items for User` in `tasks/build-issues.md` and continue. Never HALT (build-with-best policy, [`implementation.md` § Step 12](implementation.md)).

## Worked example

`variables.inputs[]` (all `elementId: trigger_1`): `test_date` (datetime, default `"2029-10-12"`, `required:true`), `test_arrary` (jsonSchema, body `{"$schema":…,"type":"array","items":{"type":"string"}}`), `test_default` (float, default `"12.0"`), `test_date_time` (datetime, default `""`), `test_file` (file, `required:true`), `test_json` (jsonSchema, body `{"$schema":…,"type":"object","properties":{…},"required":[]}`, `required:true`). `variables.outputs[]`: `test_out` (double); its `inputOutputs[]` companion default `"1.3"`.

Entry `/content/caseplan.case.bpmn#trigger_1`:

```json
"input": {
    "type": "object",
    "properties": {
        "test_date": { "type": "string", "format": "date-time", "title": "test_date", "default": "2029-10-12" },
        "test_arrary": { "type": "array", "items": { "type": "string" } },
        "test_default": { "type": "number", "format": "float", "title": "test_default", "default": "12.0" },
        "test_date_time": { "type": "string", "format": "date-time", "title": "test_date_time" },
        "test_file": { "$ref": "#/definitions/job-attachment" },
        "test_json": { "type": "object", "properties": { "test": { "type": "string" }, "newProperty2": { "type": "boolean" } }, "required": [] }
    },
    "required": ["test_date", "test_file", "test_json"],
    "definitions": { "job-attachment": { "...": "constant block above" } }
},
"output": {
    "type": "object",
    "properties": {
        "test_out": { "type": "number", "format": "double", "title": "test_out", "default": "1.3" }
    },
    "required": []
}
```

Notes: `test_arrary`/`test_json` inline their body minus `$schema` (no `title`/`default`). `test_file` → `$ref`, and triggers the `input`-level `definitions` block. `test_date_time`'s empty default is omitted. `test_json` (jsonSchema, `required:true`) **is** included in `input.required` — confirmed against a re-saved `test_in_out` FE export (`["test_date","test_file","test_json"]`).

## Multi-trigger distribution (confirmed)

A `test_in_out` re-saved with two triggers — `trigger_1` (primary) and `StartEvent_Trigger_OkGfLw` (Trigger 2) — produces **two** entries, confirming the scoping rule from a real FE export:

| entry (`filePath#`) | `input.properties` (scoped by `elementId`) | `output.properties` (all) |
|---|---|---|
| `trigger_1` | trigger_1's In-args (`test_date` … `test_intput_t1_bool`) | `test_out`, `test_out_t2` |
| `StartEvent_Trigger_OkGfLw` | **only `test_t2_in_var`** | `test_out`, `test_out_t2` |

Each entry's `input` carries only the In-args whose `elementId` is that trigger; **every** entry carries **all** Out-args. An In-arg bound to a trigger with no entry — e.g. one still pointing at a `preview-node-id` ghost node (an uncommitted canvas preview that leaked into `caseplan.case`) — matches no entry and is silently dropped from the contract; the `elementId` filter skips it (Check 6's orphan guard catches it).

<!-- END: entry-points-sync.md -->