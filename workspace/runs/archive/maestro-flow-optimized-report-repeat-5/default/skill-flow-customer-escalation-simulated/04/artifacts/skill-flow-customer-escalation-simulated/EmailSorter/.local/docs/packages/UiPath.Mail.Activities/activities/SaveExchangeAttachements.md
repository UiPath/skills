# Save Exchange Attachments

`UiPath.Mail.Exchange.Activities.SaveExchangeAttachements`

Save Exchange Attachments

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | No | | The [MailMessage](types/MailMessage.md) whose Exchange attachments will be downloaded and saved to disk. |
| FolderPath | FolderPath | InArgument | string | No | | The destination folder path where attachments will be saved. |

### Configuration

This activity does not have additional configuration properties.

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Files | Files | OutArgument\<IEnumerable\<string\>\> | The output collection of file paths for all saved attachments. |
| ResourceAttachments | Resource Attachments | OutArgument\<IEnumerable\<ILocalResource\>\> | The output collection of ILocalResource references to the saved attachment files. |

## XAML Example

```xml
<exc:SaveExchangeAttachements
    MailMessage="[mailMessage]"
    FolderPath="C:\Temp\Attachments"
    Files="[savedFiles]" />
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- ExchangeScope: when placed inside an ExchangeScope, the activity inherits the authenticated connection. When used standalone, connection properties from the base ExchangeActivity are used.
- The class name retains the original spelling "Attachements" (with an extra 'e') for backward compatibility.
- The `MailMessage` must be a [MailMessage](types/MailMessage.md) previously retrieved via `GetExchangeMailMessages` with attachment metadata intact.
- The `ResourceAttachments` output provides ILocalResource references, which is useful for passing attachments to other resource-aware activities.
- Related activities: GetExchangeMailMessages, ExchangeScope.
