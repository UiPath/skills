# ValidateDocumentDataWithDocumentData

Single activity that creates a validation task and waits synchronously for human review.

```xml
<uisad:ValidateDocumentDataWithDocumentData
    x:TypeArguments="uisaseib:Invoices"
    ActionCatalogue="default_du_actions"
    ActionPriority="Medium"
    ActionTitle="[&quot;Validate Invoice - &quot; + invoiceId]"
    AutomaticExtractionResults="[DocumentExtractedData]"
    DisplayName="Validate Document Data"
    OrchestratorBucketName="du_storage_bucket"
    OrchestratorFolderName="[&quot;Shared&quot;]"
    RemoveDataAfterProcessing="True"
    ValidatedExtractionResults="[DocumentExtractedData]" />
```

Key notes:
- `AutomaticExtractionResults` — input `uisad2:IDocumentData(Of T)` from the extraction step
- `ValidatedExtractionResults` — output `uisad2:IDocumentData(Of T)`; can be the same variable as input (overwrites)
- `ActionCatalogue` — Orchestrator action catalogue name (e.g., `"default_du_actions"`)
- `OrchestratorBucketName` — storage bucket for document data (e.g., `"du_storage_bucket"`)
- `RemoveDataAfterProcessing="True"` — cleans up document data after validation
