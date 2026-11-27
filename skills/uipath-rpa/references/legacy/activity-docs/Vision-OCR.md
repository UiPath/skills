# UiPath Vision/OCR Activities - Legacy Reference

## Overview
OCR and document recognition with multiple engine support. Package: `UiPath.Vision.Activities`.

---

## OCR Engines

| Engine | Type | Requirements |
|--------|------|-------------|
| Microsoft Azure Computer Vision | Cloud | Azure API key + endpoint |
| Google Cloud Vision | Cloud | Google API key |
| ABBYY FRE / FRE12 | Local | ABBYY FineReader Engine installed |
| Tesseract (Legacy) | Local | Tesseract binaries (bundled or installed) |

## Key Classes
- `OCRInput` / `OCROutput` - Standard I/O models
- `NormalizedOcrResult` - Unified output (Region -> Line -> Word hierarchy)
- `VisionImage` - Bitmap wrapper with format detection
- `EnginePreprocessor` / `EnginePostProcessor` - Image pre/post processing

---

## Critical Gotchas

1. **Multiple engines with different accuracy/speed** - Azure/Google better for most cases; ABBYY best for structured docs
2. **Preprocessing critical** for OCR quality - deskew, contrast enhancement, noise removal
3. **Cloud engines require API keys** and network connectivity
4. **Local engines (ABBYY, Tesseract) require separate installation**
5. **Output normalization loses engine-specific metadata** (confidence scores vary by engine)
6. **Language support varies by engine** - check engine docs for supported languages
7. **Image DPI affects quality** - 300 DPI recommended minimum for OCR
8. **EmguCV (OpenCV wrapper)** used for image preprocessing
9. **Polly library** for retry/resilience on cloud API calls
10. **IPC/hosting model** for service isolation (OCR runs in separate process)
11. **ReadApiV3 models** for Microsoft Read API response mapping (async operation)
