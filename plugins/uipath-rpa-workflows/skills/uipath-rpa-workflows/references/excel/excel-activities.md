# XAML Excel Activities

Excel activity patterns for `UiPath.Excel.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

## Package

`UiPath.Excel.Activities`

## Two Distinct Styles

| Style | Namespace prefix | Scope required | Activities |
|-------|-----------------|---------------|------------|
| **Modern** (`ueab:`) | `xmlns:ueab="clr-namespace:UiPath.Excel.Activities.Business;assembly=UiPath.Excel.Activities"` | Yes — `ExcelApplicationCard` | `ReadRangeX`, `WriteRangeX`, `ExcelForEachRowX`, etc. |
| **Classic** (`ui:`) | `xmlns:ui="http://schemas.uipath.com/workflow/activities"` | No — standalone | `ReadRange`, `WriteRange`, `AppendRange`, `ForEachRow` |

Both styles also need:
```xml
xmlns:ue="clr-namespace:UiPath.Excel;assembly=UiPath.Excel.Activities"
```
(for `IWorkbookQuickHandle`, `ISheetRef`, `CurrentRowQuickHandle`, `WorksheetQuickHandle`, `IChartRef` types)

Additional sub-namespaces (modern only, add when using the relevant activities):
```xml
xmlns:ueabf="clr-namespace:UiPath.Excel.Activities.Business.Filter;assembly=UiPath.Excel.Activities"
xmlns:ueabc="clr-namespace:UiPath.Excel.Activities.Business.ChartModifications;assembly=UiPath.Excel.Activities"
```

Namespace imports needed in `TextExpression.NamespacesForImplementation`:
- `UiPath.Excel`
- `UiPath.Excel.Activities.Business`

## Modern Style (ueab:)

### ExcelApplicationCard — Scope Container

All modern `ueab:` activities must be nested inside `ExcelApplicationCard`.

```xml
<ueab:ExcelApplicationCard
    Password="{x:Null}"
    ReadFormatting="{x:Null}"
    SensitivityLabel="{x:Null}"
    DisplayName="Use Excel file"
    ResizeWindow="None"
    SensitivityOperation="None"
    WorkbookPath="[InFilePath]">
  <ueab:ExcelApplicationCard.Body>
    <ActivityAction x:TypeArguments="ue:IWorkbookQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ue:IWorkbookQuickHandle" Name="Excel" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- nested ueab: activities here -->
      </Sequence>
    </ActivityAction>
  </ueab:ExcelApplicationCard.Body>
</ueab:ExcelApplicationCard>
```

The delegate argument name is `"Excel"` by convention. Sheet references use `Excel.Sheet("SheetName")`.
Optional: `CreateNewFile="False"` to prevent creating the file if it doesn't exist.

### ExcelProcessScopeX — Optional Outer Process Scope

An optional process-level container that can wrap one or more `ExcelApplicationCard` instances. All attributes default to `{x:Null}`:

```xml
<ueab:ExcelProcessScopeX
    DisplayAlerts="{x:Null}"
    ExistingProcessAction="{x:Null}"
    FileConflictResolution="{x:Null}"
    LaunchMethod="{x:Null}"
    LaunchTimeout="{x:Null}"
    MacroSettings="{x:Null}"
    ProcessMode="{x:Null}"
    ShowExcelWindow="{x:Null}"
    DisplayName="Excel process scope">
  <ueab:ExcelProcessScopeX.Body>
    <ActivityAction x:TypeArguments="ui:IExcelProcess">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ui:IExcelProcess" Name="ExcelProcessScopeTag" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- ExcelApplicationCard goes here -->
      </Sequence>
    </ActivityAction>
  </ueab:ExcelProcessScopeX.Body>
</ueab:ExcelProcessScopeX>
```

Note: the body type argument is `ui:IExcelProcess` (from `xmlns:ui`), not a `ue:` type.

### ReadRangeX

```xml
<ueab:ReadRangeX
    DisplayName="Read range from sheet"
    Range="[Excel.Sheet(&quot;Sheet1&quot;)]"
    SaveTo="[OutDT]" />
```

### WriteRangeX

```xml
<ueab:WriteRangeX
    Destination="[Excel.Sheet(&quot;Sheet1&quot;)]"
    DisplayName="Write DataTable to sheet"
    IgnoreEmptySource="False"
    Source="[OutDT]" />
