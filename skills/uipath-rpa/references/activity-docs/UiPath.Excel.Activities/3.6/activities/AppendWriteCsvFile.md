# Write CSV

`UiPath.CSV.Activities.AppendWriteCsvFile`

Copies a DataTable and pastes it in a specified CSV file, either appending after existing data or replacing any existing data in the file.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | Local CSV file | InArgument | `string` | Conditional | | The full local path of the CSV file. Alternative to `PathResource` — use one or the other |
| `PathResource` | Resource CSV file | InArgument | `IResource` | Conditional | | A resource reference (e.g. a local file, remote file, or abstract resource). Alternative to `FilePath` — use one or the other |
| `DataTable` | What to write | InArgument | `DataTable` | Yes | | The input DataTable containing the data to write to the CSV file |
| `CsvAction` | How to write | Property | `CsvWriteAction` | Yes | `Write` | Select how to write data into the file |
| `AddHeaders` | Include headers | Property | `bool` | | `True` | Whether the column names from the DataTable will be added to the output CSV file |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `DelimitatorForViewModel` | Delimiter | `DelimiterOptions` | `Comma` | Specifies the delimiter in the CSV file |
| `Encoding` | Encoding | `InArgument<string>` | | The character encoding to use (e.g. "utf-8", "utf-16") |
| `ShouldQuote` | Should quote | `bool` | `True` | When set to true, a field is quoted when writing if it starts/ends with a space, contains \r or \n, or contains the CSV delimiter |

## Valid Configurations

This activity supports two input modes via `[OverloadGroup]`:

**Mode A — Local File**: Set `FilePath` to the full path of the CSV file.
**Mode B — Resource File**: Set `PathResource` to an `IResource` reference.

Properties `FilePath` and `PathResource` are mutually exclusive.

### Enum Reference

**`CsvWriteAction`**: `Append`, `Write`

**`DelimiterOptions`**: `Comma`, `Semicolon`, `Pipe`, `Caret`, `Tab`

## XAML Example

```xml
<csv:AppendWriteCsvFile
  DisplayName="Write CSV"
  FilePath="[&quot;output.csv&quot;]"
  DataTable="[dataToWrite]"
  CsvAction="Write"
  AddHeaders="True"
  ShouldQuote="True" />
```

## Notes

- `Write` mode replaces any existing file content. `Append` mode adds data after existing rows.
- When neither `FilePath` nor `PathResource` is set, the activity will fail at runtime.
