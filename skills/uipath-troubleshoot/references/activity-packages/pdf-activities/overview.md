# PDF Activities

Activities from the `UiPath.PDF.Activities` package for reading and manipulating PDF files on the robot's local filesystem — e.g. **Read PDF Text** (`ReadPDFText`), **Read PDF With OCR** (`ReadPDFWithOCR`), **Extract PDF Page Range** (`ExtractPDFPageRange`), **Extract Images From PDF**, **Extract Attachments from PDF**, **Export PDF Page As Image** (`ExportPDFPageAsImage`), **Merge PDF Files** / **Join PDFs**, **Create PDF From Images** (`CreatePDFFromImages`), and **Manage PDF Password** (`ManagePDFPassword`).

## How These Activities Work

These activities are purely local — they open a file path on the robot host and parse/transform it through the bundled Digitizer PDF processor (`UiPath.PDF.PdfReader` / `PdfHelper`). No Orchestrator or network call is involved (except `Read PDF With OCR`, which calls a configured OCR engine). The failure is therefore almost always about the **input file** (missing, not a PDF, encrypted, corrupt, or out-of-range page) or, for image/password activities, the **arguments**.

Two validation layers produce two exception shapes:

1. **Activity-level validation** (`ValidationHelper`, argument checks) throws `System.ArgumentException` / `System.ArgumentNullException` carrying a resource string (e.g. `The input file does not have a .PDF extension: <path>`). This fires before the file is parsed.
2. **Reader-level failures** (`PdfReader`) surface as `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException`. An encrypted PDF with a missing/wrong password gives `The password is incorrect.` (verified); a corrupt/non-PDF stream gives `Invalid input stream`. `Create PDF From Images` throws `UiPath.PDF.ImageToPdfException` for image-input problems.

## Key Activities

- **Read PDF Text** (`UiPath.PDF.Activities.ReadPDFText`) — extract the text layer of a PDF.
- **Read PDF With OCR** (`UiPath.PDF.Activities.ReadPDFWithOCR`) — OCR a PDF; requires an OCR engine activity dropped inside it.
- **Extract PDF Page Range** (`UiPath.PDF.Activities.ExtractPDFPageRange`) — split/trim by a page `Range` string.
- **Export PDF Page As Image** (`UiPath.PDF.Activities.ExportPDFPageAsImage`) — render one page to an image.
- **Merge PDF Files** / **Join PDFs** — combine a list of PDFs into one.
- **Create PDF From Images** (`UiPath.PDF.Activities.CreatePDFFromImages`) — one image per page.
- **Manage PDF Password** (`UiPath.PDF.Activities.ManagePDFPassword`) — set/change user & owner passwords.

## Common Failure Patterns

- **File not found / not a PDF** — `Could not find file "<path>"`, `The input file does not have a .PDF extension: <path>`, or the Merge variants. See [pdf-file-not-found-or-not-pdf.md](./playbooks/pdf-file-not-found-or-not-pdf.md).
- **Encrypted PDF / password problems** — `A password for the encrypted PDF file was not supplied`, a wrong-password `PdfException`, or Manage PDF Password argument errors. See [pdf-encrypted-or-wrong-password.md](./playbooks/pdf-encrypted-or-wrong-password.md).
- **Invalid page range / page number** — `Extract PDF Page Range` raises `InvalidPageRangeException` (`The input string '<value>' was not in a correct format.` or `Page range is incorrect.`); `Export PDF Page As Image` raises `The provided page number is invalid`. See [pdf-invalid-page-range.md](./playbooks/pdf-invalid-page-range.md).
- **Read PDF With OCR — no/failed OCR engine** — `No OCR Engine assigned.` or `Digitization failed with status ...`. See [pdf-read-ocr-no-engine.md](./playbooks/pdf-read-ocr-no-engine.md).
- **Corrupt PDF / Create-PDF-From-Images input errors** — `PdfException` (`Invalid input stream`) or `ImageToPdfException` variants. See [pdf-corrupt-or-image-input.md](./playbooks/pdf-corrupt-or-image-input.md).

## Package

NuGet: `UiPath.PDF.Activities` · Exceptions: `UiPath.PDF` (`PdfException`, `ImageToPdfException`)
