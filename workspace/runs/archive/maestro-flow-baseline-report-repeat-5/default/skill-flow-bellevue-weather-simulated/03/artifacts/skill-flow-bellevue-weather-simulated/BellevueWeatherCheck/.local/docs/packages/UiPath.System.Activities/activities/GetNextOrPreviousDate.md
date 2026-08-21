# Get Next or Previous Date

`UiPath.Activities.System.Date.GetNextOrPreviousDate`

Returns the next or previous date boundary relative to a source date.

**Package:** `UiPath.System.Activities`
**Category:** Programming > Date

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source date | `InArgument` | `DateTime` | Yes | - | The date and time used as the reference point. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SelectedOperation` | Operation | `GetNextOrPreviousOperations` | `Next` | Whether to return the next or previous boundary. |
| `UnitOfTime` | Unit | `UnitsOfTime` | `Days` | The boundary unit: seconds, minutes, hours, days, day of the week, weeks, months, or years. |
| `DayOfWeekSelection` | Day of the week | `DayOfWeek` | `Monday` | The target day used when `UnitOfTime` is `DayOfTheWeek`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `DateTime` | The calculated next or previous date. |

## XAML Example

```xml
<ui:GetNextOrPreviousDate
    DisplayName="Get Next or Previous Date"
    Source="[currentDate]"
    SelectedOperation="Next"
    UnitOfTime="Months"
    Result="[nextMonthStart]" />
```

`xmlns:ui="clr-namespace:UiPath.Activities.System.Date;assembly=UiPath.System.Activities"`

## Notes

- For minutes, hours, days, weeks, months, and years, lower-order time components are reset before moving to the requested boundary.
- `Source` cannot be `DateTime.MinValue`; validation throws when the source date is empty.
