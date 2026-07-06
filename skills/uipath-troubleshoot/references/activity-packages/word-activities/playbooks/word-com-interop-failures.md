---
confidence: medium
---

# Word COM / Office Interop Failures & Word Process Crashes

## Context

This playbook covers **environmental / host-level** failures of the Word COM (Office Interop) layer that the `UiPath.Word.Activities` package depends on. It is **not specific to one activity** — any operation that drives a real `WINWORD.EXE` through Office Interop can surface these, including the `Use Word File` (`WordProcessScope`) / `Word Application Scope` container itself and the activities inside it (`Add Picture`, `Replace Text`, `Get Text`, `Set Bookmark Content`, `Export to PDF`, etc.). When the failure is genuinely activity-specific (a misplaced activity, a missing bookmark, a bad image path), use that activity's own playbook instead — this one is for the COM/host layer that is common to all of them.

What this looks like:
- `System.InvalidCastException: Unable to cast COM object of type 'System.__ComObject' / 'Microsoft.Office.Interop.Word.ApplicationClass' to interface type 'Microsoft.Office.Interop.Word._Application'` (or `_Document`), carrying an `(Exception from HRESULT: 0x…)`.
- `The application is busy` / a call-rejected or retry HRESULT.
- **Microsoft Word (`WINWORD.EXE`) itself faults and closes** mid-operation, and the activity then throws a COM cast / RPC error on its async-completion path (e.g. `UiPath.Word.Activities.WordInteropActivity.EndExecute`).
- The job runs fine in Studio on the developer's machine but faults only on a specific robot host — a strong tell of an **environmental** difference, not a source bug.

## Causes

Name the confirmed sub-cause exactly. Do NOT assert a cause unless the investigation decision tree arrived at it.

- **E1. COM type library / class not registered.** `0x8002801D` (`TYPE_E_LIBNOTREGISTERED`, "Library not registered") or the sibling `0x80040154` (`REGDB_E_CLASSNOTREG`, "Class not registered"). The cast to the Word `_Application` interface fails **during Word COM startup** (`WordApplicationScopeRuntime.EnsureWordApplication`), before any document work. Typically follows a partial or failed Office update/repair that left the interop type library unregistered.
- **E2. Bitness mismatch.** A 32-bit/64-bit mismatch between the Studio/Robot process and the installed Office. Produces the same class of COM startup cast/registration failure as E1.
- **E3. Word busy or blocked.** `0x8001010A` (`RPC_E_SERVERCALL_RETRYLATER`, "The application is busy"), `0x80010001` (`RPC_E_CALL_REJECTED`), or `0x80010100` (`RPC_E_SYS_CALL_FAILED`). An orphaned/hung `WINWORD.EXE` from a prior run holds the COM server, or Word is blocked on a modal dialog (Protected View / Mark-of-the-Web "file from the internet", activation, recover/repair prompt). Often intermittent.
- **E4. Word process crash mid-operation (COM error is a downstream symptom).** `WINWORD.EXE` faults and closes *during* an operation. The activity's async-completion path then runs `QueryInterface` against the COM server / apartment that the dying process already tore down, and surfaces `0x8001010E` (`RPC_E_WRONG_THREAD`, "interface marshalled for a different thread") and/or an `InvalidCastException` on the Word `_Document` interface. **The HRESULT is the aftermath, not the originating fault — diagnose the crash, not the marshalling error.** Triggers: a host Office instability (any of E1–E3), or an operation that pushes Word past a resource/render limit on this install. One known Add-Picture-specific trigger is **inserting a very large but otherwise valid image at full resolution** — `Add Picture` exposes no resize property, so a multi-megapixel image is handed to Word un-downscaled. *(The large-image trigger is a suspected/contributing pattern observed in the field, not a documented defect — confirm it with the faulting module per Investigation.)*

## Investigation

