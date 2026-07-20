---
confidence: high
---

# Assign — "The source contains no data rows" (LINQ / CopyToDataTable)

## Context

A workflow faults at runtime inside an `Assign` (or an expression) that runs a LINQ query over a
`DataTable` and calls `.CopyToDataTable()` when the query matched **zero rows**.
`System.Data.DataTableExtensions.CopyToDataTable()` throws when its source sequence is empty — it
cannot build a `DataTable` with no schema/rows to copy.

What this looks like (quote verbatim — routing greps for these):
- `System.InvalidOperationException: The source contains no data rows.`
- Error message fragment: `The source contains no data rows`
- The faulted activity is an `Assign` (or a filter/query step) in the user's workflow; the stack trace
  bottoms out in `System.Data.DataTableExtensions.CopyToDataTable`.

**Scope:** this is the user's own workflow expression (`.xaml`/`.cs`) — the fault is in a LINQ chain
they wrote, not inside an activity package. If the stack shows the fault deep inside a `UiPath.*` or
third-party package with no user expression in the chain, route to that package instead.

What can cause it:
- A `.Where(...)` / `.Select(...)` filter that legitimately matched **no rows** for the current input,
  followed by an unguarded `.CopyToDataTable()`.
- Filter predicate never matches: value/case/whitespace mismatch (`row("Status").ToString = "Active"`
  vs actual `"active "`), wrong column, or a date/number compared as text.
- Upstream source table was empty (Read Range hit an empty sheet, query returned no rows, the table
  was filtered to empty earlier).

What to look for:
- The exception is `System.InvalidOperationException` with the exact text "The source contains no data
  rows" — distinct from a `NullReferenceException` (the table exists and is non-null; it simply yielded
  no matching rows).
- The `Assign.Value` (or expression) contains `.CopyToDataTable()` at the end of a LINQ chain with no
  preceding `.Any()` / count guard.
- Whether the input for the failing run differs from successful runs (data-dependent — the same
  workflow succeeds when at least one row matches).

## Investigation

1. **Get the error + stack trace.** For an Orchestrator job, read the job `Info` and `jobs logs`
   (`uip or jobs get` / `uip or jobs logs`); for local execution, list `%localappdata%\UiPath\logs\`
   and open the log for the failure date. Confirm the exception is
   `System.InvalidOperationException: The source contains no data rows.` and the stack bottoms out in
   `CopyToDataTable`.
2. Confirm the fault is in the user's workflow, not a package (top stack frames reference the workflow
   `.xaml` expression / user code, and `System.Data.DataTableExtensions.CopyToDataTable`).
3. Locate the faulting `Assign`/expression in source (ask for the project directory if not provided).
   Read the full LINQ chain — the `.Where(...)`/`.Select(...)` predicate and the trailing
   `.CopyToDataTable()`.
4. Determine WHY zero rows matched: is the predicate wrong (case/whitespace/column/type), or did the
   source table legitimately have no matching rows for this input? Compare the failing run's input
   against a successful run if the failure is intermittent.

The root cause is WHY the query returned zero rows (empty source vs. non-matching predicate) plus the
unguarded `.CopyToDataTable()` — not merely "no rows." A confirmed finding names the predicate and
whether the miss is a data condition or a predicate bug.

## Resolution

- **Guard `CopyToDataTable()` with a row check (primary fix):** do not call `.CopyToDataTable()`
  unconditionally. Wrap it in an `If` on
  `YourDataTable.AsEnumerable().Where(Function(x) …).Any()` — assign the filtered table only in the
  Then branch; in the Else branch produce an empty clone (`YourDataTable.Clone()`) or handle the
  "no matches" case explicitly.
- **Materialize safely instead of throwing:** replace the trailing `.CopyToDataTable()` with a pattern
  that tolerates empty results — e.g. compute the filtered rows into an `IEnumerable(Of DataRow)`
  first, then `If rows.Any() Then rows.CopyToDataTable() Else YourDataTable.Clone()`.
- **If the predicate never matches (predicate bug):** fix the comparison — trim/normalize case
  (`row("Status").ToString.Trim().Equals("Active", StringComparison.OrdinalIgnoreCase)`), use the
  correct column name, or compare as the correct type (parse dates/numbers rather than string-compare).
- **If the source table is legitimately empty:** handle "no data" as an expected business path (log
  and skip, or raise a `BusinessRuleException`) rather than letting `CopyToDataTable()` fault the job.
- **If the source table itself is null** (not merely empty) — that is a different error
  (`NullReferenceException`); initialize/populate it first, see
  [null-reference-exception.md](./null-reference-exception.md).
