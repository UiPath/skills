# Get Asset

`UiPath.Core.Activities.GetRobotAsset`

Gets a specified asset by using a provided AssetName. If the asset is not global, it must be assigned to the local robot in order to be retrieved.

**Package:** `UiPath.System.Activities`
**Category:** Assets

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AssetName` | Asset Name | InArgument | `string` | No | — | The name of the Orchestrator asset to retrieve. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `CacheStrategy` | Cache Strategy | `CacheStrategyEnum` | — | Controls whether and how the retrieved asset value is cached locally during robot execution. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Value` | Value | OutArgument | `object` | The value of the asset. The runtime type depends on the asset type configured in Orchestrator (text, integer, boolean, or credential). |

## XAML Example

```xml
<ui:GetRobotAsset
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Get Asset"
    AssetName="[&quot;DatabaseConnectionString&quot;]"
    Value="{x:Reference assetValue}" />
```

## Notes

- Requires an active Orchestrator connection. The asset must exist in Orchestrator before this activity is executed.
- For **Per Robot** assets, the asset must be assigned to the robot running the process.
- The `Value` output is typed as `object`. Cast it to the expected type (e.g., `String`, `Integer`, `Boolean`) after retrieval.
- To retrieve a credential asset with separate `Username` and `Password` outputs, use **Get Credential** instead.
- To retrieve a secret asset as a `SecureString`, use **Get Secret** instead.
- `FolderPath` is available via the Orchestrator connection context (inherited from the base activity class) and can be configured in the activity's Orchestrator scope.
