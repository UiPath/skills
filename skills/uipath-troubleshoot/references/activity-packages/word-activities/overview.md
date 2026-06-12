# Word Activities

Activities from the `UiPath.Word.Activities` package for automating Microsoft Word documents on Windows. Activities run inside a scope container that opens a single `.docx`/`.doc` and exposes it to the child activities: the modern `Use Word File` (`WordProcessScope`) or the classic `Word Application Scope`. Most document operations — including `Add Picture` — drive a real `WINWORD.EXE` instance through Office Interop (COM), so the package depends on a working, matching-bitness Microsoft Word install on the robot host.

A separate file-based path exists for hosts where Office is missing or locked down: the `Word Document` activities (Studio activity panel under **System > File > Word Document**, e.g. `WordDocumentScope`) read/write the `.docx` through the document object model without launching Word. They do not support every COM-only operation, but cover common read/insert tasks and are the migration target when COM interop cannot be made reliable.

## Add Picture (WordAddImage)

`Add Picture` (`UiPath.Word.Activities.WordAddImage`) inserts an image into the Word document opened by its parent scope. Behaviour chain:

1. Resolve the open document handle from the surrounding `Use Word File` / `Word Application Scope`.
2. Read the image from the path in the `Picture to insert` (`ImagePath`) property — a file path string, not an in-memory image object.
3. Locate the insertion point from `Insert relative to` — `Text` (a literal anchor string), `Bookmark` (a named bookmark), or `Document` (`Start` / `End`).
4. Insert the image at the resolved point and commit it to the document.

Failures can originate at any layer — scope/context (step 1), file path or image format (step 2), target resolution (step 3), or COM interop with Word itself (any step). Knowing which layer produced the error narrows the investigation.

Key properties: `ImagePath` ("Picture to insert" — fully-qualified absolute path or an exact relative path string), `InsertRelativeTo` ("Insert relative to" — `Text` / `Bookmark` / `Document`), the corresponding anchor (`Text` string, `BookmarkName`, or `Position` = `Start`/`End`), and sizing options (`Width` / `Height`).

## Common Failure Patterns

- **Activity outside a Word scope** — `Add Picture` is placed standalone, or in a sequence that is not nested inside a `Use Word File` / `Word Application Scope`. It faults immediately or shows a design-time validation error that the activity is invalid. `Add Picture` has no document handle of its own — it only operates on the document its parent scope opened. This is a configuration/structure error, not a runtime COM fault.
- **COM / Interop exception** — `Add Picture` (or the surrounding scope) faults with an HRESULT from the Word COM layer: `0x8002801D` (`TYPE_E_LIBNOTREGISTERED`, surfaces as `Unable to cast COM object...` — the Word interop type library is not registered) or `0x8001010A` (`RPC_E_SERVERCALL_RETRYLATER`, surfaces as `The application is busy`). Causes: an orphaned/hung `WINWORD.EXE` holding the document or blocked on a modal dialog, a 32-bit/64-bit mismatch between Studio/Robot and the Office install, or missing/unregistered Office COM libraries.
- **Insertion target not found** — `Insert relative to` is set to `Text` or `Bookmark`, but the anchor does not exist in the open document. The bot cannot find the reference point. Causes: the `Text` anchor string does not match the document exactly (the match is case-sensitive), the named bookmark does not exist in that specific document, or the anchor was present in a template but not in the actual document instance opened at runtime.
- **Invalid path or unusable image** — `Add Picture` faults with a file-not-found error or a generic exception while reading the image. Causes: the `Picture to insert` value is a relative path that does not resolve under the robot's working directory, the path points to a missing/moved file, or an in-memory `UiPath.Core.Image` variable was fed directly into the field instead of a path string. `Add Picture` expects a fully-qualified absolute path (or an exact relative path) to an image file on disk.

## Package

NuGet: `UiPath.Word.Activities`

Version-specific bugs are documented in the relevant playbooks.
