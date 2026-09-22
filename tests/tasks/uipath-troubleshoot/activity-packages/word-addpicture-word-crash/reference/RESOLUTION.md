# Final Resolution

---

**Root Cause:** **Microsoft Word (`WINWORD.EXE`) crashed on the robot host while the image was being inserted** — an environmental fault, NOT a workflow defect. `Main.xaml` is correct: `Add Picture` (`WordAddImage`) is properly nested inside the `Use Word File` (`UseWordFile`) scope, `ImagePath` is a valid absolute path string (`C:\Robot\Assets\candidate-photo.jpg`), and `InsertRelativeTo="Document"` / `Position="End"`. The document opened successfully and `Add Picture` was reached; then the Word COM server process exited unexpectedly mid-insert. Because the out-of-process COM server died, its marshalled `Word._Document` proxy was torn down, and the activity's async-completion path (`WordInteropActivity.EndExecute`) ran `QueryInterface` against the now-dead apartment — surfacing `System.InvalidCastException ... (Exception from HRESULT: 0x8001010E (RPC_E_WRONG_THREAD))`. **The `RPC_E_WRONG_THREAD` cast is the downstream symptom; the originating fault is the Word process crash.**

**What went wrong:** Job `cc333333-3333-bbbb-cccc-ddddeeeeffff` (`ResumePhotoStamp`, folder `Shared`) ran for ~6s and faulted at the `Add Picture` activity. The logs show the document opened successfully, `Add Picture` began inserting `C:\Robot\Assets\candidate-photo.jpg`, then `Word Application host process (WINWORD.EXE, PID 7864) exited unexpectedly while 'Add Picture' was inserting the image`, immediately followed by:
`System.InvalidCastException: Unable to cast COM object of type 'System.__ComObject' to interface type 'Microsoft.Office.Interop.Word._Document'. ... The application called an interface that was marshalled for a different thread. (Exception from HRESULT: 0x8001010E (RPC_E_WRONG_THREAD))`, thrown from `UiPath.Word.Activities.WordInteropActivity.EndExecute` on the `AsyncCodeActivity` completion path.

**Why:** `0x8001010E` = `RPC_E_WRONG_THREAD` = "The application called an interface that was marshalled for a different thread." It does not mean the workflow used threads — it means the COM proxy the completion path tried to use is no longer valid on its apartment, which is exactly what happens when `WINWORD.EXE` crashes mid-call and the proxy/apartment it created is torn down. The fault is environmental on the host (a destabilized Office install, an orphaned/wedged prior `WINWORD.EXE`, a bitness mismatch, or an operation that pushes Word past a resource/render limit). For `Add Picture` specifically, a known crash trigger is inserting a **very large but otherwise valid image** at full resolution — the activity exposes no resize property, so a multi-megapixel image is handed to Word un-downscaled. The XAML runs fine on the developer's machine; only the robot host crashes — a strong tell of an environmental difference, not a source bug.

---

**Evidence:**

### Orchestrator (Root cause propagation)
- Failing job: `ResumePhotoStamp` (key `cc333333-...`) — Faulted at `2026-05-22T09:14:08.742Z`, ~6s after start.
- Folder: `Shared` (key `f0022244-2222-3333-4444-555566667777`, Id `6022001`).
- Host: `MOCK-HOST`, runtime `Unattended`. Robot user `UIPATH\AUTOMATION1`.
- `JobError`: `Type=InvalidCastException`, `ActivityName=WordAddImage_1`, `ActivityDisplayName="Add Picture"`, `WorkflowFilePath=Main.xaml`.
- Error (verbatim): `System.InvalidCastException: Unable to cast COM object of type 'System.__ComObject' to interface type 'Microsoft.Office.Interop.Word._Document'. ... The application called an interface that was marshalled for a different thread. (Exception from HRESULT: 0x8001010E (RPC_E_WRONG_THREAD)).`
- Stack frames: `at UiPath.Word.Activities.WordInteropActivity.EndExecute(...)` → `at System.Activities.AsyncCodeActivity.CompleteAsyncCodeActivityData.CompleteAsyncCodeActivityWorkItem.Execute(...)` — confirms the failure is on the async-completion path, after the operation was dispatched.

### Logs (decisive — Word crashed mid-insert)
- `Use Word File: resume-draft.docx — launching Word via Office Interop ... Document opened successfully.` — the document path is valid; open succeeded.
- `Add Picture: inserting image 'C:\Robot\Assets\candidate-photo.jpg' relative to Document (Position=End).` — the activity was reached and the image path is valid.
- **`Word Application host process (WINWORD.EXE, PID 7864) exited unexpectedly while 'Add Picture' was inserting the image. The Word COM server is no longer available.`** — the originating fault: the Word process crashed.
- The `InvalidCastException` / `0x8001010E` then follows — the downstream symptom of the dead COM server.

