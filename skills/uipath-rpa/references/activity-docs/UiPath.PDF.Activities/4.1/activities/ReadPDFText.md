# Read PDF Text

`UiPath.PDF.Activities.ReadPDFText`

Read and return all text content from a PDF file as a single string. Supports reading a specific page range and optionally preserving the original text formatting.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | `InArgument` | `string` | Yes* | | | The local file path of the PDF to read. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | `InArgument` | `IResource` | Yes* | | | A file resource representing the PDF to read. Mutually exclusive with `FileName`. |
| `Password` | Password | `InArgument` | `string` | | `null` | | The password used to open a password-protected PDF. Leave empty if the file is not encrypted. |

> *\*Exactly one of `FileName` or `ResourceFile` is required (`[OverloadGroup]`).*
| `Range` | Range | `InArgument` | `string` | | `"All"` | | The page range to read (e.g. `"2-4"`, `"1,3,5"`, or `"All"`). Defaults to all pages. |
| `PreserveFormatting` | PreserveFormatting | `InArgument` | `bool` | | `false` | | When `true`, whitespace and layout formatting from the PDF are preserved in the extracted text. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Text | `string` | The extracted text content from the specified page range. |

## XAML Example

```xml
<!-- xmlns:ui="http://schemas.uipath.com/workflow/activities" -->

<ui:ReadPDFText
    DisplayName="Read PDF Text"
    FileName="[pdfFilePath]"
    Range="[pageRange]"
    PreserveFormatting="[preserveFormatting]"
    Text="[outputText]" />
```

## Notes

- `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`). Supply exactly one. In the designer, a context menu lets you switch between **Use File Path** and **Use a File Resource**.
- The `Range` property accepts formats such as `"All"`, `"1"`, `"2-5"`, or comma-separated page numbers. An invalid format raises an exception at runtime.
- `PreserveFormatting` defaults to `false`; when `false`, text is extracted without spatial layout information.
- For scanned PDFs where native text extraction returns empty results, use **Read PDF With OCR** instead.
