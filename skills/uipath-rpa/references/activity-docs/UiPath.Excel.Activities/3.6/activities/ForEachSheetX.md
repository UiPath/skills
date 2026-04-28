# For Each Excel Sheet

`UiPath.Excel.Activities.Business.ForEachSheetX`

Repeats actions for each sheet in an Excel workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | The source workbook for the sheets. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `VariableName` | For each | `string` | `"CurrentSheet"` | Name of the variable representing the current sheet in the loop body. |

### Loop Variables
| Name | Type | Description |
|------|------|-------------|
| `CurrentSheet` | `WorksheetQuickHandle` | The current sheet in the iteration. |
| `CurrentIndex` | `int` | The 1-based index of the current sheet. |

## XAML Example
```xml
<excel:ForEachSheetX
  DisplayName="For Each Excel Sheet"
  Workbook="[workbookHandle]">
  <excel:ForEachSheetX.Body>
    <ActivityAction x:TypeArguments="excel:WorksheetQuickHandle, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="excel:WorksheetQuickHandle" Name="CurrentSheet" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Activities to execute for each sheet -->
      </Sequence>
    </ActivityAction>
  </excel:ForEachSheetX.Body>
</excel:ForEachSheetX>
```

## Notes
- Only visible sheets are iterated; hidden sheets are skipped.
- The loop variable name defaults to `CurrentSheet` but can be renamed in the designer.
- The `CurrentIndex` variable is 1-based.
- The activity sets each sheet as the active sheet before executing the body.
