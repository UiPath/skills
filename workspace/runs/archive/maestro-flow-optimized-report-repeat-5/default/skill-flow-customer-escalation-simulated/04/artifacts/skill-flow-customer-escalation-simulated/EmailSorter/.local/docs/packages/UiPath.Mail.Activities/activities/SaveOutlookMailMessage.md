# Save Outlook Desktop Mail Message

`UiPath.Mail.Outlook.Activities.SaveOutlookMailMessage`

Saves an Outlook mail message.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The mail message to save. This activity works only for an Outlook mail message. |
| Folder | Folder | InArgument | string | Yes | | The full path to the folder where to save the mail message. |
| FileName | File name | InArgument | string | No | | The name of the saved file. If missing, the subject of the mail message is used as file name. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| ReplaceExisting | Replace existing | bool | `false` | If true, the existing file with the same name will be overwritten. |
| SaveAsType | Save as type | ESaveMessageAsType | `ESaveMessageAsType.OutlookMessageFormatUnicode` | The format to save the mail message. |

## XAML Example

```xml
<olm:SaveOutlookMailMessage
    MailMessage="[mailMessage]"
    Folder="C:\output\emails"
    FileName="my_email"
    ReplaceExisting="False"
    SaveAsType="OutlookMessageFormatUnicode" />
```

## Notes

- Windows only -- requires Outlook COM interop
- The [`MailMessage`](types/MailMessage.md) input must be a message previously retrieved from Outlook (e.g., via GetOutlookMailMessages)
- When `FileName` is not specified, the email subject is used as the file name
- The `SaveAsType` property controls the output format (e.g., .msg Unicode, .msg ANSI, .txt, .html, etc.)
- Set `ReplaceExisting` to true to overwrite files with the same name in the target folder
- Related activities: GetOutlookMailMessages, SaveOutlookAttachments
