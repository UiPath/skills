# Word Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (`UiPath.Word.Activities.WordApplicationScope`, `UiPath.Word.Activities.WordReplaceText` / `ReplaceTextInDocument`, and `Read Text`). Classic activities (inside `Word Application Scope`, Interop) and modern activities (inside `Use Word File`) share display names but run different code paths — treat them as different. For `Read Text`, also distinguish the **Word-pack** activity (needs a container) from the **standalone** `System > File > Word Document` `Read Text` (takes a file path, `.docx`-only) — they fail for different reasons. A substitution/extraction fault is distinct from a scope-level fault: the scope opened fine and the failure is in the activity.
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
7. **Replace Text inputs + outcome** — for `Replace Text in Document` faults, capture the `Search` and `Replace` expressions (and their runtime lengths — 256 chars is the classic cap), whether the activity threw or succeeded-with-no-change, and whether it sits inside a loop with `Auto Save` enabled. For a silent miss, inspect the template's placeholder for run-splitting / mixed formatting; trace the **output document content**, not just the absence of an exception.

## Testing Prerequisites

When testing hypotheses for `Word Application Scope` issues, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity is `UiPath.Word.Activities.WordApplicationScope` and not the modern `Use Word File` activity, which runs a different code path.
2. **Document path** — exact path bound to the scope, resolved against the robot's working directory at run time (relative paths resolve against the project folder, not the document folder).
3. **Word installation + bitness** — desktop Word present on the robot machine and its bitness relative to the robot process. The user (or someone with desktop access) must check; it cannot be inferred from job logs.
4. **Interactive state** — whether a background dialog was blocking. Reproduce with the scope visible to confirm.
5. **Package version** — `UiPath.Word.Activities` version available on the execution host, compared against `project.json`.

When testing hypotheses for `Replace Text in Document` issues:

1. **Activity surface** — classic `WordReplaceText` (inside `Word Application Scope`) vs modern `ReplaceTextInDocument` (inside `Use Word File`). The 256-char limit is a classic-version constraint.
2. **Search / Replace values** — the literal expressions and their .NET string lengths at run time; confirm an exact character-for-character match against the on-screen placeholder for a silent miss, and check >256 chars for the length-limit hypothesis.
3. **Throw vs no-op** — whether the activity raised an exception (COM busy, file lock, ArgumentException) or completed with the document unchanged. A clean run with no substitution points at the template/content, not an exception path. Distinguish the silent causes: run-split placeholder (fails every row), placeholder consumed by a prior loop iteration (first row works, later rows don't), or content outside the body (headers/footers/text boxes skipped by an old package).
4. **Loop behaviour** — whether the scope runs inside a loop over the **same path**: with `Auto Save` on it's the file-lock cause; editing the template **in place** (no per-iteration copy) is the placeholder-consumed cause (first iteration succeeds, rest don't).
5. **Where the unreplaced text lives** — body vs header / footer / text box / shape; non-body misses point at an older `UiPath.Word.Activities` version. And whether the `Replace` value carries `Environment.NewLine` (multi-line formatting loss).
6. **Studio vs package version** — for a design-time `TargetInvocationException` / crash on drop, the Studio version against the installed `UiPath.Word.Activities` version (distinct from a runtime package gap).

When testing hypotheses for `Read Text` issues:

1. **Which Read Text surface** — Word-pack `Read Text` (requires a `Use Word File` / `Word Application Scope` container) vs standalone `System > File > Word Document` `Read Text` (own file path, `.docx`-only). The container vs format failures are surface-specific.
2. **Container placement** — whether the Word-pack `Read Text` is nested inside a scope; a design-time validation warning / runtime invalid-context fault points at missing-container.
3. **File format** — `.doc` (legacy binary) vs `.docx` (OpenXML); the standalone System activity fails on `.doc`. Check the real format, not just the extension.
4. **File origin** — downloaded / email / external-share (Mark-of-the-Web → Protected View) vs locally created. A read that fails only on externally-sourced files points at Protected View.
5. **Word busy** — for a `0x8001010A` / `RPC_E_SERVERCALL_RETRYLATER` on the read, the same busy-WINWORD checks as the Replace Text COM-busy case apply.
