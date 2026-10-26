# Bulk Import Reference

> **Creating the entity FROM the CSV?** If no entity exists and the user wants one built around CSV columns, use `entities create`; field types must be **confirmed, not silently inferred**. See [`data-fabric.md` Rule 14 → CSV / sample-data inference](data-fabric.md#critical-rules). Flag every inferred type with its sample value(s), surface ambiguous columns (date-shaped strings, `0`/`1` flags, UUID-shaped strings, decimal precision) as `AskUserQuestion` dropdowns, and wait for explicit user approval before invoking `entities create`. *Then* run `records import` to load the data.

> **⚠ `records import` does not support complex field types — surface this to the user before invoking (data-fabric.md Rule 20).** `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` columns are accepted in headers but values are ignored: no error or `ErrorFileLink` entry, `null` on every imported row, or row failure when `isRequired` lacks a `defaultValue`. This is current Data Fabric platform behavior, not a bug — do not work around it. Run `entities get <entity-id>` first. If any field is in that set, run `records insert --file <json>` instead (handles all types except `FILE`; run `files upload` for those, see Rule 6). See [Complex Field Types Not Supported](#complex-field-types-not-supported).

## Import Records from CSV

Run:

```bash
uip df records import <entity-id> --file data.csv [--folder-key <folder-guid>] --output json
```

Response: `{ Code: "RecordsImported", Data: { InsertedRecords, TotalRecords, ErrorFileLink? } }`

- `InsertedRecords`: successfully imported rows; `TotalRecords`: all CSV rows, including failures.
- `ErrorFileLink`: failed-row CSV download URL, present only when failures occur.
- `--folder-key`: required when the parent entity is folder-scoped.

**Pre-flight check (required by Rule 20):**

```bash
# Inspect schema before importing — tell the user which columns will be ignored
uip df entities get <entity-id> --output json
# Flag every field whose Fields[].fieldDataType.Name ∈ {CHOICE_SET_SINGLE, CHOICE_SET_MULTIPLE, RELATIONSHIP, FILE, AUTO_NUMBER}
```

## CSV Format Requirements

- **Header row is required** and must exactly match each field's `DisplayName`
  (case-sensitive), not its internal `Name`. For example, a field returned as
  `{ "Name": "SKU", "DisplayName": "Stock-Keeping Unit" }` requires the CSV
  header `Stock-Keeping Unit`; `SKU` is rejected as an invalid header.
- Run `uip df entities get <entity-id> --output json` to discover exact `Fields[].DisplayName` values.
- Exclude system fields: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`.
- Do not include line breaks or `""` inside quoted cells. `records import` refuses the file and uploads nothing; run `records insert --file <json>` to store such text exactly ([`records-query.md` → Insert Records](records-query.md#insert-records)). Do not strip those characters, as that changes the user's data.

### Example CSV

```csv
Name,Score,Active,CreatedDate
Alice,95,true,2024-01-15
Bob,82,true,2024-02-20
Charlie,74,false,2024-03-05
```

For an entity with fields: `Name` (STRING), `Score` (DECIMAL, `decimalPrecision: 0`), `Active` (BOOLEAN), `CreatedDate` (DATE).

### Complex Field Types Not Supported

Data Fabric complex types requiring extra configuration or lookup tokens are `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER`; all others are Basic types. `records import` processes only Basic types (use the UI-compatible set from [`entity-schema.md`](entity-schema.md#supported-field-types)). Complex columns are accepted in headers, but values are ignored: no error and nothing in `ErrorFileLink`, only `null` on every imported row, or row failure when `isRequired` lacks a `defaultValue`.

For an entity with any complex field, run `records insert --file <json>` instead. It handles every type except `FILE`, which is exclusively written through `files upload` (data-fabric.md Rule 6). See [`records-query.md`](records-query.md#writing-choice-set-and-relationship-values) for the value form.

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `Import errors in CSV` / `Invalid column header` | Header differs from case-sensitive field display names | Run `entities get` and use exact `Fields[].DisplayName`, not internal `Name` values |
| `Entity not found` | Wrong entity ID | Run `entities list` to get the correct ID |
| Row-level errors | Invalid data types, such as text in a number field | Check values against field types |

## Notes

- Partial success is possible; compare `InsertedRecords` with `TotalRecords` and download `ErrorFileLink` for failed rows.
- Large imports are processed server-side. No row limit is documented; keep files reasonable in size.