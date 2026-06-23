# Bulk Import Reference

> **⚠ `records import` does not support complex field types — surface this to the user before invoking (SKILL.md Rule 20).** `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` columns are **not supported**: the CSV header is accepted but the values are ignored (no error, no `ErrorFileLink` entry — `null` on every imported row, or row failure if the field is `isRequired` without a `defaultValue`). This is current Data Fabric platform behavior, not a bug — do not work around it. Run `entities get <entity-id>` first; if any field is in that set, switch to `records insert --file <json>` (handles all types except `FILE` — use `files upload` for those, see Rule 6). See [Complex Field Types Not Supported](#complex-field-types-not-supported) below.

## Import Records from CSV

```bash
uip df records import <entity-id> --file data.csv [--folder-key <folder-guid>] --output json
```

Response: `{ Code: "RecordsImported", Data: { InsertedRecords, TotalRecords, ErrorFileLink? } }`

- `InsertedRecords` — number of rows successfully imported
- `TotalRecords` — total rows in the CSV (including failures)
- `ErrorFileLink` — download URL for a CSV of failed rows (only present if there were failures)
- `--folder-key` — required when the parent entity is folder-scoped (CLI ≥ `1.197.0`)

**Pre-flight check (required by Rule 20):**

```bash
# Inspect schema before importing — tell the user which columns will be dropped
uip df entities get <entity-id> --output json
# Flag every field whose Fields[].fieldDataType.Name ∈ {CHOICE_SET_SINGLE, CHOICE_SET_MULTIPLE, RELATIONSHIP, FILE, AUTO_NUMBER}
```

## CSV Format Requirements

- **Header row is required** and must exactly match entity field names (case-sensitive)
- Use `uip df entities get <entity-id> --output json` to discover exact field names before importing
- System fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`) must NOT appear in the CSV

### Example CSV

```csv
Name,Score,Active,CreatedDate
Alice,95,true,2024-01-15
Bob,82,true,2024-02-20
Charlie,74,false,2024-03-05
```

For an entity with fields: `Name` (STRING), `Score` (INTEGER), `Active` (BOOLEAN), `CreatedDate` (DATE).

### Complex Field Types Not Supported

**Complex field types** in Data Fabric are the ones that need extra config or lookup tokens beyond the value itself: `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER`. Everything else is a Basic type.

`records import` is **not supported** for those complex types — it only processes Basic types (`STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `MULTILINE_TEXT`, `UUID`). The complex-type columns are accepted in the CSV header but their row values are ignored — no error, nothing in `ErrorFileLink`, just `null` on every imported row (or row failure if the field is `isRequired` without a `defaultValue`).

For entities with any complex field, use `records insert --file <json>` instead — the insert endpoint handles every type except `FILE` (which is exclusively written through `files upload`, SKILL.md Rule 6). See [`records-query.md`](records-query.md#writing-choice-set-and-relationship-values) for the value form.

## Full Workflow

```bash
# 1. Discover entity and field names
uip df entities list --output json
uip df entities get <entity-id> --output json   # note exact field names

# 2. Create CSV with matching headers
cat > /tmp/data.csv <<EOF
Name,Score,Active
Alice,95,true
Bob,82,true
EOF

# 3. Import
uip df records import <entity-id> --file /tmp/data.csv --output json

# 4. Verify
uip df records list <entity-id> --output json
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Import errors in CSV` | Header names don't match field names | Run `entities get` and check exact field names (case-sensitive) |
| `Entity not found` | Wrong entity ID | Run `entities list` to get correct ID |
| Row-level errors | Invalid data types (e.g. text in number field) | Check data values match field types |

## Notes

- Partial success is possible: some rows may import while others fail
- Check `InsertedRecords` vs `TotalRecords` to detect failures; download `ErrorFileLink` for the failed-row CSV
- Large imports are processed server-side; there is no row limit documented but keep files reasonable in size
