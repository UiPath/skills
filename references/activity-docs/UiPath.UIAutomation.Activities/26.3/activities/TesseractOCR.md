# Tesseract OCR

`UiPath.Core.Activities.GoogleOCR`

Extracts a string and its information from an indicated UI element using Tesseract OCR Engine. It can be used with other OCR activities (Click OCR Text, Hover OCR Text, Double Click OCR Text, Get OCR Text, Find OCR Text Position).

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.OCR.Engine

## Properties

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `AllowedCharacters` | AllowedCharacters | InArgument | `string` |  |  | The OCR engine extracts the given string according to the characters specified here. |
| `DeniedCharacters` | DeniedCharacters | InArgument | `string` |  |  | The OCR engine extracts the given string without taking into account the characters specified here. |
| `Invert` | Invert | InArgument | `bool` |  |  | If this check box is selected, the colors of the UI element are inverted before scraping. This is useful when the background is darker than the text color. |
| `Profile` | Profile | InArgument | `OCRProfile` |  |  | Choose a preprocessing profile for the specified image or UI element to achieve a better OCR read. The following options are available: None - does not apply a preprocessing profile; Screen - preprocessing suitable for remote desktop applications; Scan - preprocessing suitable for scanned files; Legacy - uses the engine's default settings for preprocessing images, this is the default option. |

## How to create a new Tesseract OCR

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.Core.Activities.GoogleOCR
```
## Notes

- This is an OCR engine activity meant to be used within other OCR activities such as `Click OCR Text`, `Get OCR Text`, or `Find OCR Text Position`.
- Tesseract OCR runs locally and does not require an API key or internet connection.
- Use `AllowedCharacters` and `DeniedCharacters` to filter the OCR output to specific character sets.
- The `Invert` option is useful when processing images with light text on dark backgrounds.
- The `Profile` option provides preprocessing optimizations for different input sources (screen captures, scanned documents, etc.).
