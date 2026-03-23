# ExtractPDFPageRange

Extracts a range of pages from a PDF file into a new PDF.

```xml
<uisappr:ExtractPDFPageRange
    FilePassword="{x:Null}"
    ResultFileName="{x:Null}"
    DisplayName="Extract PDF Page Range"
    ExportedPdf="[extractedPdf]"
    PageRange="[&quot;1-3&quot;]"
    PdfFile="[LocalResource.FromPath(filePath)]" />
```

- `PageRange` — string expression (e.g., `"1-3"`, `"2"`, `"1,3,5"`)
- `ExportedPdf` — output `upr:ILocalResource` variable
- `FilePassword` — optional string for password-protected PDFs; `{x:Null}` when not needed
- `ResultFileName` — optional output file name; `{x:Null}` to use default
