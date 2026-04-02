# UI Automation Coded API

- **Service accessor:** `uiAutomation`
- **Type:** `IUiAutomationAppService`
- **Package:** `UiPath.UIAutomation.Activities`

## Architecture

The UI Automation coded API is organized in two layers:

1. **Service layer (`IUiAutomationAppService`)** -- accessed via `uiAutomation`. Provides top-level operations such as `Attach`/`Open` (which return a `UiTargetApp` handle) and element-level actions that accept a `UiElement` directly (e.g., `Click(UiElement)`, `TypeInto(UiElement)`). Also contains global utilities like `SetRuntimeBrowser`, `KeyboardShortcut`, `TakeScreenshot`, `GetClipboard`/`SetClipboard`, and `WaitState`.

2. **Handle layer (`UiTargetApp`)** -- returned by `Attach`/`Open`. Represents an attached or opened application window. Methods on this handle accept targets by `string` name (Object Repository target name), `IElementDescriptor`, `TargetAnchorableModel`, or `RuntimeTarget`. `UiTargetApp` implements `IDisposable` and should be disposed when no longer needed. It also exposes indexers to convert a target name or element descriptor into a `TargetAnchorableModel`.

Every action method has both a synchronous variant and an `Async` variant (suffixed with `Async`) that returns `Task` or `Task<T>`.

## Auto-imported Namespaces

No additional namespaces are auto-imported beyond the defaults.

## IUiAutomationAppService Methods

### Attach

```csharp
UiTargetApp Attach(string screenName, string appName = "***", string appVersion = "***", NAppAttachMode appAttachMode = NAppAttachMode.ByInstance, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
Task<UiTargetApp> AttachAsync(string screenName, string appName = "***", string appVersion = "***", NAppAttachMode appAttachMode = NAppAttachMode.ByInstance, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
UiTargetApp Attach(string screenName, TargetAppOptions targetAppOptions, string appName = "***", string appVersion = "***");
Task<UiTargetApp> AttachAsync(string screenName, TargetAppOptions targetAppOptions, string appName = "***", string appVersion = "***");
UiTargetApp Attach(IScreenDescriptor screenDescriptor, NAppAttachMode appAttachMode = NAppAttachMode.ByInstance, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
Task<UiTargetApp> AttachAsync(IScreenDescriptor screenDescriptor, NAppAttachMode appAttachMode = NAppAttachMode.ByInstance, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
UiTargetApp Attach(IScreenDescriptor screenDescriptor, TargetAppOptions targetAppOptions);
Task<UiTargetApp> AttachAsync(IScreenDescriptor screenDescriptor, TargetAppOptions targetAppOptions);
UiTargetApp Attach(TargetAppModel targetApp, TargetAppOptions targetAppOptions = null);
Task<UiTargetApp> AttachAsync(TargetAppModel targetApp, TargetAppOptions targetAppOptions = null);
```

### Open

```csharp
UiTargetApp Open(string screenName, string appName = "***", string appVersion = "***", NAppOpenMode openMode = NAppOpenMode.IfNotOpen, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
Task<UiTargetApp> OpenAsync(string screenName, string appName = "***", string appVersion = "***", NAppOpenMode openMode = NAppOpenMode.IfNotOpen, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
UiTargetApp Open(string screenName, TargetAppOptions targetAppOptions, string appName = "***", string appVersion = "***");
Task<UiTargetApp> OpenAsync(string screenName, TargetAppOptions targetAppOptions, string appName = "***", string appVersion = "***");
UiTargetApp Open(IScreenDescriptor screenDescriptor, NAppOpenMode openMode = NAppOpenMode.IfNotOpen, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
Task<UiTargetApp> OpenAsync(IScreenDescriptor screenDescriptor, NAppOpenMode openMode = NAppOpenMode.IfNotOpen, NWindowResize windowResize = NWindowResize.None, NInteractionMode interactionMode = NInteractionMode.HardwareEvents);
UiTargetApp Open(IScreenDescriptor screenDescriptor, TargetAppOptions targetAppOptions);
Task<UiTargetApp> OpenAsync(IScreenDescriptor screenDescriptor, TargetAppOptions targetAppOptions);
UiTargetApp Open(TargetAppModel targetApp, TargetAppOptions targetAppOptions = null);
Task<UiTargetApp> OpenAsync(TargetAppModel targetApp, TargetAppOptions targetAppOptions = null);
```

### KeyboardShortcut

```csharp
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(KeyboardShortcutOptions keyboardShortcutOptions);
```

### TakeScreenshot

```csharp
void TakeScreenshot(TakeScreenshotOptions takeScreenshotOptions);
Task TakeScreenshotAsync(TakeScreenshotOptions takeScreenshotOptions);
```

### Click

```csharp
void Click(UiElement uiElement, ClickOptions clickOptions = null);
Task ClickAsync(UiElement uiElement, ClickOptions clickOptions = null);
```

### Highlight

```csharp
void Highlight(UiElement uiElement, HighlightOptions highlightOptions = null);
Task HighlightAsync(UiElement uiElement, HighlightOptions highlightOptions = null);
```

### TypeInto

```csharp
void TypeInto(UiElement uiElement, TypeIntoOptions typeIntoOptions);
Task TypeIntoAsync(UiElement uiElement, TypeIntoOptions typeIntoOptions);
```

### Hover

```csharp
void Hover(UiElement uiElement, HoverOptions hoverOptions = null);
Task HoverAsync(UiElement uiElement, HoverOptions hoverOptions = null);
```

### GetText

```csharp
string GetText(UiElement uiElement, GetTextOptions options = null);
Task<string> GetTextAsync(UiElement uiElement, GetTextOptions options = null);
```

### SelectItem

```csharp
void SelectItem(UiElement uiElement, SelectItemOptions options);
Task SelectItemAsync(UiElement uiElement, SelectItemOptions options);
```

### GetUiElement

```csharp
UiElement GetUiElement(RuntimeTarget target);
Task<UiElement> GetUiElementAsync(RuntimeTarget target);
```

### SetDefaultRuntimeBrowser

```csharp
void SetDefaultRuntimeBrowser();
Task SetDefaultRuntimeBrowserAsync();
```

### SetRuntimeBrowser

```csharp
void SetRuntimeBrowser(NBrowserType browserType);
Task SetRuntimeBrowserAsync(NBrowserType browserType);
void SetRuntimeBrowser(SetRuntimeBrowserOptions setRuntimeBrowserOptions);
Task SetRuntimeBrowserAsync(SetRuntimeBrowserOptions setRuntimeBrowserOptions);
```

### GetClipboard

```csharp
string GetClipboard(GetClipboardOptions options);
Task<string> GetClipboardAsync(GetClipboardOptions options);
```

### SetClipboard

```csharp
void SetClipboard(SetClipboardOptions setClipboardOptions);
Task SetClipboardAsync(SetClipboardOptions setClipboardOptions);
```

### WaitState

```csharp
bool WaitState(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
Task<bool> WaitStateAsync(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
```

## UiTargetApp Methods

`UiTargetApp` implements `IDisposable`. Use `using` blocks or call `Dispose()` when finished.

### Indexers

```csharp
TargetAnchorableModel this[string target] { get; }
TargetAnchorableModel this[IElementDescriptor elementDescriptor] { get; }
```

### Click

```csharp
void Click(string target, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left);
Task ClickAsync(string target, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left);
void Click(string target, ClickOptions clickOptions);
Task ClickAsync(string target, ClickOptions clickOptions);
void Click(IElementDescriptor elementDescriptor, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left);
Task ClickAsync(IElementDescriptor elementDescriptor, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left);
void Click(IElementDescriptor elementDescriptor, ClickOptions clickOptions);
Task ClickAsync(IElementDescriptor elementDescriptor, ClickOptions clickOptions);
void Click(TargetAnchorableModel target, ClickOptions clickOptions = null);
Task ClickAsync(TargetAnchorableModel target, ClickOptions clickOptions = null);
void Click(RuntimeTarget target, ClickOptions clickOptions = null);
Task ClickAsync(RuntimeTarget target, ClickOptions clickOptions = null);
```

