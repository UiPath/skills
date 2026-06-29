---
confidence: medium
---

# Word Application Scope — Save Document as PDF COM Wrong-Thread (0x8001010E RPC_E_WRONG_THREAD)

## Context

What this looks like:
- `Save Document as PDF` (`WordExportToPdf`) — or another activity inside the surrounding `Word Application Scope` / `Use Word File` — faults casting the document COM object.
- Error message contains:
  - `Unable to cast COM object of type 'System.__ComObject' to interface type 'Microsoft.Office.Interop.Word._Document'.`
  - `... the QueryInterface call on the COM component for the interface with IID '{0002096B-0000-0000-C000-000000000046}' failed ...`
  - `The application called an interface that was marshalled for a different thread. (0x8001010E (RPC_E_WRONG_THREAD)).`
- IID `{0002096B-0000-0000-C000-000000000046}` = `Microsoft.Office.Interop.Word._Document`.
- The workflow is often structurally correct — the export is the sole/last child of the scope that opened the document, with no `Parallel`/`Pick`/`Invoke`/coded thread between scope-open and export.

What can cause it (more than one may apply):
- **Scope attached to an externally-owned Word instance** — Word (`WINWORD.EXE`) was already open when the scope ran. `Word Application Scope` exposes no new-instance / isolated-instance / attach control (unlike `Excel Process Scope`), so it reuses the running Word. That instance's `_Document` lives on the external process's STA apartment; the robot worker thread's cross-apartment `QueryInterface` fails.
- **The attached Word closed mid-run** — the externally-owned Word window closed (manually, by a user, by another process, or by an embedded OLE host) after the scope bound the document but before the export. The close tore down / re-marshalled the apartment owning the `_Document`, leaving the activity's proxy bound to a stale/replaced apartment. `RPC_E_WRONG_THREAD` (not `0x80010108 RPC_E_DISCONNECTED`) is the signature of a *replaced* apartment, not a clean server death.
- **Off-STA / non-interactive runtime** — the export ran where the worker thread is not the STA that owns the document: an unattended robot in Session 0, a background process, or a thread other than the scope creator (`Parallel`/`Pick`/async/`Invoke Code`/coded `.cs`). Word interop requires an interactive STA session.
- **Package version skew** — a pre-release / alpha `UiPath.Word.Activities` build on a runtime it was not paired with. Alpha-build behavior is undefined; rule it out by testing the stable LTS-bundled version.

What to look for:
- Whether `WINWORD.EXE` was already running when the job started, and whether it stayed open through the export.
- Run surface: Studio Run/Debug foreground vs attended vs unattended/Session 0 vs background.
- Scope structure: is the export the child of the scope that opened the document; any `Parallel`/`Pick`/`Invoke`/coded thread between scope-open and export.
- `UiPath.Word.Activities` version (stable vs alpha/pre-release).

## Investigation

1. Read the error from job evidence. Confirm the HRESULT is `0x8001010E RPC_E_WRONG_THREAD` and the IID is `{0002096B-...}` (`_Document`). Distinguish from `0x80010108 RPC_E_DISCONNECTED` (server died) — different cause, different fix.
2. Read the faulted activity and its surrounding `Word Application Scope` / `Use Word File` from the `.xaml`. Confirm the export is correctly nested (sole/last child of the scope that opened the document) and capture the scope's `FilePath` / `CreateNewFile`.
3. Trace threading from source: grep the workflow(s) for `Parallel`, `ParallelForEach`, `Pick`, `PickBranch`, `InvokeWorkflowFile`, `InvokeCode`, and coded `.cs` workflows. If any sits between scope-open and export, the off-STA cause is in play.
4. Establish the runtime sequence (ask the user if not in logs): Was Word already open when the run started? Did that Word window close before the export ran? Was the run foreground Studio / attended, or unattended / Session 0 / background?
5. Grep the workflow for any activity that closes or kills Word or a host app (`Close Application`, `Close Window`, `Kill Process`, `Quit`, host `Dispose`). If none exist, a mid-run close was external/manual — out of the workflow graph.
6. Read `UiPath.Word.Activities` version from `project.json`. Note whether it is a pre-release / alpha build vs the stable version bundled with the runtime's LTS.

## Resolution

- **If Word was already open / attached externally (and/or closed mid-run):** ensure no user-opened `WINWORD.EXE` is running when the workflow executes, and do not open or close Word on the host during the run — let the scope own its own Word instance. Confirm with an A/B re-run: Trial A opens external Word, lets the scope attach, then closes that Word window before the export (expect the error); Trial B runs with no external Word open (expect success). Error only in A confirms the attachment / mid-run-close cause.
- **If the export must run while Word may be open, or unattended:** migrate the document-to-PDF path to the **System Word** activities (background, no Word UI, no shared interop instance), which remove the dependency on an interactive/external Word. Verify the System Word group covers the export before migrating; if it does not, keep `Word Application Scope` and apply the no-external-Word fix above.
- **If the run surface is unattended / Session 0 / background:** Word interop requires an interactive STA session. Run the automation attended in an interactive session, or switch to the System Word (background) activities. If a `Parallel`/`Pick`/`Invoke`/coded thread sits between scope-open and export, move the export onto the same thread/scope that opened the document.
- **If the package is a pre-release / alpha build:** pin `UiPath.Word.Activities` to the stable version bundled with the runtime's LTS and re-test to rule out a build regression.

If the failure persists after no external Word is present and the run is attended/STA, capture a `Verbose` robot log plus the full marshalling stack trace and open a UiPath support case — the residual cases are package or Office-version-specific bugs that need vendor diagnosis.
