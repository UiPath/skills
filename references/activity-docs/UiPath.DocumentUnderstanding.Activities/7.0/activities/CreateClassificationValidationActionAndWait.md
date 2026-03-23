# CreateClassificationValidationActionAndWait

Sends a low-confidence classification result to a human for correction.

```xml
<uisad1:CreateClassificationValidationActionAndWait
    ActionCatalogue="default_du_actions"
    ActionPriority="Medium"
    ActionTitle="[&quot;Validate Classification&quot;]"
    AutomaticClassificationResults="[DocumentData]"
    DisplayName="Create Classification Validation Task And Wait"
    OrchestratorBucketName="du_storage_bucket"
    OrchestratorFolderName="[&quot;Shared&quot;]"
    ValidatedClassificationResults="[DocumentData]" />
```

Key notes:
- `AutomaticClassificationResults` — input `uisad1:DocumentData` from `ClassifyDocument`
- `ValidatedClassificationResults` — output `uisad1:DocumentData`; can be the same variable as input
- Typically used inside an `If` checking `DocumentData.DocumentType.Confidence < 0.7`