### MouseScroll

```csharp
void MouseScroll(string target, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultDistanceMovementUnits);
Task MouseScrollAsync(string target, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultDistanceMovementUnits);
void MouseScroll(string target, string searchedTarget, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultToElementMovementUnits);
Task MouseScrollAsync(string target, string searchedTarget, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultToElementMovementUnits);
void MouseScroll(string target, MouseScrollOptions mouseScrollOptions);
Task MouseScrollAsync(string target, MouseScrollOptions mouseScrollOptions);
void MouseScroll(IElementDescriptor elementDescriptor, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultDistanceMovementUnits);
Task MouseScrollAsync(IElementDescriptor elementDescriptor, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultDistanceMovementUnits);
void MouseScroll(IElementDescriptor elementDescriptor, IElementDescriptor searchedElementDescriptor, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultToElementMovementUnits);
Task MouseScrollAsync(IElementDescriptor elementDescriptor, IElementDescriptor searchedElementDescriptor, NScrollDirection direction = NScrollDirection.Down, int movementUnits = Constants.MouseScrollDefaultToElementMovementUnits);
void MouseScroll(IElementDescriptor elementDescriptor, MouseScrollOptions mouseScrollOptions);
Task MouseScrollAsync(IElementDescriptor elementDescriptor, MouseScrollOptions mouseScrollOptions);
void MouseScroll(TargetAnchorableModel target);
Task MouseScrollAsync(TargetAnchorableModel target);
void MouseScroll(TargetAnchorableModel target, string searchedTarget);
Task MouseScrollAsync(TargetAnchorableModel target, string searchedTarget);
void MouseScroll(TargetAnchorableModel target, MouseScrollOptions mouseScrollOptions);
Task MouseScrollAsync(TargetAnchorableModel target, MouseScrollOptions mouseScrollOptions);
void MouseScroll(RuntimeTarget target, MouseScrollOptions mouseScrollOptions);
Task MouseScrollAsync(RuntimeTarget target, MouseScrollOptions mouseScrollOptions);
```

### GetText

```csharp
string GetText(string target);
Task<string> GetTextAsync(string target);
string GetText(string target, GetTextOptions getTextOptions);
Task<string> GetTextAsync(string target, GetTextOptions getTextOptions);
string GetText(IElementDescriptor elementDescriptor);
Task<string> GetTextAsync(IElementDescriptor elementDescriptor);
string GetText(IElementDescriptor elementDescriptor, GetTextOptions getTextOptions);
Task<string> GetTextAsync(IElementDescriptor elementDescriptor, GetTextOptions getTextOptions);
string GetText(TargetAnchorableModel target, GetTextOptions getTextOptions = null);
Task<string> GetTextAsync(TargetAnchorableModel target, GetTextOptions getTextOptions = null);
string GetText(RuntimeTarget target, GetTextOptions getTextOptions = null);
Task<string> GetTextAsync(RuntimeTarget target, GetTextOptions getTextOptions = null);
```

### TypeInto

```csharp
void TypeInto(string target, string text);
Task TypeIntoAsync(string target, string text);
void TypeInto(string target, SecureString secureText);
Task TypeIntoAsync(string target, SecureString secureText);
void TypeInto(string target, TypeIntoOptions typeIntoOptions);
Task TypeIntoAsync(string target, TypeIntoOptions typeIntoOptions);
void TypeInto(IElementDescriptor elementDescriptor, string text);
Task TypeIntoAsync(IElementDescriptor elementDescriptor, string text);
void TypeInto(IElementDescriptor elementDescriptor, SecureString secureText);
Task TypeIntoAsync(IElementDescriptor elementDescriptor, SecureString secureText);
void TypeInto(IElementDescriptor elementDescriptor, TypeIntoOptions typeIntoOptions);
Task TypeIntoAsync(IElementDescriptor elementDescriptor, TypeIntoOptions typeIntoOptions);
void TypeInto(TargetAnchorableModel target, string text);
Task TypeIntoAsync(TargetAnchorableModel target, string text);
void TypeInto(TargetAnchorableModel target, SecureString secureText);
Task TypeIntoAsync(TargetAnchorableModel target, SecureString secureText);
void TypeInto(TargetAnchorableModel target, TypeIntoOptions typeIntoOptions);
Task TypeIntoAsync(TargetAnchorableModel target, TypeIntoOptions typeIntoOptions);
void TypeInto(RuntimeTarget target, TypeIntoOptions typeIntoOptions);
Task TypeIntoAsync(RuntimeTarget target, TypeIntoOptions typeIntoOptions);
```

### TakeScreenshot

```csharp
void TakeScreenshot(string target, string fileName);
Task TakeScreenshotAsync(string target, string fileName);
void TakeScreenshot(string target, TakeScreenshotOptions takeScreenshotOptions);
Task TakeScreenshotAsync(string target, TakeScreenshotOptions takeScreenshotOptions);
void TakeScreenshot(IElementDescriptor elementDescriptor, string fileName);
Task TakeScreenshotAsync(IElementDescriptor elementDescriptor, string fileName);
void TakeScreenshot(IElementDescriptor elementDescriptor, TakeScreenshotOptions takeScreenshotOptions);
Task TakeScreenshotAsync(IElementDescriptor elementDescriptor, TakeScreenshotOptions takeScreenshotOptions);
void TakeScreenshot(TargetAnchorableModel target, string fileName);
Task TakeScreenshotAsync(TargetAnchorableModel target, string fileName);
void TakeScreenshot(TargetAnchorableModel target, TakeScreenshotOptions takeScreenshotOptions);
Task TakeScreenshotAsync(TargetAnchorableModel target, TakeScreenshotOptions takeScreenshotOptions);
void TakeScreenshot(RuntimeTarget target, TakeScreenshotOptions takeScreenshotOptions);
Task TakeScreenshotAsync(RuntimeTarget target, TakeScreenshotOptions takeScreenshotOptions);
```

### SelectItem

```csharp
void SelectItem(string target, string item);
Task SelectItemAsync(string target, string item);
void SelectItem(string target, SelectItemOptions selectItemOptions);
Task SelectItemAsync(string target, SelectItemOptions selectItemOptions);
void SelectItem(IElementDescriptor elementDescriptor, string item);
Task SelectItemAsync(IElementDescriptor elementDescriptor, string item);
void SelectItem(IElementDescriptor elementDescriptor, SelectItemOptions selectItemOptions);
Task SelectItemAsync(IElementDescriptor elementDescriptor, SelectItemOptions selectItemOptions);
void SelectItem(TargetAnchorableModel target, string item);
Task SelectItemAsync(TargetAnchorableModel target, string item);
void SelectItem(TargetAnchorableModel target, SelectItemOptions selectItemOptions);
Task SelectItemAsync(TargetAnchorableModel target, SelectItemOptions selectItemOptions);
void SelectItem(RuntimeTarget target, SelectItemOptions selectItemOptions);
Task SelectItemAsync(RuntimeTarget target, SelectItemOptions selectItemOptions);
```

### SAPClickToolbarButton

