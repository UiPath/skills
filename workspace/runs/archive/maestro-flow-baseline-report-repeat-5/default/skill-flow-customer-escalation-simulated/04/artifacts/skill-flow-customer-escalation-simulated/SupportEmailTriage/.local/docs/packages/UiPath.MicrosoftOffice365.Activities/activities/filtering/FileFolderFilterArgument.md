# FileFolderFilterArgument

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Files`

Filters OneDrive/SharePoint files and folders using the Microsoft Search API (KQL query syntax). Used by ForEachFileFolderConnections for search-based filtering across drives.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `FileFolderFilterLogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<SingleFileFolderFilterArgument>` | Zero or more filter conditions to apply. |

## SingleFileFolderFilterArgument

Each filter element specifies a field, operator, and value.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `FileFolderFilterField` | The field to filter on. |
| `Operator` | `FileFolderFilterOperator` | The comparison operator. |
| `Value` | `InArgument<String>` | String value for string-based filters. Ignored for date filters. |
| `DateFilter` | `DateFilterOption` | Predefined date range for date filters (e.g., `Today`, `LastWeek`, `LastMonth`). |
| `DateEqualsFilter` | `InArgument<DateTime>` | Exact date for equality comparison. |
| `SelectedDateFilter` | `DateTime` | Custom date for NewerThanCustom/OlderThanCustom operators. |

## FileFolderFilterField Enum

| Value | Description |
|-------|-------------|
| `FileName` | Filter by file name. |
| `FileExtension` | Filter by file extension. |
| `CreatedBy` | Filter by creator. |
| `CreatedDate` | Filter by creation date. |
| `LastModifiedBy` | Filter by last modifier. |
| `LastModifiedDate` | Filter by last modified date. |
| `SharedWithUser` | Filter by users the file is shared with. |

## FileFolderFilterOperator Enum

| Value | Applicable To | Description |
|-------|--------------|-------------|
| `Equals` | String, Date | Exact match. |
| `Contains` | String | Contains the value. |
| `NotContains` | String | Does not contain the value. |
| `StartsWith` | String | Starts with the value. |
| `NewerThan` | Date | Newer than a predefined date range. |
| `NewerThanCustom` | Date | Newer than a custom date. |
| `OlderThan` | Date | Older than a predefined date range. |
| `OlderThanCustom` | Date | Older than a custom date. |

## Cross-References

- Filters results of type [O365DriveRemoteItem](../types/O365DriveRemoteItem.md)
- Used alongside [DriveItemArgument](../components/DriveItemArgument.md) for file/folder selection
- For OData-based filtering, see [FileFilterArgument](FileFilterArgument.md)
