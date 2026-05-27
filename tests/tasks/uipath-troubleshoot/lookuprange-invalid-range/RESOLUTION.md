# Final Resolution

---

**Root Cause:** The classic `Lookup Range` activity in `Main.xaml` has its
`Range` property set to a **literal empty string** (`Range="&quot;&quot;"`,
i.e. the C# expression `""`). For `Lookup Range`, the whole-sheet search is
expressed by leaving the `Range` field **completely empty** (no value);
`""` is an *invalid range value*. The `Excel Application Scope` opens
`Catalog.xlsx` successfully, then the `Lookup Range` faults at the range
parse step with `The range '' is not valid` before any cell is searched.

**What went wrong:** The `CatalogLookup` job (started
2026-05-27T08:02:33Z) faulted ~4 seconds in, after the workbook opened.
The runtime error was `UiPath.Excel.ExcelException: The range '' is not
valid` thrown by the `Lookup Range` activity. The job log shows the scope
opening the workbook, then the lookup erroring on the empty range - so the
fault is in the activity's range configuration, not in opening the file or
in the data.

**Why:** `Lookup Range` treats a blank `Range` and a literal `""`
differently. A genuinely empty `Range` field means "search the whole used
range". A `Range` set to the expression `""` is a *value* - an empty range
reference - which the activity cannot parse, so it raises
`The range '' is not valid`. The common mistake is typing `""` into the
`Range` property expecting "whole sheet"; the correct way to get a
whole-sheet search is to leave the field blank.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CatalogLookup -- Faulted at 2026-05-27T08:02:37.870Z (ran for ~4.5 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `UiPath.Excel.ExcelException: The range '' is not valid` -> `Main.xaml` -> `LookUpRange "Lookup Range"` -> `ExcelApplicationScope "Excel Application Scope"` -> `Sequence "Main Sequence"`
- Log ordering: "Opening workbook ..." then "Workbook opened" then the range error - the scope opened cleanly; the fault is at the `Lookup Range`.

### Excel Activities (Root Cause)
- Activity surface: classic `UiPath.Excel.Activities.LookUpRange` inside `UiPath.Excel.Activities.ExcelApplicationScope`
- Configuration in `Main.xaml`: `Range="&quot;&quot;"` (the expression `""`), `SheetName="Parts"`, `Value="[partNumber]"`.
- `""` is an invalid range value; the activity fails to parse it and raises `The range '' is not valid`. A whole-sheet search requires the `Range` field to be left blank, not set to `""`.

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Clear the `Range` field entirely (leave it blank) so the `Lookup Range`
   searches the whole used range. Do not pass `""`.
   - **Why:** a blank `Range` = whole sheet; the literal `""` is an invalid
     range value that fails to parse.
   - **Where (in `Main.xaml`):** the `LookUpRange "Lookup Range"` activity -
     remove the `""` expression from its `Range` property.
   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/lookup-range-invalid-range.md`
2. If the lookup is meant to be bounded to a specific block rather than the
   whole sheet, set `Range` to a valid A1 reference instead (e.g.
   `A1:D5000`, or `Parts!A:A` for a full column), sheet-qualified if the
   active sheet is ambiguous.

After the fix, confirm the lookup returns the expected cell address. If it
then returns null with no parse error, check for active filters hiding the
row (see `lookup-range-active-filters.md`) or a value type/whitespace
mismatch.

---

**Preventive fix:**

1. **Studio** -- to search a whole sheet with `Lookup Range`, leave the
   `Range` field blank; never type `""`. Reserve a non-empty `Range` for a
   genuine A1 block.
   - **Why:** the empty-string-vs-blank trap is the most common
     `Lookup Range` misconfiguration and fails only at runtime.
   - **Who:** RPA developer.

2. **Studio** -- validate the workflow (or run it against a sample
   workbook) after editing a `Lookup Range`'s `Range`/`Value`, so a bad
   range value is caught before publishing.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Lookup Range's `Range` is set to a literal empty string `""` instead of left blank; `""` is an invalid range value and the activity faults with "The range '' is not valid" | High | Confirmed | Yes | Job error `The range '' is not valid` after the scope opened; `Main.xaml` shows `Range="&quot;&quot;"` on the `Lookup Range` | Clear the `Range` field (blank = whole sheet), or set a valid A1 reference |

---

Would you like help editing `Main.xaml` to clear the `Lookup Range`'s
`Range` field (or set a valid A1 range), or cleaning up the
`.local/investigations/` folder?
