# Final Resolution

**Fault:** The `InvoiceProcessing` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.PDF.Activities.ReadPDFText`** activity ("Read document text") and surfaces as `System.IO.FileNotFoundException`.

**Root cause:** The PDF activity faulted at **input-file validation** — the configured input file does not exist on the robot host. The actionable signature is `Could not find file "C:\RPA\Invoices\incoming\invoice_4471.pdf"`, thrown from `UiPath.PDF.Activities.PDF.ValidationHelper.ValidateInputFilePath` before the PDF was ever opened. The file at that path was not present on the machine that ran the job (wrong/relative path, the file wasn't staged on the unattended robot host, or an upstream step didn't produce it).

**Fix:** Ensure the input PDF exists at the configured path **on the robot host** that runs the job, or correct the path argument to point at a file that exists there (use an absolute path, or stage/produce the file before the read). If the path comes from an upstream variable, fix the expression that produced it.

**Must NOT attribute the root cause to:**
- The **PDF content / encryption / corruption** — the activity never opened the file; this is a pre-parse path-existence check (`FileNotFoundException`), not a `UiPath.PDF.PdfException` (which would indicate an encrypted or corrupt PDF).
- **A missing OCR engine** — that is a different failure (`No OCR Engine assigned.`) specific to `Read PDF With OCR`; this is plain `Read PDF Text`.
- **A wrong page range** — that would be `The Range argument does not have a valid format` / `ArgumentOutOfRangeException`.
- **A workflow-logic or null-variable bug**, a connection/Orchestrator problem, or a licensing/robot issue.

A correct answer identifies that **`Read PDF Text` could not find its input file at the configured path on the robot host (`FileNotFoundException: Could not find file ...`)**, and recommends making the file present at that path (or correcting the path argument). It must read the missing-file signature rather than blaming the PDF content, OCR, or the workflow logic.
