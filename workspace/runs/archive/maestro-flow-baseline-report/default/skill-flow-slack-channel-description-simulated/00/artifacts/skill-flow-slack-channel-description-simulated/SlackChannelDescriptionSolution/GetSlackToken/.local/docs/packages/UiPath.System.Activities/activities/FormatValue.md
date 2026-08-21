# Format Value

`UiPath.Core.Activities.FormatValue`

Associates a specific format to a GenericValue variable for use with `.ToString` and `Parse` operations. Supported formats are Number, DateTime, Currency, and Percentage.

**Package:** `UiPath.System.Activities`
**Platform:** Windows only
**Category:** Programming > GenericValue

## Properties

### Input/Output

> These properties require a **variable** binding — the activity reads the incoming value and writes an updated value back. Do not use literal expressions.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Value | Value | InOutArgument | GenericValue | Yes | — | The GenericValue variable to format. The activity reads its current value, applies the format, and writes the formatted value back to the same variable. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Format | Format | IFormatProvider | `GeneralNumberFormatProvider` | The format to apply to the value. Select one of the four format provider types via the property editor (Number, DateTime, Currency, Percentage). |

## Format Provider Reference

The `Format` property accepts one of four `GenericValueFormatProvider` implementations, selectable in Studio's property editor:

| Format Type | Display Name | Description |
|-------------|-------------|-------------|
| `GeneralNumberFormatProvider` | Number | Formats the value as a number. Configurable: `DecimalSeparator`, `GroupSeparator`, `DecimalDigits`. |
| `DateTimeFormatProvider` | DateTime | Formats the value as a date/time using a short date pattern. Configurable: `Pattern` (date/time format string). |
| `CurrencyNumberFormatProvider` | Currency | Formats the value as currency. Configurable: `Symbol`, `DecimalSeparator`, `GroupSeparator`, `DecimalDigits`. |
| `PercentageNumberFormatProvider` | Percentage | Formats the value as a percentage. Configurable: `Symbol` (default `%`), `DecimalSeparator`, `GroupSeparator`, `DecimalDigits`. |

## XAML Example

```xml
<!-- Format a GenericValue as a Number with 2 decimal places -->
<ui:FormatValue DisplayName="Format Value"
                xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
                xmlns:uic="clr-namespace:UiPath.Core;assembly=UiPath.System.Activities">
  <ui:FormatValue.Value>
    <InOutArgument x:TypeArguments="uic:GenericValue">[myGenericValue]</InOutArgument>
  </ui:FormatValue.Value>
  <ui:FormatValue.Format>
    <uic:GeneralNumberFormatProvider DecimalDigits="2" DecimalSeparator="." GroupSeparator="," />
  </ui:FormatValue.Format>
</ui:FormatValue>
```

## Notes

- `Value` is an `InOutArgument<GenericValue>` — it must be bound to a variable, not a literal.
- The format is applied in-place: after execution, the same variable holds a `GenericValue` with the `FormatProvider` set, which affects subsequent `.ToString()` and type-conversion calls.
- This activity is Windows-only (not available in cross-platform/Linux robots).
