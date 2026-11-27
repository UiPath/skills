# Wait for Classification Validation Task & Resume

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.WaitForClassificationValidationAction`

Waits for the completion of a Classification Validation Task (created by the **Create Classification Validation Task** activity) and resumes the workflow with the validated classification results.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CreatedClassificationValidationAction` | Created Classification Validation Task | InArgument | `CreatedClassificationValidationAction` | Yes | | The output of the **Create Classification Validation Task** activity. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ValidatedClassificationResults` | Document data | OutArgument | `DocumentData` | Validated classification data containing changes made by the reviewer in Classification Station. |

## XAML Example

```xml
<duVal:WaitForClassificationValidationAction
    DisplayName="Wait for Classification Validation Task"
    CreatedClassificationValidationAction="[createdClassificationAction]"
    ValidatedClassificationResults="[validatedClassification]" />
```

> Namespace prefix `duVal` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

## Notes

- This is a **persistent activity**. The workflow suspends while waiting for the validation task to be completed in Action Center. The project must have `"supportsPersistence": true` in `project.json` (under `"runtimeOptions"`). Without this, the workflow will fail at runtime.
- Cannot be placed inside a No Persist Scope.
- Must be used after a **Create Classification Validation Task** activity. The `CreatedClassificationValidationAction` input must come from that activity's output.
- In a typical pipeline, the `ValidatedClassificationResults` output (`DocumentData`) is passed as `FileInput` to **Extract Document Data**. `DocumentData` implements `IResource`, so it can be used directly.
