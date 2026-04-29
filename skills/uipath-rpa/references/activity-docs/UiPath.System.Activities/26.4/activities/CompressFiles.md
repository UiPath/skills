# Compress/Zip Files

`UiPath.Activities.System.Compression.Workflow.CompressFiles`

Compresses given contents into a ZIP archive.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CompressedFileName` | Compressed file name | `InArgument` | `string` | Yes | — | Name of the output compressed file to create (including `.zip` extension). |
| `ResourcesToArchive` | Resources to zip | `Property` | `InArgument<IEnumerable<IResource>>` | No | — | Collection of `IResource` items to compress. |
| `ContentToArchive` | Content to zip | `Property` | `List<InArgument<string>>` | No | — | List of local file or folder paths to compress. |
| `AllowDuplicateContentNames` | Allow contents with duplicate names | `InArgument` | `bool` | No | `false` | When `true`, files with identical names from different directories are all included in the archive. |
| `Password` | Password | `InArgument` | `string` | No | — | Password to protect the archive. Overload group: `Password`. |
| `SecurePassword` | Secure Password | `InArgument` | `SecureString` | No | — | Password as a `SecureString` to protect the archive. Overload group: `Secure password`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `CompressionLevel` | Compression level | `ArchiveCompressionLevel` | — | Controls the trade-off between compression ratio and speed: `Optimal`, `Fastest`, `NoCompression`, or `SmallestSize`. |
| `EncryptionAlgorithm` | Encryption algorithm | `ArchiveEncryptionAlgorithm` | — | Algorithm used for password encryption when a password is specified (e.g. `ZipCrypto`, `AES128`, `AES256`). |
| `OverrideExistingFile` | Overwrite existing file | `bool` | `true` | When `true`, replaces an existing archive file with the same name. |
| `CodePage` | Name encoding | `CodePages` | — | Text encoding used for file names inside the archive. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CompressedFileInfo` | Compressed file | `OutArgument` | `FileInfo` | `FileInfo` object representing the created archive. |
| `CompressedResource` | Compressed file reference | `OutArgument` | `ILocalResource` | `ILocalResource` reference to the created archive. |

## Valid Configurations

### Source selection

Two complementary approaches to specify what to compress (can be combined):

| Mode | Property | Description |
|------|----------|-------------|
| Path list | `ContentToArchive` | A list of string expressions — each resolving to a local file or folder path. |
| Resource list | `ResourcesToArchive` | An expression resolving to `IEnumerable<IResource>`. |

### Password protection

Two mutually exclusive overload groups:

| Mode | Property | Description |
|------|----------|-------------|
| Plain text password | `Password` | Password as a plain `string`. |
| Secure password | `SecurePassword` | Password as a `SecureString` for improved security. |

## XAML Example

```xml
<ui2:CompressFiles
    DisplayName="Compress/Zip Files"
    CompressedFileName="&quot;C:\output\archive.zip&quot;"
    CompressionLevel="Optimal"
    OverrideExistingFile="True"
    CompressedFileInfo="[zipFileInfo]"
    CompressedResource="[zipResource]">
  <ui2:CompressFiles.ContentToArchive>
    <InArgument x:TypeArguments="x:String">&quot;C:\reports\summary.xlsx&quot;</InArgument>
    <InArgument x:TypeArguments="x:String">&quot;C:\reports\details.csv&quot;</InArgument>
  </ui2:CompressFiles.ContentToArchive>
</ui2:CompressFiles>
```

`xmlns:ui2="clr-namespace:UiPath.Activities.System.Compression.Workflow;assembly=UiPath.System.Activities"`

## Notes

- At least one of `ContentToArchive` or `ResourcesToArchive` should be provided; supplying neither produces an empty archive.
- When a folder path is included in `ContentToArchive`, all files within that folder are added recursively.
- `EncryptionAlgorithm` only takes effect when `Password` or `SecurePassword` is set.
- `CompressedResource` and `CompressedFileInfo` both reference the same output file; use whichever is more convenient for downstream activities.
