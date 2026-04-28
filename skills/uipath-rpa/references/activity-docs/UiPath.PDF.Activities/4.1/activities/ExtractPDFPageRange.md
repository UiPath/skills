# Extract PDF Page Range

`UiPath.PDF.Activities.PDF.ExtractPDFPageRange`

Extracts a specified range of pages from a PDF file and writes them to a new PDF. The page range is expressed as a string (e.g., `"2-4"`). Supports password-protected source files.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | InArgument | `string` | Yes* | | | The local file path of the source PDF. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | InArgument | `IResource` | Yes* | | | The file resource to read from. Mutually exclusive with `FileName`. |
| `Range` | Range | InArgument | `string` | Yes | | | The page range to extract (e.g., `"2-4"`). Must be a valid range within the document's page count. |
| `Password` | Password | InArgument | `string` | | `null` | | The password used to open a password-protected PDF. Leave empty if the file is not protected. |
| `OutputFileName` | Output File Path | InArgument | `string` | | | | Full path where the extracted-page PDF will be saved. If not specified, a default path is generated automatically. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFile` | Output File | `ILocalResource` | The resulting PDF containing only the extracted pages, as a local resource. |

## Notes

- `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`). Provide exactly one.
- The `Range` format is `"start-end"` (e.g., `"2-4"` extracts pages 2, 3, and 4). An invalid range format throws a `RangeFormatException`.
- Page numbers are 1-based. Providing a range that exceeds the document's page count is a validation error at runtime.

## XAML Example

```xml
<pdf:ExtractPDFPageRange
    DisplayName="Extract PDF Page Range"
    FileName="[inputFilePath]"
    Range="[&quot;2-4&quot;]"
    Password="[filePassword]"
    OutputFileName="[outputFilePath]"
    OutputFile="[extractedFile]" />
```

> Namespace prefix `pdf` maps to `clr-namespace:UiPath.PDF.Activities.PDF;assembly=UiPath.PDF.Activities`.
