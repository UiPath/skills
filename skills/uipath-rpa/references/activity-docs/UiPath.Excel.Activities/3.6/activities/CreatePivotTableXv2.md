# Create Pivot Table

`UiPath.Excel.Activities.Business.CreatePivotTableXv2`

Creates a new pivot table from a specified data range and places it at a destination range. This is a container activity that holds child `PivotTableFieldX` activities to define the pivot table's rows, columns, filters, and values.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Table range | InArgument | `IReadRangeRef` | Yes | | Table or range to analyze with a pivot table. |
| `TableName` | New table name | InArgument | `string` | Yes | | Name of the new pivot table. |
| `DestinationRange` | Destination range | InArgument | `IReadWriteRangeRef` | Yes | | Where to place the new pivot table. |
| `LayoutRowType` | Layout | Property | `PivotTableLayoutRowType` | No | `Compact` | Enhance the pivot table layout and format. The compact form optimizes for readability, while tabular and outline forms include field headers. |
| `ValuesMode` | Values added as | Property | `PivotTableValuesMode` | No | `Columns` | Select how to add the values in the pivot table, either as columns (the default option) or rows. |

### Designer Controls (Not Mapped to XAML)
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `AddPivotField` | Add Pivot Table Field | Action Button | Inserts a new `PivotTableFieldX` child activity into the body. |

## Child Activity: PivotTableFieldX

`UiPath.Excel.Activities.Business.PivotTableFieldX`

Each child activity defines a single pivot table field. Add one per field using the **Add Pivot Table Field** button. At least one is required.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FieldName` | Field | InArgument | `string` | Yes | | The name of the source column to use as a pivot field. |
| `Type` | Is a | Property | `PivotTableFieldType` | Yes | `Row` | The role of the field in the pivot table. |
| `Function` | Function | Property | `PivotTableFunction` | No | `Sum` | The aggregation function to apply. Only visible when `Type` is `Value`. |

#### `PivotTableFieldType`
| Value | Display Name |
|-------|-------------|
| `Row` | Row |
| `Column` | Column |
| `Filter` | Filter |
| `Value` | Value |

#### `PivotTableFunction`
| Value | Display Name |
|-------|-------------|
| `Sum` | Sum |
| `Count` | Count |
| `Average` | Average |
| `Max` | Max |
| `Min` | Min |
| `Product` | Product |
| `CountNumbers` | CountNumbers |
| `StdDev` | StdDev |
| `StdDevp` | StdDevp |
| `Var` | Var |
| `Varp` | Varp |

## Enum Reference

#### `PivotTableLayoutRowType`
| Value | Display Name |
|-------|-------------|
| `Compact` | Compact |
| `Tabular` | Tabular |
| `Outline` | Outline |

#### `PivotTableValuesMode`
| Value | Display Name |
|-------|-------------|
| `Columns` | Columns |
| `Rows` | Rows |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:CreatePivotTableXv2
    Range="[sourceRange]"
    TableName="PivotTable1"
    DestinationRange="[destRange]"
    LayoutRowType="Compact"
    ValuesMode="Columns"
    DisplayName="Create Pivot Table">
    <excel:CreatePivotTableXv2.Body>
      <ActivityAction x:TypeArguments="excel:PivotTableDescriptor">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="excel:PivotTableDescriptor" Name="PivotTableDescriptor" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Do">
          <!-- PivotTableFieldX child activities here -->
        </Sequence>
      </ActivityAction>
    </excel:CreatePivotTableXv2.Body>
  </excel:CreatePivotTableXv2>
</excel:ExcelApplicationCard>
```

## Notes
- The source range and destination range must be in the same workbook. Using different workbooks throws an error.
- The `HasHeaders` property is always `True` and not visible in the designer.
- When the source range represents an entire sheet, the activity clips it to the used range before creating the pivot table.
- At least one `PivotTableFieldX` child activity is required; otherwise a runtime error occurs.
- Filter fields are added in reverse order so they appear top-to-bottom in the same order as defined in the activity.
