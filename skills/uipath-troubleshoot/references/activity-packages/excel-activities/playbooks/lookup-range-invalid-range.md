---
confidence: medium
---

# Lookup Range — Invalid Range Syntax or Value Misconfiguration

## Context

What this looks like:
- Activity `Lookup Range` (`UiPath.Excel.Activities.ExcelLookUpRange` / `LookUpRangeX`) faults or returns an unpredictable cell address
- Symptoms vary by misconfiguration:
  - Range parse error: `The range '<x>' is not valid`, `Reference is not valid`, or a COM `0x800A03EC`
  - Wrong/garbage `Output` cell address when the search value contains wildcard characters (`*`, `?`, `~`)
  - Type-mismatch miss: the value exists as displayed but the lookup does not match it because the searched type differs from the stored cell type

What can cause it (any of):
- **Malformed `Range` field** — an invalid A1 reference, or the common mistake of typing an empty string `""` into the `Range` property expecting "whole sheet". For `Lookup Range`, the whole-sheet search is expressed by leaving the `Range` field **completely empty** (no value at all), not by an empty-string literal `""`.
- **Unescaped wildcards in the search `Value`** — a search string containing `*`, `?`, or `~` is interpreted as an Excel wildcard pattern, so the lookup matches the wrong cell or returns an unexpected address instead of a literal-text match.
- **Type mismatch on the search `Value`** — a number stored as text vs. a numeric cell, a date passed as a string, or a trailing/leading space, so the equality check fails even though the value "looks" present.

Notes:
- The empty-string-vs-empty-field distinction is the single most common version of this. `Range = ""` is a *value* (an invalid range) and can crash or mis-resolve; `Range` left blank is the documented way to search the entire used range.

## Investigation

1. Read the `Lookup Range` node from the workflow `.xaml`: capture the literal `Range` value, the `Value` expression being searched, and the `Output` variable.
2. Inspect the `Range` field:
   - If it holds an empty-string literal `""`, that is the misconfiguration — it should be genuinely empty for a whole-sheet search.
   - If it holds an A1 reference, validate the syntax (valid column letters, valid row numbers, valid `Sheet!A1:B2` form if sheet-qualified).
3. Inspect the search `Value`:
   - Check for wildcard characters (`*`, `?`, `~`) in the literal or the bound variable.
   - Check the data type against the target cells: is the workflow searching a `String` against numeric/date cells, or vice versa? Look for stored-as-text numbers and stray whitespace.

## Resolution

- **If `Range` is an empty-string `""`** — clear the field entirely (leave it blank) to search the whole used range. Do not pass `""`.
  - **Source:** documented behavior — blank `Range` = whole sheet; `""` is an invalid range value.
- **If `Range` is a malformed A1 reference** — correct it to a valid reference (e.g. `A1:D500`, or `Sheet1!A:A` for a full column). Sheet-qualify it if the active sheet is ambiguous.
- **If the search `Value` contains wildcards that should be literal** — escape them so they are matched literally (prefix `~` before a literal `*` or `?`, i.e. `~*`, `~?`), or pre-clean the value, so the lookup does a literal-text match instead of a pattern match.
- **If the `Value` type does not match the cell type** — align the types: convert the search value to match how the data is stored (e.g. `.ToString()` for text-stored numbers, trim whitespace with `.Trim()`, or parse to the numeric/date type the cells use). A value that "looks" present but does not match is almost always a text-vs-number or whitespace mismatch.

After the fix, confirm the lookup returns the expected cell address. If it still returns null with no parse error and no type issue, check for active filters hiding the row (see [lookup-range-active-filters.md](./lookup-range-active-filters.md)).
