# Set Secret

`UiPath.Core.Activities.SetSecret`

Updates the value of an indicated secret asset, that is already available in Orchestrator, be it a global or a Per Robot asset.

**Package:** `UiPath.System.Activities`
**Category:** Assets

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AssetName` | Secret asset name | InArgument | `string` | Yes | — | The name of the Orchestrator secret asset to update. |
| `SecretValue` | Secret | InArgument | `string` | Yes (Normal secret) | — | The new plaintext secret value. Use this or `SecureSecretValue`, not both. |
| `SecureSecretValue` | Secure secret | InArgument | `SecureString` | Yes (Secure secret) | — | The new secret value as a `SecureString`. Use this or `SecretValue`, not both. |

## Valid Configurations

`SecretValue` and `SecureSecretValue` are mutually exclusive overload groups:

| Configuration | Required properties |
|---|---|
| **Normal secret** | `AssetName`, `SecretValue` |
| **Secure secret** | `AssetName`, `SecureSecretValue` |

## XAML Example

```xml
<!-- Using plaintext secret -->
<ui:SetSecret
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Set Secret"
    AssetName="[&quot;ApiToken&quot;]"
    SecretValue="[newTokenValue]" />
```

```xml
<!-- Using SecureString secret -->
<ui:SetSecret
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Set Secret"
    AssetName="[&quot;ApiToken&quot;]"
    SecureSecretValue="[newSecureToken]" />
```

## Notes

- Requires an active Orchestrator connection. The secret asset must already exist in Orchestrator.
- For **Per Robot** secret assets, the asset must be assigned to the robot running the process.
- Prefer `SecureSecretValue` over `SecretValue` to avoid storing plaintext sensitive values in the workflow.
- `FolderPath` is available via the Orchestrator connection context (inherited from the base activity class) and can be configured in the activity's Orchestrator scope.
