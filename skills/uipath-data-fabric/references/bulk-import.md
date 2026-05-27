# Bulk Import Reference

## Import Records from CSV

```bash
uip df records import <entity-id> --file data.csv --output json
```

Response: `{ Code: "RecordsImported", Data: { InsertedRecords, TotalRecords, ErrorFileLink? } }`

- `InsertedRecords` — number of rows successfully imported
- `TotalRecords` — total rows in the CSV (including failures)
- `ErrorFileLink` — download URL for a CSV of failed rows (only present if there were failures)

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

### Complex Field Types Are Silently Dropped

**Complex field types** in Data Fabric are the ones that need extra config or lookup tokens beyond the value itself: `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER`. Everything else is a Basic type.

`records import` only processes Basic types (`STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `MULTILINE_TEXT`, `UUID`). Columns for the complex types listed above are accepted in the header but the row values are discarded — no error, nothing in `ErrorFileLink`, just `null` on every imported row (or row failure if the field is `isRequired` without a `defaultValue`).

For entities with any complex field, use `records insert --file <json>` instead — the insert endpoint handles all types. See [`records-query.md`](records-query.md#writing-choice-set-and-relationship-values) for the value form.

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
