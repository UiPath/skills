# CreateValidationAction

Creates a validation task in Orchestrator and returns immediately without waiting (async — create only).

```xml
<uisad:CreateValidationAction
    x:TypeArguments="uisaseib:Invoices"
    ActionCatalogue="default_du_actions"
    ActionPriority="Medium"
    ActionTitle="[&quot;Validate Invoice&quot;]"
    AutomaticExtractionResults="[DocumentExtractedData]"
    CreatedValidationAction="[createdValidationAction]"
    DisplayName="Create Validation Action"
    OrchestratorBucketName="du_storage_bucket"
    OrchestratorFolderName="[&quot;Shared&quot;]" />
```

Key notes:
- `CreatedValidationAction` — output variable of type `uisad:CreatedValidationAction(Of T)` (e.g., `uisad:CreatedValidationAction(Of uisaseib:Invoices)`)
- Use this activity when the workflow needs to suspend between creating and waiting for the validation