```csharp
void SAPClickToolbarButton(string target, string button);
Task SAPClickToolbarButtonAsync(string target, string button);
void SAPClickToolbarButton(string target, SelectItemOptions selectItemOptions);
Task SAPClickToolbarButtonAsync(string target, SelectItemOptions selectItemOptions);
void SAPClickToolbarButton(IElementDescriptor elementDescriptor, string button);
Task SAPClickToolbarButtonAsync(IElementDescriptor elementDescriptor, string button);
void SAPClickToolbarButton(IElementDescriptor elementDescriptor, SelectItemOptions selectItemOptions);
Task SAPClickToolbarButtonAsync(IElementDescriptor elementDescriptor, SelectItemOptions selectItemOptions);
void SAPClickToolbarButton(TargetAnchorableModel target, string item);
Task SAPClickToolbarButtonAsync(TargetAnchorableModel target, string item);
void SAPClickToolbarButton(TargetAnchorableModel target, SelectItemOptions selectItemOptions);
Task SAPClickToolbarButtonAsync(TargetAnchorableModel target, SelectItemOptions selectItemOptions);
void SAPClickToolbarButton(RuntimeTarget target, SelectItemOptions selectItemOptions);
Task SAPClickToolbarButtonAsync(RuntimeTarget target, SelectItemOptions selectItemOptions);
```

### Check

```csharp
void Check(string target, NCheckType checkType = NCheckType.Check);
Task CheckAsync(string target, NCheckType checkType = NCheckType.Check);
void Check(string target, CheckOptions checkOptions);
Task CheckAsync(string target, CheckOptions checkOptions);
void Check(IElementDescriptor elementDescriptor, NCheckType checkType = NCheckType.Check);
Task CheckAsync(IElementDescriptor elementDescriptor, NCheckType checkType = NCheckType.Check);
void Check(IElementDescriptor elementDescriptor, CheckOptions checkOptions);
Task CheckAsync(IElementDescriptor elementDescriptor, CheckOptions checkOptions);
void Check(TargetAnchorableModel target, CheckOptions checkOptions = null);
Task CheckAsync(TargetAnchorableModel target, CheckOptions checkOptions = null);
void Check(RuntimeTarget target, CheckOptions checkOptions = null);
Task CheckAsync(RuntimeTarget target, CheckOptions checkOptions = null);
```

### IsEnabled

```csharp
bool IsEnabled(string target);
Task<bool> IsEnabledAsync(string target);
bool IsEnabled(string target, IsEnabledOptions isEnabledOptions);
Task<bool> IsEnabledAsync(string target, IsEnabledOptions isEnabledOptions);
bool IsEnabled(IElementDescriptor elementDescriptor);
Task<bool> IsEnabledAsync(IElementDescriptor elementDescriptor);
bool IsEnabled(IElementDescriptor elementDescriptor, IsEnabledOptions isEnabledOptions);
Task<bool> IsEnabledAsync(IElementDescriptor elementDescriptor, IsEnabledOptions isEnabledOptions);
bool IsEnabled(TargetAnchorableModel target, IsEnabledOptions isEnabledOptions = null);
Task<bool> IsEnabledAsync(TargetAnchorableModel target, IsEnabledOptions isEnabledOptions = null);
bool IsEnabled(RuntimeTarget target, IsEnabledOptions isEnabledOptions = null);
Task<bool> IsEnabledAsync(RuntimeTarget target, IsEnabledOptions isEnabledOptions = null);
```

### WaitState

```csharp
bool WaitState(string target, NCheckStateMode checkStateMode, double timeout);
Task<bool> WaitStateAsync(string target, NCheckStateMode checkStateMode, double timeout);
bool WaitState(string target, CheckStateOptions checkStateOptions);
Task<bool> WaitStateAsync(string target, CheckStateOptions checkStateOptions);
bool WaitState(IElementDescriptor elementDescriptor, NCheckStateMode checkStateMode, double timeout);
Task<bool> WaitStateAsync(IElementDescriptor elementDescriptor, NCheckStateMode checkStateMode, double timeout);
bool WaitState(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
Task<bool> WaitStateAsync(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
bool WaitState(TargetAnchorableModel target, NCheckStateMode checkStateMode, double timeout = 5);
Task<bool> WaitStateAsync(TargetAnchorableModel target, NCheckStateMode checkStateMode, double timeout = 5);
bool WaitState(TargetAnchorableModel target, CheckStateOptions checkStateOptions);
Task<bool> WaitStateAsync(TargetAnchorableModel target, CheckStateOptions checkStateOptions);
bool WaitState(RuntimeTarget target, CheckStateOptions checkStateOptions);
Task<bool> WaitStateAsync(RuntimeTarget target, CheckStateOptions checkStateOptions);
```

### KeyboardShortcut

```csharp
void KeyboardShortcut(string target, string shortcuts, double delayBetweenShortcuts = 0.5);
Task KeyboardShortcutAsync(string target, string shortcuts, double delayBetweenShortcuts = 0.5);
void KeyboardShortcut(string target, KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(string target, KeyboardShortcutOptions keyboardShortcutOptions);
void KeyboardShortcut(IElementDescriptor elementDescriptor, string shortcuts, double delayBetweenShortcuts = 0.5);
Task KeyboardShortcutAsync(IElementDescriptor elementDescriptor, string shortcuts, double delayBetweenShortcuts = 0.5);
void KeyboardShortcut(IElementDescriptor elementDescriptor, KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(IElementDescriptor elementDescriptor, KeyboardShortcutOptions keyboardShortcutOptions);
void KeyboardShortcut(string shortcuts, double delayBetweenShortcuts = 0.5);
Task KeyboardShortcutAsync(string shortcuts, double delayBetweenShortcuts = 0.5);
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(KeyboardShortcutOptions keyboardShortcutOptions);
void KeyboardShortcut(TargetAnchorableModel target, string shortcuts, double delayBetweenShortcuts = 0.5);
Task KeyboardShortcutAsync(TargetAnchorableModel target, string shortcuts, double delayBetweenShortcuts = 0.5);
void KeyboardShortcut(TargetAnchorableModel target, KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(TargetAnchorableModel target, KeyboardShortcutOptions keyboardShortcutOptions);
void KeyboardShortcut(RuntimeTarget target, KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(RuntimeTarget target, KeyboardShortcutOptions keyboardShortcutOptions);
```

### Highlight

```csharp
void Highlight(string target, KnownColor color = KnownColor.Yellow, double duration = 3);
Task HighlightAsync(string target, KnownColor color = KnownColor.Yellow, double duration = 3);
void Highlight(string target, HighlightOptions highlightOptions);
Task HighlightAsync(string target, HighlightOptions highlightOptions);
void Highlight(IElementDescriptor elementDescriptor, KnownColor color = KnownColor.Yellow, double duration = 3);
Task HighlightAsync(IElementDescriptor elementDescriptor, KnownColor color = KnownColor.Yellow, double duration = 3);
void Highlight(IElementDescriptor elementDescriptor, HighlightOptions highlightOptions);
Task HighlightAsync(IElementDescriptor elementDescriptor, HighlightOptions highlightOptions);
void Highlight(TargetAnchorableModel target, HighlightOptions highlightOptions = null);
Task HighlightAsync(TargetAnchorableModel target, HighlightOptions highlightOptions = null);
void Highlight(RuntimeTarget target, HighlightOptions highlightOptions = null);
Task HighlightAsync(RuntimeTarget target, HighlightOptions highlightOptions = null);
```

### GetAttribute

