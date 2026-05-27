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

## Pagination

Offset-based under the hood. Available on both `records list` and `records query`:

- `-l, --limit <number>` — page size, default `50`, min `1`. Keep constant across a sweep (changing it re-slices the offset and can skip/duplicate records).
- `--cursor <NextCursor>` — opaque string from previous response. Pass verbatim; never hand-craft.
- `-o, --offset <number>` — non-negative record index. Rounded down to the nearest page boundary (`jumpToPage = floor(offset / limit) + 1`). **Mutually exclusive with `--cursor`** — passing both errors with *"--offset and --cursor are mutually exclusive"*.
- Stop when `HasNextPage: false`. `CurrentPage` / `TotalPages` are informational.

```bash
# Sequential sweep
uip df records list <entity-id> --limit 100 --output json
uip df records list <entity-id> --limit 100 --cursor "<NextCursor>" --output json

# Jump directly to the page containing record #250 (with --limit 100 → page 3)
uip df records list <entity-id> --limit 100 --offset 250 --output json
```

## Always Query the Server for Answers

Issue a fresh `records query` (or `records list`) — don't filter cached transcript data. Records mutate between turns, and the CLI call is the audit trail. Patterns: [filtered query](#filtered-query), [choice-set](#filtering-on-choice-set-fields), [relationship](#filtering-on-relationship-fields), [aggregates](#aggregates-server-side).

## Filtered Query

```bash
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json
```

Pagination for query uses the same `--limit` / `--cursor` / `--offset` flags (not body keys).

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

> Pagination is CLI-flag only: `--limit`, `--cursor`, `--offset`. Do not put `start`, `limit`, `offset`, or `pageSize` inside `--body` — the CLI translates these flags into the underlying offset-based API call.

> **Return all fields by default.** Omit `selectedFields` — the query then returns every field. Add `selectedFields` *only* when the user explicitly asks for a specific subset. Do not project to a subset on your own (e.g. to shorten output); the default is the full record.

### Operators

`=` `!=` `>` `<` `>=` `<=` `contains` `not contains` `startswith` `endswith` `in` `not in`, plus is-empty / is-not-empty (`=` / `!=` with `value: null`). `in` / `not in` take `valueList` (not `value`); `logicalOperator` is `0`/`1` or case-insensitive `AND`/`OR`.

Operator support varies by field type — see the authoritative [operator support matrix](filter-platform-contract.md#operator-support-by-field-type). When an operator isn't supported for a field's type, or a value is missing, do not silently run it — follow the unsupported-operator flow in **SKILL.md Rule 17**.

### Verifying a filter applied

Compare the response's `TotalCount` against an unfiltered baseline. If they match, the filter didn't narrow the result set — re-check the body against the contract.

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

### Filtering on Choice-Set Fields

Filter on the integer `NumberId` (as a string in `value` / `valueList`), never the display label. Resolve via `choice-sets get <choice-set-id>` first.

```bash
# CHOICE_SET_SINGLE — category == "travel" (NumberId 1)
uip df records query <entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"category","operator":"=","value":"1"}]}}' \
  --output json
```

**`CHOICE_SET_MULTIPLE`** is stored as a JSON-encoded integer array (e.g. `[1,3]`) and has special operator semantics:

| Operator | Value form | Meaning |
|----------|-----------|---------|
| `contains` / `not contains` | bare NumberId string (`"1"`) | Membership — the usual case |
| `=` / `!=` | JSON-array string (`"[1,3]"`) | Whole-set equality, order-insensitive |
| anything else | — | Not supported |

```bash
# Membership — records tagged with NumberId 1
uip df records query <entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"tags","operator":"contains","value":"1"}]}}' \
  --output json

# Set equality — tags == exactly {1,3}
uip df records query <entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"tags","operator":"=","value":"[1,3]"}]}}' \
  --output json
```

Failure modes: `=` with a bare value (`"1"`) → HTTP 400. `contains` with brackets (`"[1]"`) → HTTP 400. For per-value reporting, run `contains` per `NumberId`; for distribution of exact combinations, use `groupBy: ["tags"]` with `COUNT`.

### Filtering on Relationship Fields

Filter on the target record's UUID `Id`, regardless of `referenceFieldName`. If the user describes the parent by another field (email, name, etc.), resolve the UUID first on the parent entity, then filter the child.

```bash
# Direct
uip df records query <child-entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"customerId","operator":"=","value":"<parent-uuid>"}]}}' \
  --output json

# Resolve-first: email → Id on parent, then filter child
uip df records query <parent-entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Email","operator":"=","value":"alice@example.com"}]},"selectedFields":["Id"]}' \
  --output json
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

Response: `Data.Records` is a single row — `[{ "total": 250 }]`.

```bash
# Count per group (one result row per distinct value)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

Response: one row per group, each with the group fields + every aggregate alias — `[{ "Status": "Open", "total": 12 }, { "Status": "Closed", "total": 5 }]`.

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

> Needs `@uipath/data-fabric-tool` `1.0.1+`; older versions silently drop `aggregates`/`groupBy` and return a plain record list — `uip tools install @uipath/data-fabric-tool@latest`.

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

### Writing Choice-Set and Relationship Values

| Field type | Value | Resolve via |
|------------|-------|-------------|
| `CHOICE_SET_SINGLE` | Integer `NumberId` | `choice-sets get <choice-set-id>` |
| `CHOICE_SET_MULTIPLE` | Integer `NumberId` array | `choice-sets get <choice-set-id>` |
| `RELATIONSHIP` | Target record's UUID `Id` (always, even if `referenceFieldName` ≠ `Id`) | `records query <target-entity-id>` on the unique field |

```bash
uip df records insert <entity-id> \
  --body '{"amount":250,"category":1,"tags":[1,3],"customerId":"<target-uuid>"}' --output json
```

Display labels, choice-value UUIDs, and non-UUID relationship values are rejected — resolve first. Reads echo the same shape.

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

Choice / relationship fields use the same value form as insert — see [Writing Choice-Set and Relationship Values](#writing-choice-set-and-relationship-values).

Single update response: `{ Code: "RecordUpdated", Data: { ...updated record } }`

Batch update response: `{ Code: "RecordsBatchUpdated", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`

## Delete Records

```bash
uip df records delete <entity-id> <id1> <id2> <id3> --output json
```

Response: `{ Code: "RecordsDeleted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`
