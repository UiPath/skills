# Get File Info

`UiPath.Core.Activities.GetFileInfoX`

Creates a `FileInfo` object for a specified file path.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | Path | `InArgument` | `string` | Yes | - | Full path of the file. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Output` | Output to | `OutArgument` | `FileInfo` | The `System.IO.FileInfo` object created for the path. |

## XAML Example

```xml
<ui:GetFileInfoX
    DisplayName="Get File Info"
    FilePath="C:\reports\summary.xlsx"
    Output="[fileInfo]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- Creating `FileInfo` does not require the file to exist; inspect the returned object's `Exists` property when needed.
