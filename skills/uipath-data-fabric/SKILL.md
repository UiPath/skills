---
name: uipath-data-fabric
description: "Build and manage UiPath Data Fabric entities and records via the CLI. TRIGGER when: user asks to create a Data Fabric entity, insert/query/update/delete records, import data from CSV, upload/download files on records, or mentions 'Data Fabric', 'data service', 'uip df'. DO NOT TRIGGER when: user is asking about Orchestrator assets, Integration Service connectors, or general database operations unrelated to UiPath Data Fabric. DO NOT TRIGGER for federated entity creation or external connection setup — not supported."
user-invokable: true
---

# UiPath Data Fabric — Agent Skill

Data Fabric is UiPath's structured data store. Entities are typed schemas;
records are rows; file fields store binary attachments.

All operations go through `uip df <subject> <verb> --output json`.

---

## Login & Tenant Setup

**Default to Production. Only switch environment/org/tenant when explicitly stated in the request.**

- If the request mentions no environment → use the current session (defaults to prod `cloud.uipath.com`)
- If the request explicitly names an environment/org/tenant → check `uip login status` and re-login if needed

When switching is required:
1. Check current login: `uip login status --output json` — verify `UIPATH_URL`, `Organization`, and `Tenant`
2. Re-login with `--authority` only if environment differs:
   - Alpha: `uip login --authority https://alpha.uipath.com --tenant <tenant>`
   - Staging: `uip login --authority https://staging.uipath.com --tenant <tenant>`
   - Production: `uip login --tenant <tenant>` (default, no `--authority` needed)
3. If already on the right environment but wrong tenant: `uip login tenant set <tenant-name>`

```bash
# Check current environment, org, and tenant
uip login status --output json

# Login to Alpha with a specific tenant
uip login --authority https://alpha.uipath.com --tenant IMDB

# List all available tenants (after login)
uip login tenant list --output json

# Switch tenant within the same environment
uip login tenant set IMDB
```

> **Critical:** The `--tenant` flag on `df` commands does NOT switch the active session tenant.
> The environment is determined by `UIPATH_URL` in the auth file — always confirm with `login status` before running `df` commands.

---

## When to Use

- Creating or modifying entity schemas (fields, types)
- Reading, inserting, updating, or deleting records
- Filtering records with complex predicates
- Importing bulk data from CSV files
- Uploading or downloading file attachments on records

> **Not supported:** Creating federated entities or setting up external connections/connectors is not currently supported — neither via this CLI nor via the UiPath portal. Federated entities are read-only views backed by Integration Service connectors (e.g. Salesforce, Azure AD). If a user asks to create a federated entity or link an entity to an external connector, inform them this is not supported at all.

---

## Native vs Federated Entities

Data Fabric has two kinds of entities:

| Kind | Description | Records writable? |
|------|-------------|-------------------|
| **Native** | Data stored directly in Data Fabric | Yes — full CRUD |
| **Federated** | Backed by an external connector (Salesforce, Azure AD, etc.) | Read-only via the connector |

The `entities list` output includes a `Source` column:
- `Native` — safe to read/write records
- `Federated (ConnectorName)` — read-only, records managed externally

**Always use `--native-only` when the task involves writing records**, to avoid accidentally targeting a federated entity.

```bash
# List only native entities
uip df entities list --native-only --output json
```

---

## Quick Start

```bash
# Check login and active tenant
uip login status --output json

# Switch tenant if needed
uip login tenant set <tenant-name>

# List entities
uip df entities list --output json

# Get entity details (shows field names and types)
uip df entities get <entity-id> --output json

# List records
uip df records list <entity-id> --output json

# Insert one record
uip df records insert <entity-id> --body '{"fieldName":"value"}' --output json

# Query with a filter
uip df records query <entity-id> \
  --body '{"filterGroup":{"queryFilters":[{"fieldName":"status","operator":"=","value":"active"}]}}' \
  --output json
```

---

## Critical Rules

1. **Always resolve org and tenant first.** If the user specifies an org/environment and tenant, run `uip login status` to check the active tenant, then `uip login tenant set <tenant>` to switch if needed. Never assume the active tenant matches the user's intent.

2. **Always resolve entity ID first.** Use `entities list` to discover entities before any operation. Never assume an entity ID.

