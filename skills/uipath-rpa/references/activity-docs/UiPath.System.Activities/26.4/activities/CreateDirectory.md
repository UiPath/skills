# Create Folder

`UiPath.Core.Activities.CreateDirectory`

Creates a folder in the specified location.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Create Folder | `InArgument` | `string` | Yes | — | Full path of the folder to create, including the new folder name. |
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | — | When `true`, execution continues even if an error occurs. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Output` | Folder | `OutArgument` | `ILocalResource` | Reference to the newly created folder. |

## XAML Example

```xml
<ui:CreateDirectory
    DisplayName="Create Folder"
    Path="&quot;C:\output\reports\2024&quot;"
    Output="[newFolder]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- If the folder already exists, the activity does not raise an error and returns a reference to the existing folder.
- Intermediate directories in the path are created automatically if they do not exist.
- The `Output` argument returns an `ILocalResource` that can be passed to other activities.
