---
name: uipath-data-fabric
description: "[PREVIEW] Data Fabric entity/record CRUD via uip df. Create entities, insert/query/update/delete records, CSV import, file attachments. For Orchestrator→uipath-platform. For Integration Service→uipath-platform."
---

# UiPath Data Fabric — Agent Skill

Data Fabric is UiPath's structured data store. Entities are typed schemas;
records are rows; file fields store binary attachments.

All operations go through `uip df <subject> <verb> --output json`.

---

## When to Use

- Creating or modifying entity schemas (add fields, update metadata)
- Reading, inserting, updating, or deleting records
- Filtering records with complex predicates
- Importing bulk data from CSV files
- Uploading or downloading file attachments on records

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

1. **Install the tool first.** If `uip df` returns "unknown command": `uip tools install @uipath/data-fabric-tool` (min version `0.2.0`).

2. **Verify login and tenant first.** Run `uip login status --output json`. Switch with `uip login tenant set <tenant>` if needed. For full login/environment setup, see the `uipath-platform` skill.

3. **Always resolve entity ID first.** Use `entities list` before any operation. Never assume an entity ID.

4. **Field names are technical identifiers** (lowercase, no spaces). Use `fieldName` in field definitions.

5. **Records need `Id` for update.** Use `records list` or `records query` to retrieve the record ID before updating.

6. **File fields are separate from record data.** Use `files upload`/`download`, not `records insert`. Field must be type `file`.

7. **CSV headers must match exact field names** (case-sensitive). Use `entities get` to discover field names before importing.

8. **Never create duplicate entities.** Always `entities list` first; reuse if it already exists.

9. **Only work with native entities.** Use `--native-only` before any write operation. Never write to federated entities.

10. **Never attempt entity delete.** No command exists. Respond: *"Deleting entities is not supported via the CLI."*

11. **Never attempt field delete.** Do not pass `removeFields` in `entities update`. Respond: *"Removing fields is not supported via the CLI."*

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
uip df records insert <entity-id> --body '{"fieldName":"value"}' --output json

# Query with a filter
uip df records query <entity-id> \
  --body '{"filterGroup":{"queryFilters":[{"fieldName":"status","operator":"=","value":"active"}]}}' \
  --output json
```

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| Explore what entities exist | `entities list` → `entities get <id>` |
| Explore only native entities | `entities list --native-only` |
| Create a new entity | `entities create <name> --body '{"fields":[{"fieldName":"title","type":"text"}]}'` |
| Update entity / add fields | `entities update <id> --body '{"addFields":[{"fieldName":"newField","type":"text"}]}'` |
| Update entity metadata | `entities update <id> --body '{"displayName":"New Name","description":"desc"}'` |
| Read records (first page) | `records list <entity-id> --limit 50` |
| Read records (next page) | `records list <entity-id> --cursor <NextCursor>` |
| Get one record | `records get <entity-id> <record-id>` |
| Insert records | `records insert <entity-id> --body '{...}'` (or `--file`) |
| Update records | `records update <entity-id> --body '{"Id":"...","field":"val"}'` |
| Delete records | `records delete <entity-id> <id1> <id2>` |
| Filter/search records | `records query <entity-id> --body '{...}'` |
| Bulk import from CSV | `records import <entity-id> --file data.csv` |
| Upload file to record | `files upload <entity-id> <record-id> <field-name> --file path` |
| Download file | `files download <entity-id> <record-id> <field-name> --destination path` |
| Delete file | `files delete <entity-id> <record-id> <field-name>` |

---

## Field Types

| User type | SQL type | Notes |
|-----------|----------|-------|
| `text` | NVARCHAR(200) | Short strings |
| `longtext` | NVARCHAR(4000) | Long strings |
| `number` | INT | Integer |
| `decimal` | DECIMAL | Floating point |
| `boolean` | BIT | true/false |
| `datetime` | DATETIME2 | Date + time |
| `date` | DATE | Date only |
| `file` | NVARCHAR(200) | File attachment (use `files upload/download` to manage) |

---

## Workflow: Discover → Act → Verify

1. **Discover** — list entities, get schema, check existing records
2. **Act** — create/insert/update
3. **Verify** — re-read to confirm the operation succeeded

```bash
uip df entities list --native-only --output json
uip df entities get <entity-id> --output json
uip df records insert <entity-id> --body '{"name":"Alice","score":95}' --output json
uip df records list <entity-id> --limit 50 --output json
# Use HasNextPage + NextCursor to page through results
uip df records list <entity-id> --cursor <NextCursor> --output json
```

---

## Query Request Format

Pass via `--body` or `--file`. Use `--limit` and `--cursor` CLI flags for pagination — not body keys.

```json
{
  "filterGroup": {
    "logicalOperator": 0,
    "queryFilters": [
      { "fieldName": "status", "operator": "=", "value": "active" },
      { "fieldName": "score", "operator": ">=", "value": "80" }
    ]
  },
  "sortOptions": [{ "fieldName": "score", "isDescending": true }],
  "selectedFields": ["title", "score", "status"]
}
```

- `logicalOperator`: `0` = AND, `1` = OR
- Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not contains`, `startswith`, `endswith`, `in`, `not in`
- Response includes `HasNextPage` and `NextCursor` — pass `NextCursor` to `--cursor` for the next page

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `unknown command: df` | Tool not installed | `uip tools install @uipath/data-fabric-tool` |
| `Not logged in` | Auth expired | `uip login` |
| `HTTP 401` | Invalid token | Re-login; ensure `DataServiceApiUserAccess` scope is present |
| `HTTP 403` | Permission denied | Ensure account has Data Fabric permissions |
| `Entity not found` | Wrong entity ID | Run `entities list` to get correct ID |
| `Record must include 'Id'` | Update missing Id | Add `"Id": "<record-id>"` to the body |
| `Each field must include a 'fieldName' string` | Invalid field in `entities create` | Use `{"fieldName":"myfield"}` not `{"name":"myfield"}` |
| `Entity name resolution failed` | Query/import with bad ID | Verify entity exists with `entities list` |
| Import errors in CSV | Header mismatch | Run `entities get` and check exact field names (case-sensitive) |
| Write to federated entity | Entity is read-only | Use `--native-only`; federated entities cannot be written to |

---

## References

- `references/entity-schema.md` — Field definitions, supported types, schema update patterns
- `references/records-query.md` — Query filter syntax, pagination, sorting examples
- `references/file-attachments.md` — File field upload/download/delete file
- `references/bulk-import.md` — CSV format requirements and bulk import patterns
