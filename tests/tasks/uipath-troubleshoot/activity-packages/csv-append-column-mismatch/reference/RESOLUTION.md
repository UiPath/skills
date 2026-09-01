# Final Resolution

---

**Root Cause:** The workflow builds a **2-column** `DataTable` (`OrderId`,
`Customer`) and appends it to `data\orders.csv`, which has **3 columns**
(`OrderId`, `Customer`, `Total`). The column counts/headers do not match, so
`Append To CSV` cannot align the incoming rows with the file's structure and
faults with a column-mismatch error.

**What went wrong:** The `CsvMerger` job (started 2026-06-13T11:11:08Z)
initialized the `DataTable` and added the `OrderId` and `Customer` columns
(logged), then faulted at `Append To CSV` with `The input DataTable has 2
column(s) but the existing file 'data\orders.csv' has 3 column(s) (OrderId,
Customer, Total). The rows cannot be appended because the column structure does
not match.` The `Total` column present in the file is missing from the
DataTable.

**Why:** `Append To CSV` writes a `DataTable`'s rows to the end of an existing
file; the table's columns must correspond to the file's columns. When the
incoming table has fewer (or differently named/ordered) columns than the file,
the rows cannot be mapped and the activity errors. This is a data-shape problem
in the workflow, not a dependency (`CsvHelper`) or file-lock issue.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvMerger -- Faulted at 2026-06-13T11:11:10.330Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Data Integration (key `ca030003-d4e5-4f60-8a03-000000000003`)
- Final error: `Append To CSV: The input DataTable has 2 column(s) but the existing file 'data\orders.csv' has 3 column(s) (OrderId, Customer, Total) ...` -> `Main.xaml` -> `AppendToCsvFile "Append To CSV"`

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.AppendToCsvFile` (Append To CSV).
- `Main.xaml` initializes a `DataTable` and adds only two columns via `Add Data Column` (`OrderId`, `Customer`); the logs confirm both were added before the append.
- The existing `orders.csv` has three columns (`OrderId`, `Customer`, `Total`). The missing `Total` column is the mismatch.

---

**Immediate fix:**

Make the input `DataTable`'s columns match the existing CSV.

### Fix path A -- align the DataTable schema (preferred)
Define the `DataTable` with the **same columns (names, order, count)** as
`orders.csv` — add the missing `Total` column (a third `Add Data Column`
`Total`, or lay out the full schema with a **Build Data Table** activity using
identical headers) before populating rows, so the structure matches the file.

### Fix path B -- write a consistent schema from the start
If the workflow owns the file format, ensure every writer (initial Write CSV and
subsequent Append To CSV) uses the same column set, so appends always align.

### Verification (hand to the user - off-host)
Open `orders.csv` and confirm its header is `OrderId,Customer,Total`. After the
DataTable is built with those three columns (in that order), the append lines up
and succeeds.

- **Source:** `csv-activities/playbooks/csv-datatable-structure-mismatch.md`

---

**Preventive fix:**

1. **Workflow** -- build the `DataTable` from the file's header (or a shared
   schema definition) rather than hand-adding a subset of columns, so the
   structure can't drift from the target CSV.
   - **Why:** A column count/order/name drift between the DataTable and the file
     is the recurring cause of append mismatches.
   - **Who:** RPA developer.

2. **Validation** -- assert the DataTable's column count equals the file's before
   the append, and fail fast with a clear message if not.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The input DataTable (OrderId, Customer) has fewer columns than the existing orders.csv (OrderId, Customer, Total), so Append To CSV cannot align the rows | High | Confirmed | Yes | Append To CSV error "input DataTable has 2 column(s) but file has 3 (OrderId, Customer, Total)"; Main.xaml adds only 2 columns | Align the DataTable to the file's columns (add Total / Build Data Table with identical headers) |

---

Would you like help aligning the DataTable schema to the file header, or cleaning
up the `.local/investigations/` folder?
