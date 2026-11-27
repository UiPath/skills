# Extract/Unzip Files

`UiPath.Activities.System.Compression.Workflow.ExtractFiles`

Extracts all contents of a zipped (compressed) file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FileToExtract` | File to extract | `InArgument` | `string` | Yes* | — | Full path of the ZIP file to extract. Overload group: `FileToExtract`. |
| `File` | File | `InArgument` | `IResource` | Yes* | — | Resource reference to the ZIP file to extract. Overload group: `File`. |
| `DestinationFolder` | Destination folder | `InArgument` | `string` | No | — | Path of the folder where contents are extracted. If empty, the folder containing the ZIP file is used. |
| `ConflictResolution` | If file already exists | `InArgument` | `FileConflictBehavior` | No | `FileConflictBehavior.Replace` | Behaviour when an extracted file already exists at the destination: `Replace`, `Skip`, or `Rename`. |
| `Password` | Password | `InArgument` | `string` | No | — | Password required to extract a password-protected archive. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExtractToADedicatedFolder` | Extract to dedicated folder | `bool` | `true` | When `true`, extracts contents into a new subfolder named after the ZIP file. |
| `SkipUnsupportedFiles` | Skip unsupported files | `bool` | `false` | When `true`, files that cannot be extracted are silently skipped instead of causing an error. |
| `CodePage` | Name encoding | `CodePages` | — | Text encoding used for file names inside the archive. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Content` | Extracted Files | `OutArgument` | `ILocalResource[]` | Array of references to all extracted files. |
| `DestinationFolderInfo` | Extracted contents folder | `OutArgument` | `DirectoryInfo` | Reference to the folder containing the extracted content. |

## Valid Configurations

Two mutually exclusive modes determine how the archive file is specified:

| Mode | Property | Description |
|------|----------|-------------|
| Local path | `FileToExtract` | String expression resolving to a local ZIP file path. |
| Resource | `File` | `IResource` expression (e.g. from a Storage Bucket or Create File). |

## XAML Example

```xml
<ui2:ExtractFiles
    DisplayName="Extract/Unzip Files"
    FileToExtract="&quot;C:\downloads\archive.zip&quot;"
    DestinationFolder="&quot;C:\output&quot;"
    ExtractToADedicatedFolder="True"
    ConflictResolution="FileConflictBehavior.Replace"
    Content="[extractedFiles]"
    DestinationFolderInfo="[extractedFolder]" />
```

`xmlns:ui2="clr-namespace:UiPath.Activities.System.Compression.Workflow;assembly=UiPath.System.Activities"`

## Notes

- Supported archive format is ZIP. GZip is not supported by this activity.
- When `ExtractToADedicatedFolder` is `true` and `DestinationFolder` is set, a new subfolder named after the ZIP file is created inside `DestinationFolder`.
- The `Content` array lists only extracted files, not directories.
- For password-protected archives, supply the `Password` argument; leaving it empty for a protected archive results in an error unless `SkipUnsupportedFiles` is `true`.