```

### ExcelForEachRowX

Requires **two** delegate arguments — `Argument1` (row handle) and `Argument2` (index):

```xml
<ueab:ExcelForEachRowX
    DisplayName="For each row in Sheet1"
    EmptyRowBehavior="Stop"
    HasHeaders="True"
    Range="[Excel.Sheet(&quot;Sheet1&quot;)]"
    SaveAfterEachRow="False">
  <ueab:ExcelForEachRowX.Body>
    <ActivityAction x:TypeArguments="ue:CurrentRowQuickHandle, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="ue:CurrentRowQuickHandle" Name="CurrentRow" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Access cell value: CurrentRow.ByField("ColumnName") or CurrentRow.ByIndex(0) -->
      </Sequence>
    </ActivityAction>
  </ueab:ExcelForEachRowX.Body>
</ueab:ExcelForEachRowX>
```

### ForEachSheetX

Iterates sheets in a workbook. Same two-argument pattern as `ExcelForEachRowX` but with `WorksheetQuickHandle`:

```xml
<ueab:ForEachSheetX
    DisplayName="For Each Excel Sheet"
    Workbook="[Excel]">
  <ueab:ForEachSheetX.Body>
    <ActivityAction x:TypeArguments="ue:WorksheetQuickHandle, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="ue:WorksheetQuickHandle" Name="CurrentSheet" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Access sheet name: CurrentSheet.Name -->
      </Sequence>
    </ActivityAction>
  </ueab:ForEachSheetX.Body>
