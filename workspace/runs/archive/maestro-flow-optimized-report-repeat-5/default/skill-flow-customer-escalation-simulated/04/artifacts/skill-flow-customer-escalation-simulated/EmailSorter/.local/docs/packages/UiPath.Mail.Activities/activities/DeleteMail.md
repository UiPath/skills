# Delete Exchange Mail Message

`UiPath.Mail.Exchange.Activities.DeleteMail`

Deletes an Exchange email message.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The [MailMessage](types/MailMessage.md) object to delete from the Exchange server. Must be a message previously retrieved from Exchange. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| DeleteMode | DeleteMode | DeleteMode | MoveToDeletedItems | Specifies how the message is deleted: MoveToDeletedItems moves it to the Deleted Items folder, SoftDelete marks it for recovery, or HardDelete permanently removes it. |

### Output

This activity does not produce output properties.

## XAML Example

```xml
<exc:DeleteMail
    MailMessage="[mailMessage]"
    DeleteMode="MoveToDeletedItems" />
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- ExchangeScope: when placed inside an ExchangeScope, the activity inherits the authenticated connection. When used standalone, connection properties from the base ExchangeActivity are used.
- The `MailMessage` must be a [MailMessage](types/MailMessage.md) previously retrieved via `GetExchangeMailMessages`, since it relies on the Exchange item ID stored in the message headers.
- `DeleteMode` values: `MoveToDeletedItems` (default, reversible), `SoftDelete` (recoverable via server admin), `HardDelete` (permanent deletion).
- Related activities: GetExchangeMailMessages, MoveMessageToFolder, ExchangeScope.
