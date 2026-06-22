# File Attachments Reference

Data Fabric supports file-type fields on entities. Files are stored per-record per-field.

> **⚠ Do NOT put FILE-typed keys in `records insert`, `records update`, or `records import` payloads.** Expected behavior: the platform silently strips FILE values — paths, base64, filenames, UUIDs, CSV cells, `null` — and returns `Result: Success` with the FILE column unchanged (data-fabric.md Rules 6 and 20). Do not interpret Success as "the file changed." `records update receipt:null` does **not** clear. `records update receipt:"<uuid>"` does **not** swap. Required write path: `records insert` (no FILE column) → capture `Data.Id` → `files upload <entity-id> <record-id> <field-name> --file <path>`. To clear: `files delete`. Never `records update`.

## Creating a FILE field correctly

The FILE field itself must still be created via the CLI before the UI can upload to it. Bind `referenceEntityId` / `referenceFieldId` to the tenant's `EntityAttachment` entity + its `Name` field — any other target produces a column the UI cannot use, with no in-place fix. Discovery snippet and full shape: [`entity-schema.md` → FILE Fields](entity-schema.md#file-fields).

## Prerequisites

1. **The entity must have a FILE field.** Use `uip df entities get <entity-id> --output json` to identify file-type fields. A correctly-defined FILE field shows `FieldDataType.Name: "FILE"`, `FieldDisplayType: "File"`, `IsForeignKey: true`, and `ReferenceEntity.Name == "EntityAttachment"`.
2. **The target record must already exist.** `files upload` writes against a `<record-id>` — create the row first with `records insert` (omit the FILE column — Rule 6) and capture `Data.Id` from the response.
3. **All three `files` commands accept `--folder-key <GUID>`** for records on folder-scoped entities (CLI ≥ `1.197.0`). Required when the parent entity lives in a folder; omit for tenant-scoped entities.

## Upload or Replace a File

`files upload` is the only verb for writing a FILE field. It both **attaches** (when the field is currently empty) and **replaces in place** (when a file is already attached) — no `files delete` is needed first.

```bash
uip df files upload <entity-id> <record-id> <field-name> \
  --file /path/to/document.pdf \
  [--folder-key <folder-guid>] \
  --output json
```

- `<field-name>` is **case-sensitive** — must match exactly the field name from `entities get`
- The record must already exist before uploading
- Pass `--folder-key` when the parent entity is folder-scoped
- Replacing in place: the per-record-per-field UUID handle (the value at `expansionLevel: 0`, or `Document.Id` at level 1+) is preserved across the upload — only the bytes, filename, `Size`, `Type`, and `UpdateTime` change. Don't use the handle to detect content change — compare bytes or watch `UpdateTime`.

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

## What records reads return for a FILE field

The shape depends on the `expansionLevel` used by the call. `records get` and `records list` always run at level `0` (neither verb exposes a way to raise it). `records query` accepts an `expansionLevel` value inside `--body` (default `0`), so the same field can come back two ways:

**`expansionLevel: 0` (default)** — FILE field is a UUID string, or omitted / `null` when no file is attached:

```json
{ "Id": "<record-uuid>", "Document": "16633BC7-F76A-F111-AC99-000D3A98AF8F" }
```

**`expansionLevel: 1` or higher** — FILE field is an object with the attachment metadata:

```json
{
  "Id": "<record-uuid>",
  "Document": {
    "Id": "16633BC7-F76A-F111-AC99-000D3A98AF8F",
    "Name": "file-upload-test.txt",
    "Size": 123,
    "Type": "application/octet-stream",
    "Path": "<entity>/<record-id>/<field-name>",
    "RecordId": "<record-uuid>",
    "EntityId": "<entity-uuid>",
    "FieldId": "<field-uuid>",
    "CreatedBy": "<user-uuid>",
    "UpdatedBy": "<user-uuid>",
    "CreateTime": "<iso8601>",
    "UpdateTime": "<iso8601>"
  }
}
```

Parse by inspecting the field's runtime type (string vs object) — or pin the shape by always setting `expansionLevel` explicitly in the body. The FILE-field object shape is the same at level 1 and level 2; only *related* fields like `UpdatedBy` / `CreatedBy` keep expanding past level 1. Same write rules still apply — the value is read-only metadata:

- Do not use the UUID handle (or `Document.Id`) to detect content change. The handle stays identical across `files upload` calls — the bytes change, the UUID does not. Compare downloaded bytes or watch `UpdateTime` instead.
- Do not try to set, swap, or clear the field via `records insert` / `records update`. Expected behavior: silently dropped (see warning above).
- To check whether a file is attached, look for the field's presence and non-null value. To clear, call `files delete`.

To read the filename through the CLI: query with `expansionLevel: 1` and read `Data.Items[].<field-name>.Name`. `files upload` also returns it as `Data.FileName` on the upload response.

## Full Workflow

```bash
# 1. Discover entity and find a record
uip df entities list --output json
uip df entities get <entity-id> --output json      # see field names

uip df records list <entity-id> --output json      # record IDs; FILE field shown as UUID string

# 2. Upload
uip df files upload <entity-id> <record-id> attachment \
  --file report.pdf --output json
#    → Data.FileName echoes the uploaded filename

# 3. Read filename and metadata (Name, Size, Type, ...) for that record
uip df records query <entity-id> \
  --body '{"expansionLevel":1,"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Id","operator":"=","value":"<record-id>"}]}}' \
  --output json
#    → Data.Items[0].attachment.Name / .Size / .Type / .UpdateTime

# 4. Verify by downloading
uip df files download <entity-id> <record-id> attachment \
  --destination /tmp/report-verify.pdf --output json
```
