# Create File

`UiPath.Core.Activities.CreateFile`

Creates a file in the specified location.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Create File | `InArgument` | `string` | Yes* | — | Path of the folder in which to create the file. Visible when `PathResource` has no value. |
| `PathResource` | Path Resource | `InArgument` | `IResource` | Yes* | — | Resource reference to the target folder. Visible when `Path` has no value. |
| `Name` | File name | `InArgument` | `string` | No | — | Name of the file to be created, including extension. |
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | `null` | When `true`, execution continues even if an error occurs. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Output` | Output File | `OutArgument` | `ILocalResource` | Reference to the newly created file. |

## Valid Configurations

The target folder supports two mutually exclusive input modes:

| Mode | Property | Description |
|------|----------|-------------|
| Local path | `Path` | String expression resolving to a local folder path. Default mode. |
| Resource | `PathResource` | `IResource` expression pointing to the target folder. |

## XAML Example

```xml
<ui:CreateFile
    DisplayName="Create File"
    Path="&quot;C:\output&quot;"
    Name="&quot;result.txt&quot;"
    Output="[createdFile]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- If a file with the same name already exists in the target folder, the activity raises an error.
- The `Output` argument returns an `ILocalResource` that can be passed directly to other file activities (e.g. Write Text File, Read Text File).
