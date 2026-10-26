# Records Query Reference

## Basic List (All Records)

```bash
# First page
uip df records list <entity-id> --limit 50 --output json

# Next page — pass Data.NextCursor.Value from the previous response
uip df records list <entity-id> --limit 50 --cursor <cursor-value> --output json
```

Response wrapper: `{ Result, Code: "RecordList" | "RecordQuery", Data: { Items, TotalCount, HasNextPage, NextCursor, CurrentPage, TotalPages, SupportsPageJump } }`.
Records are in `Data.Items`, not `Data.Records`. `Data.NextCursor` is `{ "Value": "<base64-string>" }`; pass `Data.NextCursor.Value` to `--cursor`, never the wrapper. Check `Data.HasNextPage` and stop when it is `false`.

## MULTILINE_MAX Fields — Preview vs Full Content

`records list` and `records query` do not reliably return `MULTILINE_MAX` content. Each field is a preview, tenant-dependent:

- truncated to 10,000 characters with a `...[Truncated]` suffix (a value at or under 10,000 characters can come back whole), or
- a marker beginning `HasValue=true Length=N`, sometimes followed by a hint such as `"HasValue=true Length=20000 — call Get Entity Record By Id activity to retrieve content"`.

An encrypted `MULTILINE_MAX` field always reads `HasValue=true Encrypted=true` and never returns content. Treat every form as a preview; only a single-record read returns the full value:

```bash
uip df records get <entity-id> <record-id> --output json
```

1. **Never treat a preview as the value.** Don't display, compare, or persist what `list` / `query` returned for the field; fetch via `records get` first. A truncated preview is the more dangerous form because it looks like ordinary content.
2. **Never write a preview back.** A `records update` body built by echoing a record from `list` / `query` overwrites the real content with the preview — verified: the server accepts it as a normal value, `Result: Success`, content silently destroyed. With a truncated preview the stored value keeps its first 10,000 characters and loses the rest, which is far harder to notice than a marker string. Omit `MULTILINE_MAX` keys from update bodies unless intentionally replacing the content.
3. **No filter, no sort.** `queryFilters` / `sortOptions` naming a `MULTILINE_MAX` field → 400: *"Field '<name>' is of type MULTILINE_MAX and cannot be used in filters."* / *"Sort field '<name>' is of type MULTILINE_MAX and cannot be used for sorting."* Surface verbatim (data-fabric.md Rule 18); don't retry with other operators. Full type contract: [entity-schema.md → MULTILINE_MAX fields](entity-schema.md#multiline_max-fields).

## Pagination

Both `records list` and `records query` support:

- `-l, --limit <number>` — page size, default `50`, min `1`. Keep it constant across a sweep; changing it can skip or duplicate records.
- `--cursor <NextCursor.Value>` — pass the inner `Value` from `Data.NextCursor` verbatim; never hand-craft or pass the wrapper object.
- `-o, --offset <number>` — non-negative record index, rounded down to a page boundary (`jumpToPage = floor(offset / limit) + 1`). **Mutually exclusive with `--cursor`** — passing both errors with *"--offset and --cursor are mutually exclusive"*.

Stop when `HasNextPage: false`. `CurrentPage` / `TotalPages` / `SupportsPageJump` are informational.

## Folder scope (`--folder-key`)

`records list`, `records get`, `records insert`, `records update`, `records delete`, `records query`, and `records import` accept `--folder-key <GUID>`. Pass it for folder-scoped parent entities; get it from `entities list --include-folders --output json` (`FolderId` per row). Omit it for tenant-scoped entities.

```bash
uip df records list  <entity-id> --folder-key <folder-guid> --output json
uip df records query <entity-id> --folder-key <folder-guid> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json
```

## Always Query the Server for Answers

