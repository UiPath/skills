# UI Automation Windows API Reference

Full API reference for the `uiAutomation` service (`IUiAutomationAppService`) and the `UiTargetApp` handle.

---

## Opening and Attaching to Applications

### Open

Opens an application and returns a `UiTargetApp` handle. If the application is already open, behavior depends on `openMode`.

```csharp
// With screen name (Object Repository)
UiTargetApp Open(string screenName, string appName = "***", string appVersion = "***",
    NAppOpenMode openMode = NAppOpenMode.IfNotOpen,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents)

// With screen descriptor (Object Repository)
UiTargetApp Open(IScreenDescriptor screenDescriptor,
    NAppOpenMode openMode = NAppOpenMode.IfNotOpen,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents)

// With TargetAppOptions
UiTargetApp Open(string screenName, TargetAppOptions targetAppOptions, string appName = "***", string appVersion = "***")
UiTargetApp Open(IScreenDescriptor screenDescriptor, TargetAppOptions targetAppOptions)

// With TargetAppModel
UiTargetApp Open(TargetAppModel targetApp, TargetAppOptions targetAppOptions = null)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `screenName` | `string` | required | The name of the screen in Object Repository |
| `screenDescriptor` | `IScreenDescriptor` | required | Object Repository screen descriptor (e.g., `Descriptors.MyApp.Home`) |
| `targetApp` | `TargetAppModel` | required | Target application model |
| `appName` | `string` | `"***"` (first found) | The application name in Object Repository |
| `appVersion` | `string` | `"***"` (first found) | The application version in Object Repository |
| `openMode` | `NAppOpenMode` | `IfNotOpen` | `Never`, `IfNotOpen`, `Always` |
| `windowResize` | `NWindowResize` | `None` | `None`, `Maximize`, `Restore`, `Minimize` |
| `interactionMode` | `NInteractionMode` | `HardwareEvents` | `HardwareEvents`, `Simulate`, `DebuggerApi`, `WindowMessages`, `Background` |
| `targetAppOptions` | `TargetAppOptions` | `null` | Advanced options (see TargetAppOptions section) |

Async variants: `OpenAsync(...)` — all overloads return `Task<UiTargetApp>`.

### Attach

Attaches to an already opened application window and returns a `UiTargetApp` handle.

```csharp
// With screen name
UiTargetApp Attach(string screenName, string appName = "***", string appVersion = "***",
    NAppAttachMode appAttachMode = NAppAttachMode.ByInstance,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents)

// With screen descriptor
UiTargetApp Attach(IScreenDescriptor screenDescriptor,
    NAppAttachMode appAttachMode = NAppAttachMode.ByInstance,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents)

// With TargetAppOptions
UiTargetApp Attach(string screenName, TargetAppOptions targetAppOptions, string appName = "***", string appVersion = "***")
UiTargetApp Attach(IScreenDescriptor screenDescriptor, TargetAppOptions targetAppOptions)

// With TargetAppModel
UiTargetApp Attach(TargetAppModel targetApp, TargetAppOptions targetAppOptions = null)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `screenName` | `string` | required | The name of the screen in Object Repository |
| `screenDescriptor` | `IScreenDescriptor` | required | Object Repository screen descriptor |
| `targetApp` | `TargetAppModel` | required | Target application model |
| `appName` | `string` | `"***"` (first found) | The application name |
| `appVersion` | `string` | `"***"` (first found) | The application version |
| `appAttachMode` | `NAppAttachMode` | `ByInstance` | `ByProcessName`, `ByInstance`, `SingleWindow` |
| `windowResize` | `NWindowResize` | `None` | `None`, `Maximize`, `Restore`, `Minimize` |
| `interactionMode` | `NInteractionMode` | `HardwareEvents` | Interaction mode |
| `targetAppOptions` | `TargetAppOptions` | `null` | Advanced options |

Async variants: `AttachAsync(...)` — all overloads return `Task<UiTargetApp>`.

### TargetAppOptions

Advanced options for Open/Attach, created via `Options.AppOpen(...)` or `Options.AppAttach(...)`.

