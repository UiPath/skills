# WaitForValidationAction

Waits for a previously created validation task to be completed by a human reviewer (async — wait only).

```xml
<uisad:WaitForValidationAction
    x:TypeArguments="uisaseib:Invoices"
    CreatedValidationAction="[createdValidationAction]"
    DisplayName="Wait For Validation Action"
    ValidatedExtractionResults="[DocumentExtractedData]" />
```

Key notes:
- `CreatedValidationAction` — input from `CreateValidationAction` output
- `ValidatedExtractionResults` — output `uisad2:IDocumentData(Of T)` after human validation