```csharp
string GetAttribute(string target, string attribute);
Task<string> GetAttributeAsync(string target, string attribute);
string GetAttribute(string target, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsync(string target, GetAttributeOptions getAttributeOptions);
string GetAttribute(IElementDescriptor elementDescriptor, string attribute);
Task<string> GetAttributeAsync(IElementDescriptor elementDescriptor, string attribute);
string GetAttribute(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsync(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions);
T GetAttribute<T>(string target, string attribute);
Task<T> GetAttributeAsync<T>(string target, string attribute);
T GetAttribute<T>(string target, GetAttributeOptions getAttributeOptions);
Task<T> GetAttributeAsync<T>(string target, GetAttributeOptions getAttributeOptions);
T GetAttribute<T>(IElementDescriptor elementDescriptor, string attribute);
Task<T> GetAttributeAsync<T>(IElementDescriptor elementDescriptor, string attribute);
T GetAttribute<T>(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions);
Task<T> GetAttributeAsync<T>(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions);
string GetAttribute(TargetAnchorableModel target, string attribute);
Task<string> GetAttributeAsync(TargetAnchorableModel target, string attribute);
string GetAttribute(TargetAnchorableModel target, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsync(TargetAnchorableModel target, GetAttributeOptions getAttributeOptions);
string GetAttribute(RuntimeTarget target, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsync(RuntimeTarget target, GetAttributeOptions getAttributeOptions);
T GetAttribute<T>(TargetAnchorableModel target, string attribute);
Task<T> GetAttributeAsync<T>(TargetAnchorableModel target, string attribute);
T GetAttribute<T>(TargetAnchorableModel target, GetAttributeOptions getAttributeOptions);
Task<T> GetAttributeAsync<T>(TargetAnchorableModel target, GetAttributeOptions getAttributeOptions);
T GetAttribute<T>(RuntimeTarget target, GetAttributeOptions getAttributeOptions);
Task<T> GetAttributeAsync<T>(RuntimeTarget target, GetAttributeOptions getAttributeOptions);
```

### GetAttributeAsJson

```csharp
string GetAttributeAsJson(string target, string attribute);
Task<string> GetAttributeAsJsonAsync(string target, string attribute);
string GetAttributeAsJson(string target, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsJsonAsync(string target, GetAttributeOptions getAttributeOptions);
string GetAttributeAsJson(IElementDescriptor elementDescriptor, string attribute);
Task<string> GetAttributeAsJsonAsync(IElementDescriptor elementDescriptor, string attribute);
string GetAttributeAsJson(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsJsonAsync(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions);
string GetAttributeAsJson(TargetAnchorableModel target, string attribute);
Task<string> GetAttributeAsJsonAsync(TargetAnchorableModel target, string attribute);
string GetAttributeAsJson(TargetAnchorableModel target, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsJsonAsync(TargetAnchorableModel target, GetAttributeOptions getAttributeOptions);
string GetAttributeAsJson(RuntimeTarget target, GetAttributeOptions getAttributeOptions);
Task<string> GetAttributeAsJsonAsync(RuntimeTarget target, GetAttributeOptions getAttributeOptions);
```

### Hover

```csharp
void Hover(string target, double hoverTime, CursorMotionType cursorMotionType);
Task HoverAsync(string target, double hoverTime, CursorMotionType cursorMotionType);
void Hover(string target, HoverOptions hoverOptions);
Task HoverAsync(string target, HoverOptions hoverOptions);
void Hover(IElementDescriptor elementDescriptor, double? hoverTime = null, CursorMotionType? cursorMotionType = null);
Task HoverAsync(IElementDescriptor elementDescriptor, double? hoverTime = null, CursorMotionType? cursorMotionType = null);
void Hover(IElementDescriptor elementDescriptor, HoverOptions hoverOptions);
Task HoverAsync(IElementDescriptor elementDescriptor, HoverOptions hoverOptions);
void Hover(TargetAnchorableModel target, double hoverTime, CursorMotionType cursorMotionType = CursorMotionType.Instant);
Task HoverAsync(TargetAnchorableModel target, double hoverTime, CursorMotionType cursorMotionType = CursorMotionType.Instant);
void Hover(TargetAnchorableModel target, HoverOptions hoverOptions);
Task HoverAsync(TargetAnchorableModel target, HoverOptions hoverOptions);
void Hover(RuntimeTarget target, HoverOptions hoverOptions);
Task HoverAsync(RuntimeTarget target, HoverOptions hoverOptions);
```

### GetChildren

```csharp
IEnumerable<RuntimeTarget> GetChildren(string target, string selectorFilter, bool checkRootVisibility = false, bool recursive = false, double timeout = Constants.DefaultTimeout);
Task<IEnumerable<RuntimeTarget>> GetChildrenAsync(string target, string selectorFilter, bool checkRootVisibility = false, bool recursive = false, double timeout = Constants.DefaultTimeout);
IEnumerable<RuntimeTarget> GetChildren(string target, GetChildrenOptions getChildrenOptions);
Task<IEnumerable<RuntimeTarget>> GetChildrenAsync(string target, GetChildrenOptions getChildrenOptions);
IEnumerable<RuntimeTarget> GetChildren(IElementDescriptor elementDescriptor, string selectorFilter, bool checkRootVisibility = false, bool recursive = false, double timeout = Constants.DefaultTimeout);
Task<IEnumerable<RuntimeTarget>> GetChildrenAsync(IElementDescriptor elementDescriptor, string selectorFilter, bool checkRootVisibility = false, bool recursive = false, double timeout = Constants.DefaultTimeout);
IEnumerable<RuntimeTarget> GetChildren(IElementDescriptor elementDescriptor, GetChildrenOptions getChildrenOptions);
Task<IEnumerable<RuntimeTarget>> GetChildrenAsync(IElementDescriptor elementDescriptor, GetChildrenOptions getChildrenOptions);
IEnumerable<RuntimeTarget> GetChildren(TargetAnchorableModel target, GetChildrenOptions getChildrenOptions);
Task<IEnumerable<RuntimeTarget>> GetChildrenAsync(TargetAnchorableModel target, GetChildrenOptions getChildrenOptions);
IEnumerable<RuntimeTarget> GetChildren(RuntimeTarget target, GetChildrenOptions getChildrenOptions);
Task<IEnumerable<RuntimeTarget>> GetChildrenAsync(RuntimeTarget target, GetChildrenOptions getChildrenOptions);
```

### ExtractData

```csharp
DataTable ExtractData(string target, string extractMetadata, string tableSettings = "", NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard, LimitType limitExtractionTo = LimitType.Rows, int? numberOfItems = null);
DataTable ExtractData(string target, string nextPageTarget, string extractMetadata, string tableSettings = "", double delayBetweenPages = Constants.DefaultDelayBetweenPages, NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard, LimitType limitExtractionTo = LimitType.Rows, int? numberOfItems = null);
DataTable ExtractData(string target, ExtractDataOptions extractDataOptions);
DataTable ExtractData(IElementDescriptor elementDescriptor, string extractMetadata, string tableSettings = "", NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard, LimitType limitExtractionTo = LimitType.Rows, int? numberOfItems = null);
DataTable ExtractData(IElementDescriptor elementDescriptor, string nextPageTarget, string extractMetadata, string tableSettings = "", double delayBetweenPages = Constants.DefaultDelayBetweenPages, NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard, LimitType limitExtractionTo = LimitType.Rows, int? numberOfItems = null);
DataTable ExtractData(IElementDescriptor elementDescriptor, ExtractDataOptions extractDataOptions);
DataTable ExtractData(TargetAnchorableModel target, string extractMetadata, string tableSettings = "", NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard, LimitType limitExtractionTo = LimitType.Rows, int? numberOfItems = null);
DataTable ExtractData(TargetAnchorableModel target, TargetAnchorableModel nextPageTarget, string extractMetadata, string tableSettings = "", double delayBetweenPages = Constants.DefaultDelayBetweenPages, NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard, LimitType limitExtractionTo = LimitType.Rows, int? numberOfItems = null);
DataTable ExtractData(TargetAnchorableModel target, ExtractDataOptions extractDataOptions);
DataTable ExtractData(ExtractDataOptionsModel options);
```

### ExtractTableData

