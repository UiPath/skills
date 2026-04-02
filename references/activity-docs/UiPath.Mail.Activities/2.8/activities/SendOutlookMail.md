# SendOutlookMail — Send Email via Outlook

Null attributes: `Account`, `Bcc`, `Cc`, `ContinueOnError`, `MailMessage`, `ReplyTo`, `TimeoutMS`.

```xml
<ui:SendOutlookMail
    Account="{x:Null}"
    Bcc="{x:Null}"
    Cc="{x:Null}"
    ContinueOnError="{x:Null}"
    MailMessage="{x:Null}"
    ReplyTo="{x:Null}"
    TimeoutMS="{x:Null}"
    Body="[EmailBody]"
    DisplayName="Send Outlook email"
    Importance="Normal"
    IsBodyHtml="False"
    IsDraft="False"
    Sensitivity="Normal"
    Subject="[EmailSubject]"
    To="[recipientAddress]"
    UseISConnection="True">
  <ui:SendOutlookMail.ConnectionDetailsBackupSlot>
    <usau:BackupSlot x:TypeArguments="umae:ConnectionDetails" StoredValue="{x:Null}">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umae:ConnectionDetails, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </ui:SendOutlookMail.ConnectionDetailsBackupSlot>
  <ui:SendOutlookMail.Files>
    <scg:List x:TypeArguments="InArgument(x:String)" Capacity="0" />
  </ui:SendOutlookMail.Files>
</ui:SendOutlookMail>
```

- `To`: string recipient address
- `Files`: child element — empty list when no attachments; populate with `InArgument(x:String)` items for attachments
- `Importance`: `"Normal"`, `"High"`, or `"Low"`
- `Sensitivity`: `"Normal"`, `"Personal"`, `"Private"`, or `"CompanyConfidential"`
