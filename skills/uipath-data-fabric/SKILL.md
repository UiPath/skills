---
name: uipath-data-fabric
description: "[PREVIEW] Data Fabric entity/record CRUD via uip df. Create entities, insert/query/update/delete records, CSV import, file attachments. For Orchestrator→uipath-platform. For Flow connector nodes→uipath-maestro-flow."
---

# UiPath Data Fabric — Agent Skill

Data Fabric is UiPath's structured data store. Entities are typed schemas; records are rows; file fields store binary attachments.

All operations go through `uip df <subject> <verb> --output json`.

---

## When to Use

- Creating or modifying entity schemas (add fields, update metadata)
- Reading, inserting, updating, or deleting records
- Filtering records with complex predicates
- Importing bulk data from CSV files
- Uploading or downloading file attachments on records

---

## Critical Rules

1. **Install the tool first.** If `uip df` returns "unknown command": `uip tools install @uipath/data-fabric-tool` (min version `0.2.0`).

2. **Verify login and tenant first.** Run `uip login status --output json`. Switch with `uip login tenant set <tenant>` if needed. For full login/environment setup, see the `uipath-platform` skill.

3. **Always resolve entity ID first.** Run `entities list` before any operation. Never assume an entity ID.

4. **Entity and field names must pass validation**: start with a letter, contain only letters/digits/underscores (`[a-zA-Z0-9_]`), 3–100 characters. No hyphens or spaces. Reserved field names that will error: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`.

5. **All updates require `Id` in the body.** The CLI routes single vs batch by whether the body is a JSON object (1 record) or array (multiple). Both require `"Id"` in the record. Use `records list` or `records query` to retrieve record IDs before updating.

6. **File fields are separate from record data.** Use `files upload`/`download`, not `records insert`. Field must be type `FILE`.

7. **CSV headers must match exact field names** (case-sensitive). Use `entities get` to discover field names before importing.

8. **Never create duplicate entities.** Run `entities list` first; reuse if the entity already exists.

9. **Only work with native entities.** Use `entities list --native-only` before any write to filter out federated entities. Never write to federated entities.

10. **Field type is fixed at creation.** You cannot change a field's data type via `updateFields` or any other command. If the user needs a different type, inform them — the field cannot be modified after creation.

---

## Quick Start

```bash
# 1. Verify login and tenant
uip login status --output json

# 2. List entities — always use --native-only before any write
uip df entities list --native-only --output json

# 3. Inspect entity schema (field names and types)
uip df entities get <entity-id> --output json

# 4. Act — insert, update, query, or import
uip df records insert <entity-id> --body '{"<FieldName>":"<value>"}' --output json

# 5. Verify — re-read to confirm the operation succeeded
uip df records list <entity-id> --limit 50 --output json
# Use HasNextPage + NextCursor to page through results
uip df records list <entity-id> --cursor <NextCursor> --output json
```

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| Explore what entities exist | `entities list` → `entities get <id>` |
| Explore only native entities | `entities list --native-only` |
| Create a new entity | `entities create <name> --body '{"fields":[{"fieldName":"<Name>","type":"<TYPE>"}]}'` |
| Update entity / add fields | `entities update <id> --body '{"addFields":[{"fieldName":"<NewField>","type":"<TYPE>"}]}'` |
| Update entity metadata | `entities update <id> --body '{"displayName":"<New Name>","description":"<desc>"}'` |
| Read records (first page) | `records list <entity-id> --limit 50` |
| Read records (next page) | `records list <entity-id> --cursor <NextCursor>` |
| Get one record | `records get <entity-id> <record-id>` |
| Insert one record | `records insert <entity-id> --body '{...}'` (or `--file`) |
| Batch insert | `records insert <entity-id> --body '[{...},{...}]'` |
| Update one record | `records update <entity-id> --body '{"Id":"<record-id>","<field>":"<val>"}'` |
| Batch update | `records update <entity-id> --body '[{"Id":"<id1>","<field>":"<val>"},...]'` |
| Delete records | `records delete <entity-id> <id1> <id2>` |
| Filter/search records | `records query <entity-id> --body '{...}'` — see [`references/records-query.md`](references/records-query.md) |
| Bulk import from CSV | `records import <entity-id> --file <path>` — see [`references/bulk-import.md`](references/bulk-import.md) |
| Upload file to record | `files upload <entity-id> <record-id> <field-name> --file <path>` |
| Download file | `files download <entity-id> <record-id> <field-name> --destination <path>` |
| Delete file | `files delete <entity-id> <record-id> <field-name>` |

---

## Field Types

Pass the exact `EntityFieldDataType` string — the CLI is case-sensitive. Common types: `STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `UUID`. For the full type table with SQL backing types, see [`references/entity-schema.md`](references/entity-schema.md).

---

## Anti-Patterns

- **Never attempt entity delete** — no command exists. Tell the user it is not supported.
- **Never attempt field delete or pass `removeFields` in `entities update`** — the CLI will error. Tell the user field removal is not supported.
- **Never change a field's data type** — type is fixed at creation. Inform the user and stop.
- **Never create a federated entity** — not supported via CLI or UiPath portal.
- **Never write to a federated entity** — they are read-only. Filter them with `--native-only` on `entities list` before any write.
- **Never assume an entity ID** — always resolve with `entities list` before any operation.
- **Never use `start` or `limit` as query body keys** — pagination uses `--limit` and `--cursor` CLI flags, not request body fields.
- **Never include system fields in record bodies or CSV headers** — `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime` are auto-managed and will cause errors on insert or import.

---

## References

- [`references/entity-schema.md`](references/entity-schema.md) — Field definitions, supported types, schema update patterns
- [`references/records-query.md`](references/records-query.md) — Query filter syntax, insert/update/delete operations, pagination, sorting examples
- [`references/file-attachments.md`](references/file-attachments.md) — File field upload/download/delete
- [`references/bulk-import.md`](references/bulk-import.md) — CSV format requirements and bulk import patterns
- [`references/troubleshooting.md`](references/troubleshooting.md) — Error codes, causes, and fixes
