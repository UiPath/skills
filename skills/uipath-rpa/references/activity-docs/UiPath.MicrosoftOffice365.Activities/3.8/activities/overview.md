# XAML Outlook Mail Activities

Office 365 Outlook mail activity patterns for `UiPath.MicrosoftOffice365.Activities`. Always get full XAML from `uip rpa activities get-default-xaml` — this file covers confirmed namespace and attribute patterns from real workflows only.

## Package

`UiPath.MicrosoftOffice365.Activities`

## Triggers in this package

This package contains **integration triggers** (the `.Triggers` namespace segment marks them — e.g. `UiPath.MicrosoftOffice365.Activities.Mail.Triggers.NewEmailReceived`) covering Mail, Calendar, Files, and SharePoint. All return `isTrigger: true, triggerType: "integration"` from `uip rpa activities find` and require a `ConnectionId`. **Placement: strict** — first activity of the workflow's root `Sequence`, never inside `ui:TriggerScope`. Orchestrator + Integration Service subscribe externally and dispatch a fresh job per event. The `FilterExpression` property runs server-side — use it for any "fire only if X" logic. See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md).

## Key Email Type

`umm:Office365Message` — output of `GetNewestEmail` and `NewEmailReceived`; input to `DownloadEmailAttachments`.

```xml
<Variable x:TypeArguments="umm:Office365Message" Name="email" />
```

## Connection Pattern

All activities authenticate via:
```xml
ConnectionId="<guid>" UseConnectionService="True" AuthScopesInvalid="False"
```

Use `uip is connections list --output json` to obtain the connection GUID. If no O365 connection exists, create one: `uip is connections create <o365-connector-key>`. Verify it's active: `uip is connections ping <connection-id>`.

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Connection | `ConnectionId="<guid>" UseConnectionService="True" AuthScopesInvalid="False"` |
| `umm:` assembly | `assembly=UiPath.MicrosoftOffice365` — NOT `...Activities` |
| Trigger prefix | `umamt:NewEmailReceived` — requires `xmlns:umamt=...Mail.Triggers...` |
| Filter prefix | `umamf:MailFilterCollection` / `umamf:MailFilterElement` — requires `xmlns:umamf=...Mail.Filters...` |
| Email variable type | `umm:Office365Message` — used for `Result` in `GetNewestEmail`/`NewEmailReceived`; `Email` in `DownloadEmailAttachments` |
| Recipients | `<CSharpValue x:TypeArguments="scg:IEnumerable(x:String)">new string[]{"a@b.com"}</CSharpValue>` |
| FilterExpression booleans | Backtick-quoted: `` `true` ``, `` `false` `` |
| FilterExpression AND | `&amp;&amp;` (XML-escaped `&&`) |
| BackupSlot (SendMail) | `MailboxArg` child required; `AttachmentsArg` and `InputTypeArg` also needed — use `uip rpa activities get-default-xaml` for full structure |
| Full XAML | Always use `uip rpa activities get-default-xaml` for complete activity XAML |
