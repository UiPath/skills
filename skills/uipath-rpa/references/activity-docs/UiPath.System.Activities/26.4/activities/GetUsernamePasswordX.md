# Get Username/Password

`UiPath.Activities.System.GetUsernamePasswordX`

Securely store and load usernames and passwords.

**Package:** `UiPath.System.Activities`
**Category:** System.Dialog
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| CredentialName | Credential Name | InArgument | `string` | No | — | The name used to look up the credential. Hidden in the designer by default; use `CredentialNameProperty` instead. |
| OrchestratorCredentialName | Orchestrator credential name | InArgument | `string` | No | — | The name of the credential asset stored in Orchestrator. |
| TimeoutInSeconds | Timeout (in seconds) | InArgument | `int` | No | — | How long to wait for user input before timing out. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| AppOrSite | App Or Site | `string` | — | A label identifying the application or site these credentials belong to, shown in the dialog prompt. |
| AutosubmitTimeoutSeconds | Autosubmit timeout seconds | `int` | `AutosubmitTimeout` | Number of seconds before the dialog auto-submits when credentials are pre-filled. |
| CredentialNameProperty | Credential Name Property | `string` | — | Design-time binding of the credential name; preferred over the `CredentialName` argument in the designer. |
| CredentialsSource | Credentials source | `CredentialSource` | `CredentialSource.CredentialsManager` | Where to load the credentials from (Windows Credential Manager, Orchestrator asset, or prompt). |
| ExistingCredentialWarning | Existing Credential Warning | `string` | — | Warning message displayed when a credential matching the given name already exists. |
| MissingCredentialWarning | Missing Credential Warning | `string` | — | Warning message displayed when no matching credential is found. |
| Password | Password | `string` | — | Design-time pre-fill for the password field. |
| UserName | User Name | `string` | — | Design-time pre-fill for the username field. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Credential | Credential | OutArgument | `PasswordCredentials` | The retrieved or entered credentials, containing both username and secure password. |

## Enum Reference

### CredentialSource

| Value | Description |
|-------|-------------|
| `CredentialsManager` | Load from the Windows Credential Manager |
| `Orchestrator` | Load from an Orchestrator credential asset |
| `Prompt` | Always show an interactive dialog to the user |

## XAML Example

```xml
<ui:GetUsernamePasswordX AppOrSite="MyApp"
                         CredentialsSource="CredentialsManager">
  <ui:GetUsernamePasswordX.Credential>
    <OutArgument x:TypeArguments="ui:PasswordCredentials">[myCredential]</OutArgument>
  </ui:GetUsernamePasswordX.Credential>
</ui:GetUsernamePasswordX>
```

## Notes

- This activity is only supported on Windows.
- The `Credential` output is a `PasswordCredentials` object whose `Password` property is a `SecureString`, keeping the secret out of plain memory.
- When `CredentialsSource` is `Orchestrator`, provide `OrchestratorCredentialName` to identify the asset.
- Hidden properties (`CredentialName`, `OrchestratorCredentialName`, `OrchestratorFolderPath`) are not visible in the Designer panel by default.
