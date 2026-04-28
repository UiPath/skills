# Compliance · AssistantWeb — product quirks

Product-specific CLI value conventions and error patterns for `productIdentifier: "AssistantWeb"`. Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md). This file lists only what's AssistantWeb-specific.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `AssistantWeb` (exact case) |
| Default license | `NoLicense` (AssistantWeb is tenant-level and cloud-native) |

## CLI value quirks — will cause 400 if wrong

### ⚠ `"yes"` / `"no"` strings (NOT booleans)

Same pattern as [assistant.md](assistant.md) — 7 user-override toggles. Pass `true`/`false` and the API rejects.

| Property | Accepted values |
|---|---|
| `allowTaskMining` | `"yes"` \| `"no"` |
| `enableGroupByFolder` | `"yes"` \| `"no"` |
| `allowActionCenter` | `"yes"` \| `"no"` |
| `switchToRunningTab` | `"yes"` \| `"no"` |
| `allowStudioWeb` | `"yes"` \| `"no"` |
| `showInstallButton` | `"yes"` \| `"no"` |
| `runAsMe` | `"yes"` \| `"no"` |

### Widget array

Same shape as Assistant's `widgets-edit-grid[]` — items require an `identifier` field (name+version concatenation).

## Error triage

| Error message fragment | Likely cause | Action |
|---|---|---|
| `allowTaskMining` / other yes/no field type mismatch | Passed as boolean | Halt. Coerce to `"yes"`/`"no"` in the pack. |
| Widget `identifier` missing | Array item built without name+version concat | Halt. Follow generate-data shape. |
