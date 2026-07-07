# Excel Application Scope — COM Add-in Interface Clash

This scenario reproduces a Classic `Excel Application Scope` failure
where a COM add-in loaded into the Excel instance corrupts the interop
interface negotiation. The job ends with:

```
System.InvalidCastException: Unable to cast COM object of type 'System.__ComObject' to interface type 'Microsoft.Office.Interop.Excel._Application'.
```

(QueryInterface for IID `{000208D5-...}` → `0x80004002 E_NOINTERFACE`)

## What this scenario uncovers

**Root Cause:** The scope instantiates `Excel.Application`, but the
`UiPath.Integration.ExcelAddin` (the Studio design-time Excel Add-in,
`LoadBehavior=3`, registered on this runtime host where it shouldn't be)
— alongside a third-party `AcmeBudgetTools.Connect` add-in — corrupts
the QueryInterface for `Microsoft.Office.Interop.Excel._Application`,
returning `E_NOINTERFACE`. The `System.__ComObject` can't be cast to the
interop interface. `excel.exe /safe` (add-ins disabled) succeeds,
confirming an add-in is the culprit.

The fix is to disable the offending COM add-in (File → Options →
Add-ins → COM Add-ins, or `LoadBehavior=0` in the registry) and confirm
with `excel.exe /safe`.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`
(branch 3 — COM add-in interface clash).

## The trap

The error mentions COM and Excel, which can tempt an agent toward
"Excel isn't installed / repair Excel." But Excel IS installed and
launches, and the inner HRESULT is `E_NOINTERFACE` (an interface-cast
fault), not `REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED`. The
`/safe` success is the tell: the COM stack is healthy without add-ins.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelReconExport` — single Classic `<uix:ExcelApplicationScope>` wrapping a `Read Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `jobs get` carries the `InvalidCastException` / `E_NOINTERFACE`, and `jobs logs` enumerates the loaded COM add-ins (incl. `UiPath.Integration.ExcelAddin`) and notes `excel.exe /safe` succeeds |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

Expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (`InvalidCastException`,
`E_NOINTERFACE`) → `jobs logs` (loaded COM add-ins + `/safe` succeeds) →
workflow source (single Classic scope) → conclude branch 3.

> **Note on fixtures.** Synthetic. The IID, add-in names, and
> `LoadBehavior` values are placeholders. The test grades whether the
> agent identifies the COM add-in clash (NOT not-installed, NOT a lock)
> and recommends disabling the offending add-in (UI or `LoadBehavior=0`)
> with `/safe` confirmation.
