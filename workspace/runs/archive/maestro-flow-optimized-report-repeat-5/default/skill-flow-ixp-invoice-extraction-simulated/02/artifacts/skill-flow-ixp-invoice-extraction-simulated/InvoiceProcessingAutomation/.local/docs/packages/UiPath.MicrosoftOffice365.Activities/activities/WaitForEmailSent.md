# Wait For Email Sent

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.WaitForEmailSent`

Suspends workflow execution and waits until an email is sent from the specified mailbox. This is a persistent (long-running) activity.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `MailboxArg` | Mailbox | | [`MailboxArgument`](components/MailboxArgument.md) | No | | Specifies the mailbox to use. See [MailboxArgument](components/MailboxArgument.md) for input modes. |
| `WithAttachmentsOnly` | With Attachments Only | | `InArgument<bool>` | No | `False` | Retrieve only emails with attachments. |
| `IncludeAttachments` | Include Attachments | | `InArgument<bool>` | No | `False` | Indicates if the email should contain the attachments. |

## Output Model

The activity returns an [`Office365Message`](types/Office365Message.md) as its result.

See [`Office365Message`](types/Office365Message.md) for the email object structure.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umam:WaitForEmailSent
    DisplayName="Wait For Email Sent" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- This is a persistent activity that suspends workflow execution until the trigger fires.
- Supports filtering via the `Filter` property (condition builder with variables).
- In debug mode, retrieves the most recent matching sent email instead of waiting.