```csharp
// Builder methods
Options.AppOpen(attachMode, openMode, timeout, windowResize, interactionMode)
Options.AppAttach(attachMode, openMode, timeout, windowResize, interactionMode)

// Fluent extensions
.WithOpenOptions(attachMode, openMode, timeout, windowResize, interactionMode)
.WithBrowserOptions(userDataFolderPath, userDataFolderMode, isIncognito, webDriverMode)
```

| Property | Type | Default | Description |
|---|---|---|---|
| `Timeout` | `double` | — | Timeout in seconds |
| `InteractionMode` | `NInteractionMode` | `HardwareEvents` | Interaction mode |
| `AttachMode` | `NAppAttachMode` | `ByInstance` | Attach mode |
| `OpenMode` | `NAppOpenMode` | varies | Open mode |
| `CloseMode` | `NAppCloseMode` | — | When to close the app (`Never`, `IfOpenedByAppBrowser`, `Always`) |
| `WindowResize` | `NWindowResize` | `None` | Window resize mode |
| `UserDataFolderMode` | `BrowserUserDataFolderMode` | `Automatic` | Browser user data folder mode |
| `UserDataFolderPath` | `string` | — | Custom user data folder path |
| `IsIncognito` | `bool` | `false` | Open browser in incognito/private mode |
| `WebDriverMode` | `NWebDriverMode` | — | WebDriver mode (`Disabled`, `WithGUI`, `Headless`, `DevTools`, `DevToolsHeadless`) |
| `WorkingDirectory` | `string` | — | Working directory for the application |

---

## Element Interactions

All methods below are on `UiTargetApp`. Each method has sync and async variants, and accepts targets as `string`, `IElementDescriptor`, `TargetAnchorableModel`, or `RuntimeTarget`.

### Click

Clicks a specified UI element.

```csharp
// Simple overloads
void Click(string target, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left)
void Click(IElementDescriptor elementDescriptor, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left)

// With options
void Click(string target, ClickOptions clickOptions)
void Click(IElementDescriptor elementDescriptor, ClickOptions clickOptions)
void Click(TargetAnchorableModel target, ClickOptions clickOptions = null)
void Click(RuntimeTarget target, ClickOptions clickOptions = null)
```

**ClickOptions** — created via `Options.Click(clickType, mouseButton)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `ClickType` | `NClickType` | `Single` | `Single`, `Double`, `Down`, `Up` |
| `MouseButton` | `NMouseButton` | `Left` | `Left`, `Right`, `Middle` |
| `KeyModifiers` | `NKeyModifiers` | `None` | `None`, `Alt`, `Ctrl`, `Shift`, `Win` (flags) |
| `CursorMotionType` | `CursorMotionType` | `Instant` | `Instant`, `Smooth` |
| `AlterIfDisabled` | `bool` | — | Whether to alter the element if disabled |
| `ActivateBefore` | `bool` | — | Whether to activate the window before clicking |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Override interaction mode |

Builder: `Options.Click(NClickType.Double, NMouseButton.Left).With(keyModifiers: NKeyModifiers.Ctrl)`

### TypeInto

Enters text in a specified UI element.

```csharp
// Simple overloads
void TypeInto(string target, string text)
void TypeInto(string target, SecureString secureText)
void TypeInto(IElementDescriptor elementDescriptor, string text)
void TypeInto(IElementDescriptor elementDescriptor, SecureString secureText)

// With options
void TypeInto(string target, TypeIntoOptions typeIntoOptions)
void TypeInto(IElementDescriptor elementDescriptor, TypeIntoOptions typeIntoOptions)
void TypeInto(TargetAnchorableModel target, string text)
void TypeInto(TargetAnchorableModel target, SecureString secureText)
void TypeInto(TargetAnchorableModel target, TypeIntoOptions typeIntoOptions)
void TypeInto(RuntimeTarget target, TypeIntoOptions typeIntoOptions)
```

**TypeIntoOptions** — created via `Options.TypeInto(text)` or `Options.TypeInto(secureText)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `Text` | `string` | — | The text to type |
| `SecureText` | `SecureString` | — | Secure text to type |
| `ActivateBefore` | `bool` | — | Activate window before typing |
| `ClickBeforeMode` | `NClickMode` | — | Click before typing (`None`, `Single`, `Double`) |
| `DelayBetweenKeys` | `double` | — | Delay between keys in seconds |
| `EmptyFieldMode` | `NEmptyFieldMode` | — | How to clear the field (`None`, `SingleLine`, `MultiLine`) |
| `ClipboardMode` | `NTypeByClipboardMode` | — | Clipboard mode (`Never`, `Always`, `WhenPossible`) |
| `DeselectAfter` | `bool` | — | Deselect text after typing |
| `AlterIfDisabled` | `bool` | — | Alter if element is disabled |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Override interaction mode |

