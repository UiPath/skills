# Create Classification Validation Task and Wait

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.CreateClassificationValidationActionAndWait`

Creates a Classification Validation Task in Action Center to verify the classification results and suspends the workflow until the task is completed. After a human reviewer submits the validated classification, the workflow resumes with the corrected results.

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
| `ValidatedClassificationResults` | Document data | OutArgument | `DocumentData` | Validated classification data containing changes made by the reviewer in Classification Station. |

## XAML Example

```xml
<duVal:CreateClassificationValidationActionAndWait
    DisplayName="Create Classification Validation Task and Wait"
    AutomaticClassificationResults="[classificationResults]"
    ActionTitle="[&quot;Validate classification&quot;]"

    ValidatedClassificationResults="[validatedClassification]" />
```

> Namespace prefix `duVal` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

## Notes

- This is a **persistent activity**. The workflow suspends after creating the validation task and resumes only when the task is completed in Action Center. The project must have `"supportsPersistence": true` in `project.json` (under `"runtimeOptions"`). Without this, the workflow will fail at runtime.
- Cannot be placed inside a No Persist Scope.
- For a non-blocking alternative, use **Create Classification Validation Task** followed by **Wait for Classification Validation Task & Resume**.
- In a typical pipeline, this activity follows **Classify Document**. The `ValidatedClassificationResults` output (`DocumentData`) is passed as `FileInput` to **Extract Document Data**.
