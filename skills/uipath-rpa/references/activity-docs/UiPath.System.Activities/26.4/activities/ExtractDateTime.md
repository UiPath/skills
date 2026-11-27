# Extract Date and Time from Text

`UiPath.Activities.System.Text.ExtractDateTime`

Extracts date and time from the given input text matching the specified format and outputs it as a variable.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source | InArgument | `String` | Yes | — | The text from which date and time values are to be extracted. |
| `Format` | Date and time format | InArgument | `String` | Yes | — | The expected date/time format string. Accepts standard single-character format specifiers (e.g. `d`, `D`, `f`, `F`, `g`, `G`) or custom format patterns (e.g. `MM/dd/yyyy`). Supports autocomplete. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `LocalizationCode` | Localization code | `CultureInfo` | `CultureInfo.CurrentCulture` | The culture used to interpret the format string and parse month/day names. Select from a dropdown of all installed cultures. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `DateTime` | The first `DateTime` value extracted from the text. |
| `Results` | All Extracted DateTimes | OutArgument | `IEnumerable<DateTime>` | A collection of all `DateTime` values found in the text that match the specified format. |

## XAML Example

```xml
<ucs:ExtractDateTime
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Text;assembly=UiPath.System.Activities.Standard"
  Source="[reportText]"
  Format="[&quot;MM/dd/yyyy&quot;]"
  LocalizationCode="[System.Globalization.CultureInfo.GetCultureInfo(&quot;en-US&quot;)]"
  Result="[firstDate]"
  Results="[allDates]" />
```

## Notes

- Standard single-character format specifiers (e.g. `d`) are expanded into all matching patterns for the selected culture before matching, enabling robust extraction.
- Custom format strings must exactly describe the date/time structure present in the source text; unrecognised occurrences are silently skipped.
- `Result` holds only the first match. Iterate over `Results` to process all occurrences.
- Full-name patterns such as `MMMM` (full month name) require the correct `LocalizationCode` to parse successfully.
- The activity uses `DateTime.TryParseExact` internally, so format strings follow standard .NET date/time format specifier rules.
