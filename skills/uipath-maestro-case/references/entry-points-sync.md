# entry-points.json Input/Output Refresh

Refresh `entry-points.json` `entryPoints[].input` / `.output` JSON-Schemas from the declared case In/Out arguments. The entry-point `input`/`output` is the case's external-caller contract — the typed arguments another process/case passes in and reads back.

Trigger plugins scaffold ([`plugins/case/impl-json.md`](plugins/case/impl-json.md)) and append ([`plugins/triggers/*/impl-json.md`](plugins/triggers/manual/impl-json.md)) each entry with **empty** `input`/`output` (`{ "type": "object", "properties": {} }`) at Step 6.1 — variables don't exist yet. This step back-fills them once variables are declared. No trigger-plugin change: empty-at-emit is correct.

> **This is a direct port of the Studio Web canvas transformation.** Source: `PO.Frontend/src/utils/PackagingUtil.ts` — `getEntryPoints()`, `getEntryPointJsonSchemaForVariable()`, `getTypeAndFormatForType()`, and the `JOB_ATTACHMENTS_DEFINITION` constant; variable extraction in `src/services/uipath/variables/VariableUtil.ts` (`getVariablesDefinedInRootUiPath`). The FE runs this on every canvas save and (since PR #6062, `always save canvas file on canvas load`) on first load, regenerating `entry-points.json` from the case variables. The skill produces the same file directly.

## When to Run

**Phase 2 Step 6.3** — immediately after Step 6.2 (variable declaration). One run. Both prerequisites complete:

- all `entryPoints[]` entries exist (Step 6.1 triggers),
- all In/Out formal args exist (Step 6.2 variables Loop B).

In/Out formal args (`variables.inputs[]` / `outputs[]`) are final at 6.2 — Phase 3 never adds or renames them (the uniqueness rule suffixes `var`/`id`, never `name`, and this step keys on `name`). Running at 6.3 keeps the Phase-2 publish-for-review artifact correct.

Re-run on regenerate-from-scratch (Rule 6). Idempotent — full recompute, never append.

**Check 6** (end of Phase 3, [`implementation.md` § Step 12](implementation.md)) re-verifies parity as cheap insurance.

## Source → target

| Entry-point field | Source (`getEntryPoints`) | Scope |
|---|---|---|
| `input` | `variables.inputs[]` | only In-args whose `elementId` == THIS entry's trigger id (= `filePath` after `#`) |
| `output` | `variables.outputs[]` | ALL Out-args → every entry |

NOT projected: `variables.inputOutputs[]` root state and trigger-payload `Variable`s. Only formal In/Out args reach the contract.

**Out-arg field sourcing.** The FE reads `default`/`required`/`body` directly off the in-memory output Variable. On disk those fields are split: `variables.outputs[]` carries only `{id,name,type,var}`; the matching `inputOutputs[]` companion (same `name`, `elementId:"root"`) carries `default`/`required`/`body`. So treat each Out-arg as its `outputs[]` entry **merged with its `inputOutputs[]` companion** (matched by `name`). In-args need no merge — `variables.inputs[]` already carries `default`/`required`/`body`.

## Procedure

1. Read `caseplan.json` (`variables.inputs[]`, `variables.outputs[]`, `variables.inputOutputs[]`) and `entry-points.json`.
2. For each entry in `entryPoints[]`:
   - `triggerId` = `filePath` substring after the last `#`.
   - `entry.input`  = projectSchema(`inputs[]` where `elementId === triggerId`).
   - `entry.output` = projectSchema(Out-args from all `outputs[]`, each merged with its companion).
   - Preserve `filePath`, `uniqueId`, `type`, `displayName` verbatim. `displayName` is FE-derived (`getElementLabel`) but the trigger plugin already set it — the refresh does NOT recompute it, only the `input`/`output`. Mint NO `uniqueId` (`uniqueId` == the BPMN start-event `entryPointId` GUID; a pure refresh keeps it).
   - `isTransactionRoot: true` is emitted by the FE only when `root.data.isTransactionRoot` is set. The case skill does not set it today; if a future entry carries it, preserve it — never strip.
3. Preserve top-level `$schema`, `$id`. Write the whole file with **4-space indent** (matches the trigger recipe — no whitespace churn).

> **FE entry set ≡ existing `entryPoints[]`.** `getEntryPoints` emits an entry only for a BPMN start event that (a) has an `entryPointId` and (b) is not inside a `bpmn:SubProcess`. In the skill these map 1:1 to the entries the trigger plugin already created (each case trigger is a top-level start event with a minted `uniqueId`/`entryPointId`). So iterating existing `entryPoints[]` is equivalent — the refresh creates none and drops none. (Case triggers are never inside a subprocess, so the SubProcess guard never excludes one.)

Never append `entryPoints[]` entries here — entries are owned by the trigger plugins (Step 6.1).

### projectSchema(vars) → schema object

Mirrors `getEntryPointJsonSchemaForVariable`:

- **Empty set** (`vars.length === 0`) → `{ "type": "object", "properties": {} }`. No `required`, no `definitions`. (This is exactly the scaffold/trigger empty shape — correct when a trigger has no In-args, or a case has no Out-args.)
- **Non-empty** →

```json
{ "type": "object", "properties": { /* one per var, source order */ }, "required": [ /* see below */ ], "definitions": { /* only if needed */ } }
```

Object key order: `type`, `properties`, `required`, then `definitions`.

- **`properties`** — one entry per var, in source-array order, keyed by `var.name` (NOT `id`/`var`). Body per the type rules below.
- **`required`** — `var.name` for every var with `required === true`, in source order (`variables.filter(v => v.required)`). **No type exclusion** — `jsonSchema`/`file`/etc. all qualify. The FE UI permits marking any start-event **input** required regardless of type (`canMarkRequired = isStartEvent && variableType === "input"`, `InputOutputVariablesAddNewDialog.tsx:148`), and `required` is preserved through every serialization stage for all types (no per-type branch; repo round-trip test `xml-serialization.test.ts:2657`). Confirmed against a re-saved `test_in_out` FE export: `input.required` = `["test_date","test_file","test_json"]` — the `jsonSchema` var `test_json` **is** included. (An earlier export of the same case omitted it only because `entry-points.json` hadn't been regenerated after `test_json` was marked required — the staleness PR #6062 addresses; re-saving produced the correct array.) Include every `.required` var, regardless of type.
- **`definitions`** — present only when a `file`-typed var, or a `jsonSchema`/`array` body that contained a JobAttachment schema, was projected (the `shouldAddJobAttachmentsDefinition` flag). Value = the constant `JOB_ATTACHMENTS_DEFINITION` block below.

### Per-variable property body

Keyed by `var.name`. Branch on `var.type`:

| `type` | property body | `title` | `default` |
|---|---|---|---|
| `string` | `{ "type": "string" }` | yes | yes |
| `integer` | `{ "type": "integer" }` | yes | yes |
| `boolean` | `{ "type": "boolean" }` | yes | yes |
| `float` | `{ "type": "number", "format": "float" }` | yes | yes |
| `double` | `{ "type": "number", "format": "double" }` | yes | yes |
| `date` | `{ "type": "string", "format": "date" }` | yes | yes |
| `datetime` | `{ "type": "string", "format": "date-time" }` | yes | yes |
| `time` | `{ "type": "string", "format": "time" }` | yes | yes |
| `file` | `{ "$ref": "#/definitions/job-attachment" }` | no | no |
| `jsonSchema` | inlined body (see below) | no | no |
| `array` | `{ "type": "array", "items": <items>, "title": <name> }` (see below) | yes | no |

- **scalar / date / datetime / time / float / double** (the `getTypeAndFormatForType` path) — emit `{ <type>, <format?> }`, then append `"title": <var.name>` (always), then `"default": <var.default>` **only when `var.default` is truthy** (verbatim string — never coerced; `""`/absent → omit). Property body key order: `type`, `format`, `title`, `default`. **Fallback:** any `type` not matched above (i.e. not double/float/date/datetime/time and not file/jsonSchema/array) falls through to bare `{ "type": <rawType> }` — string/integer/boolean today, and any future enum value degrades to `{type}` rather than failing.
- **`file`** — `{ "$ref": "#/definitions/job-attachment" }` only. Sets the definitions flag. No `title`/`default`.
- **`jsonSchema`** — `body = var.body ?? var._jsonSchema`. **Fallback:** if `body` is null/absent, or (when a string) fails `JSON.parse`, the property is `{}` (empty object — no schema, no title/default). Otherwise: parse if string, delete its `$schema` key, run `rewriteJobAttachmentRefs`, inline the result. No `title`/`default`.
- **`array`** — `{ "type":"array", "items": <items>, "title": <var.name> }` (title always; no default). `body = var.body` parsed if string (unparseable → `{}`, so `body?.items` is absent and resolution falls to `subType`). `<items>` =
  1. `rewriteJobAttachmentRefs(body.items)` if `body?.items` exists,
  2. else `{ "$ref": "#/definitions/job-attachment" }` if `var.subType` is `file`/`octet-stream` (sets definitions flag),
  3. else `getTypeAndFormatForType(var.subType)` if `subType` is a primitive,
  4. else `{}`.

> The current case-variable type enum ([`global-vars/planning.md` § Types](plugins/variables/global-vars/planning.md)) is `string | integer | float | double | boolean | datetime | date | jsonSchema | file` — no `array` or `time`. Those two rows are ported from the FE for fidelity/future-proofing; today array-shaped data arrives as `jsonSchema` with an array body (handled by the jsonSchema branch).

### `rewriteJobAttachmentRefs` (nested JobAttachment rewrite)

Used by the `jsonSchema` and `array` branches to normalize a file embedded inside a schema. Walk the schema node:

- Non-object / null → returned unchanged.
- A node carrying `"x-uipath-resource-kind": "JobAttachment"` → replaced with `{ "$ref": "#/definitions/job-attachment" }`; sets the definitions flag.
- A node already equal to `{ "$ref": "#/definitions/job-attachment" }` → kept; sets the flag (counts as a match).
- Object/array → recurse into children, **except** the `definitions` and `$defs` keys, which are left as-authored (no recursion). If no descendant matched, the original node is returned unchanged (identity preserved).

So a `jsonSchema`/`array` body whose items or properties include a JobAttachment schema gets those occurrences rewritten to `$ref` and triggers the input/output-level `definitions` block — same mechanism as a top-level `file` var.

### `JOB_ATTACHMENTS_DEFINITION` (constant)

Emit verbatim. Note the inner quotes in `MimeType.description` — reproduce exactly (this matches the FE constant; a divergent `description` triggers FE re-save drift):

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

Fixed constant — NOT sourced from the file var's `body` (the FE emits it even when the var carries no `body`).

## FE branch coverage (audit)

Every conditional in the FE source (`PackagingUtil.ts`) and where this doc handles it:

| FE function / branch | Handled |
|---|---|
| `getEntryPoints`: start event **has** `entryPointId` | → one entry (≡ existing `entryPoints[]`) |
| `getEntryPoints`: **no** `entryPointId` | → no entry (skill never creates an entry without a minted `uniqueId`) |
| `getEntryPoints`: start event inside `bpmn:SubProcess` | → skipped (N/A — case triggers are top-level) |
| `getEntryPoints`: `displayName` truthy / falsy | preserved as-is (not recomputed) |
| `getEntryPoints`: `isTransactionRoot` set / unset | preserved if present; skill doesn't set it |
| `getEntryPoints`: input scoped `elementId === startNode.id`; output = all | Source → target |
| `getEntryPointJsonSchemaForVariable`: empty var set | `{type:object,properties:{}}` — no `required`/`definitions` |
| …non-empty | `properties` + `required` (+ `definitions` if flagged) |
| …`required = vars.filter(v=>v.required)` | required rule — no type exclusion |
| per-var: `jsonSchema` body present | inline (strip `$schema`, rewrite) |
| per-var: `jsonSchema` body null / unparseable | property `{}` |
| per-var: `file` | `$ref` + definitions flag |
| per-var: `array` (4 item fallbacks) | array bullet |
| per-var: scalar / date / datetime / time / float / double | scalar bullet + type table |
| per-var: type not matched anywhere | bare `{type:<raw>}` passthrough |
| `getTypeAndFormatForType`: double/float, date, datetime, time, else | type table |
| `rewriteJobAttachmentRefs`: non-object, JobAttachment, existing `$ref`, recurse (skip `definitions`/`$defs`), no-match identity | `rewriteJobAttachmentRefs` subsection |
| `default` emitted iff `variable.default` truthy (verbatim) | scalar bullet |
| Out-arg `default`/`required`/`body` from companion | Out-arg field sourcing |

## Check 6 — Entry-point schema parity (Step 12 validator)

Non-HALT. For each entry in `entryPoints[]` (`triggerId` = `filePath` after `#`):

1. `input` == projectSchema(`inputs[]` where `elementId == triggerId`); `output` == projectSchema(Out-args). Compare keys, type/format mapping, `$ref` for `file`, inlined body for `jsonSchema`, `title`/`default` presence, the empty-set `{type,properties:{}}` (no `required`) shape, and `definitions` presence.
2. `required` == names of all vars with `required === true` (no type exclusion).
3. **Uniqueness guard** — `filePath` `#`-fragments unique across `entryPoints[]`. The trigger append is blind — a re-run duplicates an entry; the refresh propagates schemas to duplicates but cannot dedup (that is trigger-plugin identity).
4. **Orphan guard** — every `inputs[].elementId` matches some entry's trigger fragment (an orphaned In-arg projects into no entry and silently vanishes from the contract).

On a (1)/(2) mismatch → re-run the Procedure (deterministic recompute), re-check once. On a (3)/(4) finding or still-divergent (1)/(2) → log to `## Open Items for User` in `tasks/build-issues.md`, continue. Never HALT (build-with-best policy, [`implementation.md` § Step 12](implementation.md)).

## Worked example

`variables.inputs[]` (all `elementId: trigger_1`): `test_date` (datetime, default `"2029-10-12"`, `required:true`), `test_arrary` (jsonSchema, body `{"$schema":…,"type":"array","items":{"type":"string"}}`), `test_default` (float, default `"12.0"`), `test_date_time` (datetime, default `""`), `test_file` (file, `required:true`), `test_json` (jsonSchema, body `{"$schema":…,"type":"object","properties":{…},"required":[]}`, `required:true`). `variables.outputs[]`: `test_out` (double); its `inputOutputs[]` companion default `"1.3"`.

Entry `/content/caseplan.json.bpmn#trigger_1`:

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

Each entry's `input` carries only the In-args whose `elementId` is that trigger; **every** entry carries **all** Out-args. An In-arg bound to a trigger with no entry — e.g. one still pointing at a `preview-node-id` ghost node (an uncommitted canvas preview that leaked into `caseplan.json`) — matches no entry and is silently dropped from the contract; the `elementId` filter skips it (Check 6's orphan guard catches it).
