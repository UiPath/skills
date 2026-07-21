# Final Resolution

---

**Root Cause:** `data/feed.csv` begins with **two blank lines** before the
`Id,Sku,Qty` header row. The `Read CSV` activity runs with `AddHeaders=True`,
which expects the header (or first data row) at the top of the file. The leading
empty rows break the tabular structure, so the activity faults with `The CSV file
format for 'data\feed.csv' is invalid`.

**What went wrong:** The `FeedLoader` job (started 2026-06-14T10:41:18Z) faulted
~2 seconds in at the `Read CSV` step with `Read CSV: The CSV file format for
'data\feed.csv' is invalid` (`System.IO.InvalidDataException`). The file's first
two lines are empty; the real header `Id,Sku,Qty` is on line 3.

**Why:** `Read CSV` resolves the header/columns from the first content of the
file. Leading blank lines mean the first line it reads is empty, so it cannot
establish a valid header/column layout — hence "invalid format". A related cause
is a `Has headers` / `AddHeaders` setting that disagrees with the file (checked
when there is no title row, so the first data row is consumed as headers; or
unchecked when there is one, so titles are read as data). Here the file does have
a header — the problem is the empty rows above it.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: FeedLoader -- Faulted at 2026-06-14T10:41:20.300Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Feeds (key `da020002-d4e5-4f60-8a02-000000000002`)
- Final error: `Read CSV: The CSV file format for 'data\feed.csv' is invalid.` (`System.IO.InvalidDataException`) -> `Main.xaml` -> `ReadCsvFile "Read CSV"`

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.ReadCsvFile` (Read CSV), `AddHeaders=True`.
- `data/feed.csv` starts with two empty lines; the header `Id,Sku,Qty` is on line 3, followed by the data rows. The leading blanks are the structural problem.

---

**Immediate fix:**

Make the file start at the header row (and keep `Has headers` consistent).

### Fix path A -- strip the leading blank lines (preferred)
Remove the empty rows at the top of `feed.csv` so the header `Id,Sku,Qty` is line
1. If the source produces the blanks, trim them in the workflow before reading:
**Read Text File** → remove leading newlines with string activities → feed the
cleaned text to **Generate Data Table** (or write it back, then `Read CSV`).

### Fix path B -- align Has headers with the file
Ensure `Has headers` / `AddHeaders` matches the file: checked when there is a
title row, unchecked when the data has no titles. (Here the file has a header, so
keep it checked once the blank lines are removed.)

### Verification
Open `data/feed.csv` in a plain text editor and confirm the two empty lines
above the header; after removing them, `Read CSV` resolves the `Id,Sku,Qty`
header and succeeds.

- **Source:** `csv-activities/playbooks/read-csv-invalid-format.md`

---

**Preventive fix:**

1. **Source / pre-clean** -- trim leading blank lines from inbound files before
   `Read CSV` (Read Text File → strip → Generate Data Table), especially for
   third-party feeds.
   - **Why:** Leading blank rows are a common "invalid format" trigger that the
     file viewer hides.
   - **Who:** RPA developer.

2. **Property hygiene** -- set `Has headers`/`AddHeaders` deliberately to match
   each source's actual layout.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Leading blank lines at the top of feed.csv (with AddHeaders=True) break header detection, so Read CSV reports invalid format | High | Confirmed | Yes | `The CSV file format for 'data\feed.csv' is invalid`; feed.csv has two empty lines before the Id,Sku,Qty header | Strip the leading blank lines (or pre-clean via Read Text File -> Generate Data Table); keep Has headers consistent with the file |

---

Would you like help adding a leading-blank-line trim before the Read CSV, or
cleaning up the `.local/investigations/` folder?
