# XAML PDF Activities (UiPath.DocumentUnderstanding.Activities)

PDF activity patterns from `UiPath.DocumentUnderstanding.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

## Package

`UiPath.DocumentUnderstanding.Activities`

## Variable Types

| Type | Description |
|------|-------------|
| `upr:ILocalResource` | Output of PDF utility activities (file handles for exported PDFs, images) |

## File Input Pattern

All activities that accept a PDF file use `IResource`:

```xml
PdfFile="[LocalResource.FromPath(filePath)]"
```

Where `filePath` is a `String` variable containing the local file path.

## PDF Activities

All PDF activities are standalone — no scope container needed.

### ExtractPDFText

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

### GetPDFPageCount

```xml
<uisapg:GetPDFPageCount
    FilePassword="{x:Null}"
    DisplayName="Get PDF Page Count"
    PageCount="[pageCount]"
    PdfFile="[LocalResource.FromPath(filePath)]" />
```

- `PageCount` — output `Int32` variable
- `FilePassword` — optional string for password-protected PDFs; `{x:Null}` when not needed

### SetPDFPassword

```xml
<uisaps:SetPDFPassword
    CurrentManagePassword="{x:Null}"
    CurrentOpenPassword="{x:Null}"
    NewManagePassword="{x:Null}"
    ResultFileName="{x:Null}"
    DisplayName="Set PDF Password"
    ExportedPdf="[exportedPdf]"
    NewOpenPassword="[password]"
    PdfFile="[LocalResource.FromPath(filePath)]" />
```

- `ExportedPdf` — output `upr:ILocalResource` variable
- `NewOpenPassword` — string expression for the new open password
- `CurrentOpenPassword` / `CurrentManagePassword` — set when changing password on an already-protected PDF; `{x:Null}` otherwise
- `NewManagePassword` — optional; `{x:Null}` when not needed
- `ResultFileName` — optional output file name; `{x:Null}` to use default

### MergePDFs

Use `IndividualPdfFiles` nested property to specify files inline, or `CollectionPdfFiles` to pass a variable:

```xml
<uisapm:MergePDFs
    CollectionPdfFiles="{x:Null}"
    DisplayName="Merge PDFs"
    ExportedPdf="[mergedPdf]"
    ResultFileName="[mergedDocumentName]">
  <uisapm:MergePDFs.IndividualPdfFiles>
    <scg:List x:TypeArguments="InArgument(upr:IResource)" Capacity="4">
      <InArgument x:TypeArguments="upr:IResource">[LocalResource.FromPath(firstFilePath)]</InArgument>
      <InArgument x:TypeArguments="upr:IResource">[LocalResource.FromPath(secondFilePath)]</InArgument>
    </scg:List>
  </uisapm:MergePDFs.IndividualPdfFiles>
</uisapm:MergePDFs>
```

- `IndividualPdfFiles` — nested property; `List<InArgument<IResource>>` for inline file list
- `CollectionPdfFiles` — attribute alternative; `IEnumerable(Of IResource)` variable; `{x:Null}` when using `IndividualPdfFiles`
- `ExportedPdf` — output `upr:ILocalResource` variable
- `ResultFileName` — optional name for the merged PDF file

### ExtractPDFPageRange

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

### ExtractPDFImages

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

## Key Patterns

| Pattern | Notes |
|---------|-------|
| File input | `[LocalResource.FromPath(filePath)]` — always use this for IResource parameters |
| PDF output type | `upr:ILocalResource` — output type for SetPDFPassword, MergePDFs, ExtractPDFPageRange |
| Images output type | `IEnumerable(Of upr:ILocalResource)` — output type for ExtractPDFImages |
| MergePDFs inline | Use nested `IndividualPdfFiles` property with `scg:List`; set `CollectionPdfFiles="{x:Null}"` |
| MergePDFs variable | Set `CollectionPdfFiles` to an `IEnumerable(Of IResource)` variable; omit `IndividualPdfFiles` |
| OCR extraction | Set `ApplyOcr="True"` and `OcrEngine="UIPATH_DOCUMENT_OCR"` on `ExtractPDFText` for scanned PDFs |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
