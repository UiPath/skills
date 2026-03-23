# SaveMailAttachments — Save Attachments to Disk

Null attributes: `Attachments`, `ResourceAttachments`.

```xml
<ui:SaveMailAttachments
    Attachments="{x:Null}"
    ResourceAttachments="{x:Null}"
    DisplayName="Download attachments to folder"
    ExcludeInlineAttachments="False"
    FolderPath="[DestinationFolderPath]"
    Message="[currentEmail]"
    OverwriteExisting="False" />
```

- `Message`: binds a `snm:MailMessage` variable
- `FolderPath`: destination directory path
- `ExcludeInlineAttachments`: `"True"` to skip embedded images
