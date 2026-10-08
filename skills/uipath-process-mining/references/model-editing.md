# Editing the Process Mining app model

Distinguish the two models before editing:

| | `apps model` (semantic) | `apps data-model` (structural) |
| --- | --- | --- |
| Endpoint | `/apps/{id}/{stage}/model` | `/apps/{id}/{stage}/dataModel` |
| Contains | `data` → tables, fields with data `kind`, calculated fields, metrics; `view` → dashboards, charts, `metricFilters` | Tables with `primaryKey`/`foreignKeys` and process-mining role columns (`activityColumn`, `endColumn`, …) |
| Purpose | User-visible app definition | Table plumbing and joins to `Cases` |
| Edited by | `fields set/remove`, `update`, data manager, dashboard editor | `add-table`, data-model editor |

`query info` shows the resolved query model (field ids, physical `ColumnDataType`, metrics); use it to find field ids for `fields set` and `query`.

## Field editing surface

```bash
uip pm apps model fields list <app-id> [--stage dev|published]
uip pm apps model fields set  <app-id> <field-id> [--kind <k>] [--display-name <t>] [--expression <json|@file>] [--table <table-id>]
uip pm apps model fields remove <app-id> <field-id>
```

- **Upsert:** Existing fields update `--kind`/`--display-name`; `--expression` creates or updates a calculated field. Creating one requires `--table` + `--expression` (+ `--kind`). Mapped column fields come from ingested data and cannot be created here.
- **Settable `--kind` values:** `ordinal, nominal, numeric, datetime, boolean, percentage, currency, duration` (the data manager's `ColumnDataTypeFieldCompatibilityMap` options). `duration`, `currency`, and `percentage` are user choices stored in model `kind`; number columns default to `numeric`. `id` and `ref` are system-assigned structural kinds for key/reference columns, not settable, though `fields list` may report them.
- **Expressions:** Use JSON expression-node trees matching the app model. Example comparison:
  ```json
  {"type":"operator","operation":"lt","left":{"type":"reference","referenceType":"field","reference":"<field-id>"},"right":{"type":"constant","dataType":"duration","value":86400000}}
  ```
  Operators: `lt le gt ge eq ne and or add subtract multiply divide percentage`. A constant's `dataType` must match the compared field's data kind. Reference fields use `{type:"reference","referenceType":"field","reference":"<field-id>"}`.

Every edit applies to `dev`, is `If-Match`-guarded, and returns new edit `Versions`. ETag handling:

- `fields set` / `fields remove` take no `--etag`: they read and merge into that exact version, using the read's ETag as compare-and-swap. If a race is lost, re-run; the command re-reads and reapplies. It refuses to write if the read has no ETag.
- `apps model update` **requires `--etag`** because it replaces a locally edited document. Pass the `Data.ETag` from `apps model get`. On 409/412, re-`get` the latest model and ETag, re-apply your change, then update with the new `--etag`.

```bash
uip pm apps model get <app> --destination model.json     # prints Data.ETag
uip pm apps model update <app> --file model.json --etag 'W/"3"'
```

Prefer `fields set` for targeted edits: it needs no ETag threading and cannot clobber unrelated model parts. After editing, publish to reach dashboards; re-ingest if a data kind changed.

## The data-kind rule

Relational/arithmetic operators require operands of the same data kind (`OperatorRelationalOrdering` / `CheckFunctionArguments`). A comparison such as `field < constant` is valid only if the constant's `dataType` equals the field's `kind`; otherwise validation returns:

```
UserError_UnsupportedOperatorArgumentDataKind
{ argument:"right", operation:"lt", actual:"numeric", expected:"duration" }
→ "Must be duration, not numeric, for the 'lt' input."
```

`fields set` / `update` validate synchronously and reject mismatches with a hint naming the conflicting comparison. You cannot change a field to `duration` while a calculated field or metric compares it to a numeric constant: first update/remove the comparison or make its constant `duration`. Unlike the data-manager UI, `fields set` is safe for kind changes. Validation covers comparisons in typed model `data` (calculated fields, metrics), not opaque dashboard `view` filters/charts; publish and re-open to confirm those.

## The data-kind footgun

An app can fail to open when a metric compares a duration field with a numeric constant, e.g. `% Tijdigheid`: `PERCENTAGE( DOORLOOPTIJD[duration] lt 864000000[numeric] )` (10 days in ms). Query-model construction evaluates `lt(duration, numeric)` at open, blocking every dashboard while the data-upload module remains reachable.

The data-manager UI (unlike the synchronously validating CLI) can create this state:

1. A numeric field is compared with a numeric constant in a metric/calculated field; this is valid.
2. The data manager changes the field to `duration` deferred: the app model is not updated synchronously; the change is baked in when the model is regenerated at the next re-ingestion.
3. Re-ingestion makes the field `duration`, leaving `lt(duration, numeric)`. Regeneration does not rerun edit validation, so the invalid model persists and the app will not open.

For a broken app:
- Inspect `apps model get` / `fields list` for the field `kind` and offending calculated field/metric; the mismatch is a comparison whose constant `dataType` differs from the field `kind`.
- Range filters do not trigger this: field filters use a coercing path, so a numeric range filter on a now-duration field still opens. Only real expressions (calculated fields, metrics) hit the operator data-kind check.
- Make the comparison consistent: revert the field kind to what the constant expects, or re-type the constant to match the field (for example, use a `duration` constant).
- Import (`.pmapp`) does not rerun expression validation; exports are trusted, so importing a broken app reproduces the broken state as expected.