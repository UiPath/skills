# Bulk Import Reference

> **Creating the entity FROM the CSV?** If no entity exists and the user wants one built from the CSV columns, use `entities create`; field types must be **confirmed, not silently inferred**. See [`data-fabric.md` Rule 14 → CSV / sample-data inference](data-fabric.md#critical-rules). Flag every inferred type with its sample value(s), surface ambiguous columns (date-shaped strings, `0`/`1` flags, UUID-shaped strings, decimal precision) as `AskUserQuestion` dropdowns, and wait for explicit approval before invoking `entities create`. Then run `records import` to load the data.

> **⚠ `records import` does not support complex field types — surface this before invoking it (data-fabric.md Rule 20).** `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` columns accept headers but ignore values without errors or `ErrorFileLink` entries, producing `null` on every imported row. A row fails when such a field is `isRequired` without a `defaultValue`. Run `entities get <entity-id>` first. If any field is in that set, use `records insert --file <json>` instead; it handles all types except `FILE`, which requires `files upload` (see Rule 6). See [Complex Field Types Not Supported](#complex-field-types-not-supported).

## Import Records from CSV

Run:

```bash
uip df records import <entity-id> --file data.csv [--folder-key <folder-guid>] --output json
```

Run this first:

```bash
uip df entities get <entity-id> --output json
```

Use `--folder-key` for folder-scoped parent entities. The response is `{ Code: "RecordsImported", Data: { InsertedRecords, TotalRecords, ErrorFileLink? } }`:

- `InsertedRecords`: successfully imported rows.
- `TotalRecords`: all CSV rows, including failures.
- `ErrorFileLink`: failed-row CSV download URL, present only when failures occur.

Tell the user which columns will be ignored. Flag every `Fields[].fieldDataType.Name` in `{CHOICE_SET_SINGLE, CHOICE_SET_MULTIPLE, RELATIONSHIP, FILE, AUTO_NUMBER}`.

## CSV Format Requirements

- Require a header row matching each field's `DisplayName` exactly and case-sensitively, not its internal `Name`. For `{ "Name": "SKU", "DisplayName": "Stock-Keeping Unit" }`, use `Stock-Keeping Unit`.
- Run `uip df entities get <entity-id> --output json` to discover exact `Fields[].DisplayName` values.
- Do not include system fields: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`.

### Complex Field Types Not Supported

`CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` require configuration or lookup tokens beyond a scalar value; all other types are Basic types. `records import` processes only Basic types. Complex-type values become `null` without errors or `ErrorFileLink` entries, unless an `isRequired` field lacks a `defaultValue`, which causes row failure.

For an entity containing any complex field, use `records insert --file <json>`. It handles every type except `FILE`; write `FILE` values exclusively through `files upload` (data-fabric.md Rule 6). See [`records-query.md`](records-query.md#writing-choice-set-and-relationship-values) for value forms and [`entity-schema.md`](entity-schema.md#supported-field-types) for the UI-compatible supported-field set.

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `Import errors in CSV` / `Invalid column header` | Headers do not match field display names | Run `entities get` and use exact, case-sensitive `Fields[].DisplayName`, not internal `Name` |
| `Entity not found` | Wrong entity ID | Run `entities list` to get the correct ID |
| Row-level errors | Values do not match field types, such as text in a number field | Correct the data types |

## Notes

- Partial success is possible.
- Compare `InsertedRecords` with `TotalRecords`; download `ErrorFileLink` for failed rows.
- Imports are processed server-side. No row limit is documented; keep files reasonably sized.