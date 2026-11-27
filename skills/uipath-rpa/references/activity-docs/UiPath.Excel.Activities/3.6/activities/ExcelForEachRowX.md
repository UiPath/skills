# For Each Excel Row

`UiPath.Excel.Activities.Business.ExcelForEachRowX`

Repeats the contained activities once for each row in the specified sheet, range, or table.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | In range | InArgument | `IReadRangeRef` | Yes | | Sheet, range, or table to repeat actions for each row. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `False` | The first row in the range is a header row. |
| `EmptyRowBehavior` | Empty row behavior | `EmptyRowBehavior` | `Stop` | Desired action when an empty row is reached in the specified range. |
| `SaveAfterEachRow` | Save after each row | `bool` | `False` | Saves the workbook after running the actions for each row. Otherwise workbook is saved when all actions for the Excel file finish. |

### Body
| Name | Type | Description |
|------|------|-------------|
| `Body` | `ActivityAction<CurrentRowQuickHandle, int>` | The activities to execute for each row. Exposes `CurrentRow` (the current row handle) and `CurrentIndex` (the row index) as iteration variables. |

### Enum Reference

#### `EmptyRowBehavior`
| Value | Display Name |
|-------|-------------|
| `StopAfterThreeConsecutiveEmptyRows` | Stop after 3 consecutive empty rows |
| `Stop` | Stop |
| `Skip` | Skip |
| `Process` | Process |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:ExcelForEachRowX
    Range="[MyRange]"
    HasHeaders="True"
    EmptyRowBehavior="Stop"
    SaveAfterEachRow="False"
    DisplayName="For Each Excel Row">
    <excel:ExcelForEachRowX.Body>
      <ActivityAction x:TypeArguments="excel:CurrentRowQuickHandle, x:Int32">
        <ActivityAction.Argument1>
          <DelegateInArgument x:TypeArguments="excel:CurrentRowQuickHandle" Name="CurrentRow" />
        </ActivityAction.Argument1>
        <ActivityAction.Argument2>
          <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
        </ActivityAction.Argument2>
        <Sequence DisplayName="Do">
          <!-- Activities to execute per row go here -->
        </Sequence>
      </ActivityAction>
    </excel:ExcelForEachRowX.Body>
  </excel:ExcelForEachRowX>
</excel:ExcelApplicationCard>
```

## Notes
- The iteration variable name defaults to `CurrentRow` and can be renamed in the designer via the "For each" property.
- The `CurrentIndex` variable provides the 1-based index of the current row within the iteration (the first processed row has `CurrentIndex` = 1).
- When `HasHeaders` is `True` and the source is a range (not a table), the first row is treated as a header and iteration starts from the second row.
- When `SaveAfterEachRow` is `False`, auto-save is disabled during iteration and re-enabled after the loop completes, which improves performance for large datasets.
- The variable name for the iterator must be a valid identifier; otherwise, a validation error is raised.
