# ForEachEmailX — Iterate Emails in Folder

Requires **two** delegate arguments — `Argument1` (`snm:MailMessage`) and `Argument2` (`x:Int32` index):

```xml
<umab:ForEachEmailX
    DisplayName="For Each Email in Inbox"
    IncludeSubfolders="False"
    Mails="[Outlook.Folder(&quot;Inbox&quot;)]"
    NumberOfEmailsLimit="10"
    RetrieveAttachments="False"
    UnreadOnly="False"
    WithAttachmentsOnly="False">
  <umab:ForEachEmailX.Body>
    <ActivityAction x:TypeArguments="snm:MailMessage, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="snm:MailMessage" Name="CurrentMail" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Access email: CurrentMail.Subject, CurrentMail.SenderEmailAddress(), etc. -->
      </Sequence>
    </ActivityAction>
  </umab:ForEachEmailX.Body>
  <!-- Optional filter child -->
  <umab:ForEachEmailX.MailFilter>
    <umabf:MailFilterArgument LogicalOperator="And">
      <umabf:MailFilterArgument.Filters>
        <scg:List x:TypeArguments="umabf:SingleMailFilterArgument" Capacity="1">
          <umabf:SingleMailFilterArgument
              DateEqualsFilter="{x:Null}"
              Value="{x:Null}"
              Criteria="Date"
              DateFilter="Today"
              Operator="NewerThan" />
        </scg:List>
      </umabf:MailFilterArgument.Filters>
    </umabf:MailFilterArgument>
  </umab:ForEachEmailX.MailFilter>
</umab:ForEachEmailX>
```

- `Mails`: folder reference using delegate handle (e.g., `Outlook.Folder("Inbox")`)
- `NumberOfEmailsLimit`: `"0"` = no limit
- `MailFilter="{x:Null}"` when no filter is needed (omit the child element entirely)
- Without filter: set `MailFilter="{x:Null}"` as an attribute directly on `ForEachEmailX`
