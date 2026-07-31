# Final Resolution

---

**Root Cause:** This is an **environmental fault on the robot host**, NOT a workflow defect. `Main.xaml` is correct — `Add Picture` (`WordAddImage`) is properly nested inside the `Use Word File` (`UseWordFile`) scope, `ImagePath` is a valid absolute path string (`C:\Robot\Assets\logo.png`), and `InsertRelativeTo="Document"` / `Position="End"`. The job faults before any document work because the **Word interop type library is not registered** on the host. When the Word activities drive Word via Office Interop, the COM cast `Microsoft.Office.Interop.Word.ApplicationClass` → `_Application` fails with `System.InvalidCastException ... (Exception from HRESULT: 0x8002801D (TYPE_E_LIBNOTREGISTERED))`. `0x8002801D` = `TYPE_E_LIBNOTREGISTERED` = "Library not registered" — the COM type library for Word interop is missing/unregistered, typically after a partial or failed Office update or repair.

**What went wrong:** Job `bb222222-9999-aaaa-bbbb-ccccddddeeee` (`WordContractStamp`, folder `Shared`) ran for ~3s and faulted at the `Add Picture` activity with:
`System.InvalidCastException: Unable to cast COM object of type 'Microsoft.Office.Interop.Word.ApplicationClass' to interface type 'Microsoft.Office.Interop.Word._Application'. ... (Exception from HRESULT: 0x8002801D (TYPE_E_LIBNOTREGISTERED)).`
The fault originates in `WordApplicationScopeRuntime.EnsureWordApplication()` — i.e. while bringing up the Word COM application, before the image is ever inserted. The document path `C:\Robot\Contracts\contract-draft.docx` is valid and the workflow runs fine on the developer's machine; only the robot host is affected.

**Why:** Office Interop requires the Word type library to be registered with COM on the host. After a partial/failed Office update or repair, the type library registration can be lost, so the `QueryInterface` for IID `{00020970-0000-0000-C000-000000000046}` (the Word `_Application` interface) returns `Library not registered`. The cast fails before any file is touched. A bitness mismatch (32-bit Studio/Robot vs 64-bit Office, or vice versa) or an orphaned `WINWORD.EXE` holding the COM server can produce the same class of COM-startup failure.

---

**Evidence:**

### Orchestrator (Root cause propagation)
- Failing job: `WordContractStamp` (key `bb222222-...`) — Faulted at `2026-05-21T11:05:05.118Z`, ~3s after start.
- Folder: `Shared` (key `f0022244-2222-3333-4444-555566667777`, Id `6022001`).
- Host: `MOCK-HOST`, runtime `Unattended`. Robot user `UIPATH\AUTOMATION1`.
- `JobError`: `Type=InvalidCastException`, `ActivityName=WordAddImage_1`, `ActivityDisplayName="Add Picture"`, `WorkflowFilePath=Main.xaml`.
- Error (verbatim): `System.InvalidCastException: Unable to cast COM object of type 'Microsoft.Office.Interop.Word.ApplicationClass' to interface type 'Microsoft.Office.Interop.Word._Application'. ... (Exception from HRESULT: 0x8002801D (TYPE_E_LIBNOTREGISTERED)).`
- Stack frames: `at System.RuntimeType.ForwardCallToInvokeMember(...)` → `at UiPath.Word.Activities.WordApplicationScopeRuntime.EnsureWordApplication()` → `at UiPath.Word.Activities.WordAddImage.Execute(NativeActivityContext context)` — confirms the failure is in Word COM startup, not in image insertion.

### HRESULT decode (decisive)
- `0x8002801D` = `TYPE_E_LIBNOTREGISTERED` = "Library not registered." The Word COM type library is not registered on the host.
- The cast target is the Word `_Application` interface (IID `{00020970-0000-0000-C000-000000000046}`). The QueryInterface fails because the interop type library is absent from the COM registry — an environment/registration problem, not data and not code.

### Logs (decisive timing)
- Trace immediately before the error: `Use Word File: contract-draft.docx — launching Word via Office Interop (Visible=False) for document 'C:\Robot\Contracts\contract-draft.docx'.` — the document path is valid; the failure is during COM startup, not file access.
- Error log: the `InvalidCastException` with `0x8002801D (TYPE_E_LIBNOTREGISTERED)`.

