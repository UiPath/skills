# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **A LINQ query in an `Assign` called `.CopyToDataTable()` when the filter matched zero
rows.** The `Assign` "Filter active invoices" runs
`dtInvoices.AsEnumerable().Where(Function(r) r("Status").ToString().Trim() = "Active").CopyToDataTable()`.
On this run none of the loaded rows had `Status = "Active"`, so the `.Where(...)` produced an empty
sequence and `System.Data.DataTableExtensions.CopyToDataTable()` threw
`System.InvalidOperationException: The source contains no data rows.` — `CopyToDataTable()` cannot build
a table from an empty sequence. The job faulted at argument resolution for that `Assign`.

**What went wrong:** The source table was NOT null and NOT empty (42 rows were loaded, per the log) —
the **filter matched none of them**, and the trailing `.CopyToDataTable()` is unguarded, so an empty
result set faults the job instead of yielding an empty table.

**Why:**
- `process/Main.xaml` — the `Assign` "Filter active invoices" (`Assign_FilterActive`): `Assign.To` =
  `dtActive` (`DataTable`), `Assign.Value` = the LINQ chain ending in `.CopyToDataTable()` with no
  `.Any()` / count guard.
- Job log: "Invoice reconciliation started, rows loaded: 42" then the Error — so the source had rows;
  the predicate `r("Status").ToString().Trim() = "Active"` matched zero of them this run.
- Exception: `System.InvalidOperationException: The source contains no data rows.`; stack bottoms out
  in `System.Data.DataTableExtensions.CopyToDataTable` invoked from the workflow's compiled expression
  (`InvoiceReconciliation_Expressions.__Expr1Get` → `InArgument.TryPopulateValue`) — user workflow
  code, not a package.

**Evidence:**
- Job `b8f3c1d2-4a67-4e90-9c15-2d7e6f0a3b58` (process **InvoiceReconciliation**, folder **Shared**, host
  **MOCK-HOST**, ErrorCode `Robot`) ended **Faulted** ~1.7s after start.
- Prior runs on 2026-07-17 and 2026-07-18 were **Successful** — the failure is data-dependent (those
  runs had at least one `Active` row).
- The fault is in the user's `Assign` expression (`CopyToDataTable`), not inside an activity package.

**Immediate fix:**
1. Guard `.CopyToDataTable()` so it only runs when at least one row matches. Compute the filtered rows
   first, then materialize conditionally:
   - `If dtInvoices.AsEnumerable().Where(Function(r) r("Status").ToString().Trim() = "Active").Any()`
     → **Then** assign `dtActive` = `... .CopyToDataTable()`; **Else** `dtActive = dtInvoices.Clone()`
     (an empty table with the same schema) and handle "no active invoices" as an expected path.
2. This keeps the workflow from faulting when a run legitimately has no matching rows.

If, on investigation, the filter should have matched but didn't (a predicate bug rather than a genuine
"no data" run), fix the comparison instead — normalize case/whitespace
(`r("Status").ToString().Trim().Equals("Active", StringComparison.OrdinalIgnoreCase)`), verify the
column name, and compare as the correct type.

**Do NOT** conclude this is a `NullReferenceException` / uninitialized-table problem — the table is
non-null and had 42 rows; the query simply returned zero matches.

**Preventive fix:**
- Never call `.CopyToDataTable()` on a filtered sequence without an `.Any()` guard (or a try/catch that
  yields an empty `.Clone()`), since any filter can legitimately match zero rows on some input.
- Treat "no matching rows" as an expected business condition (log + skip, or `BusinessRuleException`),
  not a crash.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An unguarded `.CopyToDataTable()` in the `Assign` faults because the `.Where` filter matched zero of the loaded rows. | high | confirmed | Yes | `Assign_FilterActive` LINQ ends in `.CopyToDataTable()` with no `.Any()` guard; log shows 42 rows loaded then `InvalidOperationException: The source contains no data rows`; stack bottoms out in `CopyToDataTable`. | Guard with `.Any()` (assign only when matches exist; else `.Clone()` / handle empty). |
| H2 | The source `DataTable` was null (uninitialized) → `NullReferenceException`. | low | eliminated | No | Exception is `InvalidOperationException: The source contains no data rows`, not an NRE; log confirms 42 rows loaded, so the table exists and is populated. | N/A — the table is non-null; guard the empty-result case. |
| H3 | A package/platform bug caused the fault. | low | eliminated | No | Stack bottoms out in `System.Data.DataTableExtensions.CopyToDataTable` invoked from the user's compiled workflow expression, not a `UiPath.*` package. | N/A — fix the user's LINQ expression. |
