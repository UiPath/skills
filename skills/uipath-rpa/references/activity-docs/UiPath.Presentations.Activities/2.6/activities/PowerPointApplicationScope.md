# Use PowerPoint Presentation

`UiPath.Presentations.Activities.PowerPointApplicationScope`

Opens or creates a PowerPoint file for use in automation. Acts as a scope container for Windows-based PowerPoint activities that require an open presentation handle (`IPresentationQuickHandle`).

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `PresentationPath` | Path | InArgument | `string` | Yes | | | The path to the presentation |
| `Password` | Password | InArgument | `string` | | | | The password for opening the presentation, if needed |
| `EditPassword` | Edit password | InArgument | `string` | | | | The editing password, if needed |
| `SensitivityLabel` | Sensitivity label | InArgument | `object` | | | | String ID for the sensitivity label or an `IPptLabelObject` instance. Used only when `SensitivityOperation` is `Add` |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `AutoSave` | Save changes | `bool` | `true` | Saves the presentation after each PowerPoint activity that makes a change to its content |
| `CreateIfNotExists` | Create if not exists | `bool` | `true` | If the presentation cannot be found at the specified path, a new PowerPoint presentation is created. When cleared, an error is thrown instead |
| `ReadOnly` | Read only | `bool` | `false` | Opens the presentation in read-only mode. Enables data extraction from locked or edit-password-protected files |
| `SensitivityOperation` | Sensitivity operation | `PptLabelOperation` | `None` | Sensitivity label operation to apply when opening the presentation |

### Scope Reference

This is a scope activity. Child activities receive a presentation handle via a `DelegateInArgument<IPresentationQuickHandle>` defined inside the `Body` property. In the designer, this appears as the **Reference as** field (default: `"PowerPoint"`). In XAML, the reference name is serialized as the `Name` attribute of the `DelegateInArgument` element.

### Enum Reference

**`PptLabelOperation`**: `None` (No operation), `Add` (Add or update sensitivity label), `Clear` (Remove sensitivity label)

## XAML Example

```xml
<pres:PowerPointApplicationScope
    DisplayName="Use PowerPoint Presentation"
    PresentationPath="[&quot;C:\Presentations\report.pptx&quot;]"
    AutoSave="True">
    <pres:PowerPointApplicationScope.Body>
        <ActivityAction x:TypeArguments="pres:IPresentationQuickHandle">
            <ActivityAction.Argument>
                <DelegateInArgument x:TypeArguments="pres:IPresentationQuickHandle" Name="presentation" />
            </ActivityAction.Argument>
            <!-- Child activities go here, referencing [presentation] -->
        </ActivityAction>
    </pres:PowerPointApplicationScope.Body>
</pres:PowerPointApplicationScope>
```

## Notes

- Windows only — requires Desktop PowerPoint to be installed
- This is a scope activity: Windows-based PowerPoint activities that take `IPresentationQuickHandle` must be placed inside this scope
- The `DelegateInArgument` name (shown as "Reference as" in the designer) defines how child activities reference the presentation handle
- `SensitivityLabel` is only used when `SensitivityOperation` is `Add`
- `CreateIfNotExists` defaults to `true` — if the file doesn't exist, a new presentation is created
