# Get Credential

`UiPath.Core.Activities.GetRobotCredential`

Gets a specified credential asset by using a provided Asset Name. If the credential asset is not global, it must be assigned to the local robot in order to be retrieved.

**Package:** `UiPath.System.Activities`
**Category:** Assets

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AssetName` | Asset Name | InArgument | `string` | No | — | The name of the Orchestrator credential asset to retrieve. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Username` | Username | OutArgument | `string` | The username component of the credential. |
| `Password` | Password | OutArgument | `SecureString` | The password component of the credential, returned as a `SecureString`. |

## XAML Example

```xml
<ui:GetRobotCredential
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Get Credential"
    AssetName="[&quot;SAPLoginCredential&quot;]"
    Username="{x:Reference sapUser}"
    Password="{x:Reference sapPassword}" />
```

## Notes

- Requires an active Orchestrator connection. The asset must be of type **Credential** in Orchestrator.
- For **Per Robot** credential assets, the asset must be assigned to the robot running the process.
- The `Password` is returned as a `SecureString`. Use `System.Net.NetworkCredential` to convert to plaintext when required by a downstream activity.
- `FolderPath` is available via the Orchestrator connection context (inherited from the base activity class) and can be configured in the activity's Orchestrator scope.
- To retrieve only a secret (no username), use **Get Secret** instead.
