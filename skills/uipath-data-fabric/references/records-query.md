# Records Query Reference

## Basic List (All Records)

```bash
uip df records list <entity-id> --limit 50 --offset 0 --format json
```

Response: `{ TotalCount: N, Records: [...] }`

## Filtered Query

```bash
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"status","operator":"=","value":"active"}]}}' \
  --format json
```

### Query Request Schema

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
  ],
  "start": 0,
  "limit": 100
}
```

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

### Nested Groups

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
uip df records insert <entity-id> --body '{"name":"Alice","score":95}' --format json

# Multiple records (array)
uip df records insert <entity-id> --body '[{"name":"Alice","score":95},{"name":"Bob","score":82}]' --format json

# From JSON file
uip df records insert <entity-id> --file records.json --format json
```

## Update Records

Records must include the `Id` field:

```bash
uip df records update <entity-id> --body '{"Id":"<record-id>","score":100}' --format json
```

## Delete Records

```bash
uip df records delete <entity-id> <id1> <id2> <id3> --format json
```
