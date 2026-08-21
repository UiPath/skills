# Retrieve Document Validation Artifacts

`UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts.RetrieveDocumentValidationArtifacts`

**XAML element:** `<duArt:RetrieveDocumentValidationArtifacts …>` *(not generic — no `x:TypeArguments`; the output is always `IDocumentData<DictionaryData>` because the data is deserialized from storage)*
**xmlns prefix:** `duArt` → `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`
**Pairs with:** Required completion of a `CreateDocumentValidationArtifacts<T>` upstream — `ContentValidationData` input comes from that activity's output. Also takes the `CompletedAppAction` returned by the UiPath App that performed the human review. Output `ValidatedExtractionResults` (`IDocumentData<DictionaryData>`) is the final reviewed data for downstream reads.

Retrieves completed validation artifacts from an Orchestrator storage bucket and reconstructs the validated extraction results. Used after a UiPath App-based validation flow has been completed.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ContentValidationData` | Content Validation Data Object | InArgument | `ContentValidationData` | Yes | | The output of the **Create Document Validation Artifacts** activity. |
| `CompletedAppAction` | Completed Action Object | InArgument | `object` | | | The completed action object from the UiPath App validation flow. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `RemoveDataFromStorage` | Remove Data From Storage | `bool` | `false` | If true, all associated data is deleted from the storage bucket after retrieval. |
| `ReturnAutomaticExtractionResults` | Return Automatic Extraction Results | `bool` | `false` | If true, returns the original automatic extraction results instead of the validated results. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ValidatedExtractionResults` | Document data | OutArgument | `IDocumentData<DictionaryData>` | Validated extracted data containing changes made by the reviewer, or automatic extraction results if `ReturnAutomaticExtractionResults` is true. |

## XAML Example

```xml
<duArt:RetrieveDocumentValidationArtifacts
    DisplayName="Retrieve Document Validation Artifacts"
    ContentValidationData="[contentValidationData]"
    CompletedAppAction="[completedAction]"
    RemoveDataFromStorage="[True]"
    ValidatedExtractionResults="[validatedResults]" />
```

> Namespace prefix `duArt` maps to `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`.

## Notes

- Use this activity after **Create Document Validation Artifacts** and a UiPath App-based validation flow.
- The output type is `IDocumentData<DictionaryData>` (not the generic `ExtendedExtractionResultsForDocumentData`), as the validated data is deserialized from storage in a generic format.
- Set `RemoveDataFromStorage` to `true` to clean up the storage bucket after retrieval.
- Set `ReturnAutomaticExtractionResults` to `true` if you want to skip the validated results and use the original automatic extraction instead.

## Supporting References

The `ValidatedExtractionResults` output is `IDocumentData<DictionaryData>` over the contracts `ExtractionResult` reconstructed from storage:

- [`ExtractionResultHandler`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) — fluent navigator. Reach it via `validatedResults.Data.Handler`.
- [`ExtractionResult`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) — the underlying data contract; covers validator notes, business-rule exceptions, and the `OperatorConfirmed` flag the App sets per field.
