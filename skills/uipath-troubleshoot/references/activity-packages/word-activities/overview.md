# Word Activities

Activities from the `UiPath.Word.Activities` package for automating Microsoft Word on Windows. Two execution surfaces coexist: the modern/interop `Word Application Scope` / `Use Word File` activities that drive a real `WINWORD.EXE` instance via `Microsoft.Office.Interop.Word` (COM), and the **System Word** activities that process documents in the background through the document library without opening Word. `Save Document as PDF` (`WordExportToPdf`) on the interop surface is COM-only — it requires Word and a live document handle.

## How Word COM Interop Executes

`Word Application Scope` opens (or attaches to) a `WINWORD.EXE` instance and exposes a `_Document` COM object bound to that instance's STA apartment. Child activities — `Save Document as PDF`, `Replace Text`, `Read Text`, etc. — call into that document object. Behaviour chain:

1. Resolve or launch a Word `Application` instance for the scope
2. Open the document at `FilePath` and bind its `_Document` COM object on the owning STA apartment
3. Run each child activity against that document handle
4. Save/close and release the document at end of scope

Two properties of this model drive most COM failures:

- **No isolated-instance control.** Unlike `Excel Process Scope`, `Word Application Scope` exposes no new-instance / attach-to-existing / isolated-instance setting. If a `WINWORD.EXE` is already running, the scope reuses it — the document's COM apartment is then owned by that external process, not the robot.
- **STA / thread affinity.** The `_Document` proxy is valid only on the apartment that created it and only while that apartment lives. Running a child activity on a different thread (Parallel/Pick/async/coded), or tearing down the owning Word instance mid-run, marshals the proxy across a foreign/replaced apartment and faults.

## Key Activities

- **Word Application Scope** / **Use Word File** — open a Word document and expose its handle to child activities via COM interop. Properties: `FilePath` (the document to open), `CreateNewFile` (create if missing), `Password`. Exposes no isolated-instance control.
- **Save Document as PDF** (`WordExportToPdf`) — export the open document to a PDF at `FilePath`. COM-only; runs against the `_Document` of the surrounding scope.
- **System Word activities** — background document processing that does not open the Word UI or share an interop instance. The migration target when interop/COM instability cannot be avoided (Word may be open, unattended runs, Session 0).

## Common Failure Patterns

- **COM wrong-thread cast (`0x8001010E RPC_E_WRONG_THREAD`)** — a child activity (commonly `Save Document as PDF`) faults casting `System.__ComObject` to `Microsoft.Office.Interop.Word._Document` (IID `{0002096B-...}`). The document proxy was created on one STA apartment and accessed from another. Causes: the scope attached to an already-open external Word; that external Word closed mid-run; an off-STA / non-interactive runtime (unattended/Session 0/background); or a thread other than the scope creator (Parallel/Pick/Invoke/coded). Distinct from `0x80010108 RPC_E_DISCONNECTED` (the Word server died outright).

## Package

NuGet: `UiPath.Word.Activities`

Version-specific bugs are documented in the relevant playbooks. Pre-release / alpha builds on a non-paired runtime are a known source of COM instability — test against the stable version bundled with the runtime's LTS before concluding a code defect.
