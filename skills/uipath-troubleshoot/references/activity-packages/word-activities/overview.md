# Word Activities

Activities from the `UiPath.Word.Activities` package for automating Microsoft Word documents on Windows. Activities run inside a scope container that opens a single `.docx`/`.doc`/`.dotx` and exposes it to the child activities: the modern `Use Word File` (`WordProcessScope`) or the classic `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`). Most document operations — including `Add Picture` — drive a real `WINWORD.EXE` instance through Office Interop (COM), so the package depends on a working, matching-bitness Microsoft Word install on the robot host.

A separate file-based path exists for hosts where Office is missing or locked down: the `Word Document` activities (Studio activity panel under **System > File > Word Document**, e.g. `WordDocumentScope`) read/write the `.docx` through the document object model without launching Word. They do not support every COM-only operation, but cover common read/insert tasks and are the migration target when COM interop cannot be made reliable.

## How Word Application Scope Executes

`Word Application Scope` opens a `.docx`/`.doc`/`.dotx` document inside a COM-backed WINWORD.EXE session, runs the child activities against that open document, then saves and closes. Behaviour chain:

1. Create the `Word.Application` COM instance (requires registered desktop Word; bitness must be compatible with the robot process)
2. Open the document at the configured path (or create it when `Create if not exists` is set)
3. Run child activities against the open document
4. Save and close, releasing the WINWORD.EXE handle

Failures originate at distinct layers — COM/Interop availability (step 1), file resolution and locks (step 2), interactive prompts that block COM (any step), or package/type loading (before step 1). Knowing which layer produced the error narrows the investigation.

## Add Picture (WordAddImage)

`Add Picture` (`UiPath.Word.Activities.WordAddImage`) inserts an image into the Word document opened by its parent scope. Behaviour chain:

1. Resolve the open document handle from the surrounding `Use Word File` / `Word Application Scope`.
2. Read the image from the path in the `Picture to insert` (`ImagePath`) property — a file path string, not an in-memory image object.
3. Locate the insertion point from `Insert relative to` — `Text` (a literal anchor string), `Bookmark` (a named bookmark), or `Document` (`Start` / `End`).
4. Insert the image at the resolved point and commit it to the document.

Failures can originate at any layer — scope/context (step 1), file path or image format (step 2), target resolution (step 3), or COM interop with Word itself (any step).

Key properties: `ImagePath` ("Picture to insert" — fully-qualified absolute path or an exact relative path string), `InsertRelativeTo` ("Insert relative to" — `Text` / `Bookmark` / `Document`), the corresponding anchor (`Text` string, `BookmarkName`, or `Position` = `Start`/`End`), and sizing options (`Width` / `Height`).

## Replace Text in Document

`Replace Text in Document` finds a `Search` string in the document opened by the surrounding scope and substitutes `Replace`. Classic `WordReplaceText` runs inside `Word Application Scope` (Interop); modern `ReplaceTextInDocument` runs inside `Use Word File`. They share a display name but run different code paths — treat them as distinct. Classic versions cap `Search`/`Replace` at 256 characters. A failure here is distinct from a scope-level fault: the scope opened fine; the failure is in the substitution (an exception, or a silent success with the document unchanged).

## Read Text

`Read Text` extracts the document's text. Two distinct surfaces fail for different reasons: the **Word-pack** `Read Text` reads the document held open by a surrounding `Use Word File` / `Word Application Scope` (it has no file input of its own); the **standalone** `Read Text` under `System > File > Word Document` takes a file path directly (no container) but is OpenXML `.docx`-only.

## Export to PDF

`Export to PDF` (`WordExportToPdf`, also "Save Document as PDF") exports the open document to a PDF at a target path, via Word Interop inside a `Word Application Scope`. It does **not** auto-create the output directory. Faults are about the **output** (missing target folder, malformed path) or **COM** (orphaned `WINWORD.EXE` / locked input), not the document content.

## Append Text

`Append Text` (`WordAppendText`) appends text to the document. Like Read Text, it has two surfaces: the **App-Integration** `Append Text` appends to the document held open by a surrounding `Word Application Scope` / `Use Word File` (no file input of its own); the **standalone** `Append Text` under the **Word Document** category takes a file path directly (no container, no Word install needed).

## Key Activities

- **Word Application Scope** (`WordApplicationScope`, display name "Word Application Scope") — open a Word document via Interop and run child activities against it. **COM-only** — requires desktop Word. Properties include the document `Path`, `CreateIfNotExists` (generate the file when absent), and `Password`.
- **Add Picture** (`WordAddImage`, display name "Add Picture") — insert an image into the document opened by the parent scope; see the `Add Picture` execution model above.
- **Replace Text in Document** (modern `ReplaceTextInDocument` inside `Use Word File`, classic `WordReplaceText` inside `Word Application Scope`) — find a `Search` string and substitute `Replace`. Classic versions cap `Search`/`Replace` at 256 characters.
- **Read Text** (display name "Read Text") — extract the document's text. Word-pack `Read Text` reads the document held open by a surrounding `Use Word File` / `Word Application Scope` (no file input of its own); the standalone `System > File > Word Document` `Read Text` takes a file path directly but is OpenXML `.docx`-only.
- **Export to PDF** (`WordExportToPdf`, display name "Export to PDF" / "Save Document as PDF") — export the open document to a PDF at a target path, via Interop inside a `Word Application Scope`. Does **not** auto-create the output directory.
- **Append Text** (`WordAppendText`, display name "Append Text") — append text to the document. App-Integration `Append Text` appends to the document held open by a surrounding `Word Application Scope` / `Use Word File` (no file input of its own); the standalone `Word Document` `Append Text` takes a file path directly (no container, no Word install needed).

