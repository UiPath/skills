# Data model — making tables queryable (the add-table pattern)

The **data model** is the semantic layer of a process app. It is a JSON object with
`Processes`, `Metrics`, `Tables`, `Automations`, and `DefaultObject`. It is created
from the app template (`app-types get <key> <version>` returns it) and passed to
`apps create` as `model`. Everything `uip pm query` can see — every entity in
`query info`, every field, every metric — comes from this model.

## Why a bare dbt model is not queryable

`transformations create models/Workload_weekly.sql` builds a physical Snowflake
table, but `query info` will **not** list it and `query run` cannot group by it.
The transformation layer (dbt) and the semantic layer (the data model) are
separate: dbt produces tables; the data model decides which tables become
queryable **entities**. Registering a table in the model is exactly what the
**"Add table" button** in the data-model editor does.

> **Do not** work around this by overwriting the template `Tags.sql` /
> `Due_dates.sql` to smuggle your rows through their pre-registered entities. It
> "works" because those entities already exist in the model, but it corrupts the
> Tags/Due-dates features, fights their configured primary key, and misleads the
> next reader. Add a real table instead.

## The `Tables[]` entry shape

Each table in `model.Tables` maps a physical dbt table to a queryable entity:

```json
{
  "Id": "Workload_weekly",          // MUST equal the dbt model / physical table name
  "Display": "Workload weekly",
  "Fields": [
    { "Type": "column", "Name": "Service_Component", "Id": "Service_Component",
      "Display": "Service component", "Kind": "nominal",  "IsFilter": true },
    { "Type": "column", "Name": "Week", "Id": "Week",
      "Display": "Week", "Kind": "ordinal", "IsFilter": true },
    { "Type": "column", "Name": "Closed_Interactions", "Id": "Closed_Interactions",
      "Display": "Closed interactions", "Kind": "numeric", "IsFilter": true }
  ]
}
```

Field keys:

| Key | Meaning |
|-----|---------|
| `Type` | `column` for a plain column. |
| `Name` | The **column name in the dbt table** (case-sensitive, matches the SQL). |
| `Id` | The field id used in query bodies / references (unique within the model). |
| `Display` | Human label. |
| `Kind` | `nominal` (text dimension), `ordinal` (ordered dimension), or `numeric` (aggregatable measure — group-by metrics come from these). |
| `IsFilter` | Whether the field is offered as a filter/dimension. |
| `Reference` | (optional) the id of another table's key this column is a foreign key to — e.g. a child table referencing `Case_ID`. |

A child/related table (like `Tags`) carries a `Reference` field pointing at the
parent key; a standalone analytical table needs no `Reference`.

## Two ways to register the table

1. **At create time (simplest).** After `app-types get`, add your `Tables[]`
   entries to the model JSON, then create the app with that model. When your dbt
   models later produce those tables, they are queryable immediately. (If driving
   `apps create --data-mapping`, the CLI passes the template model as-is today —
   to inject custom tables you either edit the fetched model JSON and post it, or
   apply the data-model edit below after creation.)

2. **After creation (data-model edit).** The data-model editor persists table
   additions to the app's model; this is the "Add table" action. Use it to
   register a table you added to the transformation layer after the fact.

Either way the contract is the same: **`Tables[].Id` = the physical table name,
`Fields[].Name` = its columns.** Once registered, `query info` lists the entity
and `query run --group-by <col> --metric <col>:<fn>` works against it.

## Recipe: expose a custom weekly aggregate

```bash
# 1. Author the analytical model (or inline intermediates as CTEs)
uip pm transformations create <app> models/Workload_weekly.sql --file ./Workload_weekly.sql
# 2. Register it as a data-model table (add-table) — Tables[] entry as above
# 3. Rebuild + (re)publish, then query
uip pm transformations apply <app> --wait
uip pm query run <app> --group-by Service_Component --metric Closed_Interactions:sum --output table
```
