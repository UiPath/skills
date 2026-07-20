# Final Resolution

---

**Root Cause:** The `Add Picture` (`WordAddImage`) activity in `Main.xaml` is configured to insert relative to a **named bookmark** (`InsertRelativeTo="Bookmark"`, `BookmarkName="LogoAnchor"`), but the Word document opened at runtime (`C:\Robot\Templates\offer-letter.docx`) does **not contain** a bookmark named `LogoAnchor`. The bookmark existed in the design-time template, but the runtime document instance for this batch was generated without it. When `Add Picture` tries to resolve its insertion location against the missing bookmark, it faults with `UiPath.Word.BusinessException: The bookmark 'LogoAnchor' was not found in the document.`

**What went wrong:** Job `cc335555-9999-aaaa-bbbb-ccccddddeeee` (`WordTemplateFill`, folder `Shared`) ran for ~2s and faulted at the `Add Picture` activity with:
`UiPath.Word.BusinessException: The bookmark 'LogoAnchor' was not found in the document.`
The document opened successfully (log: "document opened"), then the fault occurred while `Add Picture` resolved its insertion point relative to bookmark `LogoAnchor` — the decisive smoking gun.

**Why:** With `InsertRelativeTo="Bookmark"`, `Add Picture` requires a bookmark with the configured `BookmarkName` to exist in the **opened document instance** — not merely in the design-time template. The process works on documents that carry the bookmark and fails on this batch's documents, which were produced without it. The image input itself is fine: `ImagePath` is a valid absolute path (`C:\Robot\Assets\signature.png`); the failure is purely the insertion target.

---

**Evidence:**

### Orchestrator (Root cause propagation)
- Failing job: `WordTemplateFill` (key `cc335555-...`) — Faulted at `2026-05-23T14:20:04.318Z`, ~2s after start.
- Folder: `Shared` (key `f0033344-2222-3333-4444-555566667777`, Id `6033001`).
- Host: `MOCK-HOST`, runtime `Unattended`. Robot user `UIPATH\AUTOMATION1`.
- `JobError`: `Type=BusinessException`, `ActivityName=WordAddImage_1`, `ActivityDisplayName="Add Picture"`, `WorkflowFilePath=Main.xaml`.
- Error (verbatim): `UiPath.Word.BusinessException: The bookmark 'LogoAnchor' was not found in the document.`
- Stack frame: `UiPath.Word.Activities.WordAddImage.ResolveInsertLocation(Document doc)` — confirms the failure is inside `Add Picture` while resolving the insertion location, before any image is written.

### Runtime logs (decisive)
- Trace: "Use Word File: offer-letter.docx — document opened." — the scope opened the document successfully.
- Trace: "Add Picture — resolving insertion point relative to bookmark 'LogoAnchor'." — the activity reached the bookmark-resolution step.
- Error: the `BusinessException` for the missing bookmark fired immediately after — the bookmark `LogoAnchor` is absent from this document instance.

### Workflow source (decisive)
- `Main.xaml`: `<uiword:WordAddImage DisplayName="Add Picture" ImagePath="C:\Robot\Assets\signature.png" InsertRelativeTo="Bookmark" BookmarkName="LogoAnchor" .../>` — the activity is set to anchor on bookmark `LogoAnchor`.
- `Add Picture` is correctly nested inside `Use Word File` (`Path="C:\Robot\Templates\offer-letter.docx"`); the scope opened the document before the fault.
- `ImagePath` is a valid absolute path string ending in `.png` — not an `Image` object, and the file/path is not implicated by the error.

### Cross-check — what this is NOT
- Not a missing-scope error (C1): `Add Picture` IS correctly nested inside `Use Word File`; the document opened successfully (log: "document opened").
- Not a COM/interop error (C2): no HRESULT (`0x8002801D` / `0x8001010A`) anywhere; the fault is a `UiPath.Word.BusinessException` explicitly about a missing bookmark.
- Not an invalid/unusable image input (C4): `ImagePath` is a valid absolute path (`C:\Robot\Assets\signature.png`), not an `Image` object or a stringified type name; the error never mentions the image file.

---

**Recommended Fix (Resolution):**

### Primary fix — make the insertion target exist (or remove the dependency)
Pick one:
1. **Add the bookmark to the document.** Ensure the document-generation step that produces this batch's `offer-letter.docx` inserts a bookmark named `LogoAnchor` at the intended location, so `Add Picture` can resolve it at runtime.
2. **Point `BookmarkName` at a bookmark that actually exists** in the runtime document instance, if the intended anchor lives under a different name.
3. **Drop the anchor dependency.** If the logo only needs to land at the top or bottom of the document, change `WordAddImage_1` to `InsertRelativeTo="Document"` with `Position="Start"` or `Position="End"`. This removes the bookmark requirement entirely.

### Confirm the runtime document is the intended one
Verify that the document opened by `Use Word File` (`C:\Robot\Templates\offer-letter.docx`) is the instance that is supposed to carry the bookmark. The bookmark existing in the design-time template does not guarantee it survives into every generated document instance.

### Prevention
- Treat `InsertRelativeTo="Bookmark"` as a contract: the configured `BookmarkName` must be guaranteed present in **every** document the process opens, not just the design-time template.
- When a generation step produces the document, assert the required bookmarks exist before `Add Picture` runs, or fall back to `InsertRelativeTo="Document"` placement.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The signature image file is missing or invalid on the robot host | Medium | Inconclusive | No | The error is a `BusinessException` about a missing bookmark, not a `FileNotFoundException`; `ImagePath` is a valid absolute `.png` path — disproves an image-file problem | Re-scoped to H2 |
| H2 | `Add Picture` is set `InsertRelativeTo=Bookmark` with `BookmarkName=LogoAnchor`, but the opened document instance lacks that bookmark (present in template, absent in this batch's document) | High | Confirmed | **Yes** | Source: `InsertRelativeTo="Bookmark"` `BookmarkName="LogoAnchor"`; runtime trace resolves insertion relative to `LogoAnchor`, then `BusinessException: The bookmark 'LogoAnchor' was not found in the document` | Add the bookmark to the document, fix `BookmarkName` to an existing one, or switch to `InsertRelativeTo="Document"` with `Position=Start`/`End` |
