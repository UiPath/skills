# Add or Subtract from Date

`UiPath.Activities.System.Date.AddOrSubtractFromDate`

Allows to add or subtract a specified unit of time from the source date.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source date | InArgument | `DateTime` | Yes | — | The base `DateTime` value to modify. |
| `AmountOfTime` | Amount | InArgument | `Int32` | No | — | The numeric amount to add or subtract. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SelectedOperation` | Operation | `DateOperations` | `Add` | Whether to add to or subtract from the source date. Displayed as a radio-button group. |
| `UnitOfTime` | Unit | `UnitsOfTime` | `Days` | The unit of time that `AmountOfTime` represents. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `DateTime` | The resulting `DateTime` after the specified amount has been added or subtracted. |

### Enum Reference

**`DateOperations`**: `Add`, `Subtract`

**`UnitsOfTime`** (available for this activity — `DayOfTheWeek` is excluded): `Seconds`, `Minutes`, `Hours`, `Days`, `Weeks`, `Months`, `Years`

## XAML Example

```xml
<ucs:AddOrSubtractFromDate
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Date;assembly=UiPath.System.Activities.Standard"
  Source="[startDate]"
  SelectedOperation="Add"
  UnitOfTime="Months"
  AmountOfTime="[3]"
  Result="[futureDate]" />
```

## Notes

- `Weeks` is calculated as `AmountOfTime * 7` days.
- `Months` and `Years` use .NET's `DateTime.AddMonths` and `DateTime.AddYears`, which handle month-length and leap-year boundaries automatically (e.g. adding one month to January 31 gives the last day of February).
- For the `Subtract` operation the `AmountOfTime` is negated internally, so the value of `AmountOfTime` should always be a positive integer.
- `DayOfTheWeek` is not available as a unit for this activity; use **Get Next or Previous Date** instead for day-of-week navigation.
