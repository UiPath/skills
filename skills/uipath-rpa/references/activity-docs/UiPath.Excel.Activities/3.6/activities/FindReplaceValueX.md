# Find/Replace Value

`UiPath.Excel.Activities.Business.FindReplaceValueX`

Searches in a specified range for a certain value. Depending on the Operation chosen, it either returns the location of the cell or it replaces the value(s) with another given value.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Operation` | Operation | Property | `FindReplaceOptions` | Yes | `Find` | Depending on the Operation chosen, it either returns the location of the cell or it replaces the value(s) with another given value. |
| `WhereToSearch` | Where to search | InArgument | `IReadRangeRef` | Yes | | Range where to search the value. |
| `ValueToFind` | Value to find | InArgument | `object` | Yes | | Value to search for. |
| `ReplaceWith` | Replace with | InArgument | `object` | No | | Value to replace with. |
| `LookIn` | Look in | Property | `LookInOptions` | No | `Values` | To search for data with specific details, in the box, click Formulas, Values. |
| `MatchCase` | Match case | Property | `bool` | No | `False` | Check this if you want to search for case-sensitive data. |
| `MatchEntireCellContents` | Match entire cell contents | Property | `bool` | No | `False` | Check this if you want to search for cells that contain just the characters that you typed in the Value to find field. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `FoundAt` | Found at | `string` | Address where the value was found. |

### Enum Reference

#### `FindReplaceOptions`
| Value | Display Name |
|-------|-------------|
| `Find` | Find |
| `Replace` | Replace |
| `ReplaceAll` | Replace all |

#### `LookInOptions`
| Value | Display Name |
|-------|-------------|
| `Values` | Values |
| `Formulas` | Formulas |

## Valid Configurations

- When `Operation` is `Replace` or `ReplaceAll`, `LookIn` must be set to `Values`. Attempting to replace in `Formulas` raises a validation error.

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:FindReplaceValueX
    Operation="Find"
    WhereToSearch="[MyRange]"
    ValueToFind="SearchText"
    LookIn="Values"
    MatchCase="False"
    MatchEntireCellContents="False"
    FoundAt="[ResultAddress]"
    DisplayName="Find/Replace Value" />
</excel:ExcelApplicationCard>
```

## Notes
- The `ValueToFind` must not be null or empty; otherwise, an `ArgumentException` is thrown.
- Replace operations (`Replace` and `ReplaceAll`) only work when `LookIn` is set to `Values`. A design-time validation error is raised if `LookIn` is set to `Formulas` with a replace operation.
- The `FoundAt` output contains the cell address (e.g., `$A$1`) where the value was found, or `null` if not found.
