# File Attachments Reference

Data Fabric supports file-type fields on entities. Files are stored per-record per-field.

> **⚠ Do NOT put FILE-typed keys in `records insert`, `records update`, or `records import` payloads.** Expected behavior: the platform silently strips FILE values — paths, base64, filenames, UUIDs, CSV cells, `null` — and returns `Result: Success` with the FILE column unchanged (SKILL.md Rules 6 and 20). Do not interpret Success as "the file changed." `records update receipt:null` does **not** clear. `records update receipt:"<uuid>"` does **not** swap. Required write path: `records insert` (no FILE column) → capture `Data.Id` → `files upload <entity-id> <record-id> <field-name> --file <path>`. To clear: `files delete`. Never `records update`.

## Creating a FILE field correctly

The FILE field itself must still be created via the CLI before the UI can upload to it. Bind `referenceEntityId` / `referenceFieldId` to the tenant's `EntityAttachment` entity + its `Name` field — any other target produces a column the UI cannot use, with no in-place fix. Discovery snippet and full shape: [`entity-schema.md` → FILE Fields](entity-schema.md#file-fields).

## Prerequisites

The entity must have a field configured for file storage. File fields are defined in the entity schema.
Use `uip df entities get <entity-id> --output json` to identify file-type fields. A correctly-defined FILE field shows `FieldDataType.Name: "FILE"`, `FieldDisplayType: "File"`, `IsForeignKey: true`, and `ReferenceEntity.Name == "EntityAttachment"`.

All three commands accept `--folder-key <GUID>` for records on folder-scoped entities (CLI ≥ `1.197.0`). Required when the parent entity lives in a folder; omit for tenant-scoped entities.

## Upload a File

```bash
uip df files upload <entity-id> <record-id> <field-name> \
  --file /path/to/document.pdf \
  [--folder-key <folder-guid>] \
  --output json
```

- `<field-name>` is **case-sensitive** — must match exactly the field name from `entities get`
- The record must already exist before uploading
- Pass `--folder-key` when the parent entity is folder-scoped

Response: `{ Code: "FileUploaded", Data: { EntityId, RecordId, FieldName, FileName } }`

## Download a File

```bash
uip df files download <entity-id> <record-id> <field-name> \
  --destination /path/to/save/document.pdf \
  [--folder-key <folder-guid>] \
  --output json
```

- If `--destination` is omitted, the file is saved as `<record-id>_<field-name>.bin` in the current directory

Response: `{ Code: "FileDownloaded", Data: { EntityId, RecordId, FieldName, OutputPath } }`

## Delete a File

```bash
uip df files delete <entity-id> <record-id> <field-name> \
  [--folder-key <folder-guid>] \
  --yes --reason "<why>" \
  --output json
```

Response: `{ Code: "FileDeleted", Data: { EntityId, RecordId, FieldName, Reason } }` — `Reason` echoes the `--reason` value.

## What `records get` returns for a FILE field

`records get` returns the FILE field as a UUID string, or omits it / returns `null` when no file is attached. This UUID is a **stable per-record-per-field handle**. Treat it as read-only metadata:

- Do not use it to detect content change. The handle stays identical across `files upload` calls — the bytes change, the UUID does not. Compare downloaded bytes or watch `UpdateTime` instead.
- Do not try to set, swap, or clear it via `records insert` / `records update`. Expected behavior: silently dropped (see warning above).
- Use it only as a presence check (attached vs not). To clear, call `files delete`.

The filename is not in the `records get` response. It is returned only by `files upload` (`Data.FileName`) and cannot be read back through any verb in the current CLI surface.

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
