# Save Email Message

`UiPath.Mail.Activities.SaveMail`

Saves the email message to the specified path. If the folder doesn't exist, it is created. If the file name is specified instead, the email is saved in the project folder. Files in the specified folder with the same name as the messages are overwritten.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The [`MailMessage`](types/MailMessage.md) object to save to disk as an .eml file. |
| FilePath | FilePath | InArgument | string | Yes | | The destination file path where the email will be saved. If only a folder path is provided, a filename is automatically generated from the email subject. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Email | Email | ILocalResource | The output ILocalResource reference to the saved email file on disk. |

## XAML Example

```xml
<mail:SaveMail
    MailMessage="[mailMessage]"
    FilePath="C:\Emails\saved-email.eml"
    Email="[savedFileResource]" />
```

## Notes

- Both [`MailMessage`](types/MailMessage.md) and `FilePath` are required. The activity raises a validation error if either is missing.
- If the `FilePath` does not include a file extension, the activity treats it as a folder path and generates a filename from the email subject (truncated to 30 characters) with an `.eml` extension.
- If the subject is empty, a filename of the form `SavedEmail{GUID}.eml` is generated.
- The saved file uses the standard .eml (MIME) format.
- Related activities: GetMailMessageFromFile, SaveMailAttachments.