</ueab:ForEachSheetX>
```

### Other ueab: Activities (key attributes only — use `uipcli rpa get-default-activity-xaml` for full XAML)

#### Read / Write

| Activity | Key Attributes |
|----------|---------------|
| `ReadCellValueX` | `Cell="[CurrentRow.ByIndex(0)]"`, `GetFormattedText`, output via `SaveTo` child `OutArgument` |
| `ReadCellFormulaX` | `Cell`, `SaveTo="[outFormula]"` (direct attribute) |
| `WriteCellX` | `Cell="[Excel.Sheet(&quot;Sheet1&quot;).Cell(&quot;A1&quot;)]"`, `Value` |
| `FillRangeX` | `DestinationRange="[Excel.Sheet(s).Range(&quot;B11&quot;)]"`, `Value="[&quot;SUM(B1:B10)&quot;]"` |
| `ClearRangeX` | `TargetRange`, `HasHeaders` |
| `AppendRangeX` | `SourceRange`, `DestinationRange`, `HasHeaders`, `DestinationHasHeaders`, `PasteOptions`, `Transpose`, `StartingColumnName="{x:Null}"` |
| `CopyPasteRangeX` | `SourceRange`, `DestinationRange`, `PasteOptions="All"`, `Transpose="False"` |

#### Rows / Columns

| Activity | Key Attributes |
|----------|---------------|
| `InsertColumnX` | `Range="[Excel.Sheet(...)]"`, `NewColumnName`, `RelativeColumnName`, `RelativePosition="After\|Before"`, `HasHeaders="True"` |
| `InsertRowsX` | `Range="[Excel.Sheet(...)]"`, `InsertPosition="End\|Beginning"`, `NbOfRows`, `HasHeaders="True"` |
| `DeleteColumnX` | `Range`, `ColumnName`, `HasHeaders` |
| `DeleteRowsX` | `Range`, `DeleteRowsOption="Specific"`, `RowPositions`, `HasHeaders` |

#### Sheet Management

| Activity | Key Attributes |
|----------|---------------|
| `InsertSheetX` | `Workbook="[Excel]"`, `Name="NewSheet"`, `ReferenceNewSheetAs="[outNewSheet]"` — variable type `ue:ISheetRef` |
| `RenameSheetX` | `From="[Excel.Sheet(&quot;OldName&quot;)]"`, `To="NewName"` |
| `DeleteSheetX` | `Sheet="[Excel.Sheet(&quot;SheetName&quot;)]"` |
| `DuplicateSheetX` | `SheetToDuplicate`, `NewSheetName` |
| `SaveExcelFileX` | `Workbook="[Excel]"` |
| `ProtectSheetX` | `Sheet="[Excel.Sheet(...)]"`, `Password`, `SecurePassword="{x:Null}"`, `AdditionalPermissions` |
| `UnprotectSheetX` | `Sheet`, `Password`, `SecurePassword="{x:Null}"` |

#### Table / Structure

| Activity | Key Attributes |
|----------|---------------|
| `CreateTableX` | `Range`, `HasHeaders`, `OutTableName`, `TableName="{x:Null}"` |
| `RemoveDuplicatesX` | `Range`, `ColumnsCompareMode="AllColumns"`, `Columns` child list |
| `AutoFillX` | `StartRange` |
| `AutoFitX` | `Range`, `Columns`, `Rows` |

#### Search / Sort / Lookup

| Activity | Key Attributes |
|----------|---------------|
| `FindFirstLastDataRowX` | `Range`, `ColumnName`, `FirstRowIndex`, `LastRowIndex`, `HasHeaders`, `ConfigureLastRowAs`, `BlankRowsToSkip` |
| `FindReplaceValueX` | `WhereToSearch="[Excel.Sheet(...)]"`, `ValueToFind`, `ReplaceWith`, `Operation="Replace\|FindOnly"`, `LookIn="Values"` |
| `SortX` | `Range`, `HasHeaders`; body `ActivityAction` (no type args), child `ueab:SortColumnX` inside |
| `SortColumnX` | `ColumnName`, `SortDirection="Ascending"` (nested inside `SortX` body) |
| `LookupX` | `SourceRange`, `Label`, `ResultRange="{x:Null}"`, output via `Value` child `OutArgument` |
| `VLookupX` | `SourceRange`, `Label`, `ExactMatch`, `ColumnIndex="{x:Null}"`, output via `Value` child `OutArgument` |

#### Formatting

| Activity | Key Attributes |
|----------|---------------|
| `FormatRangeX` | `Range` + child elements `Alignment`, `Font`, `Format`, `NumberFormat` (use `uipcli rpa get-default-activity-xaml` for child structure) |

#### Filtering — requires `xmlns:ueabf`

| Activity | Key Attributes |
|----------|---------------|
| `FilterX` | `Range`, `ColumnName`, `HasHeaders`, `ClearFilter`; child `FilterX.FilterArgument` uses `ueabf:FilterArgument` or `ueabf:AdvancedFilterArgument` |
| `FilterPivotTableX` | `Table="[Excel.Sheet(...).PivotTable(&quot;Name&quot;)]"`, `ColumnName`, `ClearFilter`; child `FilterArgument` uses `ueabf:FilterArgument` |

#### Pivot Tables

| Activity | Key Attributes |
|----------|---------------|
| `CreatePivotTableXv2` | `Range`, `DestinationRange`, `TableName`, `LayoutRowType`, `ValuesMode`; body `ActivityAction` (no type args), child `ueab:PivotTableFieldX` inside |
| `PivotTableFieldX` | `FieldName`, `Function="Sum"`, `Type="Row"` (nested inside `CreatePivotTableXv2` body) |
| `ChangePivotTableDataSourceX` | `PivotTable="[Excel.Sheet(&quot;Sheet1&quot;).PivotTable(&quot;PivotName&quot;)]"`, `NewSourceRange` |
| `RefreshPivotTableX` | `Table="[Excel.Sheet(...).PivotTable(...)]"`, `LayoutRowType="{x:Null}"` |

#### Charts — requires `xmlns:ueabc`

| Activity | Key Attributes |
|----------|---------------|
| `InsertExcelChartX` | `Range`, `InsertIntoSheet`, `InsertedChart` (output, type `ue:IChartRef`), `ChartCategory`, `ChartType`, `ChartHeight`, `ChartWidth`, `Left`, `Top` |
| `UpdateChartX` | `Chart`; body `ActivityAction` (no type args), child `ueabc:ChangeDataRangeModification` inside |
| `ueabc:ChangeDataRangeModification` | `Range` (nested inside `UpdateChartX` body) |

#### Export

| Activity | Key Attributes |
|----------|---------------|
| `SaveAsPdfX` | `Workbook="[Excel]"`, `DestinationPdfPath`, `SaveQuality="StandardQuality"`, `EndPage="{x:Null}"`, `StartPage="{x:Null}"` |
| `ExportExcelToCsvX` | `TargetRange`, `FilePath` |

#### VBA / Macros

| Activity | Key Attributes |
|----------|---------------|
| `InvokeVBAX` | `Workbook="[Excel]"`, `CodeFilePath`, `EntryMethodName`, `Result="{x:Null}"`; body contains `ueab:InvokeVBAArgumentX` children |
| `InvokeVBAArgumentX` | `ArgumentValue` (nested inside `InvokeVBAX` body) |
| `ExecuteMacroX` | `Workbook="[Excel]"`, `MacroName`; `Result` via child `OutArgument`; body contains `ueab:ExecuteMacroArgumentX` children |
| `ExecuteMacroArgumentX` | `ArgumentValue` (nested inside `ExecuteMacroX` body) |

## Classic Style (ui:) — Standalone, No Scope

Classic activities specify the workbook path directly — no scope container needed.

### ReadRange

```xml
<ui:ReadRange
    Range="{x:Null}"
    WorkbookPathResource="{x:Null}"
    AddHeaders="True"
    DataTable="[dtResult]"
    DisplayName="Read Range"
    SheetName="[SheetName]"
    WorkbookPath="[ExcelFilePath]" />
