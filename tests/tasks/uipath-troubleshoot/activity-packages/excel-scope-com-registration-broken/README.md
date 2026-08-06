# Excel Application Scope — COM Registration Broken After Office Upgrade

This scenario reproduces a Classic `Excel Application Scope` failure on
a Robot host where **Excel IS installed** but its `Excel.Application`
COM / type-library registration was corrupted by a recent in-place
Microsoft 365 upgrade. The job ends with:

```
UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed.
```

(with inner `COMException 0x8002801D TYPE_E_LIBNOTREGISTERED`)

## What this scenario uncovers

**Root Cause:** Excel is present (Microsoft 365 Apps build path logged,
launches interactively), but an in-place upgrade from Office 2019 left
a stale `TypeLib` registration for the Excel Object Library. The COM
class factory creates the `Excel.Application` object, then interop
type-library resolution fails with `TYPE_E_LIBNOTREGISTERED`. The
Classic scope rewraps it as the generic "Make sure Excel is installed."

The fix is to repair the COM / type-library registration (Office
Online Repair, UiPath Repair Tool, or targeted `TypeLib` cleanup) —
**not** to install Excel, which is already installed.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`
(branch 1 — COM registration corruption).

## Why this is the hard contrast case

This scenario is the deliberate counterpart to
`excel-card-excel-not-installed`. Both throw the identical
`BusinessException: Error opening workbook. Make sure Excel is
installed.` The agent must NOT reflexively conclude "Excel isn't
installed — install it." The distinguishing evidence is:

| Signal | Not-installed scenario | This scenario (registration broken) |
|---|---|---|
| Inner HRESULT | `0x80040154 REGDB_E_CLASSNOTREG` | `0x8002801D TYPE_E_LIBNOTREGISTERED` |
| Host Excel state (logs) | NOT INSTALLED (no registry, no excel.exe) | INSTALLED — build path given, launches |
| Trigger | new deployment to a headless host | recent in-place Office upgrade |
| Fix | install Excel OR migrate off COM | repair COM/TypeLib registration |

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | `ExcelLedgerReport` — single Classic `<uix:ExcelApplicationScope>` wrapping a `Read Range` |

Expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException, inner
`TYPE_E_LIBNOTREGISTERED`) → `jobs logs` (INSTALLED state + upgrade +
stale TypeLib) → workflow source (single Classic scope) → conclude
branch 1 (registration corruption).

> **Note on fixtures.** Synthetic. The exact build numbers, TypeLib
> GUID handling, and host-detection wording are placeholders. The test
> grades whether the agent recognizes Excel-is-installed-but-COM-
> registration-is-broken (NOT not-installed) and recommends a repair
> (Online Repair / UiPath Repair Tool / TypeLib cleanup) rather than
> "install Excel".

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
