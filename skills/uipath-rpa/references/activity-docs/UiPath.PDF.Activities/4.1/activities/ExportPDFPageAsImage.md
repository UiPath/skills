# Export PDF Page As Image

`UiPath.PDF.Activities.PDF.ExportPDFPageAsImage`

Exports a single page from a PDF file as an image. The page is rendered at the specified DPI and saved to the output path. Supported image formats are PNG, JPEG, BMP, GIF, and TIFF — the format is determined automatically from the output file extension.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | `InArgument` | `string` | Yes* | | | Local path to the source PDF file. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | `InArgument` | `IResource` | Yes* | | | A file resource handle pointing to the source PDF file. Mutually exclusive with `FileName`. |
| `PageNumber` | Page Number | `InArgument` | `int` | Yes | | | The 1-based page number to export as an image. Must be ≥ 1 and not exceed the total page count. |
| `OutputFileName` | Output File Path | `InArgument` | `string` | Yes | | | Full path of the output image file. The file extension determines the image format (`.png`, `.jpg`/`.jpeg`, `.bmp`, `.gif`, `.tif`/`.tiff`). |
| `Password` | Password | `InArgument` | `string` | | | | Password for password-protected PDF files. Leave empty for unprotected files. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ImageDpi` | Image DPI | `ImageDpi` | `Medium` | The DPI (dots per inch) at which the page is rendered. Higher DPI produces sharper images at the cost of larger file size. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFile` | Output File | `ILocalResource` | The exported image file as a local resource. |

### Enum Reference

**`ImageDpi`**: `Low` (96 dpi), `Medium` (150 dpi), `High` (270 dpi)

## XAML Example

```xml
<pdf:ExportPDFPageAsImage
    DisplayName="Export PDF Page As Image"
    FileName="[&quot;C:\documents\report.pdf&quot;]"
    PageNumber="[1]"
    OutputFileName="[&quot;C:\output\page1.png&quot;]"
    ImageDpi="High"
    OutputFile="[outputImage]" />
```

> The `pdf` namespace prefix maps to `clr-namespace:UiPath.PDF.Activities.PDF;assembly=UiPath.PDF.Activities`.

## Notes

- `FileName` and `ResourceFile` are decorated with `[OverloadGroup]` — exactly one must be provided. Use `FileName` for plain local paths; use `ResourceFile` when working with storage buckets or file resources.
- `PageNumber` is 1-based. Providing a value less than 1, or greater than the document's page count, raises an `ArgumentException` at runtime.
- The output image format is inferred from the `OutputFileName` extension. Supported extensions: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.tif`, `.tiff`.
- `ImageDpi` is a plain enum property set directly as an XML attribute — it is not wrapped in a VB expression.
