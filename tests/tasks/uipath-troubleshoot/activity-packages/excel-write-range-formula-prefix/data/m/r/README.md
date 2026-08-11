# Excel Write Range — Formula-Prefix Character

This scenario reproduces a Write Range failure where the source
`DataTable` contains a value starting with `=` — interpreted by
Excel COM as a malformed formula. The job ends with:

```
System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error.
```

## What this scenario uncovers

**Root Cause:** Row 43 of the scraped HR `DataTable`
(`dtEmployees`) contains `=Smith, John` in the `FullName` column —
a data-entry error in the HR source system. Excel COM's
`Range.set_Value` interprets the leading `=` as a formula prefix,
attempts to parse `=Smith, John` as a formula, fails (unknown name
token `Smith`, comma in the wrong context), and rejects the cell
with the generic 0x800A03EC HRESULT. The workflow has no
sanitization step between the HR scrape and the Excel write, so
the bad data passes through verbatim and the activity surfaces the
rejection as-is.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/write-range-failures.md`
(branch 5, formula-prefix sub-cause — distinct from branch 5's
volume sub-cause).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDirectoryProcess` project — `Invoke ScrapeHRDirectory.xaml` → `Use Excel File` → `Write Range` (COM provider) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture both the resolved Write Range config (rows=312 cols=5) AND the cell-level rejection log naming the exact offending cell value (`=Smith, John` at B44, source row 43, column `FullName`) |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (COMException 0x800A03EC
on WriteRange_1, stack through `Range.set_Value`) → `jobs logs`
(the cell-rejection Trace naming `=Smith, John` is the smoking gun) →
workflow source review (confirms no sanitization step between HR
scrape and Write Range) → conclude branch 5 formula-prefix
sub-cause.

> **Note on volume vs. formula-prefix distinction.** Branch 5 has
> two sub-causes that share the 0x800A03EC signature: oversized
> batches (volume) and formula-prefix data (content). The 312-row
> table is well under the volume threshold; the cell-rejection
> Trace specifically names a formula-prefix value. The test
> rewards agents that distinguish the two sub-causes and pick
> formula-prefix as the correct one.

> **Note on fixtures.** Synthetic. The HR scrape sub-workflow, row
> count, and exact cell value are placeholders. The test grades
> whether the agent identifies the formula-prefix root + recommends
> a real fix (apostrophe escape, prefix-stripping sanitization, or
> OpenXML provider switch) and avoids the Try-Catch-and-continue
> anti-pattern that would silently truncate the directory.
