# Collection to DataTable

`UiPath.Core.Activities.CollectionToDataTable`1``

Converts a Collection to a DataTable.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The collection to convert to a DataTable. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `DataTable` | DataTable | `OutArgument` | `DataTable` | The resulting DataTable. For primitive and built-in types (string, int, DateTime, etc.) the table has a single column named after the type. For complex types, each public instance property becomes a column. |

## XAML Example

```xml
<ui:CollectionToDataTable x:TypeArguments="x:String"
    DisplayName="Collection to DataTable"
    Collection="[myStringList]"
    DataTable="[resultTable]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

**Primitive / built-in types** (`string`, `int`, `bool`, `decimal`, `DateTime`, `TimeSpan`, `DateTimeOffset`, `Guid`, enums) produce a single-column table whose column name matches the type name.

**Complex types** produce one column per public instance property. If two properties share the same name (possible when interfaces are involved), the second column is disambiguated with the pattern `PropertyName_PropertyType`.

The DataTable name is set to the type name of `T`. Null collection items are written as `DBNull` in the row.
