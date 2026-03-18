# SendMailConnections — Send Email

Null attributes: `ArgumentAttachmentPaths`, `AttachmentList`, `Bcc`, `Cc`, `ConnectionAccountName`, `ContinueOnError`

```xml
<umam:SendMailConnections
    ArgumentAttachmentPaths="{x:Null}"
    AttachmentList="{x:Null}"
    Bcc="{x:Null}"
    Cc="{x:Null}"
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    AttachmentInputMode="Existing"
    AuthScopesInvalid="False"
    Body="[emailBody]"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="Send Email"
    InputType="HTML"
    Subject="[emailSubject]"
    UseConnectionService="True"
    UseSharedMailbox="False">
  <!-- Recipients: IEnumerable<string> -->
  <umam:SendMailConnections.To>
    <InArgument x:TypeArguments="scg:IEnumerable(x:String)">
      <CSharpValue x:TypeArguments="scg:IEnumerable(x:String)">new string[]{"user@example.com"}</CSharpValue>
    </InArgument>
  </umam:SendMailConnections.To>
  <!-- BackupSlot children required for enum properties -->
  <umam:SendMailConnections.MailboxArg>
    <umamm:MailboxArgument SharedMailbox="{x:Null}" UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umam:SendMailConnections.MailboxArg>
</umam:SendMailConnections>
```

Additional BackupSlot children (get full structure from `uip rpa get-default-activity-xaml`):
- `AttachmentsArg` — type `umame:AttachmentInputMode`
- `InputTypeArg` — type `umame:BodyInputType`
