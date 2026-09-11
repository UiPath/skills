# Filter Platform Contract

Defines valid `records query` filter operators by field type. For filter-body usage and unsupported-operator handling, see [`records-query.md`](records-query.md) and data-fabric.md Rule 17.

## Filter body and pagination

A filter group has `logicalOperator` (`AND`/`OR` or `0`/`1`, case-insensitive), leaf `queryFilters` (`{ fieldName, operator, value }`), and optional nested `filterGroups` with the same structure.

Use JSON-string `value` (`"18"`, `"true"`, or an ISO-8601 date), except `null` for empty checks. Use `valueList` only with `in`/`not in`; all other operators use `value`. `null` means is-empty (`=`) or is-not-empty (`!=`).

Responses are `Data: { Items, TotalCount, HasNextPage, NextCursor: { Value }, CurrentPage, TotalPages, SupportsPageJump }`; records are in `Data.Items`. Paginate with `--limit` / `--cursor`, passing `NextCursor.Value`; never use body keys for pagination.

## Operator support by field type

Build filters only within this matrix (✅ supported). Unsupported combinations may execute with unintended behavior (for example, `<` on Text is lexicographic); never rely on them. Unknown operators such as `==`, `Equals`, or `like` return 400. If the requested operator/type is unsupported or lacks a value, ask before running it (data-fabric.md Rule 17).

| Operator | Text / Multiline | Number / Autonum | Date/Time | Boolean | Choice Set | Relationship | File | Unique ID |
|---|---|---|---|---|---|---|---|---|
| `=` `!=` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `contains` `not contains` | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| `startswith` `endswith` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `>` `<` `>=` `<=` | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| is empty / not empty | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `in` `not in` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |

Complex-field values:

- **Choice Set:** use the integer `NumberId`. For multi-value fields, `=` takes a sorted JSON-array string such as `"[1,3]"`; `contains` takes a bare ID such as `"3"`.
- **Relationship:** use the target record's UUID `Id`.

**`MULTILINE_MAX` is outside the matrix entirely.** Text / Multiline support does not apply: no operator, including is-empty, and no `sortOptions` is supported. The server rejects these requests with 400 — *"Field '<name>' is of type MULTILINE_MAX and cannot be used in filters."* / *"Sort field '<name>' is of type MULTILINE_MAX and cannot be used for sorting."* Do not offer this field for filtering or sorting. If requested, explain the limitation and, only with the user's approval, fetch full values via `records get` and evaluate client-side.

## Unsupported operators or missing values

For an out-of-matrix combination, unlisted operator (`BETWEEN`, regex, `like`), or missing value for any operator other than is-empty/not-empty, do not run silently. Ask the user to either **(a)** run without that filter or **(b)** supply a supported one; apply only their choice and never default. Compose supported operators when appropriate: `BETWEEN x AND y` becomes `>=` plus `<=` in one `queryFilters` (`logicalOperator: 0`), and regex becomes `contains`, `startswith`, or `endswith`.