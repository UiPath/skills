# Download File from URL

`UiPath.Activities.System.FileOperations.DownloadFileFromUrl`

Use this activity to download any file from a given URL.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Url` | URL | `InArgument` | `string` | Yes | — | The full URL from which to download the file. |
| `ConflictResolution` | If file already exists | `InArgument` | `FileConflictBehavior` | No | `FileConflictBehavior.Rename` | Behaviour when a file with the same name already exists at the save location: `Replace`, `Skip`, or `Rename`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FileName` | Save file as | `InArgument` | `string` | No | — | Custom file name to use when saving. Leave empty to use the original file name from the URL. |
| `Timeout` | Timeout (seconds) | `InArgument` | `int?` | No | `600` | Duration in seconds to wait for the server to begin the download response before raising an error. Default is 600 seconds. |
| `UserAgentHeader` | User Agent | `InArgument` | `string` | No | — | Value for the HTTP `User-Agent` request header, used to identify the requesting party to the server. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ResponseAttachment` | Downloaded File | `OutArgument` | `ILocalResource` | Reference to the downloaded file saved on disk. |

## XAML Example

```xml
<ui2:DownloadFileFromUrl
    DisplayName="Download File from URL"
    Url="&quot;https://example.com/reports/monthly.xlsx&quot;"
    FileName="&quot;monthly_report.xlsx&quot;"
    ConflictResolution="FileConflictBehavior.Rename"
    Timeout="120"
    ResponseAttachment="[downloadedFile]" />
```

`xmlns:ui2="clr-namespace:UiPath.Activities.System.FileOperations;assembly=UiPath.System.Activities"`

## Notes

- The file is saved to the robot's working directory by default when no explicit save path is configured. Use `FileName` to specify a full path if a particular destination is required.
- `ConflictResolution` defaults to `Rename`, which appends a numeric suffix to avoid overwriting existing files.
- The `Timeout` applies only to the time waiting for the server to **start** streaming the response — it does not limit the total download duration.
- For servers that require a specific browser identity, set `UserAgentHeader` to a browser user-agent string.
