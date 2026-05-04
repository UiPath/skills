# Get Secret

`UiPath.Core.Activities.GetSecret`

Gets a specified secret asset by using a provided Asset Name. If the secret asset is not global, it must be assigned to the local robot in order to be retrieved.

**Package:** `UiPath.System.Activities`
**Category:** Assets

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AssetName` | Asset Name | InArgument | `string` | No | — | The name of the Orchestrator secret asset to retrieve. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Secret` | Password | OutArgument | `SecureString` | The secret value retrieved from Orchestrator, returned as a `SecureString` to avoid exposing the plaintext value in memory. |

## XAML Example

```xml
<ui:GetSecret
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Get Secret"
    AssetName="[&quot;ApiToken&quot;]"
    Secret="{x:Reference apiToken}" />
```

## Notes

- Requires an active Orchestrator connection. The asset must be of type **Secret** in Orchestrator.
- Requires Orchestrator version 20.0 or later; an error is thrown at runtime if the connected Orchestrator version does not meet this minimum.
- For **Per Robot** secret assets, the asset must be assigned to the robot running the process.
- The secret is returned as a `SecureString` to minimize exposure of sensitive values. Use `System.Net.NetworkCredential` to convert to plaintext when required.
- `FolderPath` is available via the Orchestrator connection context (inherited from the base activity class) and can be configured in the activity's Orchestrator scope.
- To retrieve a credential with both `Username` and `Password` as separate outputs, use **Get Credential** instead.
