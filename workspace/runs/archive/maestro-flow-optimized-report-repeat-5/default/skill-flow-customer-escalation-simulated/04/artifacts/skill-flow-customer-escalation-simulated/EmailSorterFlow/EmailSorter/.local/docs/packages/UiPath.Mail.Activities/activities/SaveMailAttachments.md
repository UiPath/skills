# Save Email Attachments

`UiPath.Mail.Activities.SaveMailAttachments`

Saves the email message attachments to the specified folder. If the folder doesn't exist, it is created. If no folder is specified, the downloads are saved in the project folder. Files in the specified folder with the same name as the attachments are overwritten.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Message | Message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The [`MailMessage`](types/MailMessage.md) whose attachments will be saved to disk. |
| FolderPath | FolderPath | InArgument | string | No | | The destination folder path where attachments will be saved. If the folder does not exist, it is created automatically. Defaults to the project folder. |
| Filter | Filter | InArgument | string | No | | A regex pattern to filter which attachments to save based on their file names. Only attachments whose full path matches the pattern are saved. Leave empty to save all attachments. |
| OverwriteExisting | OverwriteExisting | InArgument | bool | No | false | If true, existing files with the same name as an attachment will be overwritten. |
| ExcludeInlineAttachments | Exclude inline attachments | InArgument | bool | No | false | Indicates whether to exclude inline attachments (i.e., attachments embedded in the email body). |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Attachments | Attachments | IEnumerable\<string\> | The output collection of file paths for all saved attachments. |
| ResourceAttachments | Resource Attachments | IEnumerable\<ILocalResource\> | The output collection of ILocalResource references to the saved attachment files. |

## XAML Example

```xml
<mail:SaveMailAttachments
    Message="[mailMessage]"
    FolderPath="C:\Emails\Attachments"
    Filter=""
    OverwriteExisting="[True]"
    ExcludeInlineAttachments="[False]"
    Attachments="[savedPaths]" />
```

## Notes

- The `Message` property is required. The activity raises a validation error if it is not provided.
- When `ExcludeInlineAttachments` is false (the default), inline attachments embedded in the email body via alternate views and linked resources are also saved.
- The `Filter` property accepts a .NET regex pattern. The pattern is matched against the full file path of each attachment (folder path + file name).
- When `OverwriteExisting` is false (the default), duplicate file names will cause an error.
- The `ResourceAttachments` output is only populated if its expression is bound in the workflow.
- Related activities: SaveMail, GetMailMessageFromFile.
