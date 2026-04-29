# Url

`UiPath.MobileAutomation.Activities.OpenUrl`

Open a certain URL in the current active web browser.

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Url` | Open URL | InArgument | `string` | Yes | | Open a certain URL in the current active web browser. |

## XAML Example

```xml
<ma:OpenUrl DisplayName="Open URL"
            Url="[&quot;https://www.example.com&quot;]" />
```

## Notes

- This activity opens a URL in the currently active web browser on the mobile device
- The browser must already be open and active
- For navigating to URLs in a specific browser app, use the Open DeepLink activity instead
- Must be used within a Mobile Device Connection scope
