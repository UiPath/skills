# Get PDF Page Count

`UiPath.PDF.Activities.PDF.GetPDFPageCount`

Reads a PDF document and returns the total number of pages it contains. Optionally accepts a password for password-protected files.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | InArgument | `string` | Yes* | | | The local file path of the PDF document. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | InArgument | `IResource` | Yes* | | | The file resource to read from. Mutually exclusive with `FileName`. |
| `Password` | Password | InArgument | `string` | | `null` | | The password used to open a password-protected PDF. Leave empty if the file is not protected. |

> *\*Exactly one of `FileName` or `ResourceFile` is required (`[OverloadGroup]`).*

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `PageCount` | PageCount | `int` | The total number of pages found in the supplied PDF document. |

## Notes

- `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`). Provide exactly one.
- `FileName` accepts a local file system path (e.g., `"C:\docs\report.pdf"`).
- `ResourceFile` accepts an `IResource` object, enabling use with storage buckets and other resource providers.

## XAML Example

```xml
<pdf:GetPDFPageCount
    DisplayName="Get PDF Page Count"
    FileName="[inputFilePath]"
    Password="[filePassword]"
    PageCount="[pageCount]" />
```

> Namespace prefix `pdf` maps to `clr-namespace:UiPath.PDF.Activities.PDF;assembly=UiPath.PDF.Activities`.
