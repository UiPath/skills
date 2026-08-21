# Create Validation Task

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.CreateValidationAction`

**XAML element:** `<duVal:CreateValidationAction x:TypeArguments="dux:DictionaryData" …>` *(generic — `x:TypeArguments` is required and must match the value used on `ExtractDocumentDataWithDocumentData`)*
**xmlns prefixes:** `duVal` → `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (the activity), `dux` → `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (the type argument)
**Pairs with:** Input `AutomaticExtractionResults` comes from `ExtractDocumentDataWithDocumentData.ExtractionResults`. Output `CreatedValidationAction<T>` **must** be paired with `WaitForValidationAction<T>` later in the flow. If you don't need the non-blocking split, use the single-step `ValidateDocumentDataWithDocumentData` (display name "Create Validation Task and Wait") instead.

Creates a Document Validation Task in Action Center to verify extracted document data, without waiting for its completion. Returns a token that can be passed to the **Wait for Validation Task and Resume** activity to later retrieve the validated results.

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
| `OrchestratorBucketName` | Orchestrator bucket | InArgument | `string` | | `"du_storage_bucket"` | Orchestrator storage bucket for documents and data required for validation. The bucket must exist in the target tenant. Do not set this property unless the user specifies a bucket name — omitting it uses the default (`SWConstants.DefaultBucketName`). |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FieldsValidationConfidence` | Extracted fields validation confidence % | `int?` | | Upper-limit confidence score for filtering extracted fields that need human review. |
| `EnableRTLControls` | Enable RTL controls | `bool` | `false` | Enable right-to-left controls in Validation Station. |
| `DisplayMode` | Display mode | `DisplayModeArgument` | `Classic` | Display mode for Validation Station. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CreatedValidationAction` | Created document validation task | OutArgument | `CreatedValidationAction<ExtendedExtractionResultsForDocumentData>` | Token representing the created validation task. Pass this to the **Wait for Validation Task and Resume** activity. |

## Enum Reference

**`DisplayModeArgument`**: `Classic`, `Compact`

## XAML Example

```xml
<duVal:CreateValidationAction
    x:TypeArguments="dux:ExtendedExtractionResultsForDocumentData"
    DisplayName="Create Validation Task"
    AutomaticExtractionResults="[extractionResults]"
    ActionTitle="[&quot;Validate extraction&quot;]"

    CreatedValidationAction="[createdValidationAction]" />
```

> Namespace prefix `duVal` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.
> Namespace prefix `dux` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

### DictionaryData Variant

When using `DictionaryData` for the extraction pipeline (recommended for agent-generated workflows):

```xml
<duVal:CreateValidationAction
    x:TypeArguments="dux:DictionaryData"
    DisplayName="Create Validation Task"
    AutomaticExtractionResults="[extractionResults]"
    ActionTitle="[&quot;Validate extraction&quot;]"

    CreatedValidationAction="[createdValidationAction]" />
```

**Required variable declarations:**

```xml
<Variable x:TypeArguments="dux:IDocumentData(dux:DictionaryData)" Name="extractionResults" />
<Variable x:TypeArguments="duVal:CreatedValidationAction(dux:DictionaryData)" Name="createdValidationAction" />
```

> Namespace prefix `dux` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`. Use this prefix consistently — do not introduce a separate `du` alias for the same namespace.

## Notes

- This activity does **not** suspend the workflow. Use **Wait for Validation Task and Resume** to wait for task completion.
- This is a generic activity. In XAML, use `x:TypeArguments="dux:ExtendedExtractionResultsForDocumentData"` or `x:TypeArguments="dux:DictionaryData"`.
- The type argument **must match** the type argument used in `ExtractDocumentDataWithDocumentData`. If extraction used `DictionaryData`, this activity must also use `DictionaryData`.
- The output `CreatedValidationAction` must be passed to **Wait for Validation Task and Resume** to retrieve the validated results.
- In a typical pipeline, this activity follows Extract Document Data and precedes Wait for Validation Task and Resume.

## Supporting References

The `AutomaticExtractionResults` input is `IDocumentData<T>` over the contracts `ExtractionResult`. To inspect or pre-process it before sending to validation:

- [`ExtractionResultHandler`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) — fluent navigator. Reach it via `extractionResults.Data.Handler`.
- [`ExtractionResult`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) — the underlying data contract.
