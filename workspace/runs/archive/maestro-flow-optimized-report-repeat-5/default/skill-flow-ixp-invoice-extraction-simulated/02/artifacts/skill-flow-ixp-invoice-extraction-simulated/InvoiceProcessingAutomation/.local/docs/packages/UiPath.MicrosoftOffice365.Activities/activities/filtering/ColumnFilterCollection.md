# ColumnFilterCollection

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Sharepoint.Filters`
**Inherits:** `BaseFilterCollection<ColumnFilter, LogicalOperator>`

Filters SharePoint list items by column values using typed operators (string, date, boolean, number). The column to filter on is specified by a `Office365SharepointListColumnSlim` object (selected via the designer). Used by activities like GetListItemsConnections and ForEachListItemConnections.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `LogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<ColumnFilter>` | Zero or more filter conditions to apply. |

## ColumnFilter

Each filter element specifies a column, typed operators, and typed values. The applicable operator and value properties depend on the column type.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `Office365SharepointListColumnSlim` | The column to filter on (contains Name, DisplayName, Type). |
| `StringOperator` | `StringFilterOperator` | Operator for string columns (e.g., `Equals`, `StartsWith`, `Contains`). |
| `BooleanOperator` | `BooleanFilterOperator` | Operator for boolean columns (e.g., `Equals`). |
| `DateOperator` | `DateFilterOperator` | Operator for date columns. |
| `NumberOperator` | `NumberFilterOperator` | Operator for number columns. |
| `StringValue` | `InArgument<String>` | Value for string column filters. |
| `BooleanValue` | `InArgument<Boolean>` | Value for boolean column filters. |
| `DateValue` | `InArgument<DateTime?>` | Value for date column filters. |
| `NumberValue` | `InArgument<Decimal?>` | Value for number column filters. |

## Cross-References

- Filters results of type [Office365SharepointListItem](../types/Office365SharepointListItem.md)
- Used alongside [ListArgument](../components/ListArgument.md) for list selection
- For string-based column name filtering (without designer column selection), see [ColumnByNameFilterCollection](ColumnByNameFilterCollection.md)
- Lists are of type [Office365SharepointList](../types/Office365SharepointList.md)
