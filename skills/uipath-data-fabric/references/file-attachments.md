# File Attachments Reference

Data Fabric supports file-type fields on entities. Files are stored per-record per-field.

## Prerequisites

The entity must have a field configured for file storage. File fields are defined in the entity schema.
Use `uip df entities get <entity-id> --format json` to identify file-type fields.

## Upload a File

```bash
uip df files upload <entity-id> <record-id> <field-name> \
  --file /path/to/document.pdf \
  --format json
```

- `<field-name>` is **case-sensitive** — must match exactly the field name from `entities get`
- The record must already exist before uploading

Response: `{ Code: "FileUploaded", Data: { EntityId, RecordId, FieldName, FileName } }`

## Download a File

```bash
uip df files download <entity-id> <record-id> <field-name> \
  --output /path/to/save/document.pdf \
  --format json
```

- If `--output` is omitted, the file is saved using the original filename or `<field-name>.bin`

Response: `{ Code: "FileDownloaded", Data: { OutputPath, ContentType } }`

## Delete a File

```bash
uip df files delete <entity-id> <record-id> <field-name> --format json
```

Response: `{ Code: "FileDeleted" }`

## Full Workflow

```bash
# 1. Discover entity and find a record
uip df entities list --format json
uip df entities get <entity-id> --format json      # see field names

uip df records list <entity-id> --format json      # get record IDs

# 2. Upload
uip df files upload <entity-id> <record-id> attachment \
  --file report.pdf --format json

# 3. Verify by downloading
uip df files download <entity-id> <record-id> attachment \
  --output /tmp/report-verify.pdf --format json
```