3. **Entity names are technical names** (lowercase, no spaces). The `--fields` `name` property must follow this convention — spaces are stripped automatically.

4. **Records need `Id` for update/delete.** Use `records list` or `records query` to retrieve the ID of the record you want to modify.

5. **Query uses entity ID, but under the hood resolves entity name.** If query fails with "not found", check that the entity ID is correct with `entities get`.

6. **File fields are separate from record data.** Uploading a file uses `files upload`, not `records insert`. The field must be of type `file`.

7. **Import from CSV.** The CSV header row must match exact field names (case-sensitive). Use `entities get` to discover field names before importing.

8. **Never create duplicate entities.** Always `entities list` first. If an entity with the same name exists, use it.

9. **Only work with native entities.** Use `entities list --native-only` to discover entities before any write operation. Never attempt to insert, update, delete, or import records on a federated entity — it will fail. If asked to create a federated entity or connect to an external source, respond: *"Creating federated entities is not currently supported — neither via the CLI nor the UiPath portal."*

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| Explore what entities exist | `entities list` → `entities get <id>` |
| Explore only native entities | `entities list --native-only` |
| Create a new entity | `entities create <name> --fields '[...]'` |
| Add a field to entity | `entities add-field <id> <field-name> --type <type>` |
| Remove a field | `entities remove-field <id> <field-name>` |
| Read records | `records list <entity-id>` |
| Get one record | `records get <entity-id> <record-id>` |
| Insert records | `records insert <entity-id> --body '{...}'` (or `--file`) |
| Update records | `records update <entity-id> --body '{"Id":"...","field":"val"}'` |
| Delete records | `records delete <entity-id> <id1> <id2>` |
| Filter/search records | `records query <entity-id> --body '{...}'` |
| Bulk import from CSV | `records import <entity-id> --file data.csv` |
| Upload file to record | `files upload <entity-id> <record-id> <field-name> --file path` |
| Download file | `files download <entity-id> <record-id> <field-name> --output path` |
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
| `file` | NVARCHAR(200) | File attachment (use `files upload/download/delete` to manage) |

---

## Workflow: Discover → Act → Verify

**Always follow this pattern:**

1. **Discover** — list entities, get schema, check existing records
2. **Act** — create/insert/update/delete
3. **Verify** — re-read to confirm the operation succeeded

```bash
# 0. Ensure correct tenant
uip login status --output json
uip login tenant set <tenant-name>   # only if needed

# 1. Discover
uip df entities list --output json
uip df entities get <entity-id> --output json

# 2. Act
uip df records insert <entity-id> --body '{"name":"Alice","score":95}' --output json

# 3. Verify
uip df records list <entity-id> --output json
```

---

## Query Request Format

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
  "start": 0,
  "limit": 50
}
```

- `logicalOperator`: `0` = AND, `1` = OR
- Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not contains`, `startswith`, `endswith`, `in`, `not in`

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not logged in` | Auth expired | `uip login` |
| `HTTP 401` | Invalid token | Re-login with required scopes including `DataServiceApiUserAccess` |
| `HTTP 403` | Permission denied | Ensure account has Data Fabric permissions |
| `Entity not found` | Wrong entity ID | Run `entities list` to get correct ID |
| `Record must include 'Id'` | Update missing Id | Add `"Id": "<record-id>"` to the body |
| `No name property` | Invalid field definition | Each field must have at minimum `{"name":"fieldname"}` |
| `Entity name resolution failed` | Query/import with bad ID | Verify entity exists with `entities list` |
| Import errors in CSV | Bad headers or data | Use `entities get` to verify exact field names (case-sensitive) |
| Write to federated entity | Entity backed by external connector | Use `--native-only` to list native entities; federated entities are read-only |
| Asked to create federated entity | Not supported anywhere | Respond: "Creating federated entities is not currently supported — neither via the CLI nor the UiPath portal." |

---

## References

For deeper guidance, read these files only when needed:

- `references/entity-schema.md` — Field definitions, supported types, schema update patterns
- `references/records-query.md` — Query filter syntax, pagination, sorting examples
- `references/file-attachments.md` — File field upload/download/delete workflows
- `references/bulk-import.md` — CSV format requirements and bulk import patterns
