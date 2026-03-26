# Google Cloud Vision OCR

`UiPath.Core.Activities.GoogleCloudOCR`

Extracts a string and its information from an indicated UI element using the Google Cloud Vision OCR engine. It can be used with other OCR activities (Click OCR Text, Hover OCR Text, Double Click OCR Text, Get OCR Text, Find OCR Text Position).

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.OCR.Engine

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `ApiKey` | ApiKey | InArgument | `string` |  |  |  | The API key used to provide you access to the Google Cloud Vision OCR. |

### Configuration

| Name | Display Name | Kind | Type | Default | Required | Description |
|------|-------------|------|------|---------|----------|-------------|
| `DetectionMode` | DetectionMode | Property | `GoogleCloudDetectionMode` |  |  | Indicates what detection flag to send to the Google Cloud Vision OCR. |
| `Region` | Region | InArgument | `GoogleCloudRegion` |  |  | The geographical region for the servers to be used for OCR |
| `ResizeToApiLimits` | ResizeToMaxLimitIfNecessary | Property | `bool` |  |  | When checked, the engine will attempt downsizing the image so as to have an acceptable size according to the Google Cloud Vision imposed limits |

## How to create a new Google Cloud Vision OCR

To generate the default XAML for this activity, run the following command:

```bash
uip rpa get-default-activity-xaml --activity-class-name UiPath.Core.Activities.GoogleCloudOCR
```
## Notes

- This is an OCR engine activity meant to be used within other OCR activities such as `Click OCR Text`, `Get OCR Text`, or `Find OCR Text Position`.
- A valid Google Cloud Vision API key is required.
- The `DetectionMode` property configures the type of text detection performed by Google Cloud Vision.
- The `Region` property allows you to specify which geographic region's servers to use for OCR processing.
- Enable `ResizeToMaxLimitIfNecessary` to automatically downsize large images to meet Google Cloud Vision API size limits.
