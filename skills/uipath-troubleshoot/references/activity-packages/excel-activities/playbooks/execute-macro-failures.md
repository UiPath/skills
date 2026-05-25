---
confidence: medium
---

# Execute Macro / Run Spreadsheet Macro Failures

## Context

A `UiPath.Excel.Activities` Execute Macro activity (classic `ExecuteMacro`, or modern `Run Spreadsheet Macro` under `Use Excel File`) runs a VBA macro inside the open workbook. The activity bridges UiPath's managed runtime to Excel via COM; failures can originate in the macro's VBA code, in Excel's COM dispatch, in the Robot host's Excel configuration, or in the bridge between the two.

What this looks like — most failures surface as `System.Runtime.InteropServices.COMException`, often with one of these HRESULTs / messages:

- `0x80020009 (DISP_E_EXCEPTION)` — "Exception occurred." The macro itself threw a VBA error via `IDispatch`. The inner VBA error (Object required, Subscript out of range, Type mismatch, Application-defined or object-defined error) is the load-bearing detail.
- `0x800A03EC` — generic Excel error during macro execution.
- `0x800AC472` — apartment-threading violation from concurrent COM access.
- `Cannot run the macro '<name>'. The macro may not be available in this workbook or all macros may be disabled.` — Excel's own error message wrapped in a COMException.

Failures may also surface as:
- Job hangs with no exception — Excel modal dialog (`MsgBox`, `InputBox`, VBA `Stop` / `Debug.Print` break, "End/Continue" recovery dialog) waiting for a user response that the Robot's unattended session cannot provide.
- `UiPath.Excel.BusinessException` — Excel COM rejected the macro call before it ran.

What can cause it (cause-branches — pick the right one from evidence):

1. **Macro name not found in the workbook** — configured `Macro` property is a name (`MyModule.RunImport` or `RunImport`) that does not exist in any code module of the open workbook. Symptom: COMException with message `Cannot run the macro '<name>'. The macro may not be available in this workbook or all macros may be disabled.` Causes: typo, macro renamed upstream, macro lives in a different workbook / add-in, module-qualifier mismatch.
2. **VBA error inside the macro (DISP_E_EXCEPTION)** — the macro ran but its VBA code threw. The activity sees the COM `DISP_E_EXCEPTION` wrapper but the inner detail is the VBA error: `Run-time error '91': Object variable or With block variable not set`, `Run-time error '9': Subscript out of range`, `Run-time error '13': Type mismatch`, `Run-time error '1004': Application-defined or object-defined error`, etc. Causes: bug in the macro itself, assumption about workbook contents that doesn't hold at runtime, dependency on a worksheet / range / named cell that isn't there.
3. **Macro tears down the Excel instance** — the VBA code calls `Workbooks.Close`, `ActiveWorkbook.Close`, `Application.Quit`, `ThisWorkbook.Close`, or similar. The UiPath Excel Application Scope (or `Use Excel File` with COM) owns the Excel instance; when the macro shuts it down, the next activity finds the COM object gone. Symptom: COMException with HRESULT like `0x80010108 (RPC_E_DISCONNECTED)` on the NEXT activity, not necessarily the macro itself. Macro may have logged "succeeded" before tearing down.
4. **Modal dialog from macro** — the VBA code displays `MsgBox`, `InputBox`, or a custom `UserForm`, OR Excel's own dialog (e.g., "There is already data in [cell]. Do you want to replace it?" from a write that conflicts) interrupts execution. Symptom: job hangs indefinitely; no exception; the Robot eventually times out (turn timeout, `UIPATH_SESSION_TIMEOUT`, or operator manual kill). Excel COM cannot respond while a modal dialog is open.
5. **Macros disabled by Trust Center policy on the Robot host** — Excel's Trust Center on the Robot user's profile has `Disable all macros without notification` (or `Disable VBA macros except digitally signed`) and the workbook's macros are not in a trusted location or signed by a trusted publisher. Symptom: COMException `Cannot run the macro '<name>'. The macro may not be available in this workbook or all macros may be disabled.` Same error string as branch 1, but the macro DOES exist in the workbook. Distinguish by: macro name confirmed present + workbook works on developer's host (interactive Excel where Trust Center has dev defaults) → branch 5; macro name absent in workbook → branch 1.
6. **Concurrent COM access (apartment violation)** — Excel COM is single-threaded apartment (STA). When multiple parallel activities (or a separate automation, e.g., another Robot job on the same host) call into the Excel COM apartment, the second caller hits `0x800AC472` or `RPC_E_SERVERCALL_RETRYLATER`. Symptom: COMException with one of those HRESULTs; intermittent (only when the parallel call lands during macro execution); fails more on multi-Robot hosts.
7. **Macro depends on missing add-in or ActiveX control** — the VBA code references an add-in (`Tools → References` in the VBE) or ActiveX control that is registered on the developer's machine but NOT on the Robot host (or registered under a different user profile than the Robot's). Symptom: VBA error `Run-time error '424': Object required` or `Compile error: Can't find project or library`; surfaces as `DISP_E_EXCEPTION` like branch 2 but the inner is a missing-reference error rather than a logic bug.

