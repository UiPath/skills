# Word Activities

Activities from the `UiPath.Word.Activities` package for automating Microsoft Word on Windows. The classic `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`) drives a real WINWORD.EXE instance via **Microsoft Word Interop (COM)** — it requires desktop Word installed on the execution host. A modern `Use Word File` surface exists for newer design experiences and is the recommended migration target for several classic failure modes.

## How Word Application Scope Executes

`Word Application Scope` opens a `.docx`/`.doc`/`.dotx` document inside a COM-backed WINWORD.EXE session, runs the child activities against that open document, then saves and closes. Behaviour chain:

1. Create the `Word.Application` COM instance (requires registered desktop Word; bitness must be compatible with the robot process)
2. Open the document at the configured path (or create it when `Create if not exists` is set)
3. Run child activities against the open document
4. Save and close, releasing the WINWORD.EXE handle

Failures originate at distinct layers — COM/Interop availability (step 1), file resolution and locks (step 2), interactive prompts that block COM (any step), or package/type loading (before step 1). Knowing which layer produced the error narrows the investigation.

## Key Activities

- **Word Application Scope** (`WordApplicationScope`, display name "Word Application Scope") — open a Word document via Interop and run child activities against it. **COM-only** — requires desktop Word. Properties include the document `Path`, `CreateIfNotExists` (generate the file when absent), and `Password`.
- **Replace Text in Document** (display name "Replace Text in Document" / classic "Replace Text"; modern `ReplaceTextInDocument` inside `Use Word File`, classic `WordReplaceText` inside `Word Application Scope`) — find a `Search` string in the open document and substitute `Replace`. Runs against the document held by the surrounding scope. Classic versions cap `Search`/`Replace` at 256 characters.
- **Read Text** (display name "Read Text") — extract the document's text. Two surfaces: the **Word-pack** `Read Text` reads the document held open by a surrounding `Use Word File` / `Word Application Scope` (no file input of its own); the **standalone** `Read Text` under `System > File > Word Document` takes a file path directly (no container) but is OpenXML `.docx`-only.
- **Export to PDF** (`WordExportToPdf`, display name "Export to PDF" / "Save Document as PDF") — export the open document to a PDF at a target path, via Word **Interop** inside a `Word Application Scope`. Does **not** auto-create the output directory.

## Common Failure Patterns

- **Word not installed / COM interop failure** — the scope faults at startup creating the COM instance. Surfaces as `Error opening document, make sure Word application is installed`, `REGDB_E_CLASSNOTREG` (`80040154`), or `Could not load ... Microsoft.Office.Interop.Word`. Causes: no desktop Word (web-only Office, Linux/container robot), 32-bit/64-bit Office–robot bitness mismatch, or damaged Office COM registration.
- **"The file appears to be corrupted"** — opening/saving fails reporting corruption. Causes: an orphaned WINWORD.EXE holding the file lock, an in-place template overwrite leaving a half-written source, or Protected View / Mark-of-the-Web blocking the write.
- **Workflow hangs / freezes indefinitely** — WINWORD.EXE is up but unresponsive because Word opened a background modal prompt (password, document-recovery sidebar, Safe Mode, activation, trust-this-file). When the scope runs invisibly, the dialog still wedges the COM calls.
- **"Cannot create unknown type WordApplicationScope"** — load/compile-time failure: the execution host lacks the `UiPath.Word.Activities` package dependency, or runs a version without the type. Common when a process works in Studio but fails on a remote robot with a different/missing package version.
- **File path verification errors** — the document path does not resolve at runtime. Causes: opening a file that should be created (`Create if not exists` unset), a relative path resolved against the wrong working directory, a dynamically built path constructed incorrectly, or an unavailable mapped drive / unhydrated cloud placeholder.

### Replace Text in Document

