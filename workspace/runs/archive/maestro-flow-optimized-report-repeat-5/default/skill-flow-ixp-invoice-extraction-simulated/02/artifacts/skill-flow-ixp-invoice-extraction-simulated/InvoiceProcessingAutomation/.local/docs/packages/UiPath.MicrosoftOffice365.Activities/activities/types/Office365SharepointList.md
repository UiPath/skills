# Office365SharepointList

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Models`

Represents a SharePoint list. Returned by GetListInfo and used in SharePoint list activities.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `Id` | `String` | The unique identifier of the list. |
| `Name` | `String` | The API-facing name of the list. |
| `DisplayName` | `String` | The displayable title of the list. |
| `Description` | `String` | The description of the list. |
| `WebUrl` | `String` | The URL of the list. |
| `Columns` | `Office365SharepointListColumn[]` | The column definitions for the list (non-hidden columns only). |
| `CreatedDateTime` | `DateTime` | When the list was created. |
| `LastModifiedDateTime` | `DateTime` | When the list was last modified. |
| `ContentTypesEnabled` | `Boolean` | `true` if content types are enabled for the list. |
| `IsHidden` | `Boolean` | `true` if the list is hidden. |
| `Template` | `String` | The base list template used to create the list. |

## Office365SharepointListColumn

Defines a column in a SharePoint list.

| Property | Type | Description |
|----------|------|-------------|
| `Id` | `String` | Unique identifier for the column. |
| `Description` | `String` | Description of the column. |
| `EnforceUniqueValues` | `Boolean` | `true` if values must be unique. |
| `Indexed` | `Boolean` | `true` if the column is indexed for sorting/searching. |
| `Required` | `Boolean` | `true` if the column value is required. |

> The column also inherits properties from `Office365SharepointListColumnSlim` including `Name`, `DisplayName`, `Type`, and `LookupListId`.

## Cross-References

- Returned by GetListInfo
- List selection uses [ListArgument](../components/ListArgument.md)
- Contains items of type [Office365SharepointListItem](Office365SharepointListItem.md)
- Filtered by [ColumnFilterCollection](../filtering/ColumnFilterCollection.md) and [ColumnByNameFilterCollection](../filtering/ColumnByNameFilterCollection.md)
