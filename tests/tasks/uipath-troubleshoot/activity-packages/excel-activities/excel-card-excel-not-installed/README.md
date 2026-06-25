# Excel Application Scope — Excel Not Installed on Host

This scenario reproduces a Classic `Excel Application Scope` failure
where the Robot host has no Microsoft Excel installed. Classic scope
is COM-only; without `Excel.Application` registered in the host's
COM registry, the scope's acquisition step throws. The job ends with:

```
UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed.
```

(with inner `COMException 0x80040154 REGDB_E_CLASSNOTREG`)

## What this scenario uncovers

**Root Cause:** The workflow uses Classic `Excel Application Scope`
which always requires Excel COM. The unattended Robot host has no
Excel installed (no registry entry under `HKLM:\Software\Microsoft\
Office\*\Excel\InstallRoot`, no `excel.exe` on the filesystem). The
scope's `CoCreateInstance` for `CLSID {00024500-...}` (Excel.
Application) returns `REGDB_E_CLASSNOTREG`, surfaced as the
canonical "Make sure Excel is installed" BusinessException.

The fix branches based on whether the workflow actually needs Excel
COM features: workflows that just read/write data can migrate to
Workbook activities or Modern `Use Excel File` (OpenXML default);
workflows that need COM features need Excel installed on the host.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-card-failures.md`
(the "Excel not installed / Interop unavailable" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelInvoiceReport` project — Classic `<uix:ExcelApplicationScope>` wrapping a `Read Range`. The workflow doesn't actually need COM features (just reads data) — the Classic surface choice is the problem |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture (a) the surface choice (Classic, COM-only), (b) the host's install state (no registry entry, no `excel.exe`), and (c) the canonical COM `REGDB_E_CLASSNOTREG` HRESULT |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException with
inner COMException 0x80040154) → `jobs logs` (the three Trace lines
pinning surface + host state + COM error) → workflow source review
(confirms Classic surface used for a workflow that doesn't need
COM) → conclude branch 1.

> **Note on the surface-choice fork.** The test rewards agents
> who recognize that the fix depends on whether the workflow
> needs Excel features. An agent that recommends ONLY "install
> Excel on the host" without considering the alternative
> (migrate to Workbook surface) gets partial credit. An agent
> that recognizes the fork and asks (or recommends both paths
> with their applicable conditions) scores full marks.

> **Note on fixtures.** Synthetic. The exact COM HRESULT,
> registry path, and host detection logic are placeholders. The
> test grades whether the agent identifies the surface-vs-host
> mismatch AND recommends a viable fix (install Excel,
> repair Excel, migrate to Workbook, or migrate to Modern
> OpenXML).
