# Excel Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.Excel.Activities.Business.InvokeVBAX`, `UiPath.Excel.Activities.LookUpRange`, `UiPath.Excel.Activities.LookUpRangeX`). Classic activities (no `X` suffix, inside an `Excel Application Scope`, Interop/COM) and modern `*X` activities (inside `Use Excel File` / `Excel Process Scope`) share display names but run different code paths — treat them as different. `Invoke VBA` only exists on the modern (COM) surface; `Lookup Range` exists on both.
- **Workbook** — the workbook path in evidence matches the file the user is asking about. `Invoke VBA` operates on the workbook open inside the surrounding `Excel Process Scope` — different scope = different workbook = unrelated data.
- **Code file** — the `CodeFilePath` in evidence resolves to the macro source the user is asking about. A `.txt`/`.vba`/`.bas` file path that no longer exists on the robot machine, or a stale path checked into source control, is a different file than the one the user has open locally.
- **Entry method** — the `EntryMethodName` in evidence matches the macro the user reports calling. Don't substitute a similarly-named macro.
- **Robot / machine identity** — the robot account and the machine where Excel installed match the one the user reports. Excel security settings (Trust Center, Trust access to VBA project) are per-user-per-machine, so evidence from a different host is not transferable.
- **Office version** — the Excel/Office version installed on the robot machine matches the one the user reports. Multiple Office versions on the same host produce COM dispatcher ambiguity unrelated to a single-version user's experience.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for COM-interop investigations (transient `0x80010100` errors may not reproduce on demand) and for Trust Center investigations (the setting may have been changed since).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

### Invoke VBA

1. **Workflow source** — read the `InvokeVBAX` activity node from the surrounding `.xaml` to capture the literal values of `CodeFilePath`, `EntryMethodName`, and the expression bound to `EntryMethodParameters`. Property panel summaries truncate; the XAML is authoritative.
2. **Code file contents** — read the macro source at the resolved `CodeFilePath`. Required to verify the `Sub`/`Function` declaration name and signature against `EntryMethodName` and `EntryMethodParameters`. Check encoding: a UTF-8 BOM, UTF-16, or stray control character will compile-fail.
3. **Excel Trust Center setting** — `File > Options > Trust Center > Trust Center Settings > Macro Settings > "Trust access to the VBA project object model"` on the robot machine, under the same Windows user that runs the robot. The setting is per-user-per-machine and per Office install.
4. **Excel state at failure time** — whether Excel.exe was running, whether any modal dialog was open (recover-unsaved-files banner, license activation, macro-warning bar, "trust this file" prompt), and whether `Visible = True` was set on the surrounding `Excel Process Scope` (without it, dialogs are invisible to the user but still block the macro).
5. **Office installation inventory** — number of Office versions installed on the host (Microsoft 365, perpetual Office 2016/2019/2021, click-to-run vs. MSI), and whether the installed bitness (32-bit vs. 64-bit) matches the robot process bitness.

### Lookup Range

1. **Workflow source** — read the `LookUpRange` / `LookUpRangeX` node from the `.xaml` to capture the literal `Range`, `Value` expression, `SheetName`, and `Output` variable, plus whether the activity is inside an `Excel Application Scope` / `Use Excel File` container. Distinguish an empty-string `Range = ""` from a genuinely blank `Range` field — they behave differently.
2. **Activity output, not just errors** — for the active-filter scenario the activity throws nothing; the symptom is a null/empty/wrong `Output`. Trace the `Output` variable downstream rather than only grepping for a `Lookup Range` error line.
3. **Workbook sheet/range inventory** — the actual tab names in the target workbook (to compare against `SheetName`) and whether any named range/table the activity references is defined (`Formulas > Name Manager`).
4. **Filter state** — whether the target worksheet has active AutoFilters / hidden rows that exclude the search value. Requires inspecting the workbook (or asking the user) — not visible in the job log.
5. **Excel-installed check** — for the Interop init failure, whether Microsoft Excel is installed on the execution host (`Control Panel > Programs and Features`, or the `App Paths\excel.exe` registry key) and whether the robot is a Linux/container host that cannot run Interop at all.
6. **File-lock state** — whether the workbook is open interactively, held by an orphaned `EXCEL.EXE`, touched by a concurrent job, or locked by a sync/AV client at the failure time.

## Testing Prerequisites

### Invoke VBA

When testing hypotheses for `Invoke VBA` issues, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity is `UiPath.Excel.Activities.Business.InvokeVBAX` (display name "Invoke VBA") and not a generic `Excel.Macros` or `Invoke Macro` activity, which run different code paths.
2. **Macro source file path** — exact path bound to `CodeFilePath`, resolved against the robot's working directory at job run time (relative paths are resolved against the project folder, not the workbook folder).
3. **Macro source file contents** — the full text of the `.txt`/`.vba`/`.bas` file at that path. Verify it contains a `Sub <Name>` or `Function <Name>` declaration matching `EntryMethodName`, no syntax errors, no encoding artifacts.
4. **Entry method name and signature** — exact `EntryMethodName` string, exact `Sub`/`Function` declaration in the code file (name, parameter count, parameter types). VBA is case-insensitive but parentheses and trailing whitespace are not.
5. **Parameter expression** — the expression bound to `EntryMethodParameters`. Confirm it evaluates to an `IEnumerable<Object>` (typically a `New Object() {...}` array, not a raw string or single value).
6. **Excel Process Scope properties** — `Visible` setting, `ShowOnPrompt` / dialog handling, workbook path, password (if any), and whether the scope runs with `WorkbookPath` set or against an already-open workbook.
7. **Trust Center setting** — captured directly from the robot machine under the running user account. The setting is not visible in Orchestrator and cannot be inferred from job logs alone — the user (or someone with desktop access on the host) has to check it.
8. **Package version** — `UiPath.Excel.Activities` version. The exception messages produced by `InvokeVBAX` have shifted across major versions (notably the 2.20 → 2.22 and 6.x rewrites).
9. **Office version and bitness** — the exact Excel version installed on the robot machine and whether it is 32-bit or 64-bit. Mismatch with robot bitness is a known cause of COM dispatcher errors.

### Lookup Range

When testing hypotheses for `Lookup Range` issues, gather and verify these before drawing conclusions:

1. **Activity surface** — confirm classic `UiPath.Excel.Activities.LookUpRange` (Interop, inside `Excel Application Scope`) vs modern `UiPath.Excel.Activities.LookUpRangeX` (inside `Use Excel File` / `Excel Process Scope`). The Excel-not-installed failure is most acute on the classic Interop surface.
2. **Range / Value / SheetName** — the literal `Range` (blank vs `""` vs A1 reference), the search `Value` expression and its .NET type, and the `SheetName`. These drive the invalid-range, null-reference, and active-filter hypotheses.
3. **Output disposition** — whether the activity threw or returned a null/empty/wrong cell address. A clean return with no match points at active filters or a value type/whitespace mismatch, not an exception path.
4. **Workbook sheet names and named ranges** — the actual tabs and defined names, compared character-for-character against `SheetName` and any named-range reference.
5. **Worksheet filter state** — active AutoFilters or hidden rows on the target sheet at run time.
6. **Excel installed + reachable** — whether desktop Excel is installed on the host (for Interop) and whether the workbook file is currently locked by another process.
