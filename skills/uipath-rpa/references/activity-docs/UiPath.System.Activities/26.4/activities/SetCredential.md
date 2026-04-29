# Set Credential

`UiPath.Core.Activities.SetCredential`

Updates the value of an indicated credential asset, that is already available in Orchestrator, be it a global or a Per Robot asset.

**Package:** `UiPath.System.Activities`
**Category:** Assets

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CredentialName` | Credential Asset Name | InArgument | `string` | Yes | — | The name of the Orchestrator credential asset to update. |
| `UserName` | Username | InArgument | `string` | Yes | — | The new username value to store in the credential asset. |
| `Password` | Password | InArgument | `string` | Yes (Normal password) | — | The new plaintext password value. Use this or `SecurePassword`, not both. |
| `SecurePassword` | Secure Password | InArgument | `SecureString` | Yes (Secure password) | — | The new password as a `SecureString`. Use this or `Password`, not both. |

## Valid Configurations

`Password` and `SecurePassword` are mutually exclusive overload groups:

| Configuration | Required properties |
|---|---|
| **Normal password** | `CredentialName`, `UserName`, `Password` |
| **Secure password** | `CredentialName`, `UserName`, `SecurePassword` |

## XAML Example

```xml
<!-- Using plaintext password -->
<ui:SetCredential
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Set Credential"
    CredentialName="[&quot;SAPLoginCredential&quot;]"
    UserName="[newUsername]"
    Password="[newPassword]" />
```

```xml
<!-- Using SecureString password -->
<ui:SetCredential
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Set Credential"
    CredentialName="[&quot;SAPLoginCredential&quot;]"
    UserName="[newUsername]"
    SecurePassword="[newSecurePassword]" />
```

## Notes

- Requires an active Orchestrator connection. The credential asset must already exist in Orchestrator.
- For **Per Robot** credential assets, the asset must be assigned to the robot running the process.
- Prefer `SecurePassword` over `Password` to avoid storing plaintext credentials in the workflow.
- `FolderPath` is available via the Orchestrator connection context (inherited from the base activity class) and can be configured in the activity's Orchestrator scope.