```csharp
DataTable ExtractTableData(IElementDescriptor elementDescriptor, ExtractTableDataOptions extractTableDataOptions = null);
Task<DataTable> ExtractTableDataAsync(IElementDescriptor elementDescriptor, ExtractTableDataOptions extractTableDataOptions = null);
DataTable ExtractTableData(string target, ExtractTableDataOptions extractTableDataOptions = null);
Task<DataTable> ExtractTableDataAsync(string target, ExtractTableDataOptions extractTableDataOptions = null);
DataTable ExtractTableData(TargetAnchorableModel target, string extractMetadata, string tableSettings, TargetAnchorableModel nextPageTarget = null, ExtractTableDataOptions extractDataOptions = null);
Task<DataTable> ExtractTableDataAsync(TargetAnchorableModel target, string extractMetadata, string tableSettings, TargetAnchorableModel nextPageTarget = null, ExtractTableDataOptions extractDataOptions = null);
```

### DragAndDrop

```csharp
void DragAndDrop(string target, TargetAnchorableModel destinationTarget, NKeyModifiers? keyModifiers = null, NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null, bool? useSourceHover = null, double? delayBetweenActions = null);
Task DragAndDropAsync(string target, TargetAnchorableModel destinationTarget, NKeyModifiers? keyModifiers = null, NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null, bool? useSourceHover = null, double? delayBetweenActions = null);
void DragAndDrop(string target, DragAndDropOptions dragAndDropOptions);
Task DragAndDropAsync(string target, DragAndDropOptions dragAndDropOptions);
void DragAndDrop(IElementDescriptor elementDescriptor, TargetAnchorableModel destinationTarget, NKeyModifiers? keyModifiers = null, NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null, bool? useSourceHover = null, double? delayBetweenActions = null);
Task DragAndDropAsync(IElementDescriptor elementDescriptor, TargetAnchorableModel destinationTarget, NKeyModifiers? keyModifiers = null, NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null, bool? useSourceHover = null, double? delayBetweenActions = null);
void DragAndDrop(IElementDescriptor elementDescriptor, IElementDescriptor destinationTarget, NKeyModifiers? keyModifiers = null, NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null, bool? useSourceHover = null, double? delayBetweenActions = null);
Task DragAndDropAsync(IElementDescriptor elementDescriptor, IElementDescriptor destinationTarget, NKeyModifiers? keyModifiers = null, NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null, bool? useSourceHover = null, double? delayBetweenActions = null);
void DragAndDrop(IElementDescriptor elementDescriptor, DragAndDropOptions dragAndDropOptions);
Task DragAndDropAsync(IElementDescriptor elementDescriptor, DragAndDropOptions dragAndDropOptions);
void DragAndDrop(TargetAnchorableModel target, DragAndDropOptions dragAndDropOptions = null);
Task DragAndDropAsync(TargetAnchorableModel target, DragAndDropOptions dragAndDropOptions = null);
void DragAndDrop(RuntimeTarget target, DragAndDropOptions dragAndDropOptions = null);
Task DragAndDropAsync(RuntimeTarget target, DragAndDropOptions dragAndDropOptions = null);
```

### GetRuntimeTarget

```csharp
RuntimeTarget GetRuntimeTarget(string target, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
Task<RuntimeTarget> GetRuntimeTargetAsync(string target, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
RuntimeTarget GetRuntimeTarget(TargetAnchorableModel target, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
Task<RuntimeTarget> GetRuntimeTargetAsync(TargetAnchorableModel target, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
```

### FillForm

```csharp
void FillForm(FillFormOptions fillFormOptions);
Task FillFormAsync(FillFormOptions fillFormOptions);
void FillForm(object dataSource);
Task FillFormAsync(object dataSource);
```

### ClosePopup

```csharp
void ClosePopup(ClosePopupOptions closePopupOptions = null);
Task ClosePopupAsync(ClosePopupOptions closePopupOptions = null);
```

### SAPSelectMenuItem

```csharp
void SAPSelectMenuItem(string item);
Task SAPSelectMenuItemAsync(string item);
void SAPSelectMenuItem(SelectItemOptions selectItemOptions);
Task SAPSelectMenuItemAsync(SelectItemOptions selectItemOptions);
```

### GoToUrl

```csharp
void GoToUrl(string url);
Task GoToUrlAsync(string url);
void GoToUrl(GoToUrlOptions urlOptions);
Task GoToUrlAsync(GoToUrlOptions urlOptions);
```

### GetUrl

```csharp
string GetUrl(GetUrlOptions getUrlOptions = null);
Task<string> GetUrlAsync(GetUrlOptions getUrlOptions = null);
```

### GetAccessibilityCheck

```csharp
string GetAccessibilityCheck(GetAccessibilityCheckOptions getAccessibilityCheckOptions = null);
Task<string> GetAccessibilityCheckAsync(GetAccessibilityCheckOptions getAccessibilityCheckOptions = null);
```

### GetUiElement

```csharp
UiElement GetUiElement(RuntimeTarget target);
Task<UiElement> GetUiElementAsync(RuntimeTarget target);
UiElement GetUiElement();
Task<UiElement> GetUiElementAsync();
UiElement GetUiElement(IElementDescriptor elementDescriptor, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
Task<UiElement> GetUiElementAsync(IElementDescriptor elementDescriptor, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
UiElement GetUiElement(TargetAnchorableModel target, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
Task<UiElement> GetUiElementAsync(TargetAnchorableModel target, GetRuntimeTargetOptions getRuntimeTargetOptions = null);
```

### SetValue

```csharp
void SetValue(string target, string value);
Task SetValueAsync(string target, string value);
void SetValue(string target, SetValueOptions setValueOptions);
Task SetValueAsync(string target, SetValueOptions setValueOptions);
void SetValue(IElementDescriptor elementDescriptor, string value);
Task SetValueAsync(IElementDescriptor elementDescriptor, string value);
void SetValue(IElementDescriptor elementDescriptor, SetValueOptions setValueOptions);
Task SetValueAsync(IElementDescriptor elementDescriptor, SetValueOptions setValueOptions);
void SetValue(TargetAnchorableModel target, string value);
Task SetValueAsync(TargetAnchorableModel target, string value);
void SetValue(TargetAnchorableModel target, SetValueOptions setValueOptions);
Task SetValueAsync(TargetAnchorableModel target, SetValueOptions setValueOptions);
void SetValue(RuntimeTarget target, SetValueOptions setValueOptions);
Task SetValueAsync(RuntimeTarget target, SetValueOptions setValueOptions);
```

### UpdateUIElement

```csharp
void UpdateUIElement(string target, string value);
Task UpdateUIElementAsync(string target, string value);
void UpdateUIElement(string target, UpdateUIElementOptions updateUIElementOptions);
Task UpdateUIElementAsync(string target, UpdateUIElementOptions updateUIElementOptions);
void UpdateUIElement(IElementDescriptor elementDescriptor, string value);
Task UpdateUIElementAsync(IElementDescriptor elementDescriptor, string value);
void UpdateUIElement(IElementDescriptor elementDescriptor, UpdateUIElementOptions updateUIElementOptions);
Task UpdateUIElementAsync(IElementDescriptor elementDescriptor, UpdateUIElementOptions updateUIElementOptions);
void UpdateUIElement(TargetAnchorableModel target, string value);
Task UpdateUIElementAsync(TargetAnchorableModel target, string value);
void UpdateUIElement(TargetAnchorableModel target, UpdateUIElementOptions updateUIElementOptions);
Task UpdateUIElementAsync(TargetAnchorableModel target, UpdateUIElementOptions updateUIElementOptions);
void UpdateUIElement(RuntimeTarget target, UpdateUIElementOptions updateUIElementOptions);
Task UpdateUIElementAsync(RuntimeTarget target, UpdateUIElementOptions updateUIElementOptions);
```

### UITask

