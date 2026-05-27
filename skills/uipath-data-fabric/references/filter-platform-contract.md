# Filter Platform Contract

Which operators are valid per field type, so you build a valid `records query` filter. Body usage and the unsupported-operator handling: [`records-query.md`](records-query.md) and SKILL.md Rule 17.

## Filter body

```json
{
  "logicalOperator": "AND",          // AND/OR or 0/1 — case-insensitive
  "queryFilters": [
    { "fieldName": "Status", "operator": "=",  "value": "Active" },
    { "fieldName": "Status", "operator": "in", "valueList": ["A", "B"] }
  ],
  "filterGroups": [ /* nested groups, recursive; AND/OR may mix per level */ ]
}
```

- `value` is always a JSON **string** (`"18"`, `"true"`, ISO-8601 dates) — the server parses it.
- `in` / `not in` use `valueList`; everything else uses `value`.
- `null` value = is-empty (`=`) / is-not-empty (`!=`).
- Response: `{ TotalCount, Records, HasNextPage, NextCursor? }`. Page with `--limit` / `--cursor` flags, never body keys.

## Operator support by field type

Build only within this matrix (✅ supported). The API *runs* some ❌ cells anyway (e.g. `<` on Text — lexicographic, so `"user2@…" < "user20@…"`) and 400s only on unknown operators (`==`, `Equals`, `like`). Never rely on that: when a request needs an unsupported operator/type combo, or has no value, ask the user — don't silently run it (SKILL.md Rule 17).

| Operator | Text / Multiline | Number / Autonum | Date/Time | Boolean | Choice Set | Relationship | File | Unique ID |
|---|---|---|---|---|---|---|---|---|
| `=` `!=` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `contains` `not contains` | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| `startswith` `endswith` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `>` `<` `>=` `<=` | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| is empty / not empty | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `in` `not in` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |

Complex-field values: **Choice Set** — the integer `NumberId` (multi: `=` takes a sorted JSON-array string `"[1,3]"`, `contains` takes a bare id `"3"`). **Relationship** — the target record's UUID `Id`.

## Unsupported operator, or missing value

If a request needs an out-of-matrix operator/type combo (or an operator outside the list above — `BETWEEN`, regex, `like`), or an operator other than is-empty/not-empty has no value, **don't silently run it**. Ask the user to either **(a)** run the query without that filter, or **(b)** supply a supported one — then apply only their choice, never a default. Compositions often help: `BETWEEN x AND y` → `>=` + `<=` in one `queryFilters` (`logicalOperator: 0`); regex → `contains` / `startswith` / `endswith`.
