---
confidence: medium
---

# Append / Write CSV — DataTable Structure / Null Value Mismatch

## Context

What this looks like:
- A CSV activity faults or writes incorrectly: **mismatched columns**, rows failing to write, or a null-reference at the CSV step.

What can cause it:
- **Uninitialized `DataTable`.** The `DataTable` variable passed to `Write CSV` / `Append To CSV` was never instantiated (still `Nothing` / `null`) — e.g. it was declared but no `Build Data Table` / `Read` ever populated it.
- **Column count / header mismatch.** The incoming `DataTable`'s columns do not match the existing CSV's columns (different count, order, or header names), so `Append To CSV` cannot line the rows up with the file.
- **Mapping out-of-scope fields.** The workflow writes columns/values that are out of scope or absent from the `DataTable`, producing empty or mismatched output.

What to look for:
- Whether the `DataTable` variable is assigned a value (Build Data Table, Read CSV/Range, Generate Data Table) before the write/append, or only declared.
- The column structure (count, headers, order) of the incoming `DataTable` vs the target CSV.
- Whether special characters in the data trip CSV (de)serialization.

## Investigation

1. Read the error and confirm it is a data-shape / null problem at the CSV activity (not a `CsvHelper` `Method not found` and not a file lock — different playbooks).
2. Trace the `DataTable` variable: is it instantiated and populated before the CSV step? A `NullReferenceException` at the write points to an uninitialized table.
3. Compare the incoming `DataTable`'s columns (count, names, order) against the existing CSV's header row.

## Resolution

- **If the `DataTable` is uninitialized:** instantiate it before use — add a **Build Data Table** activity (or assign it from `Read CSV` / `Read Range` / a `New DataTable`) so the variable is a real table with defined columns before the `Add Data Row` loop runs.
- **If columns mismatch the target file:** define the `DataTable` with **identical header columns** (same names, order, count) as the existing CSV — use **Build Data Table** to lay out the schema, then add rows to it. For `Append To CSV`, the table's columns must align with the file's.
- **If special characters consistently break (de)serialization:** bypass the CSV helper — use **Read Text File** to load the raw content, manipulate it with string activities, and commit with **Append Line** for full control over quoting/escaping.
