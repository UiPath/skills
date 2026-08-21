# Get Mail (Classic)

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.GetMail`

Retrieves emails from a mail folder using the classic Office 365 activity interface. Supports OData query filtering and ordering.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `Account` | Account | Input | `InArgument<string>` | No | | The account to use. |
| `MailFolder` | Mail Folder | Input | `InArgument<string>` | No | `Inbox` | The mail folder to retrieve emails from. |
| `EmailId` | Email ID | Options | `InArgument<string>` | No | | Ignores search criteria and returns an email with a specific ID. |
| `Query` | Query | Options | `InArgument<string>` | No | | An OData query to filter emails. |
| `Top` | Top | Options | `InArgument<int>` | No | | The maximum number of emails to retrieve. |
| `OnlyUnreadMessages` | Only Unread Messages | Options | `bool` | No | `True` | Retrieve only unread messages. |
| `OrderByDate` | Order By Date | Options | `EOrderByDate` | No | `NewestFirst` | Orders emails by received date. |
| `MarkAsRead` | Mark As Read | Options | `bool` | No | `False` | Whether to mark retrieved emails as read. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Results` | Results | Output | `OutArgument<Office365Message[]>` | The retrieved email messages. |

## Output Model

See [`Office365Message`](types/Office365Message.md) for the email object structure.

## Enum Reference

| Enum | Values |
|---|---|
| `EOrderByDate` | `NewestFirst`, `OldestFirst` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umam:GetMail
    MailFolder="Inbox" OnlyUnreadMessages="True" MarkAsRead="False"
    DisplayName="Get Mail" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- This is a classic activity. For new workflows, use `GetEmailListConnections` instead.
- Default mail folder is "Inbox".
