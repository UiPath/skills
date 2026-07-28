---
confidence: medium
---

# Document Understanding — Document rejected at Validation Station

## Context

`Present Validation Station` (or a Validate Classification/Extraction step) faults with `UiPath.IntelligentOCR.Exceptions.DocumentRejectedByUserException` because a human reviewer **rejected** the document instead of confirming it. This is a deliberate business outcome surfaced as an exception, not a system/configuration fault.

What this looks like:

- `UiPath.IntelligentOCR.Exceptions.DocumentRejectedByUserException` — raised when the validation action result is "rejected." The exception carries a `DocumentRejectionReason` (the reason the reviewer picked) and an `Attributes` dictionary; the message reflects the rejection.

What can cause it:
- **Reviewer rejected the document** — the human in Validation Station marked it rejected (e.g. wrong document type, illegible, not processable, out of scope) rather than confirming the extracted data.

What to look for:
- The exception **type is `DocumentRejectedByUserException`** — the pipeline worked; a person chose to reject. The fix is workflow handling of rejection, not a technical repair. Read `DocumentRejectionReason` to understand *why* it was rejected.

> **Different cause — do not apply this playbook:**
> - `DUApiException` / tenant / storage errors are technical failures upstream of human validation → use the [license/endpoint](./du-license-or-endpoint-rejected.md), [tenant](./du-not-enabled-or-tenant-key.md), or [storage](./du-storage-or-taxonomy-missing.md) playbooks.

## Investigation

1. **Confirm the exception type** is `DocumentRejectedByUserException` and read `DocumentRejectionReason` / `Attributes`.
2. **Determine whether rejection is an expected path** for this process (some workflows route rejected documents to an exception queue / human follow-up) versus an unhandled fault.

## Resolution

- **If rejection is a valid business outcome:** handle `DocumentRejectedByUserException` in the workflow — catch it and route the document to the rejection path (exception queue, notification, manual handling) instead of letting the job fault. Do not treat it as a technical bug. (Apply workflow changes only with explicit user approval.)
- **If the rejection was unexpected:** review the `DocumentRejectionReason` with the reviewer — the document content/type or the extraction quality drove the rejection; address the upstream data quality or document routing.