```csharp
UITaskResult UITask(string task, NUITaskAgentType agentType = NUITaskAgentType.DOMBased, NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard);
Task<UITaskResult> UITaskAsync(string task, NUITaskAgentType agentType = NUITaskAgentType.DOMBased, NChildInteractionMode interactionMode = NChildInteractionMode.SameAsCard);
UITaskResult UITask(UITaskOptions options);
Task<UITaskResult> UITaskAsync(UITaskOptions options);
```

### InjectJsScript

```csharp
string InjectJsScript(string target, string scriptCodePath, string inputParameter = null);
Task<string> InjectJsScriptAsync(string target, string scriptCodePath, string inputParameter = null);
string InjectJsScript(string target, InjectJsScriptOptions injectJsScriptOptions);
Task<string> InjectJsScriptAsync(string target, InjectJsScriptOptions injectJsScriptOptions);
string InjectJsScript(IElementDescriptor elementDescriptor, string scriptCodePath, string inputParameter = null);
Task<string> InjectJsScriptAsync(IElementDescriptor elementDescriptor, string scriptCodePath, string inputParameter = null);
string InjectJsScript(IElementDescriptor elementDescriptor, InjectJsScriptOptions injectJsScriptOptions);
Task<string> InjectJsScriptAsync(IElementDescriptor elementDescriptor, InjectJsScriptOptions injectJsScriptOptions);
string InjectJsScript(TargetAnchorableModel target, string scriptCodePath, string inputParameter = null);
Task<string> InjectJsScriptAsync(TargetAnchorableModel target, string scriptCodePath, string inputParameter = null);
string InjectJsScript(TargetAnchorableModel target, InjectJsScriptOptions injectJsScriptOptions);
Task<string> InjectJsScriptAsync(TargetAnchorableModel target, InjectJsScriptOptions injectJsScriptOptions);
string InjectJsScript(RuntimeTarget target, InjectJsScriptOptions injectJsScriptOptions);
Task<string> InjectJsScriptAsync(RuntimeTarget target, InjectJsScriptOptions injectJsScriptOptions);
```

### SAPReadStatusbar

```csharp
SAPReadStatusbarResult SAPReadStatusbar();
Task<SAPReadStatusbarResult> SAPReadStatusbarAsync();
SAPReadStatusbarResult SAPReadStatusbar(SAPReadStatusbarOptions readStatusbarOptions);
Task<SAPReadStatusbarResult> SAPReadStatusbarAsync(SAPReadStatusbarOptions readStatusbarOptions);
```

### SAPSelectDatesInCalendar

```csharp
void SAPSelectDatesInCalendar(string target, DateTime date);
Task SAPSelectDatesInCalendarAsync(string target, DateTime date);
void SAPSelectDatesInCalendar(string target, DateTime startDate, DateTime endDate);
Task SAPSelectDatesInCalendarAsync(string target, DateTime startDate, DateTime endDate);
void SAPSelectDatesInCalendar(string target, int year, int week);
Task SAPSelectDatesInCalendarAsync(string target, int year, int week);
void SAPSelectDatesInCalendar(string target, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
Task SAPSelectDatesInCalendarAsync(string target, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
void SAPSelectDatesInCalendar(IElementDescriptor elementDescriptor, DateTime date);
Task SAPSelectDatesInCalendarAsync(IElementDescriptor elementDescriptor, DateTime date);
void SAPSelectDatesInCalendar(IElementDescriptor elementDescriptor, DateTime startDate, DateTime endDate);
Task SAPSelectDatesInCalendarAsync(IElementDescriptor elementDescriptor, DateTime startDate, DateTime endDate);
void SAPSelectDatesInCalendar(IElementDescriptor elementDescriptor, int year, int week);
Task SAPSelectDatesInCalendarAsync(IElementDescriptor elementDescriptor, int year, int week);
void SAPSelectDatesInCalendar(IElementDescriptor elementDescriptor, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
Task SAPSelectDatesInCalendarAsync(IElementDescriptor elementDescriptor, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
void SAPSelectDatesInCalendar(TargetAnchorableModel target, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
Task SAPSelectDatesInCalendarAsync(TargetAnchorableModel target, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
void SAPSelectDatesInCalendar(RuntimeTarget target, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
Task SAPSelectDatesInCalendarAsync(RuntimeTarget target, SAPSelectDatesInCalendarOptions sapSelectDatesInCalendarOptions);
```

### SAPCallTransaction

```csharp
void SAPCallTransaction(string transactionCode);
Task SAPCallTransactionAsync(string transactionCode);
void SAPCallTransaction(string transactionCode, string prefix);
Task SAPCallTransactionAsync(string transactionCode, string prefix);
void SAPCallTransaction(SAPCallTransactionOptions sapCallTransactionOptions);
Task SAPCallTransactionAsync(SAPCallTransactionOptions sapCallTransactionOptions);
```

### SAPExpandTree

```csharp
void SAPExpandTree(string target, string path);
void SAPExpandTree(string target, SAPExpandTreeOptions sapExpandTreeOptions);
void SAPExpandTree(IElementDescriptor elementDescriptor, string path);
void SAPExpandTree(IElementDescriptor elementDescriptor, SAPExpandTreeOptions sapExpandTreeOptions);
void SAPExpandTree(TargetAnchorableModel target, SAPExpandTreeOptions sapExpandTreeOptions);
void SAPExpandTree(RuntimeTarget target, SAPExpandTreeOptions sapExpandTreeOptions);
Task SAPExpandTreeAsync(string target, string path);
Task SAPExpandTreeAsync(string target, SAPExpandTreeOptions sapExpandTreeOptions);
Task SAPExpandTreeAsync(IElementDescriptor elementDescriptor, string path);
Task SAPExpandTreeAsync(IElementDescriptor elementDescriptor, SAPExpandTreeOptions sapExpandTreeOptions);
Task SAPExpandTreeAsync(TargetAnchorableModel target, SAPExpandTreeOptions sapExpandTreeOptions);
Task SAPExpandTreeAsync(RuntimeTarget target, SAPExpandTreeOptions sapExpandTreeOptions);
```

### SAPExpandALVTree

```csharp
void SAPExpandALVTree(string target, string path);
void SAPExpandALVTree(string target, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
void SAPExpandALVTree(IElementDescriptor elementDescriptor, string path);
void SAPExpandALVTree(IElementDescriptor elementDescriptor, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
void SAPExpandALVTree(TargetAnchorableModel target, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
void SAPExpandALVTree(RuntimeTarget target, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
Task SAPExpandALVTreeAsync(string target, string path);
Task SAPExpandALVTreeAsync(string target, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
Task SAPExpandALVTreeAsync(IElementDescriptor elementDescriptor, string path);
Task SAPExpandALVTreeAsync(IElementDescriptor elementDescriptor, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
Task SAPExpandALVTreeAsync(TargetAnchorableModel target, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
Task SAPExpandALVTreeAsync(RuntimeTarget target, SAPExpandALVTreeOptions sapExpandALVTreeOptions);
```

### Close

```csharp
void Close();
```

### Dispose

```csharp
void Dispose();
```

## Options Classes

### ClickOptions

| Property | Type | Description |
|----------|------|-------------|
| `KeyModifiers` | `NKeyModifiers` | Enables you to add a key modifier. Options: None, Alt, Ctrl, Shift, Win. Default is None. |
| `ClickType` | `NClickType` | Specifies the type of mouse click (single, double, up, down). Default is single click. |
| `MouseButton` | `NMouseButton` | The mouse button (left, right, middle). Default is left. |
| `CursorMotionType` | `CursorMotionType` | Specifies the type of motion performed by the mouse cursor. |
| `AlterIfDisabled` | `bool` | If enabled, the action is executed even if the specified UI element is disabled. |
| `InteractionMode` | `NChildInteractionMode` | The type of interaction the activities will use. |
| `ActivateBefore` | `bool` | Bring the UI element to the foreground before clicking. Default is true. |
| `VerifyOptions` | `VerifyOptions` | Verifies if the action performed by the activity was correct at runtime. |
| `UnblockInput` | `bool` | Used at runtime when Click triggers a modal dialog box. Only works with Simulate Click. |

