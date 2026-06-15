# Word Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (`UiPath.Word.Activities.WordApplicationScope`). Classic `Word Application Scope` (Interop) and the modern `Use Word File` surface share intent but run different code paths — treat them as different.
- **Document** — the document path in evidence matches the file the user is asking about. A scope pointed at a different document is unrelated data.
- **Robot / machine identity** — the robot account and the machine where Word is installed match the one the user reports. Word installation, bitness, activation state, and Trust Center settings are per-user-per-machine, so evidence from a different host is not transferable.
- **Office version and bitness** — the Word/Office version and bitness installed on the robot machine match what the user reports. Bitness mismatch with the robot process is a known COM-interop cause; multiple Office installs produce dispatcher ambiguity.
- **Package version** — the `UiPath.Word.Activities` version referenced in `project.json` matches what is installed on the execution host. A "cannot create unknown type" error is a version/restore mismatch, not a runtime defect.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for hang/COM investigations (a transient lock or background dialog may not reproduce on demand).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## What to Capture

1. **Workflow source** — read the `WordApplicationScope` node from the `.xaml` to capture the literal document `Path` expression, `CreateIfNotExists`, `Password`, and whether the scope runs visible or unattended. Property-panel summaries truncate; the XAML is authoritative.
2. **Word installed + bitness** — whether desktop Word is installed on the execution host (`Control Panel > Programs and Features`, or `HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\winword.exe`), and the Office bitness (`File > Account > About Word`) versus the robot process bitness.
3. **Robot type** — whether the host is a Linux/container robot that cannot run Interop at all.
4. **Process state at failure time** — whether WINWORD.EXE was already running or orphaned, and whether any modal dialog (password, recovery sidebar, Safe Mode, activation, Protected View) was open. Without `Visible = True`, dialogs are invisible but still block COM calls.
5. **Document path resolution** — the concrete path the dynamic expression resolves to on the robot host (not the developer machine), whether the file exists there, and whether it is held open by a sync client, antivirus, or a concurrent job.
6. **Package version** — `UiPath.Word.Activities` version in `project.json` versus the version restored on the execution host, especially for remote/Orchestrator runs.

## Testing Prerequisites

When testing hypotheses for `Word Application Scope` issues, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity is `UiPath.Word.Activities.WordApplicationScope` and not the modern `Use Word File` activity, which runs a different code path.
2. **Document path** — exact path bound to the scope, resolved against the robot's working directory at run time (relative paths resolve against the project folder, not the document folder).
3. **Word installation + bitness** — desktop Word present on the robot machine and its bitness relative to the robot process. The user (or someone with desktop access) must check; it cannot be inferred from job logs.
4. **Interactive state** — whether a background dialog was blocking. Reproduce with the scope visible to confirm.
5. **Package version** — `UiPath.Word.Activities` version available on the execution host, compared against `project.json`.