What to look for:
- **The exact COMException HRESULT / message** — the strongest first signal. `0x80020009 DISP_E_EXCEPTION` → branch 2 or 7. `Cannot run the macro '<name>'...` → branch 1 or 5. `RPC_E_DISCONNECTED` on a subsequent activity → branch 3. `0x800AC472` → branch 6. Job hangs / no exception → branch 4.
- **The inner VBA error message** if visible in the exception's `Message` or in the activity's Trace logs. UiPath usually captures the macro's `Err.Description` in the COMException wrapper.
- **Workflow source** — confirm the configured `Macro` name (literal vs. expression), whether the scope is `Excel Application Scope` (classic, COM-only) or `Use Excel File` with COM-forcing properties, and whether parallel activities access Excel.
- **Robot host's Excel configuration** — Trust Center settings (`File → Options → Trust Center → Trust Center Settings → Macro Settings`), Trusted Locations, installed add-ins under the Robot user.
- **Workbook contents** — does the macro name exist in the workbook's VBA code? Macros in `Personal.xlsb` are NOT in the open workbook; they're in a separate workbook loaded on Excel startup. Robots usually don't load `Personal.xlsb`.
- **Run pattern** — every run fails → persistent (branches 1, 3, 5, 7). Intermittent → branch 6 (concurrent) or branch 4 (modal dialog only on certain inputs).

## Investigation

1. **Capture the exact error.** From `or jobs get <job-key> --output json`: the exception class, full message, HRESULT (if a COMException), and any inner exception or VBA error text the activity surfaced. From workflow source: the activity, configured `Macro` name (literal or expression), and the scope.

2. **Categorize the symptom.**
   - Job has an exception → continue to step 3.
   - Job hangs / times out with no exception → **branch 4** (modal dialog). Confirm: the macro is known to display a dialog under certain inputs, or Excel surfaced a dialog (data-overwrite warning, recovery dialog, end/continue debug prompt). Skip to Resolution.

3. **Match the HRESULT / error message to a branch.**
   - `Cannot run the macro '<name>'. The macro may not be available in this workbook or all macros may be disabled.` → branches 1 or 5; go to step 4.
   - `0x80020009 (DISP_E_EXCEPTION)` → branches 2 or 7; go to step 5.
   - `0x80010108 (RPC_E_DISCONNECTED)` on the NEXT activity after the macro → branch 3; go to step 6.
   - `0x800AC472` / `RPC_E_SERVERCALL_RETRYLATER` → branch 6; go to step 7.
   - Other HRESULT → check Microsoft's HRESULT documentation; default to inspecting the workbook source.

4. **Distinguish branches 1 vs. 5 (macro-not-found vs. macros-disabled).** Ask the user to verify:
   - **Open the workbook in Excel** (on any host) → `Alt+F11` (VBA editor). Confirm the configured macro name exists in a code module. If absent → **branch 1** (name mismatch, typo, or macro in a different scope). If present → continue.
   - **On the Robot host, under the Robot user's profile**: open Excel → `File → Options → Trust Center → Trust Center Settings → Macro Settings`. If set to `Disable all macros without notification` or `Disable all macros with notification` (and the workbook is not in a trusted location / signed) → **branch 5** (macros disabled).
   - The user's own dev workstation having a permissive Trust Center setting is the canonical "works on dev / fails on Robot" pattern for branch 5.

5. **Distinguish branches 2 vs. 7 (VBA bug vs. missing dependency).** Look at the inner VBA error text from the COMException:
   - `Run-time error '91': Object variable or With block variable not set` — usually branch 2 (logic bug).
   - `Run-time error '9': Subscript out of range` — usually branch 2 (worksheet / range assumption).
   - `Run-time error '13': Type mismatch` — usually branch 2.
   - `Run-time error '1004': Application-defined or object-defined error` — could be either; ambiguous. Check what the macro was doing at the time.
   - `Run-time error '424': Object required` or `Compile error: Can't find project or library` — **branch 7** (missing reference / add-in / ActiveX).
   - `Run-time error '429': ActiveX component can't create object` — **branch 7** (control not registered under Robot user).

6. **Confirm branch 3 (macro tears down Excel).** Inspect the VBA source. Search for `Close`, `Quit`, `ThisWorkbook.Close`, `ActiveWorkbook.Close`, `Application.Quit`. The macro must not call any of these — UiPath owns the Excel lifecycle. If found, branch 3 is confirmed.

