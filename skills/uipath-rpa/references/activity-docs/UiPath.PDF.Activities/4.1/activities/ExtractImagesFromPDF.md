# Extract Images From PDF

`UiPath.PDF.Activities.PDF.ExtractImagesFromPDF`

Extract all images embedded in a PDF file and save them to a local folder. The activity returns the list of saved image files as `ILocalResource` references.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | `InArgument` | `string` | Yes* | | | The local file path of the PDF to extract images from. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | `InArgument` | `IResource` | Yes* | | | A file resource representing the PDF to extract images from. Mutually exclusive with `FileName`. |
| `Password` | Password | `InArgument` | `string` | | `null` | | The password used to open a password-protected PDF. Leave empty if the file is not encrypted. |
| `OutputFolderName` | Output Folder | `InArgument` | `string` | | | | The folder path where the extracted images are saved. If omitted, images are saved to the current working directory. |

> *\*Exactly one of `FileName` or `ResourceFile` is required (`[OverloadGroup]`).*

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ImageExtension` | Image Type | `ImageExtension` | `PNG` | The image format used when saving the extracted images. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFiles` | Output Files | `IEnumerable<ILocalResource>` | A collection of local resource references pointing to each extracted image file. |

### Enum Reference

**`ImageExtension`**: `PNG`, `JPEG`, `TIFF`, `BMP`, `GIF`

## XAML Example

```xml
<!-- xmlns:upap="clr-namespace:UiPath.PDF.Activities.PDF;assembly=UiPath.PDF.Activities" -->

<upap:ExtractImagesFromPDF
    DisplayName="Extract Images From PDF"
    FileName="[pdfFilePath]"
    ImageExtension="JPEG"
    OutputFolderName="[outputFolder]"
    OutputFiles="[extractedImages]" />
```

## Notes

- `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`). Supply exactly one. In the designer, a context menu lets you switch between **Use File Path** and **Use a File Resource**.
- Output images are named using the pattern `{pdfName}.{pageNumber}.{imageNumber}.{ext}` (e.g. `report.1.1.png`). Mask images follow the pattern `{pdfName}.{pageNumber}.mask-{maskNumber}.{ext}`.
- The `OutputFolderName` path must already exist; the activity does not create directories.
- `ImageExtension` is a plain enum property set as a direct XML attribute in XAML, not wrapped in an expression.
