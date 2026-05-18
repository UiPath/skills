# Records Query Reference

## Basic List (All Records)

```bash
# First page
uip df records list <entity-id> --limit 50 --output json

# Next page — pass NextCursor value from previous response
uip df records list <entity-id> --limit 50 --cursor <NextCursor> --output json
```

Response: `{ TotalCount, Records, HasNextPage, NextCursor?, CurrentPage?, TotalPages? }`

- Use `HasNextPage` to check if more records exist
- Pass the `NextCursor` string value to `--cursor` to fetch the next page

## Filtered Query

```bash
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json
```

Pagination for query also uses `--limit` and `--cursor` flags — not body keys.

```bash
# Query with pagination
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Score","operator":">=","value":"80"}]}}' \
  --limit 100 \
  --cursor <NextCursor> \
  --output json
```

### Query Body Schema

```json
{
  "selectedFields": ["FieldA", "FieldB"],
  "filterGroup": {
    "logicalOperator": 0,
    "queryFilters": [
      { "fieldName": "Score", "operator": ">=", "value": "80" }
    ],
    "filterGroups": []
  },
  "sortOptions": [
    { "fieldName": "Score", "isDescending": true }
  ]
}
```

> `start` and `limit` are **not** valid body keys — use `--limit` and `--cursor` CLI flags instead.

### Operators

| Operator | Applies to | Example |
|----------|-----------|---------|
| `=` | All types | `"value":"active"` |
| `!=` | All types | Null check when value is empty |
| `>`, `<`, `>=`, `<=` | Numbers, dates | `"value":"2024-01-01"` |
| `contains` | Text | `"value":"part"` |
| `not contains` | Text | |
| `startswith` | Text | |
| `endswith` | Text | |
| `in` | All | `"valueList":["a","b","c"]` |
| `not in` | All | `"valueList":["x","y"]` |

> `in` and `not in` use `valueList` (string array), **not** `value`. Using `value` for these operators will be ignored.

### logicalOperator

- `0` = AND (all filters must match)
- `1` = OR (any filter must match)

### Nested Filter Groups

```json
{
  "filterGroup": {
    "logicalOperator": 1,
    "filterGroups": [
      {
        "logicalOperator": 0,
        "queryFilters": [
          { "fieldName": "Status", "operator": "=", "value": "active" },
          { "fieldName": "Score", "operator": ">", "value": "50" }
        ]
      },
      {
        "logicalOperator": 0,
        "queryFilters": [
          { "fieldName": "Priority", "operator": "=", "value": "high" }
        ]
      }
    ]
  }
}
```

## Aggregates (server-side)

Add `aggregates` and optional `groupBy` to the query body to return aggregated rows instead of records. Each entry in `aggregates` produces one column on each result row, keyed by `alias`.

> **Field names are case-sensitive.** Examples below use `Status` as a placeholder — substitute the exact casing from the target entity's schema (`uip df entities get <entity-id>` lists the real names).

```bash
# Total count of records (no grouping → single result row)
uip df records query <entity-id> \
  --body '{"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

Response:

```json
{
  "Result": "Success",
  "Code": "RecordQuery",
  "Data": {
    "TotalCount": 1,
    "Records": [{ "total": 250 }],
    "HasNextPage": false
  }
}
```

```bash
# Count per group (one result row per distinct value)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

Response shape (one row per group, each row contains the group fields + every aggregate alias):

```json
{
  "Result": "Success",
  "Code": "RecordQuery",
  "Data": {
    "TotalCount": 2,
    "Records": [
      { "Status": "Open",   "total": 12 },
      { "Status": "Closed", "total":  5 }
    ],
    "HasNextPage": false
  }
}
```

### Functions

| `function` | Applies to | Notes |
|------------|-----------|-------|
| `COUNT` | Any field | Counts non-null values. For total row count use `field: "Id"` |
| `SUM`   | Numeric only | |
| `AVG`   | Numeric only | |
| `MIN`   | Numeric / date | |
| `MAX`   | Numeric / date | |

Values are the **uppercase strings** above — `"COUNT"` not `"Count"`.

### Aggregate Body Schema

```json
{
  "selectedFields": ["Status"],
  "groupBy": ["Status"],
  "aggregates": [
    { "function": "COUNT", "field": "Id",     "alias": "total" },
    { "function": "AVG",   "field": "amount", "alias": "avgAmount" }
  ]
}
```

- `aggregates[].alias` is optional. When omitted, the server returns the column keyed as `{FUNCTION}_{field}` (for example `COUNT_Id`, `AVG_amount`). Provide an `alias` for stable, readable keys in your downstream code.
- When `selectedFields` is present alongside `aggregates`, every entry in `selectedFields` must also appear in `groupBy` — otherwise the API rejects the request. The shortcut: use the same array for both, as in the examples above.
- `groupBy` and `selectedFields` may reference root-entity fields only — expansions are not supported in aggregate mode.
- The same `filterGroup`, `sortOptions`, and pagination flags (`--limit`, `--cursor`) work alongside aggregates. Filters are applied **before** grouping (SQL `WHERE`).
- Choice-set fields in `groupBy` / filters require the numeric `numberId`, not the display label. Discover via the choice-set lookup if you need to filter / group by a choice value.

> Tooling requirement: server-side aggregates ship in version `1.0.1`+ of `@uipath/data-fabric-tool` only. Older versions silently strip `aggregates` / `groupBy` from the body (the SDK they bundle prefixes unknown keys with OData `$`, which the API ignores) and the query falls back to a plain record list. If aggregates aren't returning the expected one-row-per-group shape, re-run `uip tools install @uipath/data-fabric-tool@latest` to pick up the latest.

## Insert Records

The CLI routes by body shape: a JSON object (or 1-element array) calls the single-record endpoint; a JSON array with 2+ elements calls the batch endpoint.

```bash
# Single record — JSON object
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json

# Batch insert — JSON array with 2+ records
uip df records insert <entity-id> \
  --body '[{"Name":"Alice","Score":95},{"Name":"Bob","Score":82}]' \
  --output json

# From JSON file
uip df records insert <entity-id> --file records.json --output json
```

Single insert response: `{ Code: "RecordInserted", Data: { ...record with Id } }`

Batch insert response: `{ Code: "RecordsBatchInserted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`

## Update Records

The CLI routes by body shape: a JSON object (or 1-element array) calls the single-record endpoint; a JSON array with 2+ elements calls the batch endpoint. Both require `Id` in the body.

```bash
# Single record — JSON object with Id
uip df records update <entity-id> --body '{"Id":"<record-id>","Score":100}' --output json

# Batch update — JSON array, each element must include Id
uip df records update <entity-id> \
  --body '[{"Id":"<id1>","Score":100},{"Id":"<id2>","Score":90}]' \
  --output json
```

Single update response: `{ Code: "RecordUpdated", Data: { ...updated record } }`

Batch update response: `{ Code: "RecordsBatchUpdated", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`

## Delete Records

```bash
uip df records delete <entity-id> <id1> <id2> <id3> --output json
```

Response: `{ Code: "RecordsDeleted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`
