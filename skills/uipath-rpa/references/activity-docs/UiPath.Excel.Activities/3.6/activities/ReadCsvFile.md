# Read CSV

`UiPath.CSV.Activities.ReadCsvFile`

Copies all entries from a specified CSV file to a DataTable for later use in the automation.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | Read from local file | InArgument | `string` | Conditional | | The full local path of the CSV file. Alternative to `PathResource` — use one or the other |
| `PathResource` | Read from resource file | InArgument | `IResource` | Conditional | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `FilePath` — use one or the other |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `IncludeColumnNames` | Has headers | `bool` | `True` | Specifies if the first row in the CSV file should be considered to contain the column names. If set to false, the output DataTable will have columns with default names |
| `DelimitatorForViewModel` | Delimiter | `DelimiterOptions` | `Comma` | Specifies the delimiter in the CSV file |
| `Encoding` | Encoding | `InArgument<string>` | | The character encoding to use (e.g. "utf-8", "utf-16"). Defaults to UTF-8 |
| `IgnoreQuotes` | Ignore quotes | `InArgument<bool>` | | When set, quoted fields are not treated specially — quotes are treated as regular characters |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `DataTable` | CSV Range | `DataTable` | The data retrieved from the CSV file as a DataTable |

## Valid Configurations

This activity supports two input modes via `[OverloadGroup]`:

**Mode A — Local File**: Set `FilePath` to the full path of the CSV file.
**Mode B — Resource File**: Set `PathResource` to an `IResource` reference.

Properties `FilePath` and `PathResource` are mutually exclusive.

### Enum Reference

**`DelimiterOptions`**: `Comma`, `Semicolon`, `Pipe`, `Caret`, `Tab`

## XAML Example

```xml
<csv:ReadCsvFile
  DisplayName="Read CSV"
  FilePath="[&quot;data.csv&quot;]"
  IncludeColumnNames="True"
  DataTable="[csvData]" />
```

## Notes

- When neither `FilePath` nor `PathResource` is set, the activity will fail at runtime.
- The `Encoding` property accepts standard .NET encoding names (e.g. "utf-8", "utf-16", "ascii").
