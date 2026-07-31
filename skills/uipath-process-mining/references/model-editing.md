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
- **Data kinds:** `ordinal, nominal, numeric, datetime, boolean, percentage, currency, duration, ref, id`.
  Only `numeric/currency/duration/percentage/datetime/boolean/nominal/ordinal` are derivable from data;
  `duration`, `currency`, `percentage` are **user choices stored in the model `kind`** (a number column
  defaults to `numeric` — the user upgrades it).
- **Expressions** are JSON expression-node trees, the same shape the app model stores. A comparison:
  ```json
  {"type":"operator","operation":"lt",
   "left":  {"type":"reference","referenceType":"field","reference":"<field-id>"},
   "right": {"type":"constant","dataType":"duration","value":86400000}}
  ```
  Operators: `lt le gt ge eq ne and or add subtract multiply divide percentage`. Constant
  `dataType` **must match** the datakind of what it's compared to (see below). Reference a field
  with `{type:"reference","referenceType":"field","reference":"<field-id>"}`.

Every edit is **ETag-safe** and applies on `dev`. `fields set/remove`/`update` do a read-modify-write
under `If-Match`, returning the new edit `Versions`. After editing, `publish` to reach the dashboards,
and re-ingest if a data kind changed.

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

The `fields set` / `update` commands **run this validation** and refuse an edit that would create the
mismatch, surfacing a hint that names the conflicting comparison. So you cannot flip a field to
`duration` while a calculated field / metric compares it to a numeric constant — update or remove that
comparison first, or make the constant a `duration`.

## The data-kind footgun (DNA-46960)

A customer's app failed to open with exactly the error above. Root cause, from their exported app:
a metric **`% Tijdigheid`** was `PERCENTAGE( DOORLOOPTIJD[duration] lt 864000000[numeric] )` — a
throughput-time field (kind **duration**) compared to a **numeric** constant (10 days in ms). That
`lt(duration, numeric)` is evaluated when the query model is built at open, so it blocks every
dashboard (the data-upload module stays reachable — hence "I can only reach the data upload module").

How an app reaches this state even though the interactive edit validates:

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
