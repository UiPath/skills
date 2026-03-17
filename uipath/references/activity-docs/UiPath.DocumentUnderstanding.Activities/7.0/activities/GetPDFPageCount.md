# GetPDFPageCount

Gets the number of pages in a PDF file.

```xml
<uisapg:GetPDFPageCount
    FilePassword="{x:Null}"
    DisplayName="Get PDF Page Count"
    PageCount="[pageCount]"
    PdfFile="[LocalResource.FromPath(filePath)]" />
```

- `PageCount` — output `Int32` variable
- `FilePassword` — optional string for password-protected PDFs; `{x:Null}` when not needed
