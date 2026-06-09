# UI Automation

Activities for interacting with desktop and web application UIs. Robots use selectors (XML descriptors of UI elements) to find and interact with buttons, text fields, tables, and other controls.

## How Selectors Work

A selector is an XML string that describes the path from the application window to the target UI element:

```xml
<html app='chrome.exe' title='Invoice Portal' />
<webctrl tag='BUTTON' aaname='Submit Invoice' />
```

When a robot executes a UI activity (Click, Type Into, Get Text, etc.), it uses the selector to locate the element in the live UI tree. If the element can't be found — because the UI changed, the element was renamed, or the layout shifted — the activity throws a `SelectorNotFoundException`.

## Key Activity Types

- **Click / NClick** — click a UI element
- **Type Into / NTypeInto** — type text into an input field
- **Get Text / NGetText** — extract text from a UI element
- **Set Text** — set the value of an input field
- **Check App State** — wait for a UI element to appear or disappear
- **Element Exists** — check if a UI element exists without interacting
- **Take Screenshot** — capture a screenshot of the application

## Exception Types

- **SelectorNotFoundException** — the selector didn't match any element in the UI tree. Most common failure.
- **UiElementNotFoundException** — UI element lookup failed (similar to selector not found, different internal path)
- **ElementNotInteractableException** — element was found but can't be clicked/typed into (hidden, disabled, covered by overlay)
- **UiNodeDisabledElementException** — element was found but is disabled and the activity's `AlterIfDisabled` property is not `True`. Driver HRESULT `E_UINODE_CANNOT_ALTER_DISABLED_ELEM` (0x8004027D). Raised by interaction activities `NClick`, `NTypeInto`, `NSetText`, `NCheck`, `NSelectItem`, `NSAPClickPictureOnScreen`.
- **VerifyActivityExecutionException** — activity's primary action succeeded but its `VerifyOptions` post-condition assertion did not hold within the verify retry window. Thrown by `VerifyExecutionService`, not COM-friendlied. Raised by `NClick`, `NHover`, `NKeyboardShortcuts`, `NTypeInto`. Multiple friendly messages route to distinct cause branches (`ExceptionCheckActivity`, `ExceptionVerificationTargetNotFoundOrInvalid`, `ExceptionVerificationTextNotSupported`, `ExceptionVerificationImageCouldNotBeRetrieved`, `ExceptionRecoveredButValidationFailed`, plus NTypeInto-specific text-match keys).
- **NodeNotFoundException** — DOM or UI tree node missing
- **TimeoutException** — activity exceeded its wait time (ambiguous — could be UI or non-UI)
- **ImageOperationException** — image-based UI automation failure
- **ScreenScrapingException** — screen scraping activity failure
- **ApplicationNotFoundException** — scope-level failure from `NApplicationCard` (Use Application / Use Browser) when the target application can't be located **and** the scope's `OpenMode=Never`. Distinct from `ApplicationOpenException` (which fires when `OpenMode != Never` and launch failed) and `WrongTargetApplicationException` (selector matched the wrong process).

UIAutomationNext (`N*`) activities also raise these more specific exceptions:

- **RuntimeTimeoutException** — modern activity timeout ("Activity execution exceeded the set timeout."). A UI timeout can also surface as **NodeNotFoundException** when the element never appeared within the timeout window.
- **ApplicationOpenException** — a `Use Application/Browser` scope with `Open` ≠ `Never` tried to launch the app and the launch failed ("Could not open target application.")
- **WrongTargetApplicationException** — the identified element belongs to a different application/browser than the scope's target
- **BrowserFailedToNavigateToUrlException** / **BrowserInvalidURLException** — `Go To URL` could not navigate (failed navigation, invalid/empty URL, or a local `file://` blocked on Chromium)
- **InvalidNodeException** / **UiNodeUninitializedElementException** — the element went invalid/stale between being found and acted on
- **TargetFoundButNotVisibleException** — element found but its visibility did not match what the target expected
- **TargetNotFoundBrowserBlockedException** — element could not be reached because a dialog is blocking the browser
- **UiNodeHasNoItemsException** — Select Item's target container had no items
- **UiAutomationException (activity configuration)** — an activity rejected an invalid property value (e.g. Mouse Scroll `Movement units` < 1, Keyboard Shortcuts empty/invalid sequence, Take Screenshot missing `File name`/`Saved image`, Go To URL / Inject Js Script missing required input)

## Features

- **Healing Agent Data** — recovery data captured when HA is enabled and activities fail → [interpretations/healing-agent-data.md](./interpretations/healing-agent-data.md)
