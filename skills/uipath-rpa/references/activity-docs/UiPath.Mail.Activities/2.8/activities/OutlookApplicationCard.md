# OutlookApplicationCard — Scope Container

All `umab:` activities must be nested inside `OutlookApplicationCard`. The scope handle type is `um:IMailQuickHandle`.

```xml
<umab:OutlookApplicationCard
    Account="user@example.com"
    AccountMismatchBehavior="UseDefaultEmailAccount"
    DisplayName="Open the Outlook desktop application">
  <umab:OutlookApplicationCard.Body>
    <ActivityAction x:TypeArguments="um:IMailQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="um:IMailQuickHandle" Name="Outlook" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- nested umab: activities here -->
      </Sequence>
    </ActivityAction>
  </umab:OutlookApplicationCard.Body>
</umab:OutlookApplicationCard>
```

The delegate argument name is `"Outlook"` by convention. Folder references use `Outlook.Folder("FolderName")`.
