# Excel workbook activities

Read this file when: building workflows that read, write, or filter Excel data.

## Which Excel activities to use

UiPath has TWO sets of Excel activities. **Always use the classic workbook set** for programmatic XAML generation.

| Set | Activities | Properties | Needs scope? | Use for XAML generation? |
|-----|-----------|------------|-------------|------------------------|
| **Classic workbook** | `ui:ReadRange`, `ui:WriteRange` | Simple strings (`WorkbookPath`, `SheetName`, `Range`) | No | **YES — use these** |
| Business (X-suffix) | `ueab:ReadRangeX`, `ueab:WriteRangeX` | Complex types (`IReadRangeRef`, `IReadWriteRangeRef`) | Yes (ExcelProcessScopeX > ExcelApplicationCard) | **NO — types cannot be constructed in XAML** |

The Business activities (`ReadRangeX`, `WriteRangeX`, `ExcelApplicationCard`, `ExcelProcessScopeX`) are designed for Studio's visual editor. Their `Range`/`Destination` properties require `IReadRangeRef`/`IReadWriteRangeRef` objects that cannot be created from strings. Attempting to pass a string causes:
```
BC30512: Option Strict On disallows implicit conversions from 'String' to 'IReadRangeRef'
```

## Classic workbook activity reference

### ReadRange

Class: `UiPath.Excel.Activities.ReadRange` (already installed — part of `UiPath.Excel.Activities`)

```xml
<ui:ReadRange WorkbookPath="[&quot;path/to/file.xlsx&quot;]"
              SheetName="[&quot;Sheet1&quot;]"
              AddHeaders="True"
              sap2010:WorkflowViewState.IdRef="ReadRange_1">
  <ui:ReadRange.DataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[myDataTable]</OutArgument>
  </ui:ReadRange.DataTable>
</ui:ReadRange>
```

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| `WorkbookPath` | String | Yes | Relative or absolute path to .xlsx |
| `SheetName` | String | Yes | Sheet name to read from |
| `Range` | String | No | e.g. `"A1:C10"`. Omit to read entire sheet |
| `AddHeaders` | Boolean | No | `True` = first row becomes column names |
| `DataTable` | OutArgument(DataTable) | Yes | Output — use child element syntax |

### WriteRange

Class: `UiPath.Excel.Activities.WriteRange` (already installed — part of `UiPath.Excel.Activities`)

```xml
<ui:WriteRange WorkbookPath="[&quot;path/to/file.xlsx&quot;]"
               SheetName="[&quot;HighEarners&quot;]"
               AddHeaders="True"
               sap2010:WorkflowViewState.IdRef="WriteRange_1">
  <ui:WriteRange.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[filteredData]</InArgument>
  </ui:WriteRange.DataTable>
</ui:WriteRange>
```

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| `WorkbookPath` | String | Yes | Same file or different file |
| `SheetName` | String | Yes | Creates sheet if it doesn't exist |
| `StartingCell` | String | No | e.g. `"A1"`. Default is A1 |
| `AddHeaders` | Boolean | No | `True` = write column names as first row |
| `DataTable` | InArgument(DataTable) | Yes | Input — use child element syntax |

## Required xmlns and imports

Add to the root `<Activity>` element:
```xml
xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

Add to `NamespacesForImplementation` (if not already present):
```xml
<x:String>System.Data</x:String>
```

## Filtering DataTable rows

Excel columns are often typed as `String` even for numbers. Use LINQ with explicit conversion:

**VB (recommended):**
```xml
<InArgument x:TypeArguments="sd:DataTable">[allData.AsEnumerable().Where(Function(row) CDbl(row(&quot;Salary&quot;).ToString()) &gt; 60000).CopyToDataTable()]</InArgument>
```

**Do NOT use** `DataTable.Select("[Salary] > 60000")` — it does string comparison on string-typed columns (`"4200" < "800"`).

## Complete example: Read, Filter, Write

```xml
<!-- Variables -->
<Sequence.Variables>
  <Variable x:TypeArguments="sd:DataTable" Name="allData" />
  <Variable x:TypeArguments="sd:DataTable" Name="filteredData" />
</Sequence.Variables>

<!-- Read -->
<ui:ReadRange WorkbookPath="[&quot;Data/Employees.xlsx&quot;]" SheetName="[&quot;Sheet1&quot;]" AddHeaders="True"
              sap2010:WorkflowViewState.IdRef="ReadRange_1">
  <ui:ReadRange.DataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[allData]</OutArgument>
  </ui:ReadRange.DataTable>
</ui:ReadRange>

<!-- Filter -->
<Assign sap2010:WorkflowViewState.IdRef="Assign_1">
  <Assign.To>
    <OutArgument x:TypeArguments="sd:DataTable">[filteredData]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="sd:DataTable">[allData.AsEnumerable().Where(Function(row) CDbl(row(&quot;Salary&quot;).ToString()) &gt; 60000).CopyToDataTable()]</InArgument>
  </Assign.Value>
</Assign>

<!-- Write to new sheet -->
<ui:WriteRange WorkbookPath="[&quot;Data/Employees.xlsx&quot;]" SheetName="[&quot;HighEarners&quot;]" AddHeaders="True"
               sap2010:WorkflowViewState.IdRef="WriteRange_1">
  <ui:WriteRange.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[filteredData]</InArgument>
  </ui:WriteRange.DataTable>
</ui:WriteRange>

<!-- Log count -->
<ui:LogMessage Message="[&quot;Filtered &quot; &amp; filteredData.Rows.Count.ToString() &amp; &quot; rows&quot;]"
               sap2010:WorkflowViewState.IdRef="LogMessage_1" />
```
