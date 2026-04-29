# Format Date as Text

`UiPath.Activities.System.Date.FormatDateAsText`

Format the source DateTime variable in a text (string).

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source date | InArgument | `DateTime` | Yes | — | The `DateTime` value to format as text. |
| `Format` | Date and time format | InArgument | `String` | Yes | — | The format string used to render the date. Accepts standard single-character specifiers (e.g. `d`, `D`, `f`, `F`, `g`, `G`) or custom patterns (e.g. `yyyy-MM-dd`). Supports autocomplete. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `LocalizationCode` | Localization code | `CultureInfo` | `CultureInfo.CurrentCulture` | The culture used to format the date, including the names of months and days. Select from a dropdown of all installed cultures. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `String` | The date formatted as a text string according to the specified format and culture. |

## XAML Example

```xml
<ucs:FormatDateAsText
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Date;assembly=UiPath.System.Activities.Standard"
  Source="[invoiceDate]"
  Format="[&quot;MMMM dd, yyyy&quot;]"
  LocalizationCode="[System.Globalization.CultureInfo.GetCultureInfo(&quot;en-US&quot;)]"
  Result="[formattedDate]" />
```

## Notes

- The format string follows standard .NET `DateTime.ToString(format, culture)` rules.
- Full-name patterns such as `MMMM` (full month name) or `dddd` (full day name) are culture-sensitive and require the correct `LocalizationCode` to produce localized output.
- Standard single-character specifiers such as `d`, `D`, `f`, `F`, `g`, `G`, `r`, `s`, `u` are fully supported; the autocomplete widget lists common options.
- The `LocalizationCode` dropdown lists all cultures available on the machine via `CultureInfo.GetCultures(CultureTypes.AllCultures)`.
