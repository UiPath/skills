# Final Resolution

---

**Root Cause:** The `Add Picture` (`WordAddImage`) activity in `Main.xaml` is fed an **in-memory image object** instead of a file path. Its `ImagePath` ("Picture to insert") property is bound to `[screenshotImage.ToString()]`, where `screenshotImage` is a `UiPath.Core.Image` variable produced by the upstream `Take Screenshot` activity. `Add Picture` expects a **file path string**, and `UiPath.Core.Image.ToString()` returns the type name `"UiPath.Core.Image"` — not a path. The runtime therefore tries to open a file literally named `UiPath.Core.Image`, resolves it against the Robot's per-package working directory, and faults with `FileNotFoundException`.

**What went wrong:** Job `dd444444-9999-aaaa-bbbb-ccccddddeeee` (`WordReportImage`, folder `Shared`) ran for ~2s and faulted at the `Add Picture` activity with:
`System.IO.FileNotFoundException: Could not find file 'C:\Users\automation1\AppData\Local\UiPath\Packages\WordReportImage\1.0.0\UiPath.Core.Image'.`
The filename segment of that path is the literal string `UiPath.Core.Image` — the decisive smoking gun. No file by that name exists, because it is the default `ToString()` of the image object, not a real path.

**Why:** `Add Picture` does not accept a raw `UiPath.Core.Image`. The image must first be persisted to disk (e.g. with `Save Image`) and the resulting **path string** passed to `Picture to insert`. Binding the image variable (or its `.ToString()`) directly produces a non-path string, and the activity then looks for a file by that string, resolved against the current working directory.

---

**Evidence:**

### Orchestrator (Root cause propagation)
- Failing job: `WordReportImage` (key `dd444444-...`) — Faulted at `2026-05-22T09:15:04.302Z`, ~2s after start.
- Folder: `Shared` (key `f0044444-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime `Unattended`. Robot user `UIPATH\AUTOMATION1`.
- `JobError`: `Type=FileNotFoundException`, `ActivityName=WordAddImage_1`, `ActivityDisplayName="Add Picture"`, `WorkflowFilePath=Main.xaml`.
- Error (verbatim): `System.IO.FileNotFoundException: Could not find file 'C:\Users\automation1\AppData\Local\UiPath\Packages\WordReportImage\1.0.0\UiPath.Core.Image'.`
- Stack frame: `UiPath.Word.Activities.WordAddImage.AddImageFromPath(String imagePath)` — confirms the failure is inside `Add Picture` while opening the image path.

### Resolved path (decisive)
- Filename segment: `UiPath.Core.Image` — this is the literal type name returned by `UiPath.Core.Image.ToString()`, not a real file name. A real image path would end in `.png`/`.jpg`/etc.
- Prefix: `C:\Users\automation1\AppData\Local\UiPath\Packages\WordReportImage\1.0.0\` — the Robot's per-package CWD; the non-path string had no drive/root, so it was resolved against the CWD.

### Workflow source (decisive)
- `Main.xaml`: `<uiword:WordAddImage DisplayName="Add Picture" ImagePath="[screenshotImage.ToString()]" .../>` — `ImagePath` is bound to the `.ToString()` of an image variable.
- `screenshotImage` is declared `Variable x:TypeArguments="ui:Image"` (a `UiPath.Core.Image`) and assigned by `<ui:TakeScreenshot ... Image="[screenshotImage]" />` immediately above. The image is never saved to disk; no `Save Image` activity exists in the workflow.

### Cross-check — what this is NOT
- Not a missing-scope error (C1): `Add Picture` IS correctly nested inside `Use Word File`; the document opened successfully (log: "document opened").
- Not a COM/interop error (C2): no HRESULT (`0x8002801D` / `0x8001010A`) anywhere; the fault is a plain `FileNotFoundException`.
- Not an insertion-target error (C3): `InsertRelativeTo="Document"` with `Position="End"` — no text/bookmark anchor is involved.
- Not a genuinely-missing image file: the "file" name is the type name `UiPath.Core.Image`, which proves an object was stringified, not a real path that happened to be absent.

---

**Recommended Fix (Resolution):**

### Primary fix — save the image, pass the path
In `Main.xaml`, persist the screenshot to disk and pass the **path string** to `Add Picture`:
1. Add a `Save Image` activity after `Take Screenshot`, saving `screenshotImage` to a known file, e.g. `C:\Robot\Reports\chart.png`.
2. Change `WordAddImage_1`'s `ImagePath` from `[screenshotImage.ToString()]` to that absolute path string, e.g. `"C:\Robot\Reports\chart.png"` (or a variable holding it).

`Add Picture` does not accept a `UiPath.Core.Image` object — it reads an image file from a path. `Save Image` → path string is the supported pattern.

### Use an absolute path
Use a fully-qualified absolute path (or one built with `Path.Combine` against a known root) for the saved image, so it resolves identically under the Robot account rather than against the per-package CWD.

### Prevention
- Workflow review should reject any `Picture to insert` (`ImagePath`) value that is an `Image`-typed variable or its `.ToString()`. The property is always a path string.
- Treat a resolved path whose filename is a .NET type name (`UiPath.Core.Image`, `System.Drawing.Bitmap`, etc.) as a tell-tale of an object stringified where a path was expected.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The chart image file is simply missing on the robot host | Medium | Inconclusive | No | The "file" name is the literal `UiPath.Core.Image` type name, not a real image path — disproves a plain missing-file | Re-scoped to H2 |
| H2 | `Add Picture` ImagePath is bound to an in-memory `UiPath.Core.Image` (via `.ToString()`) instead of a saved file path; runtime stringifies the object to `"UiPath.Core.Image"` and can't open it | High | Confirmed | **Yes** | Source: `ImagePath="[screenshotImage.ToString()]"`, `screenshotImage` is a `ui:Image` from `Take Screenshot`; resolved path filename = `UiPath.Core.Image` | Save the image to disk with `Save Image`, pass the absolute path string to `Picture to insert` |
