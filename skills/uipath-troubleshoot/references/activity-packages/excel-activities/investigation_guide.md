# Excel Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.Excel.Activities.Business.ReadRangeX`, `UiPath.Excel.Activities.ExcelReadRange`, `UiPath.Excel.Activities.Business.InvokeVBAX`, `UiPath.Excel.Activities.ExcelLookUpRange`, `UiPath.Excel.Activities.LookUpRangeX`). Classic Interop activities (inside an `Excel Application Scope`) and modern `*X` activities (inside `Use Excel File` / `Excel Process Scope`) share display names but run different code paths and surface different exception wrappings — treat them as different. `Invoke VBA` only exists on the modern (COM) surface; `Lookup Range` exists on both (classic `ExcelLookUpRange`, modern `LookUpRangeX`).
- **Workbook path** — the workbook path in evidence matches the file the user is asking about. Casing, drive-letter mapping, and UNC vs. mapped-drive forms can all differ between a user's mental model and the runtime path. `Invoke VBA` operates on the workbook open inside the surrounding `Excel Process Scope` — different scope = different workbook = unrelated data. Don't substitute a similar path.
- **Sheet name** — the configured `SheetName` matches the one the user reports. Sheet names are surfaced case-sensitively by the OpenXML provider; Excel COM is more forgiving.
- **Code file** — the `CodeFilePath` in evidence resolves to the macro source the user is asking about. A `.txt`/`.vba`/`.bas` file path that no longer exists on the robot machine, or a stale path checked into source control, is a different file than the one the user has open locally.
- **Entry method** — the `EntryMethodName` in evidence matches the macro the user reports calling. Don't substitute a similarly-named macro.
- **Workflow file** — if the project contains multiple workflows, the error originates from the `.xaml` / `.cs` the user is asking about, not a different workflow that happens to use the same activity.
- **Robot / machine identity** — the robot account and the machine where Excel is installed match the one the user reports. Excel install state, orphan `EXCEL.EXE` processes, AV/EDR posture, and security settings (Trust Center, Trust access to VBA project) are per-host (and per-user), so evidence from a different host is not transferable.
- **Office version** — the Excel/Office version installed on the robot machine matches the one the user reports. Multiple Office versions on the same host produce COM dispatcher ambiguity unrelated to a single-version user's experience.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for file-lock investigations (the locking process may no longer exist by the time you check), COM-interop investigations (transient `0x80010100` errors may not reproduce on demand), and Trust Center investigations (the setting may have been changed since).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Domain-Specific Data Gathering

1. **Container scope** — capture whether the activity ran inside `Excel Application Scope` (legacy) or `Use Excel File` (modern). The scope determines which provider is in use, whether Excel UI is visible, and whether file acquisition uses COM or OpenXML. Read the workflow source — the scope is not always visible in the runtime error string.
2. **Workbook provider** — for `Use Excel File`, capture whether the activity ran on the OpenXML provider or fell back to Excel COM. The `Read Formatting`, `Edit Password`, and macro-related properties force COM. Provider in use changes the exception wording and the set of supported features.
3. **Robot Execution.log** — `%LocalAppData%\UiPath\Logs\Execution.log` on the host. Captures the activity-level log lines around the failure; often shows the workbook open / close pair so the lock window is observable.
4. **Host-side process state** — for file-acquisition and COM failures, the host's process list at failure time is the authoritative evidence. If the user can capture `Get-Process EXCEL` or `handle.exe -a <path>` (Sysinternals) at the next failure, those are the strongest possible signals.

### Invoke VBA

1. **Workflow source** — read the `InvokeVBAX` activity node from the surrounding `.xaml` to capture the literal values of `CodeFilePath`, `EntryMethodName`, and the expression bound to `EntryMethodParameters`. Property panel summaries truncate; the XAML is authoritative.
2. **Code file contents** — read the macro source at the resolved `CodeFilePath`. Required to verify the `Sub`/`Function` declaration name and signature against `EntryMethodName` and `EntryMethodParameters`. Check encoding: a UTF-8 BOM, UTF-16, or stray control character will compile-fail.
3. **Excel Trust Center setting** — `File > Options > Trust Center > Trust Center Settings > Macro Settings > "Trust access to the VBA project object model"` on the robot machine, under the same Windows user that runs the robot. The setting is per-user-per-machine and per Office install.
4. **Excel state at failure time** — whether Excel.exe was running, whether any modal dialog was open (recover-unsaved-files banner, license activation, macro-warning bar, "trust this file" prompt), and whether `Visible = True` was set on the surrounding `Excel Process Scope` (without it, dialogs are invisible to the user but still block the macro).
5. **Office installation inventory** — number of Office versions installed on the host (Microsoft 365, perpetual Office 2016/2019/2021, click-to-run vs. MSI), and whether the installed bitness (32-bit vs. 64-bit) matches the robot process bitness.

### Lookup Range

