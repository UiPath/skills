# File Attachments Reference

Data Fabric supports file-type fields on entities. Files are stored per-record per-field. End-to-end upload / download / delete via `uip df files` works against any FILE field bound to the tenant's internal `EntityAttachment` entity (the only target shape the platform accepts).

## Creating a FILE field correctly

The FILE field must be created via the CLI before any upload. Bind `referenceEntityId` / `referenceFieldId` to the tenant's `EntityAttachment` entity + its `Name` field — any other target produces a column the UI cannot use AND uploads will fault with `"Update entity data failed. Relationship violation"`. Discovery snippet and full shape: [`entity-schema.md` → FILE Fields](entity-schema.md#file-fields).

## Prerequisites

The entity must have a field configured for file storage. File fields are defined in the entity schema.
Use `uip df entities get <entity-id> --output json` to identify file-type fields. A correctly-defined FILE field shows `FieldDataType.Name: "FILE"`, `FieldDisplayType: "File"`, `IsForeignKey: true`, and `ReferenceEntity.Name == "EntityAttachment"`.

After a successful upload, the file's UUID is written to the record's FILE-field column (`records get` echoes `"<FieldName>": "<file-uuid>"`). `files delete` clears that column.

## Upload a File

```bash
uip df files upload <entity-id> <record-id> <field-name> \
  --file /path/to/document.pdf \
  --output json
```

- `<field-name>` is **case-sensitive** — must match exactly the field name from `entities get`
- The record must already exist before uploading

Response: `{ Code: "FileUploaded", Data: { EntityId, RecordId, FieldName, FileName } }`

## Download a File

```bash
uip df files download <entity-id> <record-id> <field-name> \
  --destination /path/to/save/document.pdf \
  --output json
```

- If `--destination` is omitted, the file is saved as `<record-id>_<field-name>.bin` in the current directory

Response: `{ Code: "FileDownloaded", Data: { EntityId, RecordId, FieldName, OutputPath } }`

## Delete a File

```bash
uip df files delete <entity-id> <record-id> <field-name> --yes --reason "<why>" --output json
```

Irreversible — `--yes` and `--reason` are both required. Omitting `--yes` → `"Confirmation required: this will delete the file in field '<field>' and cannot be undone."`; omitting `--reason` → `"Reason required for destructive operation"`. `--reason` is echoed back in `Data.Reason`. The operation also clears the FILE-field column on the record (subsequent `records get` shows `"<FieldName>": null`).

Response: `{ Code: "FileDeleted", Data: { EntityId, RecordId, FieldName, Reason } }`

## Folder Scope

All three `files` verbs accept `--folder-key <uuid>`. The flag is **advisory** — the server resolves the record by UUID regardless of scope — but pass it defensively on `files delete` and on uploads/downloads against folder-scoped entities. Full scope matrix: **SKILL.md → Scope — Tenant vs Folder**.

```bash
uip df files upload   <entity-id> <record-id> <field-name> --file path --folder-key <uuid> --output json
uip df files download <entity-id> <record-id> <field-name> --destination path --folder-key <uuid> --output json
uip df files delete   <entity-id> <record-id> <field-name> --yes --reason "<why>" --folder-key <uuid> --output json
```

## Full Workflow

```bash
# 1. Discover entity and find a record
uip df entities list --output json
uip df entities get <entity-id> --output json      # see field names

uip df records list <entity-id> --output json      # get record IDs

# 2. Upload
uip df files upload <entity-id> <record-id> attachment \
  --file report.pdf --output json

# 3. Verify by downloading
uip df files download <entity-id> <record-id> attachment \
  --destination /tmp/report-verify.pdf --output json
```