### HRESULT decode
- `0x8001010E` = `RPC_E_WRONG_THREAD` = "interface marshalled for a different thread." On the async-completion frame after the host process died, the `Word._Document` proxy is no longer valid on its apartment, so the cast fails. This is a consequence of the crash, not a threading bug in the workflow.

### Workflow source (proves the XAML is correct — nothing to fix)
- `Main.xaml`: `<uiword:WordAddImage DisplayName="Add Picture" ImagePath="C:\Robot\Assets\candidate-photo.jpg" InsertRelativeTo="Document" Position="End" .../>` nested inside `<uiword:UseWordFile ... Path="C:\Robot\Resumes\resume-draft.docx">.Body`.
- `Add Picture` is correctly scoped, `ImagePath` is a valid absolute path string, and `InsertRelativeTo="Document"` needs no bookmark. There is no source defect to repair.

### Cross-check — what this is NOT
- **Not a missing-scope error:** `Add Picture` IS correctly nested inside `Use Word File` `.Body`.
- **Not an insertion-target / bookmark error:** `InsertRelativeTo="Document"` with `Position="End"` — no anchor involved.
- **Not an image-variable / bad-path error:** `ImagePath` is a literal absolute path string ending in `.jpg`, and the document opened and the activity was reached — the image path resolved.
- **Not a type-library-not-registered startup failure:** the fault is `0x8001010E` on the `EndExecute` completion path *after* the document opened — not `0x8002801D` during `EnsureWordApplication` startup.
- **Not a source-code bug at all:** the workflow is structurally correct and runs on the developer's machine; the Word process crashed on the robot host.

---

**Recommended Fix (Resolution):**

### Primary — treat it as a Word process crash (environmental), not a workflow edit
1. Confirm the crash and its trigger: on the robot host (`MOCK-HOST`), read the **Windows Application event log** `WINWORD.EXE` crash record (Event ID 1000 `Application Error`, 1001 Windows Error Reporting, or a `.NET Runtime` record) for the **faulting module** and exception code. The faulting module discriminates the trigger (a graphics/GDI+/image-codec module ⇒ image-insert/render crash; an Office install/interop module ⇒ a destabilized install). If no crash record exists because the host's Windows Error Reporting archive is saturated, restore WER retention or attach **ProcDump** to `WINWORD.EXE` (`procdump -e -ma WINWORD.EXE`) before reproducing.
2. Stabilize Office on the host: run an **online repair** of Microsoft Office (`Settings > Apps > Microsoft Office > Modify > Online Repair`); confirm Studio/Robot and Office share the **same bitness** (`File > Account > About Word`); and kill any orphaned `WINWORD.EXE` before re-running. No workflow change is required.

### If Word reproducibly crashes on this image — reduce what Word is asked to render
- `Add Picture` (`WordAddImage`) has **no resize property**, so a very large image is inserted at full resolution and can crash Word. **Pre-resize the image to a sane size before inserting it** (add a resize step / use a downscaled copy), use a smaller image, or insert via **`Paste Chart/Picture Into Document`** (clipboard) instead of the file-path insert.

### Fallback — avoid Office Interop
- If Office cannot be made reliable on the host, migrate to the file-based `Word Document` activities (System > File > Word Document), which manipulate the `.docx` without launching Word.

### Prevention
- Treat a `RPC_E_WRONG_THREAD` (`0x8001010E`) / `InvalidCastException` on a Word activity's async-completion path — especially alongside Word closing unexpectedly — as a **Word process crash on the host**, and diagnose the crash (faulting module, Office repair, bitness, orphaned process, oversized inputs). Do not edit the XAML.
- A job that runs fine in Studio on the developer's machine but faults only on a specific robot host is a strong tell of an environmental difference, not a source bug.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The workflow/source is defective (bad scope, bad ImagePath, missing bookmark, image-variable) | Medium | Disproven | No | `Main.xaml` correct: `Add Picture` nested in `Use Word File`, valid absolute `ImagePath`, `InsertRelativeTo=Document`; document opened and the activity was reached; runs fine on the developer's machine | Re-scoped to H2 |
| H2 | Word (`WINWORD.EXE`) crashed mid-insert on the host; the `RPC_E_WRONG_THREAD` (`0x8001010E`) cast on the `EndExecute` async-completion path is the downstream symptom of the torn-down COM proxy | High | Confirmed | **Yes** | Log: `WINWORD.EXE ... exited unexpectedly while 'Add Picture' was inserting the image`, immediately followed by the `InvalidCastException` / `0x8001010E` from `WordInteropActivity.EndExecute` | Diagnose the crash: capture the WINWORD faulting module; repair Office; match bitness; clear orphaned `WINWORD.EXE`; for a large image, pre-resize / smaller image / Paste Chart/Picture Into Document; or migrate to file-based `Word Document` activities |
