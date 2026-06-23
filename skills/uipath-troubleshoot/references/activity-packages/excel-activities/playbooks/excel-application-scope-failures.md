---
confidence: medium
---

# Excel Application Scope (Classic) COM-Interop Failures

## Context

The Classic `Excel Application Scope` (class `UiPath.Excel.Activities.ExcelApplicationScope`) opens a workbook through Microsoft Excel via COM Interop. Unlike the Modern `Use Excel File` card (which defaults to the OpenXML provider and only falls back to COM when COM-forcing properties are set), Classic is **COM-only** — every execution spins up an `Excel.Application` COM server on the host. That hard COM dependency produces a family of failures that are specific to the Classic surface and do not occur on a pure-OpenXML Modern card.

This playbook covers the **COM-interop-environment** failures of the Classic scope: the host has Excel, but the COM layer between UiPath and `EXCEL.EXE` is broken, contended, or hijacked. Three surfaces:

1. **COM registration corruption** — Excel IS installed, but the `Excel.Application` COM class / type library registration is broken (typically after an Office upgrade or repair). The scope throws "Make sure Excel is installed" even though Excel is present.
2. **Workbook acquisition blocked** — an orphan `EXCEL.EXE` from a prior crashed job (or a user-opened instance) still holds the target workbook, so the scope can't acquire it.
3. **COM Add-in interface clash** — a COM add-in loaded into the Excel instance (the UiPath Excel Add-in or a third-party add-in) corrupts the QueryInterface negotiation, producing an `InvalidCastException` on `System.__ComObject`.

> **Out of scope — cross-reference, don't re-diagnose here.** Failures the Classic scope SHARES with the Modern card live in [`./excel-application-card-failures.md`](./excel-application-card-failures.md): true Excel-not-installed (host has no Excel at all → that playbook's branch 1), empty / illegal `WorkbookPath` (branch 2), COM/RPC races across MULTIPLE scopes without an `Excel Process Scope` (branch 3), a child activity dropped outside any scope — "must be placed inside Excel Application Scope" (branch 4), and sensitivity-label rejection (branch 5). This playbook's branches assume a SINGLE Classic scope whose own COM acquisition fails on a host that DOES have Excel installed.

What this looks like — Classic Excel Application Scope COM-interop faults surface as one of these signatures:

- `UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed.` with an inner `COMException` carrying `0x8002801D TYPE_E_LIBNOTREGISTERED` ("Library not registered") or `0x80040154 REGDB_E_CLASSNOTREG` **on a host where Excel IS installed** — the interop / type-library registration is broken. Branch 1.
- `UiPath.Excel.BusinessException: Failed opening the Excel file. Possible reasons: file is corrupt, already used by another process or password protected.` — an orphan `EXCEL.EXE` or a user-owned Excel instance still holds the target workbook. Branch 2.
- `System.InvalidCastException: Unable to cast COM object of type 'System.__ComObject' to interface type 'Microsoft.Office.Interop.Excel.<Interface>'. ... QueryInterface ... failed due to the following error: No such interface supported (Exception from HRESULT: 0x80004002 (E_NOINTERFACE))` — a COM add-in (commonly `UiPath.Integration.ExcelAddin`) hijacked or corrupted the interop interface. Branch 3.

What can cause it (cause-branches — pick the right one from evidence):

