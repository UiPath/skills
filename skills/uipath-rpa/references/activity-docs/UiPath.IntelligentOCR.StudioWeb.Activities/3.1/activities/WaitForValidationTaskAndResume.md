# Wait for Validation Task and Resume

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.WaitForValidationAction`

Waits for the completion of a Document Validation Task (created by the **Create Validation Task** activity) and resumes the workflow with the validated extraction results.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CreatedValidationAction` | Created document validation task | InArgument | `CreatedValidationAction<ExtendedExtractionResultsForDocumentData>` | Yes | | The output of the **Create Validation Task** activity. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ValidatedExtractionResults` | Document data | OutArgument | `IDocumentData<ExtendedExtractionResultsForDocumentData>` | Validated extracted data containing changes made by the reviewer in Validation Station. |

## XAML Example

```xml
<duVal:WaitForValidationAction
    x:TypeArguments="du:ExtendedExtractionResultsForDocumentData"
    DisplayName="Wait for Validation Task and Resume"
    CreatedValidationAction="[createdValidationAction]"
    ValidatedExtractionResults="[validatedResults]" />
```

> Namespace prefix `duVal` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.
> Namespace prefix `du` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

### DictionaryData Variant

When using `DictionaryData` for the extraction pipeline (recommended for agent-generated workflows):

```xml
<duVal:WaitForValidationAction
    x:TypeArguments="du:DictionaryData"
    DisplayName="Wait for Validation Task and Resume"
    CreatedValidationAction="[createdValidationAction]"
    ValidatedExtractionResults="[validatedResults]" />
```

**Required variable declarations:**

```xml
<Variable x:TypeArguments="duVal:CreatedValidationAction(du:DictionaryData)" Name="createdValidationAction" />
<Variable x:TypeArguments="dux:IDocumentData(du:DictionaryData)" Name="validatedResults" />
```

## Notes

- This is a **persistent activity**. The workflow suspends while waiting for the validation task to be completed in Action Center. The project must have `"supportsPersistence": true` in `project.json` (under `"runtimeOptions"`). Without this, the workflow will fail at runtime.
- This is a generic activity. In XAML, use `x:TypeArguments="du:ExtendedExtractionResultsForDocumentData"` or `x:TypeArguments="du:DictionaryData"`.
- The type argument **must match** the type argument used in `ExtractDocumentDataWithDocumentData` and `CreateValidationAction`. All three must use the same `T`.
- Cannot be placed inside a No Persist Scope.
- Must be used after a **Create Validation Task** activity. The `CreatedValidationAction` input must come from that activity's output.
- In a typical pipeline, this is the final extraction validation step. The `ValidatedExtractionResults` output contains the human-reviewed data.
