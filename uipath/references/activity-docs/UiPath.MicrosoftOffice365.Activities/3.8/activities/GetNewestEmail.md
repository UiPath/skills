# GetNewestEmail — Retrieve Single Email

Null attributes: `ConnectionAccountName`, `ContinueOnError`

```xml
<umam:GetNewestEmail
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    AuthScopesInvalid="False"
    BodyAsHtml="False"
    BrowserFolder="Inbox"
    BrowserFolderId="Inbox"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="Get Newest Email"
    FilterSelectionMode="ConditionBuilder"
    Importance="Any"
    MarkAsRead="False"
    Result="[email]"
    SelectionMode="Browse"
    UnreadOnly="False"
    UseConnectionService="True"
    UseSharedMailbox="False"
    WithAttachmentsOnly="False">
  <!-- Optional filter -->
  <umam:GetNewestEmail.Filter>
    <umamf:MailFilterCollection LogicalOperator="And">
      <umamf:MailFilterCollection.Filters>
        <umamf:MailFilterElement
            DateValue="{x:Null}"
            Criteria="Subject"
            StringOperator="Contains"
            InStringValue="[keyword]" />
      </umamf:MailFilterCollection.Filters>
    </umamf:MailFilterCollection>
  </umam:GetNewestEmail.Filter>
</umam:GetNewestEmail>
```

Output type: `umm:Office365Message`