Builder: `Options.TypeInto("text").With(emptyFieldMode: NEmptyFieldMode.SingleLine, clickBeforeMode: NClickMode.Single)`

**Verify after typing** — use `.UntilText(expectedText, retry, timeout)`:
```csharp
Options.TypeInto("hello").UntilText("hello", retry: true, timeout: 2)
```

### GetText

Extracts and copies the text from a UI element.

```csharp
// Simple
string GetText(string target)
string GetText(IElementDescriptor elementDescriptor)

// With options
string GetText(string target, GetTextOptions getTextOptions)
string GetText(IElementDescriptor elementDescriptor, GetTextOptions getTextOptions)
string GetText(TargetAnchorableModel target, GetTextOptions getTextOptions = null)
string GetText(RuntimeTarget target, GetTextOptions getTextOptions = null)
```

**GetTextOptions** — created via `Options.GetText(scrapingOptions, scrapingMethod)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `ScrapingOptions` | `NScrapingOptions` | `None` | Scraping options |
| `ScrapingMethod` | `NScrapingMethod` | `Default` | Scraping method |

### Hover

Hovers the mouse over a specified UI element.

```csharp
// Simple
void Hover(string target, double hoverTime, CursorMotionType cursorMotionType)
void Hover(IElementDescriptor elementDescriptor, double? hoverTime = null, CursorMotionType? cursorMotionType = null)

// With options
void Hover(string target, HoverOptions hoverOptions)
void Hover(IElementDescriptor elementDescriptor, HoverOptions hoverOptions)
```

**HoverOptions** — created via `Options.Hover(hoverTime, cursorMotionType)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `HoverTime` | `double` | — | Hover duration in seconds |
| `CursorMotionType` | `CursorMotionType` | `Instant` | `Instant`, `Smooth` |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Override interaction mode |

### Check

Selects or clears a check box or radio button.

```csharp
// Simple
void Check(string target, NCheckType checkType = NCheckType.Check)
void Check(IElementDescriptor elementDescriptor, NCheckType checkType = NCheckType.Check)

// With options
void Check(string target, CheckOptions checkOptions)
void Check(IElementDescriptor elementDescriptor, CheckOptions checkOptions)
void Check(TargetAnchorableModel target, CheckOptions checkOptions = null)
void Check(RuntimeTarget target, CheckOptions checkOptions = null)
```

**CheckOptions** — created via `Options.Check(checkType)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `CheckType` | `NCheckType` | `Check` | `Check`, `Uncheck`, `Toggle` |
| `AlterIfDisabled` | `bool` | — | Alter if disabled |

### SelectItem

Selects an item from a drop-down combo box or list box.

```csharp
// Simple
void SelectItem(string target, string item)
void SelectItem(IElementDescriptor elementDescriptor, string item)

// With options
void SelectItem(string target, SelectItemOptions selectItemOptions)
void SelectItem(IElementDescriptor elementDescriptor, SelectItemOptions selectItemOptions)
void SelectItem(TargetAnchorableModel target, string item)
void SelectItem(TargetAnchorableModel target, SelectItemOptions selectItemOptions)
void SelectItem(RuntimeTarget target, SelectItemOptions selectItemOptions)
```

**SelectItemOptions** — created via `Options.SelectItem(item)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `Item` | `string` | required | The item to select |
| `AlterIfDisabled` | `bool` | — | Alter if disabled |

### SetValue

Sets the value of a UI element.

```csharp
void SetValue(string target, SetValueOptions setValueOptions)
void SetValue(TargetAnchorableModel target, SetValueOptions setValueOptions)
void SetValue(RuntimeTarget target, SetValueOptions setValueOptions)
```

**SetValueOptions** — created via `Options.SetValue(value)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `Value` | `string` | — | The value to set |
| `EnableValidation` | `bool` | — | Enable validation after setting |

### GetAttribute

Retrieves the value of a specified attribute of the indicated UI element.

```csharp
// Simple
string GetAttribute(string target, string attribute)
string GetAttribute(IElementDescriptor elementDescriptor, string attribute)

