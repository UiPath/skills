# ExtractPDFImages

Extracts images from a PDF file.

```xml
<uisapi:ExtractPDFImages
    FilePassword="{x:Null}"
    ImageExtension="{x:Null}"
    DisplayName="Extract PDF Images"
    ExtractedImages="[pdfImages]"
    PdfFile="[LocalResource.FromPath(filePath)]" />
```

- `ExtractedImages` — output `IEnumerable(Of upr:ILocalResource)` variable
- `FilePassword` — optional string for password-protected PDFs; `{x:Null}` when not needed
- `ImageExtension` — optional string to filter by image format (e.g., `"png"`); `{x:Null}` for all formats
