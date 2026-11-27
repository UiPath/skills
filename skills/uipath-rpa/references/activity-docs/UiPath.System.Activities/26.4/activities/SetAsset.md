# Set Asset

`UiPath.Core.Activities.SetAsset`

Updates the value of an indicated asset, that is already available in Orchestrator, be it a global or a Per Robot asset.

**Package:** `UiPath.System.Activities`
**Category:** Assets

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AssetName` | Asset Name | InArgument | `string` | Yes | — | The name of the Orchestrator asset to update. |
| `Value` | Value | InArgument | `object` | Yes | — | The new value to assign to the asset. Must be compatible with the asset's type configured in Orchestrator (text, integer, or boolean). |

## XAML Example

```xml
<ui:SetAsset
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Set Asset"
    AssetName="[&quot;LastRunTimestamp&quot;]"
    Value="[DateTime.Now.ToString()]" />
```

## Notes

- Requires an active Orchestrator connection. The asset must already exist in Orchestrator; this activity updates an existing asset's value and cannot create new assets.
- The asset type in Orchestrator determines which value types are accepted. Passing a value of the wrong type will cause a runtime error.
- For **Per Robot** assets, the asset must be assigned to the robot running the process.
- To update a credential asset (username and password), use **Set Credential** instead.
- To update a secret asset, use **Set Secret** instead.
- `FolderPath` is available via the Orchestrator connection context (inherited from the base activity class) and can be configured in the activity's Orchestrator scope.
