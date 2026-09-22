# Final Resolution

---

**Root Cause:** `data/contacts.csv` has a 3-column header (`Id,Name,Amount`), but
row 4's `Amount` value is `1,250` — a comma **inside an unquoted field**. The
`Read CSV` activity runs with `Delimiter=Comma` and `IgnoreQuotes=True`, so the
embedded comma is treated as a field separator: row 4 parses into 4 values
against a 3-column header, and `CsvHelper` throws `Line 4 contains more values
than the header line`.

**What went wrong:** The `CsvIngest` job (started 2026-06-14T08:12:03Z) faulted
~2 seconds in at the `Read CSV` step with `Read CSV: Line 4 contains more values
than the header line` (`CsvHelper.MissingFieldException`). Line 4 of the file is
`103,Initech,1,250` — the `1,250` makes four comma-separated tokens where the
header defines three columns.

**Why:** `Read CSV` splits each line on the `Delimiter`. A field that itself
contains the delimiter must be **quoted** so the parser treats it as one value.
Here `IgnoreQuotes=True` tells the parser **not** to honor quotes, so even a
properly quoted `"1,250"` would be split — and the source value isn't quoted at
all. The result is a row with more values than the header. The same error also
appears when the activity's `Delimiter` doesn't match the file's real separator
(e.g. a semicolon/tab file read as comma).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvIngest -- Faulted at 2026-06-14T08:12:05.330Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Imports (key `da010001-d4e5-4f60-8a01-000000000001`)
- Final error: `Read CSV: Line 4 contains more values than the header line.` (`CsvHelper.MissingFieldException`) -> `Main.xaml` -> `ReadCsvFile "Read CSV"`

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.ReadCsvFile` (Read CSV), `Delimiter=Comma`, `AddHeaders=True`, `IgnoreQuotes=True`.
- `data/contacts.csv` line 4 is `103,Initech,1,250` — four comma tokens vs the 3-column header `Id,Name,Amount`. The `1,250` is the unquoted embedded comma.

---

**Immediate fix:**

Make the embedded-comma field parse as a single value (or use a tolerant parse).

### Fix path A -- honor quotes / quote the field (preferred for this file)
The `Amount` value should be quoted in the source (`"1,250"`), and the activity
must **honor quotes** — turn **off** `IgnoreQuotes` so quoted fields are treated
as one value. (`IgnoreQuotes=True` is what makes a quoted `"1,250"` still split.)

### Fix path B -- correct the Delimiter
If the file's real separator is not a comma (e.g. it is semicolon- or
tab-separated and the commas are only inside values), set the activity's
`Delimiter` to match the file (`Semicolon` / `Tab`) so the embedded commas are no
longer treated as separators.

### Fix path C -- tolerant parse (erratic data)
If the source export is irregular and can't be fixed, read the file with **Read
Text File** into a string and parse it with **Generate Data Table** (CSV "Parse"
option), which gives explicit control over delimiter/quoting.

### Verification
Open `data/contacts.csv` and confirm line 4 (`103,Initech,1,250`) has the extra
comma; after quoting the field and honoring quotes (or fixing the delimiter), the
row parses as 3 values and `Read CSV` succeeds.

- **Source:** `csv-activities/playbooks/read-csv-more-values-than-header.md`

---

**Preventive fix:**

1. **Source export** -- ensure fields that can contain the delimiter (amounts,
   names, addresses) are quoted in the CSV, and read with quotes honored.
   - **Why:** Unquoted embedded delimiters are the most common Read CSV parse
     failure.
   - **Who:** RPA developer / data provider.

2. **Robustness** -- for third-party feeds with unpredictable formatting, prefer
   Read Text File → Generate Data Table so delimiter/quote handling is explicit.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An unquoted comma in row 4's Amount field (1,250), read with Delimiter=Comma and IgnoreQuotes=True, parses into more fields than the header | High | Confirmed | Yes | `Line 4 contains more values than the header line`; contacts.csv line 4 `103,Initech,1,250`; IgnoreQuotes=True | Quote the field and honor quotes (turn off IgnoreQuotes), or set the correct Delimiter, or Read Text File -> Generate Data Table |

---

Would you like help adjusting the Read CSV quoting/delimiter settings, or
cleaning up the `.local/investigations/` folder?