### TypeIntoOptions

| Property | Type | Description |
|----------|------|-------------|
| `Text` | `string` | The text to enter. |
| `SecureText` | `SecureString` | The secure text to enter. |
| `DelayBetweenKeys` | `double` | Delay (in seconds) between consecutive keystrokes. Max 1 second. |
| `ActivateBefore` | `bool` | Bring the UI element to the foreground before typing. Default is true. |
| `ClickBeforeMode` | `NClickMode` | Performs a click in the text-field before typing to activate it. |
| `EmptyFieldMode` | `NEmptyFieldMode` | Clear existing content before typing. |
| `ClipboardMode` | `NTypeByClipboardMode` | Whether the clipboard is used for typing. |
| `DeselectAfter` | `bool` | Adds a Complete event after text entry. Default is false. |
| `AlterIfDisabled` | `bool` | Execute even if the target element is disabled. Default is false. |
| `InteractionMode` | `NChildInteractionMode` | The method used to execute the action. |
| `VerifyOptions` | `VerifyOptions` | Runtime verification of the action. |

### CheckOptions

| Property | Type | Description |
|----------|------|-------------|
| `CheckType` | `NCheckType` | The action: Check, Uncheck, or Toggle. |
| `AlterIfDisabled` | `bool` | Execute even if the target element is disabled. Default is false. |

### CheckStateOptions

| Property | Type | Description |
|----------|------|-------------|
| `Mode` | `NCheckStateMode` | Whether to wait for appear or disappear. |
| `CheckVisibility` | `bool` | Whether to check element visibility. |
| `HealingAgentBehavior` | `NChildHealingAgentBehavior` | Healing agent behavior. Default is Disabled. |

### HighlightOptions

| Property | Type | Description |
|----------|------|-------------|
| `HighlightTime` | `double` | Time (in seconds) to highlight. Default is 2 seconds. |
| `Color` | `KnownColor` | Color of the highlight box. Default is Yellow. |

### HoverOptions

| Property | Type | Description |
|----------|------|-------------|
| `HoverTime` | `double` | Seconds to hover. Default is 1 second. |
| `CursorMotionType` | `CursorMotionType` | How to execute the hover. |
| `InteractionMode` | `NChildInteractionMode` | The type of interaction to use. |
| `VerifyOptions` | `VerifyOptions` | Runtime verification. |

### GetTextOptions

| Property | Type | Description |
|----------|------|-------------|
| `ScrapingOptions` | `NScrapingOptions` | Options: None, AllowFormatting, IgnoreHiddenText, GetWordsCoordinates. |
| `ScrapingMethod` | `NScrapingMethod` | Method: Default, Text Attribute, Fulltext, Native. |

### SelectItemOptions

| Property | Type | Description |
|----------|------|-------------|
| `Item` | `string` | The name of the item to select. |
| `AlterIfDisabled` | `bool` | Execute even if the target element is disabled. Default is false. |

### KeyboardShortcutOptions

| Property | Type | Description |
|----------|------|-------------|
| `Shortcuts` | `string` | The keyboard shortcuts to be sent. |
| `ActivateBefore` | `bool` | Bring the UI element to foreground first. Default is true. |
| `DelayBetweenShortcuts` | `double` | Delay (in seconds) between shortcuts. Default is 0.5. |
| `DelayBetweenKeys` | `double` | Delay (in seconds) between consecutive keys. |
| `ClickBeforeMode` | `NClickMode` | Click before sending shortcuts: None, Single, or Double. |
| `InteractionMode` | `NChildInteractionMode` | Method used to perform the action. |
| `VerifyOptions` | `VerifyOptions` | Runtime verification. |

### MouseScrollOptions

| Property | Type | Description |
|----------|------|-------------|
| `InteractionMode` | `NChildInteractionMode` | The type of interaction to use. |
| `CursorMotionType` | `CursorMotionType` | Cursor motion: Instant or Smooth. |
| `KeyModifiers` | `NKeyModifiers` | Key modifiers during scroll. Default is None. |
| `Direction` | `NScrollDirection` | Scroll direction: Left, Up, Right, Down. |
| `MovementUnits` | `int` | Number of mouse wheel detents. Default is 10. |
| `SearchedElement` | `SearchedElementOptions` | The UI element to scroll to. |

### TargetAppOptions

| Property | Type | Description |
|----------|------|-------------|
| `Timeout` | `double` | Timeout in seconds. |
| `InteractionMode` | `NInteractionMode` | Interaction mode. |
| `AttachMode` | `NAppAttachMode` | Attachment mode. Default is ByInstance. |
| `OpenMode` | `NAppOpenMode` | Open mode. |
| `CloseMode` | `NAppCloseMode` | Whether to close the app on scope exit. Default is Always. |
| `WindowResize` | `NWindowResize` | Window resize mode. |
| `UserDataFolderMode` | `BrowserUserDataFolderMode` | Browser user data folder mode. |
| `UserDataFolderPath` | `string` | Custom user data folder path. |
| `IsIncognito` | `bool` | Whether to open in incognito mode. |
| `WebDriverMode` | `NWebDriverMode` | WebDriver mode. |
| `WorkingDirectory` | `string` | Working directory for the application. |
| `DialogHandlingOptions` | `DialogHandlingOptions` | Browser dialog handling options. |

### TakeScreenshotOptions

| Property | Type | Description |
|----------|------|-------------|
| `FileName` | `string` | File path to save the screenshot. |

### GetAttributeOptions

Inherits from `GetAttributeBaseOptions`.

### GetAttributeBaseOptions

| Property | Type | Description |
|----------|------|-------------|
| `Attribute` | `string` | The name of the attribute to retrieve. |

### GetChildrenOptions

| Property | Type | Description |
|----------|------|-------------|
| `SelectorFilter` | `string` | The selector filter. |
| `Timeout` | `double` | Timeout in seconds. Default is 30. |
| `Recursive` | `bool` | If true, performs a recursive search. |
| `CheckRootVisibility` | `bool` | Check visibility while searching for root node. |

### ExtractDataOptions

| Property | Type | Description |
|----------|------|-------------|
| `ExtractMetadata` | `string` | XML string defining what data to extract. |
| `TableSettings` | `string` | Table settings for extraction. |
| `InteractionMode` | `NChildInteractionMode` | Interaction mode for next-page clicks. |
| `LimitExtractionTo` | `LimitType` | Type of limit to apply. |
| `NumberOfItems` | `int?` | Maximum results to extract. 0 means all. |
| `NextPage` | `NextPageOptions` | Next page navigation options. |

### ExtractTableDataOptions

| Property | Type | Description |
|----------|------|-------------|
| `InteractionMode` | `NChildInteractionMode` | Interaction mode. |
| `LimitExtractionTo` | `LimitType` | Limit type. |
| `NumberOfItems` | `int?` | Maximum items. |
| `DelayBetweenPages` | `double` | Delay between page navigations. |

### DragAndDropOptions

| Property | Type | Description |
|----------|------|-------------|
| `DestinationTarget` | `TargetAnchorableModel` | The target to drop into. |
| `KeyModifiers` | `NKeyModifiers` | Key modifiers during drag. |
| `MouseButton` | `NMouseButton` | Mouse button to use. |
| `CursorMotionType` | `CursorMotionType` | Cursor motion type. |
| `UseSourceHover` | `bool` | Hover over source before dragging. |
| `DelayBetweenActions` | `double` | Delay between actions (seconds). |

### FillFormOptions