// With options
string GetAttribute(string target, GetAttributeOptions getAttributeOptions)
string GetAttribute(IElementDescriptor elementDescriptor, GetAttributeOptions getAttributeOptions)
```

**GetAttributeOptions** — created via `Options.GetAttribute(attribute)`:

| Property | Type | Description |
|---|---|---|
| `Attribute` | `string` | The attribute name to retrieve |

### IsEnabled

Checks if a UI element is enabled.

```csharp
bool IsEnabled(string target)
bool IsEnabled(string target, IsEnabledOptions isEnabledOptions)
bool IsEnabled(IElementDescriptor elementDescriptor)
bool IsEnabled(IElementDescriptor elementDescriptor, IsEnabledOptions isEnabledOptions)
bool IsEnabled(TargetAnchorableModel target, IsEnabledOptions isEnabledOptions = null)
bool IsEnabled(RuntimeTarget target, IsEnabledOptions isEnabledOptions = null)
```

`IsEnabledOptions` inherits common timeout properties from `TargetOptions`.

---

## Keyboard Shortcuts

Sends one or more keyboard shortcuts to a UI element.

```csharp
// Simple (on UiTargetApp)
void KeyboardShortcut(string target, string shortcuts, double delayBetweenShortcuts = 0.5)
void KeyboardShortcut(IElementDescriptor elementDescriptor, string shortcuts, double delayBetweenShortcuts = 0.5)

// Without target (sends to active window)
void KeyboardShortcut(string shortcuts, double delayBetweenShortcuts = 0.5)

// With options (on UiTargetApp)
void KeyboardShortcut(string target, KeyboardShortcutOptions keyboardShortcutOptions)
void KeyboardShortcut(IElementDescriptor elementDescriptor, KeyboardShortcutOptions keyboardShortcutOptions)
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions)

// On IUiAutomationAppService (standalone, no app handle needed)
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions)
```

**KeyboardShortcutOptions** — created via builder helpers:

| Property | Type | Default | Description |
|---|---|---|---|
| `Shortcuts` | `string` | required | The keyboard shortcut string |
| `ActivateBefore` | `bool` | — | Activate window before sending |
| `DelayBetweenShortcuts` | `double` | — | Delay between shortcuts in seconds |
| `DelayBetweenKeys` | `double` | — | Delay between keys in seconds |
| `ClickBeforeMode` | `NClickMode` | `None` | Click before sending (`None`, `Single`, `Double`) |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Override interaction mode |

**Shortcut helper methods on `Options`:**

```csharp
Options.KeyboardShortcutEsc()            // Escape
Options.KeyboardShortcutTab()            // Tab
Options.KeyboardShortcutCtrlA()          // Ctrl+A
Options.KeyboardShortcutCtrlC()          // Ctrl+C
Options.KeyboardShortcutCtrlV()          // Ctrl+V
Options.KeyboardShortcutCtrl("s")        // Ctrl+S (any key)
Options.KeyboardShortcutWinM()           // Win+M
Options.KeyboardShortcutWin("d")         // Win+D (any key)
Options.KeyboardShortcut(shortcuts)      // Raw shortcut string
```

Raw shortcut string format: `[d(hk)][d(ctrl)]c[u(ctrl)][u(hk)]` for Ctrl+C. Prefer the helper methods.

---

## Mouse Scroll

Enables scrolling in applications by sending mouse scroll events.

```csharp
// Simple
void MouseScroll(string target, NScrollDirection direction = NScrollDirection.Down, int movementUnits = 10)
void MouseScroll(IElementDescriptor elementDescriptor, NScrollDirection direction = NScrollDirection.Down, int movementUnits = 10)

// Scroll to element
void MouseScroll(string target, string searchedTarget, NScrollDirection direction = NScrollDirection.Down, int movementUnits = 100)
void MouseScroll(IElementDescriptor elementDescriptor, IElementDescriptor searchedElementDescriptor, NScrollDirection direction = NScrollDirection.Down, int movementUnits = 100)

