# FileFilterArgument

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Files.Filters`

Filters OneDrive/SharePoint files using the Microsoft Graph API OData filter syntax. Used by activities like GetFileListConnections and ForEachFileFolderConnections (when using the simple filter mode).

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `FileFilterLogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<SingleFileFilterArgument>` | Zero or more filter conditions to apply. |

## SingleFileFilterArgument

Each filter element specifies a field, operator, and value.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `FileFilterField` | The field to filter on. |
| `StringOperator` | `FileStringFilterOperator` | Operator for string fields (e.g., `Equals`, `StartsWith`, `Contains`). |
| `FileExtensionStringOperator` | `FileExtensionStringFilterOperator` | Operator for file extension fields (`Equals`, `NotEqual`). |
| `DateOperator` | `FileDateFilterOperator` | Operator for date fields. |
| `IntOperator` | `FileIntFilterOperator` | Operator for integer fields (e.g., size). |
| `InStringValue` | `InArgument<String>` | String value for the filter. |
| `InFileExtensionStringValue` | `InArgument<String>` | String value for file extension filter. |
| `DateValue` | `InArgument<DateTime>` | Date value for date filters. |
| `IntValue` | `InArgument<Int32>` | Integer value for numeric filters. |

## FileFilterField Enum

| Value | Description |
|-------|-------------|
| `FileExtension` | Filter by file extension. |
| `FileName` | Filter by file name. |
| `CreatedBy` | Filter by creator. |
| `CreationDate` | Filter by creation date. |
| `LastModifiedBy` | Filter by last modifier. |
| `LastModifiedDate` | Filter by last modified date. |
| `SharedWithUser` | Filter by shared-with user. |
| `Size` | Filter by file size. |

## XAML Examples

### Filter by file extension

```xml
<!--
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umaffi="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Filters;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umaf:GetFileListConnections ...>
  <umaf:GetFileListConnections.Filter>
    <umaffi:FileFilterArgument LogicalOperator="And">
      <umaffi:FileFilterArgument.Filters>
        <scg:List x:TypeArguments="umaffi:SingleFileFilterArgument">
          <umaffi:SingleFileFilterArgument
              Criteria="FileExtension"
              FileExtensionStringOperator="Equals"
              InFileExtensionStringValue=".pdf" />
        </scg:List>
      </umaffi:FileFilterArgument.Filters>
    </umaffi:FileFilterArgument>
  </umaf:GetFileListConnections.Filter>
</umaf:GetFileListConnections>
```

### Filter by name + modified date (combined, And logic)

```xml
<umaffi:FileFilterArgument LogicalOperator="And">
  <umaffi:FileFilterArgument.Filters>
    <scg:List x:TypeArguments="umaffi:SingleFileFilterArgument">
      <umaffi:SingleFileFilterArgument
          Criteria="FileName"
          StringOperator="StartsWith"
          InStringValue="Invoice" />
      <umaffi:SingleFileFilterArgument
          Criteria="LastModifiedDate"
          DateOperator="IsGreaterThan"
          DateValue="[cutoffDate]" />
    </scg:List>
  </umaffi:FileFilterArgument.Filters>
</umaffi:FileFilterArgument>
```

## Cross-References

- Filters results of type [O365DriveRemoteItem](../types/O365DriveRemoteItem.md)
- Used alongside [DriveItemArgument](../components/DriveItemArgument.md) for file selection
- For search-based filtering (KQL), see [FileFolderFilterArgument](FileFolderFilterArgument.md)
