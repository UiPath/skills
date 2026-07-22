# OCR Activities Playbooks

**Overview:** [overview.md](./overview.md) — `UiPath.OCR.Activities` engines, local-server modes, and failure families
**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — routing by exception type and `OCRResultCode`

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| OCR Engine Config & Dependencies | Medium | Missing local-server package (CV/DU), missing `UiPath.CoreIPC`, incompatible OCR.Activities companion versions, unsupported engine, required `ApiKey`/`Endpoint` not supplied, or `Timeout must be a number greater than 0.` | [ocr-engine-config-and-dependencies.md](./playbooks/ocr-engine-config-and-dependencies.md) |
| OCR Endpoint & Authentication | Medium | `Invalid API key specified` (`UiPathOCRInvalidApiKey`), `endpoint is null or empty`, invalid CJK server config, non-2xx `Response indicates an error`, invalid/missing service response, or service-call timeout | [ocr-endpoint-and-authentication.md](./playbooks/ocr-endpoint-and-authentication.md) |
| OCR Input & Runtime | Medium | `No image input was provided`, unsupported rotation angle, `OCR timeout exceeded`, wrong scrape usage (`Usage must be Document/Screen`), or an empty/silent result | [ocr-input-and-runtime.md](./playbooks/ocr-input-and-runtime.md) |