7. **Confirm branch 6 (concurrent COM access).** Look for:
   - The workflow uses `Parallel` activities containing Excel calls.
   - Multiple Robot jobs against the same workflow on the same host (`uip or jobs list --process-name '<process>' --host '<MOCK-HOST>'`) overlap with the macro window.
   - A different automation on the same host using Excel (PowerShell, another RPA tool, scheduled VBA add-in).
   - Failures are intermittent — the symptom of an STA race.

The root cause must name the specific HRESULT / VBA error / Trust Center setting / VBA call / concurrency pattern responsible. A generic "the macro failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Macro name not found:**
  - Open the workbook in Excel and confirm the macro's actual qualified name (module name + sub name: `Module1.RunImport`). Update the activity's `Macro` property to match verbatim.
  - If the macro lives in a separate workbook / add-in, change the workflow to either open that source (Excel Application Scope on the source file, then run macro), or move the macro into the target workbook.
  - `Personal.xlsb` macros are not available to Robot sessions by default (the Robot user's Excel does not auto-load `Personal.xlsb`). Move the macro into the project workbook or into a workbook the workflow explicitly opens.
  - Prevention: name macros with explicit module qualifiers (`Module1.RunImport`, not `RunImport`); document the macro contract between workbook publisher and workflow consumer.

- **Branch 2 — VBA error inside the macro:**
  - Open the workbook in Excel, `Alt+F11` to the VBE, and reproduce the macro under the same inputs. The VBE will break at the offending line.
  - Fix the VBA logic. Common patterns: null-safe object references (`If Not rng Is Nothing Then`), explicit sheet qualifiers (`ThisWorkbook.Sheets("Data").Range("A1")` rather than `Range("A1")`), defensive type checking before assignment.
  - For long-running macros, add structured error handling in VBA: `On Error GoTo ErrHandler` + `Err.Raise` with a clear description, so the COMException surfaces a useful message rather than a generic DISP_E_EXCEPTION.
  - Prevention: unit-test macros on the same data shapes the workflow will produce. Do not rely on workbook state assumptions that the workflow's earlier activities could violate.

- **Branch 3 — Macro tears down Excel:**
  - Remove `Workbooks.Close`, `ActiveWorkbook.Close`, `Application.Quit`, `ThisWorkbook.Close` from the VBA. UiPath owns the Excel lifecycle when the macro runs inside Excel Application Scope or `Use Excel File`.
  - If the macro genuinely needs to dismiss the workbook (e.g., it opened a different workbook for processing), have it close ONLY workbooks it opened itself, never `ThisWorkbook` or `ActiveWorkbook` when those are the host workbook.
  - Prevention: workbook publisher and workflow author should agree on a contract — macros run inside UiPath's scope must not modify the application lifecycle. Add a code-review checklist for VBA macros that will be invoked from UiPath.

- **Branch 4 — Modal dialog from macro:**
  - Remove `MsgBox`, `InputBox`, and `UserForm.Show` calls from the macro. Replace with logging to a worksheet, an `Err.Raise` with a descriptive message, or a status output range the workflow reads after the macro finishes.
  - For Excel's own dialogs (data-overwrite warnings, save-as prompts), set `Application.DisplayAlerts = False` at the start of the macro (and `True` at the end). Note this suppresses ALL Excel dialogs during the macro, including legitimate confirmation prompts — use deliberately.
  - For VBA debug interruptions (`Stop`, `Debug.Print` with breakpoints): remove all `Stop` statements and clear all breakpoints before saving the workbook for production.
  - Prevention: ban interactive UI calls in VBA macros that run under UiPath. Macros are headless; they must not require user input.

- **Branch 5 — Macros disabled by Trust Center:**
  - **Preferred:** add the workbook's containing folder to Excel's Trusted Locations under the Robot user's profile. Open Excel as the Robot user → `File → Options → Trust Center → Trust Center Settings → Trusted Locations → Add new location`. Persistent under that user.
  - Alternative: sign the macro with a code-signing certificate that's trusted on the Robot host, and set Trust Center to `Disable VBA macros except digitally signed macros`.
  - Last resort (security-relaxed): set `Enable VBA macros` (the most permissive option) on the Robot user's Excel. Acceptable only when the Robot host is dedicated to trusted automation and not used for general Office work.
  - Prevention: when provisioning Robot hosts, configure Excel's Trusted Locations as part of host setup. Document the location list in the host build runbook.

- **Branch 6 — Concurrent COM access:**
  - Serialize Excel access. Options:
    - Remove `Parallel` activities that touch Excel; run those branches sequentially.
    - If multiple Robot jobs on the same host need Excel, serialize via a per-host lock asset OR a single-performer queue on the workflow.
    - If another automation on the host uses Excel, separate them (different hosts, or coordinated schedules).
  - For unavoidable intermittent races, add a Retry Scope around Execute Macro with exponential back-off (3 attempts, 5s / 15s / 30s). Excel COM apartment violations are usually transient — a short wait often unblocks them.
  - Prevention: do not design workflows that parallel-call into Excel COM. Single-threaded apartment is a hard constraint, not a quirk.

- **Branch 7 — Missing add-in or ActiveX control:**
  - Identify the missing reference: open the workbook in Excel on the Robot host (under the Robot user) → `Alt+F11` → `Tools → References`. Any reference marked "MISSING:" is the culprit.
  - Install / register the add-in or control on the Robot host under the Robot user's profile. Add-ins: copy the `.xlam` / `.xla` to `%AppData%\Microsoft\AddIns\` and enable in Excel's Add-ins dialog. ActiveX: `regsvr32 <control.dll>` as admin, but verify the control is licensed for unattended use.
  - Alternative: rewrite the macro to not depend on the missing reference (early binding → late binding via `CreateObject`, OR remove the dependency entirely if possible).
  - Prevention: document every external dependency the workbook's macros require. Provision Robot hosts with that dependency list; verify with a smoke-test workflow that exercises each macro.

## Anti-patterns (what NOT to do)

Common advice for ExecuteMacro failures contains workarounds that hide bugs rather than fix them. The agent should NOT recommend either as a primary resolution.

- **"Add a `Delay` activity before Execute Macro."** A `Delay` is a workaround for a race condition or initialization issue that the workflow author has not actually diagnosed. It "works" intermittently and hides the underlying bug — usually branch 3 (Excel torn down by a previous macro), branch 6 (concurrent COM access), or genuine workbook write-flush latency. A reliable fix names the specific timing dependency and addresses it (sequence activities correctly, use `DoEvents` in VBA before returning, configure `Application.CalculateUntilAsyncQueriesDone = True` for power-query workbooks). If a `Delay` is genuinely required, treat it as a diagnosis hint about an underlying timing problem, document the dependency in a comment, and pick a duration that's an order of magnitude above the worst observed case rather than the minimum that "works."

- **"Wrap Execute Macro in a Try Catch and continue on error."** A bare Try-Catch that catches `COMException` (or `System.Exception`) and only logs without re-throwing turns macro failures into silent skips — the workflow proceeds as if the macro succeeded, producing wrong outputs, missing data, and downstream failures that are much harder to diagnose than the original COMException. Use Try-Catch only with a real recovery path: fall back to a different macro, mark a queue item Failed with the COMException message, send a notification, or re-throw a domain-specific exception. The same anti-pattern is called out in [`read-range-file-locked.md`](./read-range-file-locked.md) (orphan EXCEL.EXE), [`read-range-sheet-not-found.md`](./read-range-sheet-not-found.md), and [`read-range-null-reference.md`](./read-range-null-reference.md) — silent exception suppression around Excel activities is consistently harmful, not helpful.

## Prevention (cross-branch)

- Workbook authors must treat macros invoked from UiPath as headless: no `MsgBox`, no `InputBox`, no `UserForm`, no `Stop` / debug breakpoints. Failures surface via `Err.Raise` or a status range, not via UI.
- Macros must not change Excel's application lifecycle (no `Workbooks.Close` / `Application.Quit` / etc.). UiPath owns it.
- VBA must use explicit qualifiers (`ThisWorkbook.Sheets("Data").Range("A1")`) not implicit `ActiveSheet` / `Selection`. The Robot's session may not have the same active context as the developer's interactive Excel.
- Robot hosts should be provisioned with: Excel's Trusted Locations covering the automation data folder; the same add-ins as the developer's machine; the same ActiveX controls registered under the Robot user; the Trust Center macro setting compatible with the workbook's signing posture.
- Workflow authors should:
  - Validate the configured `Macro` name against the workbook before invocation (a smoke-test enumerator that lists VBA macros, similar to `Get Workbook Sheets` for sheets).
  - Never use `Delay` to paper over Excel timing issues.
  - Never use bare `Try Catch` around Excel activities; always pair Catch with a real recovery action.
  - Serialize Excel access — no `Parallel` activities touching Excel, single-performer queues for cross-job concerns.

## Related

- Other Excel Activities failure fingerprints (read-side failures) are separate playbooks — see [`../summary.md`](../summary.md).
- The "Try-Catch suppression around Excel scopes" anti-pattern is consistent across all Excel playbooks; reinforcing it here.
- For headless Excel automation that does NOT need VBA macros, consider migrating the macro logic into UiPath activities or the cloud surface (`o365-activities/overview.md`). Macros are a portability hazard between developer and Robot environments; native UiPath logic is more deterministic.