- **"Application is busy" / COM interop retry** — the activity's COM call is rejected because WINWORD.EXE is busy: open in the background, locked by another session, or stalled on a hidden modal dialog. Surfaces as `RPC_E_SERVERCALL_RETRYLATER` (`0x8001010A`) or `RPC_E_CALL_REJECTED` (`0x80010001`), often intermittent.
- **File lock / read-only on save** — the scope cannot persist the edit: `The process cannot access the file because it is being used by another process` or `the file is read-only`. Causes: `Auto Save` racing another access inside a loop, a `Save As`/rename to the same still-open path, a concurrent job/sync client, or the read-only attribute set.
- **Placeholder not replaced (silent)** — no exception, but the placeholder is unchanged because Word split it across internal XML runs (the token was edited/backspaced/reformatted in place), so the exact-string search never matches the contiguous term.
- **Input string length limit** — classic versions enforce a hard 256-character cap on `Search`/`Replace`; longer values raise `ArgumentException` or truncate silently. Relaxed in current package versions.
- **TargetInvocationException / Studio crash on drop** — design-time failure when the activity is dropped or the workflow opened, from a Studio↔package version mismatch that cannot construct the designer. Distinct from the runtime "Cannot create unknown type" package gap.
- **Placeholder replaced once, then missing in a loop** — succeeds on iteration 1, then later rows have nothing to replace because the workflow edits the template in place and the first replacement consumed the placeholder. Fix: copy the template to a fresh temp file per iteration.
- **Headers / footers / text boxes skipped** — no error, but placeholders outside the main body (headers, footers, floating text boxes/shapes) survive because older package versions scan only body text. Fix: update `UiPath.Word.Activities`.
- **Multi-line replacement loses formatting** — styled/multi-paragraph replacement collapses to one line because the `Replace` value carries raw `Environment.NewLine` breaks. Use Bookmarks / Form Fields + `Set Bookmark Text` for rich content.

### Read Text

- **Activity outside its container** — the modern Word-pack `Read Text` warns at design time / faults at runtime as invalid because it has no file input of its own and was dropped outside a `Use Word File` / `Word Application Scope`. Fix: nest it in a container, or use the standalone `System > File > Word Document` `Read Text` (takes a file path).
- **Standalone System Read Text fails on .doc** — the `System > File > Word Document` `Read Text` is OpenXML `.docx`-only and errors / returns nothing on legacy binary `.doc`. Fix: read `.doc` through a `Use Word File` (Interop reads both formats), or convert to `.docx` first.
- **Protected View blocks an externally-sourced file** — reading a file from email / internet / external share faults or hangs because Word opens it in Protected View (Mark-of-the-Web). Fix: unblock the file, add the folder to Trusted Locations, or disable Protected View on the host.
- **"Application is busy" / COM interop** — same `RPC_E_SERVERCALL_RETRYLATER` (`0x8001010A`) busy-Word failure as Replace Text; the cause and fix are shared (see the Replace Text COM-busy playbook).

### Export to PDF

- **"Command Failed" — output directory missing** — `Export to PDF` faults with a generic `Command Failed` because the target folder doesn't exist; the activity won't auto-create it. Fix: `Create Folder` before the export.
- **Malformed output path / missing `.pdf`** — the File Path is built from unformatted concatenation (no `.pdf` suffix, missing/doubled separator, empty variable segment). Fix: `Path.Combine(folder, name & ".pdf")` and validate the pieces.
- **COM interop hang / crash / `COMException`** — an orphaned `WINWORD.EXE` or a locked input document blocks the export's COM call. Fix: Kill Process WINWORD before the scope, ensure the input is free; persistent → an Invoke Code C# `ExportAsFixedFormat` fallback.
- **`TargetInvocationException` / outdated package** — same design-time version-mismatch signature as Replace Text; update `UiPath.Word.Activities` (see the Replace Text version-mismatch playbook).

## Package

NuGet: `UiPath.Word.Activities`

Version-specific bugs are documented in the relevant playbooks.
