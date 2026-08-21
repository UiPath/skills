# ColumnByNameFilterCollection

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Sharepoint.Filters`
**Inherits:** `BaseFilterCollection<ColumnByNameFilter, LogicalOperator>`

Filters SharePoint list items by column name using a string-based approach. Unlike [ColumnFilterCollection](ColumnFilterCollection.md), this does not require a designer-selected column object -- the column is specified by its name as a plain string, making it suitable for AI-generated XAML.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `LogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<ColumnByNameFilter>` | Zero or more filter conditions to apply. |

## ColumnByNameFilter

Each filter element specifies a column name, operator, and value.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `String` | The SharePoint column name to filter on. |
| `Operator` | `DynamicFilterOperator` | The comparison operator (handles all column types dynamically). |
| `Value` | `InArgument` | The filter value to compare against the specified column. |

## DynamicFilterOperator Enum

Covers operators for all column types in a single enum:

| Value | Description |
|-------|-------------|
| `Equals` | Exact match. |
| `NotEqual` | Not equal. |
| `GreaterThan` | Greater than (number/date). |
| `GreaterThanOrEqual` | Greater than or equal (number/date). |
| `LessThanOrEqual` | Less than or equal (number/date). |
| `LessThan` | Less than (number/date). |
| `NewerThan` | Newer than (date). |
| `OlderThan` | Older than (date). |

## Cross-References

- Filters results of type [Office365SharepointListItem](../types/Office365SharepointListItem.md)
- Used alongside [ListArgument](../components/ListArgument.md) for list selection
- For typed column filtering with designer-selected columns, see [ColumnFilterCollection](ColumnFilterCollection.md)
- Lists are of type [Office365SharepointList](../types/Office365SharepointList.md)