| Property | Type | Description |
|----------|------|-------------|
| `DataSource` | `object` | The data to use as input. |
| `EnableValidation` | `bool` | Whether to validate the execution. |

### SetValueOptions

| Property | Type | Description |
|----------|------|-------------|
| `Value` | `string` | The value used to fill the target. |
| `EnableValidation` | `bool` | Whether to validate the execution. |

### UpdateUIElementOptions

| Property | Type | Description |
|----------|------|-------------|
| `Value` | `string` | The value used to fill the target. |
| `EnableValidation` | `bool` | Whether to validate the execution. |

### ClosePopupOptions

| Property | Type | Description |
|----------|------|-------------|
| `PreferredButtons` | `string[]` | Preferred button search order. Default is ["Close", "Cancel"]. |
| `PopupAppearTimeout` | `double` | Timeout for waiting for a popup to appear (seconds). |
| `EnableAI` | `bool` | Whether to use AI to close the popup. |

### InjectJsScriptOptions

| Property | Type | Description |
|----------|------|-------------|
| `ScriptCodePath` | `string` | JavaScript code or path to a .js file. |
| `InputParameter` | `string` | Input data for the script. |
| `ExecutionWorld` | `NExecutionWorld` | Execution world: Isolated (default) or Page. |

### UITaskOptions

| Property | Type | Description |
|----------|------|-------------|
| `Task` | `string` | The task to be executed. |
| `AgentType` | `NUITaskAgentType` | The type of agent to use. |
| `InteractionMode` | `NChildInteractionMode` | Interaction mode. |
| `MaxIterations` | `int` | Maximum iterations. 0 means no limit. |
| `ClipboardMode` | `NTypeByClipboardMode` | Whether the agent can use clipboard for typing. |
| `IsDOMEnabled` | `bool` | Whether the agent can use native DOM. |
| `IsVariableSecurityEnabled` | `bool` | Whether variable security is enabled. Default is true. |
| `TraceAttachMode` | `NTraceAttachMode` | Trace attach mode. |

### SetRuntimeBrowserOptions

| Property | Type | Description |
|----------|------|-------------|
| `BrowserType` | `NBrowserType` | The browser type to use. |

### SetClipboardOptions

| Property | Type | Description |
|----------|------|-------------|
| `Text` | `string` | The text to set on the clipboard. |

### GoToUrlOptions

| Property | Type | Description |
|----------|------|-------------|
| `Url` | `string` | The URL to navigate to. |

### GetRuntimeTargetOptions

| Property | Type | Description |
|----------|------|-------------|
| `Timeout` | `double` | Timeout (in seconds) for searching the target. |

### TargetOptions

| Property | Type | Description |
|----------|------|-------------|
| `Timeout` | `double` | Timeout in seconds. Default is 30. |
| `DelayAfter` | `double` | Delay after executing (seconds). Default is 0.3. |
| `DelayBefore` | `double` | Delay before executing (seconds). Default is 0.2. |

### VerifyOptions

| Property | Type | Description |
|----------|------|-------------|
| `Target` | `TargetAnchorableModel` | The element to verify at runtime. |
| `Mode` | `NVerifyMode` | What change to check for: Appears, Disappears, TextChanges, AspectChanges. |
| `Retry` | `bool` | Whether to retry the action if verification fails. |
| `Timeout` | `double` | Timeout (in seconds) for verification. |
| `DelayBefore` | `double` | Delay before verification (seconds). Default is 0.2. |
| `IsLoose` | `bool` | Whether the target requires an application card. |
| `ExpectedText` | `string` | Expected text to compare after typing. |

### DialogHandlingOptions

| Property | Type | Description |
|----------|------|-------------|
| `DismissAlerts` | `bool` | Auto-dismiss alerts. Default is false. |
| `DismissConfirms` | `bool` | Auto-dismiss confirms. Default is false. |
| `DismissPrompts` | `bool` | Auto-dismiss prompts. Default is false. |
| `ConfirmDialogResponse` | `NBrowserDialogResponse` | Response for confirms. Default is Cancel. |
| `PromptDialogResponse` | `NBrowserDialogResponse` | Response for prompts. Default is Cancel. |
| `PromptDialogResponseText` | `string` | Text for prompt responses. Default is empty. |

### SAPCallTransactionOptions

| Property | Type | Description |
|----------|------|-------------|
| `Transaction` | `string` | The transaction code to call. |
| `Prefix` | `string` | The prefix for the transaction. Default is "/n". |

### SAPExpandTreeOptions

| Property | Type | Description |
|----------|------|-------------|
| `Path` | `string` | The path of the tree node to expand. |

### SAPExpandALVTreeOptions

| Property | Type | Description |
|----------|------|-------------|
| `Path` | `string` | The path to the ALV tree node to expand. |

### SAPSelectDatesInCalendarOptions

| Property | Type | Description |
|----------|------|-------------|
| `SelectType` | `NDateSelectionType` | Date, Range, or Week. |
| `Date` | `DateTime` | Single date to select. |
| `StartDate` | `DateTime` | Start date for range selection. |
| `EndDate` | `DateTime` | End date for range selection. |
| `Year` | `int` | Year for week selection. |
| `Week` | `int` | Week number for week selection. |

### NextPageOptions

| Property | Type | Description |
|----------|------|-------------|
| `Target` | `TargetAnchorableModel` | Next-page link target. |
| `DelayBetweenPages` | `double` | Delay between page navigations. |

### SearchedElementOptions

| Property | Type | Description |
|----------|------|-------------|
| `Target` | `TargetAnchorableModel` | The searched UI element reference. |
| `Timeout` | `double` | Timeout (seconds) to wait for the element. Default is 0.2. |

## Common Patterns

### 1. Attach to a browser and click a button

```csharp
using var app = uiAutomation.Attach("MyWebApp");
app.Click("SubmitButton");
```

### 2. Open an application, type text, and read a result

```csharp
using var app = uiAutomation.Open("LoginScreen");
app.TypeInto("UsernameField", "admin@example.com");
app.TypeInto("PasswordField", new TypeIntoOptions
{
    SecureText = securePassword,
    EmptyFieldMode = NEmptyFieldMode.SingleLine
});
app.Click("LoginButton");

bool loaded = app.WaitState("Dashboard", NCheckStateMode.WaitAppear, 10);
string welcomeText = app.GetText("WelcomeLabel");
```

### 3. Extract table data from a web page with pagination

```csharp
using var app = uiAutomation.Open("ProductCatalog");
DataTable products = app.ExtractTableData("ProductsTable", new ExtractTableDataOptions
{
    LimitExtractionTo = LimitType.Rows,
    NumberOfItems = 100,
    DelayBetweenPages = 1.5
});

foreach (DataRow row in products.Rows)
{
    Log(row["ProductName"].ToString());
}
```

### 4. Use keyboard shortcuts and check element state

```csharp
using var app = uiAutomation.Attach("SpreadsheetApp");

app.Click("CellA1");
app.KeyboardShortcut("CellA1", "ctrl+c");
app.Click("CellB1");
app.KeyboardShortcut("CellB1", "ctrl+v");

bool isSaveEnabled = app.IsEnabled("SaveButton");
if (isSaveEnabled)
{
    app.Click("SaveButton");
}
```

### 5. Iterate child elements and get attributes

```csharp
using var app = uiAutomation.Attach("FileManager");

var children = app.GetChildren("FileList", new GetChildrenOptions
{
    SelectorFilter = "<webctrl tag='li' />",
    Recursive = false,
    Timeout = 10
});

foreach (var child in children)
{
    string fileName = app.GetText(child, new GetTextOptions
    {
        ScrapingMethod = NScrapingMethod.TextAttribute
    });
    string href = app.GetAttribute(child, new GetAttributeOptions { Attribute = "href" });
    Log($"File: {fileName}, Link: {href}");
}
```
