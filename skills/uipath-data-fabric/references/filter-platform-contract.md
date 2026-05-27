# Filter Platform Contract

Authoritative reference for `records query` filter behavior, sourced from the Data Fabric server (`CommonEntityPlatform`). Use this when you need to verify how a filter will execute, what operators are valid for a given field type, or why a particular filter shape was rejected.

For the common-case body shape, see [`records-query.md` → Filter Body Reference](records-query.md#filter-body-reference). This file covers the platform contract in full — type matrix, special rules, limits, validation order.

---

## 1. Filter request shape

Filters are sent as a `QueryFilterGroup` tree. Each node:

```json
{
  "logicalOperator": "AND",
  "queryFilters": [
    { "fieldName": "Name",   "operator": "contains", "value": "abc" },
    { "fieldName": "Age",    "operator": ">=",       "value": "18" },
    { "fieldName": "Status", "operator": "in",       "valueList": ["A", "B"] }
  ],
  "filterGroups": [ /* nested groups, recursive */ ]
}
```

- `fieldName` is required and must match the name regex (`_regexFilterAndSortFieldName`).
- Dotted names like `Customer.Email` are allowed for filtering across `$expand` joins (see §5.8).
- `operator` is required.
- `value` is a single scalar, sent as a JSON **string** regardless of the field's type — e.g. `"18"` for an `INT` field, `"true"` / `"0"` / `"1"` for `BIT`, an ISO-8601 string for dates. The server parses it to the target field's type (§3, §4). The `in` / `not in` operators take `valueList` instead — value form per operator is in §2.
- `null` value is only legal with `=` (→ `IS NULL`) or `!=` (→ `IS NOT NULL`).
- Total filter count is capped by `EnvironmentConstraintOptions.MaxQueryFilterCount` (per-tenant).
- Groups can nest arbitrarily; `AND`/`OR` can mix at each level.

---

## 2. Operators — SQL translation

| Operator | SQL emitted | Value form | Notes |
|---|---|---|---|
| `=` | `=` (or `IS NULL` when value is null) | scalar | |
| `!=` | `!=` (or `IS NOT NULL` when value is null) | scalar | |
| `>` | `>` | scalar | |
| `<` | `<` | scalar | |
| `>=` | `>=` | scalar | |
| `<=` | `<=` | scalar | |
| `in` | `IN (@p0, @p1, …)` | `valueList` | Empty list → 400 |
| `not in` | `NOT IN (@p0, @p1, …)` | `valueList` | Empty list → 400 |
| `contains` | `LIKE` | scalar | Caller is responsible for `%` wrap |
| `not contains` | `NOT LIKE` | scalar | |
| `startswith` | `LIKE` | scalar | Caller wraps with trailing `%` |
| `endswith` | `LIKE` | scalar | Caller wraps with leading `%` |

Anything else → `BadRequestException("Unexpected operator …")`.

**SQL safety:** every value is bound as a SQL parameter (`@p0`, `@p1`, …). Column names come from the entity schema metadata only — never from the raw `fieldName` string. Tenant isolation is enforced by an automatic `WHERE TenantId = …` injected outside the user's filter.

---

## 3. Field types (SQL backing)

| Name | SQL backing | Notes |
|---|---|---|
| `NVARCHAR` | `nvarchar(N)` | Text, max length configurable 1–4000 |
| `MULTILINE` | `nvarchar(max)` | Long text, length-limited 1–10000 |
| `MULTILINE_MAX` | `nvarchar(max)` | Very long text, 1–128 KB byte budget. FF-gated. **Not filterable** (§5.4). |
| `INT` | `int` | 32-bit integer |
| `BIGINT` | `bigint` | 64-bit integer |
| `DECIMAL` | `decimal(28,n)` | High-precision decimal |
| `FLOAT` | `float(53)` | 64-bit IEEE 754 |
| `REAL` | `float(24)` | 32-bit IEEE 754 (legacy) |
| `BIT` | `bit` | Boolean |
| `DATETIME2` | `datetime2` | Wall-clock datetime, no offset |
| `DATETIMEOFFSET` | `datetimeoffset` | Datetime with timezone offset |
| `DATE` | `date` | Date only |
| `UNIQUEIDENTIFIER` | `uniqueidentifier` | GUID |

Higher-level display types ride on these SQL types:

- **Relationship** → `UNIQUEIDENTIFIER` FK
- **ChoiceSetSingle** → `INT`
- **ChoiceSetMultiple** → `NVARCHAR` storing a sorted JSON array (§5.5)
- **File** → `NVARCHAR` with blob path

---

## 4. Operator support by field type

This is the **supported filter contract** — build filters only within it. ✅ = supported, ❌ = not supported. The raw API executes several ❌ combinations anyway (§4.1); treat anything outside this matrix as unsupported and follow the decision flow in SKILL.md Rule 17.

### Operators

| Operator | Symbol | Meaning |
|---|---|---|
| Equals | `=` | Exact match |
| Does not equal | `!=` | Negated exact match |
| Contains | `contains` | Substring match (`LIKE %val%`) |
| Not contains | `not contains` | Negated substring match |
| Starts with | `startswith` | Prefix match (`LIKE val%`) |
| Ends with | `endswith` | Suffix match (`LIKE %val`) |
| Is more than | `>` | Greater than |
| Is less than | `<` | Less than |
| Is not more than | `<=` | Less than or equal |
| Is not less than | `>=` | Greater than or equal |
| Is empty | `=` + `value: null` | Null / no value |
| Is not empty | `!=` + `value: null` | Has a value |
| Is in | `in` | Matches any value in `valueList` |
| Is not in | `not in` | Matches none of the values in `valueList` |

### Support matrix

| Operator | Text / Multiline | Number / Autonumber | Date / DateTime | Boolean | Choice Set (single/multi) | Relationship | File | Unique ID |
|---|---|---|---|---|---|---|---|---|
| Equals (`=`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Does not equal (`!=`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Contains | ✅¹ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Not contains | ✅¹ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Starts with | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Ends with | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Is more than (`>`) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Is less than (`<`) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Is not more than (`<=`) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Is not less than (`>=`) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Is empty (`=` null) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Is not empty (`!=` null) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Is in (`in`) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| Is not in (`not in`) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |

**Notes** (the matrix is canonical; these add only what it can't show)

- ¹ **Encrypted text** drops the `LIKE` operators — only `=`, `!=`, `in`, `not in`, empty (§5.2).
- **Choice Set**: filter on the integer `NumberId`; `CHOICE_SET_MULTIPLE` `=` vs `contains` semantics — §5.5.
- **Relationship**: filter by the target record's UUID `Id` — see [records-query.md](records-query.md#filtering-on-relationship-fields).
- **`MULTILINE_MAX`** (very long text) is non-filterable by any operator (§5.4).

### 4.1 The raw API is more permissive than this matrix

The matrix is the **supported** contract. The underlying `uip df records query` API will still *execute* several ❌ combinations — verified live: `<` / `>` on Text (lexicographic, collation-ordered), `<` on Boolean, and `in` on a Choice Set all return `Result: Success`, not a 400.

Do not rely on that. Outside the matrix the result is unsupported and frequently wrong — e.g. Text `<` orders lexicographically under `SQL_Latin1_General_CP1_CI_AS` (so `"user2@…" < "user20@…"`). Don't silently run out-of-matrix combinations — follow SKILL.md Rule 17. Unknown operators (`==`, `Equals`, `like`) are rejected outright → 400 (§2, §6).

---

## 5. Special rules and edge cases

### 5.1 Null filtering

`value: null` is only legal with `=` or `!=`. They translate to `IS NULL` / `IS NOT NULL`. Any other operator with null value → **400**.

### 5.2 Encrypted fields

Fields with `IsEncrypted = true` (column-level encryption via KMS):

- Allowed operators: **only `=`, `!=`, `in`, `not in`**. All others → `BadRequestException`.
- Filter value is hashed (SHA-256) before SQL parameterization; the filter target is rewritten from `FieldName` to `FieldName + EncryptedColHashSuffix` so the `WHERE` hits the hash column.
- Reason: the ciphertext column itself is not searchable; the hash column supports only equality semantics.

### 5.3 GUID (`UNIQUEIDENTIFIER`) filtering

- For `=` / `!=` / `in` (any operator containing `=`), the value must parse as a `Guid` — otherwise 400.
- For `>` / `<` etc., the format check is skipped, and SQL Server's GUID ordering is byte-wise (not human-intuitive). **Avoid `<` / `>` on GUIDs in practice.**

### 5.4 MULTILINE_MAX is non-filterable

A first-pass validator (`ValidateFilterGroupNoMultilineMax`) explicitly rejects any filter on a top-level `MULTILINE_MAX` field. A second pass (`ValidateFilterGroupNoMultilineMaxOnExpansions`) does the same for dotted/expansion paths. Sort is also blocked.

- Reason: `NVARCHAR(MAX)` cannot be indexed; filtering would force full-table scans of multi-KB blobs at billing-scale.
- Behavior: 400 with `"Field '<name>' is of type MULTILINE_MAX and cannot be used in filters."`
- If you need to search such a field, use the dedicated text-search endpoint (separate path, separate semantics).

### 5.5 ChoiceSetMultiple — special string semantics

The column is `NVARCHAR` storing a sorted JSON array of integer choice IDs (e.g. `"[1,3,7]"`).

- `=` / `!=`: filter value must be a JSON array; it gets parsed, sorted, re-serialized so the comparison is canonical-form against the stored canonical form.
- `contains` / `not contains`: value gets wrapped with `[^0-9]<value>[^0-9]` boundary markers via `LIKE`, so `contains 3` matches `[1,3,7]` but not `[13]`.
- `[` or `]` in raw value with `contains` → 400 (avoids injection of array delimiters).

### 5.6 Numeric range validation is filter-aware

`MinValue` / `MaxValue` checks (from `SqlType`) are enforced for writes, but skipped for filter operators — you can filter on `age > 999999` even if the field's `MaxValue` is `1000`.

### 5.7 String length validation is filter-aware

Similarly, `NVARCHAR` / `MULTILINE` length-limit checks are write-only. Long filter values pass through (subject to SQL parameter size limits at the driver level).

### 5.8 Filtering on `$expand` paths (dotted field names)

Dotted names like `Customer.Email` are supported when `Customer` is in the `$expand` clause and `Email` is a selected field of that expanded entity.

- The filter is rewritten to use the expanded table alias.
- If the expansion isn't requested or the field isn't projected, the dotted filter fails resolution.
- This is the only way to filter on related entities — there is no implicit join.

### 5.9 Date/time format

Value must parse as `DateTimeOffset` (ISO 8601). Naive datetimes without offset are accepted but interpreted as UTC. Returned values are normalized to UTC on the wire.

### 5.10 Case sensitivity

String comparisons are **case-insensitive by default** because the column collation is `SQL_Latin1_General_CP1_CI_AS`. The code has a TODO to support case-sensitive filtering via `COLLATE SQL_Latin1_General_CP1_CS_AS` but it's not yet exposed (`SelectQueryBuilder.cs:299` comment).

This also explains why `fieldName` matching tolerates wrong casing on the wire — the server resolves field references case-insensitively.

---

## 6. Validation order

API request → 5 layers of checks (in order). Knowing which layer threw the error helps interpret it:

1. **API model binding** — JSON shape mismatches → 400 from MVC.
2. **`ProcessFilterGroup` validation** (`StorageManagementService.cs:8416`):
   - `fieldName` / `operator` non-null
   - `fieldName` regex
   - `IN` / `NOT IN` list non-empty
   - encrypted-field operator allow-list (§5.2)
   - per-type value-format validation (via `ValidateDataValue`)
   - filter count vs `MaxQueryFilterCount`
3. **MULTILINE_MAX guards** (`ValidateFilterGroupNoMultilineMax`, expansions-variant) → 400.
4. **RBAC / field-folder access checks** (`EntityDataAuthorizationService`) — denies access to fields the user can't read → 403.
5. **`SelectQueryBuilder.BuildWhereClauseForFilterGroup`** — final operator switch; unknown operator → 400.

All errors from layers 2–5 surface as `BadRequestException` with a descriptive message.

---

## 7. Limits

| Limit | Where | Default / source |
|---|---|---|
| Max filters per query (across all nested groups) | `EnvironmentConstraintOptions.MaxQueryFilterCount` | Per-tenant config; default check at filter parse time |
| Max IN-list size | Implicit via `MaxQueryFilterCount`; each list item counts as 1 SQL parameter | Capped by SQL Server's 2100-parameter limit |
| Filter nesting depth | Recursive — no hard cap in code | Bound by SQL nesting plan depth in practice |
| String length in filter value | No app-level cap on filter ops (write-time caps don't apply) | Bound by SQL parameter byte size |

---

## Source-of-truth file paths (CommonEntityPlatform)

| Topic | File |
|---|---|
| `QueryFilter` / `QueryFilterGroup` models | `src/Common/Model/QueryFilter.cs` |
| `FilterLogicalOperator` enum (`AND=0`, `OR=1`) | `src/Common/Model/QueryFilter.cs` |
| `SqlTypeName` enum (field types) | `src/Common/Model/FieldDefinition.cs:443-462` |
| Operator → SQL translation | `src/DatabaseManager/QueryBuilders/SelectQueryBuilder.cs:248-283` |
| ChoiceSetMultiple membership semantics | `src/DatabaseManager/QueryBuilders/SelectQueryBuilder.cs:304-327` |
| `$expand` dotted-field resolution | `src/DatabaseManager/QueryBuilders/SelectQueryBuilder.cs:185-218` |
| Filter-aware numeric range skip | `src/StorageManager/Services/StorageManagementService.cs:8180` |
| Filter-aware string length skip | `src/StorageManager/Services/StorageManagementService.cs:8157` |
| GUID format check | `src/StorageManager/Services/StorageManagementService.cs:8203-8208` |
| Encrypted-field operator allow-list | `src/StorageManager/Services/StorageManagementService.cs:8483-8525` |
| MULTILINE_MAX filter rejection | `src/StorageManager/Services/StorageManagementService.cs:7859-7885` |
| `ProcessFilterGroup` (validation entry point) | `src/StorageManager/Services/StorageManagementService.cs:8416` |
| Max-filter-count constraint | `src/Common/Options/EnvironmentConstraintOptions.cs` (`MaxQueryFilterCount`) |
| Case-sensitive collation TODO | `src/DatabaseManager/QueryBuilders/SelectQueryBuilder.cs:299` |