// With options
void MouseScroll(string target, MouseScrollOptions mouseScrollOptions)
void MouseScroll(IElementDescriptor elementDescriptor, MouseScrollOptions mouseScrollOptions)
void MouseScroll(TargetAnchorableModel target, MouseScrollOptions mouseScrollOptions)
void MouseScroll(RuntimeTarget target, MouseScrollOptions mouseScrollOptions)
```

**MouseScrollOptions** — created via `Options.MouseScroll(direction, movementUnits)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `Direction` | `NScrollDirection` | `Down` | `Up`, `Down`, `Left`, `Right` |
| `MovementUnits` | `int` | 10 | Number of scroll detents |
| `KeyModifiers` | `NKeyModifiers` | `None` | Key modifiers during scroll |
| `CursorMotionType` | `CursorMotionType` | `Instant` | Cursor motion type |
| `InteractionMode` | `NChildInteractionMode` | `HardwareEvents` | Interaction mode |

To scroll until a target element is visible:
```csharp
Options.MouseScrollToElement(app["targetElement"], NScrollDirection.Down, movementUnits: 100)
```

---

## Drag and Drop

Drag and drop a specified UI element.

```csharp
// Simple
void DragAndDrop(string target, TargetAnchorableModel destinationTarget, NKeyModifiers? keyModifiers = null,
    NMouseButton? mouseButton = null, CursorMotionType? cursorMotionType = null,
    bool? useSourceHover = null, double? delayBetweenActions = null)

void DragAndDrop(IElementDescriptor elementDescriptor, IElementDescriptor destinationTarget, ...)
void DragAndDrop(IElementDescriptor elementDescriptor, TargetAnchorableModel destinationTarget, ...)

// With options
void DragAndDrop(string target, DragAndDropOptions dragAndDropOptions)
void DragAndDrop(IElementDescriptor elementDescriptor, DragAndDropOptions dragAndDropOptions)
```

**DragAndDropOptions** — created via `Options.DragAndDrop(...)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `DestinationTarget` | `TargetAnchorableModel` | — | Target to drop into |
| `KeyModifiers` | `NKeyModifiers` | `None` | Key modifiers during drag |
| `MouseButton` | `NMouseButton` | `Left` | Mouse button to drag with |
| `CursorMotionType` | `CursorMotionType` | `Instant` | Cursor motion |
| `UseSourceHover` | `bool` | `false` | Hover over source before dragging |
| `DelayBetweenActions` | `double` | 0 | Delay between actions |

---

## Screenshots and Highlighting

### TakeScreenshot

Takes a screenshot and saves to a file.

```csharp
// Simple
void TakeScreenshot(string target, string fileName)
void TakeScreenshot(IElementDescriptor elementDescriptor, string fileName)

// With options
void TakeScreenshot(string target, TakeScreenshotOptions takeScreenshotOptions)
void TakeScreenshot(IElementDescriptor elementDescriptor, TakeScreenshotOptions takeScreenshotOptions)
void TakeScreenshot(TargetAnchorableModel target, string fileName)
void TakeScreenshot(RuntimeTarget target, TakeScreenshotOptions takeScreenshotOptions)

// On IUiAutomationAppService (standalone, screenshot of entire screen)
void TakeScreenshot(TakeScreenshotOptions takeScreenshotOptions)
```

**TakeScreenshotOptions** — created via `Options.TakeScreenshotToFile(fileName)`:

| Property | Type | Description |
|---|---|---|
| `FileName` | `string` | Path to save the screenshot |

### Highlight

Visually highlights a specified UI element by surrounding it in a box.

```csharp
// Simple
void Highlight(string target, KnownColor color = KnownColor.Yellow, double duration = 3)
void Highlight(IElementDescriptor elementDescriptor, KnownColor color = KnownColor.Yellow, double duration = 3)

// With options
void Highlight(string target, HighlightOptions highlightOptions)
void Highlight(IElementDescriptor elementDescriptor, HighlightOptions highlightOptions)
```

**HighlightOptions** — created via `Options.Highlight(color, duration)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `Color` | `KnownColor` | `Yellow` | The highlight color (from `System.Drawing.KnownColor`) |
| `HighlightTime` | `double` | 3.0 | Duration in seconds |

---

## Browser Operations

### GoToUrl

Navigates to a URL in the browser.

```csharp
void GoToUrl(string url)
void GoToUrl(GoToUrlOptions urlOptions)
```

