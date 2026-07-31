---
confidence: medium
---

# Read CSV — "Line X contains more values than the header line"

## Context

What this looks like:
- `Read CSV` faults with `Line <X> contains more values than the header line` (a `CsvHelper`-surfaced parse error).
- The named line has more fields than the header row, so the parser cannot map the extra value to a column.

What can cause it:
- **Delimiter mismatch.** The activity's `Delimiter` property does not match the file's actual separator (e.g. the file is semicolon- or tab-separated but `Delimiter` is `Comma`). Every separator in a row is counted as a column break, so rows split into more fields than the header.
- **Unescaped / unquoted characters in a field.** A value contains the delimiter character (e.g. a price `1,000` in a comma-separated file) but is not wrapped in quotes, so the parser splits it into extra columns. Conversely, malformed quoting can confuse the parser.
- **Ragged data rows.** Some data rows genuinely have more fields than the header (extra trailing delimiter, concatenated/dirty export).

What to look for:
- The activity's `Delimiter` vs the file's real separator (open the file in a text editor — is it `,`, `;`, or a tab?).
- Whether data fields contain the delimiter character unquoted (numbers like `1,000`, addresses, free text).
- Whether the file is a clean, consistent export or erratic raw data.

## Investigation

1. Read the error and the failing line number from job evidence; confirm it is a `Read CSV` parse error (`contains more values than the header line`), not a file-not-found or format-invalid error.
2. Read the `Read CSV` activity's `Delimiter` and `IgnoreQuotes` properties from the `.xaml`.
3. Inspect the file (text editor): the actual separator, whether fields with embedded delimiters are quoted, and whether the flagged line has extra fields.

## Resolution

- **If the delimiter is wrong:** set the activity's `Delimiter` to match the file exactly (`Comma` / `Semicolon` / `Tab`). This is the most common cause.
- **If fields contain the delimiter and are quoted:** enable `IgnoreQuotes` appropriately so UiPath processes quoted fields correctly (a value like `"1,000"` should be one field, not two).
- **If the field contains the delimiter unquoted:** the source export is malformed — fix the export to quote such fields, or switch to the workaround below.
- **If the raw data is erratic/ragged (workaround):** read the file with **Read Text File** into a string, then parse it with **Generate Data Table** (CSV "Parse" option enabled), which gives you control over delimiter/quoting and tolerates irregular rows better than `Read CSV`.
