# UiPath ImageProcessing Activities - Legacy Reference

## Overview
Low-level image template matching and comparison via P/Invoke to native C++ libraries. Package: `UiPath.ImageProcessing`.

---

## Key Operations

| Method | Purpose | Key Parameters | Returns |
|--------|---------|----------------|---------|
| `Images.FindAll` | Locate template in image | target Bitmap, toFind Bitmap, threshold (0-1) | Collection\<TemplateMatch\> |
| `Images.FindFirst` | Find single match | target, toFind, threshold | TemplateMatch |
| `Images.Compare` | Image similarity score | image1, image2, CalculationMode | double (0-1) |
| `Images.AreDifferent` | Boolean difference check | image1, image2, checkRects, excludeRects | bool |

### TemplateMatch Properties
- Location (Point), Percentage (match confidence), Scale

---

## Critical Gotchas

1. **P/Invoke to native C++ DLL** - requires matching platform (x86/x64) and OS
2. **Bitmap must be kept in memory** during operation (LockBits/UnlockBits pattern)
3. **Threshold tuning critical** - too low = false positives, too high = missed matches
4. **Resolution-sensitive** - template matching fails on different screen resolutions
5. **Brightness/contrast sensitive** - minor UI changes can break matching
6. **No managed alternative** - difficult to debug native code issues
7. **FindMode**: Basic vs Enhanced algorithms (Enhanced slower but more accurate)
8. **templateScaleFactor** - adjust template size for different display scales (DPI awareness)
9. **CancellationToken support** for async cancellation