**GoToUrlOptions** — created via `Options.GoToUrl(url)`:

| Property | Type | Description |
|---|---|---|
| `Url` | `string` | The URL to navigate to |

### GetUrl

Gets the current URL of the browser.

```csharp
string GetUrl(GetUrlOptions getUrlOptions = null)
```

### SetRuntimeBrowser

Configures the runtime browser for execution. Remains in effect until execution ends or another SetRuntimeBrowser is called.

```csharp
// On IUiAutomationAppService
void SetDefaultRuntimeBrowser()
void SetRuntimeBrowser(NBrowserType browserType)
void SetRuntimeBrowser(SetRuntimeBrowserOptions setRuntimeBrowserOptions)
```

**SetRuntimeBrowserOptions** — created via `Options.SetRuntimeBrowser(browserType)`:

| Property | Type | Description |
|---|---|---|
| `BrowserType` | `NBrowserType` | `None`, `IE`, `Firefox`, `Chrome`, `Edge`, `Custom`, `WebWidgetNative`, `Safari` |

### GetAccessibilityCheck

Performs accessibility check on the current web page.

```csharp
string GetAccessibilityCheck(GetAccessibilityCheckOptions getAccessibilityCheckOptions = null)
```

---

## Clipboard Operations

### GetClipboard

Gets the text from the operating system's clipboard. Called on `IUiAutomationAppService`.

```csharp
string GetClipboard(GetClipboardOptions options)
```

### SetClipboard

Sets the text on the operating system's clipboard. Called on `IUiAutomationAppService`.

```csharp
void SetClipboard(SetClipboardOptions setClipboardOptions)
```

**SetClipboardOptions:**

| Property | Type | Description |
|---|---|---|
| `Text` | `string` | The text to set on the clipboard |

---

## State Checking

### WaitState

Checks the state of an application or web browser by verifying if an element appears in or disappears from the user interface.

```csharp
// Simple (on UiTargetApp)
bool WaitState(string target, NCheckStateMode checkStateMode, double timeout)
bool WaitState(IElementDescriptor elementDescriptor, NCheckStateMode checkStateMode, double timeout)

// With options (on UiTargetApp)
bool WaitState(string target, CheckStateOptions checkStateOptions)
bool WaitState(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions)
bool WaitState(TargetAnchorableModel target, NCheckStateMode checkStateMode, double timeout = 5)

// On IUiAutomationAppService (standalone)
bool WaitState(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions)
```

Returns `true` if the element was found in the expected state, `false` otherwise.

**CheckStateOptions** — created via builder helpers:

| Property | Type | Default | Description |
|---|---|---|---|
| `Mode` | `NCheckStateMode` | — | `WaitAppear` or `WaitDisappear` |
| `CheckVisibility` | `bool` | `false` | Also check element visibility |

Builder:
```csharp
Options.WaitAppear(checkVisibility: false, timeout: 10)
Options.WaitDisappear(checkVisibility: false, timeout: 10)
Options.CheckState(NCheckStateMode.WaitAppear, checkVisibility: false, timeout: 10)
```

---

## Element Discovery

### GetChildren

Gets the children of a specified target.

```csharp
IEnumerable<RuntimeTarget> GetChildren(string target, string selectorFilter,
    bool checkRootVisibility = false, bool recursive = false, double timeout = 30)

IEnumerable<RuntimeTarget> GetChildren(IElementDescriptor elementDescriptor, string selectorFilter,
    bool checkRootVisibility = false, bool recursive = false, double timeout = 30)

IEnumerable<RuntimeTarget> GetChildren(string target, GetChildrenOptions getChildrenOptions)
IEnumerable<RuntimeTarget> GetChildren(IElementDescriptor elementDescriptor, GetChildrenOptions getChildrenOptions)
```

**GetChildrenOptions** — created via `Options.GetChildren(selectorFilter, ...)`:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `SelectorFilter` | `string` | required | Selector filter to match children |
| `CheckRootVisibility` | `bool` | `false` | Check root element visibility |
| `Recursive` | `bool` | `false` | Get all descendants (not just direct children) |
| `Timeout` | `double` | 30 | Timeout in seconds |

### GetRuntimeTarget

Gets a `RuntimeTarget` from a specified target name.

