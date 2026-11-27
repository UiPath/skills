# Create Document Validation Artifacts

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts.CreateDocumentValidationArtifacts`

Uploads document data, DOM, taxonomy, and extraction results to an Orchestrator storage bucket as validation artifacts. These artifacts can be used for external validation through UiPath Apps. Returns a `ContentValidationData` object to be passed to **Retrieve Document Validation Artifacts** after validation is complete.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AutomaticExtractionResults` | Document Data | InArgument | `IDocumentData<ExtendedExtractionResultsForDocumentData>` | Yes | | The extraction result, output of the Extract Document Data activity. |
| `OrchestratorFolderName` | Orchestrator folder | InArgument | `string` | | | Orchestrator folder where the storage bucket is located. |
| `OrchestratorBucketName` | Orchestrator bucket | InArgument | `string` | | `"DU_Validation"` | Orchestrator storage bucket to store documents and data required for validation. The bucket must exist in the target tenant. Do not set this property unless the user specifies a bucket name — omitting it uses the default. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContentValidationData` | Content Validation Data Object | OutArgument | `ContentValidationData` | Object containing references to the uploaded validation artifacts. Pass this to **Retrieve Document Validation Artifacts** after validation. |

## XAML Example

```xml
<duArt:CreateDocumentValidationArtifacts
    x:TypeArguments="du:ExtendedExtractionResultsForDocumentData"
    DisplayName="Create Document Validation Artifacts"
    AutomaticExtractionResults="[extractionResults]"

    ContentValidationData="[contentValidationData]" />
```

> Namespace prefix `duArt` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.
> Namespace prefix `du` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

### DictionaryData Variant

When using `DictionaryData` for the extraction pipeline (recommended for agent-generated workflows):

```xml
<duArt:CreateDocumentValidationArtifacts
    x:TypeArguments="du:DictionaryData"
    DisplayName="Create Document Validation Artifacts"
    AutomaticExtractionResults="[extractionResults]"

    ContentValidationData="[contentValidationData]" />
```

## Notes

- This is a generic activity. In XAML, use `x:TypeArguments="du:ExtendedExtractionResultsForDocumentData"` or `x:TypeArguments="du:DictionaryData"`.
- The type argument **must match** the type argument used in `ExtractDocumentDataWithDocumentData`.
- Use this activity together with **Retrieve Document Validation Artifacts** for external validation through UiPath Apps, as an alternative to the Action Center-based validation activities.
- The artifacts are stored in the specified Orchestrator storage bucket and can be consumed by a UiPath App for human review.
- In a typical pipeline, this activity follows Extract Document Data as an alternative to the Action Center validation path.
