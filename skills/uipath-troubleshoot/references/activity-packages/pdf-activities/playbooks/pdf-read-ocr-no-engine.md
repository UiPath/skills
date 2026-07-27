---
confidence: high
---

# PDF — Read PDF With OCR: no/failed OCR engine

## Context

`Read PDF With OCR` (`ReadPDFWithOCR`) / `Read XPS With OCR` faults because no OCR engine is configured inside it, or the configured engine failed to digitize the document. Unlike `Read PDF Text` (which reads the embedded text layer with no engine), the OCR activities require an OCR engine activity dropped inside their body.

What this looks like:

- `No OCR Engine assigned.` (`System.ArgumentException`, resource `OCREngineException`) — the activity has no OCR engine activity inside it. **This fires at activity validation (CacheMetadata) — i.e. at design / `validate` / `build` / publish time, not as a runtime job fault.** It is normally caught in Studio or at publish, so it rarely reaches a *faulted Orchestrator job*; if you see it, the failure is at build/validation, not execution. The runtime job-fault for OCR is `Digitization failed ...` below.
- `Digitization failed with status <status> and error <code>: <detail>.` (resource `DigitizationFailedError`) — an OCR engine is present but digitization failed (engine error, unreachable OCR endpoint, unsupported/oversized input).
- `Invalid image dpi <value>` (`System.ArgumentException`, resource `InvalidImageDpiException`) — the `Image DPI` used for OCR is invalid (≤ 0 or non-numeric).

What can cause it:
- **No OCR engine inside the activity** — the activity body is empty; no engine (e.g. UiPath Document OCR, Tesseract, Omnipage, a cloud OCR) was added.
- **OCR engine failed at runtime** — the engine threw or the OCR endpoint/service it depends on was unreachable, mis-licensed, or rejected the document.
- **Bad DPI argument** — `Image DPI` resolved to an invalid value.

What to look for:
- `No OCR Engine assigned.` = a pure configuration gap (add an engine). `Digitization failed with status ...` = an engine is present but its execution failed — the `status`/`error`/`detail` name the engine-side problem.

> **Different cause — do not apply this playbook:**
> - A file-not-found / not-a-PDF `ArgumentException` is the input path, not the engine → use [pdf-file-not-found-or-not-pdf.md](./pdf-file-not-found-or-not-pdf.md).
> - If `Read PDF Text` (no OCR) fails, it does not use an OCR engine — triage as a read/corrupt-file issue instead.

## Investigation

1. **Read the message.** `No OCR Engine assigned.` → no engine inside the activity. `Digitization failed with status ...` → parse the `status`, `error`, and `detail` for the engine-side failure. `Invalid image dpi` → the DPI argument.
2. **For a digitization failure**, identify which OCR engine is inside the activity and whether it depends on a service/endpoint/license (e.g. a cloud OCR engine needing connectivity and entitlement).
3. **Confirm the engine's own prerequisites** are met on the robot host (engine package installed, endpoint reachable, license valid).

## Resolution

- **If `No OCR Engine assigned.`:** add an OCR engine activity (e.g. UiPath Document OCR / Tesseract / Omnipage / a cloud OCR engine) inside the `Read PDF With OCR` body and configure it.
- **If `Digitization failed with status ...`:** resolve the engine-side failure named in the `status`/`error`/`detail` — confirm the OCR engine/endpoint is reachable, licensed, and that the document is a supported type/size; retry transient engine/service errors.
- **If `Invalid image dpi <value>`:** set a valid positive `Image DPI`.
