# Exchange Scope

`UiPath.Mail.Exchange.Activities.ExchangeScope`

Connects to Exchange and provides a scope for other Exchange activities.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Server | Server | InArgument | string | Yes (overload: Server) | | The URL of the Exchange Web Services (EWS) endpoint. Mutually exclusive with EmailAutodiscover. |
| EmailAutodiscover | EmailAutodiscover | InArgument | string | Yes (overload: AutoDiscover) | | An email address used to automatically discover the Exchange server endpoint. Mutually exclusive with Server. |
| ExistingExchangeService | Existing Exchange Service | InArgument | ExchangeService | No (overload: ExistingConnection) | | An existing ExchangeService instance to reuse, allowing nested Exchange scopes to share a single authenticated connection. |
| User | User | InArgument | string | No | | The username or email address for Exchange server authentication. |
| Password | Password | InArgument | string | No | | The plain text password for Exchange server authentication. |
| SecurePassword | Secure password | InArgument | SecureString | No | | The password as a SecureString for Exchange server authentication. |
| Domain | Domain | InArgument | string | No | | The Windows domain for NTLM authentication with on-premises Exchange servers. |
| ApplicationId | ApplicationId | InArgument | string | No | | The Azure AD application (client) ID for Office 365 OAuth 2.0 authentication. |
| DirectoryId | DirectoryId | InArgument | string | No | | The Azure AD directory (tenant) ID for Office 365 OAuth 2.0 authentication. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the Exchange server to respond. |
| ContinueOnError | ContinueOnError | InArgument | bool | No | true | Specifies to continue executing the remaining activities even if the current activity failed. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| AuthenticationMode | AuthenticationType | AuthenticationType | Interactive | The authentication method to use: Interactive Token (OAuth 2.0), Integrated Windows Authentication, or Username/Password. |
| ExchangeVersion | ExchangeVersion | ExchangeVersion | Exchange2013 | The version of the Exchange server to target for protocol compatibility. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| ExchangeService | ExchangeService | ExchangeService | The output ExchangeService instance created by this scope. Can be passed to other Exchange scopes via ExistingExchangeService. |

## Scope Body

ExchangeScope is a `NativeActivity` with a `Body` (ActivityAction\<ExchangeService\>). Place child Exchange activities (CreateDraft, DeleteMail, GetExchangeMailMessages, MoveMessageToFolder, SaveExchangeAttachements, SendExchangeMail) inside the Body. Child activities automatically inherit the authenticated ExchangeService connection and do not need their own connection properties.

## XAML Example

```xml
<exc:ExchangeScope
    Server="https://outlook.office365.com/EWS/Exchange.asmx"
    User="user@contoso.com"
    Password="password"
    ExchangeVersion="Exchange2013">
  <exc:ExchangeScope.Body>
    <ActivityAction x:TypeArguments="ews:ExchangeService">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ews:ExchangeService" Name="ExchangeConnection" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <exc:GetExchangeMailMessages
            CustomFolder="Inbox"
            Top="[10]"
            Messages="[messages]" />
      </Sequence>
    </ActivityAction>
  </exc:ExchangeScope.Body>
</exc:ExchangeScope>
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- This is a scope activity: all Exchange child activities placed inside it inherit the authenticated connection and do not need their own connection configuration.
- Three connection overload groups exist (only one should be used at a time):
  - **Server**: Provide the EWS endpoint URL directly.
  - **AutoDiscover**: Provide an email address and Exchange will auto-discover the server endpoint.
  - **ExistingConnection**: Reuse an ExchangeService instance from a previous ExchangeScope.
- When using Office 365 OAuth 2.0 (`AuthenticationMode = Interactive`), `ApplicationId` is required. For non-interactive modes, both `ApplicationId` and `DirectoryId` must be provided together.
- `ExistingExchangeService` cannot be combined with credential properties (Domain, User, Password, SecurePassword).
- The output `ExchangeService` property can be captured and passed to another ExchangeScope via `ExistingExchangeService` to share an authenticated session.
- Related activities: CreateDraft, DeleteMail, GetExchangeMailMessages, MoveMessageToFolder, SaveExchangeAttachements, SendExchangeMail.
