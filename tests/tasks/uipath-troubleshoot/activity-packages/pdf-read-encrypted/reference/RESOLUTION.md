# Final Resolution

**Fault:** The `ContractsIntake` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.PDF.Activities.ReadPDFText`** activity ("Read document text") and surfaces as `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException`.

**Root cause:** The input PDF is **password-protected (encrypted)** and the activity was given **no password (or the wrong one)**, so the reader could not open it. The actionable signature is `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException: The password is incorrect.`, raised from `UiPath.PDF.PdfReader..ctor` via `ReadPDFText.GetFileReader`. (A missing password reads as "incorrect" for an encrypted document.)

**Fix:** Set the `Password` argument on the Read PDF Text activity to the document's user password (store it as a secure asset/credential and, with explicit user approval, wire it from there). If a password was already set, correct it to the right one for this document.

**Must NOT attribute the root cause to:**
- A **missing / not-found file** — that would be `System.IO.FileNotFoundException: Could not find file ...`; here the file was found and opened far enough to detect it is encrypted.
- A **corrupt / invalid PDF** — that would be `PdfException: Invalid input stream`; this message is specifically `The password is incorrect.` (encryption, not corruption).
- **Manage PDF Password argument strings** (`A password for the encrypted PDF file was not supplied`, etc.) — those belong to the `Manage PDF Password` activity, not `Read PDF Text`.
- An **invalid page range**, a connection/Orchestrator problem, or a workflow-logic / null-variable bug.

A correct answer identifies that **`Read PDF Text` failed because the PDF is encrypted and no/wrong password was supplied (`PdfException: The password is incorrect.`)**, and recommends setting the correct `Password` on the activity. It must read the password signature rather than blaming a missing/corrupt file, Manage-PDF-Password validation, or the workflow logic.