```

### WriteRange

```xml
<ui:WriteRange
    WorkbookPathResource="{x:Null}"
    DataTable="[dtData]"
    DisplayName="Write Range"
    SheetName="Sheet1"
    StartingCell="A1"
    WorkbookPath="[ExcelFilePath]" />
```

### AppendRange

```xml
<ui:AppendRange
    WorkbookPathResource="{x:Null}"
    DataTable="[dtData]"
    DisplayName="Append Range"
    SheetName="[SheetName]"
    WorkbookPath="[ExcelFilePath]" />
```

### ForEachRow (classic)

One delegate argument of type `DataRow`:

```xml
<ui:ForEachRow
    ColumnNames="{x:Null}"
    CurrentIndex="{x:Null}"
    DataTable="[dtData]"
    DisplayName="For Each Row">
  <ui:ForEachRow.Body>
    <ActivityAction x:TypeArguments="sd:DataRow">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Access: CurrentRow("ColumnName").ToString() -->
      </Sequence>
    </ActivityAction>
  </ui:ForEachRow.Body>
</ui:ForEachRow>
```

### WorkbookPath vs WorkbookPathResource

Mutually exclusive on all classic activities. Set the unused one to `{x:Null}`.

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Modern scope | `ueab:ExcelApplicationCard` with `ActivityAction<ue:IWorkbookQuickHandle>`, argument name `"Excel"` |
| Sheet reference (modern) | `Excel.Sheet("SheetName")` — used in `Range`, `Destination`, `WhereToSearch` etc. |
| Cell range (modern) | `Excel.Sheet("SheetName").Range("A1:B10")` |
| Direct cell (modern) | `Excel.Sheet("SheetName").Cell("A1")` — used in `WriteCellX`, `ReadCellValueX` |
| Pivot table reference | `Excel.Sheet("SheetName").PivotTable("PivotName")` |
| Row field access (modern) | `CurrentRow.ByField("ColumnName")` or `CurrentRow.ByIndex(0)` (0-based) |
| `ExcelForEachRowX` | Two args: `Argument1` (`ue:CurrentRowQuickHandle` `"CurrentRow"`) + `Argument2` (`x:Int32` `"CurrentIndex"`) |
| `ForEachSheetX` | Two args: `Argument1` (`ue:WorksheetQuickHandle` `"CurrentSheet"`) + `Argument2` (`x:Int32` `"CurrentIndex"`); `CurrentSheet.Name` for sheet name |
| Filter sub-namespace | Add `xmlns:ueabf="clr-namespace:UiPath.Excel.Activities.Business.Filter;assembly=UiPath.Excel.Activities"` for `FilterX`, `FilterPivotTableX` |
| Chart sub-namespace | Add `xmlns:ueabc="clr-namespace:UiPath.Excel.Activities.Business.ChartModifications;assembly=UiPath.Excel.Activities"` for `UpdateChartX` modifications |
| Handle variable types | `ue:ISheetRef` (InsertSheetX output), `ue:IChartRef` (InsertExcelChartX output) |
| Classic standalone | No scope — `WorkbookPath` on each activity; set `WorkbookPathResource="{x:Null}"` |
| `ForEachRow` (classic) | One arg: `DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow"` |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
