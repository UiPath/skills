# UiPath PDF Activities - Legacy Reference

## Overview
PDF reading, manipulation, and conversion. Uses UiPath.DocumentUnderstanding.Digitizer (NOT iTextSharp). Package: `UiPath.PDF.Activities`.

---

## Activities

### Text Extraction
| Activity | Key Arguments | Output |
|----------|---------------|--------|
| `ReadPDFText` | FileName, Password, Range (default "All"), PreserveFormatting | Text (string) |
| `ReadPDFWithOCR` | FileName, Password, Range, ImageDpi (Low/Medium/High), DegreeOfParallelism | Text (string) |
| `ReadXPSText` | Same as ReadPDFText (desktop only) | Text |
| `ReadXPSWithOCR` | Same as ReadPDFWithOCR (desktop only) | Text |

### Image Operations
| Activity | Key Arguments | Output |
|----------|---------------|--------|
| `ExportPDFPageAsImage` | FileName, Password, PageNumber (1-based), ImageDpi, OutputFileName | OutputFile (ILocalResource) |
| `ExtractImagesFromPDF` | FileName, Password, ImageExtension (PNG/JPEG/TIFF/BMP/GIF), OutputFolderName | OutputFiles |

### Page Manipulation
| Activity | Key Arguments | Output |
|----------|---------------|--------|
| `ExtractPDFPageRange` | FileName, Password, Range, OutputFileName | OutputFile |
| `JoinPDF` | FileList (string[]) or IndividualResourceFileList, OutputFileName | OutputFile |
| `GetPDFPageCount` | FileName, Password | PageCount (int) |

### Password Management
| Activity | Key Arguments | Output |
|----------|---------------|--------|
| `ManagePDFPassword` | FileName, OldUserPassword, NewUserPassword, OldOwnerPassword, NewOwnerPassword | OutputFile |

### Conversion (NET5+)
| Activity | Key Arguments | Output |
|----------|---------------|--------|
| `ConvertTextToPDF` | Text, FontSize (12), TextAlignment (Justify) | OutputFile |
| `ConvertHtmlToPDF` | Html, Scale (1.0), PaperSize (A4), HeaderHtml, FooterHtml | OutputFile |
| `ConvertEmailToPDF` | Email (MailMessage) | OutputFile |

---

## Critical Gotchas

### Password-Protected PDFs
1. **User Password** restricts opening (must provide to view)
2. **Owner Password** restricts editing but allows viewing
3. **Owner password required to change passwords** - throws `NoOwnerRightsException` otherwise
4. **New passwords cannot match each other** or existing passwords

### OCR
5. **No automatic OCR fallback** - ReadPDFText won't fall back to OCR on scanned PDFs
6. **OCR engine must be explicitly wired** in workflow (no built-in engine)
7. **Empty page handling** - returns empty string (no exception)
8. **DegreeOfParallelism** auto-capped to max(1, CPUs - 1)

### Page Ranges
9. **Format**: `"1,3-5,7"` (comma-separated, dash for ranges). Also supports keywords: `All`, `End`, `^` (start), `$` (end). Examples: `"1-End"`, `"^-$"`
10. **"All"** is the default (extracts all pages)
11. **Throws FormatException** on invalid range syntax

### Image DPI
12. **Low=96, Medium=150, High=270** DPI
13. **Max pixel constraints**: 3000px width, 4000px height (auto-scaled down)
14. **Higher DPI = better OCR but slower**

### JoinPDF
15. **Requires at least 2 files** - validation error otherwise
16. **Must provide FileList OR ResourceFileList** (not both)

### License
17. **Runtime license check** via `PdfLicenseManager.EnsureValidLicense()` - will fail without valid license

### XPS Activities
18. **Desktop-only** (`#if !NETPORTABLE_UIPATH`) - not available in portable workflows

### Additional Validated Gotchas
21. **ImageDpi enum maxes at 270 (High), not 300** - combined with 3000x4000 pixel cap, large pages get lower effective DPI
22. **ReadPDFText PreserveFormatting defaults to false** - text extraction without formatting produces garbled output for multi-column layouts
23. **Underlying library is Docotic.Pdf and PdfPig** (not iTextSharp) - commercial library with embedded license

### File Resources
19. **Dual-mode inputs**: All activities accept both file paths (string) and IResource objects via OverloadGroups
20. **Auto-generated output filename** if OutputFileName not provided
