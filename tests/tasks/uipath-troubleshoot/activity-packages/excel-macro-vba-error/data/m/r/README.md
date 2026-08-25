# Excel Execute Macro — VBA Error Inside The Macro

This scenario reproduces an Execute Macro failure where the macro
dispatched successfully but threw a VBA runtime error during
execution. The job ends with:

```
System.Runtime.InteropServices.COMException (0x80020009): Exception occurred.
 ---> Run-time error '91': Object variable or With block variable not set
```

## What this scenario uncovers

**Root Cause:** The macro `Module1.ProcessData` ran successfully past
the macro-lookup stage (Excel dispatched the call; VBA started
executing), then threw `Run-time error 91` inside the macro code.
HRESULT `0x80020009 DISP_E_EXCEPTION` is Excel's COM wrapper for
"the macro threw via IDispatch"; the inner VBA error is the actual
cause. Run-time error 91 specifically means the macro tried to use
an object variable that was never `Set` — typically a `Range`,
`Worksheet`, or `Workbook` reference sourced from a lookup that
returned `Nothing`.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/execute-macro-failures.md`
(the "VBA error inside the macro" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelMacroProcess` project — `Use Excel File` → `Execute Macro: Module1.ProcessData` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs get` Info field includes the inner Run-time error 91 text |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (HRESULT 0x80020009 + inner
Run-time error 91) → `jobs logs` (Trace shows macro dispatched, then
faulted with the inner error) → workflow source (Macro name +
configured properties) → conclude branch 2.

> **Note on fixtures.** Synthetic. The macro name, module name, and
> specific Run-time error line in the logs are placeholders. The test
> grades whether the agent identifies the inner VBA error as the
> load-bearing detail (branch 2) and distinguishes it from branch 7
> (which would have a different inner error: 424 Object Required or
> 429 ActiveX-cant-create).
