# File Change Trigger

`UiPath.Core.Activities.FileChangeTriggerV3`

Triggers when a file system change matching the configured path, filter, and change type is detected.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | `InArgument` | `string` | Yes | - | File or folder path to monitor. Environment variables are expanded at runtime. |
| `FileNameFilter` | File Name Filter | `InArgument` | `string` | No | Empty | File name filter passed to the file watcher. If `Path` is a file and this is empty, the file name is inferred from `Path`. |

### Event

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `NotifyFilters` | NotifyFilters | `InArgument` | `NotifyFilters` | Yes | `FileName` | File system attributes that raise events. |
| `ChangeType` | ChangeType | `InArgument` | `WatcherChangeTypes` | Yes | `Changed` | Type of file system change to monitor. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `IncludeSubdirectories` | IncludeSubdirectories | `InArgument` | `bool` | `false` | When `true`, monitors subfolders recursively. |

### Output

| Name | Type | Description |
|------|------|-------------|
| `FileChangeInfo` | `FileChangeInfo` | Trigger argument containing `ChangeType`, `FullPath`, `Name`, `OldFullPath`, and `OldName`. |

## XAML Example

```xml
<ui:FileChangeTriggerV3
    DisplayName="File Change Trigger"
    Path="C:\input"
    FileNameFilter="*.csv"
    NotifyFilters="FileName"
    ChangeType="Created"
    IncludeSubdirectories="False" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- `NotifyFilters` and `ChangeType` cannot be zero; validation fails for empty flag values.
- Use this activity inside a trigger scope or a trigger-enabled workflow surface.
