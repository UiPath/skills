# File Attachments Reference

Data Fabric stores FILE fields per record and field.

> **⚠ Do NOT put FILE-typed keys in `records insert`, `records update`, or `records import` payloads.** The platform silently strips FILE values—paths, base64, filenames, UUIDs, CSV cells, and `null`—and returns `Result: Success` with the FILE column unchanged (data-fabric.md Rules 6 and 20). Do not interpret Success as "the file changed." `records update receipt:null` does **not** clear, and `records update receipt:"<uuid>"` does **not** swap. Run `records insert` without the FILE column, capture `Data.Id`, then run `files upload <entity-id> <record-id> <field-name> --file <path>`. Run `files delete` to clear. Never use `records update` for FILE values.

## Creating a FILE field

When creating a FILE field through the CLI, use only `{"name":"X","type":"FILE"}`. The server auto-wires the `EntityAttachment` binding. See [`entity-schema.md` → FILE Fields](entity-schema.md#file-fields).

## Prerequisites

1. Run `uip df entities get <entity-id> --output json` and verify a FILE field with `FieldDataType.Name: "FILE"`, `FieldDisplayType: "File"`, `IsForeignKey: true`, and `ReferenceEntity.Name == "EntityAttachment"`.
2. Run `records insert` without the FILE column (Rule 6), capture `Data.Id`, and use it as `<record-id>`; `files upload` requires an existing record.
3. Pass `--folder-key <GUID>` to all three `files` commands when the parent entity is in a folder; omit it for tenant-scoped entities.

## Upload or replace a file

Run `files upload` to attach or replace a file; do not run `files delete` first.

```bash
uip df files upload <entity-id> <record-id> <field-name> \
  --file /path/to/document.pdf \
  [--folder-key <folder-guid>] \
  --output json
```

Use the case-sensitive `<field-name>` returned by `entities get`. The record must exist, and folder-scoped entities require `--folder-key`.

The per-record-per-field UUID handle—the value at `expansionLevel: 0`, or `Document.Id` at level 1+—is preserved when replacing a file. Only the bytes, filename, `Size`, `Type`, and `UpdateTime` change. Do not use the handle to detect content changes; compare bytes or watch `UpdateTime`.

Response: `{ Code: "FileUploaded", Data: { EntityId, RecordId, FieldName, FileName } }`

## Download a file

```bash
uip df files download <entity-id> <record-id> <field-name> \
  --destination /path/to/save/document.pdf \
  [--folder-key <folder-guid>] \
  --output json
```

If `--destination` is omitted, the file is saved as `<record-id>_<field-name>.bin` in the current directory.

Response: `{ Code: "FileDownloaded", Data: { EntityId, RecordId, FieldName, OutputPath } }`

## Delete a file

```bash
uip df files delete <entity-id> <record-id> <field-name> \
  [--folder-key <folder-guid>] \
  --yes --reason "<why>" \
  --output json
```

Response: `{ Code: "FileDeleted", Data: { EntityId, RecordId, FieldName, Reason } }`; `Reason` echoes `--reason`.

## FILE fields in record reads

`records get` and `records list` always use `expansionLevel: 0`. `records query` accepts `expansionLevel` inside `--body` and defaults to `0`.

At `expansionLevel: 0`, a FILE field is a UUID string, or is omitted / `null` when empty:

```json
{ "Id": "<record-uuid>", "Document": "16633BC7-F76A-F111-AC99-000D3A98AF8F" }
```

At `expansionLevel: 1` or higher, it is an attachment-metadata object:

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

Inspect the runtime type (string versus object), or set `expansionLevel` explicitly in the query body. The FILE object shape is the same at levels 1 and 2; only related fields such as `UpdatedBy` and `CreatedBy` expand beyond level 1.

Treat read values as read-only metadata:

- Do not use the UUID handle or `Document.Id` to detect content changes; it remains identical across `files upload` calls. Compare downloaded bytes or watch `UpdateTime`.
- Do not set, swap, or clear FILE fields through `records insert` or `records update`; values are silently dropped (Rules 6 and 20).
- Check attachment status by the field's presence and non-null value. Run `files delete` to clear it.

Run a query with `expansionLevel: 1` and read `Data.Items[].<field-name>.Name` to obtain the filename. `files upload` also returns it as `Data.FileName`; run `files download` to verify bytes when content matters.