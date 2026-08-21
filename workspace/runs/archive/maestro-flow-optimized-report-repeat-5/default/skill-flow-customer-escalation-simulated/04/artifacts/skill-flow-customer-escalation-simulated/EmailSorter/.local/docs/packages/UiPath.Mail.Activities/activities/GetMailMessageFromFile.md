# Get Mail Message from File

`UiPath.Mail.Activities.GetMailMessageFromFile`

Generate a mail message from an eml file.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| EmailFile | Email File | InArgument | IResource | Yes | | The .eml file resource to parse. The file must be in standard MIME format (RFC 822). |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| MailMessage | Mail Message | [UiPathMailMessage](types/UiPathMailMessage.md) | The output [`UiPathMailMessage`](types/UiPathMailMessage.md) object parsed from the .eml file, containing the email's full content including headers, body, and attachments. |

## XAML Example

```xml
<mail:GetMailMessageFromFile
    EmailFile="[emlFileResource]"
    MailMessage="[parsedMailMessage]" />
```

## Notes

- The `EmailFile` property is required. The activity raises a validation error if it is not provided.
- The input file must be in standard .eml (MIME / RFC 822) format.
- The output is a [`UiPathMailMessage`](types/UiPathMailMessage.md) (not `System.Net.Mail.MailMessage`), which extends the standard mail message with additional UiPath-specific functionality.
- The activity uses `EmlMessageParser` internally to parse the MIME content.
- Related activities: SaveMail, SaveMailAttachments.
