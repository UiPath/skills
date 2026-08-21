# Modify Date

`UiPath.Core.Activities.ModifyDate`

Applies one or more date modification operations to a source date, then returns the result as a `DateTime` or formatted text.

**Package:** `UiPath.System.Activities`
**Category:** Programming > Date

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceDate` | Date to modify | `InArgument` | `DateTime` | Yes | - | The source date used by the child date modification operations. |

### Options

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FormatAsText` | Format output as Text | `bool` | `false` | When `true`, writes the result to `OutText`; otherwise writes to `OutDate`. |
| `PredefinedDateFormat` | Date format | `DateFormat` | `DotNetShortDate` | Predefined format used when `FormatAsText` is `true` and `UseCustomDateFormat` is `false`. |
| `UseCustomDateFormat` | Use custom date format | `bool` | `false` | When `true`, uses `CustomDateFormat` instead of `PredefinedDateFormat`. |
| `CustomDateFormat` | Custom date format | `InArgument<string>` | - | .NET date/time format string used when `UseCustomDateFormat` is `true`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `OutDate` | Save result as DateTime | `OutArgument` | `DateTime` | The modified date when `FormatAsText` is `false`. |
| `OutText` | Save result as Text | `OutArgument` | `string` | The formatted modified date when `FormatAsText` is `true`. |

### Body

| Name | Type | Description |
|------|------|-------------|
| `Body` | `ActivityAction` | Container for date modification child activities. |

## Child Date Modifications

The designer supports date modification child activities that populate the modification descriptor:

| Child Activity | Description |
|----------------|-------------|
| `AddSubtractTimePeriodDateModification` | Adds or subtracts days, weeks, months, or years. |
| `FindDayOfWeekDateModification` | Finds the next or previous selected day of the week. |
| `FindStartEndDateModification` | Finds the first or last day of the week, month, or year. |

## XAML Example

```xml
<ui:ModifyDate
    DisplayName="Modify Date"
    SourceDate="[invoiceDate]"
    OutDate="[dueDate]">
  <ui:ModifyDate.Body>
    <ActivityAction>
      <Sequence>
        <uidm:AddSubtractTimePeriodDateModification
            Operation="Add"
            Value="30"
            TimeUnit="Days" />
      </Sequence>
    </ActivityAction>
  </ui:ModifyDate.Body>
</ui:ModifyDate>
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`
`xmlns:uidm="clr-namespace:UiPath.Core.Activities.DateModifications;assembly=UiPath.System.Activities"`

## Notes

- `SourceDate` must not be empty.
- If `FormatAsText`, `UseCustomDateFormat`, and an empty `CustomDateFormat` are combined, validation fails.
