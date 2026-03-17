# ExtractPDFText

Extracts text content from a PDF file.

```xml
<uisape:ExtractPDFText
    FilePassword="{x:Null}"
    ApplyOcr="False"
    DisplayName="Extract PDF Text"
    OcrEngine="{x:Null}"
    PdfFile="[LocalResource.FromPath(filePath)]"
    Text="[pdfText]" />
```

- `Text` — output `String` variable
- `ApplyOcr` — set `True` to apply OCR on scanned PDFs; when `True`, set `OcrEngine="UIPATH_DOCUMENT_OCR"`
- `FilePassword` — optional string for password-protected PDFs; `{x:Null}` when not needed