1. **COM registration corruption (Excel present, interop broken)** — Excel is installed and launches interactively, but the `Excel.Application` CLSID or its type library (`TYPE_E_LIBNOTREGISTERED`) isn't correctly registered for COM activation. Almost always follows an **Office version change**: an in-place upgrade to Microsoft 365 / Office 2024 click-to-run, a side-by-side install of a second Office version, or an interrupted Office update / repair. Stale `TypeLib` keys from the previous Office build point at a version that no longer exists, so `CoCreateInstance` succeeds at the class level but interface/typelib resolution fails. The Classic scope rewraps the COM error as the canonical "Make sure Excel is installed."
2. **Workbook held by another EXCEL.EXE** — the target workbook is locked. Two sub-cases: (a) an **orphan** `EXCEL.EXE` — a prior job's scope crashed or was force-killed and left a headless `EXCEL.EXE` owned by the Robot's session still holding the file; (b) a **user-owned** instance — someone has the workbook open in the interactive Excel UI on the same host (common on attended / RDP-shared machines). Either way the file handle is exclusive and the new scope can't open it.
3. **COM Add-in interface clash** — when the scope launches `EXCEL.EXE`, Excel auto-loads its registered COM add-ins. A misbehaving add-in — frequently the `UiPath.Integration.ExcelAddin` (the Studio "Excel Add-in" used for design-time recording) loaded on a runtime host where it shouldn't be, or a third-party add-in — interferes with the interop proxy so the `QueryInterface` for `Microsoft.Office.Interop.Excel.Application` (or `Workbook` / `Worksheet`) returns `E_NOINTERFACE`. The marshaled `__ComObject` can't be cast to the expected interop interface and the scope throws `InvalidCastException`.

What to look for:

