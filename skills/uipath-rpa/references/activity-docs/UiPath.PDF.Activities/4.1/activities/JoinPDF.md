# Join PDF Files

`UiPath.PDF.Activities.PDF.JoinPDF`

Merges two or more PDF files into a single output PDF. Supports two input modes: providing files as a collection (array of paths or resource array) or providing files individually one by one. The merged file is written to `OutputFileName` and returned via `OutputFile`.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `FileList` | Files (local paths) | InArgument | `string[]` | Yes† | | | An array of local PDF file paths to merge. Visible only when `InputMode` is `Collection`. Mutually exclusive with `ResourceFileList`. |
| `ResourceFileList` | Files | InArgument | `IResource[]` | Yes† | | | An array of file resources to merge. Visible only when `InputMode` is `Collection`. Mutually exclusive with `FileList`. |
| `IndividualResourceFileList` | Files | Property | `IEnumerable<InArgument<IResource>>` | | | | Individual file resource arguments added one by one. Visible only when `InputMode` is `Individual`. |
| `OutputFileName` | Output File Path | InArgument | `string` | | | | Full path where the merged PDF will be saved. If not specified, a default path is generated automatically. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InputMode` | Input Mode | `ItemsInputMode` | `Collection` | Controls how input files are specified. `Collection` uses `FileList`/`ResourceFileList`; `Individual` uses `IndividualResourceFileList`. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFile` | Output File | `ILocalResource` | The merged PDF file as a local resource. |

## Conditional Properties

These properties appear or change behavior based on other property values:

- **`FileList`** (InArgument\<string[]\>) — Visible only when `InputMode` is `Collection`. Provide either `FileList` or `ResourceFileList`, not both.
- **`ResourceFileList`** (InArgument\<IResource[]\>) — Visible only when `InputMode` is `Collection`. Provide either `ResourceFileList` or `FileList`, not both.
- **`IndividualResourceFileList`** (IEnumerable\<InArgument\<IResource\>\>) — Visible only when `InputMode` is `Individual`.

## Enum Reference

**`ItemsInputMode`**: `Collection` (Use a collection of PDF files), `Individual` (Use individual PDF files)

## Notes

- At least two files must be provided regardless of input mode; fewer than two files is a validation error.
- When `InputMode` is `Collection`, setting both `FileList` and `ResourceFileList` is a validation error — use one or the other.
- File paths are validated for existence and `.pdf` extension before merging.

## XAML Example

### Collection mode (local paths)

```xml
<pdf:JoinPDF
    DisplayName="Join PDF Files"
    InputMode="Collection"
    FileList="[new String() {&quot;C:\docs\part1.pdf&quot;, &quot;C:\docs\part2.pdf&quot;}]"
    OutputFileName="[outputFilePath]"
    OutputFile="[mergedFile]" />
```

### Collection mode (file resources)

```xml
<pdf:JoinPDF
    DisplayName="Join PDF Files"
    InputMode="Collection"
    ResourceFileList="[resourceArray]"
    OutputFileName="[outputFilePath]"
    OutputFile="[mergedFile]" />
```

> Namespace prefix `pdf` maps to `clr-namespace:UiPath.PDF.Activities.PDF;assembly=UiPath.PDF.Activities`.
