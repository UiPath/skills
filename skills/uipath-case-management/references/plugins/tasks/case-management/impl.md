# case-management task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type case-management \
  --display-name "<display-name>" \
  --name "<case-name>" \
  --folder-path "<folder-path>" \
  --task-type-id "<entityKey>" \
  --should-run-only-once \
  --is-required \
  --output json
```

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type case-management \
  --display-name "Run Vendor Onboarding Sub-Case" \
  --name "VendorOnboarding" \
  --folder-path "Shared/Procurement" \
  --task-type-id "d4e5f6g7-8901-2345-abcd-456789012345" \
  --is-required \
  --output json
```

## Resulting JSON Shape

```json
{
  "id": "tsk00000006",
  "elementId": "el_0006",
  "type": "case-management",
  "displayName": "Run Vendor Onboarding Sub-Case",
  "data": {
    "name": "VendorOnboarding",
    "folderPath": "Shared/Procurement",
    "inputs": [ /* enriched */ ],
    "outputs": [ /* enriched */ ],
    "context": { "taskTypeId": "d4e5f6g7-8901-2345-abcd-456789012345" }
  },
  "isRequired": true
}
```

## Binding Inputs

Use `uip maestro case var bind` per [bindings-and-expressions.md](../../../bindings-and-expressions.md).

## Post-Add Validation

Capture `TaskId`. Confirm `type: "case-management"` and `data.context.taskTypeId` populated.

> Sub-case recursion is allowed by the schema but watch for circular references — a case cannot embed itself directly or transitively. If the sdd.md hints at recursion, flag for user review before binding.
