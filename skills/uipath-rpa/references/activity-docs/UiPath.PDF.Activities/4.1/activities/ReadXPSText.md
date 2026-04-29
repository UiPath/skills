# Read XPS Text

`UiPath.XPS.Activities.ReadXPSText`

Read and return all text content from an XPS (XML Paper Specification) file as a single string. Supports reading a specific page range.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileName` | File (local path) | `InArgument` | `string` | Yes* | | | The local file path of the XPS file to read. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | `InArgument` | `IResource` | Yes* | | | A file resource representing the XPS file to read. Mutually exclusive with `FileName`. |
| `Password` | Password | `InArgument` | `string` | | `null` | | The password used to open a password-protected XPS file. Leave empty if the file is not encrypted. |

> *\*Exactly one of `FileName` or `ResourceFile` is required (`[OverloadGroup]`).*
| `Range` | Range | `InArgument` | `string` | | `"All"` | | The page range to read (e.g. `"2-4"`, `"1,3,5"`, or `"All"`). Defaults to all pages. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Text | `string` | The extracted text content from the specified page range. |

## XAML Example

```xml
<!-- xmlns:ui="http://schemas.uipath.com/workflow/activities" -->

<ui:ReadXPSText
    DisplayName="Read XPS Text"
    FileName="[xpsFilePath]"
    Range="[pageRange]"
    Text="[outputText]" />
```

## Notes

- `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`). Supply exactly one. In the designer, a context menu lets you switch between **Use File Path** and **Use a File Resource**.
- The `Range` property accepts formats such as `"All"`, `"1"`, `"2-5"`, or comma-separated page numbers. An invalid format raises an exception at runtime.
- This activity is only available on Windows (`#if !NETPORTABLE_UIPATH`). It uses the Windows-native XPS reader and cannot be used in cross-platform workflows.
- Unlike `ReadPDFText`, there is no `PreserveFormatting` option for XPS files.
