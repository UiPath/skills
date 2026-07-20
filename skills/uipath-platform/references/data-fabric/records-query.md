# Records Query Reference

CLI syntax, response wrappers, pagination flags, and the `Data.Items` / `NextCursor.Value` unwrap footgun all live in [Data Fabric CLI docs → `records`](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#records--response-shapes-and-footguns). This file only covers the agent-side patterns.

## MULTILINE_MAX Fields — Marker vs Full Content

`records list` and `records query` do NOT return `MULTILINE_MAX` content. Each such field comes back as a size marker string starting `HasValue=true Length=N` — live form: `"HasValue=true Length=20000 — call Get Entity Record By Id activity to retrieve content"`. Only single-record read returns the full content via `records get`.

1. **Never treat the marker as the value.** Don't display, compare, or persist `"HasValue=true Length=N"` as field content — fetch via `records get` first.
2. **Never write the marker back.** A `records update` body built by echoing a record from `list` / `query` overwrites the real content with the literal marker string — verified: the server accepts it as a normal value, `Result: Success`, content silently destroyed. Omit `MULTILINE_MAX` keys from update bodies unless intentionally replacing the content.
3. **No filter, no sort.** `queryFilters` / `sortOptions` naming a `MULTILINE_MAX` field → 400. Surface verbatim (data-fabric.md Rule 18); don't retry with other operators.

## Always Query the Server for Answers

Issue a fresh `records query` (or `records list`) — don't filter cached transcript data. Records mutate between turns, and the CLI call is the audit trail. Patterns: [filtered query](#filtered-query), [choice-set](#filtering-on-choice-set-fields), [relationship](#filtering-on-relationship-fields), [aggregates](#aggregates-server-side).

## Filtered Query

```bash
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json
```

Pagination uses the same `--limit` / `--cursor` / `--offset` flags as `records list` — never body keys.

The `filterGroup` shape, operators, response, and per-type support are in [`filter-platform-contract.md`](filter-platform-contract.md). Beyond the filter, the query body accepts:

- `"selectedFields": ["F1","F2"]` — projection. Default is all fields (data-fabric.md Rule 16).
- `"sortOptions": [{ "fieldName": "Score", "isDescending": true }]` — server-side sort.

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

Filter on the integer `NumberId` (as a string in `value` / `valueList`), never the display label. Resolve via `choice-sets list-values <choice-set-id>` first.

```bash
# CHOICE_SET_SINGLE — category == "travel" (NumberId 1)
uip df records query <entity-id> --body \
  '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"category","operator":"=","value":"1"}]}}' \
  --output json
```

**`CHOICE_SET_MULTIPLE`** has special `=` vs `contains` semantics — see the [filter contract](filter-platform-contract.md#operator-support-by-field-type) Complex-field values line. Practical examples:

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

Filter on the target record's UUID `Id`, regardless of which field was bound as `referenceFieldId` (that controls the join, not the stored value). If the user describes the parent by another field (email, name, etc.), resolve the UUID first on the parent entity, then filter the child.

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

Response: `Data.Items` is a one-row array — e.g. `[{ "Total": 250 }]`. The server **PascalCases your alias** in the response (`alias: "total"` → key `"Total"`). Read by the PascalCase key when parsing.

```bash
# Count per group (one result row per distinct value)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

Response: `Data.Items` — one row per group, each with the group fields + every aggregate alias (PascalCased) — e.g. `[{ "Status": "Open", "Total": 12 }, { "Status": "Closed", "Total": 5 }]`.

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

## Writing Record Values

Insert / update command syntax and response shapes: [CLI docs → `records`](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#records--response-shapes-and-footguns). Everything below is agent-critical value-form knowledge the CLI can't teach without the schema.

### Writing Choice-Set and Relationship Values

| Field type | Value | Resolve via |
|------------|-------|-------------|
| `CHOICE_SET_SINGLE` | Integer `NumberId` | `choice-sets list-values <choice-set-id>` |
| `CHOICE_SET_MULTIPLE` | Integer `NumberId` array | `choice-sets list-values <choice-set-id>` |
| `RELATIONSHIP` | Target record's UUID `Id` (always — the binding `referenceFieldId` controls the join, not the stored value) | `records query <target-entity-id>` on the unique field |
| `FILE` | **Not writable through `records insert` / `records update`** — see below | `files upload` |

```bash
uip df records insert <entity-id> \
  --body '{"amount":250,"category":1,"tags":[1,3],"customerId":"<target-uuid>"}' --output json
```

Display labels, choice-value UUIDs, and non-UUID relationship values are rejected — resolve first. Reads echo the same shape.

### FILE fields — never write through insert/update

CLI rejects FILE keys in `records insert` / `update` bodies from `@uipath/data-fabric-tool` `1.199.0+` (Rule 6). Write path: `records insert` without the FILE column, capture `Data.Id`, then `uip df files upload <entity-id> <record-id> <field-name> --file <path>`. `files upload` both attaches and replaces; `files delete` clears; `files download` retrieves. CSV `records import` still drops FILE columns silently — see Rule 20.

**FILE-field read shape depends on `expansionLevel`** — `records get` and `records list` are always level `0`; `records query` accepts `expansionLevel` inside `--body` (default `0`):

- Level `0` — FILE field is a bare UUID string, or omitted / `null` when unattached: `{ "Document": "16633BC7-F76A-F111-AC99-000D3A98AF8F" }`
- Level `1+` — object with `Id`, `Name`, `Size`, `Type`, `Path`, `UpdateTime`, etc. To read filename via CLI: query with `expansionLevel: 1` and read `Data.Items[].<field-name>.Name`.

The per-record-per-field UUID handle is preserved across `files upload` — the bytes change, the UUID does not. Don't use the handle to detect content change; compare bytes or watch `UpdateTime`.

## Update / Delete Records

Command syntax, response shapes, `Id` requirement, and the positional-varargs footgun on `records delete`: [CLI docs → `records`](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#records--response-shapes-and-footguns). Choice / relationship values use the same forms as insert (above). Gating (`--yes` + `--reason` on `delete`) is enforced by the CLI; the agent-side ask lives in data-fabric.md Rule 0.
