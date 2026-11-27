# Create Classification Validation Task

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.CreateClassificationValidationAction`

Creates a Classification Validation Task in Action Center to verify the classification results, without waiting for its completion. Returns a token that can be passed to the **Wait for Classification Validation Task & Resume** activity to later retrieve the validated results.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AutomaticClassificationResults` | Document Data | InArgument | `DocumentData` | Yes | | The classification result, output of the Classify Document activity. |
| `ActionTitle` | Action title | InArgument | `string` | Yes | | Title of the action as it appears in Action Center. |
| `ActionPriority` | Action priority | InArgument | `string` | | | Priority of the action. |
| `ActionCatalogue` | Action catalog | InArgument | `string` | | | Catalog where the action will be available in Action Center. |
| `OrchestratorFolderName` | Orchestrator folder | InArgument | `string` | | | Orchestrator folder where the action will be available. |
| `OrchestratorBucketName` | Orchestrator bucket | InArgument | `string` | | `"DU_Validation"` | Orchestrator storage bucket for documents and data required for validation. The bucket must exist in the target tenant. Do not set this property unless the user specifies a bucket name — omitting it uses the default. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `EnablePageReordering` | Enable Page Reordering | `bool` | `false` | Whether page reordering should be enabled in Classification Station. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CreatedClassificationValidationAction` | Created Classification Validation Task | OutArgument | `CreatedClassificationValidationAction` | Token representing the created classification validation task. Pass this to the **Wait for Classification Validation Task & Resume** activity. |

## XAML Example

```xml
<duVal:CreateClassificationValidationAction
    DisplayName="Create Classification Validation Task"
    AutomaticClassificationResults="[classificationResults]"
    ActionTitle="[&quot;Validate classification&quot;]"

    CreatedClassificationValidationAction="[createdClassificationAction]" />
```

> Namespace prefix `duVal` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

## Notes

- This activity does **not** suspend the workflow. Use **Wait for Classification Validation Task & Resume** to wait for task completion.
- The output `CreatedClassificationValidationAction` must be passed to **Wait for Classification Validation Task & Resume** to retrieve the validated results.
- In a typical pipeline, this activity follows **Classify Document**. The validated `DocumentData` output (from the subsequent Wait activity) is passed as `FileInput` to **Extract Document Data**.
