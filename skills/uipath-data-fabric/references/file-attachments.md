# File Attachments Reference

Data Fabric supports file-type fields on entities. Files are stored per-record per-field.

## Prerequisites

The entity must have a field configured for file storage. File fields are defined in the entity schema.
Use `uip df entities get <entity-id> --output json` to identify file-type fields.

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
uip df files delete <entity-id> <record-id> <field-name> --output json
```

Response: `{ Code: "FileDeleted", Data: { EntityId, RecordId, FieldName } }`

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
