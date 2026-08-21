# For Each Folder in Folder

`UiPath.Core.Activities.ForEachFolderX`

Iterates through folders in a parent folder and runs the body once for each folder.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Folder` | In folder | `InArgument` | `string` | Yes | - | Parent folder whose subfolders are enumerated. |
| `FilterByName` | Filter by name | `InArgument` | `string` | No | `null` | Regular expression used to match folder names. Empty values match all folders. |
| `IncludeSubFolders` | Include subfolders | Property | `bool` | No | `false` | When `true`, searches recursively below the parent folder. |
| `SkipFoldersWithoutPermission` | Skip folders where access is denied | Property | `bool` | No | `false` | When `true`, ignores inaccessible subfolders below the root folder. |
| `OrderBy` | Order by | Property | `ForEachFolderOrderByOptions` | No | `NameAscFirst` | Sort order for the folders before iteration. |

### Body

| Name | Type | Description |
|------|------|-------------|
| `Body` | `ActivityAction<DirectoryInfo, int>` | Activities to execute for each folder. The arguments are `CurrentFolder` and `CurrentIndex`. |

## Enum Reference

**`ForEachFolderOrderByOptions`**

| Value | Description |
|-------|-------------|
| `NameAscFirst` | Sort by name ascending. |
| `NameDescFirst` | Sort by name descending. |
| `LastUpdatedDateNewFirst` | Newest last update date first. |
| `LastUpdatedDateOldFirst` | Oldest last update date first. |
| `SizeSmallestFirst` | Smallest folder first. |
| `SizeLargestFirst` | Largest folder first. |

## XAML Example

```xml
<ui:ForEachFolderX
    DisplayName="For Each Folder in Folder"
    Folder="C:\input"
    FilterByName="^2026"
    IncludeSubFolders="True"
    OrderBy="NameAscFirst" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- `CurrentIndex` is one-based. The first folder is passed with index `1`.
- `FilterByName` is interpreted as a regular expression, not as a wildcard pattern.
- If the root folder is inaccessible, the activity throws even when `SkipFoldersWithoutPermission` is `true`.
