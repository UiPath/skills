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
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"status","operator":"=","value":"active"}]}}' \
  --output json
```

Pagination for query also uses `--limit` and `--cursor` flags — not body keys.

```bash
# Query with pagination
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"score","operator":">=","value":"80"}]}}' \
  --limit 100 \
  --cursor <NextCursor> \
  --output json
```

### Query Body Schema

```json
{
  "selectedFields": ["fieldA", "fieldB"],
  "filterGroup": {
    "logicalOperator": 0,
    "queryFilters": [
      { "fieldName": "score", "operator": ">=", "value": "80" }
    ],
    "filterGroups": []
  },
  "sortOptions": [
    { "fieldName": "score", "isDescending": true }
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
| `in` | All | `"value":"a,b,c"` |
| `not in` | All | |

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
          { "fieldName": "status", "operator": "=", "value": "active" },
          { "fieldName": "score", "operator": ">", "value": "50" }
        ]
      },
      {
        "logicalOperator": 0,
        "queryFilters": [
          { "fieldName": "priority", "operator": "=", "value": "high" }
        ]
      }
    ]
  }
}
```

## Insert Records

```bash
# Single record
uip df records insert <entity-id> --body '{"name":"Alice","score":95}' --output json

# Multiple records (array)
uip df records insert <entity-id> --body '[{"name":"Alice","score":95},{"name":"Bob","score":82}]' --output json

# From JSON file
uip df records insert <entity-id> --file records.json --output json
```

Single insert response: `{ Code: "RecordInserted", Data: { ...record } }`

Batch insert response: `{ Code: "RecordsBatchInserted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`

## Update Records

Records must include the `Id` field:

```bash
# Single record update
uip df records update <entity-id> --body '{"Id":"<record-id>","score":100}' --output json

# Batch update (array, each must include Id)
uip df records update <entity-id> \
  --body '[{"Id":"<id1>","score":100},{"Id":"<id2>","score":90}]' \
  --output json
```

Single update response: `{ Code: "RecordUpdated", Data: { ...record } }`

Batch update response: `{ Code: "RecordsBatchUpdated", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`

## Delete Records

```bash
uip df records delete <entity-id> <id1> <id2> <id3> --output json
```

Response: `{ Code: "RecordsDeleted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`