### Workflow source (proves the XAML is correct — nothing to fix)
- `Main.xaml`: `<uiword:WordAddImage DisplayName="Add Picture" ImagePath="C:\Robot\Assets\logo.png" InsertRelativeTo="Document" Position="End" .../>` — nested inside `<uiword:UseWordFile ... Path="C:\Robot\Contracts\contract-draft.docx">.Body`.
- `ImagePath` is a valid absolute path string (ends in `.png`), the activity is correctly scoped, and `InsertRelativeTo="Document"` needs no bookmark. There is no source defect to repair.

### Cross-check — what this is NOT
- **Not a missing-scope error (C1):** `Add Picture` IS correctly nested inside `Use Word File` `.Body`; the activity is in scope.
- **Not a COM/data confusion with a bad path:** the document path `C:\Robot\Contracts\contract-draft.docx` and image path `C:\Robot\Assets\logo.png` are valid; the fault is in COM startup before any file is opened.
- **Not an insertion-target / bookmark error (C3):** `InsertRelativeTo="Document"` with `Position="End"` — no text/bookmark anchor is involved.
- **Not an image-variable error (C4):** `ImagePath` is a literal absolute path string ending in `.png`, not an `Image`-typed variable or its `.ToString()`; the resolved value is a real path, not a stringified object.
- **Not a source-code bug at all:** the workflow runs fine on the developer's machine and is structurally correct. The fault is environmental — the Word interop type library is not registered on the robot host.

---

**Recommended Fix (Resolution):**

### Primary fix — re-register the Word COM type libraries (online repair of Office)
1. On the robot host (`MOCK-HOST`), run an **online repair** of Microsoft Office (Settings → Apps → Microsoft Office → Modify → Online Repair). This re-registers the Office/Word COM type libraries that `0x8002801D` reports as missing.
2. Re-run the `WordContractStamp` job. No workflow change is required — the XAML is correct.

### Verify bitness
- Confirm Studio/Robot and the installed Office are the **same bitness** (both 32-bit or both 64-bit). A 32/64-bit mismatch produces the same class of COM cast/startup failure. Reinstall the mismatched component if they differ.

### Clear orphaned Word processes
- Kill any orphaned `WINWORD.EXE` on the host (Task Manager / `taskkill /IM WINWORD.EXE /F`) before re-running, in case a stuck COM server is holding the interop registration in a bad state.

### Fallback — migrate to file-based Word Document activities
- If Office cannot be made reliable on the host, migrate the workflow to the **file-based `Word Document` activities** (System > File > Word Document), which manipulate the `.docx` directly and do not depend on a registered Office Interop type library.

### Prevention
- Treat HRESULT `0x8002801D` / `TYPE_E_LIBNOTREGISTERED` (and the sibling `0x80040154` / `REGDB_E_CLASSNOTREG`) on Word/Excel/Outlook activities as an **environment registration problem on the host**, not a workflow defect — investigate Office repair and bitness, not the XAML.
- A job that runs fine on the developer's machine but faults only on a specific robot host is a strong tell of an environmental/registration difference, not a source bug.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The workflow/source is defective (bad scope, bad ImagePath, missing bookmark, image-variable bound to ImagePath) | Medium | Disproven | No | `Main.xaml` is correct: `Add Picture` nested in `Use Word File`, `ImagePath="C:\Robot\Assets\logo.png"` (valid absolute path), `InsertRelativeTo=Document`; runs fine on the developer's machine | Re-scoped to H2 |
| H2 | Environmental: the Word interop type library is not registered on the robot host (HRESULT `0x8002801D` / `TYPE_E_LIBNOTREGISTERED`), so the COM cast to `_Application` fails during Word startup | High | Confirmed | **Yes** | `InvalidCastException ... 0x8002801D (TYPE_E_LIBNOTREGISTERED)` in `WordApplicationScopeRuntime.EnsureWordApplication()`; fault precedes any image insertion; document path is valid | Online repair of Office to re-register COM type libraries; verify Studio/Robot↔Office bitness; kill orphaned `WINWORD.EXE`; or migrate to file-based `Word Document` activities |
