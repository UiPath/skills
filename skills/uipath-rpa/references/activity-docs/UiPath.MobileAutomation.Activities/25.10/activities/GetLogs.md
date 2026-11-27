# Get Logs

`UiPath.MobileAutomation.Activities.GetLogs`

Get logs for a log type

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Logging & Debugging

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AppendToLogFile` | AppendToLogFile | InArgument | `bool` | Yes | `true` | If the new logs should be appended to the file or to recreate the file |
| `LogFilePath` | LogFilePath | InArgument | `string` | Yes | | The file where the logs are written |
| `LogType` | Get Logs | InArgument | `string` | Yes | | Get logs for a log type |

## XAML Example

```xml
<ma:GetLogs DisplayName="Get Logs"
            LogType="[&quot;logcat&quot;]"
            LogFilePath="[&quot;C:\Logs\device.log&quot;]"
            AppendToLogFile="[True]" />
```

## Notes

- This activity retrieves logs from the mobile device for a specific log type
- Use Get Log Types activity to discover available log types first
- The logs are written to the specified file path
- When AppendToLogFile is True, new logs are appended to existing file content; when False, the file is recreated
