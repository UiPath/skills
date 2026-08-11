---
confidence: medium
---

# PDF — Corrupt PDF or Create-PDF-From-Images input error

## Context

Two reader-level failure families that aren't path/password/range problems:

1. **Corrupt or non-PDF stream** — the file exists and has a `.PDF` extension, but its bytes aren't a valid PDF (truncated download, zero-byte file, a renamed non-PDF, or an in-flight/locked write). The reader fails to open it.
2. **Create PDF From Images input** — `CreatePDFFromImages` rejects the image list (empty, unsupported format, an unreadable image).

What this looks like:

- `UiPath.PDF.PdfException: Invalid input stream` — the bytes can't be parsed as a PDF (the reader catches the processor's `Invalid input stream` `ArgumentException` and re-throws it as `PdfException`). Corrupt/truncated/zero-byte/not-actually-a-PDF.
- `The image list must contain at least one image` (`CreatePDFFromImages`) — no images supplied.
- `The image list contains files with unsupported extensions. Supported formats: PNG, JPG, JPEG, JPE, TIF, TIFF, BMP.` — an image is in an unsupported format.
- `The TIFF file '<path>' does not contain any image frames.` (`UiPath.PDF.ImageToPdfException`) — a TIFF with zero frames.
- `The image '<path>' has invalid dimensions (<w>x<h>).` (`ImageToPdfException`) — an image with unusable dimensions (e.g. 0×0).
- `GIF output is no longer supported. Please choose PNG, JPEG, TIFF, or BMP.` — a removed output format was requested.
- `Attachment has an unsafe or invalid name: '<name>'` — `Extract Attachments from PDF` hit an embedded attachment whose name is unsafe to write to disk.

What can cause it:
- **Corrupt / partial / mislabeled file** — the PDF was truncated, never finished writing, is zero bytes, or is a non-PDF renamed to `.pdf`.
- **Empty / wrong-format image list** — `CreatePDFFromImages` got no images or an unsupported/zero-frame/zero-dimension image.
- **Unsafe attachment name** — an embedded file's name contains path/character sequences the activity refuses to write.

What to look for:
- `PdfException: Invalid input stream` (no inner `PdfIncorrectPasswordException`) = corrupt/non-PDF content, not encryption. `ImageToPdfException` = the image input, specific to `Create PDF From Images`.

> **Different cause — do not apply this playbook:**
> - `PdfException` whose inner is `PdfIncorrectPasswordException`, or `A password for the encrypted PDF file was not supplied` → encryption, use [pdf-encrypted-or-wrong-password.md](./pdf-encrypted-or-wrong-password.md).
> - `Could not find file` / `does not have a .PDF extension` → the path, use [pdf-file-not-found-or-not-pdf.md](./pdf-file-not-found-or-not-pdf.md).

## Investigation

1. **Classify by exception type.** `PdfException` (`Invalid input stream`) → corrupt/non-PDF file. `ImageToPdfException` / image-list `ArgumentException` → `CreatePDFFromImages` input.
2. **For a corrupt-file `PdfException`,** check the file on the robot host: size (zero bytes?), whether it opens in a PDF viewer, and whether an upstream step (download / another activity) finished writing it before this activity ran (a race / locked file).
3. **For an image error,** capture the offending image path and its actual format/dimensions/frame count from the message.

## Resolution

- **If `PdfException: Invalid input stream`:** replace the file with a valid, fully-written PDF. If an upstream activity produces it, ensure that step completes (and releases the file) before the read — add a wait / verify on the upstream output with explicit user approval before changing the workflow.
- **If `The image list must contain at least one image`:** supply at least one image to `Create PDF From Images`.
- **If `unsupported extensions`:** convert/replace images to a supported format (PNG, JPG, JPEG, JPE, TIF, TIFF, BMP).
- **If `does not contain any image frames` / `invalid dimensions`:** replace the bad TIFF/image with a valid one.
- **If `GIF output is no longer supported`:** choose PNG, JPEG, TIFF, or BMP output.
- **If `Attachment has an unsafe or invalid name`:** the embedded attachment's name is unsafe — extract with an explicit safe output name / filter, or handle that attachment separately.