1. **Workflow source** — read the `ExcelLookUpRange` / `LookUpRangeX` node from the `.xaml` to capture the literal `Range`, `Value` expression, `SheetName`, and `Output` variable, plus whether the activity is inside an `Excel Application Scope` / `Use Excel File` container. Distinguish an empty-string `Range = ""` from a genuinely blank `Range` field — they behave differently.
2. **Activity output, not just errors** — for the active-filter scenario the activity throws nothing; the symptom is a null/empty/wrong `Output`. Trace the `Output` variable downstream rather than only grepping for a `Lookup Range` error line.
3. **Workbook sheet/range inventory** — the actual tab names in the target workbook (to compare against `SheetName`) and whether any named range/table the activity references is defined (`Formulas > Name Manager`).
4. **Filter state** — whether the target worksheet has active AutoFilters / hidden rows that exclude the search value. Requires inspecting the workbook (or asking the user) — not visible in the job log.
5. **Excel-installed check** — for the Interop init failure, whether Microsoft Excel is installed on the execution host (`Control Panel > Programs and Features`, or the `App Paths\excel.exe` registry key) and whether the robot is a Linux/container host that cannot run Interop at all.
6. **File-lock state** — whether the workbook is open interactively, held by an orphaned `EXCEL.EXE`, touched by a concurrent job, or locked by a sync/AV client at the failure time.
7. **Formula-cell state of the target** — whether the cell the search value should match is the *computed* result of an Excel formula (and not a static value). Note any volatile functions, cross-sheet/external references, or add-in dependencies in the formula. Required to distinguish a formula-cell silent miss from the active-filters or type-mismatch causes.

## Testing Prerequisites

When testing hypotheses for Excel Activities issues, gather and verify these before drawing conclusions:

1. **Activity identity** — class name and display name from the workflow source or stack trace. Distinguish modern (`*X` / `ReadRangeX`) from legacy (`ReadRange`) — they belong to different activity families within the same NuGet package.
2. **Scope** — `Excel Application Scope` vs. `Use Excel File`. Determines provider and acquisition semantics.
3. **Workbook reference** — the configured workbook path expression (literal vs. variable), the resolved path at runtime if available, and the host filesystem on which the path is meant to resolve.
4. **Activity input properties** — every input the activity uses to address its target, from workflow source: `SheetName`, `Range`, `AddHeaders`, `PreserveFormat`, `Visible`, `EditPassword`, `ReadOnly`. The playbook will name the subset that matters.
5. **Host context** — host machine name, Excel version installed (or whether Excel is installed at all), Robot user that owned the failing job's session, AV/EDR product running on the host.
6. **Job run timestamp** — exact time the activity executed. Required for matching host-side process snapshots and for AV/EDR log correlation.
7. **Package version** — `UiPath.Excel.Activities` version from `project.json`. Exception messages, default provider, and the supported subset of OpenXML features have shifted across versions; version-specific bugs are documented in playbooks as they're discovered.

### Invoke VBA

When testing hypotheses for `Invoke VBA` issues, also gather and verify these:

1. **Activity identity** — confirm the faulted activity is `UiPath.Excel.Activities.Business.InvokeVBAX` (display name "Invoke VBA") and not a generic `Excel.Macros` or `Invoke Macro` activity, which run different code paths.
2. **Macro source file path** — exact path bound to `CodeFilePath`, resolved against the robot's working directory at job run time (relative paths are resolved against the project folder, not the workbook folder).
3. **Macro source file contents** — the full text of the `.txt`/`.vba`/`.bas` file at that path. Verify it contains a `Sub <Name>` or `Function <Name>` declaration matching `EntryMethodName`, no syntax errors, no encoding artifacts.
4. **Entry method name and signature** — exact `EntryMethodName` string, exact `Sub`/`Function` declaration in the code file (name, parameter count, parameter types). VBA is case-insensitive but parentheses and trailing whitespace are not.
5. **Parameter expression** — the expression bound to `EntryMethodParameters`. Confirm it evaluates to an `IEnumerable<Object>` (typically a `New Object() {...}` array, not a raw string or single value).
6. **Excel Process Scope properties** — `Visible` setting, `ShowOnPrompt` / dialog handling, workbook path, password (if any), and whether the scope runs with `WorkbookPath` set or against an already-open workbook.
7. **Trust Center setting** — captured directly from the robot machine under the running user account. Not visible in Orchestrator and not inferable from job logs alone — the user (or someone with desktop access on the host) has to check it.
8. **Office version and bitness** — the exact Excel version installed on the robot machine and whether it is 32-bit or 64-bit. Mismatch with robot bitness is a known cause of COM dispatcher errors.

### Lookup Range

When testing hypotheses for `Lookup Range` issues, also gather and verify these:

1. **Activity surface** — confirm classic `UiPath.Excel.Activities.ExcelLookUpRange` (Interop, inside `Excel Application Scope`) vs modern `UiPath.Excel.Activities.LookUpRangeX` (inside `Use Excel File` / `Excel Process Scope`). The Excel-not-installed failure is most acute on the classic Interop surface.
2. **Range / Value / SheetName** — the literal `Range` (blank vs `""` vs A1 reference), the search `Value` expression and its .NET type, and the `SheetName`. These drive the invalid-range, null-reference, and active-filter hypotheses.
3. **Output disposition** — whether the activity threw or returned a null/empty/wrong cell address. A clean return with no match points at active filters or a value type/whitespace mismatch, not an exception path.
4. **Workbook sheet names and named ranges** — the actual tabs and defined names, compared character-for-character against `SheetName` and any named-range reference.
5. **Worksheet filter state** — active AutoFilters or hidden rows on the target sheet at run time.
6. **Excel installed + reachable** — whether desktop Excel is installed on the host (for Interop) and whether the workbook file is currently locked by another process.
