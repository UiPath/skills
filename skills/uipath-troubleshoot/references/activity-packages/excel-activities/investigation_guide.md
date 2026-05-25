# Excel Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's class matches the reported failure (`UiPath.Excel.Activities.Business.ReadRangeX`, `UiPath.Excel.Activities.ExcelReadRange`, `UiPath.Excel.Activities.Read.ReadColumn`, etc.). Legacy (`Excel Application Scope` family) and modern (`Use Excel File` family) share display names but run different code paths and surface different exception wrappings — treat them as different.
- **Workbook path** — the file path the activity tried to open matches the one the user reports. Casing, drive-letter mapping, and UNC vs. mapped-drive forms can all differ between a user's mental model and the runtime path. Don't substitute a similar path.
- **Sheet name** — the configured `SheetName` matches the one the user reports. Sheet names are surfaced case-sensitively by the OpenXML provider; Excel COM is more forgiving.
- **Workflow file** — if the project contains multiple workflows, the error originates from the `.xaml` / `.cs` the user is asking about, not a different workflow that happens to use the same activity.
- **Host machine** — the failure occurred on the host the user reports. Excel install state, orphan `EXCEL.EXE` processes, and AV/EDR posture differ per host.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for file-lock investigations (the locking process may no longer exist by the time you check).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Domain-Specific Data Gathering

1. **Container scope** — capture whether the activity ran inside `Excel Application Scope` (legacy) or `Use Excel File` (modern). The scope determines which provider is in use, whether Excel UI is visible, and whether file acquisition uses COM or OpenXML. Read the workflow source — the scope is not always visible in the runtime error string.
2. **Workbook provider** — for `Use Excel File`, capture whether the activity ran on the OpenXML provider or fell back to Excel COM. The `Read Formatting`, `Edit Password`, and macro-related properties force COM. Provider in use changes the exception wording and the set of supported features.
3. **Robot Execution.log** — `%LocalAppData%\UiPath\Logs\Execution.log` on the host. Captures the activity-level log lines around the failure; often shows the workbook open / close pair so the lock window is observable.
4. **Host-side process state** — for file-acquisition failures, the host's process list at failure time is the authoritative evidence. If the user can capture `Get-Process EXCEL` or `handle.exe -a <path>` (Sysinternals) at the next failure, those are the strongest possible signals.

## Testing Prerequisites

When testing hypotheses for Excel Activities issues, gather and verify these before drawing conclusions:

1. **Activity identity** — class name and display name from the workflow source or stack trace. Distinguish modern (`*X` / `ReadRangeX`) from legacy (`ReadRange`) — they belong to different activity families within the same NuGet package.
2. **Scope** — `Excel Application Scope` vs. `Use Excel File`. Determines provider and acquisition semantics.
3. **Workbook reference** — the configured workbook path expression (literal vs. variable), the resolved path at runtime if available, and the host filesystem on which the path is meant to resolve.
4. **Activity input properties** — every input the activity uses to address its target, from workflow source: `SheetName`, `Range`, `AddHeaders`, `PreserveFormat`, `Visible`, `EditPassword`, `ReadOnly`. The playbook will name the subset that matters.
5. **Host context** — host machine name, Excel version installed (or whether Excel is installed at all), Robot user that owned the failing job's session, AV/EDR product running on the host.
6. **Job run timestamp** — exact time the activity executed. Required for matching host-side process snapshots and for AV/EDR log correlation.
7. **Package version** — `UiPath.Excel.Activities` version from `project.json`. Exception messages, default provider, and the supported subset of OpenXML features have shifted across versions; version-specific bugs are documented in playbooks as they're discovered.
