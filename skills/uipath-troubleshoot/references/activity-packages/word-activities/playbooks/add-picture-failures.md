---
confidence: medium
---

# Add Picture (WordAddImage) Failures

## Context

`Add Picture` (`UiPath.Word.Activities.WordAddImage`) fails to insert an image into a Word document. The failure falls into one of four distinct categories, each with its own signature and fix. Identify the category first, then apply the matching resolution.

What this looks like:
- A design-time validation warning that the activity is invalid, or an immediate fault when the activity is reached
- A Word COM HRESULT — `Unable to cast COM object ... 0x8002801D` or `The application is busy ... 0x8001010A`
- A missing-reference error — the bookmark or text anchor where the image should go cannot be found
- A file-not-found or generic exception while reading the `Picture to insert` value

What can cause it — four distinct mechanisms:

- **C1. Activity outside a Word scope.** `Add Picture` is not nested inside a `Use Word File` (`WordProcessScope`) or `Word Application Scope`. It has no document handle of its own — outside a scope there is no document to insert into, so it is invalid. Faults synchronously or shows a design-time validation error. (A common variant: `Add Picture` lives in an `Invoke Workflow File` child and the scope's document context does not cross the invoke boundary.)
- **C2. COM / Interop exception.** The Word COM layer faults. `0x8002801D` (`TYPE_E_LIBNOTREGISTERED`, surfaces as `Unable to cast COM object...`) means the Word interop type library is not registered. `0x8001010A` (`RPC_E_SERVERCALL_RETRYLATER`, "The application is busy") means a `WINWORD.EXE` instance is wedged or blocked. Causes: an orphaned/hung `WINWORD.EXE`, a 32-bit/64-bit mismatch between Studio/Robot and Office, or missing/unregistered Office COM libraries. Often intermittent.
- **C3. Insertion target not found.** `Insert relative to` is `Text` or `Bookmark`, but the anchor does not exist in the open document. Text matching is **case- and whitespace-sensitive**; the named bookmark may be a typo, may live only in a template, or may have been removed upstream. (`Insert relative to = Document` has no anchor dependency.)
- **C4. Invalid path or unusable image.** `Picture to insert` (`ImagePath`) cannot be read. Causes: an in-memory `UiPath.Core.Image` variable was bound instead of a path string; a relative path that does not resolve under the Robot account; a missing/moved file (UNC unreachable, drive not mapped, OneDrive placeholder); or a path typo / extension-casing mismatch.

## Causes

Name the confirmed sub-cause exactly. Do NOT assert a cause unless the investigation decision tree arrived at it.

- **C1.** Activity outside a `Use Word File` / `Word Application Scope`.
- **C2.** Word COM / Interop exception (`0x8002801D` type library unregistered, or `0x8001010A` application busy).
- **C3.** Insertion target (text/bookmark) not found in the open document.
- **C4.** Invalid path or unusable image fed to `Picture to insert`.

## Investigation

1. **Read the error signature** from job evidence and the `Add Picture` configuration from the `.xaml`. Match against the decision tree below; stop at the first match.
2. **Decision tree:**
   - Design-time "invalid activity" validation error, or a missing-scope/context message → **C1**. Confirm in the `.xaml` that no ancestor of `Add Picture` is a `Use Word File` / `Word Application Scope` (and that the document context is not lost across an `Invoke Workflow File` boundary).
   - Error contains a COM HRESULT (`0x8002801D`, `0x8001010A`, or related) → **C2**. Capture the exact HRESULT, check the robot host for orphaned `WINWORD.EXE`, and capture the Office edition/channel/bitness (`File > Account > About Word`) versus the Studio/Robot process bitness.
   - Error references a missing bookmark or an unlocatable text anchor → **C3**. Read `InsertRelativeTo` and its anchor (`Text` string / `BookmarkName`), open the document the scope actually opened, and search for the anchor exactly (case + whitespace for text; the bookmark list for bookmarks). Confirm the opened file is the intended document, not a template or stale copy.
   - File-not-found or a generic exception reading the image → **C4**. Read the `ImagePath` binding and its type. If it is a `String`, resolve it to a concrete path and confirm the file exists on the robot host under the Robot's Windows user; if relative, determine the working directory it resolves against at runtime. If it is an `Image`/object variable, that is the cause.

## Resolution

Apply the fix for the identified sub-cause.

- **C1 — outside a scope:** wrap `Add Picture` in a `Use Word File` (preferred) or `Word Application Scope` pointed at the target document, and move the activity into the scope body. If it sits in an invoked child workflow, open the scope in that child or move the activity into the parent — scope context does not cross the invoke boundary implicitly. If the structure looks correct but validation still flags it, confirm `UiPath.Word.Activities` is installed and restored in `project.json`.
- **C2 — COM / Interop:**
  - **`0x8001010A` / orphaned process:** add a `Kill Process` activity for `WINWORD` at the start of the workflow (or kill it once via Task Manager / `Stop-Process -Name WINWORD -Force`) so the scope opens a clean instance; ensure no `Try/Catch` swallows the scope's `Dispose`.
  - **Bitness mismatch:** reinstall Office at the same architecture as the Studio/Robot process (both 32-bit or both 64-bit).
  - **`0x8002801D` / unregistered type library:** run an **online repair** of Microsoft Office (`Settings > Apps > Microsoft Office > Modify > Online Repair`) to re-register the COM libraries.
  - **Office restricted / unreliable:** migrate to the file-based `Word Document` activities (Studio panel under **System > File > Word Document**), which manipulate the `.docx` without launching Word.
- **C3 — target not found:** correct the `Text` anchor to match the document exactly (case + whitespace) or normalize the document text; add or fix the `BookmarkName` so it points at a bookmark that exists in that document. If only top/bottom placement is needed, switch `Insert relative to` to `Document` with `Position` = `Start` / `End` to drop the anchor dependency entirely. If the wrong document was opened, fix the scope's file path.
- **C4 — invalid path / image:** if an in-memory `UiPath.Core.Image` was bound, save it to disk first with `Save Image` and pass that path string. Use a fully-qualified **absolute** path (e.g. `C:\Images\chart.png`) or build one explicitly (`Path.Combine(...)`) so it resolves identically under the Robot account. Ensure the file is present and readable on the robot host under the Robot's Windows user.

If a COM HRESULT (C2) persists after all environmental causes are ruled out, capture a `Verbose` robot log plus a Process Monitor trace of `WINWORD.EXE` during the failure and open a UiPath support case.
