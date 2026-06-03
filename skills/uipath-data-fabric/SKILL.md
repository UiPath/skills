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

12. **Complex field types need extra config and lookups, just like `DECIMAL` needs `decimalPrecision`.** `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` require `choiceSetId` (UUID, from `choice-sets list`); `RELATIONSHIP` and `FILE` require `referenceEntityId` (target entity UUID — from `entities list`) + `referenceFieldId` (target field UUID — from `entities get <target-id>`). Names are silently dropped, the FK never wires — always use UUIDs. The target entity must exist first. Full shape in [`references/entity-schema.md`](references/entity-schema.md).

13. **Choice-set authoring is in the CLI.** `choice-sets create` / `update` / `delete` + `choice-set-values create` / `update` / `delete`, alongside `list` and `list-values`. If a needed choice set is missing, ask the user — then create it (don't fall back to `STRING`). Full surface: [`references/choice-sets.md`](references/choice-sets.md).

14. **Choice / relationship record values use lookup tokens, not labels.** Choice value → integer `NumberId` (single) or array of `NumberId`s (multi), from `choice-sets list-values`. Relationship value → target record's UUID `Id` regardless of which field was bound as `referenceFieldId`. Filter / `groupBy` use the same tokens; `CHOICE_SET_MULTIPLE` filtering has special operator semantics — see [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields).

15. **Answer with `records query`, not from memory.** Counts, sums, filters, lookups — issue a fresh `records query` (or `records list`) and use the server's response. Do not reuse cached insert responses, IDs you generated earlier, or values from previous tool results. Exception: the `Id` returned by the same `records insert` you just made.

16. **`records query` filters.** Body shape, operators, per-type support, response, and unsupported-operator handling are in the [filter contract](references/filter-platform-contract.md). Symbol-form operators only (`==`/`Equals`/`like` → 400). On an unsupported operator/type or a missing value, don't run it — ask the user (Rule 17). **Return all fields by default** — omit `selectedFields` unless a subset is requested.

17. **When a request isn't supported, stop and confirm an alternative — never silently substitute.** Triggers (not exhaustive): a filter operator unsupported for the field type / not in the symbol list / missing a value (see [filter contract → Unsupported operator](references/filter-platform-contract.md#unsupported-operator-or-missing-value)); an unknown `fieldName`; a nonexistent or federated entity; a missing CLI verb (`removeFields`, entity delete, … — see *Not Supported*); cross-entity joins or value forms the API can't serve.
    Sequence: (1) state precisely what isn't supported (cite the rule / schema / *Not Supported* table); (2) propose a concrete alternative and name it — e.g. for an unknown `fieldName`, list the entity's real same-type fields from `entities get` and ask which; (3) apply **only** what the user approves, never your own fallback. If nothing works, recommend the right sibling skill (`uipath-maestro-flow` / `uipath-platform` / `uipath-rpa` / `uipath-agents` / `uipath-test`) — don't fabricate or return a degraded result.

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
| Manage choice sets | `choice-sets list` / `list-values <id>` / `create` / `update` / `delete`; values via `choice-set-values create` / `update` / `delete` — full surface in [`references/choice-sets.md`](references/choice-sets.md) |
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

Pass the exact `EntityFieldDataType` string — the CLI is case-sensitive. Common types: `STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `UUID`, `FILE`. Complex types that require extra config: `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` (need `choiceSetId`), `RELATIONSHIP` and `FILE` (need `referenceEntityId` + `referenceFieldId`), `AUTO_NUMBER`. Full table with SQL backing types, required extras, and value semantics in [`references/entity-schema.md`](references/entity-schema.md).

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

Pass the query body via `--body` or `--file`; pagination uses `--limit` / `--cursor` / `--offset` CLI flags, never body keys (see [Pagination](#pagination) below). The body shape, operators, per-type support, and response shape live in [`references/filter-platform-contract.md`](references/filter-platform-contract.md); query-only extras (`selectedFields`, `sortOptions`) are documented in [`references/records-query.md`](references/records-query.md).

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
- `references/choice-sets.md` — Full choice-set CRUD (`list`/`list-values`/`create`/`update`/`delete` plus `choice-set-values create`/`update`/`delete`), look up `NumberId`s, add CHOICE_SET fields to entities, write choice values on records
- `references/records-query.md` — Query filter syntax, pagination, sorting, choice/relationship semantics on read & write
- `references/filter-platform-contract.md` — Filter body structure, per-type operator support matrix, and what to do when a request needs an unsupported operator
- `references/file-attachments.md` — File field upload/download/delete file
- `references/bulk-import.md` — CSV format requirements and the Basic-fields-only limitation (complex types are silently dropped — use `records insert` with a JSON body instead)
