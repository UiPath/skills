---
name: uipath-data-fabric
description: "UiPath Data Fabric entity/record CRUD via `uip df`. Create entities, insert/query/update/delete records, CSV import, file attachments. For Flow connector nodes (query/create/update/delete/get-by-id inside a `.flow`)→uipath-maestro-flow. For Orchestrator→uipath-platform. For Integration Service→uipath-platform."
---

# UiPath Data Fabric — Agent Skill

> **Preview** — skill is under active development; surface and behavior may change.

Data Fabric is UiPath's structured data store. Entities are typed schemas;
records are rows; file fields store binary attachments.

All operations go through `uip df <subject> <verb> --output json`.

---

## When to Use

- Creating or modifying entity schemas (add fields, update metadata)
- Reading, inserting, updating, or deleting records
- Filtering records with complex predicates
- Computing aggregate metrics for dashboards / KPIs (counts, sums, averages, group-by) — see [references/records-query.md](references/records-query.md#aggregates-server-side)
- Importing bulk data from CSV files
- Uploading or downloading file attachments on records

## When NOT to Use — Hand Off to Another Skill

Embedding Data Fabric reads/writes **inside a `.flow` file** as connector activity nodes (Query / Create / Update / Delete / Get Entity Record by ID) is owned by `uipath-maestro-flow`. That skill knows the node JSON, `bindings_v2.json`, connection-resource layout, and `node configure` mechanics.

Use this skill (`uipath-data-fabric`) for entity discovery and record seeding from the CLI; hand off to `uipath-maestro-flow` for in-flow node authoring.

| Task | Skill |
|------|-------|
| Discover entities, list/describe fields before authoring a flow node | `uipath-data-fabric` (`uip df entities list`/`get`) |
| Seed test records the flow will read | `uipath-data-fabric` (`uip df records insert` / `import`) |
| Add a Query/Create/Update/Delete/GetById node to a `.flow` | `uipath-maestro-flow` |
| Resolve the IS `uipath-uipath-dataservice` connection for binding | `uipath-maestro-flow` (in-flow binding) or `uipath-platform` (general IS connection management) |

---

## Not Supported — Never Attempt These

Respond that the operation is not supported. Do not try to work around it.

| Operation | Response |
|-----------|----------|
| Delete an entity | No `entities delete` command exists |
| Delete / remove a field | Field removal is not supported — the CLI will error |
| Change a field's data type | Not supported; type is fixed at creation |
| Create a federated entity | Not supported via CLI or UiPath portal |
| Write records to a federated entity | Federated entities are read-only |
| Create / update / delete a choice set | Choice sets are authored in the Data Fabric web UI; the CLI exposes only `choice-sets list` / `choice-sets get` for browsing |

---

## Critical Rules

1. **Install the tool first.** If `uip df` returns "unknown command": `uip tools install @uipath/data-fabric-tool`. See *Tool Version Requirements* below for the floor needed per feature.

2. **Verify login and tenant first.** Run `uip login status --output json`. Switch with `uip login tenant set <tenant>` if needed. For full login/environment setup, see the `uipath-platform` skill.

3. **Always resolve entity ID first.** Use `entities list` before any operation. Never assume an entity ID.

4. **Entity and field names must pass validation**: start with a letter, contain only letters/digits/underscores (`[a-zA-Z0-9_]`), 3–100 characters. No hyphens or spaces. Reserved field names that will error: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`.

5. **All updates require `Id` in the body.** The CLI routes single vs batch by whether the body is a JSON object (1 record) or array (multiple). Both require `"Id"` in the record. Use `records list` or `records query` to retrieve record IDs before updating.

6. **File fields are separate from record data.** Use `files upload`/`download`, not `records insert`. Field must be type `FILE`.

7. **CSV headers must match exact field names** (case-sensitive). Use `entities get` to discover field names before importing.

8. **Never create duplicate entities.** Always `entities list` first; reuse if it already exists.

9. **Only work with native entities.** When listing entities before a write, use `entities list --native-only` to filter out federated entities. Never write to federated entities.

10. **Never attempt entity delete.** No command exists. Respond: *"Deleting entities is not supported via the CLI."*

11. **Never attempt field delete.** Do not pass `removeFields` in `entities update`. Respond: *"Removing fields is not supported via the CLI."*

12. **Complex field types need extra config and lookups, just like `DECIMAL` needs `decimalPrecision`.** `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` require `choiceSetId` (from `choice-sets list`); `RELATIONSHIP` requires `referenceEntityName` (target's technical `Name`) + `referenceFieldName` (usually `Id`), and the target entity must exist first. Full shape in [`references/entity-schema.md`](references/entity-schema.md).

13. **`choice-sets` is read-only.** CLI has only `list` / `get` — author choice sets in the Data Fabric web UI. If a needed choice set is missing, stop and ask; do not fall back to `STRING`.

14. **Choice / relationship record values use lookup tokens, not labels.** Choice value → integer `NumberId` (single) or array of `NumberId`s (multi), from `choice-sets get`. Relationship value → target record's UUID `Id` regardless of `referenceFieldName`. Filter / `groupBy` use the same tokens; `CHOICE_SET_MULTIPLE` filtering has special operator semantics — see [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields).

15. **Answer with `records query`, not from memory.** Counts, sums, filters, lookups — issue a fresh `records query` (or `records list`) and use the server's response. Do not reuse cached insert responses, IDs you generated earlier, or values from previous tool results. Exception: the `Id` returned by the same `records insert` you just made.

16. **`records query` filter body.** Shape: `{"filterGroup":{"logicalOperator":<0|1|"AND"|"OR">,"queryFilters":[{"fieldName":"<name>","operator":"<symbol>","value":"<string>"}]}}`. Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not contains`, `startswith`, `endswith`, `in`, `not in`, plus is-empty (`=` with `value: null`) and is-not-empty (`!=` with `value: null`) — symbol form only; `==` / `Equals` / `eq` / `like` are rejected (400). `in` / `not in` use `valueList` (array), not `value`. **Operators are field-type-specific** — comparison (`<` `>` `<=` `>=`) only on Number / Date / Unique ID; Boolean only `=`/`!=`/empty; Choice Set has no comparison and no `in`/`not in`; Relationship supports `=`/`!=`/`in`/`not in` + empty (filter by the related record's FK `Id`); File presence only. Full support matrix, encrypted-field allow-list, `MULTILINE_MAX` non-filterability, GUID ordering, and `ChoiceSetMultiple` semantics — see [`references/filter-platform-contract.md` → Operator support by field type](references/filter-platform-contract.md#4-operator-support-by-field-type). The API will *execute* unsupported combinations instead of rejecting them — never rely on that (Rule 17). **Return all fields by default** — omit `selectedFields`; add it only when the user explicitly asks for a specific subset, never to trim output yourself.

17. **When any requested operation isn't supported, stop and confirm an alternative with the user. Never silently substitute. If no alternative works, recommend the right sibling skill.** Applies to any request Data Fabric (CLI or API) can't serve as stated — examples, not exhaustive:
    - Filter operator outside Rule 16's symbol list (`==`, `Equals`, `like`, regex, `BETWEEN`, full-text search, etc.) — rejected with 400.
    - Filter operator unsupported for the field's type per the support matrix (e.g. `<` / `>` on Text or Boolean, `in` / `not in` on Choice Set, `startswith` on a Number, comparison on Relationship). The API often *executes* these and returns wrong or unfiltered results — treat them as unsupported, never silent-run them.
    - Filter whose `value` is missing (any operator other than is-empty / is-not-empty) — an incomplete request.
    - `fieldName` that isn't in the entity's schema (typo, dropped column, wrong field for the entity).
    - Entity name that doesn't exist in the tenant or that's federated when a native operation was requested.
    - CLI verb that doesn't exist (`removeFields`, choice-set authoring, full entity rename, distinct case-insensitive equality, `groupBy` with expansions, etc. — see the *Not Supported* table).
    - Cross-entity joins or aggregations the API doesn't expose.
    - Value forms outside the SDK contract for a given field type.

    Required sequence:
    1. State precisely what was requested and which part isn't supported (cite the relevant Critical Rule, the schema, or the *Not Supported* table).
    2. Propose a concrete alternative and name it explicitly. By category:
        - **Unknown `fieldName`** — run `entities get` to list the entity's real fields, surface the candidates with the same type / a similar name, and ask which one to use. Example: prompt says *"filter by `Department`"* but the schema has `Dept`, `Role`, `Manager` → respond *"`Department` isn't a field on this entity. Did you mean `Dept`? Other STRING fields on this entity: `Role`, `Manager`. Which one should I filter on?"*
        - **Operator not in the symbol list** (`==`, `like`, regex, `BETWEEN`) — propose the closest supported operator or a composition (`BETWEEN x AND y` → `>=` + `<=` combined in `queryFilters` with `logicalOperator: 0`; regex → `contains` / `startswith` / `endswith` if a substring approximation fits).
        - **Operator unsupported for the field's type** (matrix) — do not silently run it. Offer the user two choices: **(a)** execute the request *without* this filter (run with the remaining filters, or return the unfiltered result set if it was the only one), or **(b)** stop and add a different, supported filter. Apply only the choice they pick.
        - **Missing `value`** (operator other than is-empty / is-not-empty) — do not proceed. Ask for the value (or `valueList`); report the request as incomplete. Never substitute a default.
        - **Missing CLI verb** — name the supported verb if one exists (`records query` vs `records list` for filtered reads), or hand off to the right sibling skill.
        - **Unsupported value form / type** — show the SDK-typed shape and ask the user to confirm the conversion.
    3. Ask the user to confirm. Apply **only** what they explicitly approve, using their exact choice. Never silently fall back to your own pick.
    4. If the user declines every alternative and Data Fabric genuinely cannot satisfy the request, stop and recommend the appropriate sibling skill — for example: in-flow connector activity → `uipath-maestro-flow`; Orchestrator / Integration Service ops → `uipath-platform`; UI / robot automation → `uipath-rpa`; agent lifecycle → `uipath-agents`; Test Manager → `uipath-test`. Do not fabricate a result or proceed with a degraded one.

---

## Tool Version Requirements

| Feature | Required `@uipath/data-fabric-tool` |
|---------|--------------------------------------|
| `entities` / `records` CRUD, `query` with filters/sort, `records import`, `files` | `0.9.0+` |
| Server-side `aggregates` and `groupBy` on `records query` | `1.0.1+` |

Upgrade with `uip tools install @uipath/data-fabric-tool@latest` when a feature appears to silently no-op (e.g. aggregate body keys returning raw record lists).

---

## Quick Start

```bash
# List entities (use --native-only before any write)
uip df entities list --native-only --output json

# Get entity schema (field names and types)
uip df entities get <entity-id> --output json

# List records (first page)
uip df records list <entity-id> --limit 50 --output json

# Insert one record
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json

# Query with a filter
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json

# Aggregate query — count of records per Status (server-side groupBy)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

For Complex types  field shapes and value formats, see [`references/entity-schema.md`](references/entity-schema.md#supported-field-types) and [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields).

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| Explore what entities exist | `entities list` → `entities get <id>` |
| Explore only native entities | `entities list --native-only` |
| Browse / inspect choice sets (read-only) | `choice-sets list`, `choice-sets get <choice-set-id>` |
| Create a new entity | `entities create <name> --body '{"fields":[{"fieldName":"Title","type":"STRING"}]}'` — for complex field types (`CHOICE_SET_*`, `RELATIONSHIP`) and their required extras, see [`references/entity-schema.md`](references/entity-schema.md#supported-field-types) |
| Update entity / add fields | `entities update <id> --body '{"addFields":[{"fieldName":"NewField","type":"STRING"}]}'` |
| Update existing field metadata | `entities update <id> --body '{"updateFields":[{"id":"<field-uuid>","displayName":"New Label","isRequired":true}]}'` — `id` is the field UUID from `entities get Fields[].ID` |
| Update entity metadata | `entities update <id> --body '{"displayName":"New Name","description":"desc"}'` |
| Read records (first page) | `records list <entity-id> --limit 50` |
| Read records (next page) | `records list <entity-id> --cursor <NextCursor>` |
| Get one record | `records get <entity-id> <record-id>` |
| Insert one record | `records insert <entity-id> --body '{...}'` (or `--file`). Choice / relationship value formats: see [`references/records-query.md`](references/records-query.md#writing-choice-set-and-relationship-values) |
| Batch insert | `records insert <entity-id> --body '[{...},{...}]'` |
| Update one record | `records update <entity-id> --body '{"Id":"<record-id>","field":"val"}'` |
| Batch update | `records update <entity-id> --body '[{"Id":"<id1>","field":"val"},{"Id":"<id2>","field":"val"}]'` |
| Delete records | `records delete <entity-id> <id1> <id2>` |
| Filter/search records | `records query <entity-id> --body '{...}'`. Choice / relationship filter operators: see [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields) |
| Aggregate / group-by metrics | `records query <entity-id> --body '{"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}],"groupBy":["FieldName"]}'` |
| Bulk import from CSV (Basic field types only — `CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, `AUTO_NUMBER` are silently dropped) | `records import <entity-id> --file data.csv` |
| Bulk seed records that include complex fields | `records insert <entity-id> --file records.json` with a JSON array body |
| Upload file to record | `files upload <entity-id> <record-id> <field-name> --file path` |
| Download file | `files download <entity-id> <record-id> <field-name> --destination path` |
| Delete file | `files delete <entity-id> <record-id> <field-name>` |

---

## Field Types

Pass the exact `EntityFieldDataType` string — the CLI is case-sensitive. Common types: `STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `UUID`, `FILE`. Complex types that require extra config: `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` (need `choiceSetId`), `RELATIONSHIP` (needs `referenceEntityName` + `referenceFieldName`), `AUTO_NUMBER`. Full table with SQL backing types, required extras, and value semantics in [`references/entity-schema.md`](references/entity-schema.md).

### Advanced Field Constraints

Optional per-type constraints on create/update — `lengthLimit` (STRING, MULTILINE_TEXT), `maxValue` / `minValue` (INTEGER, BIG_INTEGER, DECIMAL, FLOAT, DOUBLE), `decimalPrecision` (DECIMAL, FLOAT, DOUBLE). See `references/entity-schema.md` for ranges and examples.

---

## Workflow: Discover → Act → Verify

1. **Discover** — list entities, get schema, check existing records
2. **Act** — create/insert/update
3. **Verify** — re-read to confirm the operation succeeded

```bash
uip df entities list --native-only --output json
uip df entities get <entity-id> --output json
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json
uip df records list <entity-id> --limit 50 --output json
# Use HasNextPage + NextCursor to page through results
uip df records list <entity-id> --cursor <NextCursor> --output json
```

---

## Query Request Format

Pass via `--body` or `--file`. Use `--limit`, `--cursor`, and `--offset` CLI flags for pagination — not body keys. See [Pagination](#pagination) below.

```json
{
  "filterGroup": {
    "logicalOperator": 0,
    "queryFilters": [
      { "fieldName": "Status", "operator": "=", "value": "active" },
      { "fieldName": "Score", "operator": ">=", "value": "80" }
    ]
  },
  "sortOptions": [{ "fieldName": "Score", "isDescending": true }],
  "selectedFields": ["Title", "Score", "Status"]
}
```

- `logicalOperator`: `0` = AND, `1` = OR
- Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not contains`, `startswith`, `endswith`, `in`, `not in`
- For `in` / `not in` use `"valueList": ["a","b","c"]` — **not** a comma-separated `value` string
- Response includes `HasNextPage` and `NextCursor` — pass `NextCursor` to `--cursor` for the next page

## Pagination

`records list` / `records query` paginate via `--limit`, `--cursor`, `--offset`. See [`references/records-query.md`](references/records-query.md).

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `unknown command: df` | Tool not installed | `uip tools install @uipath/data-fabric-tool` |
| `Not logged in` | Auth expired | `uip login` |
| `HTTP 401` | Invalid token | Re-login; ensure `DataServiceApiUserAccess` scope is present |
| `HTTP 403` | Permission denied | Ensure account has Data Fabric permissions |
| `Entity not found` | Wrong entity ID | Run `entities list` to get correct ID |
| `Record must include 'Id'` | Update body missing Id | Every record passed to `records update` must include `"Id": "<record-id>"` — both single and batch |
| `Each field must include a 'fieldName' string` | Invalid field in `entities create` | Use `{"fieldName":"myfield"}` not `{"name":"myfield"}` |
| `Entity name resolution failed` | Query/import with bad ID | Verify entity exists with `entities list` |
| Import errors in CSV | Header mismatch | Run `entities get` and check exact field names (case-sensitive) |
| `records import` succeeded but choice / relationship / file column is `null` on every row | `records import` silently drops complex field types (Basic only) | Re-seed via `records insert` with a JSON body — see [`references/bulk-import.md`](references/bulk-import.md) |
| Write to federated entity | Entity is read-only | Use `--native-only`; federated entities cannot be written to |

---

## References

- `references/entity-schema.md` — Field definitions, supported types, schema update patterns, choice-set + relationship field shapes
- `references/choice-sets.md` — Browse choice sets, look up `NumberId`s, add CHOICE_SET fields to entities, write choice values on records
- `references/records-query.md` — Query filter syntax, pagination, sorting, choice/relationship semantics on read & write
- `references/filter-platform-contract.md` — Authoritative filter contract sourced from `CommonEntityPlatform`: per-type operator support matrix, encrypted-field rules, GUID ordering, `MULTILINE_MAX` non-filterability, `ChoiceSetMultiple` JSON-array semantics, `$expand` dotted-field resolution, validation order, limits, source file paths
- `references/file-attachments.md` — File field upload/download/delete file
- `references/bulk-import.md` — CSV format requirements and the Basic-fields-only limitation (complex types are silently dropped — use `records insert` with a JSON body instead)
