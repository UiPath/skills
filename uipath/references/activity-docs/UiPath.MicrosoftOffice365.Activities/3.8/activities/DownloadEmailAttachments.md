# DownloadEmailAttachments — Extract Attachments

Null attributes: `ConnectionAccountName`, `ContinueOnError`, `Filter`, `FilterByFileNames`, `NewResult`

```xml
<umam:DownloadEmailAttachments
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    Filter="{x:Null}"
    FilterByFileNames="{x:Null}"
    NewResult="{x:Null}"
    AuthScopesInvalid="False"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="Download Email Attachments"
    Email="[email]"
    ExcludeInlineAttachments="True"
    Result="[attachmentPaths]"
    SearchMode="UseSimple"
    UseConnectionService="True" />
```

- `Email`: binds a `umm:Office365Message` variable
- `Result`: `IEnumerable<string>` — saved attachment file paths
- `SearchMode`: `"UseSimple"` is the standard value