## Common Failure Patterns

- **Word not installed / COM interop failure** — the scope faults at startup creating the COM instance. Surfaces as `Error opening document, make sure Word application is installed`, `REGDB_E_CLASSNOTREG` (`80040154`), or `Could not load ... Microsoft.Office.Interop.Word`. Causes: no desktop Word (web-only Office, Linux/container robot), 32-bit/64-bit Office–robot bitness mismatch, or damaged Office COM registration. Package-wide environmental failures (type library not registered, bitness mismatch, Word busy/blocked `0x8001010A`, `WINWORD.EXE` crashing mid-operation with `RPC_E_WRONG_THREAD` `0x8001010E`) are documented in [word-com-interop-failures.md](./playbooks/word-com-interop-failures.md).
- **"The file appears to be corrupted"** — opening/saving fails reporting corruption. Causes: an orphaned WINWORD.EXE holding the file lock, an in-place template overwrite leaving a half-written source, or Protected View / Mark-of-the-Web blocking the write.
- **Workflow hangs / freezes indefinitely** — WINWORD.EXE is up but unresponsive because Word opened a background modal prompt (password, document-recovery sidebar, Safe Mode, activation, trust-this-file). When the scope runs invisibly, the dialog still wedges the COM calls.
- **"Cannot create unknown type WordApplicationScope"** — load/compile-time failure: the execution host lacks the `UiPath.Word.Activities` package dependency, or runs a version without the type. Common when a process works in Studio but fails on a remote robot with a different/missing package version.
- **File path verification errors** — the document path does not resolve at runtime. Causes: opening a file that should be created (`Create if not exists` unset), a relative path resolved against the wrong working directory, a dynamically built path constructed incorrectly, or an unavailable mapped drive / unhydrated cloud placeholder.
- **Add Picture — activity outside a Word scope** — `Add Picture` is placed standalone, or in a sequence not nested inside a `Use Word File` / `Word Application Scope`. It faults immediately or shows a design-time validation error. `Add Picture` has no document handle of its own — it only operates on the document its parent scope opened. This is a configuration/structure error, not a runtime COM fault.
- **Add Picture — insertion target not found** — `Insert relative to` is set to `Text` or `Bookmark`, but the anchor does not exist in the open document. Causes: the `Text` anchor string does not match the document exactly (case-sensitive), the named bookmark does not exist in that document, or the anchor was present in a template but not the actual document instance opened at runtime.
- **Add Picture — invalid path or unusable image** — `Add Picture` faults with a file-not-found error or a generic exception while reading the image. Causes: a relative `Picture to insert` path that does not resolve under the robot's working directory, a missing/moved file, or an in-memory `UiPath.Core.Image` variable fed into the field instead of a path string. `Add Picture` expects a fully-qualified absolute path (or an exact relative path) to an image file on disk.
- **Replace Text — placeholder not replaced (silent)** — no exception, but the placeholder is unchanged because Word split it across internal XML runs (the token was edited/backspaced/reformatted in place), so the exact-string search never matches the contiguous term. Trace the output document content, not just the absence of an exception.
- **Replace Text — input string length limit** — classic versions enforce a hard 256-character cap on `Search`/`Replace`; longer values raise `ArgumentException` or truncate silently. Relaxed in current package versions.
- **Read Text — activity outside its container** — the modern Word-pack `Read Text` warns at design time / faults at runtime as invalid because it has no file input of its own and was dropped outside a `Use Word File` / `Word Application Scope`. Fix: nest it in a container, or use the standalone `System > File > Word Document` `Read Text` (takes a file path).
- **Read Text — standalone System Read Text fails on .doc** — the `System > File > Word Document` `Read Text` is OpenXML `.docx`-only and errors / returns nothing on legacy binary `.doc`. Fix: read `.doc` through a `Use Word File` (Interop reads both formats), or convert to `.docx` first.
- **Read Text — Protected View blocks an externally-sourced file** — reading a file from email / internet / external share faults or hangs because Word opens it in Protected View (Mark-of-the-Web). Fix: unblock the file, add the folder to Trusted Locations, or disable Protected View on the host.
- **Export to PDF — "Command Failed" (output directory missing)** — `Export to PDF` faults with a generic `Command Failed` because the target folder doesn't exist; the activity won't auto-create it. Fix: `Create Folder` before the export.
- **Export to PDF — malformed output path / missing `.pdf`** — the File Path is built from unformatted concatenation (no `.pdf` suffix, missing/doubled separator, empty variable segment). Fix: `Path.Combine(folder, name & ".pdf")` and validate the pieces.
- **Export to PDF — COM interop hang / crash / `COMException`** — an orphaned `WINWORD.EXE` or a locked input document blocks the export's COM call. Fix: Kill Process WINWORD before the scope, ensure the input is free; persistent → an Invoke Code C# `ExportAsFixedFormat` fallback.
- **Append Text — "Activity is valid only inside WordApplicationScope"** — the App-Integration `Append Text` is outside a `Word Application Scope` / `Use Word File`; it has no file input of its own. Fix: nest it in a scope, or use the standalone `Word Document` `Append Text` (takes a file path).
- **Append Text — "Archive file cannot be size zero"** — the target `.docx` is a 0-byte file (a renamed `.txt`, or a failed/truncated write), not a valid OpenXML package. Fix: delete it + `Create if not exists`, or fix the upstream that produced the empty file.

## Package

NuGet: `UiPath.Word.Activities`

Version-specific bugs are documented in the relevant playbooks.
