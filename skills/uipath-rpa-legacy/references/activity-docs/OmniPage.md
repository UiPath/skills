# UiPath OmniPage OCR Activities - Legacy Reference

## Overview
OmniPage OCR engine for text extraction from images/documents. Package: `UiPath.OmniPage.Activities`. **#29 by adoption (1.12%)**.

---

## Activity: OmniPageOCR

### Input Arguments
| Argument | Type | Default | Notes |
|----------|------|---------|-------|
| `Image` | Image | REQUIRED | Image to OCR |
| `Language` | string | "auto" | BCP-47 code or "auto" for detection |
| `Profile` | OCRProfile | None | None, Screen, Scan, Legacy |
| `ExtractWords` | bool | false | Extract individual words |
| `ExtractHandprintedText` | bool | false | Handwriting extraction |
| `Scale` | double | 1.0 | Image scaling factor |
| `BundleType` | OmniPageBundleType | Basic | Basic or Extended bundle |

### Output Arguments
| Argument | Type | Notes |
|----------|------|-------|
| `Text` | string | Extracted text |

### OCR Profiles
- **None** - No preprocessing
- **Screen** - Optimized for screen captures (auto-set for screen scraping)
- **Scan** - Optimized for scanned documents (auto-set ComputeSkewAngle=true)
- **Legacy** - Legacy processing mode

### Bundle Types
- **Basic** - Standard OCR functionality
- **Extended** - Advanced features (requires Extended bundle installed)

---

## Critical Gotchas

### Installation
1. **CoreIPC 2.0.1+ REQUIRED** - throws InvalidOperationException at runtime if missing
2. **Bundle folder must be installed** - missing bundle causes validation error ("Bundle not installed")
3. **Extended bundle requires separate installation** - Basic bundle is default

### Compatibility
4. **Emgu (OpenCV) version incompatibility** - OmniPage v1.19.2+ required for UiPath 24.6+; validates against full list of incompatible package versions
5. **IOCR 6.19+, OCRActivities 3.20+ incompatible** with older OmniPage versions

### Configuration
6. **Language "auto" may produce suboptimal results** for mixed-language documents - set specific language
7. **Scale factor has no validation bounds** - very high/low values degrade accuracy
8. **ExtractHandprintedText significantly increases processing time** - disable if not needed
9. **Profile auto-selected for Document vs Screen** usage context:
   - Document: ComputeSkewAngle=true, Profile=Scan
   - Screen: ComputeSkewAngle=false, Profile=Screen
   - Manual override not exposed in scrape UI

### Performance
10. **Images automatically converted to PNG byte arrays** internally - no format control
11. **NoopExecution mode** exists (Browsable=false) - returns empty results without processing; for testing only
