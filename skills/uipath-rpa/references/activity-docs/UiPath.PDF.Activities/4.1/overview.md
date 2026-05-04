# UiPath PDF Activities

`UiPath.PDF.Activities`

A set of activities for working with PDF and XPS documents: read text, extract images, export pages as images, join and split PDF files, manage passwords, and convert HTML, plain text, and email content to PDF.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

## Activities

### App Integration > PDF

| Activity                                                       | Description                                                                                               |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [Get PDF Page Count](activities/GetPDFPageCount.md)            | Pick a PDF document and get its page count.                                                               |
| [Manage PDF Password](activities/ManagePDFPassword.md)         | Manage the password set for a PDF file.                                                                   |
| [Join PDF Files](activities/JoinPDF.md)                        | Merge two or more PDF files together into a single document.                                              |
| [Extract PDF Page Range](activities/ExtractPDFPageRange.md)    | Extract a range of pages from a PDF file into a new document.                                             |
| [Convert HTML to PDF](activities/ConvertHtmlToPDF.md)          | Convert HTML content to a PDF file.                                                                       |
| [Convert Text to PDF](activities/ConvertTextToPDF.md)          | Convert plain text content to a PDF file.                                                                 |
| [Convert Email to PDF](activities/ConvertEmailToPDF.md)        | Convert an email message to a PDF file.                                                                   |
| [Export PDF Page As Image](activities/ExportPDFPageAsImage.md) | Export a single PDF page as an image at a specified DPI.                                                  |
| [Extract Images From PDF](activities/ExtractImagesFromPDF.md)  | Extract all embedded images from a PDF file and save them to a folder.                                    |
| [Read PDF Text](activities/ReadPDFText.md)                     | Read and return all text from a PDF file, with optional formatting preservation and page range filtering. |
| [Read PDF With OCR](activities/ReadPDFWithOCR.md)              | Read all characters from a PDF file using OCR technology, for scanned PDFs where native text extraction returns empty results. Use UiPath Document OCR as the OCR engine (requires Endpoint and ApiKey). |
| [Read XPS Text](activities/ReadXPSText.md)                     | Read and return all text from an XPS file, with optional page range filtering. Windows only.              |
| [Read XPS With OCR](activities/ReadXPSWithOCR.md)              | Read all characters from an XPS file using OCR technology, for scanned documents. Windows only. Use UiPath Document OCR as the OCR engine (requires Endpoint and ApiKey). |
