# Final Resolution

**Fault:** The `StatementsBatch` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.PDF.Activities.ReadPDFText`** activity ("Read document text") and surfaces as `UiPath.PDF.PdfException`.

**Root cause:** The input file exists and has a `.PDF` extension, but its **bytes are not a valid PDF** — the Digitizer PDF reader rejects the stream. The actionable signature is `UiPath.PDF.PdfException: Invalid input stream`, raised from `UiPath.PDF.PdfReader..ctor` when `OpenDocument` cannot parse the file. The file is corrupt, truncated, zero-byte, or a non-PDF renamed to `.pdf` (commonly an upstream download/write that didn't finish, or the wrong file staged).

**Fix:** Replace the input with a valid, fully-written PDF. If an upstream step (download, export, another activity) produces the file, ensure that step completes and releases the file before `Read PDF Text` runs (add a wait/verify on the upstream output). Confirm the file opens in a PDF viewer.

**Must NOT attribute the root cause to:**
- A **missing / not-found file** — that would be `System.IO.FileNotFoundException: Could not find file ...`; here the file was found and opened, and only the *content* failed to parse (`PdfException: Invalid input stream`).
- **Encryption / wrong password** — that would be a `PdfException` wrapping `PdfIncorrectPasswordException`, or (for Manage PDF Password) `A password for the encrypted PDF file was not supplied`; this message is specifically `Invalid input stream` (unparseable bytes), not a password issue.
- A **missing OCR engine** (`No OCR Engine assigned.`), an **invalid page range** (`InvalidPageRangeException`), a connection/Orchestrator problem, or a workflow-logic / null-variable bug.

A correct answer identifies that **`Read PDF Text` could not parse the input file because it is corrupt / not a valid PDF (`PdfException: Invalid input stream`)**, and recommends replacing it with a valid PDF (and fixing any upstream step that produced the bad file). It must read the `Invalid input stream` signature rather than blaming a missing file, encryption, OCR, or the workflow logic.
