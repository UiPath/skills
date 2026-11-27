# MoveOutlookMessage — Move Email to Folder

Null attribute: `Account`.

```xml
<ui:MoveOutlookMessage
    Account="{x:Null}"
    DisplayName="Move email to Invoices folder"
    MailFolder="Invoices"
    MailMessage="[currentEmail]" />
```

- `MailMessage`: binds a `snm:MailMessage` variable (e.g., loop iterator)
- `MailFolder`: destination folder name
