---
confidence: medium
---

# Lookup Range — Value Not Found When Active Filters Exist

## Context

What this looks like:
- Activity `Lookup Range` (`UiPath.Excel.Activities.LookUpRange` / `LookUpRangeX`) completes **without throwing** but returns a null, empty, or unexpected cell address
- The value being searched for visibly exists in the spreadsheet when opened by hand, yet the lookup reports it is not present
- Downstream activities then fault on the null/empty result (e.g. a later `NullReferenceException`, an empty-string write, or a wrong-row update) — the lookup itself logged no error

What can cause it:
- The target worksheet has **active AutoFilters or column filters** applied. When rows that contain the search value are hidden by a filter, `Lookup Range` does not see them and returns no match (or matches a different, visible row). This is a silent wrong-result, not an exception — the activity searches the *currently visible* cells, and filtered-out rows are excluded.

Notes:
- This is a **silent failure** — there is no error string in the job log from the activity itself. The symptom is a wrong/empty `Output` value, or a downstream fault that traces back to the lookup result. Do not expect a `Lookup Range` error line; look at what the activity *returned*.
- A saved workbook can carry a filter state from a prior manual edit. The filter does not have to be applied by the workflow to bite.

## Investigation

1. Read the `Lookup Range` node from the workflow `.xaml`: capture the target sheet/range, the `Value` being searched, and the `Output` variable.
2. Trace the `Output` downstream — confirm the actual failure is "lookup returned nothing / wrong cell" rather than an exception thrown by the activity.
3. Inspect the target workbook (or ask the user to) for active filters: open the sheet and check whether the filter/funnel icons are present on the header row, or whether any rows are hidden. The row the search value lives on may be filtered out.
4. Confirm the search value really is present in a **filtered-out** row (not simply absent or misspelled — that would be a different cause).

## Resolution

- **If active filters are hiding the target rows** — reset or remove the filters before the lookup runs:
  1. Add a **Filter Table** activity configured to clear the filter, OR a **Clear Sheet/Range/Table** activity (the "clear filters" variant) on the target worksheet, immediately before the `Lookup Range`.
  2. Re-run. With all rows visible, the lookup sees the full data set and finds the value.
  - **Who:** RPA developer
- **If the workbook ships with a saved filter state** — also fix the source workbook (open it, clear the AutoFilter, save) so the filter does not silently reappear on the next run from a fresh copy.
- **If no filters are present and the value is genuinely absent** — this is not the filter scenario. Re-check the search `Value` for a type/whitespace mismatch against the cell contents (see the invalid-range playbook) before concluding the data is missing.