```csharp
RuntimeTarget GetRuntimeTarget(string target, GetRuntimeTargetOptions getRuntimeTargetOptions = null)
```

### GetUiElement

Gets a `UiElement` corresponding to the indicated target. Available only for coded workflows.

```csharp
// On IUiAutomationAppService
UiElement GetUiElement(RuntimeTarget target)
```

---

## Data Extraction

### ExtractTableData

Extract data as a `DataTable`. Configuration is retrieved from Object Repository based on the target.

```csharp
// From Object Repository configuration
DataTable ExtractTableData(IElementDescriptor elementDescriptor, ExtractTableDataOptions extractTableDataOptions = null)
DataTable ExtractTableData(string target, ExtractTableDataOptions extractTableDataOptions = null)

// With explicit metadata and settings
DataTable ExtractTableData(TargetAnchorableModel target, string extractMetadata, string tableSettings,
    TargetAnchorableModel nextPageTarget = null, ExtractTableDataOptions extractDataOptions = null)
```

**ExtractTableDataOptions** — created via `Options.ExtractTableData(...)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `DelayBetweenPages` | `double` | — | Delay between pages in seconds |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction mode for next page click |
| `LimitExtractionTo` | `LimitType` | `Rows` | `Rows`, `None`, `Page` |
| `NumberOfItems` | `int?` | `null` | Max results (null or 0 = all) |

### ExtractData (Obsolete)

The `ExtractData` methods are obsolete. Use `ExtractTableData` instead.

---

## Form Filling and Popups

### FillForm

Fills a form with the provided data.

```csharp
void FillForm(object dataSource)
void FillForm(FillFormOptions fillFormOptions)
```

**FillFormOptions** — created via `Options.FillForm(dataSource)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `DataSource` | `object` | `null` | Data source to fill the form with |
| `EnableValidation` | `bool` | — | Enable validation after filling |

### ClosePopup

Closes all popups that are on top of the application and block a target.

```csharp
void ClosePopup(ClosePopupOptions closePopupOptions = null)
```

**ClosePopupOptions** — created via `Options.ClosePopup(preferredButtons, popupAppearTimeout)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `PreferredButtons` | `string[]` | `null` | Preferred button names to click (default: "Cancel" and "Close") |
| `PopupAppearTimeout` | `double` | — | Timeout waiting for popup to appear |
| `EnableAI` | `bool` | — | Enable AI for popup detection |

---

## JavaScript Injection

### InjectJsScript

Injects and executes a JavaScript script in a browser element.

```csharp
string InjectJsScript(string target, InjectJsScriptOptions injectJsScriptOptions)
string InjectJsScript(IElementDescriptor elementDescriptor, InjectJsScriptOptions injectJsScriptOptions)  // via RuntimeTargetApp
```

**InjectJsScriptOptions** — created via `Options.InjectJsScript(scriptCodePath, inputParameter)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `ScriptCodePath` | `string` | required | Path to the JavaScript file |
| `InputParameter` | `string` | `""` | Input parameter to pass to the script |
| `ExecutionWorld` | `NExecutionWorld` | `Isolated` | Execution world for the script |

---

## UI Task (Agent)

Executes an AI-powered UI task.

```csharp
UITaskResult UITask(UITaskOptions options = null)
```

**UITaskOptions** — created via `Options.UITask(task)`:

| Property | Type | Default | Description |
|---|---|---|---|
| `Task` | `string` | required | The task description for the AI agent |
| `AgentType` | `NUITaskAgentType` | — | The type of agent |
| `InteractionMode` | `NChildInteractionMode` | — | Interaction mode |
| `MaxIterations` | `int` | — | Maximum number of agent iterations |
| `ClipboardMode` | `NTypeByClipboardMode` | — | Clipboard mode for typing |
| `IsDOMEnabled` | `bool` | — | Enable DOM access |
| `IsVariableSecurityEnabled` | `bool` | — | Enable variable security |
| `TraceAttachMode` | `NTraceAttachMode` | — | Trace attach mode |

**UITaskResult:**

| Property | Type | Description |
|---|---|---|
| `Status` | — | Task execution status |
| `Result` | `string` | Task result |
| `ErrorMessage` | `string` | Error message if failed |
| `HttpErrorStatusCode` | — | HTTP error status code if applicable |
| `TraceFiles` | — | Trace files |

