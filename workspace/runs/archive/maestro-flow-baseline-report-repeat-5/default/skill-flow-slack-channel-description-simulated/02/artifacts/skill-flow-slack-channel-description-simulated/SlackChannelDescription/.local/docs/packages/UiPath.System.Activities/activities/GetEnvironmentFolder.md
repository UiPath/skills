# Get Environment Folder

`UiPath.Core.Activities.GetEnvironmentFolder`

Gets the path to the specified system special folder.

**Package:** `UiPath.System.Activities`
**Category:** System.Environment

## Properties

### Input

_No input arguments._

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| SpecialFolder | Special Folder | `System.Environment.SpecialFolder` | — | The well-known system folder whose path is to be retrieved. Required. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| FolderPath | Folder Path | OutArgument | `string` | The full file system path of the selected special folder. |

## Enum Reference

### System.Environment.SpecialFolder (common values)

| Value | Typical path |
|-------|-------------|
| `Desktop` | `C:\Users\<user>\Desktop` |
| `MyDocuments` | `C:\Users\<user>\Documents` |
| `ApplicationData` | `C:\Users\<user>\AppData\Roaming` |
| `LocalApplicationData` | `C:\Users\<user>\AppData\Local` |
| `ProgramFiles` | `C:\Program Files` |
| `System` | `C:\Windows\System32` |
| `Windows` | `C:\Windows` |
| `Temp` | User temporary folder |

See the full list in the [.NET documentation](https://learn.microsoft.com/dotnet/api/system.environment.specialfolder).

## XAML Example

```xml
<ui:GetEnvironmentFolder SpecialFolder="MyDocuments">
  <ui:GetEnvironmentFolder.FolderPath>
    <OutArgument x:TypeArguments="x:String">[documentsPath]</OutArgument>
  </ui:GetEnvironmentFolder.FolderPath>
</ui:GetEnvironmentFolder>
```

## Notes

- Returns the path as reported by the operating system; the folder is not guaranteed to exist if the OS profile is incomplete.
- On multi-user systems the returned path is always relative to the current user's profile.
