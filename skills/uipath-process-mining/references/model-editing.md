# Editing the Process Mining app model

There are **two** models behind a process app. Editing the wrong one is the most common source
of confusion, so be precise about which you mean.

| | `apps model` (semantic) | `apps data-model` (structural) |
| --- | --- | --- |
| Endpoint | `/apps/{id}/{stage}/model` | `/apps/{id}/{stage}/dataModel` |
| Contains | `data` → tables → **fields with their `kind`** (data kind), **calculated fields**, **metrics**; plus `view` → dashboards, charts, `metricFilters` | Tables with `primaryKey`/`foreignKeys` and the process-mining **role columns** (`activityColumn`, `endColumn`, …) |
| Think of it as | "the app definition" the user sees and edits | "the table plumbing" — which tables exist and how they join to `Cases` |
| Edited by | `fields set/remove`, `update`; the data manager & dashboard editor | `add-table`; the data-model editor |

`query info` shows the resolved *query* model (field ids, physical `ColumnDataType`, metrics) — useful
to discover the exact field ids to pass to `fields set` and `query`.

## Field editing surface

```bash
uip pm apps model fields list <app-id> [--stage dev|published]
uip pm apps model fields set  <app-id> <field-id> [--kind <k>] [--display-name <t>] [--expression <json|@file>] [--table <table-id>]
uip pm apps model fields remove <app-id> <field-id>
```

- **Upsert semantics.** If `<field-id>` exists, its `--kind` / `--display-name` are updated, and
  passing `--expression` turns it into (or updates) a **calculated field**. If it does not exist, a
  new **calculated field** is created in `--table` — so `--table` + `--expression` (+ `--kind`) are
  required to create. Mapped *column* fields can't be created through the model; they come from the
  ingested data.
- **Data kinds you can set (`--kind`):** `ordinal, nominal, numeric, datetime, boolean, percentage, currency, duration`
  — the union of the data manager's field-type options (FE `ColumnDataTypeFieldCompatibilityMap`).
  `duration`, `currency`, `percentage` are **user choices stored in the model `kind`** (a number column
  defaults to `numeric` — the user upgrades it). `id` and `ref` are **structural** (system-assigned to
  key/reference columns) and not settable, though `fields list` may report a field that already has them.
- **Expressions** are JSON expression-node trees, the same shape the app model stores. A comparison:
  ```json
  {"type":"operator","operation":"lt",
   "left":  {"type":"reference","referenceType":"field","reference":"<field-id>"},
   "right": {"type":"constant","dataType":"duration","value":86400000}}
  ```
  Operators: `lt le gt ge eq ne and or add subtract multiply divide percentage`. Constant
  `dataType` **must match** the data kind of what it's compared to (see below). Reference a field
  with `{type:"reference","referenceType":"field","reference":"<field-id>"}`.

Every edit is `If-Match`-guarded and applies on `dev`, returning the new edit `Versions` — but the two
routes differ in who supplies the ETag:

- **`fields set` / `fields remove` take no `--etag`.** They read the model and merge your change into
  exactly that version, so the read's own ETag is a real compare-and-swap. On a lost race, **just
  re-run** — they re-read and re-apply. (They refuse to write at all if the read came back without an
  ETag, rather than writing unguarded.)
- **`apps model update` REQUIRES `--etag`** — it replaces a document you edited locally, so it must
  carry the `Data.ETag` that `apps model get` returned. On 409/412, re-`get` for the latest model
  **and its new ETag**, re-apply your change on top, then update again with the new `--etag`.

```bash
uip pm apps model get <app> --destination model.json     # prints Data.ETag
uip pm apps model update <app> --file model.json --etag 'W/"3"'
```

Prefer `fields set` for a targeted change: no ETag to thread, and it can't clobber unrelated parts of
the model. After editing, `publish` to reach the dashboards, and re-ingest if a data kind changed.

## The data-kind rule

Relational/arithmetic operators require their operands to share a data kind (backend
`OperatorRelationalOrdering` / `CheckFunctionArguments`). So a comparison like `field < constant` is
only valid when the constant's `dataType` equals the field's `kind`. If they differ the model fails
validation with:

```
UserError_UnsupportedOperatorArgumentDataKind
{ argument:"right", operation:"lt", actual:"numeric", expected:"duration" }
→ "Must be duration, not numeric, for the 'lt' input."
```

The `fields set` / `update` commands **run this validation synchronously** and refuse an edit that
would create the mismatch, surfacing a hint that names the conflicting comparison. So via the CLI you
cannot flip a field to `duration` while a calculated field / metric compares it to a numeric constant —
update or remove that comparison first, or make the constant a `duration`. This synchronous check is
exactly what the **data-manager UI does not do** (it defers the kind change to the next re-ingestion —
the footgun below), so `fields set` is the *safe* way to change a kind. Caveat: the check covers
comparisons in the typed model `data` (calculated fields, metrics); a kind change that conflicts only
with an opaque dashboard **view** filter/chart is not caught, so publish and re-open to confirm.

## The data-kind footgun (DNA-46960)

A customer's app failed to open with exactly the error above. Root cause, from their exported app:
a metric **`% Tijdigheid`** was `PERCENTAGE( DOORLOOPTIJD[duration] lt 864000000[numeric] )` — a
throughput-time field (kind **duration**) compared to a **numeric** constant (10 days in ms). That
`lt(duration, numeric)` is evaluated when the query model is built at open, so it blocks every
dashboard (the data-upload module stays reachable — hence "I can only reach the data upload module").

How an app reaches this state via the **data-manager UI** (not the CLI, which validates synchronously):

1. Field is **numeric**; a metric/calculated field compares it to a numeric constant → valid.
2. The field's type is changed to **duration** in the *data manager*. This is applied in a
   **deferred** way — it is not written to the app model synchronously; it is baked in when the app
   model is regenerated at the **next re-ingestion**.
3. On re-ingest the field becomes `duration`, so the pre-existing comparison is now
   `lt(duration, numeric)` — and the ingestion-time regeneration does **not** re-run the edit
   validation, so the now-invalid model is persisted → the app won't open.

Takeaways when working with an app in this state:
- To reproduce/inspect: `apps model get` / `fields list` shows the field `kind` and the offending
  calculated field/metric; the mismatch is a comparison whose constant `dataType` ≠ the field `kind`.
- **Range filters do not trigger it** — filters on a field go through a coercing path, so a numeric
  range filter on a now-duration field still opens. Only real expressions (calculated fields, metrics)
  hit the operator data-kind check.
- The fix for a broken app is to make the comparison consistent: either revert the field to the kind
  the constant expects, or re-type the constant to match the field (e.g. a `duration` constant).
- Import (`.pmapp`) does not re-run this expression validation (exports are trusted), so importing a
  broken app reproduces the broken state; that is expected and not the bug.