- **The exception class + inner HRESULT** — first signal. `BusinessException: Error opening workbook. Make sure Excel is installed.` + inner `0x8002801D TYPE_E_LIBNOTREGISTERED` (or `0x80040154` despite a confirmed install) → branch 1. `BusinessException: Failed opening the Excel file. ... already used by another process` → branch 2. `InvalidCastException` on `System.__ComObject` + `0x80004002 E_NOINTERFACE` → branch 3.
- **Host Excel install state** — the fork between this playbook's branch 1 and the card playbook's branch 1. If `HKLM:\Software\Microsoft\Office\*\Excel\InstallRoot` is **present** and `excel.exe` launches interactively, Excel IS installed → registration corruption (this playbook, branch 1). If there's no install at all → that's [`./excel-application-card-failures.md`](./excel-application-card-failures.md) branch 1, not this one.
- **Recent Office change** — was Office upgraded, repaired, or had a second version installed shortly before the failures started? "Worked last week, broke after the M365 rollout" is the branch 1 fingerprint.
- **Host process list at failure time** — `Get-Process EXCEL` / `tasklist /FI "IMAGENAME eq EXCEL.EXE"` on the host. A lingering `EXCEL.EXE` (especially one owned by the Robot's session with no visible window) is the branch 2 signal. Distinguish an **orphan** (no UI, Robot-session-owned, left by a prior job) from a **user-owned** instance (interactive UI, logged-in user's session).
- **Loaded COM add-ins** — `HKLM:\Software\Microsoft\Office\Excel\Addins\` and `HKCU:\Software\Microsoft\Office\Excel\Addins\` enumerate registered add-ins and their `LoadBehavior`. `UiPath.Integration.ExcelAddin` with `LoadBehavior=3` on a runtime host is the branch 3 signal.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, the inner HRESULT, and the surface.** From `uip or jobs get <job-key> --output json` → `Info`: the `BusinessException` / `InvalidCastException` message, the **inner exception HRESULT**, and the full stack. From workflow source: confirm the scope is the Classic `<uix:ExcelApplicationScope>` element (NOT `<uix:UseExcelFile>`) and that there's a SINGLE scope (multiple scopes racing → card playbook branch 3, not here). From `project.json`: the `UiPath.Excel.Activities` version. From job logs: any Trace lines naming the host's Excel state or the acquisition step.

2. **Branch the diagnostic on the signature.**
   - `BusinessException: Make sure Excel is installed.` + inner `TYPE_E_LIBNOTREGISTERED` (`0x8002801D`) or `REGDB_E_CLASSNOTREG` (`0x80040154`) → could be this playbook's branch 1 (registration broken) OR the card playbook's branch 1 (Excel truly absent). Disambiguate at step 3.
   - `BusinessException: Failed opening the Excel file. ... already used by another process` → branch 2; go to step 4.
   - `InvalidCastException` on `System.__ComObject` + `E_NOINTERFACE` (`0x80004002`) → branch 3; go to step 5.

3. **Disambiguate branch 1 (registration corruption) from "Excel truly not installed."** This is the decisive fork:
   - **Is Excel installed on the host?** Check `Get-ItemProperty 'HKLM:\Software\Microsoft\Office\*\Excel\InstallRoot'` (PowerShell) and whether `excel.exe` exists under `C:\Program Files\Microsoft Office\root\Office16\` (or equivalent). **No install at all → STOP: this is [`./excel-application-card-failures.md`](./excel-application-card-failures.md) branch 1**, not registration corruption.
   - **Does Excel launch interactively?** Have the host operator open Excel from the Start menu. If it opens cleanly, the binary is fine and the problem is COM **activation** registration, not the install — branch 1 (this playbook) confirmed.
   - **Was Office recently changed?** Check for a recent upgrade (M365 / Office 2024 click-to-run), a second Office version, or an interrupted update / repair. A version change immediately before the failures is the branch 1 fingerprint.
   - **Is the inner HRESULT `TYPE_E_LIBNOTREGISTERED` (`0x8002801D`)?** That HRESULT specifically means the type library isn't registered — strong evidence of stale / orphaned `TypeLib` keys from a previous Office build, i.e., registration corruption rather than a missing install.

4. **Confirm branch 2 (workbook held by another EXCEL.EXE).** Check:
   - **Host process snapshot at failure time** — `Get-Process EXCEL` on the host. A lingering `EXCEL.EXE` confirms the lock holder exists. (The timestamp matters — the locking process may be gone by the time you check; correlate with the job's run time.)
   - **Orphan vs. user-owned** — an orphan has no visible window and is owned by the Robot's session (left by a prior crashed / force-killed job). A user-owned instance has an interactive UI in a logged-in user's session. `Get-Process EXCEL | Select-Object Id, SI, MainWindowTitle` (the `SI` session id and empty `MainWindowTitle` flag an orphan).
   - **File handle** — if Sysinternals is available, `handle.exe -a "<workbook-path>"` names the exact process holding the file.
   - **Prior-job correlation** — check the Robot's `Execution.log` (`%LocalAppData%\UiPath\Logs\Execution.log`) for a prior job on the same host that opened this workbook and ended abnormally (faulted / killed) without a clean scope-close. That prior job is the orphan's origin.

5. **Confirm branch 3 (COM Add-in interface clash).** Check:
   - **Inner HRESULT** — `0x80004002 E_NOINTERFACE` inside an `InvalidCastException` on `System.__ComObject` is the fingerprint. The message names the interop interface it failed to cast to (`Microsoft.Office.Interop.Excel.Application` / `Workbook` / `Worksheet`).
   - **Registered Excel COM add-ins** — enumerate `HKLM:\Software\Microsoft\Office\Excel\Addins\` and `HKCU:\Software\Microsoft\Office\Excel\Addins\`. Look for `UiPath.Integration.ExcelAddin` (the Studio Excel Add-in, meant for design-time recording — not for runtime hosts) or any third-party add-in with `LoadBehavior=3` (load at startup).
   - **Reproduce by isolating add-ins** — launch Excel on the host with `excel.exe /safe` (add-ins disabled). If a manual COM open then succeeds where the scope failed, an add-in is the culprit.

The root cause is **which of the three COM-interop surfaces** the failure maps to: broken interop registration on an installed Excel (branch 1), the workbook held by another `EXCEL.EXE` (branch 2), or a COM add-in corrupting the interop interface (branch 3). A confirmed finding names the surface plus its decisive evidence — the inner HRESULT, the host's install-vs-registration state, the lock-holding process, or the offending add-in.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — COM registration corruption (Excel present, interop broken):**
  - **Office Online Repair (canonical fix):** Windows Settings → Apps → Installed Apps → Microsoft Office → Modify → **Online Repair**. This re-registers the Excel COM classes and type libraries from the current build and clears stale registration from the prior version. Requires admin rights on the Robot host. This is the right first move when the breakage followed an Office upgrade.
  - **UiPath "Repair Tool for Microsoft Office":** UiPath Studio → Tools → "Repair Tool for Microsoft Office". Lighter than Online Repair; re-registers the Excel interop components without a full Office repair. Quick to try first if you don't have admin rights for Online Repair.
  - **Targeted `TypeLib` cleanup (only if the error is `TYPE_E_LIBNOTREGISTERED` and repair didn't resolve it):** stale `TypeLib` keys from a previous Office build can survive a repair. **Back up the registry key before editing.** In `regedit`, under `HKCR\TypeLib\`, the Excel type library GUID is `{00020813-0000-0000-C000-000000000046}`; ensure its version subkeys point to the **currently installed** Office version's `excel.exe` / `EXCEL.EXE` typelib path and remove orphaned version subkeys that reference an uninstalled build. Editing the registry is the last resort — prefer Online Repair, which does this safely and completely.
  - **Cross-branch alternative — drop COM entirely:** if the workflow doesn't actually need Excel COM features (formula recalc, macros, formatting interaction), migrate off the Classic scope to Workbook activities or a Modern OpenXML `Use Excel File` card. See [`./excel-application-card-failures.md`](./excel-application-card-failures.md) branch 1 resolution for the migration steps. This sidesteps the whole COM-registration surface.

- **Branch 2 — Workbook held by another EXCEL.EXE:**
  - **Clear orphan processes as a recovery step:** add a `Kill Process` activity with `ProcessName = "EXCEL"` immediately BEFORE the `Excel Application Scope` to terminate stray headless instances. **Caveat:** this is a blunt instrument — it also kills any Excel the interactive user has open. Use it only on dedicated unattended Robot hosts where no human is working in Excel, never on attended / shared machines.
  - **Fix the root cause of orphans (preferred):** orphans come from scopes that didn't close cleanly. Ensure the failing/aborting upstream workflow closes its Excel scope properly (don't `Application.Quit` from a child macro — see [`./execute-macro-failures.md`](./execute-macro-failures.md) branch 3); wrap multi-scope workflows in an `Excel Process Scope` so EXCEL.EXE lifecycle is governed; avoid force-killing jobs mid-scope.
  - **User-owned lock:** if the holder is an interactive user's Excel instance, the file simply can't be opened exclusively while it's in use. Coordinate so the workbook isn't manually open during automation runs, point the automation at a copy, or open read-only (`ReadOnly = True` on the scope) if the workflow only reads.
  - **Network-share lock:** if the workbook is on a UNC share, the lock may be held by a different host. The lock owner (`.~lock` / owner file, or `handle.exe` on the holding host) names it; resolve at the share level.

- **Branch 3 — COM Add-in interface clash:**
  - **Disable the offending COM add-in (canonical fix):** open Excel manually on the host → File → Options → Add-ins → at the bottom set the **Manage** dropdown to **COM Add-ins** → **Go** → uncheck `UiPath.Integration.ExcelAddin` (and any suspect third-party add-in) → OK. Restart the automation. The Studio Excel Add-in is a design-time recording aid; it should not be loaded on a runtime Robot host.
  - **Disable per-machine via registry (for unattended provisioning):** set `LoadBehavior` to `0` under the add-in's key in `HKLM:\Software\Microsoft\Office\Excel\Addins\UiPath.Integration.ExcelAddin` (and the `HKCU` hive for the Robot user). This prevents the add-in from loading at Excel startup across jobs without manual UI steps — bake it into the host-provisioning runbook.
  - **Confirm with `/safe`:** validate the fix by launching `excel.exe /safe` and confirming a manual COM open succeeds; then re-run the job with the add-in disabled.
  - **Third-party add-in that's required:** if the clashing add-in genuinely must stay loaded, isolate Excel automation to a host without it, or move the workflow to the Workbook surface (no `EXCEL.EXE`, so no add-in loads at all).

## Anti-patterns (what NOT to do)

Common advice for Classic Excel Application Scope COM failures contains workarounds that mask the fault. The agent should NOT recommend any of these as a primary resolution.

- **"Add a `Delay` before the Excel Application Scope."** A Delay does nothing for a broken COM registration (branch 1) or an add-in clash (branch 3) — the registry state and loaded add-ins are identical a few seconds later. For an orphan-process lock (branch 2) a Delay only "helps" if the orphan happens to exit during the window, which is non-deterministic. Fix the registration, clear the orphan deterministically, or disable the add-in instead.

- **"Wrap the scope in a bare `Try Catch` and continue on error."** Catching `BusinessException` / `InvalidCastException` and only logging turns the failure into a silent skip — the child activities don't run and the workflow proceeds with missing data. All three branches here are deterministic configuration / environment faults; suppressing them hides a host that will fail every run. Use Try-Catch only with a real recovery path (kill orphan + retry, notify ops, fall back to Workbook activities).

- **"Reinstall Office from scratch to fix the registration error."** For branch 1, a full uninstall/reinstall is disproportionate and slow. **Online Repair** re-registers the COM classes and type libraries without the downtime and license-reactivation churn of a reinstall. Reserve a full reinstall for cases where repair demonstrably fails.

- **"`Kill Process EXCEL` unconditionally at the start of every workflow."** On a shared / attended host this destroys the interactive user's open workbooks (data loss). It's a valid recovery ONLY on dedicated unattended hosts. Even there, prefer fixing what leaves orphans (clean scope close, no macro `Application.Quit`, `Excel Process Scope` for multi-scope flows) over routinely killing processes.

- **"Set `Visible: True` to see what's happening."** On unattended hosts the desktop session often isn't rendered, so the property has no diagnostic value, and it adds COM-UI overhead. It doesn't surface registration corruption, locks, or add-in clashes — use the host's process list, registry, and `excel.exe /safe` instead.

## Prevention (cross-branch)

- **Pin the Office build on Robot hosts** and route Office upgrades through a change process that includes an Excel-COM smoke test (a workflow that opens and reads a workbook via Classic scope) after every Office update. This catches branch 1 registration breakage before production jobs hit it.
- **Strip the Studio Excel Add-in from runtime hosts.** `UiPath.Integration.ExcelAddin` is a design-time tool; set its `LoadBehavior=0` (or don't install it) on unattended Robot hosts to prevent branch 3 clashes. Document this in the host-provisioning runbook.
- **Govern EXCEL.EXE lifecycle** to prevent orphans (branch 2): wrap multi-scope workflows in an `Excel Process Scope`, never tear down Excel from a child macro (`Application.Quit` / `Workbooks.Close`), and avoid force-killing jobs while a scope is open.
- **Prefer the lowest-COM surface that meets the requirement.** If a workflow doesn't need Excel COM features, use Workbook activities or a Modern OpenXML `Use Excel File` card — that eliminates the entire COM-interop failure surface (all three branches here) on hosts that don't otherwise need Excel.
- **For attended / shared hosts,** never bake an unconditional `Kill Process EXCEL` into workflows; coordinate workbook access so automation and humans don't contend for the same file.

## Related

- [`./excel-application-card-failures.md`](./excel-application-card-failures.md) — the SHARED scope-container playbook. Excel **truly not installed** (branch 1 there), empty / illegal `WorkbookPath` (branch 2), COM/RPC **races across multiple scopes** (branch 3), **child activity outside any scope** (branch 4), and **sensitivity-label** rejection (branch 5) all live there. This playbook is the Classic-COM-interop complement: a single installed-but-broken / contended / hijacked COM layer.
- [`./execute-macro-failures.md`](./execute-macro-failures.md) — branch 3 there (macro tears down Excel via `Application.Quit` / `Workbooks.Close`) is a common upstream cause of the orphan / disconnected-process state that this playbook's branch 2 observes downstream.
- [`../overview.md`](../overview.md) — package overview; the OpenXML-vs-COM provider model and the Classic-scope-is-COM-only distinction are load-bearing for all three branches here.
- [`../summary.md`](../summary.md) — navigation across all Excel Activities playbooks.