Issue a fresh `records query` (or `records list`), not a filter over cached transcript data: records mutate between turns and the CLI call is the audit trail. Patterns: [filtered query](#filtered-query), [choice-set](#filtering-on-choice-set-fields), [relationship](#filtering-on-relationship-fields), [aggregates](#aggregates-server-side).

## Filtered Query

```bash
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json
```

Pagination uses the `records list` `--limit` / `--cursor` / `--offset` flags, never body keys. The `filterGroup` shape, operators, response, and per-type support are in [`filter-platform-contract.md`](filter-platform-contract.md). The body also accepts:

- `"selectedFields": ["F1","F2"]` — projection; default is all fields (data-fabric.md Rule 17).
- `"sortOptions": [{ "fieldName": "Score", "isDescending": true }]` — server-side sort.

### Verifying a filter applied

Check that every returned record satisfies the predicate. Equal filtered and unfiltered counts are valid when every record matches.

### Nested Filter Groups

```json
{
  "filterGroup": {
    "logicalOperator": 1,
    "filterGroups": [
      { "logicalOperator": 0, "queryFilters": [
        { "fieldName": "Status", "operator": "=", "value": "active" },
        { "fieldName": "Score", "operator": ">", "value": "50" }
      ] },
      { "logicalOperator": 0, "queryFilters": [
        { "fieldName": "Priority", "operator": "=", "value": "high" }
      ] }
    ]
  }
}
```

### Filtering on Choice-Set Fields

Filter on integer `NumberId` (as a string in `value` / `valueList`), never the display label. Resolve it first with `choice-sets list-values <choice-set-id>`.

```bash
# CHOICE_SET_SINGLE — category == "travel" (NumberId 1)
uip df records query <entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"category","operator":"=","value":"1"}]}}' \
  --output json
```

`CHOICE_SET_MULTIPLE` has special `=` vs `contains` semantics; see the [filter contract](filter-platform-contract.md#operator-support-by-field-type) Complex-field values line.

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

`=` with a bare value (`"1"`) → HTTP 400; `contains` with brackets (`"[1]"`) → HTTP 400. For per-value reporting, run `contains` per `NumberId`; for exact-combination distribution, use `groupBy: ["tags"]` with `COUNT`.

### Filtering on Relationship Fields

Filter on the target record UUID `Id`, regardless of the bound `referenceFieldId` (which controls the join, not the stored value). If the user gives another parent field, resolve its UUID on the parent entity first.

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

Add `aggregates` and optional `groupBy` to return aggregated rows instead of records. Each aggregate produces a column keyed by `alias`. Field names are case-sensitive; use exact schema casing from `uip df entities get <entity-id>`.

```bash
# Total count of records (no grouping → single result row)
uip df records query <entity-id> \
  --body '{"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

`Data.Items` is one row, e.g. `[{ "Total": 250 }]`. The server PascalCases aliases (`"total"` → `"Total"`); parse the PascalCase key.

```bash
# Count per group (one result row per distinct value)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

Grouped `Data.Items` has one row per group with group fields and PascalCased aggregate aliases, e.g. `[{ "Status": "Open", "Total": 12 }, { "Status": "Closed", "Total": 5 }]`.

### Functions

| `function` | Applies to | Notes |
|------------|-----------|-------|
| `COUNT` | Any field | Counts non-null values. For total row count use `field: "Id"` |
| `SUM` | Numeric only | |
| `AVG` | Numeric only | |
| `MIN` | Numeric / date | |
| `MAX` | Numeric / date | |

Values are uppercase strings: `"COUNT"`, not `"Count"`.

### Aggregate Body Schema

```json
{
  "selectedFields": ["Status"],
  "groupBy": ["Status"],
  "aggregates": [
    { "function": "COUNT", "field": "Id", "alias": "total" },
    { "function": "AVG", "field": "amount", "alias": "avgAmount" }
  ]
}
```

- `aggregates[].alias` is optional; without it the key is `{FUNCTION}_{field}` (for example `COUNT_Id`, `AVG_amount`). Supply an alias for stable readable keys.
- With `selectedFields`, every entry must also be in `groupBy`, or the API rejects the request; the shortcut is using the same array for both.
- `groupBy` and `selectedFields` may reference root-entity fields only; expansions are unsupported.
- The same `filterGroup`, `sortOptions`, `--limit`, and `--cursor` work with aggregates. Filters run before grouping (SQL `WHERE`).
- `groupBy` names the choice-set field; group keys and filter values use numeric `NumberId`, not display labels.

## Insert Records

A JSON object or 1-element array routes to the single-record endpoint; an array with 2+ elements routes to batch. One call accepts at most 1,000 records; larger arrays fail whole (`"Number of items provided 1500 exceeds limit 1000"`) and insert nothing, so chunk larger loads into batches of up to 1,000.

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

Single response: `{ Code: "RecordInserted", Data: { ...record with Id } }`.
Batch response: `{ Code: "RecordsBatchInserted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`.

An insert never matches stored rows: rerunning seeding inserts every row unless an `isUnique` field rejects repeats into `FailureRecords`. Before seeding, count stored records with the [aggregate `COUNT`](#aggregates-server-side); `TotalCount` briefly counts rejected inserts too. If non-zero, tell the user and ask before inserting.

### Writing Choice-Set and Relationship Values

| Field type | Value | Resolve via |
|------------|-------|-------------|
| `CHOICE_SET_SINGLE` | Integer `NumberId` | `choice-sets list-values <choice-set-id>` |
| `CHOICE_SET_MULTIPLE` | Integer `NumberId` array | `choice-sets list-values <choice-set-id>` |
| `RELATIONSHIP` | Target record UUID `Id` always; `referenceFieldId` controls the join, not stored value | `records query <target-entity-id>` on the unique field |
| `FILE` | **Not writable through `records insert` / `records update`** — see below | `files upload` |

```bash
uip df records insert <entity-id> \
  --body '{"amount":250,"category":1,"tags":[1,3],"customerId":"<target-uuid>"}' --output json
```

Display labels, choice-value UUIDs, and non-UUID relationship values are rejected; resolve first. Reads echo the same shape.

### FILE fields

Never include a FILE key in record insert/update/import payloads; the platform silently drops it. Insert the row without it, then use `files upload`. See data-fabric.md Rule 6 and [`file-attachments.md`](file-attachments.md).

## Update Records

A JSON object or 1-element array routes to single-record update; an array with 2+ elements routes to batch. Both require `Id` in the body.

```bash
# Single record — JSON object with Id
uip df records update <entity-id> --body '{"Id":"<record-id>","Score":100}' --output json

# Batch update — JSON array, each element must include Id
uip df records update <entity-id> \
  --body '[{"Id":"<id1>","Score":100},{"Id":"<id2>","Score":90}]' \
  --output json
```

Choice and relationship fields use the same forms as insert: see [Writing Choice-Set and Relationship Values](#writing-choice-set-and-relationship-values).

Single response: `{ Code: "RecordUpdated", Data: { ...updated record } }`.
Batch response: `{ Code: "RecordsBatchUpdated", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords } }`.

## Delete Records

Deletion is irreversible; `--yes` and `--reason` are required (server-gated, like `entities delete` / `choice-sets delete`). Pass each ID as a separate positional argument, not a space-joined quoted string; otherwise the CLI parses one invalid GUID and errors with *"Error converting value '… …' to type 'System.Guid'"*.

```bash
uip df records delete <entity-id> <id1> <id2> <id3> \
  [--folder-key <…>] \
  --yes --reason "<why>" \
  --output json
```

Response: `{ Code: "RecordsDeleted", Data: { SuccessCount, FailureCount, SuccessRecords, FailureRecords, Reason } }`; `Reason` echoes `--reason` for audit logging.