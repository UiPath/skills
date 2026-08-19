# Final Resolution

---

**Root Cause:** The `Add Picture` (`WordAddImage`) activity in `Main.xaml` is placed **outside** the `Use Word File` scope. It sits as a **sibling** of `UseWordFile` in the outer `Main Sequence`, *after* the scope's closing tag — not inside `UseWordFile.Body`. `Add Picture` requires an open Word document context, which only exists while execution is inside a `Use Word File` (or `Word Application Scope`) body. By the time the sibling `Add Picture` runs, the scope has already exited and the document context is closed, so the activity faults with `InvalidOperationException`.

**What went wrong:** Job `aa111111-9999-aaaa-bbbb-ccccddddeeee` (`WordLogoStamp`, folder `Shared`) ran for ~1s and faulted at the `Add Picture` activity with:
`System.InvalidOperationException: The 'Add Picture' activity must be used inside a 'Use Word File' or 'Word Application Scope' activity. No Word document is open in the current scope.`
The document opened successfully inside the scope (log: "document opened"), the scope then exited (log: "scope exited; document context closed"), and only afterward did `Add Picture` run — with no open document — and throw.

**Why:** `Add Picture` operates on the document opened by its enclosing `Use Word File` / `Word Application Scope`. It resolves that document context from the activity tree at runtime. When the activity is not a descendant of a scope body, there is no document to resolve, so `ResolveDocumentContext()` throws `InvalidOperationException`. The activity must be **nested inside** the scope's `Body`, not be a peer of the scope.

---

**Evidence:**

### Orchestrator (Root cause propagation)
- Failing job: `WordLogoStamp` (key `aa111111-...`) — Faulted at `2026-05-19T07:30:03.061Z`, ~1s after start.
- Folder: `Shared` (key `f0011144-2222-3333-4444-555566667777`, Id `6011001`).
- Host: `MOCK-HOST`, runtime `Unattended`. Robot user `UIPATH\AUTOMATION1`.
- `JobError`: `Type=InvalidOperationException`, `ActivityName=WordAddImage_1`, `ActivityDisplayName="Add Picture"`, `WorkflowFilePath=Main.xaml`.
- Error (verbatim): `System.InvalidOperationException: The 'Add Picture' activity must be used inside a 'Use Word File' or 'Word Application Scope' activity. No Word document is open in the current scope.`
- Stack frame: `UiPath.Word.Activities.WordAddImage.ResolveDocumentContext()` then `.Execute(NativeActivityContext context)` — confirms the failure is `Add Picture` failing to resolve an open document context.

### Execution timeline (decisive)
- Logs show the document opened *inside* the scope (`Use Word File: monthly-report.docx — document opened`), then the scope exited and closed the document context (`scope exited; document context closed`), and only then did `Add Picture` error. The fault happens *after* the scope has closed — proving `Add Picture` ran outside it.

### Workflow source (decisive)
- `Main.xaml`: `<uiword:WordAddImage DisplayName="Add Picture" ImagePath="C:\Robot\Reports\logo.png" .../>` is a direct child of the outer `<Sequence DisplayName="Main Sequence">`, positioned **after** the closing `</uiword:UseWordFile>` tag.
- The `UseWordFile.Body` contains only a `LogMessage` ("Report document opened — ready to stamp logo.") — the `Add Picture` is **not** among the scope body's children.
- So `WordAddImage_1` is a **sibling** of `UseWordFile_1`, not nested in it. There is no open document at the point it executes.

### Cross-check — what this is NOT
- Not an image-variable / invalid-input error (C4): the `ImagePath` is a plain, valid file-path string (`C:\Robot\Reports\logo.png`), not an in-memory `UiPath.Core.Image` or its `.ToString()`; the error is not `FileNotFoundException` and the resolved path is not a stringified type name.
- Not a COM/interop error (C2): no HRESULT (`0x8002801D` / `0x8001010A`) anywhere; the fault is a managed `InvalidOperationException` about scope, not a COM failure.
- Not an insertion-target / bookmark error (C3): `InsertRelativeTo="Document"` with `Position="End"` — no text/bookmark anchor is referenced, and the error names the missing scope, not a missing anchor.
- Not a missing or corrupt document file: the document **opened successfully** inside the scope (log confirms), and the error is explicitly about no open document *in the current scope*, not about the file being absent or unreadable.

---

**Recommended Fix (Resolution):**

### Primary fix — move Add Picture inside the Use Word File scope
In `Main.xaml`, relocate the `Add Picture` activity so it is a child of the `Use Word File` scope's `Body`, not a sibling that runs after the scope:
1. Cut `WordAddImage_1` (`Add Picture`) from the outer `Main Sequence`.
2. Paste it inside the `UseWordFile.Body` sequence (e.g. after the "Report document opened" log), so it executes while the document is open.
3. Re-validate the workflow.

`Add Picture` resolves the open document from its enclosing `Use Word File` / `Word Application Scope`. It must be a descendant of that scope's body — being a peer of the scope leaves it with no document context.

### Re-validate
After moving the activity, re-validate the project (e.g. `uip rpa validate` / Studio validation) and re-run the job to confirm the `Add Picture` now runs against the open document and no longer faults.

### Prevention
- Any Word content activity (`Add Picture`, `Replace Text`, `Set Bookmark Content`, etc.) must live **inside** a `Use Word File` / `Word Application Scope` body. Treat an `InvalidOperationException` naming a required scope as a placement (nesting) bug, not a data/file bug.
- Workflow review should reject Word content activities that are siblings of — rather than descendants of — their scope.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Word document file is missing/corrupt or the `logo.png` image is missing | Medium | Disproven | No | Logs confirm the document opened successfully inside the scope; the error is `InvalidOperationException` about no open scope, not `FileNotFoundException` | Re-scoped to H2 |
| H2 | `Add Picture` is placed OUTSIDE the `Use Word File` scope (sibling in the outer Main Sequence, not nested in `UseWordFile.Body`), so it runs with no open document context and faults | High | Confirmed | **Yes** | Source: `WordAddImage_1` is a child of `Main Sequence`, after the closing `</uiword:UseWordFile>`; scope body holds only a `LogMessage`. Logs show the scope closed before `Add Picture` ran | Move `Add Picture` inside the `Use Word File` scope body, then re-validate |
