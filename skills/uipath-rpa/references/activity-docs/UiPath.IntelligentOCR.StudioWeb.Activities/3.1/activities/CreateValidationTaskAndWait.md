# Create Validation Task and Wait

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.ValidateDocumentDataWithDocumentData`

Creates a Document Validation Task in Action Center to verify extracted document data and suspends the workflow until the task is completed. After a human reviewer submits the validated data, the workflow resumes with the corrected extraction results.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AutomaticExtractionResults` | Document Data | InArgument | `IDocumentData<ExtendedExtractionResultsForDocumentData>` | Yes | | The extraction result, output of the Extract Document Data activity. |
| `ActionTitle` | Action title | InArgument | `string` | Yes | | Title of the action as it appears in Action Center. |
| `ActionPriority` | Action priority | InArgument | `string` | | | Priority of the action. |
| `ActionCatalogue` | Action catalog | InArgument | `string` | | | Catalog where the action will be available in Action Center. |
| `OrchestratorFolderName` | Orchestrator folder | InArgument | `string` | | | Orchestrator folder where the action will be available. |
| `OrchestratorBucketName` | Orchestrator bucket | InArgument | `string` | | `"DU_Validation"` | Orchestrator storage bucket for documents and data required for validation. The bucket must exist in the target tenant. Do not set this property unless the user specifies a bucket name — omitting it uses the default. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FieldsValidationConfidence` | Extracted fields validation confidence % | `int?` | | Upper-limit confidence score for filtering extracted fields that need human review. |
| `EnableRTLControls` | Enable RTL controls | `bool` | `false` | Enable right-to-left controls in Validation Station. |
| `DisplayMode` | Display mode | `DisplayModeArgument` | `Classic` | Display mode for Validation Station. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ValidatedExtractionResults` | Document data | OutArgument | `IDocumentData<ExtendedExtractionResultsForDocumentData>` | Validated extracted data containing changes made by the reviewer in Validation Station. |

## Enum Reference

**`DisplayModeArgument`**: `Classic`, `Compact`

## XAML Example

```xml
<duVal:ValidateDocumentDataWithDocumentData
    x:TypeArguments="du:ExtendedExtractionResultsForDocumentData"
    DisplayName="Create Validation Task and Wait"
    AutomaticExtractionResults="[extractionResults]"
    ActionTitle="[&quot;Validate extraction&quot;]"

    ValidatedExtractionResults="[validatedResults]" />
```

> Namespace prefix `duVal` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.
> Namespace prefix `du` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

### DictionaryData Variant

When using `DictionaryData` for the extraction pipeline (recommended for agent-generated workflows):

```xml
<duVal:ValidateDocumentDataWithDocumentData
    x:TypeArguments="du:DictionaryData"
    DisplayName="Create Validation Task and Wait"
    AutomaticExtractionResults="[extractionResults]"
    ActionTitle="[&quot;Validate extraction&quot;]"

    ValidatedExtractionResults="[validatedResults]" />
```

**Required variable declarations:**

```xml
<Variable x:TypeArguments="dux:IDocumentData(du:DictionaryData)" Name="extractionResults" />
<Variable x:TypeArguments="dux:IDocumentData(du:DictionaryData)" Name="validatedResults" />
```

## Notes

- This is a **persistent activity**. The workflow suspends after creating the validation task and resumes only when the task is completed in Action Center. The project must have `"supportsPersistence": true` in `project.json` (under `"runtimeOptions"`). Without this, the workflow will fail at runtime.
- This is a generic activity. In XAML, use `x:TypeArguments="du:ExtendedExtractionResultsForDocumentData"` or `x:TypeArguments="du:DictionaryData"`.
- The type argument **must match** the type argument used in `ExtractDocumentDataWithDocumentData`. If extraction used `DictionaryData`, this activity must also use `DictionaryData`.
- For a non-blocking alternative, use **Create Validation Task** followed by **Wait for Validation Task and Resume** to separate task creation from waiting.
- Cannot be placed inside a No Persist Scope.
- In a typical pipeline, this activity follows Extract Document Data. It combines the functionality of Create Validation Task + Wait for Validation Task and Resume into a single step.