---

## Verify (Post-Action Verification)

Many option types support `.Until(...)` for post-action verification — checking if a target appears or disappears after performing the action:

```csharp
// Verify after Click
app.Click("submitBtn", Options.Click().Until("successMessage", until: NVerifyMode.Appears, retry: true, timeout: 5));

// Verify after TypeInto
app.TypeInto("field", Options.TypeInto("text").UntilText("text", retry: true, timeout: 2));
```

**Supported on**: `ClickOptions`, `TypeIntoOptions`, `HoverOptions`, `KeyboardShortcutOptions` (any type implementing `IWithVerify`).

**VerifyOptions:**

| Property | Type | Default | Description |
|---|---|---|---|
| `Target` / `TargetName` | — | — | Target to verify |
| `Mode` | `NVerifyMode` | `Appears` | `Appears` or `Disappears` |
| `Retry` | `bool` | `true` | Retry the action if verification fails |
| `Timeout` | `double` | 2 | Verification timeout in seconds |
| `DelayBefore` | `double` | 0.2 | Delay before verification |
| `ExpectedText` | `string` | `null` | Expected text (for UntilText) |

---

## SAP Operations

### SAPSelectMenuItem

Selects a menu item from a SAP window.

```csharp
void SAPSelectMenuItem(string item)
void SAPSelectMenuItem(SelectItemOptions selectItemOptions)
```

### SAPClickToolbarButton

Simulates a click on a SAP toolbar button.

```csharp
void SAPClickToolbarButton(string target, string button)
void SAPClickToolbarButton(string target, SelectItemOptions selectItemOptions)
void SAPClickToolbarButton(IElementDescriptor elementDescriptor, string button)
void SAPClickToolbarButton(TargetAnchorableModel target, string item)
void SAPClickToolbarButton(RuntimeTarget target, SelectItemOptions selectItemOptions)
```

### SAPReadStatusbar

Reads the SAP statusbar.

```csharp
SAPReadStatusbarResult SAPReadStatusbar()
SAPReadStatusbarResult SAPReadStatusbar(SAPReadStatusbarOptions readStatusbarOptions)
```

**SAPReadStatusbarResult:**

| Property | Type | Description |
|---|---|---|
| `MessageType` | `string` | Type of message |
| `MessageText` | `string` | Message text |
| `MessageId` | `string` | Message ID |
| `MessageNumber` | `string` | Message number |
| `MessageData` | — | Additional message data |

### SAPSelectDatesInCalendar

Selects dates in a SAP calendar control.

```csharp
// Single date
void SAPSelectDatesInCalendar(string target, DateTime date)

// Date range
void SAPSelectDatesInCalendar(string target, DateTime startDate, DateTime endDate)

// Week
void SAPSelectDatesInCalendar(string target, int year, int week)

// With options
void SAPSelectDatesInCalendar(string target, SAPSelectDatesInCalendarOptions options)
```

**SAPSelectDatesInCalendarOptions:**

| Property | Type | Description |
|---|---|---|
| `SelectType` | `NDateSelectionType` | `Date`, `Range`, `Week` |
| `Date` | `DateTime` | Single date |
| `StartDate` | `DateTime` | Range start date |
| `EndDate` | `DateTime` | Range end date |
| `Year` | `int` | Year for week selection |
| `Week` | `int` | Week number |

### SAPCallTransaction

Calls a SAP transaction.

```csharp
void SAPCallTransaction(string transaction)
void SAPCallTransaction(string transaction, string prefix)
void SAPCallTransaction(SAPCallTransactionOptions options)
```

**SAPCallTransactionOptions:**

| Property | Type | Description |
|---|---|---|
| `Transaction` | `string` | Transaction code |
| `Prefix` | `string` | Transaction prefix |

### SAPExpandTree / SAPExpandALVTree

Expands a node in a SAP tree / ALV tree control.

```csharp
void SAPExpandTree(string target, string path)
void SAPExpandTree(string target, SAPExpandTreeOptions options)

void SAPExpandALVTree(string target, string path)
void SAPExpandALVTree(string target, SAPExpandALVTreeOptions options)
```

| Property | Type | Description |
|---|---|---|
| `Path` | `string` | Tree path to expand |
