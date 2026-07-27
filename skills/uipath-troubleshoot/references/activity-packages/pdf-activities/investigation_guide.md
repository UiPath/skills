# PDF Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's class matches the reported failure (`UiPath.PDF.Activities.ReadPDFText`, `...ReadPDFWithOCR`, `...ExtractPDFPageRange`, `...CreatePDFFromImages`, `...ManagePDFPassword`, etc.). A different PDF activity = a different failure family.
- **Input file** — the file path in the error is the one the user is asking about. PDF activities are local; the path names the exact file on the robot host.
- **Workflow file** — the error originates from the workflow the user references, not another `.xaml`/`.cs` that also touches PDFs.
- **Host** — the robot host that ran the job is where the file must exist. A path that resolves on the developer machine may not exist on the unattended robot.
- **Timestamp** — the failure occurred in the reported window.

If the data doesn't match: discard it.

## Domain-Specific Data Gathering

1. **Classify by exception type first.**
   - `System.ArgumentException` / `System.ArgumentNullException` carrying a PDF resource string → **activity-level validation** failed before parsing (missing path, wrong extension, empty file list, range format). The file may not even have been opened.
   - `UiPath.PDF.PdfException` → **reader-level** failure: wrong/missing password (inner `PdfIncorrectPasswordException`) or a corrupt/non-PDF stream (`Invalid input stream`).
   - `UiPath.PDF.ImageToPdfException` → **Create PDF From Images** input problem (unsupported extension, TIFF with no frames, invalid dimensions).
   - `System.ArgumentOutOfRangeException` → a requested page is outside the document's page count.
2. **Read the message verbatim and match it to a playbook signature.** PDF messages are fixed resource strings — match the literal text (e.g. `No OCR Engine assigned.`, `The Range argument does not have a valid format`), not a paraphrase.
3. **Distinguish "no password supplied" from "wrong password."** `A password for the encrypted PDF file was not supplied` is the activity-level check (no `Password` set). A `PdfException` whose inner is `PdfIncorrectPasswordException` means a password was supplied but rejected.
4. **For file-not-found, confirm where the file should be.** PDF activities run on the robot host; a path valid in the project/dev machine may be absent or differently mapped under the unattended robot account. Check the path is absolute or resolves against the right working folder.

## Testing Prerequisites

1. **Activity identity** — confirm which PDF activity and capture its display name.
2. **Exception type + message** — `ArgumentException`/`ArgumentNullException` (validation) vs. `PdfException` (reader) vs. `ImageToPdfException` (images) vs. `ArgumentOutOfRangeException` (page range), with the verbatim message.
3. **Input file** — the file path, whether it exists on the robot host, its extension, and whether it is encrypted (`Manage PDF Password` / `IsUserPasswordProtected`).
4. **Arguments** — for page-range activities the `Range` string and the document page count; for `Manage PDF Password` the user/owner password fields; for `Create PDF From Images` the image list and formats.
5. **OCR engine** — for `Read PDF With OCR`, whether an OCR engine activity is present inside the scope and configured.
6. **Package version** — `UiPath.PDF.Activities` version.