1. **Decode the HRESULT and locate the faulting frame** from the job error and stack.
2. **Decision tree** (stop at the first match):
   - Cast to the Word **`_Application`** interface failing in `EnsureWordApplication` / `WordApplicationScopeRuntime` during **startup**, with `0x8002801D` or `0x80040154` → **E1** (or **E2** if Studio/Robot and Office bitness differ — check both before concluding).
   - "Application is busy" / call-rejected / retry-later (`0x8001010A`, `0x80010001`, `0x80010100`) → **E3**. Check the robot host for an orphaned `WINWORD.EXE`, and for a modal/Protected-View state (especially if inputs came from `Downloads` / the internet — see Mark-of-the-Web).
   - Cast to the Word **`_Document`** interface with **`0x8001010E` (`RPC_E_WRONG_THREAD`)** on an async-completion frame (`WordInteropActivity.EndExecute`), **and/or the user reports that Word faulted and closed** → **E4**. The marshalling error is downstream of a process crash.
3. **For E4 — recover the crash forensics (decisive).** Pull the Windows **Application event log** record for the `WINWORD.EXE` crash — Event ID **1000** (`Application Error`), **1001** (Windows Error Reporting / APPCRASH bucket), or a `.NET Runtime` record — and read the **faulting module name + version** and **exception code** (e.g. `0xc0000005` access violation). The faulting module discriminates the trigger: a graphics / GDI+ / image-codec module points at an image-insert/render crash; an Office install / interop / loader module points at E1–E3; an RTF-import / document-conversion module points at a document-state interaction. If no crash record exists because the host's WER `ReportArchive` is saturated (e.g. another process is in a crash loop), restore WER retention or attach **ProcDump** to `WINWORD.EXE` (`procdump -e -ma WINWORD.EXE`) before reproducing. *(ProcDump and the WER archive are standard Microsoft/Sysinternals host tooling, not UiPath-documented steps.)*
4. **Capture the host Office state** for E1–E4: Office edition/channel and **bitness** (`File > Account > About Word`) versus the Studio/Robot process bitness; whether multiple Office installs coexist; and any orphaned `WINWORD.EXE` (Task Manager / `Get-Process WINWORD`).
5. **Confirm the workflow is not the cause.** If the activity is correctly scoped and its inputs are valid, and the same workflow succeeds in Studio on the developer's machine, the fault is environmental/host — do not edit the XAML.

## Resolution

Apply the fix for the identified sub-cause. The workflow itself usually needs no change.

- **E1 — type library / class not registered:** run an **online repair** of Microsoft Office on the robot host (`Settings > Apps > Microsoft Office > Modify > Online Repair`) to re-register the Office/Word COM type libraries. No workflow change required.
- **E2 — bitness mismatch:** reinstall Office at the same architecture as the Studio/Robot process (both 32-bit or both 64-bit).
- **E3 — busy / blocked:** kill any orphaned `WINWORD.EXE` (Task Manager / `Stop-Process -Name WINWORD -Force`) so the scope opens a clean instance, and ensure no `Try/Catch` swallows the scope's `Dispose`; dismiss/avoid modal and Protected-View states — if inputs are downloaded files, **unblock** them (`Right-click > Properties > Unblock` or `Unblock-File`) to clear the Mark-of-the-Web banner.
- **E4 — Word process crash:** this is a crash, not a marshalling bug.
  1. Apply the E1–E3 host remediation (repair Office, match bitness, clear orphaned `WINWORD.EXE`) — a destabilized Office install is the most common crash cause.
  2. If a specific operation reproducibly crashes Word with **valid** inputs, reduce what you hand Word. For `Add Picture` crashing on a large image, **pre-resize the image to a sane size before inserting it** (the activity has no resize property), use a smaller image, or insert via **`Paste Chart/Picture Into Document`** (clipboard) instead of the file-path insert.
  3. Capture the faulting module (Investigation step 3) to confirm the trigger before committing to a fix.
- **Fallback (any cause) — avoid Office Interop entirely:** migrate to the file-based `Word Document` activities (Studio panel under **System > File > Word Document**), which manipulate the `.docx` through the document object model without launching Word.

**Prevention.** Treat a Word COM HRESULT (`0x8002801D` / `0x80040154` / `0x8001010A` / `0x8001010E`) — or a job that succeeds in Studio but faults only on a robot host — as an **environment problem on the host**, not a workflow defect. Investigate Office repair, bitness, orphaned processes, and (for crashes) the faulting module; do not edit the XAML.

If a COM failure persists after all environmental causes are ruled out, capture a `Verbose` robot log plus a Process Monitor trace and/or a **ProcDump** crash dump of `WINWORD.EXE` during the failure (and the offending input file, e.g. the image), and open a UiPath support case.
