# WordExportToPdf

Exports the Word document to a PDF file.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordExportToPdf
    DisplayName="Export to PDF"
    FilePath="[pdfOutputPath]"
    ReplaceExisting="True" />
```

- `FilePath` — output PDF file path (string expression)
- `ReplaceExisting` — `True` to overwrite an existing file at the path
