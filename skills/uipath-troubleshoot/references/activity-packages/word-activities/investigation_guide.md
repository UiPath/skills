# Word Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (`UiPath.Word.Activities.WordApplicationScope`, `UiPath.Word.Activities.WordReplaceText` / `ReplaceTextInDocument`, and `Read Text`). Classic `Word Application Scope` (Interop) and the modern `Use Word File` surface share intent but run different code paths — treat them as different. For `Read Text`, also distinguish the **Word-pack** activity (needs a container) from the **standalone** `System > File > Word Document` `Read Text` (takes a file path, `.docx`-only) — they fail for different reasons. A substitution/extraction fault is distinct from a scope-level fault: the scope opened fine and the failure is in the activity. `Export to PDF` (`WordExportToPdf`) faults are about the **output** (missing directory, malformed path) or **COM** (orphaned WINWORD), not the document content. `Append Text` (`WordAppendText`) has the same App-Integration-vs-standalone split as Read Text (container required vs file path), plus a 0-byte-file ("Archive file cannot be size zero") signature; its install / lock / version faults are shared with the scope-level playbooks.
- **Faulting frame** — the deepest `UiPath.Word.*` stack frame routes to the right playbook: `WordAppHelpers.StartNewApplication` / `ComAppReferenceCountManager.StartOrAttach` = COM **start** failure (Word couldn't launch — background/Session-0, not-installed, or broken registration); `WordDocumentFactory.OpenOrCreateNewDocument` / `Documents.Open` = **open** failure (bad or URL `FilePath`); a child cast to `_Document` (IID `{0002096B-...}`) = **wrong-thread** apartment fault. Do not apply one signature's cause to a different frame. For a COM-start failure on an unattended run, read `runtimeOptions.requiresUserInteraction` in `project.json`: `false` ⇒ Background Process ⇒ Session 0 with no interactive session (the primary COM-start cause).
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
8. **External Word state + run surface** — for a COM wrong-thread fault (`0x8001010E`), whether `WINWORD.EXE` was already running when the run started and whether it stayed open through the operation, plus the run surface (foreground Studio vs unattended / Session 0 / background) and whether the faulting activity runs on a non-creator thread (Parallel/Pick/Invoke/coded). The fault depends on an externally-owned instance and the apartment the proxy is accessed from.

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
3. **Throw vs no-op** — whether the activity raised an exception (COM busy, file lock, ArgumentException) or completed with the document unchanged (run-split placeholder). A clean run with no substitution points at the template, not an exception path.

When testing hypotheses for `Read Text` issues:

1. **Which Read Text surface** — Word-pack `Read Text` (requires a `Use Word File` / `Word Application Scope` container) vs standalone `System > File > Word Document` `Read Text` (own file path, `.docx`-only). The container vs format failures are surface-specific.
2. **Container placement** — whether the Word-pack `Read Text` is nested inside a scope; a design-time validation warning / runtime invalid-context fault points at missing-container.
3. **File format + origin** — for the standalone activity, whether the input is legacy `.doc` (unsupported, `.docx`-only) and whether the file came from email/internet/external share (Mark-of-the-Web → Protected View block).

When testing hypotheses for `Export to PDF` (`WordExportToPdf`) issues:

1. **Output path** — capture the literal output File Path. Does the **parent folder exist** on the host (missing folder → generic `Command Failed`)? Does it end in `.pdf` with one clean separator and no empty variable segments (malformed path → save failure)?
2. **Generic `Command Failed` carries no detail** — disambiguate by checking folder existence and path format before assuming COM.
3. **COM state** — for a hang/crash/`COMException`, check for orphaned `WINWORD.EXE` and whether the input document is locked/open elsewhere.
4. **Package vs Studio version** — for a `TargetInvocationException`, compare `UiPath.Word.Activities` against the Studio version (same as the Replace Text version-mismatch case).
