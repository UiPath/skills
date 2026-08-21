# For Each File in Folder

`UiPath.Core.Activities.ForEachFileX`

Iterates through files in a folder and runs the body once for each file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Folder` | In folder | `InArgument` | `string` | Yes | - | Folder whose files are enumerated. |
| `Filter` | Filter | `InArgument` | `string` | No | `null` | Wildcard file name filter. Empty values are treated as `*`. |
| `IncludeSubDirectories` | IncludeSubdirectories | Property | `bool` | No | `false` | When `true`, also searches subfolders. |
| `SkipFolderWithoutPermission` | Skip folders where access is denied | Property | `bool` | No | `false` | When `true`, ignores inaccessible subfolders below the root folder. |
| `OrderBy` | Order | Property | `ForEachFileOrderByOptions` | No | `NameAscFirst` | Sort order for the files before iteration. |

### Body

| Name | Type | Description |
|------|------|-------------|
| `Body` | `ActivityAction<FileInfo, int>` | Activities to execute for each file. The arguments are `CurrentFile` and `CurrentIndex`. |

## Enum Reference

**`ForEachFileOrderByOptions`**

| Value | Description |
|-------|-------------|
| `NameAscFirst` | Sort by name ascending. |
| `NameDescFirst` | Sort by name descending. |
| `CreationDateNewFirst` | Newest creation date first. |
| `CreationDateOldFirst` | Oldest creation date first. |
| `LastUpdatedDateNewFirst` | Newest last update date first. |
| `LastUpdatedDateOldFirst` | Oldest last update date first. |
| `SizeSmallestFirst` | Smallest file first. |
| `SizeLargestFirst` | Largest file first. |

## XAML Example

```xml
<ui:ForEachFileX
    DisplayName="For Each File in Folder"
    Folder="C:\input"
    Filter="*.xlsx"
    IncludeSubDirectories="False"
    OrderBy="NameAscFirst" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- `CurrentIndex` is one-based. The first file is passed with index `1`.
- If the root folder is inaccessible, the activity throws even when `SkipFolderWithoutPermission` is `true`.
